# Claim tests

Everything on this wiki was traced from the mod's code. That is not the same as
having watched it run.

This page describes a datapack that exists to close that gap. Each asset in it
tests one claim the wiki makes, and each test is designed so that the result is
visible from the air with no commands and no guessing.

The pack is at `docs/examples/wiki-test/` in the repository.

## Results so far

Run on 7.4.12, Minecraft 1.20.1, Forge.

| Test | Result |
|---|---|
| Multi-building grid order | **Confirmed.** Red north-west, yellow south-west, blue north-east, green south-east. The outer list is X, exactly as documented. |
| Weighted list reaching 128 slots | **Confirmed.** Speckled black and white decks generated. |
| A concrete definition beats an alias | **Confirmed, by accident.** The probe's walls came out as the style's stone stairs, not the aliased red. `A` is concretely defined in the style's palette, and [that rule](../reference/palette.md#how-aliases-resolve) says a concrete definition wins over an alias wherever it appears. The test picked a character already in use, so it proved the override rule instead of the alias. |
| `overrideFloors` | **Test invalid, and it exposed a wiki error.** Both buildings generated at the same height. The cause is that `minfloors` is a `max()` applied after the maximum, so both reached 6 floors with or without the key. The page said a building "can only make itself shorter than the profile allows, never taller", which is false. [Corrected](../reference/building.md#how-floor-and-cellar-counts-are-decided). |
| Street part name as a list | **Blocked by a mod bug, now documented.** Two builds produced no marked street anywhere. The cause is that the marked pair sat on the `full` shape, and `StreetType.FULL` is never assigned: the mod picks the type with `nextInt(0, values().length - 2)`, which on 3 constants can only return `NORMAL`. So `streetblocks.parts.full` is a fourth dead key. See [Streets](../concepts/infrastructure-parts.md#streets). The list form itself is still untested and moves to every reachable shape in build 4. |

Two of the five tests were badly designed. Both design faults are fixed in the next
build, and one of them found a real documentation error on the way.

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

## Recording a result

A test that runs and disagrees with the wiki is the most valuable outcome here, not
a failure of the exercise. Note which test, what you saw, and the mod version, then
open an issue. See [Contributing](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki#contributing).
