# The Lost Cities - DevTool: build plan

A companion mod for The Lost Cities, aimed at people authoring content for it.
Source lives in `mod/` in this repository, alongside the wiki whose findings it
implements.

## What it is, and what it is not

**It is** a tool for authors: it reports faults earlier and more accurately, it
accepts a friendlier file format, and it optionally repairs behaviour this wiki has
traced to a bug.

**It is not** a fork, a performance mod, or a content mod. It adds no blocks, no
items, no assets and no generation of its own. Removing it from an instance leaves
every world it touched still loadable by vanilla Lost Cities.

Three rules follow, and they decide the whole ordering below.

| Rule | Why |
|---|---|
| A feature that changes what generates is **off by default** | A world generated with the mod must be reproducible without it. Anything that alters block placement is opt-in. |
| A feature that only changes diagnostics is **on by default** | Better messages cannot corrupt anything, and the reason to install the mod is to see faults sooner. |
| Every feature has an acceptance test on the existing rig | `research/server-1.20.1-7.4.12/harness.py` already boots a headless server, force loads a grid and reads the world back. Each feature below names what proves it works. |

## Feature inventory

Grouped by risk, which is also the build order.

### Tier 0: foundation

No behaviour. Everything else depends on it.

| # | Item | Notes |
|---|---|---|
| 0.1 | Gradle project, Forge MDK, `mods.toml`, mod class | Modelled on `infectiouspatch`, same author conventions |
| 0.2 | Config file with one toggle per feature | Forge `ForgeConfigSpec`, common config |
| 0.3 | Mixin plumbing: refmap, config json, one no-op mixin proving the toolchain | The first real mixin lands in 1.1 |

### Tier 1: diagnostics, on by default, cannot change generation

| # | Feature | What it fixes | Evidence |
|---|---|---|---|
| 1.1 | **Catch on the sphere feature** | `LostCitySphereFeature` has no `try` anywhere. On `landscapeType: spheres`, `cavernspheres` or `space`, a fault that `LostCityFeature` catches and logs instead escapes to vanilla's feature placer. Measured: 35 caught and 0 uncaught on `default`, against 18 caught and 21 uncaught on `spheres`, where the server then shut down. | [Known Issues](../docs/troubleshooting/known-issues.md), `research/bug-fixes.md` |
| 1.2 | **Name the palette, not the part** | **Done.** `Could not find entry 'X' in the palette for part 'Y'!` names the part when the fault is a palette. The report now gives the character's code point and Unicode name, which a log cannot render, and the four places to look. | [Palette](../docs/reference/palette.md) |
| 1.3 | **Report the failing building, not the querying chunk** | **Done.** A fault raised while building a chunk's `BuildingInfo` spreads to every neighbour that queries it, and those queries chain. The message is now enriched at the throw, where the building and chunk are known exactly, so no search is needed. 78 undifferentiated failures became 3 named faults. | [Error Messages](../docs/troubleshooting/errors.md) |
| 1.4 | **Load-time validation** | **Done.** Ported the rules from `docs/examples/validate.py`, which already reproduces four real in-game failures statically: uncovered levels, `loot`/`mob` holding an ID rather than a Condition name, `inpart`/`belowpart` in a building's `parts`, and a layer that is not `xsize * zsize` characters. Reported at datapack load with a file name and a line number, which generation cannot supply because by then only the parsed object survives. | `docs/examples/validate.py` |
| 1.5 | **Chunk report command** | **Done.** `/lcdev report` dumps the resolved asset chain for the chunk the caller stands in: profile, world style, city style, building, the parts chosen per level, and the merged palette's source for a named character. `/lostcities debug` prints to the server console only and stops short of the palette. | [Commands](../docs/tooling/commands.md) |
| 1.6 | **Lookup by asset name** | **Done.** `/lcdev in <asset> char|block` answers from a named palette, part or building, with tab completion, so the question can be asked while editing rather than only while standing on a generated result. The bare forms now report the chunk and every named asset that defines the character. Every asset is built on its own rather than through `AssetRegistries.loadAll`, which has no guard and stops at the first throw. | [Commands](../docs/tooling/commands.md) |

### Tier 2: authoring conveniences, on by default, additive only

