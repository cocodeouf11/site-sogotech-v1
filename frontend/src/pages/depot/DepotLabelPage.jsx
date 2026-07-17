import { useEffect, useRef, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { Printer, Download, FileDown, RotateCcw } from "lucide-react";

const PDFJS_SRC = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
const PDFJS_WORKER_SRC = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
const JSPDF_SRC = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";

const DEFAULT_CROP = { x0: 0.6067, y0: 0.1525, x1: 0.9812, y1: 0.8439 };

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const script = document.createElement("script");
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

export default function DepotLabelPage() {
  const sourceCanvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const croppedCanvasRef = useRef(null);
  const fileNameRef = useRef("etiquette");

  const [ready, setReady] = useState(false);
  const [active, setActive] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [meta, setMeta] = useState({ dims: "—", file: "—" });
  const [previewSrc, setPreviewSrc] = useState(null);

  useEffect(() => {
    (async () => {
      await loadScript(PDFJS_SRC);
      if (window.pdfjsLib) window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_SRC;
      await loadScript(JSPDF_SRC);
      setReady(true);
    })();
  }, []);

  const renderPdf = async (arrayBuffer) => {
    const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const page = await pdf.getPage(1);
    const scale = 2.2;
    const viewport = page.getViewport({ scale });
    const canvas = sourceCanvasRef.current;
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    const ctx = canvas.getContext("2d");
    await page.render({ canvasContext: ctx, viewport }).promise;
  };

  const renderImage = (img) => {
    const canvas = sourceCanvasRef.current;
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);
  };

  const cropWithFraction = (frac) => {
    const source = sourceCanvasRef.current;
    const sw = source.width, sh = source.height;
    const sx = frac.x0 * sw, sy = frac.y0 * sh;
    const cw = (frac.x1 - frac.x0) * sw, ch = (frac.y1 - frac.y0) * sh;

    const cropped = document.createElement("canvas");
    cropped.width = Math.round(cw);
    cropped.height = Math.round(ch);
    const ctx = cropped.getContext("2d");
    ctx.drawImage(source, sx, sy, cw, ch, 0, 0, cropped.width, cropped.height);
    croppedCanvasRef.current = cropped;
    setPreviewSrc(cropped.toDataURL("image/png"));
    setMeta({ dims: `${cropped.width} × ${cropped.height} px`, file: fileNameRef.current });
  };

  const handleFile = async (file) => {
    fileNameRef.current = file.name || "etiquette";
    if (file.type === "application/pdf") {
      const buf = await file.arrayBuffer();
      await renderPdf(buf);
    } else {
      const url = URL.createObjectURL(file);
      const img = new Image();
      await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url; });
      renderImage(img);
    }
    setActive(true);
  };

  useEffect(() => {
    if (active && sourceCanvasRef.current?.width) {
      cropWithFraction(DEFAULT_CROP);
    }
  }, [active]);

  const onInputChange = (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); };
  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const doPrint = () => {
    if (!croppedCanvasRef.current) return;
    const dataUrl = croppedCanvasRef.current.toDataURL("image/png");
    const win = window.open("", "_blank");
    win.document.write(`<html><head><title>Étiquette</title><style>@page{margin:0;} body{margin:0;} img{width:100mm;display:block;}</style></head><body><img src="${dataUrl}" onload="window.print();"/></body></html>`);
    win.document.close();
  };

  const downloadPng = () => {
    if (!croppedCanvasRef.current) return;
    const a = document.createElement("a");
    a.download = `${fileNameRef.current.replace(/\.[^.]+$/, "")}-etiquette.png`;
    a.href = croppedCanvasRef.current.toDataURL("image/png");
    a.click();
  };

  const downloadPdf = () => {
    if (!croppedCanvasRef.current) return;
    const { jsPDF } = window.jspdf;
    const widthMM = 100;
    const heightMM = widthMM * (croppedCanvasRef.current.height / croppedCanvasRef.current.width);
    const pdf = new jsPDF({ orientation: widthMM > heightMM ? "landscape" : "portrait", unit: "mm", format: [widthMM, heightMM] });
    pdf.addImage(croppedCanvasRef.current.toDataURL("image/png"), "PNG", 0, 0, widthMM, heightMM);
    pdf.save(`${fileNameRef.current.replace(/\.[^.]+$/, "")}-etiquette.pdf`);
  };

  const reset = () => {
    setActive(false);
    setPreviewSrc(null);
    croppedCanvasRef.current = null;
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <Layout title="Dépôt — Découpe étiquette">
      <div className="max-w-2xl">
        <canvas ref={sourceCanvasRef} className="hidden" />
        {!active && (
          <label
            htmlFor="etiquette-file-input"
            data-testid="etiquette-dropzone"
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`block border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors duration-200 ${dragging ? "border-primary bg-primary/5" : "border-border bg-card"}`}
          >
            <span className="inline-block text-xs font-mono border border-foreground/40 rounded px-2 py-1 mb-4">PDF / JPG / PNG</span>
            <p className="font-semibold mb-1">Dépose ton bordereau Chronopost ici</p>
            <p className="text-sm text-muted-foreground">ou clique pour choisir un fichier — la zone encadrée en rouge est détectée automatiquement</p>
            <input
              id="etiquette-file-input"
              ref={fileInputRef}
              data-testid="etiquette-file-input"
              type="file"
              accept="application/pdf,image/png,image/jpeg"
              className="hidden"
              disabled={!ready}
              onChange={onInputChange}
            />
          </label>
        )}

        {active && (
          <div className="rounded-xl border border-border bg-card p-6" data-testid="etiquette-workarea">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Étiquette découpée automatiquement</p>
              <button onClick={reset} data-testid="etiquette-reset-button" className="text-xs text-muted-foreground underline flex items-center gap-1">
                <RotateCcw size={12} /> recommencer
              </button>
            </div>
            <div className="rounded-lg border border-border bg-secondary/40 p-4 flex items-center justify-center min-h-[220px] mb-4" data-testid="etiquette-preview">
              {previewSrc ? (
                <img src={previewSrc} alt="Étiquette découpée" className="max-w-full max-h-[340px] shadow-lg" />
              ) : (
                <p className="text-xs font-mono text-muted-foreground">Traitement en cours…</p>
              )}
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              <button onClick={doPrint} disabled={!previewSrc} data-testid="etiquette-print-button" className="px-4 py-3 rounded-md bg-primary text-primary-foreground font-semibold text-sm disabled:opacity-40 flex items-center gap-2">
                <Printer size={15} /> Imprimer
              </button>
              <button onClick={downloadPng} disabled={!previewSrc} data-testid="etiquette-download-png-button" className="px-4 py-3 rounded-md border border-foreground/30 font-semibold text-sm disabled:opacity-40 flex items-center gap-2">
                <Download size={15} /> Télécharger en image (PNG)
              </button>
              <button onClick={downloadPdf} disabled={!previewSrc} data-testid="etiquette-download-pdf-button" className="px-4 py-3 rounded-md border border-foreground/30 font-semibold text-sm disabled:opacity-40 flex items-center gap-2">
                <FileDown size={15} /> Télécharger en PDF
              </button>
            </div>
            <div className="flex justify-between text-xs font-mono text-muted-foreground border-t border-dashed border-border pt-3">
              <span data-testid="etiquette-meta-dims">{meta.dims}</span>
              <span data-testid="etiquette-meta-file">{meta.file}</span>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
