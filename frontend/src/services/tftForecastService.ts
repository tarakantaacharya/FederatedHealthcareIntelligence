/**
 * TFT Forecast Service
 * STRICTLY for multi-horizon time-series forecasting
 * NO ML_REGRESSION logic - completely separate from single-point predictions
 */
import api from './api';

/**
 * Horizon Forecast (single time point with uncertainty)
 */
export interface HorizonForecast {
  timestamp: string;
  hour_ahead: number;
  p10: number;  // 10th percentile (lower bound)
  p50: number;  // 50th percentile (median)
  p90: number;  // 90th percentile (upper bound)
  confidence_level: number;
}

/**
 * TFT Forecast Request
 */
export interface TFTForecastRequest {
  model_id: number;
  encoder_sequence?: any[];  // Optional time series context
  prediction_length?: number;  // Default 72
}

/**
 * TFT Forecast Response
 */
export interface TFTForecastResponse {
  model_architecture: string;  // Always "TFT"
  model_id: number;
  training_type: string;  // LOCAL or FEDERATED
  target_column: string;
  used_dataset_id?: number;
  horizons: Record<string, HorizonForecast>;  // e.g., { "6h": {...}, "24h": {...} }
  forecast_sequence: number[];  // Full sequence for plotting
  confidence_interval: {
    lower: number[];
    upper: number[];
  };
  quality_metrics: {
    mape: number;
    bias: number;
    trend_alignment: number;
  };
  timestamp: string;
}

/**
 * TFT Model Validation Request
 */
export interface TFTModelValidationRequest {
  model_id: number;
  dataset_id?: number;
}

/**
 * TFT Model Validation Response
 */
export interface TFTModelValidationResponse {
  is_valid: boolean;
  model_id: number;
  required_time_columns: string[];
  has_timestamp_column: boolean;
  min_sequence_length_required: number;
  actual_sequence_length?: number;
  warnings: string[];
  can_proceed: boolean;
}

/**
 * TFT Forecast Save Request
 */
export interface TFTForecastSaveRequest {
  model_id: number;
  forecast_data: any;
  prediction_length: number;
  dataset_id?: number;
}

/**
 * TFT Forecast Save Response
 */
export interface TFTForecastSaveResponse {
  prediction_record_id: number;
  message: string;
  timestamp: string;
}

/**
 * TFT Forecast History Item
 */
export interface TFTForecastHistoryItem {
  id: number;
  model_id: number;
  target_column?: string;
  forecast_horizon: number;
  forecast_data: any;
  created_at: string;
}

/**
 * TFT Forecast History Response
 */
export interface TFTForecastHistoryResponse {
  forecasts: TFTForecastHistoryItem[];
  total_count: number;
}

class TFTForecastService {
  /**
   * Generate multi-horizon TFT forecast
   * POST /api/predictions/tft
   */
  async forecast(request: TFTForecastRequest): Promise<TFTForecastResponse> {
    const response = await api.post<TFTForecastResponse>('/api/predictions/tft', request);
    return response.data;
  }

  /**
   * Validate dataset compatibility with TFT model
   * POST /api/predictions/tft/validate
   */
  async validateDataset(request: TFTModelValidationRequest): Promise<TFTModelValidationResponse> {
    const response = await api.post<TFTModelValidationResponse>(
      '/api/predictions/tft/validate',
      request
    );
    return response.data;
  }

  /**
   * Save TFT forecast result
   * POST /api/predictions/tft/save
   */
  async saveForecast(request: TFTForecastSaveRequest): Promise<TFTForecastSaveResponse> {
    const response = await api.post<TFTForecastSaveResponse>(
      '/api/predictions/tft/save',
      request
    );
    return response.data;
  }

  /**
   * Get TFT forecast history
   * GET /api/predictions/tft/history
   */
  async getHistory(limit = 20): Promise<TFTForecastHistoryResponse> {
    const response = await api.get<TFTForecastHistoryResponse>(
      '/api/predictions/tft/history',
      { params: { limit } }
    );
    return response.data;
  }

  /**
   * Format MAPE as percentage
   */
  formatMAPE(mape: number): string {
    return mape.toFixed(2) + '%';
  }

  /**
   * Get quality color class for MAPE
   */
  getQualityColor(mape: number): string {
    if (mape <= 10) return 'text-green-600';
    if (mape <= 20) return 'text-yellow-600';
    return 'text-red-600';
  }

  /**
   * Format forecast value for display
   */
  formatForecast(value: number, decimals = 1): string {
    return value.toFixed(decimals);
  }

  /**
   * Extract horizon keys from forecast response
   */
  getHorizonKeys(horizons: Record<string, HorizonForecast>): string[] {
    return Object.keys(horizons).sort((a, b) => {
      const aHours = parseInt(a.replace('h', ''));
      const bHours = parseInt(b.replace('h', ''));
      return aHours - bHours;
    });
  }

  /**
   * Build chart data from forecast response for plotting
   */
  buildChartData(forecast: TFTForecastResponse) {
    const horizonKeys = this.getHorizonKeys(forecast.horizons);
    
    const labels = horizonKeys.map(key => key);
    const p50Values = horizonKeys.map(key => forecast.horizons[key].p50);
    const p10Values = horizonKeys.map(key => forecast.horizons[key].p10);
    const p90Values = horizonKeys.map(key => forecast.horizons[key].p90);
    
    return {
      labels,
      datasets: [
        {
          label: 'Forecast (Median)',
          data: p50Values,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: false,
          tension: 0.3
        },
        {
          label: 'Lower Bound (P10)',
          data: p10Values,
          borderColor: 'rgba(156, 163, 175, 0.5)',
          borderDash: [5, 5],
          fill: false,
          tension: 0.3
        },
        {
          label: 'Upper Bound (P90)',
          data: p90Values,
          borderColor: 'rgba(156, 163, 175, 0.5)',
          borderDash: [5, 5],
          fill: false,
          tension: 0.3
        }
      ]
    };
  }
}

const tftForecastService = new TFTForecastService();

export default tftForecastService;
