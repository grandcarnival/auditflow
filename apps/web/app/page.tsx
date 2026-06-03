"use client";

import { useMemo, useState } from "react";

type ProcessResult = {
  jobId: string;
  downloadUrl: string;
  preservationScore: number;
  packageValid: boolean;
  findingsCount: number;
  duplicatedSlides: number;
  report: {
    package_validation?: {
      issues?: Array<{ code: string; message: string; part?: string | null }>;
    };
    export_table?: string[][];
    export_chart?: {
      categories: string[];
      series: Array<{ name: string; values: Array<number | string> }>;
    };
  };
};

export default function HomePage() {
  const [priorDeck, setPriorDeck] = useState<File | null>(null);
  const [findings, setFindings] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessResult | null>(null);

  const canSubmit = useMemo(() => Boolean(priorDeck && findings && status !== "running"), [priorDeck, findings, status]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!priorDeck || !findings) return;
    setStatus("running");
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("priorDeck", priorDeck);
    formData.append("findingsWorkbook", findings);
    formData.append("notes", notes);

    const response = await fetch("/api/process", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) {
      setStatus("error");
      setError(payload.error ?? "Processing failed.");
      return;
    }
    setResult(payload);
    setStatus("done");
  }

  return (
    <main className="shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>AuditFlow AI</h1>
            <p>Refresh a recurring audit committee deck while preserving editable PowerPoint formatting.</p>
          </div>
          <div className="statusPill" data-state={status}>
            {status === "running" ? "Processing" : status === "done" ? "Ready" : status === "error" ? "Needs attention" : "Idle"}
          </div>
        </header>

        <form className="panel uploadPanel" onSubmit={onSubmit}>
          <label className="field">
            <span>Prior-year PowerPoint</span>
            <input type="file" accept=".pptx" onChange={(event) => setPriorDeck(event.target.files?.[0] ?? null)} />
          </label>

          <label className="field">
            <span>Updated findings workbook</span>
            <input type="file" accept=".xlsx" onChange={(event) => setFindings(event.target.files?.[0] ?? null)} />
          </label>

          <label className="field">
            <span>Optional notes/context</span>
            <textarea rows={5} value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>

          <button type="submit" disabled={!canSubmit}>
            {status === "running" ? "Generating deck..." : "Generate updated deck"}
          </button>
        </form>

        <section className="panel">
          <h2>Processing Summary</h2>
          {!result && status !== "error" ? <p className="muted">Upload files to generate a preservation report.</p> : null}
          {error ? <p className="errorText">{error}</p> : null}
          {result ? (
            <div className="summaryGrid">
              <Metric label="Preservation score" value={result.preservationScore.toFixed(3)} tone={result.preservationScore === 1 ? "good" : "warn"} />
              <Metric label="Package valid" value={result.packageValid ? "Yes" : "No"} tone={result.packageValid ? "good" : "bad"} />
              <Metric label="Findings" value={String(result.findingsCount)} />
              <Metric label="Duplicated slides" value={String(result.duplicatedSlides)} />
              <a className="downloadButton" href={result.downloadUrl}>
                Download editable PPTX
              </a>
            </div>
          ) : null}
        </section>

        {result ? (
          <section className="panel reportPanel">
            <h2>Preservation Report</h2>
            <div className="reportColumns">
              <div>
                <h3>Updated table</h3>
                <pre>{JSON.stringify(result.report.export_table, null, 2)}</pre>
              </div>
              <div>
                <h3>Updated chart</h3>
                <pre>{JSON.stringify(result.report.export_chart, null, 2)}</pre>
              </div>
            </div>
            {result.report.package_validation?.issues?.length ? (
              <div className="issues">
                <h3>Validation issues</h3>
                <pre>{JSON.stringify(result.report.package_validation.issues, null, 2)}</pre>
              </div>
            ) : (
              <p className="successText">No structural validation issues detected.</p>
            )}
          </section>
        ) : null}
      </section>
    </main>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "good" | "warn" | "bad" }) {
  return (
    <div className="metric" data-tone={tone ?? "neutral"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

