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
| 1.2 | **Name the palette, not the part** | `Could not find entry 'X' in the palette for part 'Y'!` names the part when the fault is usually a palette that failed to define or resolve `X`. The palette identity is known at throw time. Add it rather than replacing the existing text. | [Palette](../docs/reference/palette.md) |
| 1.3 | **Report the failing building, not the querying chunk** | A fault raised while building a chunk's `BuildingInfo` spreads to every neighbour that queries it. Measured: 3 broken buildings, 77 failed chunks over a 13 by 10 area. The message names the chunk that asked, not the building at fault. | [Error Messages](../docs/troubleshooting/errors.md) |
| 1.4 | **Load-time validation** | Port the rules from `docs/examples/validate.py`, which already reproduces four real in-game failures statically: uncovered levels, `loot`/`mob` holding an ID rather than a Condition name, `inpart`/`belowpart` in a building's `parts`, and a layer that is not `xsize * zsize` characters. Report at datapack load, before a chunk is generated. | `docs/examples/validate.py` |
| 1.5 | **Chunk report command** | `/lcdev report` dumping the resolved asset chain for the chunk the caller stands in: profile, world style, city style, building, the parts chosen per level, and the merged palette's source for a named character. `/lostcities debug` prints to the server console only and stops short of the palette. | [Commands](../docs/tooling/commands.md) |

### Tier 2: authoring conveniences, on by default, additive only

| # | Feature | Notes |
|---|---|---|
| 2.1 | **JSON5 for Lost Cities assets** | Comments and trailing commas in `data/<ns>/lostcities/**`. **Scoped by path**, not global: no other mod's or Minecraft's own JSON is touched. |
| 2.2 | **Asset export** | Write the merged, fully resolved view of an asset to disk: a city style after inheritance, or a palette after merging and alias resolution. Both are currently only inspectable by reading the mod. |

### Tier 3: behaviour repairs, off by default, one toggle each

Each changes what generates, so each is opt-in and separately switchable.

| # | Feature | The bug | Risk |
|---|---|---|---|
| 3.1 | **`belowpart` reads the part below** | `ConditionContext` stores `belowPart` in a field with no accessor, and the predicate calls `getPart()`. The floor loop already tracks the previous level's part and passes it in, so only the accessor and the predicate are missing. Present in 7.4.12 through 10.0.1. | Medium. Buildings written against the broken behaviour would change. |
| 3.2 | **`streetblocks.parts.full` generates** | `StreetType.values()[random.nextInt(0, values().length - 2)]` makes the `full` shape unreachable. Off by one on the bound. | Medium. Street layouts change wherever `full` becomes reachable. |
| 3.3 | **Per-block rail variation** | `railmain` is resolved once per chunk, producing 16-block colour strips. The palette already has a `get(char, Random)` overload the railway code does not call. | Low. Affects rail beds only. |
| 3.4 | **Corner stairs** | The neighbour-aware correction discards any `shape=` written in a palette. A per-part or per-character opt-out would let an author force a shape without the command-block workaround. | Medium. Needs a design decision on where the opt-out is declared. |

### Tier 4: client and GUI, no server effect

| # | Feature | Notes |
|---|---|---|
| 4.1 | **Re-anchor the Cities button on resize** | It keeps its old position when the window grows instead of staying anchored top right. |
| 4.2 | **Right-click cycles profiles backwards** | Left-click already cycles forward. |
| 4.3 | **Show non-selectable profiles** | A profile whose name contains a digit, uppercase letter, hyphen or dot loads and wires up correctly but is never offered on the world creation screen. Either list it or say why it is hidden. |

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
| 3.2 | A street pack marking only `full` produces marked chunks, which it currently never does. |
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

## Placeholders to fill before any release

| Item | Needed for |
|---|---|
| GitHub repository URL | `issueTrackerURL` and `displayURL` in `mods.toml` |
| `logo.png`, 128 by 128 | `mods.toml` logo entry |
| Long description | CurseForge or Modrinth listing |
| Distribution decision | Whether this is published at all, or stays a repo artifact |

Metadata already settled: mod id `lostcities_devtool`, display name
`The Lost Cities - DevTool`, group `com.rinkynooble.lostcitiesdevtool`, author
`RinkyNooble`, licence `0BSD`.
