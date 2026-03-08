import React from 'react';

type EligibilityStatus = 'eligible' | 'partial' | 'not_trained' | 'unknown';

interface ModelStatusBadgeProps {
  isTrained: boolean;
  weightsUploaded: boolean;
  maskUploaded: boolean;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  tooltip?: boolean;
}

export interface ModelStatusBadgeHandle {
  refetch: () => Promise<void>;
}

/**
 * ModelStatusBadge
 * Color-coded badge showing model eligibility status
 * - Green: Fully eligible (trained + weights + mask)
 * - Yellow: Partial (trained + weights only)
 * - Red: Not trained
 * - Gray: Unknown status
 */
export const ModelStatusBadge = React.forwardRef<
  ModelStatusBadgeHandle,
  ModelStatusBadgeProps
>(({ isTrained, weightsUploaded, maskUploaded, size = 'md', showLabel = true, tooltip = true }, ref) => {
  // Determine status
  let status: EligibilityStatus = 'unknown';
  let statusLabel = 'Unknown';
  let statusColor = 'bg-gray-100 text-gray-800';
  let statusIcon = '?';
  let tooltipText = 'Status unknown';

  if (!isTrained) {
    status = 'not_trained';
    statusLabel = 'Not Trained';
    statusColor = 'bg-red-100 text-red-800';
    statusIcon = '✕';
    tooltipText = 'Model not trained for this round';
  } else if (weightsUploaded && maskUploaded) {
    status = 'eligible';
    statusLabel = 'Eligible';
    statusColor = 'bg-green-100 text-green-800 ring-2 ring-green-300';
    statusIcon = '✓';
    tooltipText = 'Ready for aggregation (trained, weights & mask uploaded)';
  } else if (weightsUploaded) {
    status = 'partial';
    statusLabel = 'Partial';
    statusColor = 'bg-yellow-100 text-yellow-800 ring-2 ring-yellow-300';
    statusIcon = '⚠';
    tooltipText = 'Weights uploaded, but mask pending';
  } else if (isTrained) {
    status = 'partial';
    statusLabel = 'Partial';
    statusColor = 'bg-blue-100 text-blue-800';
    statusIcon = '◐';
    tooltipText = 'Model trained, weights pending';
  }

  // Size mapping
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-2 text-base'
  }[size];

  const iconSize = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  }[size];

  // Public refetch method for parent components (no-op for badge)
  React.useImperativeHandle(
    ref,
    () => ({
      refetch: () => Promise.resolve()
    })
  );

  const badge = (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold ${statusColor} ${sizeClasses} transition-all duration-200`}>
      <span className={`${iconSize} leading-none`}>{statusIcon}</span>
      {showLabel && <span>{statusLabel}</span>}
    </span>
  );

  if (tooltip) {
    return (
      <div className="relative inline-block group">
        {badge}
        <div className="absolute hidden group-hover:block bg-gray-900 text-white text-xs rounded p-2 whitespace-nowrap z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 pointer-events-none shadow-lg">
          {tooltipText}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    );
  }

  return badge;
});

ModelStatusBadge.displayName = 'ModelStatusBadge';

/**
 * ModelStatusIndicator
 * Inline status indicator with details
 */
interface ModelStatusIndicatorProps {
  isTrained: boolean;
  weightsUploaded: boolean;
  maskUploaded: boolean;
  compact?: boolean;
}

export const ModelStatusIndicator = React.forwardRef<
  ModelStatusBadgeHandle,
  ModelStatusIndicatorProps
>(({ isTrained, weightsUploaded, maskUploaded, compact = false }, ref) => {
  if (compact) {
    return (
      <ModelStatusBadge
        isTrained={isTrained}
        weightsUploaded={weightsUploaded}
        maskUploaded={maskUploaded}
        size="sm"
        tooltip={true}
      />
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <ModelStatusBadge
          isTrained={isTrained}
          weightsUploaded={weightsUploaded}
          maskUploaded={maskUploaded}
          size="md"
          showLabel={true}
        />
      </div>

      {/* Detailed status list */}
      <div className="bg-gray-50 rounded p-3 space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isTrained ? 'bg-green-500' : 'bg-gray-300'}`}></span>
          <span className={isTrained ? 'text-green-900' : 'text-gray-600'}>
            Model trained
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              weightsUploaded ? 'bg-green-500' : 'bg-gray-300'
            }`}
          ></span>
          <span className={weightsUploaded ? 'text-green-900' : 'text-gray-600'}>
            Weights uploaded
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${maskUploaded ? 'bg-green-500' : 'bg-gray-300'}`}
          ></span>
          <span className={maskUploaded ? 'text-green-900' : 'text-gray-600'}>
            Mask uploaded
          </span>
        </div>
      </div>
    </div>
  );
});

ModelStatusIndicator.displayName = 'ModelStatusIndicator';
export default ModelStatusBadge;
