# remarkable-skill

Drive a reMarkable tablet from the command line. No cable.

## What it does

**Push notes to the tablet:**
- Point it at a folder of `.md` files
- Converts each to PDF
- Uploads to reMarkable Cloud
- Tablet gets it over Wi-Fi automatically

**Pull annotations off the tablet:**
- Downloads a document you wrote/drew on
- Extracts your handwritten strokes
- Merges them back onto the original PDF, in place
- Works around a real bug: `rmapi`'s own annotation export is broken

**Setup:**
- One script installs everything needed (`rmapi`, `pandoc`, Python deps)
- One-time reMarkable login (pairing code)

## Where things are

| Task | Script |
|---|---|
| Setup | `skills/run-remarkable-skill/driver/setup.sh` |
| Upload notes | `skills/run-remarkable-skill/driver/sync_to_remarkable.sh` |
| Pull annotations | `skills/run-remarkable-skill/driver/pull_annotated.py` |
| Run tests (doctests + lint + typecheck) | `skills/run-remarkable-skill/driver/run_tests.sh` |

## Install

This is a Claude Code **plugin** — usable from any project, not just this
repo.

**Try it locally, no install:**
```bash
claude --plugin-dir /path/to/remarkable-skill
```
Then `/remarkable-skill:run-remarkable-skill` is available for that session.

**Load it every session automatically:**
```bash
claude plugin init  # or: symlink/copy this repo's skills/run-remarkable-skill
                     # into ~/.claude/skills/
```
Simplest: `ln -s /path/to/remarkable-skill/skills/run-remarkable-skill ~/.claude/skills/run-remarkable-skill`
— Claude Code auto-loads anything under `~/.claude/skills/`, in every project.

**Share it with others:** publish this repo, then anyone points
`--plugin-dir` at their local clone, or you list it in a
[plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
for `/plugin install`.

## More detail

Full usage, prerequisites, and the weird bugs this ran into (reMarkable
sync-format quirks, a PDF scaling bug, an annotation-position calibration,
a "zombie document" recovery trick) are in
[`skills/run-remarkable-skill/SKILL.md`](skills/run-remarkable-skill/SKILL.md).
