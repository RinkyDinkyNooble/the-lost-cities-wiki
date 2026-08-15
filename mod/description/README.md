# Listing copy, and how to publish

| File | Goes to |
|---|---|
| [`modrinth.md`](modrinth.md) | Modrinth description. Pure Markdown, which is all Modrinth accepts |
| [`curseforge.md`](curseforge.md) | CurseForge description. Markdown with HTML for tables, headings and two coloured callouts |
| [`changelog-1.0.0.md`](changelog-1.0.0.md) | The changelog field on both, and the body of the GitHub release |

Both descriptions say the same things. They differ only in what the site renders, so
edit both when a fact changes.

## Building the release jar

```bash
cd mod
./gradlew clean build
```

The jar lands in `build/libs/` named `lostcities_devtool-<mc>-<version>.jar`, for
example `lostcities_devtool-1.20.1-1.0.0.jar`. The Minecraft version is in the file
name because six branches of this mod will exist, one per Lost Cities version, and a
jar in a downloads folder has to say which one it is without being opened.

Check before uploading:

| | |
|---|---|
| Size is around 170 KB | anything much larger means something was bundled that should not be |
| `unzip -l` shows no `mcjty/` entries | McJty's classes are compile-only and must not travel |
| `LICENSE_lostcities_devtool.txt` is present | 0BSD asks for nothing, but a jar that states its own terms is one fewer question |
| `logo.png` and `META-INF/mods.toml` are present | the mod list looks unfinished without the first |

## Why there is no release workflow

**GitHub Actions cannot build this mod.** Every mixin targets a Lost Cities class, so
the build needs `mod/libs/lostcities-1.20-7.4.12.jar` on the compile classpath, and
that jar is McJty's to distribute rather than ours. It is gitignored, so a runner
checking out this repository does not have it and never will.

A workflow that looked like automation and failed on every run would be worse than
none, so releases are built locally and uploaded by hand.

**The way out, when it matters:** [CurseMaven](https://cursemaven.com) resolves
CurseForge files as Gradle dependencies by project and file id, which is the sanctioned
route and redistributes nothing. Switching `libs/` for a CurseMaven coordinate would
let CI build the mod, and would also mean nobody cloning this repository has to fetch
the jar by hand. Worth doing before the multi-version ports, when there are six builds
to keep straight rather than one. Not worth doing the week of the first release.

## Publishing

1. Build, and run the checks above.
2. Create the GitHub release. Tag `mod-v1.0.0`, body from the changelog, jar attached.
3. Upload to CurseForge and Modrinth with the matching description file.

On both sites the mod is **Forge 1.20.1** only, and The Lost Cities is a **required
dependency**. Say that in the dependency field rather than only in the description:
the metadata is what a launcher reads.
