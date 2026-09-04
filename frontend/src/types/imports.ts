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

export type ImportStepStatus = "pending" | "processing" | "done" | "error";

export interface ImportWorkflowState {
  upload: ImportStepStatus;
  parsing: ImportStepStatus;
  normalization: ImportStepStatus;
  mapping: ImportStepStatus;
  review: ImportStepStatus;
}
