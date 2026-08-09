# Palette Reference

!!! tip "TL;DR"
    `palettes/<name>.json`. Maps single characters to blocks. Each entry is `char` plus **exactly one** of `block`, `variant`, `blocks`, or `frompalette`.

## File shape

```json
{
  "palette": [
    { "char": "α", "block": "minecraft:stone_bricks" }
  ]
}
```

## Entry fields

| Key | Required | Meaning |
|---|---|---|
| `char` | **yes** | Single character. Must be unique within the merged palette set it's used in. See [What counts as a valid character](#what-counts-as-a-valid-character). |
| `block` | one of these four | A fixed block state string. |
| `variant` | | Name of a [Variant](variant.md), a shared weighted block list. |
| `blocks` | | Inline weighted list, same shape as a Variant but not reusable elsewhere. |
| `frompalette` | | Alias to another character's resolved value. See [Namespaces](../getting-started/namespaces.md#the-default-namespace-trap) for the same "bare name" gotcha applying here. |
| `damaged` | no | Block this maps to when ruined/damaged. Independent of the four above. |
| `mob` | no | **Not a literal mob ID.** Name of a [Condition](condition.md) entry. A real `mob_spawner` block is placed here, and the Condition's resolved value becomes the mob type it spawns. |
| `loot` | no | Loot table to use here. Rolled lazily, after the whole chunk finishes placing, and only if the block at that exact position is still unmodified at that point. If a later part (a floor above, a ruin pass) overwrites this position first, the loot roll is silently skipped. |
| `torch` | no | Boolean. A torch character never needs a `facing=` in its `block` string, this is why: torches are queued during placement and given a real attachment (checked against the four cardinal neighbors, then straight down, for the first solid block) in a separate pass after the whole chunk exists. |
| `tag` | no | Raw NBT compound. This is the mechanism behind command-block palette tricks. |

!!! note "frompalette is an alias, not inheritance"
    It copies the *entire* resolved value (one block, or a whole weighted list) from another character, wholesale. There's no partial override, you can't inherit the block but change the loot. Only the first character of the string is used as the lookup, and it resolves once when palettes are merged, not per-placement. `tag`/`mob`/`loot`/`torch`/`damaged` on a `frompalette` entry are still independent, they don't come from the aliased character.

### How aliases resolve, and where it bites

Aliases are resolved after every concrete entry is in place, by repeatedly sweeping the palette set until nothing new can be resolved. Three consequences:

**Chains work, in any order.** `A` aliasing `B` aliasing a real block resolves fine, and it doesn't matter which palette in the merge each link lives in, or what order they're listed.

**An alias follows overrides.** It resolves against the **final merged** value of the target character, not the value it had in the file where the alias was written. If a later palette redefines the target, the alias silently picks up the new block. Usually what you want, occasionally a surprise.

**A concrete definition beats an alias, regardless of order.** This one inverts the normal rule. Everywhere else in palette merging, later wins. But if character `X` is concretely defined in *any* palette in the set, an `X` alias in a *later* palette is skipped entirely. You cannot override a real block with a `frompalette` alias.

!!! warning "Circular references don't hang, they leave the characters undefined"
    `A` → `B` → `A`, or `A` → `A`, is not an infinite loop and not a stack overflow. The resolver only makes progress when it can attach a character to a value that already exists, so a cycle simply never resolves and the sweep stops.

    The characters are then **missing from the compiled palette**, which surfaces later as a generation crash the first time a part uses one:

    ```
    Could not find entry 'A' in the palette for part 'mypack:my_part'!
    ```

    Nothing is logged at load time, so the message points at the part rather than at the palette that's actually broken. If you get that error on a character you're certain you defined, check whether it's an alias in a cycle.

## What counts as a valid character

Short answer: **almost any character you can type, as long as it's a single UTF-16 code unit (U+0000 to U+FFFF).** Files are read as UTF-8, so Greek, Cyrillic, CJK, box-drawing, arrows, and accented Latin all work, and you can paste them into the JSON literally rather than escaping them.

`char` is declared as a JSON *string*, not a character, and the mod keeps only its **first UTF-16 code unit**. Nothing validates the rest:

