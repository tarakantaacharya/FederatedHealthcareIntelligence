import React, { useState } from 'react';

interface ClearModelsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (deleteFiles: boolean) => Promise<void>;
  title: string;
  scope: 'local' | 'global';
  loading?: boolean;
}

const ClearModelsModal: React.FC<ClearModelsModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  scope,
  loading = false
}) => {
  const [deleteFiles, setDeleteFiles] = useState(true);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    await onConfirm(deleteFiles);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        </div>

        <div className="p-6 space-y-4">
          {scope === 'local' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                <span className="font-semibold">Local Models:</span> This will delete all trained models for your hospital only. Global federated models will NOT be affected.
              </p>
            </div>
          )}

          {scope === 'global' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-900">
                <span className="font-semibold">⚠️ ADMIN ONLY:</span> This will delete ALL global federated models from the central server. This cannot be undone.
              </p>
            </div>
          )}

          <div className="space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={deleteFiles}
                onChange={(e) => setDeleteFiles(e.target.checked)}
                disabled={loading}
                className="w-4 h-4 rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">
                Delete physical model files from disk
              </span>
            </label>
            <p className="text-xs text-gray-500 ml-7">
              Database records will be deleted. Uncheck to keep files only.
            </p>
          </div>

          <p className="text-sm text-gray-600 pt-2">
            Are you sure you want to proceed?
          </p>
        </div>

        <div className="p-6 border-t border-gray-200 flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className={`px-4 py-2 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed ${
              scope === 'global'
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Clearing...' : 'Clear Models'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ClearModelsModal;
