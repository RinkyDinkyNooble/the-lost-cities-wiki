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
- [ ] Size in the expected range, currently around 170 KB
- [ ] `unzip -p build/libs/*.jar META-INF/mods.toml | grep version` shows the new number

## 4. Test the jar you will ship

Not a rebuild of it. Copy the exact file.

```bash
cd ../research/server-1.20.1-7.4.12
rm mods/lostcities_devtool-*.jar
cp ../../mod/build/libs/lostcities_devtool-*.jar mods/

python harness.py --pack <pack> --profile <profile> --probes probes/<file>.json
```

Minimum set, all must pass:

- [ ] `j5-fighting`, 8/8, no failed chunks
- [ ] `j5-pure-json`, 8/8, control that needs no mod
- [ ] `wiki-test7` with `fixBelowPart` and `fixFullStreetShape` on, 28/28
- [ ] No mixin failures: `grep -ci "mixin apply failed\|InvalidInjection" logs/debug.log` is 0

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

User pushes. Never push.

## 8. Publish

- [ ] GitHub release, body from `release-<version>.md`, jar attached
- [ ] CurseForge file upload, changelog from `changelog-<version>.md`
- [ ] CurseForge: The Lost Cities set as a **required dependency** in the dependency
      field, not only in the description text
- [ ] Update the release link in `docs/tooling/commands.md`,
      `docs/troubleshooting/known-issues.md` and `docs/troubleshooting/errors.md`

Not Modrinth. Its content rules restrict work made with AI assistance, including
icons.

## Naming

```
lostcities_devtool-<minecraft>-<version>.jar
lostcities_devtool-<loader>-<minecraft>-<version>.jar   once a second loader exists
```

Tags follow: `mod-v<version>`, or `mod-<loader>-<minecraft>-v<version>` once one
Minecraft version is built for two loaders.
