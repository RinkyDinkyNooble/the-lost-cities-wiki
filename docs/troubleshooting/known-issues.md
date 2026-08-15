---
status: in-progress
---

# Known Issues & Workarounds

Each entry is a behaviour traced to its cause in the 7.4.12 source, with a workaround that needs nothing but JSON. An absence from this page means the behaviour has not been traced, not that it is correct.

Two kinds of thing live here:

- **Genuine oddities** in how the mod behaves, where the fix is a workaround rather than a setting.
- **Things that look like bugs but are working as designed**, listed so that time is not spent trying to fix them.

Anything that produces an actual error message belongs on [Error Messages](errors.md) instead.

## Corner stairs generate with the wrong shape

**Status:** working as designed. Workaround available, no extra mods needed.

Whatever `shape=` you write in a palette's `block` string is **discarded**. Every block placed through a part goes through the same neighbour-aware correction pass vanilla uses when a player places a stair by hand, and the `shape` property is recalculated from whatever ends up adjacent. This is unconditional in the compiled code, and there is no JSON key anywhere that turns it off.

=== "Fix A: let the geometry do it (try this first)"

    The correction produces the right corner **on its own** when real neighbouring stairs back it up: same `half`, perpendicular `facing`, adjacent position. If your part places those neighbours correctly, you do not need `shape=` at all, and you should not write one, since it is overwritten regardless.

    Check this before reaching for Fix B. It is usually one fewer thing to hand-author, not more.

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

!!! note "Per-block variety is a code change, not a setting"
    The number of times the palette is sampled per chunk is fixed in the compiled method. The mod already has a `get(char, Random)` overload that would give per-block variation, and the railway code does not call it. Reaching that behaviour requires a Mixin or a patched jar.

## Four keys parse and then do nothing

**Status:** confirmed dead in 7.4.12, found by sweeping every asset accessor for consumers.

These keys load without complaint, survive inheritance, and never affect generation.

| Key | Where | How dead |
|---|---|---|
| `streetblocks.width` | City Style | Reaches the city style and the public API. No generator reads it. |
| `streetblocks.streetbase` | City Style | Reaches the city style and the public API. No generator reads it. |
| `streetblocks.streetvariant` | City Style | Reaches the city style and the public API. No generator reads it. |
| `rotatable` | Scattered Building | Does not even reach the asset. Parsed into the codec record and never copied into the object the generator uses, and no API method exposes it. |

All four look load-bearing because the mod's own content sets them. `citystyle_config` exists solely to set `width`, and `citystyle_common` and `citystyle_border` both set `streetbase` and `streetvariant`.

**Fix:** for street appearance, edit the palette characters the street part uses, or override `streetblocks.parts` with your own part. For scattered structures, author them in the orientation you want. See [City Style](../reference/citystyle.md) and [Scattered Building](../reference/scattered.md).

