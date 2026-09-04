import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ImportsPage from "./ImportsPage";

const parseMfitPdf = jest.fn();
const normalizeImport = jest.fn();
const mapImport = jest.fn();

jest.mock("../services/importService", () => ({
  parseMfitPdf: (...args: unknown[]) => parseMfitPdf(...args),
  normalizeImport: (...args: unknown[]) => normalizeImport(...args),
  mapImport: (...args: unknown[]) => mapImport(...args),
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
    parseMfitPdf.mockResolvedValue({
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
    expect(parseMfitPdf).toHaveBeenCalledWith(pdf);
  });

  test("normaliza, habilita mapeamento e navega para revisão após concluir", async () => {
    parseMfitPdf.mockResolvedValue({
      import_id: "import-1",
      filename: "ficha.pdf",
      sha256: "1234567890abcdef",
      status: "parsed",
      workouts_count: 5,
      exercises_count: 36,
    });
    normalizeImport.mockResolvedValue({ import_id: "import-1", normalized_count: 36, needs_review_count: 3 });
    mapImport.mockResolvedValue({ import_id: "import-1", mapped_count: 36, needs_review_count: 33, no_match_count: 10 });
    renderPage();
    fireEvent.change(input(), { target: { files: [new File(["%PDF-1.4"], "ficha.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByText("Processar ficha MFIT"));
    fireEvent.click(await screen.findByText("Normalizar exercícios"));
    fireEvent.click(await screen.findByText("Mapear exercícios no Hevy"));
    fireEvent.click(await screen.findByText("Abrir revisão dos treinos"));
    await waitFor(() => expect(mapImport).toHaveBeenCalledWith("import-1"));
  });
});
