# Error Messages

!!! tip "TL;DR"
    Paste the message you got into the search box. Every error Lost Cities throws by name is listed here with its cause and fix.

Messages are quoted **exactly** as the mod produces them, with `<...>` where it substitutes a value. Every entry was taken from the 7.4.12 source, not from reports.

!!! note "Where the message shows up"
    Most of these are thrown during **chunk generation**, which on a client looks like a world crash while flying into new terrain, and on a server looks like a chunk that never finishes loading plus a stack trace in the log. A few happen earlier, at world load. The table for each says which.

## Palette errors

### `Could not find entry '<char>' in the palette for part '<part>'!`

**When:** chunk generation.

A part used a character that the merged palette does not define.

The message names the **part**, not the palette, which is misleading when the real fault is on the palette side. Causes, in order of likelihood:

| Cause | Fix |
|---|---|
| Typo in the part's `slices`, or a row of the wrong length shifting characters | Check row lengths first, they are never validated |
| The character is defined in a palette that is not in this building's chain | Add it to the part's `refpalette`, or to the [Style](../reference/style.md)'s palettes |
| The character is `frompalette` and part of a **circular reference** | A cycle resolves to nothing and leaves the character undefined, with no warning at load. See [How aliases resolve](../reference/palette.md#how-aliases-resolve-and-where-it-bites) |
| The character is a space and your style does not include the `common` palette | `" "` maps to air because `common` says so, not because the engine special-cases it |

### `Invalid palette entry for '<char>'! Not enough blocks in the random list (factor should go up to 128)`

**When:** the first time this palette is compiled, during generation.

A weighted list (`blocks`, or a referenced `variant`) has `random` weights totalling **less than 128**. The list fills a fixed 128-slot array and the mod refuses a partially filled one.

Add a catch-all entry **last** with a large weight. The mod's own idiom is small honest numbers for rare options, then something like `1000` at the end to soak up the remainder. See [The 128-slot rule](../reference/palette.md#the-128-slot-rule-for-blocks-and-variant).

### `Invalid palette entry for '<char>'!`

Same place, different cause: the entry resolved to nothing usable at all. Usually a `variant` name that does not exist.

### `Illegal palette <name>!`

**When:** palette load.

An entry in that palette has **none** of `block`, `variant`, `blocks`, or `frompalette`. Every entry needs exactly one.

### `Cannot find block: '<blockstate>'!`

**When:** palette load.

A `block`, `damaged`, or weighted-list block string names a block that is not registered. Check spelling and namespace, and make sure the mod providing it is actually installed. If the string contains `[...]` state properties, a malformed property list throws a different, uglier parser exception instead.

## Building and part errors

### `Misconfiguration! Floor were generated for a building where no part condition matches!`

**When:** chunk generation. **The most common error in the mod.**

The generator picked a floor index and no entry in the building's `parts` matched it.

The rule is **coverage**, not declaring bounds: every index from `-cellars` to `+floors` needs a matching part. Height comes from the [Profile](../reference/profile.md), and your building's own `minfloors`/`maxfloors` only *clamp* that unless you also set `overrideFloors: true`. So parts written for floors 0-2 work fine until the profile rolls 3.

**Fix:** add one part reference with **no condition fields at all**. It matches every level. Full detail at [Floor coverage](../reference/building.md#floor-coverage-the-most-common-crash).

`parts2` never causes this, it is a genuinely optional overlay.

### `Cannot find support block '<char>' for highway part '<part>'!`

**When:** chunk generation, on highways over open ground.

The part's `meta` has a `support` character that the palette does not define. Either define it, or remove the `support` meta entirely (the highway then generates with no pillars, which is safe). See [`meta`](../reference/part.md#meta).

### `Cannot find rail block '<char>' for type '<type>'!`

**When:** chunk generation, on railways.

The city style's `railblocks.railmain` character is not in the palette for that chunk. Check the character exists in every style a railway can pass through, not just your main one.

### A part comes out smeared diagonally, with no error

Not an exception, but it belongs here because people search for it. A `slices` row that is not exactly `xsize` characters long shifts every block after it in that layer. Rows are concatenated and indexed by position, and nothing validates their length. Count in UTF-16 units: an emoji counts as two. See [Part](../reference/part.md).

## Multi-building errors

### `Cannot find multibuilding: <name>` / `Cannot find building: <name>`

**When:** chunk generation.

A city style's `multibuildings` selector, or a multi-building's grid, names something that does not exist. Almost always a missing namespace: a bare name means `lostcities:<name>`. See [Namespaces](../getting-started/namespaces.md).

### `Topleft building type is not set!` / `Invalid building for multibuilding!`

**When:** chunk generation.

Internal consistency failures while assembling a multi-chunk building. In practice these follow from a multi-building whose grid does not match its `dimx`/`dimz`, or a city style that can produce a multi-building but has an empty `buildings` selector.

### `bound must be positive` (an `IllegalArgumentException`, no custom message)

**When:** chunk generation.

Thrown by the random number generator when a range is empty. Three known causes, none of which produce a friendly message:

| Cause | Fix |
|---|---|
| A multi-building's `dimx`/`dimz` exceeds the `areasize` it is placed with (`multisettings.areasize`, default 10; `scattered.areasize`, default 8) | Raise `areasize` or shrink the multi-building. See [Multi-Building](../reference/multibuilding.md) |
| A [Stuff Object](../reference/stuff.md) with `maxcount` equal to or below `mincount` | `maxcount` must be **strictly greater** |
| A Stuff Object with `maxheight` equal to or below `minheight` | Same rule |

## Asset lookup errors

### `Can't find '<name>' in minecraft:root!`

**When:** world load or chunk generation, depending on the asset type.

A name did not resolve.

!!! note "The message does not tell you which kind of asset it was"
    That trailing part looks like it should name the registry, but it prints the **root** registry name rather than `lostcities:citystyles` or `lostcities:parts`. It is the same string for every asset type, so it carries no information. To find out what was actually being looked up, read the stack trace: the frame below the lookup names the caller.

The overwhelmingly common cause is a **missing namespace**. Bare names resolve to `lostcities:`, so `"mycity"` looks for `lostcities:mycity` and finds nothing. The second most common is a wrong file path: assets live at `data/<namespace>/lostcities/<type>/<name>.json`, with **one** `lostcities` segment, not two.

### `Error getting resource <name>!`

Same situation, but the underlying failure was an exception rather than a missing entry. The wrapped cause underneath is the real message, look further down the stack trace.

### `Invalid name given to minecraft:root getOrThrow!`

A required name field was null or absent. Check for a missing key rather than a wrong one.

### Streets that just are not there, with a warning in the log

Not a crash. Street part lookups **warn and skip** instead of throwing, so a bad street part name produces `Cannot find '<name>' in minecraft:root!` as a **warning** in the log, and a chunk with no street layer. Highways, railways, and monorails throw for the same mistake. See [Streets, Highways, Rails & Monorails](../concepts/infrastructure-parts.md).

## Configuration errors

### `Bad landscape type: <type>!`

**When:** profile load, at startup.

A profile's `landscapeType` is not one of `default`, `floating`, `space`, `cavern`. Check spelling and case.

### `Unknown base profile '<name>'!`

A profile (or a mod creating one through the API) inherits from a base profile that does not exist.

### `Bad value for 'highwayLevelFromCities'!`

The profile's `highwayLevelFromCities` is not `0`, `1`, `2`, or `3`. Nothing clamps it, so any other number reaches the switch and throws.

### `Bad range specification: <l1>,<l2>!`

A [Condition](../reference/condition.md) or building part reference has a malformed `range`. It must be exactly two integers separated by a comma, as a string: `"range": "1,3"`. Not a list, not spaced, not a single number.

### `Can't find a valid spawn position!`

**When:** world creation. The world fails to create at all.

The profile's spawn settings cannot be satisfied. Setting any of `spawnBiome`, `spawnCity`, `spawnSphere`, `spawnNotInBuilding`, `forceSpawnInBuilding`, `forceSpawnBuildings`, or `forceSpawnParts` **replaces** vanilla's spawn search rather than layering onto it, and if the combination is impossible within `spawnCheckAttempts` chunks it hard-fails.

| Fix | |
|---|---|
| A `spawnCity` or `spawnSphere` name with no matching [Predefined](../reference/predefined.md) asset | Correct or remove it |
| Contradictory filters, like `spawnNotInBuilding` plus `forceSpawnInBuilding` | Pick one |
| A genuinely rare combination | Raise `spawnCheckAttempts` and `spawnCheckRadius` |

### `Condition '<name>' did not return a valid mob!`

**When:** chunk generation, placing a spawner.

A palette entry's `mob` field points at a [Condition](../reference/condition.md), and that condition matched nothing in this context. Add an unconditioned fallback entry to the condition's `values`, exactly like the building-parts rule above.

Note this is also the fix for the underlying misconception: `mob` is **not** a mob ID, it is a condition name. See [Palette](../reference/palette.md).

## Errors that indicate a mod bug, not your content

These carry no useful information for an author. If you hit one with plain JSON content, it is worth reporting upstream.

| Message | Where |
|---|---|
| `Not possible!` | street shape selection |
| `Error with rail!` | railway generation |
| `This is really impossible!` | railway layout |
| `This cannot happen: <n>` | chunk writing |
| `Cannot happen!` | transform / setup |
| `Staring interpolation twice` | noise generation (the typo is the mod's) |
| `Trying to sample interpolator outside the interpolation loop` | noise generation |
| `Cannot find city style for chunk: <coord>` | multi-building placement, usually a world style with an empty `citystyles` list |
| `Missing buildings for scattered '<name>'!` | a [Scattered](../reference/scattered.md) asset with neither `buildings` nor `multibuilding` |

## Nothing happens, and there is no error at all

The most common failure mode of all. Lost Cities does not warn about content it never found.

Work through [When nothing happens](../getting-started/first-city.md#when-nothing-happens).
