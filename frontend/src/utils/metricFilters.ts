/**
 * Metric Filtering Utilities for Regression-Based Platform
 * 
 * This platform is regression-based and should NOT display classification metrics like accuracy.
 * Only regression-appropriate metrics (Loss, R², RMSE, MSE, MAE, MAPE, etc.) should be shown.
 */

/**
 * List of metric keys that should be filtered out (classification metrics)
 */
const BLOCKED_METRIC_KEYS = [
  'accuracy',
  'acc',
  'classification_accuracy',
  'local_accuracy',
  'global_accuracy',
  'federated_accuracy',
  'average_accuracy',
  'avg_accuracy',
  'std_accuracy'
];

/**
 * Check if a metric key should be blocked from display
 */
export function isAccuracyMetric(key: string): boolean {
  const lowerKey = key.toLowerCase();
  return BLOCKED_METRIC_KEYS.some(blocked => lowerKey.includes(blocked));
}

/**
 * Filter out accuracy-related metrics from an object
 * Returns a new object with only regression-appropriate metrics
 */
export function filterRegressionMetrics<T extends Record<string, any>>(metrics: T): Partial<T> {
  if (!metrics || typeof metrics !== 'object') {
    return metrics;
  }

  const filtered: any = {};
  
  for (const [key, value] of Object.entries(metrics)) {
    if (!isAccuracyMetric(key)) {
      filtered[key] = value;
    }
  }
  
  return filtered as Partial<T>;
}

/**
 * Get display-friendly metric names for regression metrics
 */
export const REGRESSION_METRIC_LABELS: Record<string, string> = {
  loss: 'Loss',
  local_loss: 'Local Loss',
  global_loss: 'Global Loss',
  r2: 'R² Score',
  r2_score: 'R² Score',
  rmse: 'RMSE',
  mse: 'MSE',
  mae: 'MAE',
  mape: 'MAPE',
  local_mape: 'Local MAPE',
  global_mape: 'Global MAPE',
  bias: 'Bias',
  trend: 'Trend',
  training_loss: 'Training Loss',
  validation_loss: 'Validation Loss',
  test_loss: 'Test Loss'
};

/**
 * Check if a metric value is valid for display
 */
export function hasValidMetricValue(value: any): boolean {
  return value !== null && value !== undefined && !isNaN(Number(value));
}

/**
 * Format metric value for display
 */
export function formatMetricValue(value: number, precision: number = 4): string {
  if (!hasValidMetricValue(value)) {
    return '0.0';
  }
  return Number(value).toFixed(precision);
}
