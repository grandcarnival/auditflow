from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "ai"))
sys.path.insert(0, str(ROOT / "packages" / "documents"))
sys.path.insert(0, str(ROOT / "packages" / "pptx"))
sys.path.insert(0, str(ROOT / "packages" / "workflow"))

from auditflow_workflow import run_mvp_workflow  # noqa: E402


STATUS_QUEUED = "queued"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AuditFlow AI Supabase processing worker.")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job and exit.")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    args = parser.parse_args()

    worker = SupabaseWorker()
    while True:
        processed = worker.process_next_job()
        if args.once:
            return
        if not processed:
            time.sleep(args.poll_interval)


class SupabaseWorker:
    def __init__(self) -> None:
        self.url = _required_env("SUPABASE_URL").rstrip("/")
        self.key = _required_env("SUPABASE_SERVICE_ROLE_KEY")
        self.bucket = os.environ.get("AUDITFLOW_STORAGE_BUCKET", "auditflow-artifacts")

    def process_next_job(self) -> bool:
        job = self.next_queued_job()
        if not job:
            return False

        job_id = job["id"]
        try:
            self.update_job(job_id, {"status": STATUS_PROCESSING, "started_at": "now()"})
            result = self.process_job(job)
            self.update_job(
                job_id,
                {
                    "status": STATUS_COMPLETED,
                    "completed_at": "now()",
                    "output_deck_path": result["output_deck_path"],
                    "report_path": result["report_path"],
                    "manifest_path": result["manifest_path"],
                    "preservation_score": result["preservation_score"],
                    "package_valid": result["package_valid"],
                    "findings_count": result["findings_count"],
                    "duplicated_slides": result["duplicated_slides"],
                    "error_message": None,
                },
            )
        except Exception as error:
            self.update_job(
                job_id,
                {
                    "status": STATUS_FAILED,
                    "completed_at": "now()",
                    "error_message": str(error)[:4000],
                },
            )
        return True

    def next_queued_job(self) -> dict[str, Any] | None:
        rows = self.request_json(
            "GET",
            "/rest/v1/auditflow_jobs?status=eq.queued&order=created_at.asc&limit=1&select=*",
        )
        return rows[0] if rows else None

    def update_job(self, job_id: str, patch: dict[str, Any]) -> None:
        normalized = {key: value for key, value in patch.items() if value != "now()"}
        now_fields = {key: value for key, value in patch.items() if value == "now()"}
        if now_fields:
            timestamp = _utc_now()
            for key in now_fields:
                normalized[key] = timestamp
            normalized["updated_at"] = timestamp
        else:
            normalized["updated_at"] = _utc_now()
        self.request_json(
            "PATCH",
            f"/rest/v1/auditflow_jobs?id=eq.{urllib.parse.quote(job_id)}",
            body=normalized,
        )

    def process_job(self, job: dict[str, Any]) -> dict[str, Any]:
        job_id = job["id"]
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            prior = workdir / "prior.pptx"
            findings = workdir / "findings.xlsx"
            output = workdir / "auditflow-export.pptx"
            report = workdir / "report.json"
            manifest = workdir / "manifest.json"

            self.download_object(job["prior_deck_path"], prior)
            self.download_object(job["findings_workbook_path"], findings)

            workflow = run_mvp_workflow(
                prior_deck=prior,
                findings_workbook=findings,
                output_deck=output,
                fiscal_year=2026,
                report_path=report,
                manifest_path=manifest,
            )

            output_path = f"jobs/{job_id}/output/auditflow-export.pptx"
            report_path = f"jobs/{job_id}/output/report.json"
            manifest_path = f"jobs/{job_id}/output/manifest.json"
            self.upload_object(output_path, output, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            self.upload_object(report_path, report, "application/json")
            self.upload_object(manifest_path, manifest, "application/json")

            return {
                "output_deck_path": output_path,
                "report_path": report_path,
                "manifest_path": manifest_path,
                "preservation_score": workflow.preservation_score,
                "package_valid": workflow.package_valid,
                "findings_count": workflow.findings_count,
                "duplicated_slides": workflow.duplicated_slides,
            }

    def download_object(self, object_path: str, target: Path) -> None:
        data = self.request_bytes("GET", self.storage_path(object_path))
        target.write_bytes(data)

    def upload_object(self, object_path: str, source: Path, content_type: str) -> None:
        self.request_bytes(
            "POST",
            self.storage_path(object_path),
            body=source.read_bytes(),
            content_type=content_type,
            extra_headers={"x-upsert": "true"},
        )

    def storage_path(self, object_path: str) -> str:
        return f"/storage/v1/object/{self.bucket}/{urllib.parse.quote(object_path, safe='/')}"

    def request_json(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        response = self.request_bytes(method, path, body=data, content_type="application/json")
        return json.loads(response.decode("utf-8")) if response else None

    def request_bytes(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        content_type: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> bytes:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        if extra_headers:
            headers.update(extra_headers)
        request = urllib.request.Request(f"{self.url}{path}", data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase request failed: {error.code} {detail}") from error


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
