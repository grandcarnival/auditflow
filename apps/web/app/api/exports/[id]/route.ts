import { readFile } from "fs/promises";
import path from "path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[a-f0-9-]{36}$/.test(id)) {
    return NextResponse.json({ error: "Invalid export id." }, { status: 400 });
  }

  const repoRoot = path.resolve(process.cwd(), "..", "..");
  const exportPath = path.join(repoRoot, ".runtime", "jobs", id, "auditflow-export.pptx");
  try {
    const file = await readFile(exportPath);
    return new Response(file, {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Content-Disposition": 'attachment; filename="auditflow-export.pptx"',
      },
    });
  } catch {
    return NextResponse.json({ error: "Export not found." }, { status: 404 });
  }
}

