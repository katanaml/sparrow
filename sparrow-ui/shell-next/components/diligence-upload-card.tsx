"use client";

import { useRef, useState } from "react";
import { CircleAlert, FileText, Upload, X } from "lucide-react";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/tiff", "image/webp", "application/pdf"];
const ACCEPTED_EXTENSIONS = ".pdf,.png,.jpg,.jpeg,.tiff,.tif,.webp";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateFile(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return "Invalid file type. Only PDF, PNG, JPG and TIFF files are allowed.";
  }
  if (file.size > MAX_FILE_SIZE) {
    return `File size exceeds 5 MB (${formatBytes(file.size)}). Please upload a smaller file.`;
  }
  return null;
}

// Upload without any preview — the page stays compact and the extracted
// company identity is shown instead once the document has been read.
export function UploadCard({
  file,
  onFile,
  locked,
}: {
  file: File | null;
  onFile: (file: File | null) => void;
  locked: boolean; // true while a run is in progress
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accept = (f: File | undefined) => {
    if (!f || locked) return;
    const problem = validateFile(f);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    onFile(f);
  };

  const clear = () => {
    setError(null);
    onFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title"><Upload size={14} /> Company document</div>
          <div className="card-desc">Company profile, letterhead or registration extract · PDF or image · max 5 MB</div>
        </div>
        {file && !locked && (
          <button className="btn btn-ghost btn-icon btn-sm" onClick={clear} title="Remove file">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="card-body stack-sm">
        {!file ? (
          <div
            className="drop dd-drop"
            style={dragging ? { background: "hsl(var(--muted) / 0.7)", borderColor: "hsl(var(--ring) / 0.5)" } : undefined}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => { e.preventDefault(); setDragging(false); accept(e.dataTransfer.files?.[0]); }}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          >
            <div className="drop-icon"><Upload size={16} /></div>
            <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
              Drop a document or{" "}
              <span style={{ color: "hsl(var(--primary))", textDecoration: "underline", cursor: "pointer" }}>
                browse files
              </span>
            </div>
            <div className="hint">PDF, PNG, JPG, TIFF · max 5 MB</div>
          </div>
        ) : (
          <div className="file-row">
            <div className="file-icon"><FileText size={16} /></div>
            <div className="file-meta">
              <div className="file-name">{file.name}</div>
              <div className="file-size">{formatBytes(file.size)}</div>
            </div>
            <button
              className="btn btn-ghost btn-icon btn-sm"
              title="Replace file"
              onClick={() => inputRef.current?.click()}
              disabled={locked}
            >
              <Upload size={14} />
            </button>
          </div>
        )}

        {error && (
          <div className="file-error">
            <CircleAlert size={13} />
            {error}
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          style={{ display: "none" }}
          onChange={(e) => { accept(e.target.files?.[0]); e.target.value = ""; }}
        />
      </div>
    </div>
  );
}