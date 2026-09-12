import { useEffect, useState } from "react";
import { Alert, Badge, Card, Spinner } from "react-bootstrap";
import { Link, useParams } from "react-router-dom";
import { getExercise } from "../services/exerciseCatalogService";
import type { ExerciseDto } from "../types/exercises";

export function ExerciseDetailsPage() {
  const { exerciseId } = useParams<{ exerciseId: string }>();
  const [exercise, setExercise] = useState<ExerciseDto | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { if (exerciseId) getExercise(exerciseId).then(setExercise).catch(() => setError("Exercício não encontrado.")); }, [exerciseId]);
  if (error) return <Alert variant="danger" className="mt-4">{error}</Alert>;
  if (!exercise) return <Spinner animation="border" className="mt-4" aria-label="Carregando exercício" />;
  return <div className="py-4"><Link to="/exercises">← Voltar ao catálogo</Link><Card className="mt-3"><Card.Body><h1>{exercise.name}</h1><div className="mb-3"><Badge className="me-2" bg="secondary">{exercise.source}</Badge>{exercise.hevy_template_id && <Badge bg="success">Template Hevy ligado</Badge>}</div>{exercise.image_url && <img src={exercise.image_url} alt={`Demonstração de ${exercise.name}`} className="img-fluid rounded mb-3" style={{ maxHeight: 360 }} />}<p><strong>Alvo:</strong> {exercise.target_muscle || "—"} · <strong>Equipamento:</strong> {exercise.equipment || "—"}</p><p><strong>Padrão:</strong> {exercise.movement_pattern || "—"} · <strong>Parte do corpo:</strong> {exercise.body_part || "—"}</p>{exercise.instructions && <><h2 className="h5">Instruções</h2><p className="white-space-pre-line">{exercise.instructions}</p></>}<Link className="btn btn-outline-primary" to="/exercises">Voltar ao catálogo</Link></Card.Body></Card></div>;
}

export default ExerciseDetailsPage;