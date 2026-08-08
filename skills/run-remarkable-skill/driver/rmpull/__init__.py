"""Pull a reMarkable document's hand-drawn annotations and merge them onto
the original PDF.

``rmapi geta`` (the built-in "get with annotations" command) cannot parse
the ``.rm`` v6 format used by current reMarkable software. This package
reimplements the same job as a small pipeline of single-purpose
:class:`~rmpull.commands.ShellCommand` objects, composed by the
:class:`~rmpull.pipeline.PullAnnotatedDocument` command:

::

    CLI          Pull            RM           Archive        Page           Ann          FS
    (pull_       (PullAnnotated  (rmapi       (Remarkable    (Document      (Page        (rmc /
    annotated.py) Document)      cloud)       Archive)       Page)          Annotation)  cairosvg)
     |             |              |             |              |             |             |
     |--execute()->|              |             |              |             |             |
     |             |--FetchDocumentArchive.execute()---------->|             |             |
     |             |              |             |              |             |             |
     |             |<-------------extracted archive dir--------|             |             |
     |             |                                            |             |             |
     |             |--open(extracted dir)-------------------->|             |             |
     |             |                                            |             |             |
     |             |             for each base PDF page:                    |             |
     |             |--page(index)---------------------------->|             |             |
     |             |<-DocumentPage (+ optional PageAnnotation)-|             |             |
     |             |                                            |             |             |
     |             |         [page has annotations]                        |             |
     |             |--merged(calibration)-->|                              |             |
     |             |                        |--overlay_pdf(rmc_bin,        |             |
     |             |                        |   cairosvg_bin, work_dir)--->|             |
     |             |                        |                              |--RenderPageAnnotationSvg.execute() (rmc)-->|
     |             |                        |                              |<--------raw SVG-------------------------|
     |             |                        |                              |--NormalizeSvgUnits.execute() (pure, in-process)
     |             |                        |                              |--ConvertSvgToPdf.execute() (cairosvg)--->|
     |             |                        |                              |<--------overlay PDF----------------------|
     |             |                        |<-------overlay PDF path------|             |             |
     |             |                        |--calibration.transform_for(...) + merge    |             |
     |             |<---merged PdfWriter page|                              |             |             |
     |             |                                            |             |             |
     |             |         [page has no annotations]                     |             |
     |             |--merged(calibration)-->|                              |             |
     |             |<-original PdfWriter page, unchanged--------|             |             |
     |             |                                            |             |             |
     |<--output PDF path--|                                     |             |             |
"""
