# Claim tests

Everything on this wiki was traced from the mod's code. That is not the same as
having watched it run.

This page describes a datapack that exists to close that gap. Each asset in it
tests one claim the wiki makes, and each test is designed so that the result is
visible from the air with no commands and no guessing.

The pack is at `docs/examples/wiki-test/` in the repository.

## Results

All tests below were run on 7.4.12, Minecraft 1.20.1, Forge, across 4 builds of the
pack. Every claim tested is now either confirmed in a world or corrected.

| Claim | Result |
|---|---|
| Multi-building grid is `buildings[x][z]`, outer list is X | **Confirmed.** Red north-west, yellow south-west, blue north-east, green south-east. |
| A weighted `blocks` list must fill 128 slots | **Confirmed.** The 100 + 28 list generated speckled decks. |
| A concrete definition beats a `frompalette` alias | **Confirmed.** A probe aliasing `A`, which the shipped style defines concretely, came out as the style's stone stairs rather than the alias target. |
| `frompalette` resolves to the aliased character | **Confirmed.** Moved to `λ`, which no shipped palette defines, and the walls generated red. |
| `overrideFloors` replaces the profile's bounds instead of narrowing them | **Confirmed.** The overriding building generates at 1 storey beside 5 storey towers that declare the same bounds without the key. |
| A street part name accepts a list, sampled per chunk | **Confirmed.** Both marked variants appear across the road network, mixed. |
| `streetblocks.parts` is all or nothing on inheritance | **Confirmed.** All 7 shapes were restated and all generate. |
| `streetblocks.parts.full` | **Refuted, and it is a mod bug.** The `full` shape never generates. See [Streets](../concepts/infrastructure-parts.md#streets). |

### Two wiki errors this found

**`filler` and `rubble` resolve against the building's palette, not the part's.**
The page said otherwise, and the wiki's own tutorial example carried the fault. It
produced 590 failed chunks on the first run, almost all of them logging only `null`
because the JVM stops recording traces for a repeated `NullPointerException`.
[Corrected](../reference/building.md#filler-what-it-is-and-why-it-is-required).

**A building's `minfloors` can push it past every maximum.** The page said a
building "can only make itself shorter than the profile allows, never taller". The
minimum is a `max()` applied after the maximum, so the opposite is true.
[Corrected](../reference/building.md#how-floor-and-cellar-counts-are-decided).

Both errors were found because a test failed and the reason had to be chased. Two
of the tests were also badly designed, and rebuilding them is what exposed the
`full` bug.

## What it targets

Lost Cities **7.4.12**, Minecraft **1.20.1**, Forge. The claims tested are
version-specific and the pack is not meaningful on another version.

## Installing it

The datapack and the profile go in different places. This trips people up, so it
is spelled out.

**1. The datapack.** Copy `wiki-test/` into the world, keeping the folder:

```
<world>/datapacks/wiki-test/
  pack.mcmeta
  data/wikitest/lostcities/...
```

You can also add it on the world creation screen with the **Data Packs** button,
which is easier because the pack must be present before the world generates.

**2. The profile.** This is config, not datapack. Copy the file out of the pack:

```
config/lostcities/profiles/wikitest.json
```

**3. The wiring.** In `config/lostcities/common.toml`:

```toml
dimensionsWithProfiles = [
    "lostcities:lostcity=wikitest"
]
```

**4. Restart**, then create a new world and travel to the Lost City dimension.
`cityChance` is `0.2`, so cities are common. `buildingchance` is `0.15`, so most
city chunks are streets, which is what the street test needs. Ruins and explosions
are both off, so the test buildings stay readable.

## The tests

### 1. Multi-building grid order

**Claim:** `buildings[x][z]`. The outer list is X, so index 0 is west. Inside each
list, index 0 is north.

**How to read it:** find the 2 by 2 building made of 4 solid colours and look
straight down with F3 open so you know which way north is.

| | West | East |
|---|---|---|
| **North** | Red | Blue |
| **South** | Yellow | Green |

**If the wiki is wrong** and the outer list is Z, then yellow and blue swap. Red
and green stay put either way, so they tell you nothing. **Yellow and blue are the
whole test.**

### 2. `overrideFloors`

**Claim:** with `overrideFloors`, a building's `maxfloors` is used alone. Without
it, the smallest of the profile, city style and building values wins the maximum,
and the largest wins the minimum.

The profile asks for 5 to 6 floors. Both test buildings set `minfloors: 1` and
`maxfloors: 1`. Both bounds are needed, because the minimum is applied last and is
a `max()`, so leaving `minfloors` out lets the profile's 5 win in both cases. That
is what made builds 2 and 3 unreadable.

| Building | Colour | `overrideFloors` | Expected |
|---|---|---|---|
| `clamped` | Purple | absent | 5 or 6 floors. The profile's minimum of 5 beats the building's 1 in the `max()`. |
| `overridden` | Orange | `true` | 1 floor. Both of the building's own bounds are used alone. |

**How to read it:** orange should be a single storey next to 5 or 6 storey purple
towers. That difference is unmissable. Same height means the override does nothing.

### 3. Street part names accept a list

**Claim:** a street part name may be a list, and the mod picks one uniformly at
random per chunk. No file the mod ships uses the list form, so this has never been
exercised.

**Every** street shape is set to the same 2 parts, one marked with a **gold** block
square and one with a **diamond** block square. Build 3 marked only `full`, which
turned out to be unreachable, so no marker ever appeared.

**How to read it:** follow the roads. Full-street chunks should show both gold and
diamond markers, mixed with no pattern. Only one marker appearing across many
chunks means the list is not being sampled.

Since every shape is overridden, every street chunk should carry a marker. A world
of streets with no marker at all would mean the list form does not work.

### 4. Palette features

**Claim A:** a weighted `blocks` list must fill 128 slots. The probe building's
floors and ceilings use a list of `100` white concrete and `28` black concrete,
totalling exactly 128.

**Claim B:** `frompalette` is a character alias. The probe building's walls use the
character `λ`, aliased to red.

The first attempt used `A`, which the shipped style already defines concretely, so
the concrete definition won and the walls came out as stone stairs. `λ` is not used
by any shipped palette, so nothing competes with the alias this time.

**How to read it:** find the building with speckled white and black decks. Its
walls should be **red**. Roughly 1 block in 5 of the deck should be black.

If the walls come out as anything other than red, look for
`Could not find entry 'λ' in the palette for part 'wikitest:palette_probe'!` in the
log. That would mean the alias did not resolve at all, rather than losing to a
concrete definition.

## If nothing generates

Run this first:

```
/lostcities locate wikitest:overridden
```

A hit means the whole chain resolved. If it reports nothing, stand in a city chunk
and run `/lostcities debug`, which dumps the generator's decisions for that chunk to
the **server console**, not to chat.

Then work through [When nothing happens](../getting-started/first-city.md#when-nothing-happens).

## The failure-mode pack

Every test above is a positive claim: do this, and that happens. The wiki also
makes **failure** claims, and those are the ones that cost a reader most when they
are wrong. A second pack tests them, at `docs/examples/wiki-fail/`.

It ships **3 profiles**. Each isolates one claim, and 2 of them are expected to
crash world generation, so they must be run one at a time. A crash in the first
would hide anything after it.

!!! warning "2 of these deliberately break world generation"
    Use a throwaway world for each, and make a new one between runs. That is the
    test, not a mistake.

### Installing

The datapack goes in as usual. All 3 profiles go into
`config/lostcities/profiles/`. Then run them one at a time by changing a single
line in `config/lostcities/common.toml` and restarting:

```toml
dimensionsWithProfiles = [ "lostcities:lostcity=wtfailbridge" ]
```

Then `wtfailfloors`, then `wtfailsafe`.

### What each one tests

| Profile | Claim | Result |
|---|---|---|
| `wtfailbridge` | An empty `bridges` selector fails **even when `bridgeChance` is 0**, because the bridge part is resolved eagerly for every building chunk | **Confirmed.** 1842 failed chunks, all `Invalid name given to minecraft:root getOrThrow!`, with `bridgeChance` at `0.0`. |
| `wtfailfloors` | A building whose only part reference is gated on `top` matches nothing on lower floors | **Confirmed.** 1471 failed chunks, `Misconfiguration! Floor were generated for a building where no part condition matches!` |
| `wtfailsafe` | `parks`, `fountains`, `stairs`, `fronts` and `raildungeons` are safe to leave empty | **Confirmed.** Zero `Error generating chunk` lines and zero exceptions, with buildings generating normally and no parks, fountains, stairs, fronts or rail dungeons anywhere. |

The 3 city styles deliberately do **not** inherit `citystyle_common`. Selector
inheritance is additive, so an inherited selector cannot be emptied, and emptying
one is the whole point of the first test. That is itself a confirmation of the
[additive inheritance rule](../reference/citystyle.md#inheritance).

The `safe` result is a clean comparison rather than a single observation. The same
5 selectors were empty in all 3 runs. The first 2 produced 1892 failed chunks and
**not one** came from a selector. The only change in the third was supplying the
missing city style characters, after which the count went to 0.

!!! danger "Not inheriting has a second consequence, which cost 2 runs"
    A standalone city style must define every character the generator dereferences
    without a null check, not just the selectors. Build 1 omitted them all and
    failed on `streetblocks.street`. Build 2 supplied the street characters and
    failed on `corridorblocks.roof`. Each run only reveals the next missing one.

    Build 3 supplies the complete set, taken from `citystyle_common`. The full list
    is in [City Style](../reference/citystyle.md).

    The 2 crash tests were unaffected, because their own faults hit first and
    produced the exact predicted messages.

!!! note "Omitting a selector and writing `[]` are the same thing"
    `Selectors` stores an omitted list as `null`, but the city style initialises
    every selector to an empty list and only adds to it when the codec supplies
    one. Both routes end at an empty list, so the bridge test omits `bridges`
    rather than writing `[]`, and the result is identical.

### The validator already catches one of them

Running `validate.py` against this pack reports exactly 1 error:

```
ERROR  toponly.json: no unconditioned part reference;
       some floor will match nothing and crash generation
```

That is the `wtfailfloors` crash, caught before the game ever starts. If the
in-game result matches, the rule the future DevTool will enforce is correct.

## The pinned-grid pack

The two packs above both had the same weakness: the tests generate wherever the
world happens to put them, so reading a result starts with hunting for the
building. This third pack removes that. It is at `docs/examples/wiki-test6/`,
and `wiki-test5/` is the first build of it, kept because its failures are the
finding.

A [predefined city](../reference/predefined.md) pins one city to world chunk
**8, 8** with a radius of 8, and pins every test building to a fixed chunk inside
it. `cityChance` is `0.0`, so that city is the only one in the world. Each test
therefore has a block coordinate you can fly straight to.

### Installing

Same split as before. The datapack goes in the world, the profile goes in the
config folder:

```
<world>/datapacks/wiki-test6/
config/lostcities/profiles/wtsix.json
```

```toml
dimensionsWithProfiles = [ "lostcities:lostcity=wtsix" ]
```

Restart, make a new world, enter the Lost City dimension, then go to the grid:

```
/execute in lostcities:lostcity run tp @s 136 120 136
```

### Where everything is

Every test building is one chunk. The gaps between them are pinned streets, and
the grey buildings filling the rest of the city are backdrop, not a test.

| # | Test | Building | Chunk | Block corner | Floors |
|---|---|---|---|---|---|
| 1 | Pinned coordinates are relative | `origin` | 8, 8 | 128, 128 | 4 |
| 2 | A third number in `range` | `rangetest` | 10, 8 | 160, 128 | 6 |
| 3 | Conditions are AND, never OR | `andtest` | 12, 8 | 192, 128 | 4 |
| 4 | `belowpart` | `belowtest` | 14, 8 | 224, 128 | 3 |
| 5 | Palette precedence | `prectest` | 8, 10 | 128, 160 | 3 |
| 6 | The 128-slot cutoff | `slottest` | 10, 10 | 160, 160 | 2 |
| 7 | `shape=` on stairs is discarded | `stairtest` | 12, 10 | 192, 160 | 1 |
| 8 | `torch` attachment pass | `torchtest` | 14, 10 | 224, 160 | 1 |
| 9 | Loot with both chances at 0 | `loottest` | 8, 12 | 128, 192 | 2 |
| 10 | `mob` names a Condition | `mobtest` | 10, 12 | 160, 192 | 1 |
| 11 | `tag` raw NBT | `tagtest` | 12, 12 | 192, 192 | 1 |
| 12 | A `char` longer than one character | `chartest` | 14, 12 | 224, 192 | 2 |
| 13 | A circular `frompalette` | `circulartest` | 8, 14 | 128, 224 | 2 |

### What each one should look like

**1. Pinned coordinates are relative.** A solid emerald tower, 4 floors. It is
pinned at `chunkx: 0, chunkz: 0` while the city is at 8, 8. If the coordinates
are relative, as the code says, it stands on chunk 8, 8. If they were absolute it
would stand at block 0, 0, far outside the city, and probably nowhere at all.

**2. A third number in `range`.** Six floors. The lower part is gated
`range: "0,2,9"` and the upper one `range: "3,5"`.

| Result | Means |
|---|---|
| Gold on floors 0 to 2, diamond on 3 to 5 | The mod read `0,2` and threw the `9` away. What the wiki says. |
| Gold and diamond mixed on every floor | The mod used the `9`, so both entries match most floors. |
| The chunk fails, `Bad range specification` | The mod rejects a third number rather than ignoring it. |

**3. Conditions are AND, never OR.** Four floors: white bottom, two gold, red
top. The middle entry sets `ground: false` **and** `top: false`. Under OR that
entry would match every floor, and the tower would come out mixed instead of
banded.

**4. `belowpart`.** Three floors: white, gold, diamond, bottom to top. Each floor
above the first is selected only by what sits under it. If `belowpart` does not
match on a fully qualified name, floors 1 and 2 match nothing and the chunk fails
with `Misconfiguration! Floor were generated for a building where no part
condition matches!`.

**5. Palette precedence.** Three floors, each one a different level of the
palette merge for the same character.

| Floor | Comes out | Confirms |
|---|---|---|
| 0, gold | The building's `refpalette` | Building level applies when the part has no palette |
| 1, diamond | The part's `refpalette` | Part beats building |
| 2, lapis | The building redefines `A`, which the shipped standard style defines concretely | Building beats style |

The part on floor 1 has a palette holding **one** character. It still needs `#`
and `_` from the building's palette, so if it comes out at all, a part palette
merges rather than replaces. If instead the chunk fails on
`Could not find entry '#'`, it replaces.

**6. The 128-slot cutoff.** A white and black speckled block, 2 floors. The
weighted list is 120 white, then 20 black, then 100 red. The wiki says the black
entry is cut short at 8 slots and the red entry gets nothing. **One red block
anywhere on this building refutes it.**

**7. `shape=` on stairs is discarded.** A stone deck holding five oak stairs with
nothing next to any of them, all written `shape=outer_right`. They should all be
straight. Four rows further along is a perpendicular pair, which is the geometry
that does produce a corner.

**8. `torch` attachment pass.** Two torches. One stands on the deck, which is the
easy case. The other sits one block up with air underneath and a stone block to
its west, so it can only survive as a wall torch. If the attachment pass works it
is attached to that stone. If it does not, it is missing.

**9. Loot with both chances at 0.** Eight chests, four per floor. The profile sets
`generateLoot: true`, `buildingWithoutLootChance: 0.0` and
`chestWithoutLootChance: 0.0`, so the wiki says **every one** of them is filled.
Nothing is above them to overwrite. One empty chest here means one of the five
causes on [Palette](../reference/palette.md#why-a-chest-generates-empty) is
missing from that list.

**10. `mob` names a Condition.** Three spawners. The palette gives them
`mob: "wt5:mobpick"`, and that condition resolves to `minecraft:blaze`. Blaze
spawners confirm it. Pig spawners, the vanilla default, would mean the value
never reached the spawner.

**11. `tag` raw NBT.** Three chests carrying a `CustomName`. Open one. The title
should read **WIKITAG**.

**12. A `char` longer than one character.** Gold walls. The palette entry is
written `"char": "王zz"` and the part uses `王`. Gold walls mean the mod kept the
first code unit and discarded the rest without complaining.

**13. A circular `frompalette`.** This one is **meant to fail**, and it is the
only chunk in the world that should. `Ѱ` aliases `Ѳ` and `Ѳ` aliases `Ѱ`, so
neither resolves. Expect nothing at block 128, 224, no message at load, and this
in the log:

```
Could not find entry 'Ѱ' in the palette for part 'wt5:ct_box'!
```

That the other twelve buildings are unaffected is itself the point. A failure is
scoped to the chunk that caused it.

### Results from the first build

Run on 7.4.12, Minecraft 1.20.1, Forge. The game did not crash.

| Claim | Result |
|---|---|
| A pinned building's coordinates are relative to the city | **Confirmed.** The tower pinned at `0, 0` stands on world chunk 8, 8 while the city is at 8, 8. |
| A predefined city generates at `cityChance: 0.0` | **Confirmed.** One city, exactly where it was pinned, in an otherwise empty world. |
| Condition keys chain with AND, never OR | **Confirmed.** Banded white, gold, red rather than mixed. |
| `mob` names a Condition | **Confirmed.** Blaze spawners, from a condition resolving to `minecraft:blaze`. |
| `tag` places raw NBT | **Confirmed.** The chests read WIKITAG. |
| A `char` of more than one character keeps the first | **Confirmed.** `"char": "王zz"` gave gold walls under `王`. |
| A circular `frompalette` leaves the character undefined, silently at load | **Confirmed.** Nothing at load, then `Could not find entry 'Ѱ' in the palette for part 'wt5:ct_box'!` and one empty chunk. |
| `shape=` on a stair block string is discarded | **Confirmed.** The five isolated stairs came out straight, and the perpendicular pair produced a corner. |

Four tests did not report, because I built them wrong, and one reported
something better than what it was testing.

**`loot` does not name a loot table.** It names a
[Condition](../reference/palette.md#loot-names-a-condition-not-a-loot-table),
exactly as `mob` does. `"loot": "minecraft:chests/simple_dungeon"` threw
`Error getting resource minecraft:chests/simple_dungeon!` in the post-generation
pass, which left chests that open, are empty, and **render invisible**, because
their block entities were never finished. The page had called `loot` a loot table
and had listed a bad name as one of the silent causes of an empty chest. Both are
corrected.

**Three tests declared one level fewer than they generate.** `rangetest`,
`belowtest` and `prectest` each covered levels `0` to `maxfloors - 1`, when levels
run `0` to `maxfloors` **inclusive**. The wiki says this plainly and I did not
follow it. Every one of them failed on
`Misconfiguration! Floor were generated for a building where no part condition
matches!`. `andtest` was the only conditioned building to survive, because
`ground` and `top` cover any height.

### Results from the corrected build

Every test that had been obscured reported. Same version, same method.

| Claim | Result |
|---|---|
| A third number in `range` is discarded | **Confirmed.** `"0,2,9"` gave gold on levels 0 to 2 and diamond on 3 to 6, so the mod read `0,2`. |
| Levels run 0 to `maxfloors` inclusive | **Confirmed again.** `maxfloors: 6` produced 7 storeys, `maxfloors: 2` produced 3. |
| A part palette beats a building palette | **Confirmed.** Gold on level 0, diamond on level 1 from a part palette holding that one character. |
| A part palette **merges**, it does not replace | **Confirmed.** That part palette defines one character and the part still resolved `#` and `_` from the building's. |
| A building palette beats the style's | **Confirmed.** Level 2 came out lapis, not the standard style's stone stairs, for a character the shipped style defines concretely. |
| The 128-slot cutoff | **Confirmed.** White and black speckle with **no red block anywhere**, from a list of 120 white, 20 black, then 100 red. |
| `loot` names a Condition | **Confirmed.** 12 chests, all rendered, all filled, once the value went through a Condition. |
| Both loot chances at `0` fill every chest | **Confirmed.** 12 of 12. |
| A palette fault stays in its own chunk | **Confirmed.** The circular alias failed chunk 8, 14 and nothing else, in two separate worlds. |

Two tests reported something other than what they were testing.

### `belowpart` does not do what its name says

The `belowpart` chain failed every chunk, in open ground and again over ocean.
Reading the mod explains why, and it is the second bug this wiki has found.

`ConditionContext` is handed the part below the current level and stores it in a
field called `belowPart`. **That field has no accessor and nothing reads it.** The
predicate compiled for `belowpart` calls `getPart()`, the current part, which is
exactly what `inpart` compiles to. The two tests are the same test.

Underneath that sits a second problem: a building's floor loop builds its condition
context before it has picked a part, so the current part is the literal `<none>`.
Neither `inpart` nor `belowpart` can match anything from a building's `parts` list,
and fixing the first bug would not change that.

Present in 7.4.12, 7.5.1, 8.4.1, 9.5.1 and 10.0.1. Written up on
[Known Issues](../troubleshooting/known-issues.md#belowpart-tests-the-wrong-part-in-every-version-that-has-it).

### `torch: true` deletes the block by default

No torch generated, in any run, with no log line. The cause is a profile key rather
than the palette:

```
if (isTorch) {
    if (profile.GENERATE_LIGHTING) queue it for the attachment pass;
    else                           blockState = air;
}
```

`generateLighting` defaults to `false`, so a `torch` entry becomes **air** and the
`block` you wrote is discarded. The mod's own `common` palette marks `T` the same
way, which is why shipped buildings are unlit under a default profile.

When it is on, the pass places a vanilla `torch` or `wall_torch` and still ignores
your `block` value, so `torch: true` cannot produce a lantern or a modded light.
Written up on [Palette](../reference/palette.md#torch-is-off-by-default-and-off-means-air).

### The second build crashed, which no asset mistake had managed

Running pack 6's datapack against pack 5's profile, so the profile named a
`worldStyle` that was no longer loaded, produced a real crash report with
`Description: Feature placement`. Nothing in either earlier pack had done that,
including two profiles written deliberately to fail.

The catch in `LostCityFeature` covers the call to `LostCityTerrainFeature.generate`
and nothing else. `getDimensionInfo` runs before it, and resolving the profile's
world style is part of that. So:

| Mistake in | Result |
|---|---|
| Your assets: parts, palettes, buildings, city styles, selectors | Failed chunks and log lines. No crash. |
| The wiring between profile and datapack | **Crash**, with a crash report. |

The line number on `m_142674_` in the trace tells you which you have. 49 is the
unguarded setup, 62 is inside the catch. Written up on
[Error Messages](../troubleshooting/errors.md#thrown-during-chunk-generation).

The validator now rejects a profile whose `worldStyle` sits in the pack's own
namespace with no file behind it, and a profile whose file name is not lowercase
letters, which is the other way to get a profile the game will not offer you.

### The finding that came out of my own mistake

Those 3 broken buildings produced **77 failed chunks**, over a 13 by 10 chunk
area. They stand up to 6 chunks apart and the failures joined into one region.

A chunk asks its neighbours for their `BuildingInfo` in order to shape terrain at
its edges, lay railways and spread debris, and building that info is what
evaluates part conditions. So a building with an uncovered level fails **every
chunk that looks at it**, and those queries chain outward.

The circular-alias building, 6 chunks from the nearest of the three, failed
exactly one chunk: its own. That is the difference between a fault thrown while
building the chunk's info and one thrown while placing blocks. Both are now on
[Error Messages](../troubleshooting/errors.md#where-you-actually-see-these).

I had written on this page that a failure is scoped to the chunk that caused it.
That is true only for the second kind.

### What the validator says about this pack in advance

The rule that fired on the first build was "a building needs one part entry with
no conditions on it". That was a proxy, and it was wrong in both directions: it
rejected `andtest`, which generates perfectly, and it gave no clue why the other
three failed.

It now computes coverage instead, over the real level range, and reproduces all
four in-game outcomes before the game starts:

```
ERROR  rangetest.json: levels [6] match no part. Levels run from -0 to 6 INCLUSIVE,
       so 'maxfloors': 6 is a 7-storey building.
ERROR  prectest.json:  levels [3] match no part.
ERROR  belowtest.json: no unconditioned part reference, and coverage cannot be proven
       because ['belowpart'] depend on more than the level index
ERROR  test.json: char 'loot' on 'c': 'minecraft:chests/simple_dungeon' is a loot table
       ID, but 'loot' names a Condition
```

`andtest` passes. On the corrected pack only two errors remain, and both are
deliberate: the 128-slot cutoff, which is test 6, and `belowpart`, which no static
checker can resolve because the answer depends on what generated underneath.

## Recording a result

A test that runs and disagrees with the wiki is the most valuable outcome here, not
a failure of the exercise. Note which test, what you saw, and the mod version, then
open an issue. See [Contributing](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki#contributing).
