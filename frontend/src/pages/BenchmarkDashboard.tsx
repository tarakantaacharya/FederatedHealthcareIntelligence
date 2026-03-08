/**
 * Benchmark Dashboard (Phase 28)
 * Multi-hospital performance comparison and leaderboard
 */
import React, { useEffect, useState } from "react";
import ConsoleLayout from '../components/ConsoleLayout';
import { formatErrorMessage } from "../utils/errorMessage";
import {
  getLeaderboard,
  getRoundBenchmark,
  getHospitalProgress,
  getRoundStatistics,
} from "../services/benchmarkService";

interface LeaderboardEntry {
  rank: number;
  hospital: string;
  avg_accuracy: number;
  num_models: number;
}

interface RoundBenchmark {
  hospital: string;
  accuracy: number;
  loss: number;
  round: number;
}

interface ProgressEntry {
  round: number;
  accuracy: number;
  loss: number;
  timestamp: string;
}

interface RoundStats {
  round_number: number;
  avg_accuracy: number;
  min_accuracy: number;
  max_accuracy: number;
  avg_loss: number;
  min_loss: number;
  max_loss: number;
  num_participants: number;
}

const BenchmarkDashboard: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [roundBenchmarks, setRoundBenchmarks] = useState<RoundBenchmark[]>([]);
  const [progress, setProgress] = useState<ProgressEntry[]>([]);
  const [roundStats, setRoundStats] = useState<RoundStats | null>(null);
  const [selectedRound, setSelectedRound] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load leaderboard
      const leaderboardRes = await getLeaderboard(10);
      setLeaderboard(leaderboardRes.data);

      // Load hospital progress
      const progressRes = await getHospitalProgress();
      setProgress(progressRes.data);

      // Load round benchmarks for round 1 by default
      if (progressRes.data.length > 0) {
        const latestRound = progressRes.data[progressRes.data.length - 1].round;
        setSelectedRound(latestRound);
        await loadRoundData(latestRound);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load benchmark data");
      console.error("Error loading benchmark data:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadRoundData = async (round: number) => {
    try {
      const [benchmarkRes, statsRes] = await Promise.all([
        getRoundBenchmark(round),
        getRoundStatistics(round),
      ]);
      setRoundBenchmarks(benchmarkRes.data);
      setRoundStats(statsRes.data);
    } catch (err: any) {
      console.error("Error loading round data:", err);
    }
  };

  const handleRoundChange = (round: number) => {
    setSelectedRound(round);
    loadRoundData(round);
  };

  if (loading) {
    return (
      <ConsoleLayout title="Benchmark" subtitle="Performance comparison">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-gray-700">Loading benchmarks...</p>
        </div>
      </ConsoleLayout>
    );
  }

  return (
    <ConsoleLayout title="Benchmark" subtitle="Performance comparison">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800">
            Multi-Hospital Performance Benchmarking
          </h1>
          <p className="text-gray-600 mt-2">
            Privacy-preserving aggregated performance metrics across federated hospitals
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <strong className="font-bold">Error: </strong>
            <span>{formatErrorMessage(error)}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Leaderboard */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-purple-800 mb-4">
              Global Leaderboard
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Top 10 hospitals by average accuracy across all rounds
            </p>

            <div className="overflow-x-auto">
              <table className="table-auto w-full border-collapse">
                <thead className="bg-purple-100">
                  <tr>
                    <th className="border border-purple-300 p-3 text-left">Rank</th>
                    <th className="border border-purple-300 p-3 text-left">Hospital</th>
                    <th className="border border-purple-300 p-3 text-right">Avg Accuracy</th>
                    <th className="border border-purple-300 p-3 text-right">Models</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((entry) => (
                    <tr
                      key={entry.rank}
                      className={`hover:bg-purple-50 ${
                        entry.rank <= 3 ? "bg-yellow-50" : ""
                      }`}
                    >
                      <td className="border border-purple-200 p-3 font-bold">
                        {entry.rank === 1 && "🥇"}
                        {entry.rank === 2 && "🥈"}
                        {entry.rank === 3 && "🥉"}
                        {entry.rank > 3 && entry.rank}
                      </td>
                      <td className="border border-purple-200 p-3">{entry.hospital}</td>
                      <td className="border border-purple-200 p-3 text-right font-semibold text-green-700">
                        {(entry.avg_accuracy * 100).toFixed(2)}%
                      </td>
                      <td className="border border-purple-200 p-3 text-right text-gray-600">
                        {entry.num_models}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Hospital Progress */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-blue-800 mb-4">
              Your Performance History
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Your hospital's accuracy progression across training rounds
            </p>

            <div className="overflow-x-auto max-h-96">
              <table className="table-auto w-full border-collapse">
                <thead className="bg-blue-100 sticky top-0">
                  <tr>
                    <th className="border border-blue-300 p-3 text-left">Round</th>
                    <th className="border border-blue-300 p-3 text-right">Accuracy</th>
                    <th className="border border-blue-300 p-3 text-right">Loss</th>
                  </tr>
                </thead>
                <tbody>
                  {progress.map((entry) => (
                    <tr
                      key={entry.round}
                      className="hover:bg-blue-50 cursor-pointer"
                      onClick={() => handleRoundChange(entry.round)}
                    >
                      <td className="border border-blue-200 p-3 font-semibold">
                        Round {entry.round}
                      </td>
                      <td className="border border-blue-200 p-3 text-right text-green-700">
                        {entry.accuracy
                          ? (entry.accuracy * 100).toFixed(2) + "%"
                          : "N/A"}
                      </td>
                      <td className="border border-blue-200 p-3 text-right text-red-700">
                        {entry.loss ? entry.loss.toFixed(4) : "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Round-Specific Benchmarks */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-green-800 flex items-center">
              <span className="mr-2">🔍</span>
              Round {selectedRound} Benchmarks
            </h2>
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">Select Round:</label>
              <select
                value={selectedRound}
                onChange={(e) => handleRoundChange(Number(e.target.value))}
                className="border border-gray-300 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {progress.map((entry) => (
                  <option key={entry.round} value={entry.round}>
                    Round {entry.round}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Round Statistics */}
          {roundStats && (
            <div className="bg-green-50 p-4 rounded-lg mb-4 grid grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-600">Avg Accuracy</p>
                <p className="text-lg font-bold text-green-700">
                  {(roundStats.avg_accuracy * 100).toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Range</p>
                <p className="text-sm font-semibold text-gray-700">
                  {(roundStats.min_accuracy * 100).toFixed(1)}% -{" "}
                  {(roundStats.max_accuracy * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Avg Loss</p>
                <p className="text-lg font-bold text-red-700">
                  {roundStats.avg_loss.toFixed(4)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Participants</p>
                <p className="text-lg font-bold text-blue-700">
                  {roundStats.num_participants}
                </p>
              </div>
            </div>
          )}

          {/* Round Benchmarks Table */}
          <div className="overflow-x-auto">
            <table className="table-auto w-full border-collapse">
              <thead className="bg-green-100">
                <tr>
                  <th className="border border-green-300 p-3 text-left">Hospital</th>
                  <th className="border border-green-300 p-3 text-right">Accuracy</th>
                  <th className="border border-green-300 p-3 text-right">Loss</th>
                </tr>
              </thead>
              <tbody>
                {roundBenchmarks
                  .sort((a, b) => (b.accuracy || 0) - (a.accuracy || 0))
                  .map((entry, idx) => (
                    <tr key={idx} className="hover:bg-green-50">
                      <td className="border border-green-200 p-3">{entry.hospital}</td>
                      <td className="border border-green-200 p-3 text-right font-semibold text-green-700">
                        {entry.accuracy
                          ? (entry.accuracy * 100).toFixed(2) + "%"
                          : "N/A"}
                      </td>
                      <td className="border border-green-200 p-3 text-right text-red-700">
                        {entry.loss ? entry.loss.toFixed(4) : "N/A"}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default BenchmarkDashboard;
