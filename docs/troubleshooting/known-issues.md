---
status: in-progress
---

# Known Issues & Workarounds

!!! info "This page grows as issues are traced"
    Each entry below is a behaviour traced to its cause in the 7.4.12 source, with a workaround that works today. More will be added as they are confirmed. If something looks like a bug but is not listed, it may not be traced yet.

Two kinds of thing live here:

- **Genuine oddities** in how the mod behaves, where the fix is a workaround rather than a setting.
- **Things that look like bugs but are working as designed**, which are worth knowing so you stop trying to fix them.

Anything that produces an actual error message belongs on [Error Messages](errors.md) instead.

## Corner stairs generate with the wrong shape

**Status:** working as designed. Workaround available, no extra mods needed.

Whatever `shape=` you write in a palette's `block` string is **discarded**. Every block placed through a part goes through the same neighbour-aware correction pass vanilla uses when a player places a stair by hand, and the `shape` property is recalculated from whatever ends up adjacent. This is unconditional in the compiled code, and there is no JSON key anywhere that turns it off.

=== "Fix A: let the geometry do it (try this first)"

    The correction produces the right corner **on its own** when real neighbouring stairs back it up: same `half`, perpendicular `facing`, adjacent position. If your part places those neighbours correctly, you do not need `shape=` at all, and you should not write one, since it is overwritten regardless.

    Worth checking before reaching for Fix B. It is usually one fewer thing to hand-author, not more.

=== "Fix B: a self-replacing command block"

    For a corner the surrounding geometry genuinely cannot produce (a decorative or impossible shape), place it *after* generation. The correction pass only runs during the generation call itself, so a command block that fires once and overwrites itself lands the exact state you asked for.

    ```json title="Palette entry"
    {
      "char": "ω",
      "block": "minecraft:command_block[conditional=false,facing=west]",
      "tag": {
        "Command": "setblock ~ ~ ~ minecraft:smooth_quartz_stairs[facing=east,half=bottom,shape=outer_left] replace",
        "auto": 1,
        "conditionMet": 1
      }
    }
    ```

    Pure vanilla, no KubeJS, no companion mod. The command block replaces itself, so nothing is left behind. Full pattern and its costs at [Command Blocks](../advanced/command-blocks.md).

## Railways come out in flat 16-block colour strips

**Status:** working as designed. Fully fixable if you will accept a uniform block.

`railmain` is resolved to a single block **once per chunk** and reused for that chunk's entire rail bed. It is not re-rolled per block. So a weighted `railmain` produces solid chunk-length strips of one material rather than block-by-block noise, and the shipped city style points `railmain` at the `stonebrick` variant, which is mostly plain stone bricks with occasional cracked or mossy. The result is long stretches of identical rail with an occasional whole chunk that stands out.

**Fix:** point `railmain` at a fixed `block` instead of a `variant` or `blocks` list.

```json title="Your city style"
{ "railblocks": { "railmain": "y" } }
```
```json title="Your palette, character y"
{ "char": "y", "block": "minecraft:stone_bricks" }
```

Nothing to randomize means nothing to stripe. One palette edit, pure JSON.