| # | Feature | Notes |
|---|---|---|
| 2.1 | **JSON5 for Lost Cities assets** | **Done.** Comments and trailing commas in `data/<ns>/lostcities/**`. **Scoped by path**, not global: no other mod's or Minecraft's own JSON is touched. |
| 2.2 | **The `.json5` extension** | **Done.** Nothing in Minecraft or Lost Cities lists a `.json5` file, so one is presented to both loaders under its `.json` name. Covers datapack assets and `config/lostcities/profiles`. Where both names exist the `.json5` wins, and the shadowed file is reported in the log and once in chat to any operator joining. |

Asset export was considered and dropped. Writing a merged city style or a resolved
palette to disk is easy, but nothing consumes the result: the mod reads assets, not
exports, so an edited export has no route back in. The information it would carry is
better delivered by 1.5, which answers the same question about a live chunk.

### Tier 3: behaviour repairs, off by default, one toggle each

Each changes what generates, so each is opt-in and separately switchable.

| # | Feature | The bug | Risk |
|---|---|---|---|
| 3.1 | **Done.** **`belowpart` reads the part below** | `ConditionContext` stores `belowPart` in a field with no accessor, and the predicate calls `getPart()`. The floor loop already tracks the previous level's part and passes it in, so only the accessor and the predicate are missing. Present in 7.4.12 through 10.0.1. | Medium. Buildings written against the broken behaviour would change. |
| 3.2 | **Done.** **`streetblocks.parts.full` generates** | `StreetType.values()[random.nextInt(0, values().length - 2)]` makes the `full` shape unreachable. Off by one on the bound. | Medium. Street layouts change wherever `full` becomes reachable. |
| 3.3 | **Per-block rail variation** | `railmain` is resolved once per chunk, producing 16-block colour strips. The palette already has a `get(char, Random)` overload the railway code does not call. | Low. Affects rail beds only. |
| 3.4 | **Corner stairs** | The neighbour-aware correction discards any `shape=` written in a palette. A per-part or per-character opt-out would let an author force a shape without the command-block workaround. | Medium. Needs a design decision on where the opt-out is declared. |

### Tier 4: client and GUI, no server effect

| # | Feature | Notes |
|---|---|---|
| 4.1 | **Done.** **Re-anchor the Cities button on resize** | It keeps its old position when the window grows instead of staying anchored top right. |
| 4.2 | **Done.** **Right-click cycles profiles backwards** | Left-click cycles forward and wraps, so stepping back one profile means clicking through the whole list. The button is a plain vanilla `Button`, whose handler accepts the left button only, so a right-click on it does nothing at all today. Handled as a screen event rather than a mixin on the button, because there is nothing on the button to patch. |
| 4.3 | **Dropped.** ~~Show non-selectable profiles~~ | The premise did not survive being traced. `toggleProfile` filters on `isPublic()` alone and nothing tests the characters of a name, so there is no class of profile that loads and is wrongly hidden. What `isPublic()` hides is hidden on purpose: the sphere-outside profiles, which are meant to be referenced rather than chosen. The two real causes found in its place, the first-dot name split and the `IOException` handler that returns rather than continues, are recorded in `research/test-backlog.md` and are faults in reading profiles, not in offering them. |
| 4.4 | **Done.** **Customize no longer crashes** | `LostCitySetup.reset()` nulls the profile list when a world is left, `toggleProfile()` rebuilds it lazily, and `customize()` does not. Pressing Customize after having played a world throws and closes the game. |

## Build order, and why

**1.1 first.** It is the smallest feature in the plan, roughly one mixin and a
`try`, and it is the only one that turns a server shutdown into a log line. It also
proves the entire toolchain end to end, mixin plumbing included, against a fault
that is already reproducible on the rig. A first feature should be the one where a
build problem is unambiguous.

**Then the rest of Tier 1, in 1.2 to 1.5 order.** Ascending size. 1.2 and 1.3 are
message changes. 1.4 is the largest item in the tier and benefits from the config
and logging conventions the earlier three settle.

**Tier 2 after Tier 1**, because JSON5 changes how files are read, and a fault in it
would be easiest to diagnose with the better diagnostics already in place.

**Tier 3 last of the server-side work.** Every item alters generation. They are also
the features most likely to need their own claim-test pack, and by then the wiki's
rig will have been extended for the mod anyway.

**Tier 4 whenever convenient.** It is isolated from everything else and needs a
client rather than the headless rig, so it does not block any other item.

