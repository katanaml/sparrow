"use client";

import { useRef, useState, useCallback, useEffect } from "react";

// ─── Constants ────────────────────────────────────────────────────────────
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/tiff", "image/webp", "application/pdf"];
const ACCEPTED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp"];

// ─── Types ────────────────────────────────────────────────────────────────
interface UploadedFile {
  file: File;
  name: string;
  sizeLabel: string;
  isPdf: boolean;
  previewUrl: string | null;
  dimensions: string | null;
}

// ─── Icons ────────────────────────────────────────────────────────────────
const UploadIcon = ({ w = 16 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const FileIcon = ({ w = 16 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
);

const ImageIcon = ({ w = 16 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <circle cx="9" cy="9" r="2"/>
    <path d="m21 15-5-5L5 21"/>
  </svg>
);

const XIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

const MaximizeIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 3H5a2 2 0 0 0-2 2v3"/>
    <path d="M21 8V5a2 2 0 0 0-2-2h-3"/>
    <path d="M3 16v3a2 2 0 0 0 2 2h3"/>
    <path d="M16 21h3a2 2 0 0 0 2-2v-3"/>
  </svg>
);

const DownloadIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

const AlertIcon = ({ w = 14 }: { w?: number }) => (
  <svg width={w} height={w} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);

// ─── Helpers ──────────────────────────────────────────────────────────────
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getImageDimensions(url: string): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(`${img.naturalWidth} × ${img.naturalHeight} px`);
    img.onerror = () => resolve("");
    img.src = url;
  });
}

function validateFile(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return "Invalid file type. Only JPG, PNG, TIFF and PDF files are allowed.";
  }
  if (file.size > MAX_FILE_SIZE) {
    return `File size exceeds 5 MB (${formatBytes(file.size)}). Please upload a smaller file.`;
  }
  return null;
}

// ─── Component ────────────────────────────────────────────────────────────
export function InputDocumentCard({
  onFileChange,
  loadFile,
  onClear,
}: {
  onFileChange?: (file: File | null, pageCount: number) => void;
  loadFile?: File | null;
  onClear?: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploaded, setUploaded] = useState<UploadedFile | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processFile = useCallback(async (file: File) => {
    setError(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    const isPdf = file.type === "application/pdf";
    const previewUrl = isPdf ? null : URL.createObjectURL(file);
    const dimensions = previewUrl ? await getImageDimensions(previewUrl) : null;

    // Detect PDF page count client-side
    let pageCount = 1;
    if (isPdf) {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          "pdfjs-dist/build/pdf.worker.min.mjs",
          import.meta.url
        ).toString();
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise;
        pageCount = pdf.numPages;
      } catch (e) {
        console.warn("Could not read PDF page count:", e);
      }
    }

    setUploaded({ file, name: file.name, sizeLabel: formatBytes(file.size), isPdf, previewUrl, dimensions });
    onFileChange?.(file, pageCount);
  }, [onFileChange]);

  // Load external file (e.g. example documents) — must be after processFile
  useEffect(() => {
    if (loadFile) processFile(loadFile);
  }, [loadFile, processFile]);

  const handleClear = () => {
    if (uploaded?.previewUrl) URL.revokeObjectURL(uploaded.previewUrl);
    setUploaded(null);
    setError(null);
    onFileChange?.(null, 0);
    onClear?.();
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  // ── Empty / error state ──────────────────────────────────────────────
  if (!uploaded) {
    return (
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title"><UploadIcon w={14} /> Input document</div>
            <div className="card-desc">PDF or image · max 5 MB · removed after inference</div>
          </div>
        </div>
        <div className="card-body stack-sm">
          <div
            className="drop"
            style={dragging ? { background: "hsl(var(--muted) / 0.7)", borderColor: "hsl(var(--ring) / 0.5)" } : undefined}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          >
            <div className="drop-icon"><UploadIcon w={16} /></div>
            <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
              Drop a document or{" "}
              <span style={{ color: "hsl(var(--primary))", textDecoration: "underline", cursor: "pointer" }}>
                browse files
              </span>
            </div>
            <div className="hint">Supported: PDF, PNG, JPG, TIFF · max 5 MB</div>
          </div>

          {/* Inline error */}
          {error && (
            <div className="file-error">
              <AlertIcon w={13} />
              {error}
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS.join(",")}
            style={{ display: "none" }}
            onChange={handleInputChange}
          />
        </div>
      </div>
    );
  }

  // ── File uploaded state ──────────────────────────────────────────────
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title"><UploadIcon w={14} /> Input document</div>
          <div className="card-desc">Removed after inference completes</div>
        </div>
        <button className="btn btn-ghost btn-icon btn-sm" onClick={handleClear} title="Remove file">
          <XIcon w={14} />
        </button>
      </div>

      <div className="card-body stack-sm">
        <div className="file-row">
          <div className="file-icon">
            {uploaded.isPdf ? <FileIcon w={16} /> : <ImageIcon w={16} />}
          </div>
          <div className="file-meta">
            <div className="file-name">{uploaded.name}</div>
            <div className="file-size">{uploaded.sizeLabel} · uploaded just now</div>
          </div>
          <button className="btn btn-ghost btn-icon btn-sm" title="Replace file" onClick={() => inputRef.current?.click()}>
            <UploadIcon w={14} />
          </button>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          style={{ display: "none" }}
          onChange={handleInputChange}
        />

        {/* PDF — no preview */}
        {uploaded.isPdf && (
          <div className="pdf-placeholder">
            <div className="empty-icon" style={{ margin: "0 auto 10px" }}><FileIcon w={20} /></div>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>PDF preview unavailable</div>
            <div className="hint" style={{ maxWidth: 320, margin: "0 auto" }}>
              Sparrow extracts pages directly without rendering them. Run extraction to see the parsed output on the right.
            </div>
          </div>
        )}

        {/* Image — preview */}
        {!uploaded.isPdf && uploaded.previewUrl && (
          <>
            <div className="row between" style={{ marginTop: 4 }}>
              <span className="hint mono">{uploaded.name}{uploaded.dimensions ? ` · ${uploaded.dimensions}` : ""}</span>
              <div className="row" style={{ gap: 4 }}>
                <button className="btn btn-ghost btn-icon btn-sm" title="Fullscreen" onClick={() => window.open(uploaded.previewUrl!, "_blank")}>
                  <MaximizeIcon w={14} />
                </button>
                <a href={uploaded.previewUrl} download={uploaded.name} className="btn btn-ghost btn-icon btn-sm" title="Download">
                  <DownloadIcon w={14} />
                </a>
              </div>
            </div>
            <div className="preview-frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={uploaded.previewUrl} alt={uploaded.name} style={{ width: "100%", height: "auto", display: "block" }} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}