!!! note "Wanting per-block variety instead is a code change"
    The number of times the palette is sampled per chunk is fixed in the compiled method. The mod already has a `get(char, Random)` overload that would give per-block variation, the railway code just does not call it. Getting that behaviour means a Mixin or a patched jar, not configuration.

    This is one of the cases a companion mod would genuinely solve. See [below](#a-companion-mod-is-planned).

## Four keys parse and then do nothing

**Status:** confirmed dead in 7.4.12, found by sweeping every asset accessor for consumers.

These keys load without complaint, survive inheritance, and never affect generation.

| Key | Where | How dead |
|---|---|---|
| `streetblocks.width` | City Style | Reaches the city style and the public API. No generator reads it. |
| `streetblocks.streetbase` | City Style | The same. |
| `streetblocks.streetvariant` | City Style | The same. |
| `rotatable` | Scattered Building | Worse. Parsed into the codec record and never copied into the asset the generator uses. No API method exposes it either. |

All four look load-bearing because the mod's own content sets them. `citystyle_config` exists solely to set `width`, and `citystyle_common` and `citystyle_border` both set `streetbase` and `streetvariant`.

**Fix:** for street appearance, edit the palette characters the street part uses, or override `streetblocks.parts` with your own part. For scattered structures, author them in the orientation you want. See [City Style](../reference/citystyle.md) and [Scattered Building](../reference/scattered.md).

!!! note "How these were found"
    Every accessor on every asset class was checked for a caller outside its own class. Anything with no consumer is a candidate, and each candidate was then read by hand. The same sweep confirmed the rest of the asset surface is live, so this table is expected to be the complete set for 7.4.12 rather than a sample.

    Two meta value types, `string` and `float`, are also accepted and never read, but those are storage slots rather than settings. See [Part](../reference/part.md#any-other-key).

## Out-of-range profile numbers are accepted silently

**Status:** working as designed, and a real trap.

Every numeric profile key has a documented range, and **none of them are enforced when the profile is loaded from JSON**. Only the in-game config screen clamps. `"buildingMaxFloors": 9999` loads without a warning and is used exactly as written.

The same is true of every number in every asset file: there is no range validation anywhere in the mod.

**Fix:** treat the ranges on [Profile](../reference/profile.md) as rules you enforce yourself. [`validate.py`](../examples/index.md#validatepy) checks the ones this wiki documents.

## Edits to built-in profiles disappear on restart

**Status:** working as designed.

The mod rewrites all 17 built-in profile files **on every launch**, not just the first. Editing `wasteland.json` or `default.json` in place means losing that edit the next time the game starts.

**Fix:** always use a file name the mod does not ship, like `mycity.json`. Files it does not recognise are read and left alone. `/lostcities saveprofile <name>` is the intended way to get a starting point.

## Buildings inherited from `citystyle_common` keep showing up

**Status:** working as designed, and almost always a surprise.

City style `inherit` is **additive** for all eight selector lists. Your buildings are appended to the parent's, they do not replace them. A name that appears in both is in the pool twice, at the sum of both weights.

There is no way to remove or narrow an inherited list.

| What you want | What to do |
|---|---|
| Mostly your buildings | Inherit, and give yours a much larger `factor` |
| **Only** your buildings | Do not inherit from a style that has any. Declare everything yourself, including all the block characters |

See [Inheritance](../reference/citystyle.md#inheritance).

## Changes do not show up after editing files

**Status:** working as designed.

`/reload` does not reload Lost Cities assets, and already-generated chunks never regenerate. There is no regenerate command.

See [Seeing your changes](../tooling/commands.md#seeing-your-changes) for the full table of what does and does not pick up an edit.

## A companion mod is planned

Some of the above cannot be fixed from JSON at all, because the behaviour is fixed in compiled code. A small companion Forge mod is planned to address that class of problem.

**What it could reasonably fix**, based on what has been traced so far:

| Issue | Why a mod can fix it |
|---|---|
| Per-block rail variation | The needed palette method already exists, the railway code just does not call it |
| Validation at load time | Nothing currently checks ranges, row lengths, or floor coverage. A mod could fail loudly at load instead of mid-generation |
| Better error messages | Several errors name the wrong file. A mod could report the palette rather than the part |

The mod's own API is unusually good for this. It posts `LostCityEvent.CharacteristicsEvent` **before** it caches the result, and every key on the characteristics object is a public mutable one. A companion mod can therefore change, per chunk and from outside: whether the chunk is a city at all, whether it could hold a building, the city level, the city style, the building type, and the multi-building. That is enough to redirect most placement decisions without touching the mod's own code.

!!! info "Not written yet"
    This section is a statement of intent, not a release. It will be replaced with real documentation once the mod exists. Nothing on this page depends on it, every workaround above works today with vanilla Lost Cities.

## See also

- [Error Messages](errors.md) for anything that produces an actual exception
- [Your First Custom City](../getting-started/first-city.md) if content is not loading at all
