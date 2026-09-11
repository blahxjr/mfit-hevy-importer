import { useState } from "react";
import { Alert } from "react-bootstrap";

type MfitPdfViewerProps = { importId: string; baseUrl?: string };

export function MfitPdfViewer({ importId, baseUrl = "/imports" }: MfitPdfViewerProps) {
  const [failed, setFailed] = useState(false);
  const pdfUrl = `${baseUrl || "/imports"}/${encodeURIComponent(importId)}/pdf`;
  return (
    <section aria-label="PDF original do My Fit">
      <h2 className="h5">PDF original do My Fit</h2>
      {failed ? <Alert variant="warning">PDF original não disponível</Alert> : (
        <iframe src={pdfUrl} title="PDF original do My Fit" className="w-100 border rounded" style={{ height: 384 }} onError={() => setFailed(true)} />
      )}
    </section>
  );
}

export default MfitPdfViewer;
