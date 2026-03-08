type NullableNumber = number | null;

export interface PredictionAnalysisInput {
  predictionId: number;
  modelType?: string;
  datasetName?: string;
  predictionHorizon?: number;
  metrics: {
    r2: NullableNumber;
    mae: NullableNumber;
    mse: NullableNumber;
    rmse: NullableNumber;
    loss: NullableNumber;
    mape: NullableNumber;
    bias?: NullableNumber;
    trend_alignment?: NullableNumber;
  };
  predictedValues: number[];
  actualValues?: number[];
  targetVariable?: string;
  isTFT?: boolean;
  tftHorizons?: Record<string, any>;
  forecastSequence?: number[];
  confidenceInterval?: {
    lower: number[];
    upper: number[];
  };
}

class PredictionAiAnalysisService {
  private readonly apiKey = process.env.REACT_APP_GEMINI_API_KEY;
  private readonly model = process.env.REACT_APP_GEMINI_MODEL || 'gemini-2.0-flash';

  isConfigured(): boolean {
    return Boolean(this.apiKey);
  }

  buildCacheKey(input: PredictionAnalysisInput): string {
    const signature = JSON.stringify({
      predictionId: input.predictionId,
      modelType: input.modelType || 'unknown',
      datasetName: input.datasetName || 'unknown',
      predictionHorizon: input.predictionHorizon || null,
      metrics: input.metrics,
      predictedLength: input.predictedValues.length,
      actualLength: input.actualValues?.length || 0,
      predictedHead: input.predictedValues.slice(0, 8),
      actualHead: input.actualValues?.slice(0, 8) || [],
    });

    return `prediction_ai_analysis_${input.predictionId}_${this.hashString(signature)}`;
  }

