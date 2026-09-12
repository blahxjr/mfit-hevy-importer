import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Col, Form, Row, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";
import { listWorkouts } from "../services/workoutEngineService";
import type { WorkoutDto, WorkoutStatus } from "../types/workouts";

const labels: Record<WorkoutStatus, string> = { planned: "Planejado", in_progress: "Em andamento", completed: "Concluído", aborted: "Abortado" };
const colors: Record<WorkoutStatus, string> = { planned: "secondary", in_progress: "info", completed: "success", aborted: "danger" };

export function WorkoutsPage() {
  const [items, setItems] = useState<WorkoutDto[]>([]);
  const [status, setStatus] = useState<WorkoutStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = () => { setLoading(true); listWorkouts({ status }).then((data) => setItems(data.workouts)).catch(() => setError("Não foi possível carregar o histórico de treinos.")).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return <div className="py-4"><div className="d-flex justify-content-between align-items-center mb-4"><div><h1>Treinos locais</h1><p className="text-muted">Histórico e execução do MagicMusculo, sem sincronização automática externa.</p></div><Link className="btn btn-primary" to="/imports">Criar a partir de import</Link></div><Card className="mb-4"><Card.Body><Row><Col md={4}><Form.Select aria-label="Filtrar status" value={status} onChange={(event) => setStatus(event.target.value as WorkoutStatus | "")}><option value="">Todos os status</option>{Object.entries(labels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</Form.Select></Col><Col><Button variant="outline-primary" onClick={load}>Filtrar</Button></Col></Row></Card.Body></Card>{error && <Alert variant="danger">{error}</Alert>}{loading ? <Spinner animation="border" aria-label="Carregando treinos" /> : items.length === 0 ? <Alert variant="info">Nenhum treino local encontrado.</Alert> : <Row>{items.map((item) => <Col md={6} lg={4} className="mb-3" key={item.id}><Card className="h-100"><Card.Body><Card.Title>{item.name}</Card.Title><p className="text-muted">{new Date(item.date).toLocaleString()}</p><Badge bg={colors[item.status]}>{labels[item.status]}</Badge><div><Link className="btn btn-sm btn-outline-primary mt-3" to={`/workouts/${item.id}`}>{item.status === "in_progress" ? "Continuar" : "Abrir treino"}</Link></div></Card.Body></Card></Col>)}</Row>}</div>;
}

export default WorkoutsPage;