# Claim tests

Everything on this wiki was traced from the mod's code. That is not the same as
having watched it run.

This page describes a datapack that exists to close that gap. Each asset in it
tests one claim the wiki makes, and each test is designed so that the result is
visible from the air with no commands and no guessing.

The pack is at `docs/examples/wiki-test/` in the repository.

!!! warning "Results are not filled in yet"
    This pack has been validated against the documented rules but has not been run
    in game. The **Expected** column below states what the wiki predicts. Nothing
    here is evidence until someone runs it and the results are recorded.

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
`cityChance` is `0.2`, so cities are common. Ruins and explosions are both off, so
the test buildings stay readable.

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

**Claim:** without `overrideFloors`, a building's `minfloors` and `maxfloors`
clamp the profile's range. With it, they replace the profile's range.

The profile allows 2 to 3 floors. Both test buildings ask for exactly 6.

| Building | Colour | `overrideFloors` | Expected |
|---|---|---|---|
| `clamped` | Purple | absent | 2 or 3 floors, because the profile wins |
| `overridden` | Orange | `true` | 6 floors, because the building wins |

**How to read it:** count floors. An orange tower noticeably taller than a purple
one confirms the claim. If both are the same height, the claim is wrong.

### 3. Street part names accept a list

**Claim:** a street part name may be a list, and the mod picks one uniformly at
random per chunk. No file the mod ships uses the list form, so this has never been
exercised.

The `full` street shape is set to 2 parts, one marked with a **gold** block square
and one with a **diamond** block square. Every other shape uses the shipped default.

**How to read it:** follow the roads. Full-street chunks should show both gold and
diamond markers, mixed with no pattern. Only one marker appearing across many
chunks means the list is not being sampled.

This also tests a second claim: `streetblocks.parts` is **all or nothing** on
inheritance. The pack lists all 7 shapes for that reason. If the other 6 shapes
generate normally, that claim holds too.

### 4. Palette features

**Claim A:** a weighted `blocks` list must fill 128 slots. The probe building's
floors and ceilings use a list of `100` white concrete and `28` black concrete,
totalling exactly 128.

**Claim B:** `frompalette` is a character alias, and the mod uses only the first
character of the string as the lookup. The probe building's walls use a character
aliased to red.

**How to read it:** find the building with speckled white and black decks. Its
walls should be **red**. Roughly 1 block in 5 of the deck should be black.

If the building fails to generate at all, look for
`Could not find entry 'A' in the palette for part 'wikitest:palette_probe'!`,
which would mean the alias did not resolve.

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
