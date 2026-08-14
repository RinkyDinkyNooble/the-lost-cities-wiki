# Error Messages

!!! tip "TL;DR"
    Paste the message you got into the search box. Every message the mod throws by name is listed here with its cause and its fix.

Messages are quoted **exactly** as the mod produces them, with `<...>` marking a value the mod substitutes. Every entry was taken from the source, not from bug reports.

Most of this page is 7.4.12. Version 7.5.1 has 36 messages that 7.4.12 does not, and removes none of the older ones. All 36 come from the new road and highway planners. They are in [Messages added in 7.5](#messages-added-in-75).

## Where you actually see these

None of these strings are written to a file by the mod as a matter of course. They reach you in one of two ways, and the difference decides which file to open.

### Thrown during chunk generation

**The game does not crash.** This is the single most important thing to know about
every message on this page that comes from generation.

`LostCityFeature` wraps the whole generation of a chunk in a `try` block that
catches `Exception`. When anything throws, the mod logs
`Error generating chunk <x>,<z>: <message>`, prints the stack trace, and carries on
with the next chunk.

| What actually happens | |
|---|---|
| The game | Keeps running. No crash report is written. |
| That chunk | Is left partially generated. Terrain may be there with the buildings missing. |
| Its neighbours | Often fail too. See below. |
| Every other chunk with the same fault | Fails the same way, one log line each |
| In game | Nothing tells you, beyond the world looking wrong |
| File to open | `logs/latest.log`. **Not** `crash-reports/`, because none is produced. |

Verified by running it: a datapack with an empty `bridges` selector produced 1842
`Error generating chunk` lines in a single session, and the game never crashed.

The same `catch` is present in 7.4.12, 7.5.1, 8.4.1 and 10.0.1, so this applies to
every version this wiki covers.

!!! danger "One broken building takes its neighbours down with it"
    A chunk does not only generate itself. To shape terrain at its edges, to lay
    railways, and to spread debris, it asks the chunks around it for their
    `BuildingInfo`, and building that info is what evaluates the part conditions.
    So a building that throws fails **every chunk that looks at it**, not only the
    chunk it stands in.

    The reach is much larger than one chunk, because those queries chain.
    `getDesiredMaxHeightL2` calls `getDesiredMaxHeightL1` on a neighbour, which
    queries its own neighbours in turn.

    Measured on 7.4.12: **3 broken buildings produced 77 failed chunks**, spread
    over a 13 by 10 chunk area. Two of the three stood 6 chunks apart, and the
    failures joined into one continuous region.

    The practical consequence when you are diagnosing: **the coordinates in
    `Error generating chunk x,z` are usually not where your mistake is.** They are
    where something asked about it. Look for the building the message names, or use
    the extent of the failed region to find its centre.

!!! note "Which faults spread and which stay put"
    The split is where in generation the throw happens, and it is worth knowing
    because it tells you how far to look.

    | Fault | Thrown while | Spreads |
    |---|---|---|
    | A level matching no part, an empty selector, a bad `range` | Building the chunk's `BuildingInfo` | **Yes.** Neighbours build that same info. |
    | An undefined palette character | Placing blocks | **No.** One chunk, one line. |
    | A `loot` or `mob` name that is not a Condition | The post-generation pass | **No.** One chunk. |

    Measured in the same run: 3 buildings with uncovered levels took out 77 chunks,
    while a building with a circular palette alias standing 6 chunks away failed
    exactly 1, its own, and its four neighbours generated normally.

!!! danger "Volume is the real symptom, and the traces run out"
    A single misconfiguration produces one failure per affected chunk, so a short
    session can log thousands. After the first few, the JVM stops recording stack
    traces for a repeatedly thrown exception, and the remaining lines carry only the
    message, or `null`.

    **Read the earliest errors in the file.** The recent ones are the least useful.

Generation is not the only place the mod throws. Anything thrown while a profile or
an asset is being **loaded**, before generation starts, is outside that `try` and
behaves like a normal crash.

In the log, the message appears as the exception line at the top of the stack trace:

```
java.lang.RuntimeException: Misconfiguration! Floor were generated for a building where no part condition matches!
	at mcjty.lostcities.worldgen.lost.BuildingInfo...
```

Search for the message text, then read **down** the trace. The frames below the mod's own classes tell you which chunk and which asset was being processed.

### Logged warnings

A few failures are logged instead of thrown. The mod writes these through a log4j logger named `lostcities`, so they appear only in `logs/latest.log` and in the server console. **They never produce a crash report**, and nothing in game tells you they happened.

The line looks like this:

```
[Server thread/WARN] [lostcities/]: Cannot find 'mycity:my_street' in minecraft:root!
```

This is the quiet failure mode behind streets, parks, fountains, stairs, rail dungeons and building fronts that simply never appear. If content is missing and the game has not crashed, search `latest.log` for `lostcities` before you touch your JSON.

!!! tip "Grep the log rather than scrolling it"
    `latest.log` is large. On Windows, `findstr /C:"lostcities" logs\latest.log` is enough. The mod's own lines are the only ones carrying that logger name.

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

### `Error getting resource <name>!`

**When:** chunk generation, and for `loot` specifically during the post-generation
pass, after every block is already placed.

A named asset is not in the mod's registry. The name in the message is exactly what
you wrote, so the fault is a name that does not exist, a missing namespace, or the
wrong **kind** of name.

| Cause | Fix |
|---|---|
| A palette `loot` or `mob` key holds a loot table or entity ID | Both name a [Condition](../reference/condition.md). Wrap the value in a one-entry Condition and name that instead. This is by far the most common form. |
| A bare name that resolved into the `minecraft` namespace | See [Namespaces](../getting-started/namespaces.md#the-default-namespace-trap). |
| A genuine typo in an asset name | Compare against the file name, which is the asset name. |

!!! warning "For `loot`, the symptom does not look like an exception"
    The loot pass runs after placement, so the blocks are already in the world. What
    you see is a building whose chests can be opened, are empty, and **render
    invisible**, because their block entities were never completed. Nothing appears
    in chat. Confirmed in game on 7.4.12.

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

**Fix:** add one part reference with **no condition keys at all**. It matches every level. See [Floor coverage](../reference/building.md#floor-coverage-the-most-common-failure).

`parts2` never causes this. It is a genuinely optional overlay.

### `NullPointerException` in `ChunkDriver.correct`

**When:** chunk generation, the moment the mod places a door. Observed in a real world, not derived from reading code.

```
Error generating chunk -6,-8: Cannot invoke
  "net.minecraft.world.level.block.state.BlockState.m_60734_()" because "state" is null
    at mcjty.lostcities.worldgen.ChunkDriver.correct(ChunkDriver.java:253)
    at mcjty.lostcities.worldgen.ChunkDriver.add(ChunkDriver.java:289)
    at mcjty.lostcities.worldgen.gen.Doors.generateDoors(Doors.java:60)
```

The building's `filler` character did not resolve to a block.

`Doors` asks the building for its filler block and looks the character up in the **building's** palette. That palette is the [Style](../reference/style.md)'s palettes plus the building's own `refpalette` or `palette`. **A `refpalette` on a part is not in that set.**

| Cause | Fix |
|---|---|
| The `filler` character is defined only in a palette that the building's **parts** reference | Add the same `refpalette` to the **building**. |
| The character is not defined anywhere in scope | Define it, or change `filler` to a character the style already provides. |

!!! warning "This produces one failure per chunk, and most of them have no stack trace"
    Every affected chunk logs `Error generating chunk <x>,<z>`. After the first few, the JVM stops recording stack traces for a repeatedly thrown `NullPointerException`, so the rest log only `null` with no trace and no clue.

    A log full of `Error generating chunk ...: null` with a handful of real traces near the top is this bug. **Read the earliest errors in the file**, not the most recent.

The chunks still generate. Terrain and streets appear, buildings are missing or partial, and nothing tells you in game.

### `NullPointerException` on a null `Character`

**When:** chunk generation. Observed in a real world.

```
java.lang.NullPointerException: Cannot invoke "java.lang.Character.charValue()"
  because "corridorRoofBlock" is null
    at mcjty.lostcities.worldgen.gen.Corridors.generateCorridors
```

The name in the message tells you which character is missing. Others seen include
`CityStyle.getStreetBlock()`.

The [City Style](../reference/citystyle.md) in use does not define that character,
and the generator dereferences it without checking. **This only reaches you if your
city style inherits nothing**, because `citystyle_common` supplies the whole set.

**Fix:** inherit a style that defines them, or set all of them yourself. The full
list is in [City Style](../reference/citystyle.md).

Expect to meet these one at a time. Each run fails on the first missing character it
reaches, so fixing one exposes the next.

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

!!! note "If the message reads `Cannot find multibuilding: null`, the selector is empty"
    A literal `null` in the message means the mod asked the city style for a multi-building name and got nothing back, which happens when the merged `multibuildings` selector is empty. It surfaces once an area rolls at least one multi-building, so the count comes from the world style's `multisettings`. Either populate the selector or set `multisettings.maximum` to `0`.

### `Invalid building for multibuilding!`

**When:** chunk generation, on any chunk the mod decided to put a building on.

**The name is misleading. This is the empty `buildings` selector error, and it has nothing to do with multi-buildings in the usual case.**

The mod asks the city style for a random building name. When the merged `buildings` selector is empty, the weighted picker returns `null`, and the mod throws this rather than continuing.

**Fix:** give the city style at least one entry in `selectors.buildings`, or inherit from a style that has some. Remember that inheritance is additive, so writing `"buildings": []` on a style that inherits `citystyle_common` still leaves you the parent's 8 entries. You only reach this error when the **merged** list is empty. See [City Style](../reference/citystyle.md#an-empty-selector-list-is-safe-for-five-of-the-eight-and-fatal-for-three).

### `Topleft building type is not set!`

**When:** chunk generation, on a chunk that belongs to a multi-building but is not its top-left corner.

The mod looks up the top-left chunk's characteristics to find out which building this multi-chunk structure is, and that value came back null. In practice this follows from a multi-building whose grid does not match its `dimx` and `dimz`.

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

!!! danger "The usual cause is an empty `bridges` selector"
    A city style with `"bridges": []` produces this on the first city chunk that has a building. The mod resolves the bridge part eagerly, alongside the door block and the stair part, and **does not test `bridgeChance` first**. Setting the chance to `0` does not protect an empty list.

    Keep at least one entry in `bridges` and set `bridgeChance` to `0` if you do not want bridges. See [City Style](../reference/citystyle.md#an-empty-selector-list-is-safe-for-five-of-the-eight-and-fatal-for-three).

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

On 7.5.0 and later the key also accepts `4`, so only a value outside `0` to `4` throws there. See [What changed in 7.5](../versions/7-5.md#highwaylevelfromcities-changed-its-default).

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

## Messages added in 7.5

Version 7.5.1 has 36 messages that 7.4.12 does not, and removes none of the older
ones. Every one comes from the planned road system or the inter-city highway
network, so none of them can appear on 7.4.12. They also appear on 8.4.1, 9.5.1
and 10.0.1, which carry the same system.

No 7.5.0 jar was checked, so these are attributed to the 7.5 line rather than to a
specific patch release.

If you see one of these, your road settings are the cause, not your datapack.

### Road settings rejected at config load

The mod validates the road keys against each other, not only against their own
ranges. A value inside its own range still throws if it contradicts another key.

| Message | Keys involved |
|---|---|
| `Primary road candidate spacing must be between 8 and 128 chunks` | `primaryRoadSpacingX`, `primaryRoadSpacingZ` |
| `Road separation and edge distance must be between 2 and 32 chunks` | `minimumRoadSeparation`, `minimumRoadEdgeDistance` |
| `Secondary road counts must be between 0 and 128` | the four `secondaryRoad*Count*` keys |
| `Secondary road minimum counts cannot exceed maximum counts` | `secondaryRoadMinCountX` against `secondaryRoadMaxCountX`, and the Z pair |
| `tertiaryRoadMinLength cannot exceed tertiaryRoadMaxLength` | `tertiaryRoadMinLength`, `tertiaryRoadMaxLength` |
| `Invalid tertiary road chance or length` | `tertiaryRoadChance` with the two length keys |
| `Invalid primary road activation chance or forced interval` | `primaryRoadOptionalChance`, `primaryRoadForceEvery` |
| `Invalid planned primary bridge chance or maximum length` | `plannedPrimaryBridgeChance`, `plannedPrimaryBridgeMaxLength` |
| `highwayMinimumHubDistance cannot exceed highwayMaximumHubDistance` | the two hub distance keys |
| `highwayHubSampleSpacing cannot exceed highwayPlanningCellSize` | `highwayHubSampleSpacing`, `highwayPlanningCellSize` |

### Road settings rejected when the planner is built

The same values are checked a second time, by the planner itself. These messages
are worded differently from the ones above even when they guard the same key, so
match on the exact text to tell which check failed.

| Message | Source |
|---|---|
| `Invalid primary road activation settings` | Street planner |
| `Invalid secondary road count range` | Street planner |
| `Invalid tertiary road settings` | Street planner |
| `Primary road candidate spacing must be at least 8 chunks` | Street planner |
| `Road separation and edge distance must be at least 2 chunks` | Street planner |
| `Highway planning-cell size must be between 32 and 512 chunks` | Highway planner |
| `Highway hub sample spacing must be positive and no larger than the planning cell` | Highway planner |
| `Highway hub minimum potential must be between 0 and 1` | Highway planner |
| `Highway hub search radius must be between 0 and 8 cells` | Highway planner |
| `Highway minimum hub distance must not exceed the maximum` | Highway planner |
| `Highway maximum hub distance must not exceed 4096 chunks` | Highway planner |
| `Highway maximum connection degree must be between 1 and 8` | Highway planner |
| `Invalid highway route length or city penalty` | Highway planner |
| `Invalid highway level mode or fixed network level` | Highway planner |

### `The inter-city highway planner is unavailable in LEGACY mode`

**When:** something asks for the highway planner while `highwayGenerationMode` is
`LEGACY`.

The two modes are not interchangeable at runtime. Set `highwayGenerationMode` to
`INTERCITY_NETWORK_V1`, or leave the caller alone. Note that this is a separate key
from `streetGenerationMode`: setting one to `LEGACY` does not set the other.

### Logged warnings, not crashes

These two are logged and generation continues. They appear in `logs/latest.log`
with the `[lostcities/]` prefix, and nowhere else.

| Message | Meaning |
|---|---|
| `Unknown persisted street mode '<name>' for <dimension>; using LEGACY` | The world's saved street mode is not a name the mod recognises. It falls back to `LEGACY`, so the world generates with 7.4.12 street behaviour from then on. |
| `Unknown persisted highway mode '<name>' for <dimension>; using LEGACY` | The same, for highways. |

!!! warning "9.5.1 and 10.0.1 removed these two warnings"
    The saved data keys are unchanged, but neither version logs this message. On
    those versions an unrecognised saved mode produces no line at all. Do not read
    a silent log as proof that the mode loaded correctly.

### Messages that indicate a mod bug

These carry no useful information for an author.

| Message | Where it comes from |
|---|---|
| `Lost Cities generation context is not active` | Generation context, accessed outside a generation pass. |
| `Cannot access Lost Cities world generation data without an overworld` | Saved data lookup. |
| `Cannot access Lost Cities highway data without an overworld` | Highway saved data lookup. |
| `No forced primary candidate found` | Street planner, choosing a forced corridor. |
| `Highway connection endpoints must be distinct and canonical` | Highway graph construction. |
| `X highway segment must have a constant Z coordinate` | Highway segment construction. |
| `Z highway segment must have a constant X coordinate` | Highway segment construction. |
| `Scattered buildings only support rotations` | Scattered placement, given a transform that is not a rotation. |
| `Don't access this client-side!` | Server-only data reached from the client. Added in 8.4.1, not present in 7.5.1. |

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
