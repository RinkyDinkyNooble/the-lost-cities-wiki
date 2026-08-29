# The Lost Cities - DevTool

A Forge **1.20.1** companion mod for **The Lost Cities 7.4.12**, plus the MkDocs wiki
that documents it. The mod adds no blocks, no items and no generation of its own.

Skills carry the procedures: call `lc-ship` before landing a change, `lc-check` before
writing or running one of the checks, `lc-review` to review, `lc-assets` when touching
the exporter, importer or validator. What follows applies whether or not a skill was
invoked.

## Never

- **Never push.** The author pushes. Commit freely; `git push` is theirs.
- **Never an em dash**, anywhere, including code comments and commit messages.
  `python research/ai-tell-scan.py` finds AI-cliché phrasing; touched files must add
  no new candidates.
- **Never run two server checks at once**, and never start one while a suite is
  running. They share one rig, one port and one world folder. Breaking this has cost
  two checks and one false failure on separate occasions.
- **Never spawn sub-agents.** `research/DESIGN-NOTES.md` records why it was rejected.
- **Never set up CurseForge automation** without explicit permission. Modrinth is not
  a publishing target, because its rules restrict AI-assisted work.
- **Never bump the version to a bare number.** `mod_version` stays `<x>-dev` until the
  publish loop.

## Layout

| Path | |
|---|---|
| `mod/` | The mod. Ships. |
| `mod/tools/` | The checks and the tools that are not checks |
| `testrig/` | The rig. `rcon.py` and `rig.py` are tracked; `servers/`, `java/`, `downloads/` are not |
| `docs/` | The wiki. **Describes the released mod**, currently 1.0.1, never unreleased work |
| `research/` | Private, gitignored. Working notes, plans, the changelog draft |
| `mod/libs/` | Gitignored. McJty's jar is not ours to ship |

Start from `research/<version>/NEXT.md`; it points at the rest in reading order.

## Writing

- **No first person in docs**, and no advisory register in committed files. State what
  is, not what the reader ought to feel.
- Colour is allowed in `mod/description/curseforge.md` and nowhere else.
- Dense and scannable over prose. Tables over paragraphs. One example per concept.
- A field table's Meaning column ties behaviour to the value, not just the name.

## Traps that have already cost time

- **A heredoc mangles escapes in code written through Bash.** Anything containing
  `\n`, `\\` or a triple quote goes through the Write or Edit tool instead. This has
  recurred more than ten times.
- **`docs/` describes the released mod.** A page describing unreleased work is wrong
  for everyone running the current version. New behaviour goes in the changelog draft
  as a doc correction owed, not into `docs/`.
- **The build warns about `ResourceLocation` constructors.** Those warnings predate
  the current work; do not treat them as newly introduced.
