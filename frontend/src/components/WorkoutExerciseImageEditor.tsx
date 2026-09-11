import { useEffect, useState } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { updateWorkoutExerciseMedia, uploadWorkoutExerciseMedia } from "../services/importService";
import type { WorkoutExerciseVisualDescriptor } from "../types/imports";

type Props = {
  importId: string;
  exerciseIndex: number;
  visual: WorkoutExerciseVisualDescriptor;
  onMediaUpdated?: () => void;
};

export function WorkoutExerciseImageEditor({ importId, exerciseIndex, visual, onMediaUpdated }: Props) {
  const [open, setOpen] = useState(false);
  const [altText, setAltText] = useState(visual.alt_text);
  const [verified, setVerified] = useState(visual.is_verified);
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const imageUrl = visual.local_image_url || visual.image_url;

  useEffect(() => { setAltText(visual.alt_text); setVerified(visual.is_verified); }, [visual]);

  const save = async () => {
    setSaving(true); setError(""); setMessage("");
    try {
      if (file) await uploadWorkoutExerciseMedia(importId, exerciseIndex, file, altText, verified);
      else await updateWorkoutExerciseMedia(importId, exerciseIndex, altText, verified);
      setMessage("Imagem de referência atualizada.");
      onMediaUpdated?.();
      setOpen(false);
    } catch { setError("Não foi possível salvar a imagem de referência."); }
    finally { setSaving(false); }
  };

  return <>
    <div className="d-flex align-items-center gap-2 mt-2">
      {imageUrl ? <img src={imageUrl} alt={visual.alt_text} style={{ width: 80, height: 80, objectFit: "cover" }} className="rounded border" /> : <div className="border rounded d-flex align-items-center justify-content-center text-muted" style={{ width: 80, height: 80 }}>Sem imagem</div>}
      <Button size="sm" variant="outline-primary" onClick={() => { setError(""); setOpen(true); }}>Editar imagem de referência</Button>
    </div>
    {message && <div className="small text-success mt-1">{message}</div>}
    <Modal show={open} onHide={() => !saving && setOpen(false)} centered>
      <Modal.Header closeButton><Modal.Title>Imagem de referência</Modal.Title></Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {imageUrl && <img src={imageUrl} alt={visual.alt_text} className="img-fluid rounded mb-3" />}
        <Form.Group className="mb-3"><Form.Label>Texto alternativo</Form.Label><Form.Control value={altText} onChange={(event) => setAltText(event.target.value)} maxLength={255} required /></Form.Group>
        <Form.Group className="mb-3"><Form.Label>Nova imagem (PNG, JPG ou WEBP; até 3 MB)</Form.Label><Form.Control type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setFile((event.target as HTMLInputElement).files?.[0] ?? null)} /></Form.Group>
        <Form.Check type="checkbox" label="Esta imagem está correta para este exercício" checked={verified} onChange={(event) => setVerified(event.target.checked)} />
        <div className="small text-muted mt-2">A imagem é somente referência visual e não confirma o mapeamento.</div>
      </Modal.Body>
      <Modal.Footer><Button variant="secondary" onClick={() => setOpen(false)} disabled={saving}>Cancelar</Button><Button onClick={() => void save()} disabled={saving || !altText.trim()}>{saving && <Spinner size="sm" className="me-2" />}Salvar</Button></Modal.Footer>
    </Modal>
  </>;
}

export default WorkoutExerciseImageEditor;
