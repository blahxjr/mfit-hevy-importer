export interface ParseImportResponse {
  import_id: string;
  filename: string;
  sha256: string;
  status?: string;
  message?: string;
  workouts_count?: number;
  exercises_count?: number;
  warnings?: string[];
}

export interface NormalizeImportResponse {
  import_id: string;
  normalized_count: number;
  needs_review_count: number;
  warnings?: string[];
  error?: string;
}

export interface MapImportResponse {
  import_id: string;
  mapped_count: number;
  needs_review_count: number;
  no_match_count: number;
  mappings?: unknown[];
  error?: string;
}

export interface ReviewAlternative {
  template_id: string;
  template_title: string;
  confidence: number;
}

export interface TemplateVisualDescriptor {
  template_id: string | null;
  kind: "official_image" | "local_image" | "placeholder";
  image_url: string | null;
  local_image_url: string | null;
  alt_text: string;
  movement_icon: string;
  muscle_label: string | null;
  equipment_label: string | null;
  is_verified: boolean;
}

export interface WorkoutExerciseVisualDescriptor {
  import_id: string;
  exercise_index: number;
  template_id: string | null;
  kind: "local_image" | "generic_image" | "placeholder";
  image_url: string | null;
  local_image_url: string | null;
  alt_text: string;
  movement_icon: string;
  muscle_label: string | null;
  equipment_label: string | null;
  is_verified: boolean;
  source: "local_manual" | "generic_library" | "none";
}

export interface ReviewMapping {
  mapping_id: number | null;
  template_id: string | null;
  template_title: string | null;
  method: string | null;
  confidence: number | null;
  needs_review: boolean;
  template_visual?: TemplateVisualDescriptor | null;
}

export interface ReviewCanonicalization {
  canonical_name_en: string | null;
  search_aliases_en: string[];
  confidence: number;
  provider: string;
  needs_review: boolean;
}

export interface ReviewExercise {
  source_name: string;
  order: number;
  exercise_index: number;
  sets_raw: string | null;
  reps_raw: string | null;
  load_raw: string | null;
  rest_raw: string | null;
  techniques: string | null;
  mapping: ReviewMapping;
  canonicalization?: ReviewCanonicalization | null;
  workout_exercise_visual: WorkoutExerciseVisualDescriptor;
}

export interface HevyTemplateSearchResult {
  id: string;
  title: string;
  type?: string | null;
  primary_muscle_group?: string | null;
  equipment?: string | null;
  is_custom?: boolean;
}

export interface HevyTemplateSearchResponse {
  templates: HevyTemplateSearchResult[];
  query: string;
  count: number;
}

export interface ReviewWorkout {
  workout_name: string;
  order: number;
  status: string;
  exercises: ReviewExercise[];
}

export interface ReviewSummary {
  total_exercises: number;
  mapped_count: number;
  needs_review_count: number;
  no_match_count: number;
}

export interface ReviewResponse {
  import_id: string;
  filename: string;
  status: string;
  workouts: ReviewWorkout[];
  summary: ReviewSummary;
}

export interface ExternalAiPackageResponse {
  import_id: string;
  status: "exported";
  regenerated: boolean;
  prompt_filename: string;
  context_filename: string;
  prompt_relative_path: string;
  context_relative_path: string;
  workouts_count: number;
  exercises_count: number;
}

export interface ExternalAiValidationReport {
  valid: boolean;
  errors: string[];
  workouts_expected: number;
  workouts_received: number;
  exercises_expected: number;
  exercises_received: number;
}

export interface ExternalAiResponseImportResult {
  import_id: string;
  status: "imported" | "rejected" | "failed";
  provider?: string;
  model_name?: string | null;
  accepted_count: number;
  created_count: number;
  updated_count: number;
  rejected_count: number;
  warnings: string[];
  validation_report: ExternalAiValidationReport;
}

export type ImportStepStatus = "pending" | "processing" | "done" | "error";

export interface ImportWorkflowState {
  upload: ImportStepStatus;
  parsing: ImportStepStatus;
  normalization: ImportStepStatus;
  mapping: ImportStepStatus;
  review: ImportStepStatus;
}