!!! note "How to reproduce"
    Check every accessor on every asset class for a caller outside its own class. Anything with no consumer is a candidate, and each candidate then has to be read by hand. That sweep also confirms the rest of the asset surface is live, so this table is the complete set for 7.4.12 rather than a sample.

    Two meta value types, `string` and `float`, are also accepted and never read, but those are storage slots rather than settings. See [Part](../reference/part.md#any-other-key).

## `belowpart` tests the wrong part, in every version that has it

**Status:** confirmed in game on 7.4.12, and by disassembly in 7.5.1, 8.4.1, 9.5.1 and 10.0.1.

`ConditionContext` receives the part below the current level and stores it in a
field named `belowPart`. **The class has no accessor for that field and nothing
ever reads it.** The predicate the mod compiles for `belowpart` calls `getPart()`,
which is the current part, and is byte for byte the same predicate `inpart`
compiles to.

`belowpart` is therefore a second name for `inpart`, not a test of what is
underneath.

| Version | State |
|---|---|
| 7.4.12, 7.5.1, 8.4.1, 9.5.1, 10.0.1 | Key exists, behaves as `inpart` |
| 8.2.2 | Key not declared. Writing it is a load error, not a silent no-op. |

There is a second problem underneath the first. A building's floor loop builds its
condition context **before** it has chosen a part, so it passes the literal
`<none>`. Both `inpart` and `belowpart` compare against that. Neither key can match
anything from a building's `parts` list even once `belowpart` is fixed.

**Fix:** select parts by height with `floor`, `range`, `ground` and `top`. A part
chain that depends on what generated below it is not expressible in 7.4.12. If
your building has entries gated on `belowpart`, those levels match nothing and
every chunk holding the building fails, which also takes out its neighbours. See
[Condition](../reference/condition.md#belowpart-and-inpart-in-a-building).

## Out-of-range profile numbers are accepted silently

**Status:** working as designed, and a real trap.

Every numeric profile key has a documented range, and **none of them are enforced when the profile is loaded from JSON**. Only the in-game config screen clamps. `"buildingMaxFloors": 9999` loads without a warning and is used exactly as written.

The same is true of every number in every asset file: there is no range validation anywhere in the mod.

**Fix:** treat the ranges on [Profile](../reference/profile.md) as rules you enforce yourself. [`validate.py`](../examples/index.md#validatepy) checks the ones this wiki documents.

## Edits to built-in profiles disappear on restart

**Status:** working as designed.

The mod rewrites every built-in profile file **on every launch**, not just the first. 7.4.12 ships 17 of them. Editing `wasteland.json` or `default.json` in place means losing that edit the next time the game starts.

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

## A shipped palette carries a 1.12 block id and cannot be built

`lostcities:bricks_desert_redsand` holds a `block` value from before the flattening:

```json
{ "char": "X", "block": "minecraft:red_sandstone@2", "damaged": "minecraft:iron_bars" }
```

A `block` value is split at the `[` that opens a blockstate and everything before it
goes to `ResourceLocation`, whose path accepts only `[a-z0-9/._-]`. `@` is not in
that set, so the value throws rather than being ignored.

**The throw happens while the palette is being built, not while the character is
being read.** So the file does not lose one character, it loses all of them:

| Char | Written as | Result |
|---|---|---|
| `X` | `minecraft:red_sandstone@2` | the entry at fault |
| `$` | `minecraft:red_sandstone_slab[type=double]` | valid, and unreachable anyway |
| `#` | a weighted list holding the same bad id | the entry at fault |

Nothing in 7.4.12 references this palette, so no shipped city style hits it. It only
matters if you point at it yourself, with `refpalette`, `frompalette` or a style, and
then every chunk that uses it fails.

**Workaround.** Copy the entries you want into your own palette and write the
modern id. `@2` on `red_sandstone` was the smooth variant, which is now
`minecraft:smooth_red_sandstone`, but confirm the block you actually want rather
than trusting the old number.

!!! note
    Read from 7.4.12. Reported by the DevTool's load-time asset check, which names
    the file, the line and the character.

## Changes do not show up after editing files

**Status:** working as designed.

`/reload` does not reload Lost Cities assets, and already-generated chunks never regenerate. There is no regenerate command. Read from 7.4.12.

See [Seeing your changes](../tooling/commands.md#seeing-your-changes) for the full table of what does and does not pick up an edit.

## What cannot be fixed from JSON

Three of the entries above are fixed in compiled code and no datapack or config reaches them.

| Issue | What it would take |
|---|---|
| Per-block rail variation | The palette method that would give it exists and the railway code does not call it, so a Mixin or a patched jar |
| `streetblocks.parts.full` never generating | The bound is off by one in a compiled method |
| `belowpart` testing the current part | The accessor it needs does not exist on `ConditionContext` |

The broken palette above is different: it is content, not compiled code, so it is
fixable in JSON by whoever ships it. Nothing references it, so nothing is broken
until someone points at it.

Every other entry has a workaround that needs nothing but JSON.

## See also

- [Error Messages](errors.md) for anything that produces an actual exception
- [Your First Custom City](../getting-started/first-city.md) if content is not loading at all
