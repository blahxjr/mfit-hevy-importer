import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ReviewPage from "./ReviewPage";

const mockGetReview = jest.fn();
const mockGetMappingAlternatives = jest.fn();
const mockSearchHevyTemplates = jest.fn();
const mockConfirmMapping = jest.fn();
const mockApproveReviewWorkout = jest.fn();
const mockApproveReview = jest.fn();

jest.mock("../services/importService", () => ({
  getReview: (...args: unknown[]) => mockGetReview(...args),
  getMappingAlternatives: (...args: unknown[]) => mockGetMappingAlternatives(...args),
  searchHevyTemplates: (...args: unknown[]) => mockSearchHevyTemplates(...args),
  confirmMapping: (...args: unknown[]) => mockConfirmMapping(...args),
  approveReviewWorkout: (...args: unknown[]) => mockApproveReviewWorkout(...args),
  approveReview: (...args: unknown[]) => mockApproveReview(...args),
}));

const review = {
  import_id: "import-1",
  filename: "ficha.pdf",
  status: "parsed",
  workouts: [{
    workout_name: "A - Peito",
    order: 0,
    status: "pending",
    exercises: [{
      source_name: "Supino reto",
      order: 0,
      sets_raw: "3 x 8",
      reps_raw: "8",
      load_raw: null,
      rest_raw: "60s",
      techniques: null,
      mapping: { mapping_id: 1, template_id: null, template_title: null, method: null, confidence: null, needs_review: true },
    }],
  }],
  summary: { total_exercises: 1, mapped_count: 0, needs_review_count: 1, no_match_count: 1 },
};

function renderPage(path = "/review/import-1") {
  return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/review/:importId" element={<ReviewPage />} /><Route path="/review" element={<ReviewPage />} /></Routes></MemoryRouter>);
}

describe("ReviewPage", () => {
  beforeEach(() => jest.clearAllMocks());

  test("mostra loading completo enquanto busca a revisão", () => {
    mockGetReview.mockReturnValue(new Promise(() => undefined));
    renderPage();
    expect(screen.getByText("Carregando revisão...")).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "Carregando revisão" })).toBeInTheDocument();
  });

  test("renderiza a resposta real e mostra template nulo como sem sugestão", async () => {
    mockGetReview.mockResolvedValue(review);
    renderPage();
    expect(await screen.findByText("ficha.pdf")).toBeInTheDocument();
    expect(screen.getByText("A - Peito")).toBeInTheDocument();
    expect(screen.getByText("Supino reto")).toBeInTheDocument();
    expect(screen.getByText("Sem sugestão automática")).toBeInTheDocument();
    expect(screen.getByText("Revisar")).toBeInTheDocument();
    expect(screen.getByText(/Total de exercícios/)).toBeInTheDocument();
  });

  test("mostra erro HTTP de forma segura", async () => {
    mockGetReview.mockRejectedValue({ response: { status: 500, data: { detail: "erro interno" } } });
    renderPage();
    expect(await screen.findByText("Erro 500: erro interno")).toBeInTheDocument();
  });

  test("carrega alternativas usando somente o nome original do exercício", async () => {
    mockGetReview.mockResolvedValue(review);
    mockGetMappingAlternatives.mockResolvedValue([{ template_id: "template-1", template_title: "Bench Press", confidence: 0.91 }]);
    renderPage();
    await screen.findByText("Supino reto");
    fireEvent.click(screen.getByText("Ver alternativas"));
    expect(await screen.findByText("Bench Press (0.91)")).toBeInTheDocument();
    expect(mockGetMappingAlternatives).toHaveBeenCalledWith("Supino reto");
  });

  test("pesquisa manual no catálogo, seleciona sem confirmar e confirma explicitamente", async () => {
    mockGetReview.mockResolvedValue(review);
    mockSearchHevyTemplates.mockResolvedValue({
      templates: [{ id: "template-1", title: "Neutral Grip Lat Pulldown", type: "strength", primary_muscle_group: "back", equipment: "machine", is_custom: false }],
      query: "Lat Pulldown",
      count: 1,
    });
    mockConfirmMapping.mockResolvedValue(undefined);
    renderPage();
    await screen.findByText("Supino reto");
    const search = screen.getByPlaceholderText("Ex.: Lat Pulldown");
    fireEvent.change(search, { target: { value: "Lat Pulldown" } });
    fireEvent.click(screen.getByText("Pesquisar"));
    expect(await screen.findByText("Neutral Grip Lat Pulldown")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Selecionar"));
    expect(screen.getByText(/Seleção pendente/)).toBeInTheDocument();
    expect(mockConfirmMapping).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Confirmar mapeamento"));
    await waitFor(() => expect(mockConfirmMapping).toHaveBeenCalledWith(1, "template-1"));
  });

  test("pesquisa todos os aliases e remove duplicados", async () => {
    const withCanonicalization = { ...review, workouts: [{ ...review.workouts[0], exercises: [{ ...review.workouts[0].exercises[0], canonicalization: { canonical_name_en: "Lat Pulldown", search_aliases_en: ["Lat Pulldown", "Neutral Grip Lat Pulldown"], confidence: 0.8, provider: "chatgpt", needs_review: true } }] }] };
    mockGetReview.mockResolvedValue(withCanonicalization);
    mockSearchHevyTemplates.mockImplementation(async (query: string) => ({
      templates: query === "Lat Pulldown" ? [{ id: "same", title: "Lat Pulldown" }] : [{ id: "same", title: "Lat Pulldown" }, { id: "other", title: "Neutral Grip Lat Pulldown" }],
      query,
      count: query === "Lat Pulldown" ? 1 : 2,
    }));
    renderPage();
    await screen.findByText("Aliases: Lat Pulldown, Neutral Grip Lat Pulldown");
    fireEvent.click(screen.getByText("Pesquisar todos os aliases"));
    await waitFor(() => expect(screen.getAllByText("Lat Pulldown").length).toBeGreaterThan(0));
    expect(mockSearchHevyTemplates).toHaveBeenCalledTimes(2);
    expect(screen.getAllByText("Lat Pulldown").length).toBeLessThan(4);
  });

  test("trata import id ausente sem buscar endpoint", () => {
    renderPage("/review");
    expect(screen.getByText("Importação não informada.")).toBeInTheDocument();
    expect(mockGetReview).not.toHaveBeenCalled();
  });

  test("não chama endpoint de escrita", async () => {
    mockGetReview.mockResolvedValue(review);
    renderPage();
    await screen.findByText("Supino reto");
    expect(mockApproveReview).not.toHaveBeenCalled();
    expect(mockApproveReviewWorkout).not.toHaveBeenCalled();
    expect(mockConfirmMapping).not.toHaveBeenCalled();
    expect(mockGetReview).toHaveBeenCalledTimes(1);
  });
});
