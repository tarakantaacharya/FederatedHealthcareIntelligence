/**
 * Live Predictions Page (Phase 27)
 * Real-time WebSocket streaming of prediction updates
 */
import React, { useEffect, useState } from "react";
import ConsoleLayout from '../components/ConsoleLayout';
import { formatErrorMessage } from "../utils/errorMessage";

interface PredictionUpdate {
  type: string;
  timestamp: string;
  data: {
    global_model: {
      id: number;
      round_number: number;
      model_type: string;
      created_at: string;
    } | null;
    current_round: {
      round_number: number;
      status: string;
      num_participating_hospitals: number;
      average_loss: number | null;
      started_at: string;
      completed_at: string | null;
    } | null;
    system_status: string;
    active_connections: number;
  };
}

const LivePredictions: React.FC = () => {
  const [data, setData] = useState<PredictionUpdate | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    
    if (!token) {
      setError("No authentication token found. Please login.");
      return;
    }

    // Establish WebSocket connection
    const ws = new WebSocket(
      `ws://localhost:8000/ws/predictions?token=${token}`
    );

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log("[WebSocket] Connected to prediction stream");
    };

    ws.onmessage = (event) => {
      try {
        const message: PredictionUpdate = JSON.parse(event.data);
        if (message.type === "prediction_update") {
          setData(message);
        }
      } catch (err) {
        console.error("[WebSocket] Parse error:", err);
      }
    };

    ws.onerror = (event) => {
      console.error("[WebSocket] Error:", event);
      setError("WebSocket connection error");
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log("[WebSocket] Connection closed");
      setIsConnected(false);
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  return (
    <ConsoleLayout title="Live Predictions" subtitle="Real-time model stream">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Live Predictions Stream</h2>
            <div className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full mr-2 ${
                  isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
                }`}
              ></div>
              <span className="text-sm text-gray-600">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <strong className="font-bold">Error: </strong>
              <span>{formatErrorMessage(error)}</span>
            </div>
          )}

          {/* Data Display */}
          {data ? (
            <div className="space-y-4">
              {/* Global Model Info */}
              {data.data.global_model && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-blue-800 mb-2">
                    Global Model
                  </h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Model ID:</span>{" "}
                      <span className="text-gray-900">{data.data.global_model.id}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Round:</span>{" "}
                      <span className="text-gray-900">{data.data.global_model.round_number}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Type:</span>{" "}
                      <span className="text-gray-900">{data.data.global_model.model_type}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Created:</span>{" "}
                      <span className="text-gray-900">
                        {new Date(data.data.global_model.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Round Info */}
              {data.data.current_round && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-green-800 mb-2">
                    Current Training Round
                  </h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Round #:</span>{" "}
                      <span className="text-gray-900">{data.data.current_round.round_number}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Status:</span>{" "}
                      <span className={`font-semibold ${
                        data.data.current_round.status === 'completed' ? 'text-green-600' :
                        data.data.current_round.status === 'in_progress' ? 'text-yellow-600' :
                        'text-gray-600'
                      }`}>
                        {data.data.current_round.status.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Hospitals:</span>{" "}
                      <span className="text-gray-900">
                        {data.data.current_round.num_participating_hospitals}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Avg Loss:</span>{" "}
                      <span className="text-gray-900">
                        {data.data.current_round.average_loss?.toFixed(4) || "N/A"}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* System Status */}
              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-purple-800 mb-2">
                  ⚡ System Status
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Status:</span>{" "}
                    <span className="text-green-600 font-semibold">
                      {data.data.system_status.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Active Connections:</span>{" "}
                    <span className="text-gray-900">{data.data.active_connections}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Last Update:</span>{" "}
                    <span className="text-gray-900">
                      {new Date(parseFloat(data.timestamp) * 1000).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Raw Data (Debug) */}
              <details className="bg-gray-50 p-4 rounded-lg">
                <summary className="cursor-pointer text-sm font-medium text-gray-700">
                  🔍 Raw Data (JSON)
                </summary>
                <pre className="mt-2 text-xs bg-gray-100 p-3 rounded overflow-x-auto">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Waiting for data stream...</p>
            </div>
          )}
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default LivePredictions;
