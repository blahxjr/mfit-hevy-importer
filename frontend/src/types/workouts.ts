export type WorkoutStatus = "planned" | "in_progress" | "completed" | "aborted";

export interface WorkoutSetLogDto {
  id: string;
  set_index: number;
  actual_reps: number | null;
  actual_load: string | null;
  actual_time_seconds: number | null;
  actual_distance_meters: number | null;
  rpe: number | null;
  completed_at: string | null;
}

export interface WorkoutExerciseDto {
  id: string;
  exercise_id: string;
  exercise_name: string | null;
  sequence_index: number;
  planned_sets: number;
  planned_reps: number | null;
  planned_load: string | null;
  planned_time_seconds: number | null;
  planned_distance_meters: number | null;
  notes: string | null;
  set_logs: WorkoutSetLogDto[];
}

export interface WorkoutDto {
  id: string;
  import_id: string | null;
  hevy_workout_id: string | null;
  hevy_routine_id: string | null;
  name: string;
  date: string;
  status: WorkoutStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  exercises?: WorkoutExerciseDto[];
}

export interface WorkoutListResponse { workouts: WorkoutDto[]; }

export interface WorkoutFilters {
  date_from?: string;
  date_to?: string;
  status?: WorkoutStatus | "";
}