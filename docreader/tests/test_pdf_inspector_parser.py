import sys
import types
import unittest
from pathlib import Path
from unittest import mock

from docreader.models.document import Document

parser_package = types.ModuleType("docreader.parser")
parser_package.__path__ = [str(Path(__file__).parents[1] / "parser")]
sys.modules.setdefault("docreader.parser", parser_package)


class PDFInspectorParserTest(unittest.TestCase):
    def test_parse_returns_markdown_and_metadata(self):
        result = types.SimpleNamespace(
            markdown="# 标题\n\n正文",
            pdf_type="TextBased",
            confidence=0.98,
            pages_needing_ocr=[2],
            has_encoding_issues=False,
            ocr_reasons_by_page={2: ["suspected_garbled_text"]},
        )
        module = types.SimpleNamespace(
            process_pdf_bytes=mock.Mock(return_value=result),
            __version__="0.2.6",
        )

        with mock.patch.dict(sys.modules, {"pdf_inspector": module}):
            from docreader.parser.pdf_inspector_parser import PDFInspectorParser

            document = PDFInspectorParser(
                file_name="document.pdf", file_type="pdf"
            ).parse_into_text(b"%PDF-1.7")

        self.assertIsInstance(document, Document)
        self.assertEqual(document.content, "# 标题\n\n正文")
        self.assertEqual(document.images, {})
        self.assertEqual(document.metadata["parser_engine"], "pdf_inspector")
        self.assertEqual(document.metadata["parser_version"], "0.2.6")
        self.assertEqual(document.metadata["pdf_type"], "TextBased")
        self.assertEqual(document.metadata["confidence"], 0.98)
        self.assertEqual(document.metadata["pages_needing_ocr"], [2])
        self.assertFalse(document.metadata["has_encoding_issues"])
        self.assertEqual(
            document.metadata["ocr_reasons_by_page"],
            {"2": ["suspected_garbled_text"]},
        )
        module.process_pdf_bytes.assert_called_once_with(b"%PDF-1.7")

    def test_parse_rejects_empty_markdown(self):
        module = types.SimpleNamespace(
            process_pdf_bytes=mock.Mock(
                return_value=types.SimpleNamespace(markdown="   ")
            )
        )

        with mock.patch.dict(sys.modules, {"pdf_inspector": module}):
            from docreader.parser.pdf_inspector_parser import PDFInspectorParser

            parser = PDFInspectorParser(file_name="empty.pdf", file_type="pdf")
            with self.assertRaisesRegex(ValueError, "empty Markdown"):
                parser.parse_into_text(b"%PDF-1.7")

    def test_availability_reports_missing_package(self):
        from docreader.parser.pdf_inspector_parser import pdf_inspector_available

        with mock.patch(
            "docreader.parser.pdf_inspector_parser.importlib.util.find_spec",
            return_value=None,
        ):
            available, reason = pdf_inspector_available()

        self.assertFalse(available)
        self.assertIn("pdf-inspector", reason)

    def test_availability_rejects_incompatible_package(self):
        from docreader.parser.pdf_inspector_parser import pdf_inspector_available

        module = types.SimpleNamespace()
        with mock.patch(
            "docreader.parser.pdf_inspector_parser.importlib.util.find_spec",
            return_value=object(),
        ), mock.patch(
            "docreader.parser.pdf_inspector_parser.importlib.import_module",
            return_value=module,
        ):
            available, reason = pdf_inspector_available()

        self.assertFalse(available)
        self.assertIn("process_pdf_bytes", reason)

if __name__ == "__main__":
    unittest.main()
