# Error Messages

!!! tip "TL;DR"
    Paste the message you got into the search box. Every message the mod throws by name is listed here with its cause and its fix.

Messages are quoted **exactly** as the mod produces them, with `<...>` marking a value the mod substitutes. Every entry was taken from the 7.4.12 source, not from bug reports.

!!! note "Where the message appears"
    The mod throws most of these during **chunk generation**. On a client that looks like a crash while you fly into new terrain. On a server it looks like a chunk that never finishes loading, plus a stack trace in the log. A few are thrown earlier, at world load. Each entry says which.

## Palette errors

### `Could not find entry '<char>' in the palette for part '<part>'!`

**When:** chunk generation.

A part used a character that the merged palette does not define.

The message names the **part**, not the palette, which misleads you when the fault is on the palette side. The causes, in order of likelihood:

| Cause | Fix |
|---|---|
| A typo in the part's `slices`, or a row of the wrong length shifting characters | Check row lengths first. The mod never validates them. |
| The character is defined in a palette that is not in this building's chain | Add it to the part's `refpalette`, or to the [Style](../reference/style.md)'s palettes. |
| The character is a `frompalette` alias in a **circular reference** | A cycle resolves to nothing and leaves the character undefined, with no warning at load. See [How aliases resolve](../reference/palette.md#how-aliases-resolve). |
| The character is a space and your style does not include the `common` palette | `" "` maps to air because `common` defines it, not because the mod special-cases it. |

### `Invalid palette entry for '<char>'! Not enough blocks in the random list (factor should go up to 128)`

**When:** the first time the mod compiles this palette, during generation.

A weighted list (`blocks`, or a referenced `variant`) has `random` weights totalling **less than 128**. The mod fills a fixed array of 128 slots and refuses a partially filled one.

Add a catch-all entry **last** with a large weight. The mod's own idiom is small honest numbers for the rare options, then something like `1000` at the end to fill the remainder. See [The 128-slot rule](../reference/palette.md#the-128-slot-rule-for-blocks-and-variant).

### `Invalid palette entry for '<char>'!`

**When:** the same point, for a different cause. The entry resolved to nothing usable. A `variant` name that does not exist is the usual reason.

### `Illegal palette <name>!`

**When:** palette load.

An entry in that palette has **none** of `block`, `variant`, `blocks` or `frompalette`. Every entry needs exactly one of them.

### `Cannot find block: '<blockstate>'!`

**When:** palette load.

A `block`, `damaged`, or weighted-list block string names a block that is not registered. Check the spelling and the namespace, and confirm that the mod providing the block is installed. If the string contains `[...]` state properties, a malformed property list throws a different and less readable parser exception instead.

## Building and part errors

### `Misconfiguration! Floor were generated for a building where no part condition matches!`

**When:** chunk generation. **This is the most common error in the mod.**

The mod picked a floor index and no entry in the building's `parts` matched it.

The rule is **coverage**, not declaring bounds. Every index from `-cellars` to `+floors` needs a matching part. The height comes from the [Profile](../reference/profile.md), and your building's own `minfloors` and `maxfloors` only clamp that unless you also set `overrideFloors: true`. So parts written for floors 0 to 2 work until the profile rolls 3.

**Fix:** add one part reference with **no condition keys at all**. It matches every level. See [Floor coverage](../reference/building.md#floor-coverage-the-most-common-crash).

`parts2` never causes this. It is a genuinely optional overlay.

### `Cannot find support block '<char>' for highway part '<part>'!`

**When:** chunk generation, on a highway over open ground.

The part's `meta` has a `support` character that the palette does not define. Either define the character, or remove the `support` meta. Without it the highway generates with no pillars, which is safe. See [`meta`](../reference/part.md#meta).

### `Cannot find rail block '<char>' for type '<type>'!`

**When:** chunk generation, on a railway.

The city style's `railblocks.railmain` character is not in the palette for that chunk. Check that the character exists in every style a railway can pass through, not only your main one.

### A part comes out smeared diagonally, with no error

This is not an exception, but readers search for it, so it belongs here. A `slices` row that is not exactly `xsize` characters long shifts every block after it in that layer. The mod concatenates the rows and indexes them by position, and nothing validates their length. Count in UTF-16 units: an emoji counts as two. See [Part](../reference/part.md).

## Multi-building errors

### `Cannot find multibuilding: <name>` and `Cannot find building: <name>`

**When:** chunk generation.

A city style's `multibuildings` selector, or a multi-building's grid, names something that does not exist. A missing namespace is almost always the cause, because a bare name means `lostcities:<name>`. See [Namespaces](../getting-started/namespaces.md).

### `Topleft building type is not set!` and `Invalid building for multibuilding!`

**When:** chunk generation.

These are internal consistency failures while the mod assembles a multi-chunk building. In practice they follow from a multi-building whose grid does not match its `dimx` and `dimz`, or a city style that can produce a multi-building but has an empty `buildings` selector.

### `bound must be positive`

**When:** chunk generation. This is an `IllegalArgumentException` from the JDK, with no message of the mod's own.

The random number generator throws it when a range is empty. There are three known causes, and none of them produces a helpful message.

| Cause | Fix |
|---|---|
| A multi-building's `dimx` or `dimz` exceeds the `areasize` it is placed with (`multisettings.areasize` defaults to 10, `scattered.areasize` to 8) | Raise `areasize` or shrink the multi-building. See [Multi-Building](../reference/multibuilding.md). |
| A [Stuff Object](../reference/stuff.md) whose `maxcount` is equal to or below its `mincount` | `maxcount` must be strictly greater. |
| A Stuff Object whose `maxheight` is equal to or below its `minheight` | The same rule. |

## Asset lookup errors

### `Can't find '<name>' in minecraft:root!`

**When:** world load or chunk generation, depending on the asset type.

A name did not resolve.

!!! note "The message does not tell you which kind of asset it was"
    The trailing part looks like it should name the registry, but the mod prints the **root** registry rather than `lostcities:citystyles` or `lostcities:parts`. The string is identical for every asset type, so it carries no information. To find out what the mod was looking up, read the stack trace. The frame below the lookup names the caller.

A missing namespace is by far the most common cause. A bare name resolves against `lostcities:`, so `"mycity"` looks for `lostcities:mycity` and finds nothing. A wrong file path is the second most common. Assets live at `data/<namespace>/lostcities/<type>/<name>.json`, with **one** `lostcities` segment, not two.

### `Error getting resource <name>!`

**When:** the same situation, except that the underlying failure was an exception rather than a missing entry. The wrapped cause below it in the stack trace is the real message.

### `Invalid name given to minecraft:root getOrThrow!`

**When:** the same lookup, when the name was null rather than wrong. Look for a missing key, not a misspelled one.

### Streets that are simply absent, with a warning in the log

This is not a crash. A street part lookup **warns and skips** instead of throwing, so a bad street part name produces `Cannot find '<name>' in minecraft:root!` as a **warning**, and a chunk with no street layer.

Note the wording differs by one word between the two paths. The throwing path says `Can't find`, and the warning path says `Cannot find`. Highways, railways and monorails throw for the same mistake. See [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md).

## Configuration errors

### `Bad landscape type: <type>!`

**When:** profile load, at startup.

A profile's `landscapeType` is not one of the six accepted values: `default`, `floating`, `space`, `cavern`, `spheres`, `cavernspheres`. Check the spelling and the case.

### `Unknown base profile '<name>'!`

**When:** profile load. A profile, or a mod creating one through the API, inherits from a base profile that does not exist.

### `Bad value for 'highwayLevelFromCities'!`

**When:** generation. The profile's `highwayLevelFromCities` is not `0`, `1`, `2` or `3`. Nothing clamps the value, so any other number reaches the switch and throws.

### `Bad range specification: <l1>,<l2>!`

**When:** the mod parses a [Condition](../reference/condition.md) or a building part reference with a malformed `range`.

`range` must be a string holding two integers separated by a comma, for example `"range": "1,3"`. It throws for one number, for a non-number, and for a stray space such as `"1, 3"`.

!!! warning "A third number does not throw"
    The mod reads only the first two pieces. `"1,2,3"` produces the range 1 to 2 and discards the 3, with no error and no log line. If your floors are wrong and you get no message, check for an extra number here.

### `Can't find a valid spawn position!`

**When:** world creation. The world fails to create at all.

The profile's spawn settings cannot be satisfied. Setting any of `spawnBiome`, `spawnCity`, `spawnSphere`, `spawnNotInBuilding`, `forceSpawnInBuilding`, `forceSpawnBuildings` or `forceSpawnParts` **replaces** the vanilla spawn search rather than layering onto it. If the combination is impossible within `spawnCheckAttempts` chunks, world creation fails outright.

| Cause | Fix |
|---|---|
| A `spawnCity` or `spawnSphere` name with no matching [Predefined](../reference/predefined.md) asset | Correct the name or remove the key. |
| Contradictory filters, such as `spawnNotInBuilding` with `forceSpawnInBuilding` | Choose one. |
| A combination that is merely rare | Raise `spawnCheckAttempts` and `spawnCheckRadius`. |

### `Condition '<name>' did not return a valid mob!`

**When:** chunk generation, while the mod places a spawner.

A palette entry's `mob` key names a [Condition](../reference/condition.md), and that condition matched nothing in this context. Add an unconditioned fallback entry to the condition's `values`, exactly as you would for building parts.

This error also corrects a common misconception. `mob` is **not** a mob ID. It is a condition name. See [Palette](../reference/palette.md).

## Errors that indicate a mod bug, not your content

These carry no useful information for an author. If you hit one with plain JSON content, it is worth reporting upstream.

| Message | Where it comes from |
|---|---|
| `Not possible!` | Street shape selection. |
| `Error with rail!` | Railway generation. |
| `This is really impossible!` | Railway layout. |
| `This cannot happen: <n>` | Chunk writing. |
| `Cannot happen!` | Transform and setup. |
| `Staring interpolation twice` | Noise generation. The typo is the mod's. |
| `Trying to sample interpolator outside the interpolation loop` | Noise generation. |
| `Invalid SpawnData` | Spawner placement, when the mod fails to encode the spawner NBT it has just built. |
| `Cannot find city style for chunk: <coord>` | Multi-building placement. Usually a world style with an empty `citystyles` list. |
| `Missing buildings for scattered '<name>'!` | A [Scattered](../reference/scattered.md) asset with neither `buildings` nor `multibuilding`. |
| `Could not find category '<name>'!` | The config screen asked for a settings category that does not exist. |
| `Could not find value '<name>'!` | The config screen asked for a setting that does not exist. |
| `Missing category: <name>` | Config registration, before any profile is read. |

The last three come only from the in-game config screen and the mod's own startup. Editing a profile JSON by hand cannot produce them.

## Nothing happens, and there is no error at all

This is the most common failure of all. The mod does not warn about content it never found.

Work through [When nothing happens](../getting-started/first-city.md#when-nothing-happens).