## Acceptance tests

Each feature is proved on the existing rig unless noted.

| Feature | Test |
|---|---|
| 1.1 | Run `wiki-test8` under `landscapeType: spheres`. Without the mod: 21 uncaught and a dead server. With it: 0 uncaught, all faults logged, server alive. |
| 1.2 | The circular-alias building in `wiki-test7` logs a message naming `wt7:circ` as well as `wt7:ct_box`. |
| 1.3 | The `belowsem` building in `wiki-test7` produces a message naming the building, not only the 35 chunks that queried it. |
| 1.4 | `wiki-test7` and `wiki-test8` report their known faults at load. The count must match what `validate.py` reports on the same packs. |
| 3.1 | `belowsem` comes out gold on level 0 and diamond on level 1, instead of gold on both. |
| 2.2 | `wiki-test9` generates from a building, part and palette that exist only as `.json5`, a `.json5` wins over the `.json` beside it, a plain `.json` resolves a `.json5` part, and a `.json5` profile decides `cityChance`. With `acceptJson5Extension` off, all four markers return to zero. |
| 1.6 | A `char` and a `block` lookup answer from a named asset while standing outside any city, and the bare forms list every asset that defines the character. An asset that cannot be built is named rather than dropped. |
| 2.2 | Three packs generated from one definition, `pure-json`, `pure-json5` and `fighting`, each produce the same three towers: 8 of 8 probes, no failed chunks, and 12 override warnings on the fighting pack covering every asset kind and the profile. |
| 3.2 | A street pack marking only `full` produces marked chunks, which it currently never does. |
| 4.2 | By hand, with a client. Right-click the profile button: it should step to the entry before the current one, with the disabled state sitting between the last profile and the first. The rig can only show no regression, which it does: 8 of 8 on the fighting pack and no mixin failures. |
| 4.x | By hand, with a client. |

## Version support

In priority order. Each is a separate branch of the same source, not a rewrite.

| Order | Minecraft | Lost Cities | Loader |
|---|---|---|---|
| 1 | 1.20.1 | 7.4.12 | Forge 47.4.10 |
| 2 | 1.20.1 | 7.5.1 | Forge |
| 3 | 1.21 | 8.2.2 | NeoForge |
| 4 | 1.21.1 | 8.4.1 | NeoForge |
| 5 | 1.21.11 | 9.5.1 | NeoForge |
| 6 | 26.1.2 | 10.0.1 | NeoForge |

7.4.12 is first because it is the version this wiki is written against and the one
in the author's own modpack. It will eventually stop being primary, and 7.5.1 takes
over when it does.

A mixin is bound to the shape of the code it patches, so each target version needs
its own verification pass rather than a version-range bump. `belowpart` is confirmed
broken in all six, so 3.1 is expected to apply throughout; the others need checking
per version.

## Release checklist, and what was outstanding

| Item | Needed for | State |
|---|---|---|
| `issueTrackerURL` | `mods.toml` | **Done.** The wiki repository's issues |
| `displayURL` | `mods.toml` | **Done.** The wiki site, which is what the mod implements |
| `logo.png` | `mods.toml` | **Done.** 256 by 256, from `research/tlcm-dt-icon.png` |
| `credits` | `mods.toml` | **Done.** Credits McJty and disclaims affiliation |
| Long description | The CurseForge listing | **Done.** `description/curseforge.md`, plus a summary and a changelog |
| Distribution decision | Whether this is published at all, or stays a repo artifact | **Settled.** GitHub Releases and CurseForge, uploaded by hand. Not Modrinth |
| Repository layout | Whether the mod keeps living in the wiki repository or gets its own | **Settled.** It stays in the wiki repository, so both URLs above are already right |

Metadata already settled: mod id `lostcities_devtool`, display name
`The Lost Cities - DevTool`, group `com.rinkynooble.lostcitiesdevtool`, author
`RinkyNooble`, licence `0BSD`.

`description/` holds the listing copy: `curseforge.md`, `summary.txt`, and a changelog
serving both the CurseForge changelog field and the GitHub release body.

Modrinth is not a target. Its content rules restrict work made with AI assistance,
including icons, and this project does not qualify.

Set The Lost Cities as a **required dependency** in CurseForge's dependency field
rather than only in the description text. That field is what a launcher reads.
