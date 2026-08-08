"""Geometry for placing a reMarkable annotation overlay onto a PDF page.

reMarkable applies its own "bestFit" scaling plus margins when it imports
a PDF for on-device annotation, and does not expose the resulting
geometry through any public metadata. There is no formula derived from
first principles here -- :data:`DEFAULT_CALIBRATION` was reverse
engineered by visual A/B comparison against one real annotated document.
Treat it as a starting point and re-tune per document family if needed.
"""

from dataclasses import dataclass

from pypdf import Transformation


@dataclass(frozen=True, slots=True)
class Size:
    """A page or overlay's width/height, in PDF points."""

    width: float
    height: float


def _scale_and_offset(
    base: Size, overlay: Size, scale_mult: float, ty_extra: float, tx_extra: float
) -> tuple[float, float, float]:
    """Compute (scale, x-offset, y-offset) to place ``overlay`` on ``base``.

    The overlay is scaled uniformly to ``base``'s width (times
    ``scale_mult``), then centered, then nudged by ``tx_extra``/``ty_extra``.

    >>> s, tx, ty = _scale_and_offset(
    ...     Size(612, 792), Size(447.6, 643.9), scale_mult=1.0, ty_extra=0, tx_extra=0
    ... )
    >>> round(s, 4)
    1.3673
    >>> round(tx, 2), round(ty, 2)
    (0.0, -44.2)

    A ``scale_mult`` < 1 shrinks the overlay further and re-centers it:

    >>> s, tx, ty = _scale_and_offset(
    ...     Size(612, 792), Size(447.6, 643.9), scale_mult=0.86, ty_extra=0, tx_extra=0
    ... )
    >>> round(s, 4)
    1.1759
    >>> tx > 0
    True
    """
    scale = (base.width / overlay.width) * scale_mult
    scaled_height = overlay.height * scale
    tx = (base.width - overlay.width * scale) / 2 + tx_extra
    ty = (base.height - scaled_height) / 2 + ty_extra
    return scale, tx, ty


@dataclass(frozen=True, slots=True)
class Calibration:
    """Knows how to fit an annotation overlay onto a base PDF page.

    A rich value object, not a bag of numbers: callers ask it for a
    ready-to-use :class:`pypdf.Transformation` rather than reimplementing
    the scale/offset math themselves (keeps that math in one place, per
    document -- DRY).
    """

    scale_mult: float
    ty_extra: float
    tx_extra: float

    def transform_for(self, base: Size, overlay: Size) -> Transformation:
        """Build the pypdf transform that places ``overlay`` onto ``base``."""
        scale, tx, ty = _scale_and_offset(
            base, overlay, self.scale_mult, self.ty_extra, self.tx_extra
        )
        return Transformation().scale(scale, scale).translate(tx, ty)


# Reverse engineered by visual A/B calibration against one real annotated
# document (see module docstring). Good starting point, not a general law.
DEFAULT_CALIBRATION = Calibration(scale_mult=0.86, ty_extra=99, tx_extra=-38)
