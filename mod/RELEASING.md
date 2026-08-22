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
python mod/tools/check-export.py
python mod/tools/check-import.py
python mod/tools/check-roundtrip.py
python mod/tools/check-import-twice.py
python mod/tools/check-suggest-speed.py
python mod/tools/check-loud-output.py
python mod/tools/check-import-fidelity.py
python mod/tools/check-clear.py
```

The first needs no server and finishes in about a second. The other nine boot one
each and take roughly ninety seconds apiece. All ten end in `all checks passed`:

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
