"""
Federated AI Copilot LLM Service
Lightweight Hugging Face model integration with strict safety controls
"""
import json
import os
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache
from collections import OrderedDict
import threading
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

# Safety patterns - hard-coded overrides BEFORE LLM
UNSAFE_PATTERNS = [
    r"show\s+raw\s+data",
    r"patient\s+details",
    r"export\s+prediction\s+table",
    r"give\s+me\s+.*\s+records",
    r"list\s+all\s+patients",
    r"sensitive\s+data",
    r"identifiable\s+information",
]

SAFE_REFUSAL = (
    "I cannot access or disclose patient-level data. "
    "I can provide aggregated insights, governance analysis, and federated learning intelligence only."
)

# Model configuration
DEFAULT_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Smallest, fastest
ALTERNATIVE_MODELS = [
    "microsoft/phi-2",  # 2.7B - better quality
    "mistralai/Mistral-7B-Instruct-v0.2",  # 7B - best quality but needs GPU
]

USE_4BIT_QUANTIZATION = os.getenv("LLM_USE_4BIT", "false").lower() == "true"
MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "300"))
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT", "30.0"))  # Increased from 3s to 30s for CPU
CACHE_SIZE = int(os.getenv("LLM_CACHE_SIZE", "100"))  # Cache last 100 responses
AUTO_LOAD_ON_REQUEST = os.getenv("LLM_AUTO_LOAD_ON_REQUEST", "false").lower() == "true"

# System prompt (governance-aware, safety-first)
SYSTEM_PROMPT = """You are a Federated Healthcare AI Governance Assistant.

Your role: Interpret aggregated metadata from a privacy-preserving federated learning platform.

STRICT RULES:
1. NEVER return patient-level data or row-level predictions
2. Answer ONLY using the provided structured metadata JSON
3. If data is insufficient, clearly say so
4. Be concise, analytical, and governance-aware
5. Focus on federated learning impact, differential privacy, and audit trails

FORBIDDEN TOPICS:
- Patient identities
- Raw prediction records
- Unverified claims about metrics not in context

Your responses must help healthcare AI governance teams make informed decisions."""