| You write | What actually gets registered |
|---|---|
| `"α"` | `α`. Normal case. |
| `"ab"` | `a`. The `b` is silently discarded, no warning. |
| `"字"` | `字`. Any Basic Multilingual Plane character is fine. |
| `""` | Crash at datapack load (string index out of range). |
| `"😀"` | **Not the emoji.** See below. |

Every "character" field in every Lost Cities file behaves this way, not just palettes: `filler`, `rubble`, and the city style block characters all take the first code unit of a string.

!!! danger "Emoji and other characters above U+FFFF are broken, in two separate ways"
    Java strings are UTF-16, so anything above U+FFFF (emoji, most rare CJK, musical symbols) is stored as a **surrogate pair**: two code units for one character.

    1. **In a palette**, only the first half is kept. Every emoji in the same 1024-code-point range collapses onto the *same* key, so 🚗 and 🚙 would overwrite each other.
    2. **In a part's `slices`**, that character occupies **two** positions instead of one, shifting every block after it in that layer by one column.

    The second one is the dangerous one for anyone generating parts with a script. Python and JavaScript count an emoji as length 1, so your generator writes what it thinks is a 16-character row while the mod reads 17 code units. The output looks correct in the file and comes out diagonally smeared in-game.

    **Stay inside U+0000 to U+FFFF and this can't happen.**

### Which characters to actually pick

The mod's own `/lc exportpart` command assigns characters to new blocks from a fixed pool, exhausting each tier before moving to the next. It's a reasonable list to copy:

| Tier | Range | Count |
|---|---|---|
| 1 | Printable ASCII, except space, `"` and `\` (listed below) | 92 |
| 2 | U+0370 to U+03FF, Greek and Coptic (`α β γ Δ Ω`) | 144 |
| 3 | U+0400 to U+04FF, Cyrillic (`а б в Я Ж`) | 256 |

```text title="Tier 1, in the exact order the exporter tries them"
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:'<>,.?/`~
```

492 characters total, far more than any part will need. The two ASCII omissions are deliberate: `"` and `\` both need escaping inside a JSON string, which is an easy way to break a hand-written generator. Space is omitted because it already means air.

!!! tip "Prefer non-ASCII for your own entries"
    Your palette gets merged with the mod's, and a collision silently replaces the other entry rather than erroring. A merged palette for the standard style already claims **56 characters**, mostly ASCII. Starting your custom entries in the Greek or Cyrillic range keeps you clear of anything the mod adds later.

### Collisions and merge order

`char` only has to be unique within the **merged** palette a part actually sees, which is built in this order, each step overwriting the one before it:

1. The [Style](style.md)'s palettes, merged in the order the `randompalettes` groups are listed
2. The [Building](building.md)'s own `palette`, if it has one
3. The [Part](part.md)'s `palette` or `refpalette`, if it has one

So a part-local palette always wins, and a later `randompalettes` group beats an earlier one. There is no warning on collision, the newer entry just replaces the older one.

An undefined character is not silently ignored. It throws during chunk generation:

```
Could not find entry 'ß' in the palette for part 'mypack:my_part'!
```

!!! note "Space is not hardcoded to air"
    `" "` maps to `minecraft:air` because the shipped `common` palette says so, and every shipped style lists `common` first. It is not a rule in the code.

    There is one genuine special case: a column that is **entirely** spaces from top to bottom is skipped without ever being looked up. So a part full of spaces won't crash even with no space entry, but a wall with a doorway in it will. If you write a style from scratch, include `common` or define `" "` yourself.

## The 128-slot rule for `blocks` and `variant`

Weighted lists (`blocks` here, or inside a [Variant](variant.md)) fill a **fixed 128-slot array**, in list order.

- Total weight **under 128** → hard crash at palette load (`"Not enough blocks in the random list"`).
- Total weight **over 128** → the entry that fills the last slot gets cut short, and **every entry listed after it gets nothing at all**. Order matters, not just the sum.
- Total weight **exactly 128** → everyone gets their exact stated share.

