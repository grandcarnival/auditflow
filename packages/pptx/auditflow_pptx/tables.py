from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import etree

from .openxml import NS, read_package, serialize_xml, write_package


@dataclass(frozen=True)
class TableUpdateResult:
    slide_index: int
    table_index: int
    original_rows: int
    updated_rows: int
    column_count: int
    style_preserved: bool
    merged_cells_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_index": self.slide_index,
            "table_index": self.table_index,
            "original_rows": self.original_rows,
            "updated_rows": self.updated_rows,
            "column_count": self.column_count,
            "style_preserved": self.style_preserved,
            "merged_cells_preserved": self.merged_cells_preserved,
        }


def update_table_in_clone(
    source: str | Path,
    target: str | Path,
    slide_index: int,
    rows: list[list[Any]],
    table_index: int = 0,
    preserve_header: bool = False,
) -> TableUpdateResult:
    infos, parts = read_package(source)
    slide_name = f"ppt/slides/slide{slide_index}.xml"
    if slide_name not in parts:
        raise ValueError(f"Slide {slide_index} was not found.")

    root = etree.fromstring(parts[slide_name])
    tables = root.xpath(".//a:tbl", namespaces=NS)
    if table_index >= len(tables):
        raise ValueError(f"Table {table_index} was not found on slide {slide_index}.")

    table = tables[table_index]
    original_rows = table.xpath("./a:tr", namespaces=NS)
    if not original_rows:
        raise ValueError("Cannot update a table with no rows.")

    original_row_count = len(original_rows)
    original_style_fingerprint = _row_style_fingerprint(table)
    original_merge_fingerprint = _row_merge_fingerprint(table)
    column_count = _column_count(table)

    if preserve_header:
        body_rows = rows
        desired_total = 1 + len(body_rows)
        _resize_rows(table, desired_total, prototype_index=1 if original_row_count > 1 else 0)
        target_rows = table.xpath("./a:tr", namespaces=NS)[1:]
    else:
        body_rows = rows
        _resize_rows(table, len(body_rows), prototype_index=1 if original_row_count > 1 else 0)
        target_rows = table.xpath("./a:tr", namespaces=NS)

    for row_node, values in zip(target_rows, body_rows):
        _write_row(row_node, values, column_count)

    parts[slide_name] = serialize_xml(root)
    updated_root = etree.fromstring(parts[slide_name])
    updated_tables = updated_root.xpath(".//a:tbl", namespaces=NS)
    updated_table = updated_tables[table_index]
    write_package(target, infos, parts)

    return TableUpdateResult(
        slide_index=slide_index,
        table_index=table_index,
        original_rows=original_row_count,
        updated_rows=len(updated_table.xpath("./a:tr", namespaces=NS)),
        column_count=column_count,
        style_preserved=_style_preserved(original_style_fingerprint, _row_style_fingerprint(updated_table)),
        merged_cells_preserved=_merge_preserved(original_merge_fingerprint, _row_merge_fingerprint(updated_table)),
    )


def extract_table_matrix(path: str | Path, slide_index: int, table_index: int = 0) -> list[list[str]]:
    _, parts = read_package(path)
    slide_name = f"ppt/slides/slide{slide_index}.xml"
    root = etree.fromstring(parts[slide_name])
    tables = root.xpath(".//a:tbl", namespaces=NS)
    table = tables[table_index]
    matrix: list[list[str]] = []
    for row in table.xpath("./a:tr", namespaces=NS):
        matrix.append([_cell_text(cell) for cell in row.xpath("./a:tc", namespaces=NS)])
    return matrix


def _resize_rows(table: etree._Element, desired_count: int, prototype_index: int) -> None:
    rows = table.xpath("./a:tr", namespaces=NS)
    desired_count = max(1, desired_count)
    while len(rows) > desired_count:
        table.remove(rows[-1])
        rows = table.xpath("./a:tr", namespaces=NS)
    while len(rows) < desired_count:
        prototype = rows[min(prototype_index, len(rows) - 1)]
        new_row = copy.deepcopy(prototype)
        _clear_row(new_row)
        table.append(new_row)
        rows = table.xpath("./a:tr", namespaces=NS)


