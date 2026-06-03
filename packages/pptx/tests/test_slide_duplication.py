from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import collect_metrics, duplicate_slide_in_clone, extract_slide_text, replace_text_in_clone, validate_preservation


def test_duplicate_slide_copies_chart_embedding_and_notes(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    local_source = tmp_path / "source.pptx"
    target = tmp_path / "duplicated.pptx"
    shutil.copyfile(source, local_source)

    result = duplicate_slide_in_clone(local_source, target, slide_index=2)
    metrics = collect_metrics(target)
    validation = validate_preservation(local_source, target)
    slide_text = extract_slide_text(target)

    assert result.new_slide_index == 4
    assert result.notes_preserved
    assert result.chart_parts_copied == 1
    assert result.embedded_parts_copied == 1
    assert metrics.slide_count == 4
    assert metrics.chart_count == 2
    assert metrics.notes_count == 4
    assert "Executive Summary" in slide_text[3]
    assert validation["checks"]["masters_preserved"]
    assert validation["checks"]["layouts_preserved"]
    assert _package_valid(target)
    assert "ppt/charts/chart2.xml" in result.copied_parts
    assert "ppt/embeddings/Microsoft_Excel_Sheet2.xlsx" in result.copied_parts


def test_slide_specific_text_replacement_after_duplication(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    duplicated = tmp_path / "duplicated.pptx"
    target = tmp_path / "second_finding.pptx"

    duplicate_slide_in_clone(source, duplicated, slide_index=3)
    replace_text_in_clone(
        duplicated,
        target,
        {"Finding Detail | Access Governance": "Finding Detail | Vendor Access"},
        slide_index=4,
    )

    slide_text = extract_slide_text(target)
    assert "Finding Detail | Access Governance" in slide_text[2]
    assert "Finding Detail | Vendor Access" in slide_text[3]


def test_duplicate_slide_deduplicates_image_assets_by_reusing_media_part(tmp_path: Path) -> None:
    source = tmp_path / "image_source.pptx"
    target = tmp_path / "image_duplicated.pptx"
    _create_image_fixture(source, tmp_path / "asset.png")

    duplicate_slide_in_clone(source, target, slide_index=1)
    metrics = collect_metrics(target)

    assert metrics.slide_count == 2
    assert metrics.image_count == 1
    assert _package_valid(target)
    with zipfile.ZipFile(target) as zf:
        rels = zf.read("ppt/slides/_rels/slide2.xml.rels").decode("utf-8")
    assert "../media/image1.png" in rels


def _create_image_fixture(path: Path, image_path: Path) -> None:
    Image.new("RGB", (64, 64), color=(31, 78, 121)).save(image_path)
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Image Slide"
    slide.shapes.add_picture(str(image_path), Inches(1), Inches(1.5), width=Inches(1.5), height=Inches(1.5))
    prs.save(path)


def _package_valid(path: Path) -> bool:
    with zipfile.ZipFile(path) as zf:
        return zf.testzip() is None
