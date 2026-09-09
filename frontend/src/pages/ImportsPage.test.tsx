import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ImportsPage from "./ImportsPage";

const mockParseMfitPdf = jest.fn();
const mockNormalizeImport = jest.fn();
const mockMapImport = jest.fn();
const mockGenerateExternalAiPackage = jest.fn();
const mockDownloadExternalAiPrompt = jest.fn();
const mockDownloadExternalAiContext = jest.fn();
const mockImportExternalAiResponse = jest.fn();

jest.mock("../services/importService", () => ({
  parseMfitPdf: (...args: unknown[]) => mockParseMfitPdf(...args),
  normalizeImport: (...args: unknown[]) => mockNormalizeImport(...args),
  mapImport: (...args: unknown[]) => mockMapImport(...args),
  generateExternalAiPackage: (...args: unknown[]) => mockGenerateExternalAiPackage(...args),
  downloadExternalAiPrompt: (...args: unknown[]) => mockDownloadExternalAiPrompt(...args),
  downloadExternalAiContext: (...args: unknown[]) => mockDownloadExternalAiContext(...args),
  importExternalAiResponse: (...args: unknown[]) => mockImportExternalAiResponse(...args),
}));

const renderPage = () => render(<BrowserRouter><ImportsPage /></BrowserRouter>);
const input = () => document.querySelector("#mfit-pdf") as HTMLInputElement;

describe("ImportsPage", () => {
  beforeEach(() => jest.clearAllMocks());

  test("renderiza o estado inicial com normalização e mapeamento desabilitados", () => {
    renderPage();
    expect(screen.getByText("Processar ficha MFIT")).toBeDisabled();
    expect(screen.queryByText("Normalizar exercícios")).not.toBeInTheDocument();
    expect(screen.getByText(/Nenhuma rotina será criada no Hevy/)).toBeInTheDocument();
  });

  test("rejeita arquivos que não sejam PDF", () => {
    renderPage();
    const invalid = new File(["not-pdf"], "ficha.txt", { type: "text/plain" });
    fireEvent.change(input(), { target: { files: [invalid] } });
    expect(screen.getByText("Selecione somente um arquivo PDF exportado do MFIT.")).toBeInTheDocument();
    expect(screen.getByText("Processar ficha MFIT")).toBeDisabled();
  });

  test("processa o PDF e habilita somente a normalização", async () => {
    mockParseMfitPdf.mockResolvedValue({
      import_id: "import-1",
      filename: "ficha.pdf",
      sha256: "1234567890abcdef",
      status: "parsed",
      workouts_count: 5,
      exercises_count: 36,
      warnings: [],
    });
    renderPage();
    const pdf = new File(["%PDF-1.4"], "ficha.pdf", { type: "application/pdf" });
    fireEvent.change(input(), { target: { files: [pdf] } });
    fireEvent.click(screen.getByText("Processar ficha MFIT"));
    expect(await screen.findByText("Normalizar exercícios")).toBeEnabled();
    expect(screen.queryByText("Mapear exercícios no Hevy")).not.toBeInTheDocument();
    expect(mockParseMfitPdf).toHaveBeenCalledWith(pdf);
  });

  test("normaliza, habilita mapeamento e navega para revisão após concluir", async () => {
    mockParseMfitPdf.mockResolvedValue({
      import_id: "import-1",
      filename: "ficha.pdf",
      sha256: "1234567890abcdef",
      status: "parsed",
      workouts_count: 5,
      exercises_count: 36,
    });
    mockNormalizeImport.mockResolvedValue({ import_id: "import-1", normalized_count: 36, needs_review_count: 3 });
    mockMapImport.mockResolvedValue({ import_id: "import-1", mapped_count: 36, needs_review_count: 33, no_match_count: 10 });
    renderPage();
    fireEvent.change(input(), { target: { files: [new File(["%PDF-1.4"], "ficha.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByText("Processar ficha MFIT"));
    fireEvent.click(await screen.findByText("Normalizar exercícios"));
    fireEvent.click(await screen.findByText("Mapear exercícios no Hevy"));
    fireEvent.click(await screen.findByText("Abrir revisão dos treinos"));
    await waitFor(() => expect(mockMapImport).toHaveBeenCalledWith("import-1"));
  });

  test("mostra upload JSON após parsing, rejeita tipo inválido e limita a 5 MB", async () => {
    mockParseMfitPdf.mockResolvedValue({ import_id: "import-1", filename: "ficha.pdf", sha256: "hash", status: "parsed" });
    renderPage();
    fireEvent.change(input(), { target: { files: [new File(["%PDF"], "ficha.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByText("Processar ficha MFIT"));

    const responseInput = await screen.findByLabelText("Resposta JSON");
    expect(screen.getByText("Importar resposta da IA externa")).toBeInTheDocument();
    expect(screen.getByText("Validar e importar resposta da IA")).toBeDisabled();
    fireEvent.change(responseInput, { target: { files: [new File(["bad"], "resposta.txt", { type: "text/plain" })] } });
    expect(screen.getByText("Selecione somente um arquivo JSON de resposta da IA externa.")).toBeInTheDocument();
    const tooLarge = new File([new Uint8Array(5 * 1024 * 1024 + 1)], "grande.json", { type: "application/json" });
    fireEvent.change(responseInput, { target: { files: [tooLarge] } });
    expect(screen.getByText("A resposta JSON deve ter no máximo 5 MB.")).toBeInTheDocument();
  });

  test("importa resposta, mostra resultado e remapeia somente via mapping", async () => {
    mockParseMfitPdf.mockResolvedValue({ import_id: "import-1", filename: "ficha.pdf", sha256: "hash", status: "parsed" });
    mockImportExternalAiResponse.mockResolvedValue({
      import_id: "import-1",
      status: "imported",
      provider: "chatgpt",
      accepted_count: 1,
      created_count: 1,
      updated_count: 0,
      rejected_count: 0,
      warnings: ["warning"],
      validation_report: { valid: true, errors: [], workouts_expected: 1, workouts_received: 1, exercises_expected: 1, exercises_received: 1 },
    });
    mockMapImport.mockResolvedValue({ import_id: "import-1", mapped_count: 1, needs_review_count: 1, no_match_count: 0 });
    renderPage();
    fireEvent.change(input(), { target: { files: [new File(["%PDF"], "ficha.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByText("Processar ficha MFIT"));
    const responseInput = await screen.findByLabelText("Resposta JSON");
    const responseFile = new File(["{}"], "resposta.json", { type: "application/json" });
    fireEvent.change(responseInput, { target: { files: [responseFile] } });
    fireEvent.click(screen.getByText("Validar e importar resposta da IA"));
    expect(await screen.findByText("Canonicalizações importadas — revisão humana ainda obrigatória")).toBeInTheDocument();
    expect(screen.getByText("chatgpt")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Refazer sugestões de exercícios"));
    await waitFor(() => expect(mockMapImport).toHaveBeenCalledWith("import-1"));
    expect(mockImportExternalAiResponse).toHaveBeenCalledWith(responseFile);
  });

  test("mantém a seção disponível para import duplicado", async () => {
    mockParseMfitPdf.mockResolvedValue({ import_id: "import-1", filename: "ficha.pdf", sha256: "hash", status: "duplicate" });
    renderPage();
    fireEvent.change(input(), { target: { files: [new File(["%PDF"], "ficha.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByText("Processar ficha MFIT"));
    expect(await screen.findByText("Importar resposta da IA externa")).toBeInTheDocument();
    expect(screen.getByText("Abrir revisão do import existente")).toBeInTheDocument();
  });
});
