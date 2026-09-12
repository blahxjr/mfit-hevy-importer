import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Col, Form, Row, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";
import { listExercises, syncExerciseDb } from "../services/exerciseCatalogService";
import type { ExerciseDto } from "../types/exercises";

export function ExercisesCatalogPage() {
  const [items, setItems] = useState<ExerciseDto[]>([]);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const load = () => {
    setLoading(true); setError("");
    listExercises({ q: query || undefined, source: source || undefined })
      .then((response) => setItems(response.exercises)).catch(() => setError("Não foi possível carregar o catálogo."))
      .finally(() => setLoading(false));
  };
  useEffect(() => { const initial = new URLSearchParams(window.location.search).get("q") || ""; if (initial) setQuery(initial); setLoading(true); listExercises({ q: initial || undefined }).then((response) => setItems(response.exercises)).catch(() => setError("Não foi possível carregar o catálogo.")).finally(() => setLoading(false)); }, []);
  const sync = () => {
    setSyncing(true); setError("");
    syncExerciseDb().then(load).catch(() => setError("A sincronização ExerciseDB falhou. Verifique a configuração da API."))
      .finally(() => setSyncing(false));
  };
  return <div className="py-4">
    <div className="d-flex justify-content-between align-items-center mb-3"><div><h1>Catálogo de exercícios</h1><p className="text-muted">ExerciseDB, templates Hevy e exercícios próprios em um só lugar.</p></div><Button onClick={sync} disabled={syncing}>{syncing ? "Sincronizando..." : "Sincronizar ExerciseDB"}</Button></div>
    <Card className="mb-4"><Card.Body><Row className="g-2"><Col md={7}><Form.Control aria-label="Buscar exercícios" placeholder="Buscar por nome" value={query} onChange={(event) => setQuery(event.target.value)} /></Col><Col md={3}><Form.Select aria-label="Filtrar origem" value={source} onChange={(event) => setSource(event.target.value)}><option value="">Todas as origens</option><option value="exercisedb">ExerciseDB</option><option value="hevy_template">Hevy</option><option value="custom">Customizado</option></Form.Select></Col><Col md={2}><Button className="w-100" variant="outline-primary" onClick={load}>Filtrar</Button></Col></Row></Card.Body></Card>
    {error && <Alert variant="danger">{error}</Alert>}{loading ? <Spinner animation="border" aria-label="Carregando catálogo" /> : <Row>{items.map((item) => <Col md={6} lg={4} key={item.id} className="mb-3"><Card className="h-100"><Card.Body><Card.Title>{item.name}</Card.Title><div className="small text-muted">{item.target_muscle || item.body_part || "Músculo não informado"} · {item.equipment || "Equipamento não informado"}</div><div className="mt-2"><Badge bg="secondary" className="me-2">{item.source}</Badge>{item.hevy_template_id ? <Badge bg="success">Ligado ao Hevy</Badge> : <Badge bg="light" text="dark">Sem template Hevy</Badge>}</div><Link className="btn btn-sm btn-outline-primary mt-3" to={`/exercises/${item.id}`}>Ver detalhes</Link></Card.Body></Card></Col>)}</Row>}
    {!loading && items.length === 0 && <Alert variant="info">Nenhum exercício encontrado.</Alert>}
  </div>;
}

export default ExercisesCatalogPage;