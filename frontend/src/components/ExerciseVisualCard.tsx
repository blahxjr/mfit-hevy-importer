import type { ReactNode } from "react";
import { Badge, Card } from "react-bootstrap";
import type { TemplateVisualDescriptor } from "../types/imports";

type ExerciseVisualCardProps = {
  templateTitle: string;
  visual: TemplateVisualDescriptor;
  canonicalization?: string | null;
  state?: "selected" | "pending" | "confirmed";
  showTitle?: boolean;
  children?: ReactNode;
};

export function ExerciseVisualCard({ templateTitle, visual, canonicalization, state = "pending", showTitle = true, children }: ExerciseVisualCardProps) {
  const sourceUrl = visual.kind === "official_image" ? visual.image_url : visual.kind === "local_image" ? visual.local_image_url ?? visual.image_url : null;
  const displayTitle = templateTitle || "Exercício";

  return (
    <Card className="h-100 shadow-sm border-0">
      <Card.Body className="p-0">
        {sourceUrl ? (
          <div className="position-relative">
            <img
              src={sourceUrl}
              alt={visual.alt_text || `Imagem de referência para ${displayTitle}`}
              className="img-fluid w-100"
              style={{ height: 180, objectFit: "cover", display: "block" }}
              loading="lazy"
              onError={(event) => {
                const target = event.currentTarget as HTMLImageElement;
                target.style.display = "none";
                target.parentElement?.setAttribute("data-show-placeholder", "true");
              }}
            />
            {!sourceUrl && <div className="p-3 text-muted">Imagem indisponível</div>}
          </div>
        ) : (
          <div className="p-3 bg-light h-100" style={{ minHeight: 180 }}>
            <div className="d-flex align-items-center mb-2">
              <i className={`bi ${visual.movement_icon ?? "bi-card-image"} fs-4 me-2`} />
              {showTitle && <strong>{displayTitle}</strong>}
            </div>
            <div className="small text-muted">Imagem não disponível</div>
            {visual.muscle_label && <div className="mt-2"><Badge bg="secondary">Músculo: {visual.muscle_label}</Badge></div>}
            {visual.equipment_label && <div className="mt-2"><Badge bg="secondary">Equipamento: {visual.equipment_label}</Badge></div>}
          </div>
        )}
        <div className="px-3 pb-3 pt-2">
          {canonicalization && <div className="small text-muted mb-2">Canonical: {canonicalization}</div>}
          {state === "pending" && <Badge bg="warning" text="dark">Pendente</Badge>}
          {state === "selected" && <Badge bg="info">Selecionado</Badge>}
          {state === "confirmed" && <Badge bg="success">Confirmado</Badge>}
          <div className="mt-2 small text-muted">A imagem é somente referência visual e não confirma o mapeamento.</div>
          {children}
        </div>
      </Card.Body>
    </Card>
  );
}

export default ExerciseVisualCard;
