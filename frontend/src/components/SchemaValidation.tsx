import React, { useState } from 'react';
import predictionService from '../services/predictionService';

interface SchemaValidationProps {
  modelId: number;
  datasetId: number;
  onValidationComplete?: (result: SchemaValidationResult) => void;
}

export interface SchemaValidationResult {
  schema_match: boolean | null;
  missing_columns: string[];
  extra_columns: string[];
  warnings: string[];
  can_auto_align: boolean;
  model_schema: {
    required_columns: string[];
    excluded_columns: string[];
    target_column: string | null;
    num_features: number;
  } | null;
  dataset_schema: {
    columns: string[];
    num_columns: number;
  } | null;
}

const SchemaValidation: React.FC<SchemaValidationProps> = ({
  modelId,
  datasetId,
  onValidationComplete
}) => {
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<SchemaValidationResult | null>(null);
  const [error, setError] = useState('');

  const handleValidate = async () => {
    setValidating(true);
    setError('');
    setResult(null);

    try {
      const validationResult = await predictionService.validateSchema({
        model_id: modelId,
        dataset_id: datasetId
      });
      setResult(validationResult);
      if (onValidationComplete) {
        onValidationComplete(validationResult);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Schema validation failed.';
      setError(errorMessage);
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Schema Validation</h3>
        <button
          onClick={handleValidate}
          disabled={validating}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {validating ? 'Validating...' : 'Check Schema'}
        </button>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Validate if your dataset schema matches the model's training schema before running predictions.
      </p>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Schema Match Status */}
          <div className={`p-4 rounded-lg ${
            result.schema_match === null 
              ? 'bg-gray-100' 
              : result.schema_match 
              ? 'bg-green-100 border border-green-400' 
              : 'bg-yellow-100 border border-yellow-400'
          }`}>
            <div className="flex items-center">
              {result.schema_match === null && (
                <>
                  <svg className="w-5 h-5 text-gray-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="font-semibold text-gray-700">Schema metadata not available</span>
                </>
              )}
              {result.schema_match === true && (
                <>
                  <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="font-semibold text-green-700">Schema matches perfectly</span>
                </>
              )}
              {result.schema_match === false && (
                <>
                  <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="font-semibold text-yellow-700">Schema mismatch detected</span>
                </>
              )}
            </div>
            {result.can_auto_align && result.schema_match === false && (
              <p className="text-sm mt-2 text-yellow-700">
                ✓ Automatic alignment is available - prediction will proceed with aligned features
              </p>
            )}
          </div>

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">Alignment Warnings:</h4>
              <ul className="list-disc list-inside space-y-1">
                {result.warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-blue-800">{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Columns */}
          {result.missing_columns.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h4 className="font-semibold text-orange-900 mb-2">
                Missing Columns ({result.missing_columns.length}):
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.missing_columns.map((col, idx) => (
                  <span key={idx} className="px-2 py-1 bg-orange-200 text-orange-800 rounded text-sm">
                    {col}
                  </span>
                ))}
              </div>
              <p className="text-sm text-orange-700 mt-2">
                These columns will be added with zero values during inference.
              </p>
            </div>
          )}

          {/* Extra Columns */}
          {result.extra_columns.length > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="font-semibold text-purple-900 mb-2">
                Extra Columns ({result.extra_columns.length}):
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.extra_columns.map((col, idx) => (
                  <span key={idx} className="px-2 py-1 bg-purple-200 text-purple-800 rounded text-sm">
                    {col}
                  </span>
                ))}
              </div>
              <p className="text-sm text-purple-700 mt-2">
                These columns will be dropped during inference.
              </p>
            </div>
          )}

          {/* Schema Details */}
          {result.model_schema && result.dataset_schema && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-2">Model Schema</h4>
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Target:</span> {result.model_schema.target_column || 'N/A'}
                </p>
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Features:</span> {result.model_schema.num_features}
                </p>
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Required Columns:</span> {result.model_schema.required_columns.length}
                </p>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 mb-2">Dataset Schema</h4>
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Total Columns:</span> {result.dataset_schema.num_columns}
                </p>
                <p className="text-sm text-gray-700 mt-2">
                  <span className="font-medium">Columns:</span>
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {result.dataset_schema.columns.slice(0, 10).map((col, idx) => (
                    <span key={idx} className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                      {col}
                    </span>
                  ))}
                  {result.dataset_schema.columns.length > 10 && (
                    <span className="text-xs text-gray-500">
                      +{result.dataset_schema.columns.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SchemaValidation;