  async generateAnalysis(input: PredictionAnalysisInput): Promise<string> {
    if (!this.apiKey) {
      throw new Error('Gemini API key is not configured');
    }

    const prompt = this.buildPrompt(input);
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent?key=${this.apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [
            {
              role: 'user',
              parts: [{ text: prompt }],
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Gemini request failed: ${response.status} ${text}`);
    }

    const data = await response.json();
    const parts = data?.candidates?.[0]?.content?.parts;
    if (!Array.isArray(parts)) {
      throw new Error('Gemini response did not include text content');
    }

    const text = parts
      .map((part: any) => (typeof part?.text === 'string' ? part.text : ''))
      .join('\n')
      .trim();

    if (!text) {
      throw new Error('Gemini response was empty');
    }

    return text;
  }

  private buildPrompt(input: PredictionAnalysisInput): string {
    if (input.isTFT) {
      return this.buildTFTPrompt(input);
    }

    const predictedPreview = this.limitArray(input.predictedValues);
    const actualPreview = this.limitArray(input.actualValues || []);

    return [
      'Analyze the following regression prediction results and provide a clear professional report.',
      '',
      'Return the response in this exact section order:',
      '1) Model Performance Summary',
      '2) R2 Score Interpretation',
      '3) Error Analysis (MAE and RMSE)',
      '4) Model Stability Assessment',
      '5) Risk Indicators',
      '6) Prediction Distribution Observations',
      '7) Overall Reliability Assessment',
      '',
      'Context:',
      `Model type: ${input.modelType || 'N/A'}`,
      `Dataset name: ${input.datasetName || 'N/A'}`,
      `Prediction horizon: ${input.predictionHorizon ?? 'N/A'}`,
      '',
      'Metrics:',
      `R2: ${this.formatMetric(input.metrics.r2)}`,
      `MAE: ${this.formatMetric(input.metrics.mae)}`,
      `MSE: ${this.formatMetric(input.metrics.mse)}`,
      `RMSE: ${this.formatMetric(input.metrics.rmse)}`,
      `Loss: ${this.formatMetric(input.metrics.loss)}`,
      `MAPE: ${this.formatMetric(input.metrics.mape)}`,
      '',
      `Prediction values (${input.predictedValues.length}): ${JSON.stringify(predictedPreview)}`,
      `Actual values (${(input.actualValues || []).length}): ${JSON.stringify(actualPreview)}`,
      '',
      'Important rules:',
      '- This is a regression model.',
      '- Do not mention classification accuracy.',
      '- Focus only on R2, MAE, MSE, RMSE, Loss, and MAPE where available.',
      '- If a metric is N/A, state limitations clearly without inventing values.',
    ].join('\n');
  }

  private buildTFTPrompt(input: PredictionAnalysisInput): string {
    const forecastPreview = this.limitArray(input.forecastSequence || input.predictedValues);
    const lowerBounds = this.limitArray(input.confidenceInterval?.lower || []);
    const upperBounds = this.limitArray(input.confidenceInterval?.upper || []);

    const horizonInfo = input.tftHorizons
      ? Object.entries(input.tftHorizons)
          .slice(0, 6)
          .map(([key, val]: [string, any]) => `${key}: p50=${val.p50?.toFixed(2)}, range=[${val.p10?.toFixed(2)}, ${val.p90?.toFixed(2)}]`)
          .join('\n  ')
      : 'N/A';

    return [
      'Analyze the following Temporal Fusion Transformer (TFT) forecasting results and provide a professional analysis report.',
      '',
      'Return the response in this exact section order:',
      '1) Model Performance Interpretation',
      '2) Error Evaluation (MAPE, Bias)',
      '3) Forecast Reliability Assessment',
      '4) Trend Observations',
      '5) Potential Anomalies',
      '6) Healthcare Forecasting Insights',
      '7) Overall Reliability and Recommendations',
      '',
      'Context:',
      `Model: Temporal Fusion Transformer (TFT)`,
      `Target Variable: ${input.targetVariable || 'N/A'}`,
      `Prediction Horizon: ${input.predictionHorizon ?? 'N/A'} hours`,
      `Dataset: ${input.datasetName || 'N/A'}`,
      '',
      'Metrics:',
      `MAPE: ${this.formatMetric(input.metrics.mape)}%`,
      `Bias: ${this.formatMetric(input.metrics.bias)}`,
      `Trend Alignment: ${this.formatMetric(input.metrics.trend_alignment)}`,
      `R2: ${this.formatMetric(input.metrics.r2)}`,
      `MAE: ${this.formatMetric(input.metrics.mae)}`,
      `RMSE: ${this.formatMetric(input.metrics.rmse)}`,
      `MSE: ${this.formatMetric(input.metrics.mse)}`,
      '',
      'Forecast Data:',
      `Multi-horizon forecasts:`,
      `  ${horizonInfo}`,
      '',
      `Forecast sequence (${forecastPreview.length} values): ${JSON.stringify(forecastPreview)}`,
      lowerBounds.length > 0 ? `Confidence lower bounds: ${JSON.stringify(lowerBounds)}` : '',
      upperBounds.length > 0 ? `Confidence upper bounds: ${JSON.stringify(upperBounds)}` : '',
      '',
      'Important rules:',
      '- This is a time-series regression forecasting model.',
      '- Do NOT mention classification accuracy anywhere.',
      '- Focus on MAPE, Bias, Trend Alignment, and other regression metrics.',
      '- Interpret uncertainty bands (p10-p90 range).',
      '- Provide healthcare-specific insights for resource planning.',
      '- If a metric is N/A, acknowledge the limitation clearly.',
    ].filter(Boolean).join('\n');
  }

  private formatMetric(value: NullableNumber | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return 'N/A';
    }
    return Number(value).toFixed(6);
  }

  private limitArray(values: number[]): number[] {
    if (!Array.isArray(values)) {
      return [];
    }
    return values
      .filter((value) => Number.isFinite(value))
      .slice(0, 200);
  }

  private hashString(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i += 1) {
      hash = (hash << 5) - hash + input.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash).toString(36);
  }
}

const predictionAiAnalysisService = new PredictionAiAnalysisService();

export default predictionAiAnalysisService;