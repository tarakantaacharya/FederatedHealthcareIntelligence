"""
Temporal Fusion Transformer (TFT) Model (Phase 15)
Advanced multi-horizon time series forecasting
"""
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from torch.utils.data import Dataset, DataLoader


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer for hospital resource forecasting
    
    Features:
    - Multi-horizon forecasting (predict multiple future time steps)
    - Variable selection networks
    - Temporal self-attention
    - Quantile regression for uncertainty
    """
    
    def __init__(
        self,
        num_static_features: int,
        num_historical_features: int,
        num_future_features: int,
        hidden_size: int = 128,
        num_attention_heads: int = 4,
        num_quantiles: int = 3,
        dropout_rate: float = 0.1,
        forecast_horizon: int = 24
    ):
        """
        Initialize TFT model
        
        Args:
            num_static_features: Number of static features (hospital characteristics)
            num_historical_features: Number of time-varying historical features
            num_future_features: Number of known future features
            hidden_size: Hidden layer dimension
            num_attention_heads: Number of attention heads
            num_quantiles: Number of quantiles to predict (e.g., [0.1, 0.5, 0.9])
            dropout_rate: Dropout probability
            forecast_horizon: Number of time steps to forecast
        """
        super(TemporalFusionTransformer, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_attention_heads = num_attention_heads
        self.num_quantiles = num_quantiles
        self.forecast_horizon = forecast_horizon
        
        # Variable selection networks
        self.static_variable_selection = VariableSelectionNetwork(
            num_static_features, hidden_size, dropout_rate
        )
        
        self.historical_variable_selection = VariableSelectionNetwork(
            num_historical_features, hidden_size, dropout_rate
        )
        
        self.future_variable_selection = VariableSelectionNetwork(
            num_future_features, hidden_size, dropout_rate
        )
        
        # LSTM encoders
        self.historical_lstm = nn.LSTM(
            hidden_size, hidden_size, batch_first=True, dropout=dropout_rate
        )
        
        self.future_lstm = nn.LSTM(
            hidden_size, hidden_size, batch_first=True, dropout=dropout_rate
        )
        
        # Self-attention layer
        self.self_attention = nn.MultiheadAttention(
            hidden_size, num_attention_heads, dropout=dropout_rate, batch_first=True
        )
        
        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 4),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size * 4, hidden_size)
        )
        
        # Quantile output layers (one per quantile)
        self.quantile_outputs = nn.ModuleList([
            nn.Linear(hidden_size, 1) for _ in range(num_quantiles)
        ])
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(hidden_size)
    
    def forward(
        self,
        static_features: torch.Tensor,
        historical_features: torch.Tensor,
        future_features: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            static_features: [batch, num_static_features]
            historical_features: [batch, seq_len, num_historical_features]
            future_features: [batch, forecast_horizon, num_future_features]
        
        Returns:
            Dictionary with:
            - quantile_forecasts: [batch, forecast_horizon, num_quantiles]
            - attention_weights: [batch, num_heads, forecast_horizon, seq_len]
        """
        batch_size = static_features.size(0)
        
        # Variable selection
        static_context = self.static_variable_selection(static_features)
        historical_context = self.historical_variable_selection(historical_features)
        future_context = self.future_variable_selection(future_features)
        
        # Encode historical sequence
        historical_encoded, (h_n, c_n) = self.historical_lstm(historical_context)
        
        # Encode future sequence (with historical state)
        future_encoded, _ = self.future_lstm(future_context, (h_n, c_n))
        
        # Self-attention over temporal sequence
        attended, attention_weights = self.self_attention(
            future_encoded, future_encoded, future_encoded
        )
        
        # Feed-forward network with residual connection
        ffn_output = self.ffn(attended)
        output = self.layer_norm(attended + ffn_output)
        
        # Quantile predictions
        quantile_forecasts = []
        for quantile_layer in self.quantile_outputs:
            quantile_pred = quantile_layer(output)  # [batch, forecast_horizon, 1]
            quantile_forecasts.append(quantile_pred)
        
        quantile_forecasts = torch.cat(quantile_forecasts, dim=-1)  # [batch, horizon, num_quantiles]
        
        return {
            'quantile_forecasts': quantile_forecasts,
            'attention_weights': attention_weights
        }