!!! example "Real example from the mod's own shipped content"
    ```json title="variants/stonebrick.json"
    {
      "blocks": [
        { "random": 9, "block": "minecraft:cracked_stone_bricks" },
        { "random": 8, "block": "minecraft:mossy_stone_bricks" },
        { "random": 1000, "block": "minecraft:stone_bricks" }
      ]
    }
    ```
    Total is 1017, not 128. In practice: 9/128 cracked, 8/128 mossy, and the remaining 111/128 slots go to stone bricks (the `1000` gets clipped down to whatever's left). This is the mod author's own idiom: give rare options small honest numbers, then a big catch-all number **last** to soak up the remainder. Put that catch-all anywhere but last, and everything after it becomes unreachable.

## Stairs, fences, and walls auto-correct on placement

Every block placed through a part goes through a neighbor-aware correction pass before it lands, the same logic vanilla Minecraft uses when a player places these blocks by hand:

- **Stairs** (`minecraft:*_stairs`): the `shape` property is always recalculated from whatever ends up next to it (matching stairs on the facing side or its opposite produce an outer/inner corner, anything else is `straight`). **Whatever `shape=` you write in a `block` string is discarded and replaced.** This isn't occasional, it happens on every stair placement. If a corner comes out wrong, it's because the recalculated shape doesn't match what the surrounding part geometry produces, not because the palette entry was ignored.
- **Fences, walls, and similar connecting blocks**: connections to neighbors are recalculated the same way, this is expected and rarely surprising.
- **Structure void blocks**: silently placed as nothing.

!!! warning "Forcing an exact stair shape"
    If you need a specific corner shape the auto-correction won't produce, the only reliable workaround is placing it *after* generation finishes, since the correction pass only runs during the terrain-generation call itself. The [Command Blocks](../advanced/command-blocks.md) page shows the pattern: a palette entry that places an auto-firing command block whose command forces the exact block state, bypassing the normal palette-to-block path entirely.

## Rotation and the `lostcities:rotatable` tag

Parts get placed rotated or mirrored, not just as authored. Buildings reuse the same part on multiple sides, and streets/highways/rails reuse the same handful of shapes ([straight, bend, T, and so on](../concepts/infrastructure-parts.md)) in whatever orientation the intersection actually needs. When that happens, a block only rotates along with the part if it's in the `lostcities:rotatable` block tag, or is a rail block (`RailShape` is remapped separately, always).

**Anything not in that tag keeps its original facing when the part is rotated.** By default, `lostcities:rotatable` contains exactly one thing: the vanilla `minecraft:stairs` tag (every vanilla stair block). A door, a furnace, a ladder, a banner, or a modded directional block placed in a palette will look correctly oriented on the side of the building the part was authored for, and wrong on any other side or rotation the same part gets reused on.

!!! tip "Fixing it"
    Add the block to `lostcities:rotatable` yourself with a normal datapack tag merge, no code or Lost Cities file needed:
    ```json title="data/<namespace>/tags/blocks/rotatable.json"
    {
      "values": ["minecraft:ladder", "minecraft:furnace"]
    }
    ```
    This merges into the existing tag rather than replacing it (same merge behavior as any vanilla block tag).

## Block tags Lost Cities checks

Besides `rotatable`, five more tags under the `lostcities` namespace affect how palette blocks behave. All are ordinary datapack tags, extendable the same way as above.

| Tag | Default contents | Affects |
|---|---|---|
| `lostcities:notbreakable` | Bedrock, end portal, end portal frame, end gateway | Explosion/ruin damage always skips these, regardless of `explosionMaxRadius` or ruin settings |
| `lostcities:easybreakable` | `forge:glass` (all glass) | Breaks more readily under explosion/ruin damage than an untagged block |
| `lostcities:needspoi` | Villager job-site blocks (barrel, smoker, blast furnace, loom, lectern, and similar) | Marks blocks that need proper point-of-interest registration when placed during generation, so villager AI linkage doesn't silently break |
| `lostcities:foliage` | Coral, bamboo, logs, leaves, saplings, flowers | Foliage-specific placement/decay handling |
| `lostcities:lights` | Every block with a light-emission value above 0 | Used wherever the generator needs to know "is this a light source" without a hardcoded list |

## See also

- [Error Messages](../troubleshooting/errors.md) for the palette errors above, with causes
- [Variant Reference](variant.md)
- [Style Reference](style.md) for how multiple palettes combine
- [Condition Reference](condition.md) for what a `mob` field's value actually points at
- [Streets, Highways, Rails & Monorails](../concepts/infrastructure-parts.md) for where part rotation comes from
- [Namespaces](../getting-started/namespaces.md)
