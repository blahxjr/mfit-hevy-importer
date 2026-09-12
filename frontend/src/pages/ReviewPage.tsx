import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Col, Container, Row, Spinner } from "react-bootstrap";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import {
  approveReview,
  approveReviewWorkout,
  confirmMapping,
  getMappingAlternatives,
  getReview,
  searchHevyTemplates,
} from "../services/importService";
import type { HevyTemplateSearchResult, ReviewAlternative, ReviewExercise, ReviewResponse, ReviewWorkout, TemplateVisualDescriptor } from "../types/imports";
import { ExerciseVisualCard } from "../components/ExerciseVisualCard";
import { MfitPdfViewer } from "../components/MfitPdfViewer";
import { WorkoutExerciseImageEditor } from "../components/WorkoutExerciseImageEditor";

type AlternativeState = {
  items: ReviewAlternative[];
  loading: boolean;
  error: string;
};

function safeErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.length <= 300) {
      return status ? `Erro ${status}: ${detail}` : detail;
    }
    return status ? `Erro ${status}: não foi possível concluir a solicitação.` : "Não foi possível concluir a solicitação.";
  }
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = error.response as { status?: number; data?: { detail?: unknown } } | undefined;
    const detail = response?.data?.detail;
    if (typeof detail === "string" && detail.length <= 300) {
      return response?.status ? `Erro ${response.status}: ${detail}` : detail;
    }
  }
  return "Não foi possível concluir a solicitação.";
}

function mappingConfidence(value: number | null): string {
  return typeof value === "number" ? value.toFixed(2) : "—";
}

function exerciseKey(workout: ReviewWorkout, exercise: ReviewExercise): string {
  return `${workout.order}-${exercise.order}`;
}

function placeholderVisualFromTemplate(template: Pick<HevyTemplateSearchResult, "id" | "title" | "primary_muscle_group" | "equipment">): TemplateVisualDescriptor {
  return {
    template_id: template.id,
    kind: "placeholder",
    image_url: null,
    local_image_url: null,
    alt_text: `Imagem de referência para ${template.title}`,
    movement_icon: "bi-card-image",
    muscle_label: template.primary_muscle_group ?? null,
    equipment_label: template.equipment ?? null,
    is_verified: false,
  };
}

function placeholderWorkoutVisual(importId: string, exerciseIndex: number, title: string) {
  return {
    import_id: importId,
    exercise_index: exerciseIndex,
    template_id: null,
    kind: "placeholder" as const,
    image_url: null,
    local_image_url: null,
    alt_text: `Imagem de referência para ${title}`,
    movement_icon: "bi-card-image",
    muscle_label: null,
    equipment_label: null,
    is_verified: false,
    source: "none" as const,
  };
}

