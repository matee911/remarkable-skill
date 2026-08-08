"""Rich domain objects for merging one document's pages and annotations.

:class:`DocumentPage` and :class:`PageAnnotation` own the behaviour of
producing a merged page, not just the data describing one -- callers ask
a page to merge *itself*, rather than a free function reaching into page
internals (avoids an anemic model).
"""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PageObject, PdfReader

from rmpull.calibration import Calibration, Size
from rmpull.commands import ConvertSvgToPdf, NormalizeSvgUnits, RenderPageAnnotationSvg


@dataclass(frozen=True, slots=True)
class Toolchain:
    """Where to find the external binaries this pipeline shells out to."""

    rmc_bin: Path
    cairosvg_bin: Path


@dataclass(frozen=True, slots=True)
class PageAnnotation:
    """One page's hand-drawn strokes, and how to turn them into a PDF overlay."""

    rm_file: Path

    def overlay_pdf(self, toolchain: Toolchain, work_dir: Path, tag: str) -> Path:
        """Render this annotation to a standalone, unit-corrected PDF overlay."""
        raw_svg = RenderPageAnnotationSvg(
            rmc_bin=toolchain.rmc_bin,
            rm_file=self.rm_file,
            output_svg=work_dir / f"{tag}.svg",
        ).execute()
        fixed_svg = NormalizeSvgUnits(
            input_svg=raw_svg, output_svg=work_dir / f"{tag}_pt.svg"
        ).execute()
        return ConvertSvgToPdf(
            cairosvg_bin=toolchain.cairosvg_bin,
            input_svg=fixed_svg,
            output_pdf=work_dir / f"{tag}_overlay.pdf",
        ).execute()


@dataclass(frozen=True, slots=True)
class DocumentPage:
    """One page of the base PDF, with its optional annotation."""

    index: int
    base_page: PageObject
    annotation: PageAnnotation | None
    calibration: Calibration
    toolchain: Toolchain
    work_dir: Path

    def merged(self) -> PageObject:
        """Return the base page with its annotation overlay merged in.

        A no-op (returns the base page unchanged) when this page has no
        annotation.
        """
        if self.annotation is None:
            return self.base_page

        overlay_pdf_path = self.annotation.overlay_pdf(
            self.toolchain, self.work_dir, tag=f"p{self.index}"
        )
        overlay_page = PdfReader(overlay_pdf_path).pages[0]

        base_size = Size(
            width=float(self.base_page.mediabox.width),
            height=float(self.base_page.mediabox.height),
        )
        overlay_size = Size(
            width=float(overlay_page.mediabox.width),
            height=float(overlay_page.mediabox.height),
        )
        transform = self.calibration.transform_for(base_size, overlay_size)
        self.base_page.merge_transformed_page(overlay_page, transform)
        return self.base_page
