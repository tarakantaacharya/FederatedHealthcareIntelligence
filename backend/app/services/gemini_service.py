"""
Gemini AI Summarization Service

Provides AI-powered summaries for predictions using Google's Gemini API.
Generates natural language insights about forecast results, metrics, and trends.
"""
import json
from typing import Dict, Any, Optional, List
from app.config import get_settings

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

settings = get_settings()


class GeminiService:
    """AI summarization service using Google Gemini"""

    _configured = False

    @classmethod
    def _ensure_configured(cls):
        """Configure Gemini API with key"""
        if not GEMINI_AVAILABLE:
            return
        if not cls._configured and settings.ENABLE_AI_SUMMARIES:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            cls._configured = True

    @staticmethod
    def generate_prediction_summary(
        prediction_data: Dict[str, Any],
        forecast_values: List[float],
        metrics: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI-powered summary of a prediction result

        Args:
            prediction_data: Basic prediction metadata (target, horizon, model type)
            forecast_values: List of forecasted values
            metrics: Performance metrics (MAPE, RMSE, R2, etc.)
            context: Additional context (hospital name, dataset info, etc.)

        Returns:
            Natural language summary of the prediction
        """
        if not settings.ENABLE_AI_SUMMARIES or not GEMINI_AVAILABLE:
            return GeminiService._generate_fallback_summary(
                prediction_data, forecast_values, metrics
            )

        try:
            GeminiService._ensure_configured()
            model = genai.GenerativeModel(settings.GEMINI_MODEL)

            # Build structured prompt
            prompt = GeminiService._build_prediction_prompt(
                prediction_data, forecast_values, metrics, context
            )

            # Generate summary
            response = model.generate_content(prompt)
            summary = response.text.strip()

            return summary

        except Exception as e:
            print(f"[GEMINI ERROR] Failed to generate AI summary: {str(e)}")
            # Fallback to rule-based summary
            return GeminiService._generate_fallback_summary(
                prediction_data, forecast_values, metrics
            )

    @staticmethod
    def _build_prediction_prompt(
        prediction_data: Dict[str, Any],
        forecast_values: List[float],
        metrics: Dict[str, float],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build detailed prompt for Gemini"""
        
        target = prediction_data.get("target_column", "value")
        horizon = prediction_data.get("forecast_horizon", len(forecast_values))
        model_type = prediction_data.get("model_type", "LOCAL")
        
        # Calculate statistics
        avg_forecast = sum(forecast_values) / len(forecast_values) if forecast_values else 0
        min_forecast = min(forecast_values) if forecast_values else 0
        max_forecast = max(forecast_values) if forecast_values else 0
        
        # Determine trend
        if len(forecast_values) >= 2:
            first_half = sum(forecast_values[:len(forecast_values)//2]) / (len(forecast_values)//2)
            second_half = sum(forecast_values[len(forecast_values)//2:]) / (len(forecast_values) - len(forecast_values)//2)
            trend = "increasing" if second_half > first_half else "decreasing" if second_half < first_half else "stable"
        else:
            trend = "stable"

        prompt = f"""You are an AI assistant for a Federated Healthcare Intelligence Platform. Generate a concise, professional summary of the following prediction results.

**Prediction Context:**
- Target Variable: {target}
- Forecast Horizon: {horizon} hours
- Model Type: {model_type}
- Hospital: {context.get('hospital_name', 'N/A') if context else 'N/A'}

**Forecast Statistics:**
- Average Predicted Value: {avg_forecast:.2f}
- Range: {min_forecast:.2f} to {max_forecast:.2f}
- Trend: {trend}

**Model Performance Metrics:**
- MAPE (Mean Absolute Percentage Error): {metrics.get('mape', 0):.2f}%
- RMSE (Root Mean Squared Error): {metrics.get('rmse', 0):.4f}
- R² Score: {metrics.get('r2', 0):.4f}
- MAE (Mean Absolute Error): {metrics.get('mae', 0):.4f}

**Forecast Values (first 10):**
{json.dumps(forecast_values[:10], indent=2)}

**Instructions:**
1. Write a 3-4 sentence summary suitable for healthcare professionals
2. Highlight key insights (trend, accuracy, actionable information)
3. Use professional medical/healthcare terminology
4. Mention if the model performance is excellent (MAPE<10%), good (10-20%), or needs improvement (>20%)
5. Be concise but informative

Generate the summary now:"""

        return prompt

    @staticmethod
    def _generate_fallback_summary(
        prediction_data: Dict[str, Any],
        forecast_values: List[float],
        metrics: Dict[str, float]
    ) -> str:
        """Generate rule-based summary when AI is unavailable"""
        
        target = prediction_data.get("target_column", "value")
        horizon = prediction_data.get("forecast_horizon", len(forecast_values))
        model_type = prediction_data.get("model_type", "LOCAL")
        
        avg = sum(forecast_values) / len(forecast_values) if forecast_values else 0
        mape = metrics.get("mape", 0)
        r2 = metrics.get("r2", 0)
        
        # Assess quality
        if mape < 10:
            quality = "excellent accuracy"
        elif mape < 20:
            quality = "good accuracy"
        else:
            quality = "moderate accuracy"
        
        # Determine trend
        if len(forecast_values) >= 2:
            first_half = sum(forecast_values[:len(forecast_values)//2]) / (len(forecast_values)//2)
            second_half = sum(forecast_values[len(forecast_values)//2:]) / (len(forecast_values) - len(forecast_values)//2)
            if second_half > first_half * 1.1:
                trend_desc = "shows an increasing trend"
            elif second_half < first_half * 0.9:
                trend_desc = "shows a decreasing trend"
            else:
                trend_desc = "remains relatively stable"
        else:
            trend_desc = "indicates stable values"
        
        summary = (
            f"This {model_type.lower()} model forecast predicts {target} over the next {horizon} hours "
            f"with an average value of {avg:.2f}. The prediction {trend_desc} throughout the forecast horizon. "
            f"Model performance shows {quality} with MAPE of {mape:.2f}% and R² of {r2:.4f}. "
            f"These predictions can be used for resource planning and operational decision-making."
        )
        
        return summary

    @staticmethod
    def generate_comparison_summary(
        comparisons: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI summary comparing multiple models

        Args:
            comparisons: List of model comparison data
            context: Additional context

        Returns:
            Summary comparing models
        """
        if not settings.ENABLE_AI_SUMMARIES or not GEMINI_AVAILABLE or not comparisons:
            return "Model comparison summary not available."

        try:
            GeminiService._ensure_configured()
            model = genai.GenerativeModel(settings.GEMINI_MODEL)

            # Build comparison prompt
            prompt = f"""You are analyzing multiple forecasting models for a healthcare platform. Compare the following models:

"""
            for i, comp in enumerate(comparisons, 1):
                model_type = comp.get("model_type", "Unknown")
                mape = comp.get("mape", 0)
                r2 = comp.get("r2", 0)
                avg_pred = comp.get("average_prediction", 0)
                
                prompt += f"""
Model {i} ({model_type}):
- MAPE: {mape:.2f}%
- R² Score: {r2:.4f}
- Average Prediction: {avg_pred:.2f}
"""

            prompt += """
Generate a 2-3 sentence comparison highlighting:
1. Which model performs best and why
2. Key differences in predictions
3. Recommendation for which model to use

Be concise and professional:"""

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            print(f"[GEMINI ERROR] Failed to generate comparison summary: {str(e)}")
            return "Multiple models analyzed. Review individual metrics to determine best performance."

    @staticmethod
    def generate_report_insights(
        prediction_record: Dict[str, Any],
        historical_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """
        Generate comprehensive insights for PDF report

        Args:
            prediction_record: Full prediction record with all metadata
            historical_context: Previous predictions for trend analysis

        Returns:
            Dict with sections: executive_summary, technical_analysis, recommendations
        """
        if not settings.ENABLE_AI_SUMMARIES or not GEMINI_AVAILABLE:
            return {
                "executive_summary": "Executive summary not available.",
                "technical_analysis": "Technical analysis not available.",
                "recommendations": "Recommendations not available."
            }

        try:
            GeminiService._ensure_configured()
            model = genai.GenerativeModel(settings.GEMINI_MODEL)

            # Build comprehensive prompt
            prompt = f"""You are generating a comprehensive prediction report for healthcare executives and data scientists.

**Prediction Details:**
{json.dumps(prediction_record, indent=2, default=str)}

Generate three sections:

1. **EXECUTIVE SUMMARY** (2-3 sentences):
   - High-level overview for non-technical stakeholders
   - Key takeaway and business impact
   
2. **TECHNICAL ANALYSIS** (3-4 sentences):
   - Detailed assessment of model performance
   - Statistical insights and accuracy metrics
   - Forecast characteristics (trend, volatility, confidence)
   
3. **RECOMMENDATIONS** (2-3 bullet points):
   - Actionable recommendations based on the prediction
   - Resource allocation suggestions
   - Monitoring and follow-up actions

Format as JSON with keys: executive_summary, technical_analysis, recommendations"""

            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                insights = json.loads(text)
                return insights
            except json.JSONDecodeError:
                # If not valid JSON, split by headers
                sections = {
                    "executive_summary": "",
                    "technical_analysis": "",
                    "recommendations": ""
                }
                
                current_section = None
                for line in text.split("\n"):
                    line = line.strip()
                    if "EXECUTIVE SUMMARY" in line.upper():
                        current_section = "executive_summary"
                    elif "TECHNICAL ANALYSIS" in line.upper():
                        current_section = "technical_analysis"
                    elif "RECOMMENDATION" in line.upper():
                        current_section = "recommendations"
                    elif current_section and line:
                        sections[current_section] += line + " "
                
                return sections

        except Exception as e:
            print(f"[GEMINI ERROR] Failed to generate report insights: {str(e)}")
            return {
                "executive_summary": "This prediction provides forecast insights for operational planning.",
                "technical_analysis": "Model performance metrics are available in the detailed metrics section.",
                "recommendations": "Review forecast values and adjust resource allocation accordingly."
            }
