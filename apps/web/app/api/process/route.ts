import { randomUUID } from "crypto";
import { mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import { spawn } from "child_process";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 60;

type WorkflowResult = {
  output_deck: string;
  findings_count: number;
  duplicated_slides: number;
  preservation_score: number;
  package_valid: boolean;
};

type SupabaseJob = {
  id: string;
  status: string;
  prior_deck_path: string;
  findings_workbook_path: string;
  notes_path: string | null;
};

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const priorDeck = formData.get("priorDeck");
    const findingsWorkbook = formData.get("findingsWorkbook");
    const notes = formData.get("notes");

    if (!(priorDeck instanceof File) || !(findingsWorkbook instanceof File)) {
      return NextResponse.json({ error: "Upload a prior-year PPTX and findings workbook." }, { status: 400 });
    }
    if (!priorDeck.name.toLowerCase().endsWith(".pptx") || !findingsWorkbook.name.toLowerCase().endsWith(".xlsx")) {
      return NextResponse.json({ error: "Upload a .pptx prior deck and .xlsx findings workbook." }, { status: 400 });
    }

    if (supabaseProcessingEnabled()) {
      const job = await createSupabaseJob({
        priorDeck,
        findingsWorkbook,
        notes: typeof notes === "string" ? notes : "",
      });
      return NextResponse.json({
        jobId: job.id,
        status: job.status,
        statusUrl: `/api/jobs/${job.id}`,
        message: "Files uploaded. Processing job queued.",
      });
    }

    if (!localProcessingEnabled()) {
      return NextResponse.json(
        {
          error:
            "Processing is not configured. Set AUDITFLOW_PROCESSOR_MODE=supabase for pilot processing or local for local development.",
        },
        { status: 503 },
      );
    }

    const jobId = randomUUID();
    const repoRoot = getRepoRoot();
    const jobDir = path.join(repoRoot, ".runtime", "jobs", jobId);
    await mkdir(jobDir, { recursive: true });

    const priorPath = path.join(jobDir, "prior.pptx");
    const findingsPath = path.join(jobDir, "findings.xlsx");
    const outputPath = path.join(jobDir, "auditflow-export.pptx");
    const reportPath = path.join(jobDir, "report.json");
    const manifestPath = path.join(jobDir, "manifest.json");

    await writeUpload(priorDeck, priorPath);
    await writeUpload(findingsWorkbook, findingsPath);

    const workflow = await runWorkflow({
      repoRoot,
      priorPath,
      findingsPath,
      outputPath,
      reportPath,
      manifestPath,
    });
    const report = JSON.parse(await readFile(reportPath, "utf-8"));

    return NextResponse.json({
      jobId,
      downloadUrl: `/api/exports/${jobId}`,
      preservationScore: workflow.preservation_score,
      packageValid: workflow.package_valid,
      findingsCount: workflow.findings_count,
      duplicatedSlides: workflow.duplicated_slides,
      report,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Processing failed." },
      { status: 500 },
    );
  }
}

async function writeUpload(file: File, targetPath: string) {
  const bytes = Buffer.from(await file.arrayBuffer());
  await writeFile(targetPath, bytes);
}

function runWorkflow(paths: {
  repoRoot: string;
  priorPath: string;
  findingsPath: string;
  outputPath: string;
  reportPath: string;
  manifestPath: string;
}) {
  const python = process.env.AUDITFLOW_PYTHON ?? (process.platform === "win32" ? "python.exe" : "python");
  const script = path.join(paths.repoRoot, "tools", "workflow", "run_mvp_workflow.py");
  const args = [
    script,
    "--prior-deck",
    paths.priorPath,
    "--findings-workbook",
    paths.findingsPath,
    "--output-deck",
    paths.outputPath,
    "--report",
    paths.reportPath,
    "--manifest",
    paths.manifestPath,
    "--fiscal-year",
    "2026",
  ];

  return new Promise<WorkflowResult>((resolve, reject) => {
    const child = spawn(python, args, { cwd: paths.repoRoot });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr || `Workflow exited with code ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout.trim()) as WorkflowResult);
      } catch {
        reject(new Error("Workflow completed but returned invalid JSON."));
      }
    });
  });
}

function getRepoRoot() {
  return process.env.AUDITFLOW_REPO_ROOT ?? path.resolve(process.cwd(), "..", "..");
}

function localProcessingEnabled() {
  const mode = process.env.AUDITFLOW_PROCESSOR_MODE ?? (process.env.VERCEL === "1" ? "disabled" : "local");
  return mode === "local";
}

function supabaseProcessingEnabled() {
  return process.env.AUDITFLOW_PROCESSOR_MODE === "supabase";
}

async function createSupabaseJob(input: { priorDeck: File; findingsWorkbook: File; notes: string }): Promise<SupabaseJob> {
  const jobId = randomUUID();
  const bucket = storageBucket();
  const priorPath = `jobs/${jobId}/input/prior.pptx`;
  const findingsPath = `jobs/${jobId}/input/findings.xlsx`;
  const notesPath = input.notes.trim() ? `jobs/${jobId}/input/notes.txt` : null;

  await uploadStorageObject(bucket, priorPath, input.priorDeck, "application/vnd.openxmlformats-officedocument.presentationml.presentation");
  await uploadStorageObject(bucket, findingsPath, input.findingsWorkbook, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
  if (notesPath) {
    await uploadStorageObject(bucket, notesPath, new Blob([input.notes], { type: "text/plain" }), "text/plain");
  }

  const response = await supabaseFetch("/rest/v1/auditflow_jobs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Prefer: "return=representation",
    },
    body: JSON.stringify({
      id: jobId,
      status: "queued",
      prior_deck_path: priorPath,
      findings_workbook_path: findingsPath,
      notes_path: notesPath,
    }),
  });
  const rows = (await response.json()) as SupabaseJob[];
  return rows[0];
}

async function uploadStorageObject(bucket: string, objectPath: string, file: File | Blob, contentType: string) {
  const response = await supabaseFetch(`/storage/v1/object/${bucket}/${objectPath}`, {
    method: "POST",
    headers: {
      "Content-Type": contentType,
      "x-upsert": "true",
    },
    body: Buffer.from(await file.arrayBuffer()),
  });
  if (!response.ok) {
    throw new Error(`Storage upload failed for ${objectPath}: ${await response.text()}`);
  }
}

async function supabaseFetch(pathname: string, init: RequestInit) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("Supabase processing requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.");
  }
  const response = await fetch(`${url}${pathname}`, {
    ...init,
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      ...(init.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`Supabase request failed: ${response.status} ${await response.text()}`);
  }
  return response;
}

function storageBucket() {
  return process.env.AUDITFLOW_STORAGE_BUCKET ?? "auditflow-artifacts";
}
