"""The extracted reMarkable document archive, as a domain object.

:class:`RemarkableArchive` owns the on-disk layout of a ``.rmdoc``/``.zip``
export (the ``.content`` page-ordering file, the base PDF, the per-page
``.rm`` stroke files) so nothing else in the pipeline needs to know that
layout. Behaviour lives with the data it operates on -- a rich model, not
a struct plus free functions.
"""

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path


class DocumentContentMissing(Exception):
    """Raised when an archive has metadata but no actual page content.

    Seen in the wild when a document's cloud copy has been orphaned by a
    botched ``rmapi rm`` racing a concurrent on-device edit: the tablet
    believes it already synced, so it never re-pushes, and ``rmapi get``
    forever returns a metadata-only archive for that document ID. The
    only known recovery is duplicating the document on the tablet to get
    a fresh ID.
    """


def _page_ids_from_content(content: dict) -> tuple[str, ...]:
    """Extract the ordered page IDs from a ``.content`` file's parsed JSON.

    reMarkable's ``.content`` schema has changed shape across software
    versions: older exports have a flat top-level ``"pages"`` list of ID
    strings, newer ones nest it under ``"cPages": {"pages": [{"id": ...}]}``.
    Both are handled so callers don't need to know which one they got.

    >>> _page_ids_from_content({"pages": ["a", "b"]})
    ('a', 'b')

    >>> _page_ids_from_content({"cPages": {"pages": [{"id": "a"}, {"id": "b"}]}})
    ('a', 'b')
    """
    if "pages" in content and isinstance(content["pages"], list):
        return tuple(content["pages"])
    return tuple(page["id"] for page in content["cPages"]["pages"])


@dataclass(frozen=True, slots=True)
class RemarkableArchive:
    """An extracted reMarkable document: base PDF plus per-page strokes."""

    extract_dir: Path
    base_pdf_path: Path
    _page_ids: tuple[str, ...]
    _rm_dir: Path

    @classmethod
    def open(cls, archive_path: Path, extract_dir: Path) -> "RemarkableArchive":
        """Unzip ``archive_path`` into ``extract_dir`` and index its pages."""
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(extract_dir)

        content_files = list(extract_dir.glob("*.content"))
        pdf_files = list(extract_dir.glob("*.pdf"))
        if not content_files or not pdf_files:
            raise DocumentContentMissing(
                f"{archive_path.name} has no .content/.pdf -- metadata-only "
                "download (see rmpull.archive.DocumentContentMissing)"
            )

        content = json.loads(content_files[0].read_text())
        page_ids = _page_ids_from_content(content)
        return cls(
            extract_dir=extract_dir,
            base_pdf_path=pdf_files[0],
            _page_ids=page_ids,
            _rm_dir=extract_dir / content_files[0].stem,
        )

    @property
    def page_count(self) -> int:
        return len(self._page_ids)

    def rm_file_for_page(self, index: int) -> Path | None:
        """The ``.rm`` stroke file for page ``index``, if that page has any."""
        candidate = self._rm_dir / f"{self._page_ids[index]}.rm"
        return candidate if candidate.exists() else None
