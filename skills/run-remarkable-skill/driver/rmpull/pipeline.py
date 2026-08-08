"""The top-level command: pull a document, merge its annotations, write it out."""

import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from rmpull.archive import RemarkableArchive
from rmpull.calibration import DEFAULT_CALIBRATION, Calibration
from rmpull.commands import FetchDocumentArchive
from rmpull.document import DocumentPage, PageAnnotation, Toolchain


@dataclass(frozen=True, slots=True)
class PullAnnotatedDocument:
    """Command: fetch ``remote_path`` and write it, annotations merged, to ``output_path``."""

    remote_path: str
    output_path: Path
    work_dir: Path
    toolchain: Toolchain
    calibration: Calibration = DEFAULT_CALIBRATION

    def execute(self) -> Path:
        doc_name = self.remote_path.rsplit("/", 1)[-1]
        self.work_dir.mkdir(parents=True, exist_ok=True)

        archive_path = FetchDocumentArchive(
            remote_path=self.remote_path, work_dir=self.work_dir
        ).execute()
        archive = RemarkableArchive.open(
            archive_path, extract_dir=self.work_dir / f"{doc_name}_extract"
        )

        base_pdf = PdfReader(archive.base_pdf_path)
        writer = PdfWriter()
        annotated_pages = 0

        for index, base_page in enumerate(base_pdf.pages):
            rm_file = archive.rm_file_for_page(index)
            annotation = PageAnnotation(rm_file) if rm_file is not None else None
            annotated_pages += annotation is not None

            page = DocumentPage(
                index=index,
                base_page=base_page,
                annotation=annotation,
                calibration=self.calibration,
                toolchain=self.toolchain,
                work_dir=self.work_dir,
            )
            writer.add_page(page.merged())

        if annotated_pages == 0:
            print("warning: no .rm annotation files found in this document", file=sys.stderr)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "wb") as f:
            writer.write(f)
        return self.output_path
