import importlib
import importlib.metadata
import importlib.util
from typing import Any, Dict, Optional, Tuple

from docreader.models.document import Document
from docreader.parser.base_parser import BaseParser


def pdf_inspector_available(
    overrides: Optional[Dict[str, str]] = None,
) -> Tuple[bool, str]:
    if importlib.util.find_spec("pdf_inspector") is None:
        return False, "请安装 pdf-inspector==0.2.6"
    try:
        module = importlib.import_module("pdf_inspector")
    except Exception as exc:
        return False, f"pdf-inspector 导入失败: {exc}"
    if not callable(getattr(module, "process_pdf_bytes", None)):
        return False, "pdf-inspector 缺少 process_pdf_bytes API"
    return True, ""


def _metadata_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_metadata_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _metadata_value(item) for key, item in value.items()}
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return _metadata_value(enum_value)
    return str(value)


def _package_version(module: Any) -> str:
    version = getattr(module, "__version__", None)
    if version:
        return str(version)
    try:
        return importlib.metadata.version("pdf-inspector")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


class PDFInspectorParser(BaseParser):
    def parse_into_text(self, content: bytes) -> Document:
        module = importlib.import_module("pdf_inspector")
        result = module.process_pdf_bytes(content)
        markdown = getattr(result, "markdown", "")
        if not isinstance(markdown, str) or not markdown.strip():
            raise ValueError("PDF Inspector returned empty Markdown")

        metadata: Dict[str, Any] = {
            "parser_engine": "pdf_inspector",
            "parser_version": _package_version(module),
        }
        for name in (
            "pdf_type",
            "confidence",
            "pages_needing_ocr",
            "has_encoding_issues",
            "ocr_reasons_by_page",
        ):
            value = getattr(result, name, None)
            if value is not None:
                metadata[name] = _metadata_value(value)

        return Document(content=markdown, metadata=metadata)
