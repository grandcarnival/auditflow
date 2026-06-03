from .openxml import (
    PptxMetrics,
    collect_metrics,
    extract_slide_text,
    replace_text_in_clone,
    validate_preservation,
)
from .template import TemplateModel, SlideStructure, TextRun, analyze_template
from .tables import TableUpdateResult, extract_table_matrix, update_table_in_clone
from .charts import ChartSeries, ChartUpdateResult, extract_chart_data, update_chart_in_clone
from .slides import SlideDuplicationResult, duplicate_slide_in_clone
from .validation import PptxValidationReport, ValidationIssue, validate_pptx_package
from .failures import FailureDiagnostic, analyze_failure_modes

__all__ = [
    "ChartSeries",
    "ChartUpdateResult",
    "FailureDiagnostic",
    "PptxMetrics",
    "PptxValidationReport",
    "TemplateModel",
    "SlideStructure",
    "SlideDuplicationResult",
    "TableUpdateResult",
    "TextRun",
    "ValidationIssue",
    "analyze_template",
    "analyze_failure_modes",
    "collect_metrics",
    "extract_chart_data",
    "extract_table_matrix",
    "extract_slide_text",
    "duplicate_slide_in_clone",
    "replace_text_in_clone",
    "update_chart_in_clone",
    "update_table_in_clone",
    "validate_pptx_package",
    "validate_preservation",
]
