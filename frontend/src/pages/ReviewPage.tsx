import { useCallback, useEffect, useState } from 'react';
import { Alert, Badge, Button, Card, Container, Form, Spinner } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

type Alternative = { template_id: string; template_title: string; confidence: number };
type Mapping = { mapping_id: number | null; template_id: string | null; template_title: string | null; method: string | null; confidence: number | null; needs_review: boolean };
type Exercise = { source_name: string; order: number; sets_raw: string | null; reps_raw: string | null; load_raw: string | null; rest_raw: string | null; techniques: string | null; mapping: Mapping };
type Workout = { workout_name: string; order: number; status: string; exercises: Exercise[] };
type Review = { import_id: string; filename: string; status: string; workouts: Workout[]; summary: { total_exercises: number; mapped_count: number; needs_review_count: number; no_match_count: number } };
const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000' });

export function ReviewPage() {
  const { importId } = useParams(); const navigate = useNavigate();
  const [review, setReview] = useState<Review | null>(null); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
    const [alternatives, setAlternatives] = useState<Record<string, Alternative[]>>({}); 
    const [saving, setSaving] = useState<string | null>(null);
  const load = useCallback(async () => { if (!importId) return; setLoading(true); try { setReview((await api.get<Review>(`/review/${importId}`)).data); setError(''); } catch { setError('Não foi possível carregar a revisão.'); } finally { setLoading(false); } }, [importId]);
  useEffect(() => { void load(); }, [load]);
    const getAlternatives = async (name: string) => {
      try {
        const response = await api.get<{ alternatives: Alternative[] }>(`/mapping/alternatives/${encodeURIComponent(name)}`);
        setAlternatives((current) => ({ ...current, [name]: response.data.alternatives }));
      } catch {
        setError("Não foi possível carregar alternativas.");
      }
    };
  const confirm = async (mappingId: number | null, templateId: string) => { if (!mappingId) return; setSaving(String(mappingId)); try { await api.post(`/mapping/${mappingId}/confirm`, null, { params: { template_id: templateId } }); await load(); } catch { setError('Não foi possível confirmar o mapeamento.'); } finally { setSaving(null); } };
  const approve = async () => { try { await api.post(`/review/${importId}/approve`); navigate(`/imports/${importId}/payload`); } catch { setError('Ainda existem mapeamentos pendentes de confirmação.'); } };
  const approveWorkout = async (workout: Workout) => { try { await api.post(`/review/${importId}/workouts/${workout.order}/approve`); await load(); } catch { setError(`O treino ${workout.workout_name} ainda possui mapeamentos pendentes.`); } };
  if (loading) return <Container className="py-5 text-center"><Spinner animation="border" /></Container>;
  if (!review) return <Container className="py-4"><Alert variant="danger">{error || 'Importação não encontrada.'}</Alert></Container>;
  return <Container className="py-4"><h1>Revisar importação</h1><p className="text-muted">{review.filename} · Status: <strong>{review.status}</strong></p>{error && <Alert variant="danger">{error}</Alert>}<Alert variant={review.summary.needs_review_count ? 'warning' : 'success'}><strong>{review.summary.needs_review_count ? 'Revisão necessária' : 'Plano pronto para aprovação'}</strong><div>{review.summary.total_exercises} exercícios · {review.summary.mapped_count} mapeados · {review.summary.no_match_count} sem correspondência</div></Alert>
    {review.workouts.map((workout) => <Card className="mb-3" key={workout.order}><Card.Header className="d-flex justify-content-between"><strong>{workout.workout_name}</strong><Badge bg={workout.status === 'approved' || workout.status === 'completed' ? 'success' : 'secondary'}>{workout.status}</Badge></Card.Header><Card.Body>{workout.exercises.map((exercise) => <div className="border rounded p-3 mb-3" key={exercise.order}><div className="d-flex justify-content-between"><strong>{exercise.source_name}</strong><Badge bg={exercise.mapping.needs_review ? 'warning' : 'success'}>{exercise.mapping.needs_review ? 'Revisar' : 'Confirmado'}</Badge></div><small>{exercise.sets_raw} · Carga: {exercise.load_raw || '—'} · Descanso: {exercise.rest_raw || '—'}</small>{exercise.techniques && <div><small>Técnicas: {exercise.techniques}</small></div>}<div className="mt-2">{exercise.mapping.template_title ? <>Hevy: <strong>{exercise.mapping.template_title}</strong> ({exercise.mapping.method}, {(exercise.mapping.confidence || 0).toFixed(2)})</> : <span className="text-danger">Sem correspondência</span>}</div>{exercise.mapping.needs_review && <div className="mt-2"><Button size="sm" variant="outline-primary" onClick={() => void getAlternatives(exercise.source_name)}>Ver alternativas</Button>{alternatives[exercise.source_name]?.map((item) => <Form.Check key={item.template_id} className="mt-2" type="radio" name={`mapping-${exercise.mapping.mapping_id}`} label={`${item.template_title} (${item.confidence.toFixed(2)})`} onChange={() => void confirm(exercise.mapping.mapping_id, item.template_id)} disabled={saving === String(exercise.mapping.mapping_id)} />)}</div>}</div>)}<Button disabled={workout.status !== 'pending'} onClick={() => void approveWorkout(workout)}>Aprovar este treino</Button></Card.Body></Card>)}
    <Button size="lg" disabled={!review.workouts.every((workout) => workout.status === 'approved' || workout.status === 'completed')} onClick={() => void approve()}>Aprovar plano completo</Button></Container>;
}