export function ReviewPage() {
  const { importId } = useParams<{ importId: string }>();
  const navigate = useNavigate();
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [alternatives, setAlternatives] = useState<Record<string, AlternativeState>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const [manualQueryByExerciseId, setManualQueryByExerciseId] = useState<Record<string, string>>({});
  const [searchResultsByExerciseId, setSearchResultsByExerciseId] = useState<Record<string, HevyTemplateSearchResult[]>>({});
  const [searchLoadingByExerciseId, setSearchLoadingByExerciseId] = useState<Record<string, boolean>>({});
  const [searchErrorByExerciseId, setSearchErrorByExerciseId] = useState<Record<string, string | null>>({});
  const [selectedTemplateByExerciseId, setSelectedTemplateByExerciseId] = useState<Record<string, string | null>>({});

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    if (!importId) {
      setLoading(false);
      setError("Importação não informada.");
      return () => {
        active = false;
        controller.abort();
      };
    }

    setLoading(true);
    setError("");
    getReview(importId, controller.signal)
      .then((data) => {
        if (active) setReview(data);
      })
      .catch((caught: unknown) => {
        if (active && !axios.isCancel(caught)) {
          setError(safeErrorMessage(caught));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [importId]);

  const loadAlternatives = async (workout: ReviewWorkout, exercise: ReviewExercise) => {
    const key = exerciseKey(workout, exercise);
    setAlternatives((current) => ({ ...current, [key]: { items: [], loading: true, error: "" } }));
    try {
      const items = await getMappingAlternatives(exercise.source_name);
      setAlternatives((current) => ({ ...current, [key]: { items, loading: false, error: "" } }));
    } catch (caught) {
      setAlternatives((current) => ({ ...current, [key]: { items: [], loading: false, error: safeErrorMessage(caught) } }));
    }
  };

  const canonicalQuery = (exercise: ReviewExercise): string => exercise.canonicalization?.canonical_name_en || exercise.source_name;

  const searchManual = async (workout: ReviewWorkout, exercise: ReviewExercise, queryOverride?: string) => {
    const key = exerciseKey(workout, exercise);
    const query = (queryOverride ?? manualQueryByExerciseId[key] ?? canonicalQuery(exercise)).trim();
    setManualQueryByExerciseId((current) => ({ ...current, [key]: query }));
    if (query.length < 2) {
      setSearchErrorByExerciseId((current) => ({ ...current, [key]: "Digite pelo menos 2 caracteres." }));
      return;
    }
    setSearchLoadingByExerciseId((current) => ({ ...current, [key]: true }));
    setSearchErrorByExerciseId((current) => ({ ...current, [key]: null }));
    try {
      const response = await searchHevyTemplates(query, 20);
      setSearchResultsByExerciseId((current) => ({ ...current, [key]: response.templates }));
    } catch (caught) {
      setSearchErrorByExerciseId((current) => ({ ...current, [key]: safeErrorMessage(caught) }));
    } finally {
      setSearchLoadingByExerciseId((current) => ({ ...current, [key]: false }));
    }
  };

  const searchAliases = async (workout: ReviewWorkout, exercise: ReviewExercise) => {
    const aliases = exercise.canonicalization?.search_aliases_en || [];
    const key = exerciseKey(workout, exercise);
    if (aliases.length === 0) return searchManual(workout, exercise);
    setSearchLoadingByExerciseId((current) => ({ ...current, [key]: true }));
    setSearchErrorByExerciseId((current) => ({ ...current, [key]: null }));
    try {
      const responses = await Promise.all(aliases.map((alias) => searchHevyTemplates(alias, 20)));
      const unique = new Map<string, HevyTemplateSearchResult>();
      responses.flatMap((response) => response.templates).forEach((template) => unique.set(template.id, template));
      setSearchResultsByExerciseId((current) => ({ ...current, [key]: Array.from(unique.values()) }));
    } catch (caught) {
      setSearchErrorByExerciseId((current) => ({ ...current, [key]: safeErrorMessage(caught) }));
    } finally {
      setSearchLoadingByExerciseId((current) => ({ ...current, [key]: false }));
    }
  };

  const confirm = async (exercise: ReviewExercise, templateId: string) => {
    if (exercise.mapping.mapping_id === null) return;
    const key = String(exercise.mapping.mapping_id);
    setSaving(key);
    setActionError("");
    try {
      await confirmMapping(exercise.mapping.mapping_id, templateId);
      if (importId) setReview(await getReview(importId));
    } catch (caught) {
      setActionError(safeErrorMessage(caught));
    } finally {
      setSaving(null);
    }
  };

  const confirmSelected = async (exercise: ReviewExercise, key: string) => {
    const templateId = selectedTemplateByExerciseId[key];
    if (!templateId) return;
    await confirm(exercise, templateId);
    setSelectedTemplateByExerciseId((current) => ({ ...current, [key]: null }));
  };

  const approveWorkout = async (workout: ReviewWorkout) => {
    if (!importId) return;
    setActionError("");
    try {
      await approveReviewWorkout(importId, workout.order);
      setReview(await getReview(importId));
    } catch (caught) {
      setActionError(safeErrorMessage(caught));
    }
  };

  const approve = async () => {
    if (!importId) return;
    setActionError("");
    try {
      await approveReview(importId);
      navigate(`/imports/${importId}/payload`);
    } catch (caught) {
      setActionError(safeErrorMessage(caught));
    }
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" role="status" aria-label="Carregando revisão" />
        <p className="mt-3">Carregando revisão...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-4">
        <Alert variant="danger"><strong>Não foi possível carregar a revisão.</strong><div>{error}</div></Alert>
      </Container>
    );
  }

  if (!review) {
    return <Container className="py-4"><Alert variant="warning">Não há dados de revisão disponíveis.</Alert></Container>;
  }

  const canApprove = review.workouts.length > 0 && review.workouts.every((workout) => workout.status === "approved" || workout.status === "completed");

  return (
    <Container className="py-4">
      <div className="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h1>Revisar importação</h1>
          <p className="text-muted mb-0">Confira cada sugestão antes de qualquer aprovação.</p>
        </div>
        <Badge bg={review.status === "completed" ? "success" : "secondary"}>{review.status}</Badge>
      </div>

      {actionError && <Alert variant="danger">{actionError}</Alert>}
      <Card className="mb-4">
        <Card.Body>
          <Row>
            <Col md={6}><p><strong>Arquivo:</strong> {review.filename}</p><p><strong>Import ID:</strong> <code>{review.import_id}</code></p></Col>
            <Col md={6}><p><strong>Status:</strong> {review.status}</p><p><strong>Total de exercícios:</strong> {review.summary.total_exercises}</p></Col>
          </Row>
          <div className="d-flex flex-wrap gap-3">
            <span><strong>Mapeados:</strong> {review.summary.mapped_count}</span>
            <span><strong>Precisam de revisão:</strong> {review.summary.needs_review_count}</span>
            <span><strong>Sem match:</strong> {review.summary.no_match_count}</span>
          </div>
        </Card.Body>
      </Card>
      {importId && <Card className="mb-4"><Card.Body><MfitPdfViewer importId={importId} /></Card.Body></Card>}

      {review.workouts.length === 0 ? (
        <Alert variant="info">Não há treinos nesta importação.</Alert>
      ) : review.workouts.map((workout) => (
        <Card className="mb-3" key={workout.order}>
          <Card.Header className="d-flex justify-content-between align-items-center">
            <strong>{workout.workout_name}</strong>
            <Badge bg={workout.status === "approved" || workout.status === "completed" ? "success" : "secondary"}>{workout.status}</Badge>
          </Card.Header>
          <Card.Body>
            {workout.exercises.map((exercise) => {
              const key = exerciseKey(workout, exercise);
              const alternativeState = alternatives[key];
              const workoutVisual = exercise.workout_exercise_visual ?? placeholderWorkoutVisual(importId ?? review.import_id, exercise.exercise_index ?? exercise.order, exercise.source_name);
              return (
                <div className="border rounded p-3 mb-3" key={key}>
                  <div className="d-flex justify-content-between align-items-start">
                    <strong>{exercise.source_name}</strong>
                    <Badge bg={exercise.mapping.needs_review ? "warning" : "success"}>{exercise.mapping.needs_review ? "Revisar" : "Confirmado"}</Badge>
                  </div>
                  <div className="small text-muted mt-2">
                    <div>Séries: {exercise.sets_raw ?? "—"} · Repetições: {exercise.reps_raw ?? "—"}</div>
                    <div>Carga: {exercise.load_raw ?? "—"} · Descanso: {exercise.rest_raw ?? "—"}</div>
                    {exercise.techniques && <div>Técnicas: {exercise.techniques}</div>}
                  </div>
                  <div className="mt-2">
                    {exercise.mapping.template_id ? (
                      <span>Template sugerido: <strong>{exercise.mapping.template_title ?? exercise.mapping.template_id}</strong> · Método: {exercise.mapping.method ?? "—"} · Confiança: {mappingConfidence(exercise.mapping.confidence)}</span>
                    ) : <span className="text-danger">Sem sugestão automática</span>}
                  </div>
                  {(exercise.canonicalization || exercise.mapping.template_visual) && (
                    <div className="mt-3">
                      <div className="row g-3 align-items-stretch">
                        <div className="col-12 col-lg-6">
                          <div className="small text-muted mb-1">MFIT original</div>
                          <div className="border rounded p-3 h-100 bg-light">
                            <strong>{exercise.source_name}</strong>
                            {exercise.canonicalization && (
                              <div className="mt-2 small text-muted">
                                {exercise.canonicalization.canonical_name_en && <div>Canonical: {exercise.canonicalization.canonical_name_en}</div>}
                                {!!exercise.canonicalization.search_aliases_en.length && <div>Aliases: {exercise.canonicalization.search_aliases_en.join(", ")}</div>}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="col-12 col-lg-6">
                          <div className="small text-muted mb-1">Template Hevy selecionado</div>
                          <ExerciseVisualCard
                            templateTitle={exercise.mapping.template_title ?? exercise.source_name}
                            visual={exercise.mapping.template_visual ?? placeholderVisualFromTemplate({ id: exercise.mapping.template_id ?? `template-${key}`, title: exercise.mapping.template_title ?? exercise.source_name, primary_muscle_group: null, equipment: null })}
                            canonicalization={exercise.canonicalization?.canonical_name_en ?? null}
                            state={exercise.mapping.template_id ? "confirmed" : "pending"}
                          />
                        </div>
                      </div>
                      <div className="mt-2 small text-muted">A imagem é somente referência visual e não confirma o mapeamento.</div>
                    </div>
                  )}
                  <WorkoutExerciseImageEditor
                    importId={importId ?? review.import_id}
                    exerciseIndex={workoutVisual.exercise_index}
                    visual={workoutVisual}
                    onMediaUpdated={() => {
                      if (importId) void getReview(importId).then(setReview);
                    }}
                  />
                  {exercise.canonicalization && <div className="mt-2">
                    <Badge bg="info" className="me-2">IA: {exercise.canonicalization.canonical_name_en || "Sem nome canônico"}</Badge>
                    <Badge bg="warning" className="me-2">Revisão humana obrigatória</Badge>
                    <small>Confiança: {exercise.canonicalization.confidence.toFixed(2)} · Provedor: {exercise.canonicalization.provider}</small>
                  </div>}
                  <div className="mt-3">
                    <label className="form-label" htmlFor={`manual-search-${key}`}>Pesquisar no catálogo Hevy</label>
                    <div className="input-group">
                      <input id={`manual-search-${key}`} type="search" className="form-control" placeholder="Ex.: Lat Pulldown" value={manualQueryByExerciseId[key] ?? canonicalQuery(exercise)} onChange={(event) => setManualQueryByExerciseId((current) => ({ ...current, [key]: event.target.value }))} />
                      <Button onClick={() => void searchManual(workout, exercise)} disabled={searchLoadingByExerciseId[key]}>Pesquisar</Button>
                    </div>
                    <div className="form-text">A pesquisa consulta apenas o catálogo local sincronizado do Hevy.</div>
                    {exercise.canonicalization?.search_aliases_en.map((alias) => <Button key={alias} size="sm" variant="outline-info" className="me-1 mt-2" onClick={() => void searchManual(workout, exercise, alias)}>{alias}</Button>)}
                    {!!exercise.canonicalization?.search_aliases_en.length && <Button size="sm" variant="outline-info" className="mt-2" onClick={() => void searchAliases(workout, exercise)}>Pesquisar todos os aliases</Button>}
                    <Button size="sm" variant="outline-secondary" className="mt-2 ms-2" onClick={() => navigate(`/exercises?q=${encodeURIComponent(canonicalQuery(exercise))}`)}>Explorar catálogo próprio</Button>
                    {searchLoadingByExerciseId[key] && <div className="mt-2"><Spinner animation="border" size="sm" className="me-2" />Pesquisando catálogo...</div>}
                    {searchErrorByExerciseId[key] && <Alert variant="danger" className="mt-2">{searchErrorByExerciseId[key]}</Alert>}
                    {!!searchResultsByExerciseId[key]?.length && <div className="mt-2"><small className="text-muted">Selecionar um resultado não confirma o mapeamento automaticamente.</small>{searchResultsByExerciseId[key].map((template) => <div className="border rounded p-2 mt-2" key={template.id}><div className="d-flex justify-content-between"><strong>{template.title}</strong>{template.is_custom && <Badge bg="secondary">Customizado</Badge>}</div><div className="small text-muted">{template.type || "—"} · {template.primary_muscle_group || "—"} · {template.equipment || "—"}</div><div className="mt-2"><ExerciseVisualCard templateTitle={template.title} visual={placeholderVisualFromTemplate(template)} canonicalization={exercise.canonicalization?.canonical_name_en ?? null} state="pending" showTitle={false} /></div><Button size="sm" variant="outline-success" className="mt-2" onClick={() => setSelectedTemplateByExerciseId((current) => ({ ...current, [key]: template.id }))}>Selecionar</Button></div>)}</div>}
                    {selectedTemplateByExerciseId[key] && <Alert variant="warning" className="mt-2 mb-0">Seleção pendente — clique em Confirmar mapeamento. {exercise.mapping.mapping_id === null && "É necessário um mapeamento local existente para confirmar."}<div><Button size="sm" variant="success" className="mt-2" disabled={exercise.mapping.mapping_id === null || saving === String(exercise.mapping.mapping_id)} onClick={() => void confirmSelected(exercise, key)}>Confirmar mapeamento</Button></div></Alert>}
                  </div>
                  {exercise.mapping.needs_review && <div className="mt-3">
                    <Button size="sm" variant="outline-primary" onClick={() => void loadAlternatives(workout, exercise)} disabled={alternativeState?.loading}>
                      {alternativeState?.loading ? <><Spinner animation="border" size="sm" className="me-2" />Carregando alternativas...</> : "Ver alternativas"}
                    </Button>
                    {alternativeState?.error && <Alert variant="danger" className="mt-2 mb-2">{alternativeState.error}</Alert>}
                    {alternativeState?.items.map((item) => <Button key={item.template_id} className="d-block mt-2" size="sm" variant="outline-secondary" onClick={() => void confirm(exercise, item.template_id)} disabled={saving === String(exercise.mapping.mapping_id)}>{item.template_title} ({item.confidence.toFixed(2)})</Button>)}
                  </div>}
                </div>
              );
            })}
            <Button disabled={workout.status !== "pending"} onClick={() => void approveWorkout(workout)}>Aprovar este treino</Button>
          </Card.Body>
        </Card>
      ))}

      <Button size="lg" disabled={!canApprove} onClick={() => void approve()}>Aprovar plano completo</Button>
    </Container>
  );
}

export default ReviewPage;
