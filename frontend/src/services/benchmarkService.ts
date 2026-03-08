/**
 * Benchmark Service (Phase 28)
 * API calls for multi-hospital performance comparison
 */
import api from "./api";

/**
 * Get performance benchmarks for a specific training round
 * @param round - Round number
 */
export const getRoundBenchmark = (round: number) =>
  api.get(`/api/benchmark/round/${round}`);

/**
 * Get global leaderboard of top-performing hospitals
 * @param limit - Maximum number of results (default: 10)
 */
export const getLeaderboard = (limit: number = 10) =>
  api.get(`/api/benchmark/leaderboard?limit=${limit}`);

/**
 * Get performance progression for the current hospital
 */
export const getHospitalProgress = () =>
  api.get(`/api/benchmark/hospital/progress`);

/**
 * Get aggregated statistics for a specific round
 * @param round - Round number
 */
export const getRoundStatistics = (round: number) =>
  api.get(`/api/benchmark/round/${round}/statistics`);
