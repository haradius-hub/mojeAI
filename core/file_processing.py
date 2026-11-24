"""Extrakce textového obsahu z podporovaných kancelářských dokumentů."""

import os
import zipfile

MAX_TEXT_CHARS = 100_000
MAX_ARCHIVE_UNCOMPRESSED = 50 * 1024 * 1024
MAX_ARCHIVE_FILES = 5_000


def _over_text_limit(parts, text):
    current = sum(len(part) for part in parts)
    if current + len(text) > MAX_TEXT_CHARS:
        raise ValueError("Textový obsah souboru překračuje limit 100 000 znaků.")
    parts.append(text)


def _check_office_archive(path):
    """Omezí riziko neúměrně velkých ZIP dokumentů před jejich parsováním."""
    if not zipfile.is_zipfile(path):
        raise ValueError("Soubor není platný kancelářský dokument (ZIP/Office kontejner).")

    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ARCHIVE_FILES:
            raise ValueError("Dokument obsahuje příliš mnoho vnitřních souborů.")
        total_size = sum(entry.file_size for entry in entries)
        if total_size > MAX_ARCHIVE_UNCOMPRESSED:
            raise ValueError("Rozbalený obsah dokumentu překračuje bezpečnostní limit 50 MB.")
        for entry in entries:
            if entry.file_size > 0 and entry.compress_size == 0:
                raise ValueError("Dokument obsahuje neplatnou kompresní položku.")
            if entry.compress_size and entry.file_size / entry.compress_size > 200:
                raise ValueError("Dokument má nepřiměřený kompresní poměr.")


def _extract_docx(path):
    from docx import Document

    document = Document(path)
    parts = []
    for paragraph in document.paragraphs:
        if paragraph.text:
            _over_text_limit(parts, paragraph.text + "\n")

    for table_index, table in enumerate(document.tables, start=1):
        _over_text_limit(parts, f"\n[Tabulka {table_index}]\n")
        for row in table.rows:
            cells = [cell.text.replace("\n", " / ").strip() for cell in row.cells]
            _over_text_limit(parts, " | ".join(cells) + "\n")

    return "".join(parts)


def _extract_xlsx(path):
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    parts = []
    try:
        for sheet in workbook.worksheets:
            _over_text_limit(parts, f"\n[List: {sheet.title}]\n")
            for row in sheet.iter_rows(values_only=True):
                values = ["" if value is None else str(value) for value in row]
                if any(values):
                    _over_text_limit(parts, " | ".join(values) + "\n")
    finally:
        workbook.close()
    return "".join(parts)


def _extract_pptx(path):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    presentation = Presentation(path)
    parts = []

    def read_shapes(shapes):
        for shape in shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                read_shapes(shape.shapes)
            elif getattr(shape, "has_text_frame", False):
                text = shape.text.strip()
                if text:
                    _over_text_limit(parts, text + "\n")
            elif getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    values = [cell.text.replace("\n", " / ").strip() for cell in row.cells]
                    _over_text_limit(parts, " | ".join(values) + "\n")

    for slide_number, slide in enumerate(presentation.slides, start=1):
        _over_text_limit(parts, f"\n[Snímek {slide_number}]\n")
        read_shapes(slide.shapes)

    return "".join(parts)


def _extract_odf(path):
    from odf.opendocument import load
    from odf.teletype import extractText

    document = load(path)
    try:
        # extractText projde textové uzly dokumentu včetně buněk tabulek a snímků.
        return extractText(document)
    finally:
        document.close()


def extract_document_text(path, extension):
    """Vrátí text z DOCX/XLSX/PPTX/ODT/ODS/ODP s jednotným limitem."""
    extension = extension.lower()
    supported = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
    if extension not in supported:
        raise ValueError("Nepodporovaný kancelářský formát.")

    _check_office_archive(path)

    if extension == ".docx":
        text = _extract_docx(path)
    elif extension == ".xlsx":
        text = _extract_xlsx(path)
    elif extension == ".pptx":
        text = _extract_pptx(path)
    else:
        text = _extract_odf(path)

    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("Textový obsah souboru překračuje limit 100 000 znaků.")
    return text.strip()
