export interface ExerciseDto {
  id: string;
  exercisedb_id: string | null;
  hevy_template_id: string | null;
  name: string;
  name_en: string | null;
  body_part: string | null;
  target_muscle: string | null;
  secondary_muscles: string[];
  equipment: string | null;
  movement_pattern: string | null;
  instructions: string | null;
  image_url: string | null;
  video_url: string | null;
  media_hint: string | null;
  source: "exercisedb" | "hevy_template" | "custom" | string;
}

export interface ExerciseListResponse {
  exercises: ExerciseDto[];
  count: number;
  offset: number;
  limit: number;
}

export interface ExerciseFilters {
  q?: string;
  body_part?: string;
  target?: string;
  equipment?: string;
  source?: string;
  movement_pattern?: string;
  linked?: boolean;
  limit?: number;
  offset?: number;
}