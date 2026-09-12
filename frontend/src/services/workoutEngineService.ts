import axios from "axios";
import type { WorkoutDto, WorkoutFilters, WorkoutListResponse, WorkoutSetLogDto } from "../types/workouts";

const api = axios.create({ baseURL: process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000", timeout: 30000 });

export function createWorkoutFromImport(importId: string): Promise<WorkoutDto> {
  return api.post<WorkoutDto>(`/workouts/from-import/${encodeURIComponent(importId)}`).then((response) => response.data);
}
export function createWorkoutFromHevyRoutine(routineId: string): Promise<WorkoutDto> {
  return api.post<WorkoutDto>(`/workouts/from-hevy-routine/${encodeURIComponent(routineId)}`).then((response) => response.data);
}
export function getWorkout(workoutId: string): Promise<WorkoutDto> {
  return api.get<WorkoutDto>(`/workouts/${encodeURIComponent(workoutId)}`).then((response) => response.data);
}
export function listWorkouts(filters: WorkoutFilters = {}): Promise<WorkoutListResponse> {
  const params = Object.entries(filters).filter(([, value]) => value).reduce<Record<string, string>>((result, [key, value]) => { result[key] = String(value); return result; }, {});
  return api.get<WorkoutListResponse>("/workouts", { params }).then((response) => response.data);
}
export function startWorkout(workoutId: string): Promise<WorkoutDto> {
  return api.post<WorkoutDto>(`/workouts/${encodeURIComponent(workoutId)}/start`).then((response) => response.data);
}
export function completeWorkout(workoutId: string): Promise<WorkoutDto> {
  return api.post<WorkoutDto>(`/workouts/${encodeURIComponent(workoutId)}/complete`).then((response) => response.data);
}
export function abortWorkout(workoutId: string): Promise<WorkoutDto> {
  return api.post<WorkoutDto>(`/workouts/${encodeURIComponent(workoutId)}/abort`).then((response) => response.data);
}
export function addExerciseToWorkout(workoutId: string, payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  return api.post<Record<string, unknown>>(`/workouts/${encodeURIComponent(workoutId)}/exercises`, payload).then((response) => response.data);
}
export function logSet(workoutExerciseId: string, setIndex: number, payload: Record<string, unknown>): Promise<WorkoutSetLogDto> {
  return api.post<WorkoutSetLogDto>(`/workout-exercises/${encodeURIComponent(workoutExerciseId)}/sets/log`, { ...payload, set_index: setIndex }).then((response) => response.data);
}