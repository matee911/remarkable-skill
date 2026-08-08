#!/usr/bin/env python3
"""CLI adapter for :class:`rmpull.pipeline.PullAnnotatedDocument`.

See ``rmpull/__init__.py`` for the pipeline's sequence diagram and
``../SKILL.md`` for the calibration/troubleshooting notes.
"""

import argparse
import sys
import tempfile
from pathlib import Path

from rmpull.calibration import DEFAULT_CALIBRATION, Calibration
from rmpull.document import Toolchain
from rmpull.pipeline import PullAnnotatedDocument


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("remote_path", help="e.g. notes/my-document")
    parser.add_argument("-o", "--output", required=True, help="output merged PDF path")
    parser.add_argument("--work-dir", default=None, help="scratch dir (default: temp)")
    parser.add_argument("--scale-mult", type=float, default=DEFAULT_CALIBRATION.scale_mult)
    parser.add_argument(
        "--ty", type=float, default=DEFAULT_CALIBRATION.ty_extra, help="extra vertical shift, pt, +up"
    )
    parser.add_argument(
        "--tx", type=float, default=DEFAULT_CALIBRATION.tx_extra, help="extra horizontal shift, pt, +right"
    )
    parser.add_argument("--rmc", default=str(Path(__file__).parent / "venv" / "bin" / "rmc"))
    parser.add_argument("--cairosvg", default=str(Path(__file__).parent / "venv" / "bin" / "cairosvg"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    work_dir = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp())

    command = PullAnnotatedDocument(
        remote_path=args.remote_path,
        output_path=Path(args.output),
        work_dir=work_dir,
        toolchain=Toolchain(rmc_bin=Path(args.rmc), cairosvg_bin=Path(args.cairosvg)),
        calibration=Calibration(
            scale_mult=args.scale_mult, ty_extra=args.ty, tx_extra=args.tx
        ),
    )
    output_path = command.execute()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
