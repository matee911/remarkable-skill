"""Single-purpose commands wrapping the external tools in the pull pipeline.

Each command has exactly one reason to change (SRP) and exposes the same
narrow, single-method interface (:class:`ShellCommand` -- Interface
Segregation: callers depend only on ``execute()``, never on a command's
internals).
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from rmpull.svg_units import fix_svg_units


class ShellCommand(Protocol):
    """Something that can be executed once and yields a filesystem path."""

    def execute(self) -> Path: ...


def _run(*args: str, cwd: Path) -> None:
    print("+", " ".join(args), file=sys.stderr)
    subprocess.run(args, check=True, cwd=cwd)


@dataclass(frozen=True, slots=True)
class FetchDocumentArchive:
    """Downloads a document from reMarkable Cloud via ``rmapi get``."""

    remote_path: str
    work_dir: Path

    def execute(self) -> Path:
        doc_name = self.remote_path.rsplit("/", 1)[-1]
        _run("rmapi", "get", self.remote_path, cwd=self.work_dir)
        candidates = sorted(self.work_dir.glob(f"{doc_name}*.rmdoc")) or sorted(
            self.work_dir.glob(f"{doc_name}*.zip")
        )
        if not candidates:
            raise FileNotFoundError(
                f"rmapi did not produce an archive for {doc_name!r} in {self.work_dir}"
            )
        return candidates[0]


@dataclass(frozen=True, slots=True)
class RenderPageAnnotationSvg:
    """Renders one page's ``.rm`` strokes to SVG via ``rmc``."""

    rmc_bin: Path
    rm_file: Path
    output_svg: Path

    def execute(self) -> Path:
        _run(
            str(self.rmc_bin),
            "-t",
            "svg",
            "-o",
            str(self.output_svg),
            str(self.rm_file),
            cwd=self.output_svg.parent,
        )
        return self.output_svg


@dataclass(frozen=True, slots=True)
class NormalizeSvgUnits:
    """Rewrites an SVG's dimensions to explicit points (see svg_units)."""

    input_svg: Path
    output_svg: Path

    def execute(self) -> Path:
        self.output_svg.write_text(fix_svg_units(self.input_svg.read_text()))
        return self.output_svg


@dataclass(frozen=True, slots=True)
class ConvertSvgToPdf:
    """Rasterizes a (unit-corrected) SVG to a single-page PDF via cairosvg."""

    cairosvg_bin: Path
    input_svg: Path
    output_pdf: Path

    def execute(self) -> Path:
        _run(
            str(self.cairosvg_bin),
            str(self.input_svg),
            "-o",
            str(self.output_pdf),
            cwd=self.output_pdf.parent,
        )
        return self.output_pdf
