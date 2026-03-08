/**
 * Debug Component for Prediction Detail
 * Logs actual data structures to help diagnose rendering issues
 */

export function logPredictionData(prediction: any, label: string = 'Prediction') {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`DEBUG: ${label}`);
  console.log(`${'='.repeat(60)}`);

  // Log basic info
  console.log('Prediction ID:', prediction.id);
  console.log('Target Column:', prediction.target_column);
  console.log('Forecast Horizon:', prediction.forecast_horizon);
  console.log('Prediction Value:', prediction.prediction_value);

  // Log forecast_data structure
  console.log('\nForecast Data Structure:');
  console.log('  forecast_data type:', typeof prediction.forecast_data);
  if (prediction.forecast_data) {
    console.log('  forecast_data keys:', Object.keys(prediction.forecast_data));

    // Check each possible format
    if (prediction.forecast_data.forecasts) {
      console.log('  ✓ Has "forecasts" array:');
      console.log('    Length:', Array.isArray(prediction.forecast_data.forecasts) ? prediction.forecast_data.forecasts.length : 'not an array');
      if (Array.isArray(prediction.forecast_data.forecasts) && prediction.forecast_data.forecasts.length > 0) {
        console.log('    First item:', prediction.forecast_data.forecasts[0]);
      }
    }

    if (prediction.forecast_data.horizon_forecasts) {
      console.log('  ✓ Has "horizon_forecasts" object:');
      console.log('    Keys:', Object.keys(prediction.forecast_data.horizon_forecasts));
      const firstKey = Object.keys(prediction.forecast_data.horizon_forecasts)[0];
      if (firstKey) {
        console.log(`    Sample "${firstKey}":`, prediction.forecast_data.horizon_forecasts[firstKey]);
      }
    }

    if (prediction.forecast_data.horizons) {
      console.log('  ✓ Has "horizons" object:');
      console.log('    Keys:', Object.keys(prediction.forecast_data.horizons));
      const firstKey = Object.keys(prediction.forecast_data.horizons)[0];
      if (firstKey) {
        console.log(`    Sample "${firstKey}":`, prediction.forecast_data.horizons[firstKey]);
      }
    }

    if (prediction.forecast_data.ai_summary) {
      console.log('  ✓ Has "ai_summary":', prediction.forecast_data.ai_summary.substring(0, 100) + '...');
    }
  }

  // Log metrics
  console.log('\nMetrics:');
  if (prediction.forecast_data?.quality_metrics) {
    console.log('  quality_metrics:', prediction.forecast_data.quality_metrics);
  }
  if (prediction.performance_metrics) {
    console.log('  performance_metrics:', prediction.performance_metrics);
  }
  if (prediction.forecast_data?.regression_metrics) {
    console.log('  regression_metrics:', prediction.forecast_data.regression_metrics);
  }

  // Log governance
  console.log('\nGovernance:');
  if (prediction.governance) {
    console.log('  governance:', prediction.governance);
  }

  console.log(`${'='.repeat(60)}\n`);
}

export function analyzeVisualizations(prediction: any) {
  console.log('\nVISUALIZATION ANALYSIS:');

  let visualizationForecasts: any[] = [];

  if (Array.isArray(prediction.forecast_data?.forecasts) && prediction.forecast_data.forecasts.length > 0) {
    console.log('  ✓ Using "forecasts" array format');
    visualizationForecasts = prediction.forecast_data.forecasts;
  } else if (prediction.forecast_data?.horizon_forecasts && typeof prediction.forecast_data.horizon_forecasts === 'object') {
    const entries = Object.entries(prediction.forecast_data.horizon_forecasts);
    if (entries.length > 0) {
      console.log('  ✓ Using "horizon_forecasts" dict format');
      visualizationForecasts = entries.map(([key, data]: [string, any]) => ({
        hour_ahead: parseInt(String(key).replace('h', '') || '0', 10),
        prediction: data?.prediction,
        lower_bound: data?.lower_bound,
        upper_bound: data?.upper_bound,
        confidence_level: data?.confidence_level || 0.95,
        timestamp: data?.timestamp,
      }));
    }
  }

  if (visualizationForecasts.length === 0 && prediction.forecast_data?.horizons && typeof prediction.forecast_data.horizons === 'object') {
    const entries = Object.entries(prediction.forecast_data.horizons);
    if (entries.length > 0) {
      console.log('  ✓ Using "horizons" dict format (TFT)');
      visualizationForecasts = entries.map(([key, data]: [string, any]) => ({
        hour_ahead: parseInt(String(key).replace('h', '') || '0', 10),
        prediction: data?.p50,
        lower_bound: data?.p10,
        upper_bound: data?.p90,
        confidence_level: data?.confidence_level || 0.8,
        timestamp: data?.timestamp,
      }));
    }
  }

  if (visualizationForecasts.length === 0) {
    console.log('  ✗ NO forecast data found in any format!');
    return;
  }

  console.log(`  Total entries: ${visualizationForecasts.length}`);

  const cleanForecasts = visualizationForecasts
    .filter((item: any) => Number.isFinite(Number(item?.hour_ahead)) && Number.isFinite(Number(item?.prediction)))
    .sort((a: any, b: any) => a.hour_ahead - b.hour_ahead);

  console.log(`  After filtering: ${cleanForecasts.length} valid entries`);

  if (cleanForecasts.length > 0) {
    console.log('  ✓ Valid forecasts found - charts WILL render');
    console.log('  Sample entries:', cleanForecasts.slice(0, 3));
  } else {
    console.log('  ✗ NO valid forecasts after filtering:');
    console.log('  Validation failures:');
    visualizationForecasts.forEach((item, idx) => {
      const hasValidHour = Number.isFinite(Number(item?.hour_ahead));
      const hasValidPred = Number.isFinite(Number(item?.prediction));
      if (!hasValidHour || !hasValidPred) {
        console.log(`    Entry ${idx}: hour_ahead=${item?.hour_ahead} (valid=${hasValidHour}), prediction=${item?.prediction} (valid=${hasValidPred})`);
      }
    });
  }
}

// Usage in PredictionDetail.tsx:
// import { logPredictionData, analyzeVisualizations } from '@/components/PredictionDetailDebug';
// useEffect(() => {
//   if (prediction) {
//     logPredictionData(prediction);
//     analyzeVisualizations(prediction);
//   }
// }, [prediction]);
