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