def _write_row(row: etree._Element, values: list[Any], column_count: int) -> None:
    cells = row.xpath("./a:tc", namespaces=NS)
    for index, cell in enumerate(cells[:column_count]):
        _set_cell_text(cell, _format_cell_value(values[index]) if index < len(values) else "")


def _clear_row(row: etree._Element) -> None:
    for cell in row.xpath("./a:tc", namespaces=NS):
        _set_cell_text(cell, "")


def _set_cell_text(cell: etree._Element, text: str) -> None:
    text_nodes = cell.xpath(".//a:t", namespaces=NS)
    if text_nodes:
        text_nodes[0].text = text
        for extra in text_nodes[1:]:
            extra.text = ""
        return

    tx_body = cell.find("a:txBody", namespaces=NS)
    if tx_body is None:
        tx_body = etree.SubElement(cell, f"{{{NS['a']}}}txBody")
        etree.SubElement(tx_body, f"{{{NS['a']}}}bodyPr")
        etree.SubElement(tx_body, f"{{{NS['a']}}}lstStyle")
    paragraph = etree.SubElement(tx_body, f"{{{NS['a']}}}p")
    run = etree.SubElement(paragraph, f"{{{NS['a']}}}r")
    node = etree.SubElement(run, f"{{{NS['a']}}}t")
    node.text = text


def _cell_text(cell: etree._Element) -> str:
    return " ".join(node.text or "" for node in cell.xpath(".//a:t", namespaces=NS))


def _format_cell_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _column_count(table: etree._Element) -> int:
    grid_columns = table.xpath("./a:tblGrid/a:gridCol", namespaces=NS)
    if grid_columns:
        return len(grid_columns)
    rows = table.xpath("./a:tr", namespaces=NS)
    return len(rows[0].xpath("./a:tc", namespaces=NS)) if rows else 0


def _row_style_fingerprint(table: etree._Element) -> list[list[str]]:
    fingerprints: list[list[str]] = []
    table_pr = table.find("a:tblPr", namespaces=NS)
    table_pr_text = etree.tostring(table_pr, encoding="unicode") if table_pr is not None else ""
    for row in table.xpath("./a:tr", namespaces=NS):
        row_fingerprint = [table_pr_text, row.get("h", "")]
        for node in row.xpath(".//a:tcPr|.//a:lnL|.//a:lnR|.//a:lnT|.//a:lnB", namespaces=NS):
            clone = copy.deepcopy(node)
            for text in clone.xpath(".//a:t", namespaces=NS):
                text.text = ""
            row_fingerprint.append(etree.tostring(clone, encoding="unicode"))
        fingerprints.append(row_fingerprint)
    return fingerprints


def _row_merge_fingerprint(table: etree._Element) -> list[list[tuple[str, str, str, str]]]:
    values: list[list[tuple[str, str, str, str]]] = []
    for row in table.xpath("./a:tr", namespaces=NS):
        row_values: list[tuple[str, str, str, str]] = []
        for cell in row.xpath("./a:tc", namespaces=NS):
            row_values.append((
                cell.get("gridSpan", ""),
                cell.get("rowSpan", ""),
                cell.get("hMerge", ""),
                cell.get("vMerge", ""),
            ))
        values.append(row_values)
    return values


def _style_preserved(original: list[list[str]], updated: list[list[str]]) -> bool:
    if len(updated) < min(1, len(original)):
        return False
    comparable = min(len(original), len(updated))
    if updated[:comparable] != original[:comparable]:
        return False
    if len(updated) <= len(original):
        return True
    prototype = original[1] if len(original) > 1 else original[0]
    return all(row == prototype for row in updated[len(original):])


def _merge_preserved(
    original: list[list[tuple[str, str, str, str]]],
    updated: list[list[tuple[str, str, str, str]]],
) -> bool:
    comparable = min(len(original), len(updated))
    if updated[:comparable] != original[:comparable]:
        return False
    if len(updated) <= len(original):
        return True
    prototype = original[1] if len(original) > 1 else original[0]
    return all(row == prototype for row in updated[len(original):])
