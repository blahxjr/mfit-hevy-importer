import axios from "axios";
import type { ExternalAiPackageResponse, ExternalAiResponseImportResult, HevyTemplateSearchResponse, MapImportResponse, NormalizeImportResponse, ParseImportResponse, ReviewAlternative, ReviewResponse } from "../types/imports";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 120000,
});

const reviewApi = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 30000,
});

export async function parseMfitPdf(file: File): Promise<ParseImportResponse> {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<ParseImportResponse>("/imports/parse", form)).data;
}

export async function normalizeImport(importId: string): Promise<NormalizeImportResponse> {
  return (await api.post<NormalizeImportResponse>(`/normalize/${importId}`)).data;
}

export async function mapImport(importId: string): Promise<MapImportResponse> {
  return (await api.post<MapImportResponse>(`/mapping/${importId}/map`)).data;
}

export async function generateExternalAiPackage(importId: string): Promise<ExternalAiPackageResponse> {
  return (await api.post<ExternalAiPackageResponse>(`/ai-export/${importId}`)).data;
}

async function downloadExternalAiFile(importId: string, kind: "prompt" | "context", fallbackName: string): Promise<void> {
  const response = await api.get<Blob>(`/ai-export/${importId}/download/${kind}`, { responseType: "blob" });
  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function downloadExternalAiPrompt(importId: string): Promise<void> {
  return downloadExternalAiFile(importId, "prompt", `mfit_ai_prompt_${importId}.md`);
}

export function downloadExternalAiContext(importId: string): Promise<void> {
  return downloadExternalAiFile(importId, "context", `mfit_ai_context_${importId}.json`);
}

export async function importExternalAiResponse(file: File): Promise<ExternalAiResponseImportResult> {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<ExternalAiResponseImportResult>("/ai-response/import", form)).data;
}

export function getReview(importId: string, signal?: AbortSignal): Promise<ReviewResponse> {
  return reviewApi.get<ReviewResponse>(`/review/${encodeURIComponent(importId)}`, { signal }).then((response) => response.data);
}

export function getMappingAlternatives(sourceName: string, signal?: AbortSignal): Promise<ReviewAlternative[]> {
  return reviewApi.get<{ alternatives: ReviewAlternative[] }>(`/mapping/alternatives/${encodeURIComponent(sourceName)}`, { signal }).then((response) => response.data.alternatives);
}

export function confirmMapping(mappingId: number, templateId: string): Promise<void> {
  return reviewApi.post(`/mapping/${mappingId}/confirm`, null, { params: { template_id: templateId } }).then(() => undefined);
}

export function approveReviewWorkout(importId: string, workoutOrder: number): Promise<void> {
  return reviewApi.post(`/review/${encodeURIComponent(importId)}/workouts/${workoutOrder}/approve`).then(() => undefined);
}

export function approveReview(importId: string): Promise<void> {
  return reviewApi.post(`/review/${encodeURIComponent(importId)}/approve`).then(() => undefined);
}

export function searchHevyTemplates(query: string, limit = 20): Promise<HevyTemplateSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return reviewApi.get<HevyTemplateSearchResponse>(`/catalog/templates/search?${params.toString()}`).then((response) => response.data);
}

export function getTemplateVisual(templateId: string): Promise<Record<string, unknown>> {
  return api.get<Record<string, unknown>>(`/catalog/templates/${encodeURIComponent(templateId)}/media`).then((response) => response.data);
}

export function uploadTemplateMedia(
  templateId: string,
  file: File,
  altText: string,
  source = "local_manual",
  isVerified = false,
): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append("file", file);
  form.append("alt_text", altText);
  form.append("source", source);
  form.append("is_verified", String(isVerified));
  return api.post<Record<string, unknown>>(`/catalog/templates/${encodeURIComponent(templateId)}/media/upload`, form).then((response) => response.data);
}
