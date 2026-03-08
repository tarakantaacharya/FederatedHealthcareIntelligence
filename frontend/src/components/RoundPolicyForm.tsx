import React, { useState, useEffect } from 'react';
import adminService, { Hospital, RoundPolicyRequest, CanonicalField } from '../services/adminService';

interface RoundPolicyFormProps {
  onSubmit: (policy: RoundPolicyRequest) => void;
  loading?: boolean;
  error?: string;
}

const RoundPolicyForm: React.FC<RoundPolicyFormProps> = ({ onSubmit, loading = false, error = '' }) => {
  const [targetColumn, setTargetColumn] = useState('');
  const [targetSearch, setTargetSearch] = useState('');
  const [showTargetDropdown, setShowTargetDropdown] = useState(false);
  const [canonicalFields, setCanonicalFields] = useState<CanonicalField[]>([]);
  const [loadingFields, setLoadingFields] = useState(true);
  const [selectedField, setSelectedField] = useState<CanonicalField | null>(null);
  const [isEmergency, setIsEmergency] = useState(false);
  const [participationMode, setParticipationMode] = useState<'ALL' | 'SELECTIVE'>('ALL');
  const [selectionCriteria, setSelectionCriteria] = useState<'REGION' | 'SIZE' | 'EXPERIENCE' | 'MANUAL' | ''>('');
  const [selectionValue, setSelectionValue] = useState('');
  const [manualHospitals, setManualHospitals] = useState<number[]>([]);
  const [availableHospitals, setAvailableHospitals] = useState<Hospital[]>([]);
  const [loadingHospitals, setLoadingHospitals] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [modelType, setModelType] = useState<'TFT' | 'ML_REGRESSION'>('TFT');
  const [requiredCanonicalFeatures, setRequiredCanonicalFeatures] = useState<string[]>([]);
  const [requiredHyperparameters, setRequiredHyperparameters] = useState<Record<string, any>>({
    epochs: 2,
    batch_size: 32,
    learning_rate: 0.001,
  });
  const [tftHiddenSize, setTftHiddenSize] = useState<number | ''>('');
  const [tftAttentionHeads, setTftAttentionHeads] = useState<number | ''>('');
  const [tftDropout, setTftDropout] = useState<number | ''>('');
  const [tftRegularizationFactor, setTftRegularizationFactor] = useState<number | ''>('');
  const [allocatedPrivacyBudget, setAllocatedPrivacyBudget] = useState<number | ''>('');

  // Fetch canonical fields on mount
  useEffect(() => {
    const fetchFields = async () => {
      try {
        setLoadingFields(true);
        const fields = await adminService.getCanonicalFields();
        setCanonicalFields(fields);
      } catch (error) {
        console.error('Failed to fetch canonical fields:', error);
      } finally {
        setLoadingFields(false);
      }
    };
    fetchFields();
  }, []);

  // Fetch hospitals for manual selection
  useEffect(() => {
    if (selectionCriteria === 'MANUAL') {
      const fetchHospitals = async () => {
        try {
          setLoadingHospitals(true);
          const hospitals = await adminService.getAllHospitals();
          setAvailableHospitals(hospitals.filter(h => h.is_verified));
        } catch (error) {
          console.error('Failed to fetch hospitals:', error);
        } finally {
          setLoadingHospitals(false);
        }
      };
      fetchHospitals();
    }
  }, [selectionCriteria]);

  // Reset participation mode when emergency changes
  useEffect(() => {
    if (isEmergency) {
      setParticipationMode('ALL');
      setSelectionCriteria('');
      setSelectionValue('');
      setManualHospitals([]);
    }
  }, [isEmergency]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    // Validate target column (now mandatory)
    if (!targetColumn.trim()) {
      setValidationError('Please select a target column');
      return;
    }

    if (requiredCanonicalFeatures.length === 0) {
      setValidationError('Please select at least one required canonical feature');
      return;
    }

    if (requiredCanonicalFeatures.includes(targetColumn.trim())) {
      setValidationError('Required canonical features must not include target column');
      return;
    }

    // Validate SELECTIVE mode (only for non-emergency rounds)
    if (!isEmergency && participationMode === 'SELECTIVE') {
      if (!selectionCriteria) {
        setValidationError('Please select a selection criteria');
        return;
      }

      if (selectionCriteria === 'MANUAL') {
        if (manualHospitals.length === 0) {
          setValidationError('Please select at least one hospital for manual selection');
          return;
        }
      } else {
        if (!selectionValue) {
          setValidationError(`Please enter a ${selectionCriteria.toLowerCase()} value`);
          return;
        }
      }
    }

    const policy: RoundPolicyRequest = {
      target_column: targetColumn.trim(),
      is_emergency: isEmergency,
      participation_mode: participationMode,
      model_type: modelType,
      required_canonical_features: requiredCanonicalFeatures,
      required_hyperparameters: requiredHyperparameters,
      allocated_privacy_budget: allocatedPrivacyBudget === '' ? undefined : allocatedPrivacyBudget,
      tft_hidden_size: tftHiddenSize === '' ? undefined : (tftHiddenSize as number),
      tft_attention_heads: tftAttentionHeads === '' ? undefined : (tftAttentionHeads as number),
      tft_dropout: tftDropout === '' ? undefined : (tftDropout as number),
      tft_regularization_factor: tftRegularizationFactor === '' ? undefined : (tftRegularizationFactor as number),
    };

    if (participationMode === 'SELECTIVE') {
      policy.selection_criteria = selectionCriteria as any;
      if (selectionCriteria === 'MANUAL') {
        policy.manual_hospital_ids = manualHospitals;
      } else {
        policy.selection_value = selectionValue;
      }
    }

    onSubmit(policy);
  };

  const handleFieldSelect = (field: CanonicalField) => {
    setTargetColumn(field.field_name);
    setSelectedField(field);
    setTargetSearch('');
    setShowTargetDropdown(false);
  };

  const filteredFields = canonicalFields.filter(field =>
    field.field_name.toLowerCase().includes(targetSearch.toLowerCase()) ||
    (field.description && field.description.toLowerCase().includes(targetSearch.toLowerCase()))
  );

  const toggleHospitalSelection = (hospitalId: number) => {
    setManualHospitals(prev =>
      prev.includes(hospitalId)
        ? prev.filter(id => id !== hospitalId)
        : [...prev, hospitalId]
    );
  };

  const toggleRequiredFeature = (fieldName: string) => {
    setRequiredCanonicalFeatures(prev =>
      prev.includes(fieldName)
        ? prev.filter(feature => feature !== fieldName)
        : [...prev, fieldName]
    );
  };

  const moveFeature = (index: number, direction: 'up' | 'down') => {
    setRequiredCanonicalFeatures(prev => {
      const next = [...prev];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      if (targetIndex < 0 || targetIndex >= next.length) {
        return prev;
      }
      [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
      return next;
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}
      {validationError && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">{validationError}</p>
        </div>
      )}

      {/* Target Column - Searchable Dropdown */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Column *
        </label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowTargetDropdown(!showTargetDropdown)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-left bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {selectedField ? (
              <div>
                <span className="font-medium">{selectedField.field_name}</span>
                <p className="text-xs text-gray-500 mt-1">{selectedField.description}</p>
              </div>
            ) : (
              <span className="text-gray-500">Select a target column...</span>
            )}
          </button>

          {showTargetDropdown && (
            <div className="absolute top-full left-0 right-0 mt-1 border border-gray-300 rounded-lg bg-white shadow-lg z-50">
              <input
                type="text"
                placeholder="Search fields..."
                value={targetSearch}
                onChange={(e) => setTargetSearch(e.target.value)}
                className="w-full px-3 py-2 border-b border-gray-200 focus:outline-none"
                autoFocus
              />
              <div className="max-h-60 overflow-y-auto">
                {loadingFields ? (
                  <p className="p-3 text-sm text-gray-600">Loading fields...</p>
                ) : filteredFields.length === 0 ? (
                  <p className="p-3 text-sm text-gray-600">No fields found</p>
                ) : (
                  filteredFields.map(field => (
                    <button
                      key={field.id}
                      type="button"
                      onClick={() => handleFieldSelect(field)}
                      className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-b-0"
                    >
                      <div className="font-medium text-gray-900">{field.field_name}</div>
                      <div className="text-xs text-gray-600 mt-1">
                        {field.description || 'No description'}
                      </div>
                      {field.unit && (
                        <div className="text-xs text-gray-500 mt-1">
                          Unit: {field.unit}{field.category && ` • Category: ${field.category}`}
                        </div>
                      )}
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
        <p className="text-xs text-gray-600 mt-1">
          * Target column is mandatory and must be selected from approved canonical schema
        </p>
      </div>

      {/* Round Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Round Type
        </label>
        <div className="space-y-3">
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              checked={!isEmergency}
              onChange={() => setIsEmergency(false)}
              className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
            />
            <span className="ml-3 text-sm text-gray-700">
              <span className="font-medium">Ordinary Round</span>
              <p className="text-gray-500">Standard federated learning round with configurable participation</p>
            </span>
          </label>

          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              checked={isEmergency}
              onChange={() => setIsEmergency(true)}
              className="w-4 h-4 text-red-600 border-gray-300 focus:ring-red-500"
            />
            <span className="ml-3 text-sm text-gray-700">
              <span className="font-medium">🚨 Emergency Round</span>
              <p className="text-gray-500">All verified hospitals automatically included, bypasses all policies</p>
            </span>
          </label>
        </div>
      </div>

      {/* Model Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Model Architecture
        </label>
        <div className="space-y-3">
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              checked={modelType === 'TFT'}
              onChange={() => setModelType('TFT')}
              className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
            />
            <span className="ml-3 text-sm text-gray-700">
              <span className="font-medium">TFT (Temporal Fusion Transformer)</span>
              <p className="text-gray-500">Deep learning model with attention mechanism for time series (3-horizon forecast)</p>
            </span>
          </label>

          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              checked={modelType === 'ML_REGRESSION'}
              onChange={() => setModelType('ML_REGRESSION')}
              className="w-4 h-4 text-green-600 border-gray-300 focus:ring-green-500"
            />
            <span className="ml-3 text-sm text-gray-700">
              <span className="font-medium">ML_REGRESSION (Baseline)</span>
              <p className="text-gray-500">Traditional machine learning (Random Forest + feature engineering)</p>
            </span>
          </label>
        </div>
      </div>

      {/* Federated Contract - Ordered Canonical Feature Set */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-4">
        <label className="block text-sm font-medium text-gray-700">
          Required Canonical Features (Ordered) *
        </label>
        <p className="text-xs text-gray-600">
          Hospitals must match this exact canonical feature set and ordering for federated training.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-gray-200 rounded p-3 max-h-56 overflow-y-auto space-y-2">
            <p className="text-xs font-semibold text-gray-700">Available Canonical Fields</p>
            {loadingFields ? (
              <p className="text-sm text-gray-500">Loading fields...</p>
            ) : (
              canonicalFields
                .filter(field => field.field_name !== targetColumn)
                .map(field => (
                  <label key={field.id} className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={requiredCanonicalFeatures.includes(field.field_name)}
                      onChange={() => toggleRequiredFeature(field.field_name)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">{field.field_name}</span>
                  </label>
                ))
            )}
          </div>

          <div className="border border-gray-200 rounded p-3 max-h-56 overflow-y-auto space-y-2">
            <p className="text-xs font-semibold text-gray-700">Selected Order ({requiredCanonicalFeatures.length})</p>
            {requiredCanonicalFeatures.length === 0 ? (
              <p className="text-sm text-gray-500">No features selected</p>
            ) : (
              requiredCanonicalFeatures.map((feature, index) => (
                <div key={feature} className="flex items-center justify-between bg-gray-50 rounded px-2 py-1">
                  <span className="text-sm text-gray-800">{index + 1}. {feature}</span>
                  <div className="space-x-1">
                    <button type="button" onClick={() => moveFeature(index, 'up')} className="text-xs px-2 py-1 border rounded">↑</button>
                    <button type="button" onClick={() => moveFeature(index, 'down')} className="text-xs px-2 py-1 border rounded">↓</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Federated Contract - Hyperparameters */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-3">
        <label className="block text-sm font-medium text-gray-700">Required Hyperparameters *</label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <p className="text-xs text-gray-600 mb-1">Epochs</p>
            <input
              type="number"
              min="1"
              value={requiredHyperparameters.epochs}
              onChange={(e) => setRequiredHyperparameters(prev => ({ ...prev, epochs: Number(e.target.value) || 1 }))}
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Batch Size</p>
            <input
              type="number"
              min="1"
              value={requiredHyperparameters.batch_size}
              onChange={(e) => setRequiredHyperparameters(prev => ({ ...prev, batch_size: Number(e.target.value) || 1 }))}
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Learning Rate</p>
            <input
              type="number"
              min="0.0001"
              step="0.0001"
              value={requiredHyperparameters.learning_rate}
              onChange={(e) => setRequiredHyperparameters(prev => ({ ...prev, learning_rate: Number(e.target.value) || 0.0001 }))}
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* TFT-Specific Hyperparameters (Phase 42) */}
      {modelType === 'TFT' && (
        <div className="border border-blue-200 rounded-lg p-4 space-y-3 bg-blue-50">
          <label className="block text-sm font-medium text-blue-900">TFT Architecture Parameters (Optional)</label>
          <p className="text-xs text-blue-700 mb-2">
            Configure Temporal Fusion Transformer-specific hyperparameters. Leave empty for defaults.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-gray-600 mb-1">Hidden Size (Embedding Dimension)</p>
              <input
                type="number"
                min="8"
                placeholder="64"
                value={tftHiddenSize}
                onChange={(e) => setTftHiddenSize(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3 py-2 border border-blue-300 rounded"
              />
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Attention Heads</p>
              <input
                type="number"
                min="1"
                placeholder="4"
                value={tftAttentionHeads}
                onChange={(e) => setTftAttentionHeads(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3 py-2 border border-blue-300 rounded"
              />
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Dropout Rate (0.0-1.0)</p>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                placeholder="0.1"
                value={tftDropout}
                onChange={(e) => setTftDropout(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3 py-2 border border-blue-300 rounded"
              />
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Regularization Factor</p>
              <input
                type="number"
                min="0"
                step="0.0001"
                placeholder="0.01"
                value={tftRegularizationFactor}
                onChange={(e) => setTftRegularizationFactor(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3 py-2 border border-blue-300 rounded"
              />
            </div>
          </div>
        </div>
      )}

      {/* Privacy Budget Allocation */}
      <div className="border border-purple-200 rounded-lg p-4 space-y-3 bg-purple-50">
        <label className="block text-sm font-medium text-purple-900">Privacy Budget Allocation (Epsilon per Hospital)</label>
        <p className="text-xs text-purple-700 mb-2">
          Set the maximum epsilon budget each hospital can spend in this round. Leave empty for default (10.0).
        </p>
        <input
          type="number"
          min="0"
          step="0.1"
          placeholder="10.0 (default)"
          value={allocatedPrivacyBudget}
          onChange={(e) => setAllocatedPrivacyBudget(e.target.value ? Number(e.target.value) : '')}
          className="w-full px-3 py-2 border border-purple-300 rounded focus:ring-purple-500 focus:border-purple-500"
        />
      </div>

      {/* Participation Scope - Only show for Ordinary rounds */}
      {!isEmergency && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Participation Scope
          </label>
          <div className="space-y-3">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                checked={participationMode === 'ALL'}
                onChange={() => setParticipationMode('ALL')}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700">
                <span className="font-medium">All Verified Hospitals</span>
                <p className="text-gray-500">Any verified hospital can participate</p>
              </span>
            </label>

            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                checked={participationMode === 'SELECTIVE'}
                onChange={() => setParticipationMode('SELECTIVE')}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700">
                <span className="font-medium">Selective Participation</span>
                <p className="text-gray-500">Only hospitals matching selection criteria can participate</p>
              </span>
            </label>
          </div>
        </div>
      )}

      {/* Selection Criteria - Only show for SELECTIVE mode */}
      {!isEmergency && participationMode === 'SELECTIVE' && (
        <div className="border-l-4 border-blue-300 bg-blue-50 p-4 rounded space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Selection Criteria
            </label>
            <select
              value={selectionCriteria}
              onChange={(e) => {
                setSelectionCriteria(e.target.value as any);
                setSelectionValue('');
                setManualHospitals([]);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select criteria...</option>
              <option value="REGION">Geographic Region</option>
              <option value="SIZE">Hospital Size (SMALL/LARGE)</option>
              <option value="EXPERIENCE">Experience Level (NEW/EXPERIENCED)</option>
              <option value="MANUAL">Manual Hospital Selection</option>
            </select>
          </div>

          {/* Region Selection */}
          {selectionCriteria === 'REGION' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Region Value
              </label>
              <input
                type="text"
                value={selectionValue}
                onChange={(e) => setSelectionValue(e.target.value)}
                placeholder="e.g., EAST, WEST, NORTH, SOUTH"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-600 mt-1">
                Only hospitals with this region in their profile will be eligible
              </p>
            </div>
          )}

          {/* Size Selection */}
          {selectionCriteria === 'SIZE' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Size Category
              </label>
              <select
                value={selectionValue}
                onChange={(e) => setSelectionValue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select size...</option>
                <option value="SMALL">Small Hospitals</option>
                <option value="LARGE">Large Hospitals</option>
              </select>
              <p className="text-xs text-gray-600 mt-1">
                Only hospitals of this size category will be eligible
              </p>
            </div>
          )}

          {/* Experience Selection */}
          {selectionCriteria === 'EXPERIENCE' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Experience Level
              </label>
              <select
                value={selectionValue}
                onChange={(e) => setSelectionValue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select level...</option>
                <option value="NEW">New Hospitals</option>
                <option value="EXPERIENCED">Experienced Hospitals</option>
              </select>
              <p className="text-xs text-gray-600 mt-1">
                Only hospitals at this experience level will be eligible
              </p>
            </div>
          )}

          {/* Manual Selection */}
          {selectionCriteria === 'MANUAL' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Hospitals
              </label>
              {loadingHospitals ? (
                <p className="text-sm text-gray-600">Loading hospitals...</p>
              ) : (
                <div className="border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto space-y-2">
                  {availableHospitals.length === 0 ? (
                    <p className="text-sm text-gray-500">No verified hospitals available</p>
                  ) : (
                    availableHospitals.map(hospital => (
                      <label key={hospital.id} className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={manualHospitals.includes(hospital.id)}
                          onChange={() => toggleHospitalSelection(hospital.id)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="ml-3 text-sm text-gray-700">
                          {hospital.hospital_name} ({hospital.hospital_id})
                        </span>
                      </label>
                    ))
                  )}
                </div>
              )}
              <p className="text-xs text-gray-600 mt-2">
                {manualHospitals.length} hospital(s) selected
              </p>
            </div>
          )}
        </div>
      )}

      {/* Submit Button */}
      <div className="pt-4 border-t">
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
            loading
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
          }`}
        >
          {loading ? 'Creating Round...' : 'Create Round'}
        </button>
      </div>

      {/* Policy Summary */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm">
        <p className="font-medium text-gray-900 mb-2">Round Configuration Summary:</p>
        <ul className="space-y-1 text-gray-700 text-xs">
          <li>
            • Target: <span className="font-mono font-medium">{targetColumn || 'Not selected'}</span>
            {selectedField && selectedField.description && (
              <span className="text-gray-600 ml-1">({selectedField.description})</span>
            )}
          </li>
          <li>• Type: {isEmergency ? '🚨 Emergency (All verified)' : 'Ordinary'}</li>
          <li>• Model: {modelType === 'TFT' ? 'TFT (Temporal Fusion Transformer)' : 'ML_REGRESSION (Random Forest)'}</li>
          <li>• Contract Feature Count: {requiredCanonicalFeatures.length}</li>
          <li>• Contract Features (ordered): {requiredCanonicalFeatures.length > 0 ? requiredCanonicalFeatures.join(', ') : 'Not selected'}</li>
          <li>• Contract Hyperparams: epochs={requiredHyperparameters.epochs}, batch_size={requiredHyperparameters.batch_size}, learning_rate={requiredHyperparameters.learning_rate}</li>
          {!isEmergency && <li>• Scope: {participationMode === 'ALL' ? 'All verified hospitals' : 'Selective'}</li>}
          {!isEmergency && participationMode === 'SELECTIVE' && selectionCriteria && (
            <li>• Criteria: {selectionCriteria} {selectionCriteria === 'MANUAL' ? `(${manualHospitals.length} selected)` : `= ${selectionValue}`}</li>
          )}
        </ul>
      </div>
    </form>
  );
};

export default RoundPolicyForm;
