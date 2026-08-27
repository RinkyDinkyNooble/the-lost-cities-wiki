# Releasing

Run in order. Every step is a command or a yes/no check.

## 1. Decide the number

| Change | Bump |
|---|---|
| Fix only | patch, `1.0.1` to `1.0.2` |
| New feature or setting | minor, `1.0.1` to `1.1.0` |
| A world made with the old version stops behaving the same | major |

The mod version tracks changes to this mod, not to Lost Cities. A port that adds
nothing is a minor bump, not the Lost Cities version.

```bash
# mod/gradle.properties
mod_version=1.0.2
```

## 2. Build

```bash
cd mod
./gradlew clean build
```

## 3. Audit the jar

```bash
unzip -l build/libs/lostcities_devtool-*.jar
```

- [ ] No `mcjty/` entries
- [ ] `META-INF/mods.toml`, `logo.png`, `LICENSE_lostcities_devtool.txt` present
- [ ] `lostcities_devtool.mixins.json` and `.refmap.json` present
- [ ] Size in the expected range, currently around 300 KB
- [ ] `unzip -p build/libs/*.jar META-INF/mods.toml | grep version` shows the new number

## 4. Test the jar you will ship

Test the exact file, not a rebuild of it. The server checks install the jar
from `build/libs` and remove it afterwards, so do not rebuild between running them
and uploading.

```bash
cd ../..
python mod/tools/check-validator.py
python mod/tools/check-workshop.py
python mod/tools/check-layout.py
python mod/tools/check-tags.py
python mod/tools/check-licence-text.py
python mod/tools/check-export.py
python mod/tools/check-export-plot.py
python mod/tools/check-import.py
python mod/tools/check-roundtrip.py
python mod/tools/check-import-twice.py
python mod/tools/check-suggest-speed.py
python mod/tools/check-loud-output.py
python mod/tools/check-import-fidelity.py
python mod/tools/check-clear.py
python mod/tools/check-part-reuse.py
python mod/tools/check-tag-export.py
python mod/tools/check-conversions.py
python mod/tools/check-sync.py
python mod/tools/check-licence.py
python mod/tools/check-cmd-report.py
python mod/tools/check-cmd-plot.py
python mod/tools/check-cmd-mark.py
python mod/tools/check-cmd-workshop.py
python mod/tools/check-cmd-io.py
```

The first four need no server and finish in about a second each. The other
twenty boot one apiece and take roughly ninety seconds. Run them one at a time:
two servers cannot share the rig. All twenty four end in `all checks passed`:

- [ ] `check-validator`, every asset-check rule, and nothing thrown by a malformed
      file
- [ ] `check-workshop`, the dimension and the catalogue
- [ ] `check-export`, the pack generates a city, gold block count non-zero
- [ ] `check-import`, Lost Cities' own pack comes in on 42 plots
- [ ] `check-roundtrip`, the two exports are byte identical and every plot holds
      the blocks it held
- [ ] `check-import-twice`, a second import does not hide the first city, and a
      wipe backs up before it empties
- [ ] `check-suggest-speed`, completion stays inside its budget and the cache
      notices a reload
- [ ] `check-loud-output`, a lookup on a broken pack stays readable
- [ ] `check-import-fidelity`, a shared band keeps its variety and a tagged block
      keeps its NBT
- [ ] `check-clear`, a confirmed clear leaves nothing standing and a shared short
      name does not block the backup
- [ ] `check-layout`, growing a row moves nothing that already existed
- [ ] `check-part-reuse`, identical levels share one part file
- [ ] `check-tags`, a keep-list and a drop-list mean opposite things
- [ ] `check-tag-export`, tagkeys reaches the export and notags turns it off
- [ ] `check-conversions`, a narrower scope wins and adds to the wider
- [ ] `check-export-plot`, one plot exports as a fragment with no world style
- [ ] `check-sync`, a file naming a plot the catalogue lacks is found and laid out
- [ ] `check-licence-text`, a licence is cut to three lines and carrying a notice
      does not wrap it again
- [ ] `check-licence`, a pack's terms are found at both places looked, an oversized
      one is capped, and an export carries what was found
- [ ] `check-cmd-report`, the reading commands answer about a generated city and
      name where each answer came from
- [ ] `check-cmd-plot`, a plot offers the keys its row class really has, the four
      scopes fold most specific first, and every refusal says what would work
- [ ] `check-cmd-mark`, all six marks reach the pack on the entry for the position
      they were placed at
- [ ] `check-cmd-workshop`, the catalogue describes itself, refuses what its codecs
      cannot take, and lays out the same way twice
- [ ] `check-cmd-io`, a pasted command block arrives disarmed unless `run` asks for
      it, and an export will not quietly replace one
- [ ] No mixin failures in the rig's log:
      `grep -ci "mixin apply failed\|InvalidInjection" testrig/servers/forge-1.20.1-47.4.10/logs/debug.log`
      is 0

## 5. Write the two documents

```bash
mod/description/changelog-<version>.md    what changed, for someone who has it
mod/description/release-<version>.md      what it is, for someone who does not
```

Copy the previous pair and edit. Keep the changelog's headings benefit-first, not
config-group-first.

- [ ] No implementation detail: no class names, no "compiles to", no mixin talk
- [ ] Measured numbers kept, they persuade without background
- [ ] Nothing references a version that was never published

## 6. Gates

The same six CI runs. `check_render.py` reads the built site, so it has to come
after the build.

```bash
cd ../..
.venv/Scripts/python.exe -m mkdocs build --strict
.venv/Scripts/python.exe docs/examples/validate.py
.venv/Scripts/python.exe docs/examples/check_claims.py
.venv/Scripts/python.exe docs/examples/key-coverage.py
.venv/Scripts/python.exe docs/examples/check_pages.py
.venv/Scripts/python.exe docs/examples/check_render.py
```

- [ ] All six clean

## 7. Commit and tag

```bash
git add -A
git commit
git tag mod-v<version>
```

The commit and the tag stay local at this point. Publishing is step 8, and the order
there matters: the wiki links to the release by tag, so pushing the docs before the
release exists leaves four broken links on the live site.

## 8. Publish

- [ ] GitHub release, body from `release-<version>.md`, jar attached
- [ ] CurseForge file upload, changelog from `changelog-<version>.md`
- [ ] CurseForge: The Lost Cities set as a **required dependency** in the dependency
      field, not only in the description text
- [ ] Update the release link in `docs/tooling/commands.md`,
      `docs/tooling/lcdev.md`, `docs/troubleshooting/known-issues.md` and
      `docs/troubleshooting/errors.md`. All four point at a tag, so they 404 between
      the docs being pushed and the release existing: create the release first

Not Modrinth. Its content rules restrict work made with AI assistance, including
icons.

## Naming

```
lostcities_devtool-<minecraft>-<version>.jar
lostcities_devtool-<loader>-<minecraft>-<version>.jar   once a second loader exists
```

Tags follow: `mod-v<version>`, or `mod-<loader>-<minecraft>-v<version>` once one
Minecraft version is built for two loaders.
