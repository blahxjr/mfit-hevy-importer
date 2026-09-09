import axios from "axios";
import type { ExternalAiPackageResponse, ExternalAiResponseImportResult, MapImportResponse, NormalizeImportResponse, ParseImportResponse } from "../types/imports";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 120000,
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
