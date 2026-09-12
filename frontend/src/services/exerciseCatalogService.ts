import axios from "axios";
import type { ExerciseDto, ExerciseFilters, ExerciseListResponse } from "../types/exercises";

const api = axios.create({ baseURL: process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000", timeout: 120000 });

export function listExercises(filters: ExerciseFilters = {}): Promise<ExerciseListResponse> {
  const params = Object.entries(filters).filter(([, value]) => value !== undefined && value !== "").reduce<Record<string, string>>((result, [key, value]) => {
    result[key] = String(value);
    return result;
  }, {});
  return api.get<ExerciseListResponse>("/catalog/exercises", { params }).then((response) => response.data);
}

export function getExercise(exerciseId: string): Promise<ExerciseDto> {
  return api.get<ExerciseDto>(`/catalog/exercises/${encodeURIComponent(exerciseId)}`).then((response) => response.data);
}

export function syncExerciseDb(): Promise<Record<string, unknown>> {
  return api.post<Record<string, unknown>>("/catalog/exercises/sync").then((response) => response.data);
}