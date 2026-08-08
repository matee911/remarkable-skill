"""Fix the unit ambiguity in ``rmc``'s SVG output.

``rmc -t svg`` emits bare numeric ``width``/``height`` attributes meant as
PDF points, but SVG renderers (cairosvg included) default to treating
unitless numbers as CSS px at 96dpi -- i.e. they silently multiply by
0.75. Left uncorrected, every annotation lands at the wrong scale and
position once merged onto the original page.
"""

import re

_DIMENSIONS = re.compile(r'height="([0-9.]+)" width="([0-9.]+)"')


def fix_svg_units(svg_markup: str) -> str:
    """Rewrite bare-number ``width``/``height`` attributes to explicit ``pt``.

    >>> fix_svg_units('<svg height="643.9" width="447.6" viewBox="0 0 1 1">')
    '<svg height="643.9pt" width="447.6pt" viewBox="0 0 1 1">'

    Attributes that already carry a unit are left untouched:

    >>> fix_svg_units('<svg height="10pt" width="20pt">')
    '<svg height="10pt" width="20pt">'
    """
    return _DIMENSIONS.sub(r'height="\1pt" width="\2pt"', svg_markup)
