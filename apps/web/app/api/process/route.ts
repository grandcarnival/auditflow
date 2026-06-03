import { randomUUID } from "crypto";
import { mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import { spawn } from "child_process";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type WorkflowResult = {
  output_deck: string;
  findings_count: number;
  duplicated_slides: number;
  preservation_score: number;
  package_valid: boolean;
};

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const priorDeck = formData.get("priorDeck");
    const findingsWorkbook = formData.get("findingsWorkbook");

    if (!(priorDeck instanceof File) || !(findingsWorkbook instanceof File)) {
      return NextResponse.json({ error: "Upload a prior-year PPTX and findings workbook." }, { status: 400 });
    }

    const jobId = randomUUID();
    const repoRoot = path.resolve(process.cwd(), "..", "..");
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
