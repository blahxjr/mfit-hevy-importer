import { ChangeEvent, useMemo, useState } from "react";
import { Alert, Badge, Button, Card, Col, Container, Form, ListGroup, Row, Spinner } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { mapImport, normalizeImport, parseMfitPdf } from "../services/importService";
import type { ImportStepStatus, ImportWorkflowState, MapImportResponse, NormalizeImportResponse, ParseImportResponse } from "../types/imports";

const initialSteps: ImportWorkflowState = {
  upload: "pending",
  parsing: "pending",
  normalization: "pending",
  mapping: "pending",
  review: "pending",
};

const stepLabels: Array<[keyof ImportWorkflowState, string]> = [
  ["upload", "Upload do PDF"],
  ["parsing", "Parsing"],
  ["normalization", "Normalização"],
  ["mapping", "Mapeamento"],
  ["review", "Revisão humana"],
];

function statusVariant(status: ImportStepStatus): string {
  if (status === "done") return "success";
  if (status === "processing") return "info";
  if (status === "error") return "danger";
  return "secondary";
}

function statusLabel(status: ImportStepStatus): string {
  if (status === "done") return "Concluída";
  if (status === "processing") return "Processando";
  if (status === "error") return "Erro";
  return "Pendente";
}

export function ImportsPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [steps, setSteps] = useState<ImportWorkflowState>(initialSteps);
  const [parseResult, setParseResult] = useState<ParseImportResponse | null>(null);
  const [normalizeResult, setNormalizeResult] = useState<NormalizeImportResponse | null>(null);
  const [mapResult, setMapResult] = useState<MapImportResponse | null>(null);
  const [error, setError] = useState("");

  const importId = parseResult?.import_id;
  const shortHash = useMemo(() => parseResult?.sha256 ? `${parseResult.sha256.slice(0, 12)}…` : "", [parseResult]);
  const isDuplicate = parseResult?.status === "duplicate";

  const setStep = (name: keyof ImportWorkflowState, status: ImportStepStatus) => {
    setSteps((current) => ({ ...current, [name]: status }));
  };

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setError("");
    setParseResult(null);
    setNormalizeResult(null);
    setMapResult(null);
    setSteps(initialSteps);
    if (!selected) {
      setFile(null);
      return;
    }
    const isPdf = selected.type === "application/pdf" || selected.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      setFile(null);
      setSteps((current) => ({ ...current, upload: "error" }));
      setError("Selecione somente um arquivo PDF exportado do MFIT.");
      return;
    }
    setFile(selected);
    setSteps((current) => ({ ...current, upload: "done" }));
  };

  const processFile = async () => {
    if (!file) return;
    setError("");
    setParseResult(null);
    setNormalizeResult(null);
    setMapResult(null);
    setSteps({ upload: "done", parsing: "processing", normalization: "pending", mapping: "pending", review: "pending" });
    try {
      const result = await parseMfitPdf(file);
      setParseResult(result);
      setSteps({ upload: "done", parsing: "done", normalization: "pending", mapping: "pending", review: "pending" });
    } catch {
      setStep("parsing", "error");
      setError("Não foi possível processar o PDF. Verifique o arquivo e tente novamente.");
    }
  };

  const normalize = async () => {
    if (!importId) return;
    setError("");
    setStep("normalization", "processing");
    try {
      const result = await normalizeImport(importId);
      setNormalizeResult(result);
      setStep("normalization", "done");
    } catch {
      setStep("normalization", "error");
      setError("Não foi possível normalizar os exercícios desta importação.");
    }
  };

  const map = async () => {
    if (!importId) return;
    setError("");
    setStep("mapping", "processing");
    try {
      const result = await mapImport(importId);
      setMapResult(result);
      setSteps((current) => ({ ...current, mapping: "done", review: "pending" }));
    } catch {
      setStep("mapping", "error");
      setError("Não foi possível mapear os exercícios no catálogo Hevy.");
    }
  };

  const openReview = () => {
    if (importId) {
      setStep("review", "done");
      navigate(`/review/${importId}`);
    }
  };

  const processing = steps.parsing === "processing" || steps.normalization === "processing" || steps.mapping === "processing";

  return (
    <Container className="py-4">
      <Row className="justify-content-center">
        <Col lg={10}>
          <div className="mb-4">
            <h1>Importações</h1>
            <p className="text-muted">Faça upload de uma ficha MFIT e prepare os dados para revisão humana.</p>
            <Alert variant="info">
              O sistema apenas prepara e revisa os dados nesta etapa. Nenhuma rotina será criada no Hevy sem confirmação explícita.
            </Alert>
            {error && <Alert variant="danger">{error}</Alert>}
          </div>

          <Card className="mb-4">
            <Card.Body>
              <Card.Title>Etapas do processamento</Card.Title>
              <ListGroup horizontal className="flex-wrap gap-2 border-0">
                {stepLabels.map(([key, label]) => (
                  <ListGroup.Item className="border-0 px-0" key={key}>
                    <Badge bg={statusVariant(steps[key])}>{label}: {statusLabel(steps[key])}</Badge>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>

          <Card className="mb-4">
            <Card.Body>
              <Card.Title>Upload da ficha MFIT</Card.Title>
              <Form.Group className="mb-3" controlId="mfit-pdf">
                <Form.Label>Arquivo PDF</Form.Label>
                <Form.Control type="file" accept="application/pdf,.pdf" onChange={selectFile} disabled={processing} />
                <Form.Text className="text-muted">Somente PDFs exportados do MFIT são aceitos.</Form.Text>
              </Form.Group>
              {file && <Alert variant="secondary" className="py-2"><strong>{file.name}</strong> · {(file.size / 1024 / 1024).toFixed(2)} MB</Alert>}
              <Button variant="primary" onClick={() => void processFile()} disabled={!file || processing}>
                {steps.parsing === "processing" ? <><Spinner animation="border" size="sm" className="me-2" />Processando…</> : "Processar ficha MFIT"}
              </Button>
            </Card.Body>
          </Card>

          {parseResult && <Card className="mb-4">
            <Card.Body>
              <Card.Title>Resultado do parsing</Card.Title>
              {isDuplicate && <Alert variant="warning">Este PDF já foi importado anteriormente. Você pode abrir a revisão existente ou continuar o fluxo com o import encontrado.</Alert>}
              <Row>
                <Col md={6}><p><strong>Arquivo:</strong> {parseResult.filename}</p><p><strong>Import ID:</strong> <code>{parseResult.import_id}</code></p><p><strong>SHA-256:</strong> <code>{shortHash}</code></p></Col>
                <Col md={6}><p><strong>Treinos:</strong> {parseResult.workouts_count ?? "—"}</p><p><strong>Exercícios:</strong> {parseResult.exercises_count ?? "—"}</p><p><strong>Status:</strong> <Badge bg={isDuplicate ? "warning" : "success"}>{parseResult.status || "parsed"}</Badge></p></Col>
              </Row>
              {!!parseResult.warnings?.length && <Alert variant="warning"><strong>Avisos do parser:</strong><ul className="mb-0">{parseResult.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></Alert>}
              <Button variant="secondary" onClick={() => void normalize()} disabled={steps.normalization === "done" || steps.normalization === "processing"}>
                {steps.normalization === "processing" ? <><Spinner animation="border" size="sm" className="me-2" />Normalizando…</> : "Normalizar exercícios"}
              </Button>
              {isDuplicate && <Button variant="outline-primary" className="ms-2" onClick={openReview}>Abrir revisão do import existente</Button>}
            </Card.Body>
          </Card>}

          {normalizeResult && <Card className="mb-4">
            <Card.Body>
              <Card.Title>Normalização</Card.Title>
              <p><strong>Exercícios normalizados:</strong> {normalizeResult.normalized_count}</p>
              <p><strong>Precisam de revisão:</strong> <Badge bg={normalizeResult.needs_review_count ? "warning" : "success"}>{normalizeResult.needs_review_count}</Badge></p>
              {!!normalizeResult.warnings?.length && <Alert variant="warning">{normalizeResult.warnings.join("; ")}</Alert>}
              <Button variant="secondary" onClick={() => void map()} disabled={steps.normalization !== "done" || steps.mapping === "done" || steps.mapping === "processing"}>
                {steps.mapping === "processing" ? <><Spinner animation="border" size="sm" className="me-2" />Mapeando…</> : "Mapear exercícios no Hevy"}
              </Button>
            </Card.Body>
          </Card>}

          {mapResult && <Card>
            <Card.Body>
              <Card.Title>Mapeamento</Card.Title>
              <Row>
                <Col md={4}><strong>Mapeados:</strong> {mapResult.mapped_count}</Col>
                <Col md={4}><strong>Revisão:</strong> <Badge bg="warning">{mapResult.needs_review_count}</Badge></Col>
                <Col md={4}><strong>Sem match:</strong> <Badge bg="danger">{mapResult.no_match_count}</Badge></Col>
              </Row>
              <hr />
              <Button variant="success" onClick={openReview} disabled={steps.mapping !== "done"}>Abrir revisão dos treinos</Button>
            </Card.Body>
          </Card>}
        </Col>
      </Row>
    </Container>
  );
}

export default ImportsPage;
