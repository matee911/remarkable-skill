---
name: run-remarkable-skill
description: Push Markdown notes to a reMarkable tablet wirelessly (MD -> PDF -> cloud upload via rmapi) and pull hand-written annotations back off the tablet, merged onto the original PDF. Use when asked to sync, upload, push, or send files to reMarkable/reMarkable Connect, or to read/pull/download/extract annotations, highlights, or handwriting from a reMarkable document.
---

Paths below are relative to this repo's root (`remarkable-skill/`). The
driver scripts live in `skills/run-remarkable-skill/driver/`.

This is a macOS-only, no-GUI pipeline driven entirely by shell/Python
scripts — there is no app window to screenshot. "Running" it means
invoking the drivers below against a real reMarkable Cloud account and
checking the resulting PDF.

## Prerequisites

- macOS with Homebrew, Google Chrome installed in `/Applications`
- A reMarkable Cloud account (reMarkable Connect or classic) with at
  least one document already in it
- pyenv with a Python >=3.10 available (the `rmc` annotation-parsing
  library requires it; system Python on macOS is often 3.9)

```bash
./driver/setup.sh
```

This installs (idempotently — safe to re-run):
- `rmapi` (ddvk/rmapi prebuilt release binary) to `/usr/local/bin` (asks
  for `sudo` once)
- `pandoc` via `brew`
- a local venv at `driver/venv` with `driver/requirements.txt` (runtime:
  `rmc`, `cairosvg`, `pypdf`) and `driver/requirements-dev.txt`
  (lint/typecheck: `ruff`, `pyrefly` — only needed if you're editing
  `rmpull/`)

On first run it also runs `rmapi ls`, which triggers reMarkable's
one-time device pairing if not already logged in: it prints "Enter
one-time code" — get one at
https://my.remarkable.com/device/browser/connect and paste it in. The
resulting token is cached in `~/Library/Application Support/rmapi/`,
independent of this repo, so this is a true one-time step per machine.

## Run (agent path)

### Upload: Markdown -> reMarkable, wirelessly

```bash
./driver/sync_to_remarkable.sh <src_dir_with_md_files> <remote_folder>
```

Verified this session with a real file:

```bash
$ ./driver/sync_to_remarkable.sh /tmp/notes-src notes/test-folder
uploading example-note...
uploading: [/var/folders/.../example-note.pdf]...OK
done: 1 files uploaded to notes/test-folder
```

It converts every `*.md` in the source dir to PDF (`pandoc` -> HTML ->
headless Chrome print-to-pdf) and pushes each one with `rmapi put`. No
cable — the tablet picks it up over Wi-Fi via its normal cloud sync
(seconds to a couple of minutes, depending on how up to date its own
sync loop is).

### Download: pull annotations back, merged onto the original PDF

```bash
./driver/venv/bin/python3 driver/pull_annotated.py "<remote_folder>/<doc_name>" -o out.pdf
```

Verified this session against a real annotated document (a doc with a
hand-drawn `+`, dots next to bullet points, and an `L`-shaped bracket):

```bash
$ ./driver/venv/bin/python3 driver/pull_annotated.py \
    "notes/example-doc" -o /tmp/rm_skill_test_output.pdf
+ rmapi get notes/example-doc
downloading: [notes/example-doc]...
OK
+ .../venv/bin/rmc -t svg -o .../example-doc_p1.svg .../<page-id>.rm
+ .../venv/bin/cairosvg .../example-doc_p1_pt.svg -o .../overlay.pdf
wrote /tmp/rm_skill_test_output.pdf
```

Resulting page 2 had the annotations landing correctly next to their
bullet points (verified visually this session; no screenshot is
checked into this repo since the test document is a private note —
re-run the command above against your own document to verify locally).

`rmapi` has no built-in equivalent that works reliably (see Gotchas) —
`pull_annotated.py` is a thin CLI adapter over the `rmpull` package
(`driver/rmpull/`), which reimplements `geta` by hand as a small
pipeline of single-purpose commands: `rmapi get` -> unzip the `.rmdoc`
archive -> `rmc` renders each page's `.rm` strokes to SVG -> fix SVG
units (see Gotchas) -> `cairosvg` to PDF -> `pypdf` merges the
annotation layer onto the matching page of the original PDF, with a
calibrated scale/offset (see Gotchas). The full sequence is diagrammed
in `driver/rmpull/__init__.py`'s module docstring.

Each module in `rmpull/` has one job (SRP): `svg_units.py` and
`calibration.py` hold the pure, doctested geometry/text logic;
`commands.py` wraps each external tool call behind a narrow
single-method `ShellCommand` interface; `archive.py` and `document.py`
are the rich domain objects (a `DocumentPage` merges *itself*, given a
`Calibration`); `pipeline.py` is the top-level `PullAnnotatedDocument`
command that composes all of the above.

Before committing changes to `rmpull/`, run the full quality gate
(doctests + ruff + pyrefly):

```bash
./driver/run_tests.sh
```

## Gotchas