class VariableSelectionNetwork(nn.Module):
    """Variable selection network with gating"""
    
    def __init__(self, num_features: int, hidden_size: int, dropout_rate: float = 0.1):
        super(VariableSelectionNetwork, self).__init__()
        
        self.num_features = num_features
        self.hidden_size = hidden_size
        
        # Feature transformations
        self.feature_transforms = nn.ModuleList([
            nn.Linear(1, hidden_size) for _ in range(num_features)
        ])
        
        # Gating network
        self.gate = nn.Sequential(
            nn.Linear(num_features * hidden_size, num_features),
            nn.Softmax(dim=-1)
        )
        
        self.dropout = nn.Dropout(dropout_rate)
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            features: [batch, ..., num_features]
        
        Returns:
            Selected features: [batch, ..., hidden_size]
        """
        original_shape = features.shape
        features = features.reshape(-1, self.num_features)
        
        # Transform each feature
        transformed = []
        for i, transform in enumerate(self.feature_transforms):
            feat = features[:, i:i+1]  # [batch, 1]
            transformed.append(transform(feat))  # [batch, hidden_size]
        
        transformed = torch.stack(transformed, dim=1)  # [batch, num_features, hidden_size]
        
        # Gating
        flat_transformed = transformed.reshape(-1, self.num_features * self.hidden_size)
        gates = self.gate(flat_transformed)  # [batch, num_features]
        gates = gates.unsqueeze(-1)  # [batch, num_features, 1]
        
        # Weighted sum
        selected = (transformed * gates).sum(dim=1)  # [batch, hidden_size]
        
        # Restore original batch dimensions
        output_shape = list(original_shape[:-1]) + [self.hidden_size]
        selected = selected.reshape(output_shape)
        
        return self.dropout(selected)


class HospitalTimeSeriesDataset(Dataset):
    """Dataset for hospital time series data"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        static_features: List[str],
        historical_features: List[str],
        future_features: List[str],
        target_column: str,
        sequence_length: int = 24,
        forecast_horizon: int = 24
    ):
        """
        Initialize dataset
        
        Args:
            df: Pandas DataFrame with time series data
            static_features: List of static feature column names
            historical_features: List of historical feature column names
            future_features: List of future feature column names
            target_column: Target column name
            sequence_length: Historical sequence length
            forecast_horizon: Number of steps to forecast
        """
        self.df = df
        self.static_features = static_features
        self.historical_features = historical_features
        self.future_features = future_features
        self.target_column = target_column
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        
        # Create sequences
        self.sequences = self._create_sequences()
    
    def _create_sequences(self) -> List[Dict]:
        """Create training sequences from dataframe"""
        sequences = []
        
        max_idx = len(self.df) - self.sequence_length - self.forecast_horizon
        
        for i in range(max_idx):
            # Historical window
            hist_start = i
            hist_end = i + self.sequence_length
            
            # Future window
            future_start = hist_end
            future_end = future_start + self.forecast_horizon
            
            # Extract data
            static = self.df[self.static_features].iloc[hist_start].values.astype(np.float32)
            historical = self.df[self.historical_features].iloc[hist_start:hist_end].values.astype(np.float32)
            future = self.df[self.future_features].iloc[future_start:future_end].values.astype(np.float32)
            target = self.df[self.target_column].iloc[future_start:future_end].values.astype(np.float32)
            
            sequences.append({
                'static': static,
                'historical': historical,
                'future': future,
                'target': target
            })
        
        return sequences
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        seq = self.sequences[idx]
        
        return {
            'static': torch.tensor(seq['static'], dtype=torch.float32),
            'historical': torch.tensor(seq['historical'], dtype=torch.float32),
            'future': torch.tensor(seq['future'], dtype=torch.float32),
            'target': torch.tensor(seq['target'], dtype=torch.float32)
        }


def quantile_loss(predictions: torch.Tensor, targets: torch.Tensor, quantiles: List[float]) -> torch.Tensor:
    """
    Quantile loss for uncertainty estimation
    
    Args:
        predictions: [batch, horizon, num_quantiles]
        targets: [batch, horizon]
        quantiles: List of quantile levels (e.g., [0.1, 0.5, 0.9])
    
    Returns:
        Loss value
    """
    targets = targets.unsqueeze(-1)  # [batch, horizon, 1]
    
    losses = []
    for i, q in enumerate(quantiles):
        pred = predictions[:, :, i:i+1]  # [batch, horizon, 1]
        error = targets - pred
        loss = torch.max((q - 1) * error, q * error)
        losses.append(loss)
    
    return torch.cat(losses, dim=-1).mean()
