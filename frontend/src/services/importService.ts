import axios from "axios";
import type { MapImportResponse, NormalizeImportResponse, ParseImportResponse } from "../types/imports";

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