- **`rmapi geta` doesn't work on current reMarkable software.** It
  fails with `Unknown header` or `archive does not contain a unique
  content file` on `.rm` v6 files (the format used by reMarkable
  Connect / recent firmware). This is a known, apparently abandoned
  upstream issue (ddvk/rmapi#35) — no fix, no workaround from rmapi
  itself. `pull_annotated.py` exists specifically to route around this.

- **cairosvg silently mis-scales `rmc`'s SVG output by 25%.** `rmc -t
  svg` emits bare numeric width/height (meant as PDF points), but
  cairosvg's default unit assumption is CSS px at 96dpi, i.e. it
  multiplies by 0.75. Symptom: annotations render at the wrong scale
  and position when merged. Fix (already in `pull_annotated.py`):
  rewrite the SVG's `width`/`height` attributes to have an explicit
  `pt` suffix before feeding to cairosvg.

- **The `.content` file's page-list schema is not stable across
  reMarkable software versions.** Older exports have a flat top-level
  `"pages": ["id1", "id2"]`; newer ones nest it as `"cPages": {"pages":
  [{"id": "id1"}, {"id": "id2"}]}`. Both were observed against the same
  account within this session. `rmpull.archive._page_ids_from_content`
  handles both; if `rmapi`/reMarkable changes the schema again, that's
  the one place to patch (see its doctest for the expected shapes).

- **`pyrefly` needs to be pointed at the venv explicitly** —
  `pyrefly check` alone resolves imports against the system Python (3.9
  here) and reports `pypdf`/etc. as missing even though it's installed
  in `driver/venv`. Always pass `--python-interpreter-path
  driver/venv/bin/python3`.

- **The annotation canvas has a different aspect ratio than the
  original PDF page**, and there's no public metadata field that gives
  an exact transform (reMarkable applies its own "bestFit" scaling +
  margins when it imports a PDF for on-device annotation, and doesn't
  expose the resulting geometry). `pull_annotated.py`'s defaults
  (`SCALE_MULT=0.86`, `TY_EXTRA=99`, `TX_EXTRA=-38`) were reverse
  engineered by visual A/B calibration against one real document and
  are a reasonable starting point, not a general solution. **Always
  visually check the merged PDF** (open it, or render a page thumbnail
  with `qlmanage -t -s 1000 -o . page.pdf` on macOS) and re-tune with
  `--scale-mult` / `--ty` / `--tx` if annotations are off — they were
  designed to be nudged in small increments (a few points at a time is
  ~1 visible pixel at typical zoom).

- **A botched `rmapi rm` can permanently break a document's cloud
  content while leaving its metadata alive ("zombie" document).** If
  you `rmapi rm` a document that's concurrently being edited on the
  tablet, you can end up with a document ID whose `rmapi get` forever
  returns metadata-only archives (no `.pdf`/`.content`/`.rm`), even
  after the tablet re-syncs — `ModifiedClient` in `rmapi stat` stops
  updating too, because the tablet believes it's already synced and
  won't re-push. There is no known fix for the affected ID. **The only
  recovery is on the tablet: duplicate the document to get a fresh ID**,
  then point `pull_annotated.py` at the duplicate's name. Lesson: don't
  `rmapi rm` a document that a human might be actively using.

- **`rmc` requires Python >=3.10**; macOS system Python (3.9.6 as of
  this writing) is too old and `pip install rmc` fails with "Could not
  find a version that satisfies the requirement". Use pyenv (see
  `setup.sh`).

- **`rmrl`** (an alternative, more "batteries-included" library that
  claims to render a fully-merged annotated PDF directly) was tried and
  abandoned: it pins `reportlab<4.0.0`, whose native build fails on
  current macOS/Python ("cannot find ft2build.h" even with freetype
  installed via brew and `CFLAGS`/`LDFLAGS` set), and it also imports
  the removed-in-modern-setuptools `pkg_resources`. Not worth fighting;
  `rmc` + `cairosvg` + `pypdf` is the path that actually works.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `rmapi ls` hangs asking for a one-time code | Go to https://my.remarkable.com/device/browser/connect, generate a code, paste it in |
| `pip install rmc` fails, "no versions satisfy" | You're on a Python <3.10 (check with `python3 --version`); re-run `setup.sh`, which auto-selects a pyenv 3.10+ if one is installed, or install one: `pyenv install 3.13.3` |
| `rmc ... ERROR cannot unmarshal object into Go struct field Content.pageTags` (from `rmapi geta`, not this skill's driver) | Expected — this is why `pull_annotated.py` exists instead. Use it, not `rmapi geta`. |
| `pull_annotated.py` errors "archive has no .content/.pdf (metadata-only download)" | The document's cloud copy is a "zombie" (see Gotchas) — duplicate it on the tablet and retry against the new name |
| Annotations appear but are offset/wrong scale in the merged PDF | Re-run with `--scale-mult`, `--ty` (points, +up), `--tx` (points, +right) tuned in small steps; open the output after each change |
| `sync_to_remarkable.sh`: Chrome print produces a blank/broken PDF | Confirm `/Applications/Google Chrome.app` exists and the `.md` file isn't empty; check `pandoc`'s HTML output in the work dir directly |