class ResponseCache:
    """Thread-safe LRU cache for LLM responses"""
    
    def __init__(self, max_size: int = CACHE_SIZE):
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _hash_key(self, message: str, context: Dict[str, Any], role: str) -> str:
        """Generate cache key from query components"""
        # Hash only message and role (context may contain timestamps)
        key_data = f"{role}:{message.lower().strip()}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, message: str, context: Dict[str, Any], role: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if available"""
        key = self._hash_key(message, context, role)
        with self.lock:
            if key in self.cache:
                self.hits += 1
                # Move to end (LRU)
                self.cache.move_to_end(key)
                cached = self.cache[key].copy()
                cached["from_cache"] = True
                logger.info(f"Cache HIT: {key[:8]}... (hit rate: {self.get_hit_rate():.2%})")
                return cached
            else:
                self.misses += 1
                return None
    
    def put(self, message: str, context: Dict[str, Any], role: str, response: Dict[str, Any]):
        """Store response in cache"""
        key = self._hash_key(message, context, role)
        with self.lock:
            self.cache[key] = response.copy()
            self.cache.move_to_end(key)
            
            # Evict oldest if over limit
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                logger.debug(f"Cache evicted: {oldest_key[:8]}...")
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def clear(self):
        """Clear all cached responses"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Response cache cleared")


class CopilotLLMService:
    """Lightweight LLM service for federated healthcare intelligence"""
    
    _model = None
    _tokenizer = None
    _model_name = None
    _load_lock = threading.Lock()
    _enabled = os.getenv("COPILOT_LLM_ENABLED", "true").lower() == "true"
    _response_cache = ResponseCache(max_size=CACHE_SIZE)
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if LLM is enabled (can be disabled via env var)"""
        return cls._enabled
    
    @classmethod
    @lru_cache(maxsize=1)
    def _get_model_choice(cls) -> str:
        """
        Select model based on:
        1. Environment variable LLM_MODEL
        2. GPU availability
        3. Fallback to TinyLlama (CPU-friendly)
        """
        env_model = os.getenv("LLM_MODEL", "").strip()
        if env_model:
            return env_model
        
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("GPU detected, using Mistral-7B with 4-bit quantization")
                return "mistralai/Mistral-7B-Instruct-v0.2"
        except ImportError:
            pass
        
        logger.info("No GPU or PyTorch not available, using TinyLlama (CPU-optimized)")
        return DEFAULT_MODEL_NAME
    
    @classmethod
    def load_model(cls) -> Tuple[bool, Optional[str]]:
        """
        Load the LLM model (lazy initialization)
        Returns: (success: bool, error_message: Optional[str])
        """
        if not cls._enabled:
            return False, "LLM disabled via COPILOT_LLM_ENABLED=false"
        
        if cls._model is not None:
            return True, None
        
        with cls._load_lock:
            # Double-check after acquiring lock
            if cls._model is not None:
                return True, None
            
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                model_name = cls._get_model_choice()
                cls._model_name = model_name
                
                logger.info(f"⏳ Loading LLM: {model_name} (this may take several minutes on first run)")
                logger.info(f"💡 Tip: The model will be cached locally for faster subsequent loads")
                
                # Load configuration
                load_kwargs = {
                    "device_map": "auto",
                    "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
                    "low_cpu_mem_usage": True,
                }
                
                # Apply 4-bit quantization if enabled and available
                if USE_4BIT_QUANTIZATION and torch.cuda.is_available():
                    try:
                        from transformers import BitsAndBytesConfig
                        load_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4",
                        )
                        logger.info("✅ Enabled 4-bit quantization (GPU)")
                    except ImportError:
                        logger.warning("⚠️ bitsandbytes not available, skipping quantization")
                
                logger.info(f"📥 Downloading/loading tokenizer...")
                cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
                logger.info(f"✅ Tokenizer loaded")
                
                logger.info(f"📥 Downloading/loading model ({model_name})...")
                cls._model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
                logger.info(f"✅ Model loaded successfully")
                
                logger.info(f"🚀 LLM is ready: {model_name}")
                return True, None
                
            except Exception as e:
                logger.error(f"❌ Failed to load LLM: {str(e)}")
                logger.error(f"💡 Copilot will fall back to rule-based responses")
                cls._model = None
                cls._tokenizer = None
                return False, f"Model load failed: {str(e)}"
    
    @classmethod
    def check_safety(cls, message: str) -> Optional[str]:
        """
        Hard-coded safety check BEFORE LLM
        Returns refusal message if unsafe, None if safe
        """
        import re
        message_lower = message.lower()
        
        for pattern in UNSAFE_PATTERNS:
            if re.search(pattern, message_lower):
                return SAFE_REFUSAL
        
        return None
    
    @classmethod
    def sanitize_context(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from context before LLM processing
        - Strip identifiers
        - Aggregate everything
        - Round floats
        - Limit list lengths
        """
        sanitized = {}
        
        for key, value in context.items():
            if key in ["hospital_id", "user_id", "patient_id"]:
                continue  # Skip identifiable IDs
            
            if isinstance(value, dict):
                sanitized[key] = cls.sanitize_context(value)
            elif isinstance(value, list):
                # Limit list length and sanitize items
                sanitized[key] = [
                    cls.sanitize_context(item) if isinstance(item, dict) else item
                    for item in value[:10]  # Max 10 items
                ]
            elif isinstance(value, float):
                sanitized[key] = round(value, 3)
            else:
                sanitized[key] = value
        
        return sanitized
    
    @classmethod
    def construct_prompt(cls, message: str, context: Dict[str, Any], role: str) -> str:
        """
        Build safe prompt with structured context
        Format: System + Context JSON + User Query
        """
        sanitized_context = cls.sanitize_context(context)
        
        context_json = json.dumps(sanitized_context, indent=2, default=str)
        
        prompt = f"""{SYSTEM_PROMPT}

User Role: {role}
Platform Context (Structured Metadata):
```json
{context_json}
```

User Query: {message}

Analysis:"""
        
        return prompt
    
    @classmethod
    def validate_response(cls, response: str, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate LLM response for hallucinations and unsafe content
        Returns: (is_valid: bool, cleaned_response: Optional[str])
        """
        if not response or len(response.strip()) < 20:
            return False, None
        
        response_lower = response.lower()
        
        # Reject if mentions non-existent entities
        hallucination_markers = [
            "dataset_99",
            "round_999",
            "hospital xyz",
            "patient #",
        ]
        
        for marker in hallucination_markers:
            if marker in response_lower:
                logger.warning(f"Detected hallucination: {marker}")
                return False, None
        
        # Reject if mentions raw data
        unsafe_mentions = [
            "raw patient data",
            "individual records",
            "export all",
        ]
        
        for mention in unsafe_mentions:
            if mention in response_lower:
                logger.warning(f"Unsafe content detected: {mention}")
                return False, None
        
        # Truncate to max length
        if len(response) > 2000:
            response = response[:1997] + "..."
        
        return True, response
    
    @classmethod
    def generate_response(
        cls,
        message: str,
        context: Dict[str, Any],
        role: str,
    ) -> Dict[str, Any]:
        """
        Generate LLM response with full safety pipeline + caching
        Returns: {
            "answer": str,
            "model_used": str,
            "response_time": float,
            "fallback_used": bool,
            "guardrails_triggered": List[str],
            "from_cache": bool
        }
        """
        start_time = time.time()
        guardrails_triggered = []
        
        # Check cache first
        cached_response = cls._response_cache.get(message, context, role)
        if cached_response:
            logger.info(f"Returning cached response (saved {cached_response.get('response_time', 0)}s)")
            cached_response["response_time"] = round(time.time() - start_time, 3)  # Update with cache retrieval time
            return cached_response
        
        # Safety check BEFORE LLM
        safety_refusal = cls.check_safety(message)
        if safety_refusal:
            guardrails_triggered.append("unsafe_query_pattern")
            result = {
                "answer": safety_refusal,
                "model_used": "safety_filter",
                "response_time": time.time() - start_time,
                "fallback_used": False,
                "guardrails_triggered": guardrails_triggered,
                "from_cache": False,
            }
            cls._response_cache.put(message, context, role, result)
            return result
        
        # Load model if not loaded (optional to prevent request-time blocking)
        if cls._model is None:
            if not AUTO_LOAD_ON_REQUEST:
                guardrails_triggered.append("model_not_preloaded")
                result = {
                    "answer": "LLM is not preloaded. Falling back to rule-based system.",
                    "model_used": "none",
                    "response_time": time.time() - start_time,
                    "fallback_used": True,
                    "guardrails_triggered": guardrails_triggered,
                    "from_cache": False,
                }
                return result

            success, error = cls.load_model()
            if not success:
                guardrails_triggered.append("model_load_failed")
                result = {
                    "answer": f"LLM unavailable ({error}). Falling back to rule-based system.",
                    "model_used": "none",
                    "response_time": time.time() - start_time,
                    "fallback_used": True,
                    "guardrails_triggered": guardrails_triggered,
                    "from_cache": False,
                }
                return result  # Don't cache failures
        
        try:
            # Construct prompt
            prompt = cls.construct_prompt(message, context, role)
            
            logger.info(f"Starting LLM generation (timeout: {TIMEOUT_SECONDS}s)")
            
            # Run generation with timeout using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(cls._generate_with_model, prompt)
                try:
                    response = future.result(timeout=TIMEOUT_SECONDS)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"LLM generation timed out after {TIMEOUT_SECONDS}s")
                    guardrails_triggered.append("generation_timeout")
                    result = {
                        "answer": f"LLM generation took too long (>{TIMEOUT_SECONDS}s). Falling back to rule-based system.",
                        "model_used": cls._model_name or "unknown",
                        "response_time": time.time() - start_time,
                        "fallback_used": True,
                        "guardrails_triggered": guardrails_triggered,
                        "from_cache": False,
                    }
                    return result  # Don't cache timeouts
            
            # Validate response
            is_valid, cleaned_response = cls.validate_response(response, context)
            
            if not is_valid:
                guardrails_triggered.append("response_validation_failed")
                result = {
                    "answer": "Generated response failed validation. Falling back to rule-based system.",
                    "model_used": cls._model_name or "unknown",
                    "response_time": time.time() - start_time,
                    "fallback_used": True,
                    "guardrails_triggered": guardrails_triggered,
                    "from_cache": False,
                }
                return result  # Don't cache invalid responses
            
            result = {
                "answer": cleaned_response,
                "model_used": cls._model_name or "unknown",
                "response_time": round(time.time() - start_time, 2),
                "fallback_used": False,
                "guardrails_triggered": guardrails_triggered,
                "from_cache": False,
            }
            
            # Cache successful response
            cls._response_cache.put(message, context, role, result)
            
            logger.info(f"LLM generation successful in {result['response_time']}s")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            guardrails_triggered.append("generation_exception")
            result = {
                "answer": f"LLM error: {str(e)}. Falling back to rule-based system.",
                "model_used": cls._model_name or "unknown",
                "response_time": time.time() - start_time,
                "fallback_used": True,
                "guardrails_triggered": guardrails_triggered,
                "from_cache": False,
            }
            return result  # Don't cache exceptions
    
    @classmethod
    def unload_model(cls):
        """Free GPU/CPU memory"""
        if cls._model is not None:
            del cls._model
            del cls._tokenizer
            cls._model = None
            cls._tokenizer = None
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            logger.info("LLM unloaded")
    
    @classmethod
    def _generate_with_model(cls, prompt: str) -> str:
        """
        Internal method to generate response (synchronous).
        Used with timeout wrapper in generate_response().
        """
        import torch
        
        # Tokenize
        inputs = cls._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        # Move to device
        if cls._model.device.type != "cpu":
            inputs = {k: v.to(cls._model.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = cls._model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                eos_token_id=cls._tokenizer.eos_token_id,
                pad_token_id=cls._tokenizer.pad_token_id,
            )
        
        # Decode
        generated_text = cls._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract response
        if "Analysis:" in generated_text:
            return generated_text.split("Analysis:")[-1].strip()
        else:
            return generated_text[len(prompt):].strip()
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(cls._response_cache.cache),
            "max_size": cls._response_cache.max_size,
            "hits": cls._response_cache.hits,
            "misses": cls._response_cache.misses,
            "hit_rate": cls._response_cache.get_hit_rate(),
        }
    
    @classmethod
    def clear_cache(cls):
        """Clear response cache"""
        cls._response_cache.clear()
