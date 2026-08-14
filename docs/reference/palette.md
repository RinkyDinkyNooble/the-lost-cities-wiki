# Palette Reference

!!! tip "TL;DR"
    `palettes/<name>.json` maps single characters to blocks. Each entry is a `char` plus **exactly one** of `block`, `variant`, `blocks` or `frompalette`.

!!! note "`tag` is absent in 6.0.3"
    Every other key on this page exists in every datapack-era version. See
    [Key availability](../versions/key-availability.md).

## File shape

```json
{
  "palette": [
    { "char": "α", "block": "minecraft:stone_bricks" }
  ]
}
```

## Entry keys

| Key | Required | Meaning |
|---|---|---|
| `char` | **yes** | One character. It must be unique within the merged palette set that uses it. See [What counts as a valid character](#what-counts-as-a-valid-character). |
| `block` | one of these four | A fixed block state string. |
| `variant` | | The name of a [Variant](variant.md), which is a shared weighted block list. |
| `blocks` | | An inline weighted list. Same shape as a Variant, but not reusable elsewhere. |
| `frompalette` | | An alias to another character's resolved value. The same bare-name trap applies here, see [Namespaces](../getting-started/namespaces.md#the-default-namespace-trap). |
| `damaged` | no | The block this character becomes when the building is ruined. Independent of the four keys above. |
| `mob` | no | **Not a literal mob ID.** The name of a [Condition](condition.md). The mod places a real `mob_spawner` block, and the condition's resolved value becomes the mob it spawns. |
| `loot` | no | **Not a loot table ID.** The name of a [Condition](condition.md), exactly like `mob`. The condition's resolved value is the loot table. See [below](#loot-names-a-condition-not-a-loot-table). |
| `torch` | no | Boolean. **Gated on the profile's `generateLighting`, which is `false` by default, and when it is off the character becomes air.** See [below](#torch-is-off-by-default-and-off-means-air). |
| `tag` | no | A raw NBT compound. This is the mechanism behind the command-block palette technique. |

!!! note "`frompalette` is an alias, not inheritance"
    An alias copies the **entire** resolved value from another character, either one block or a whole weighted list. There is no partial override, so you cannot inherit the block and change the loot.

    The mod uses only the first character of the string as the lookup, and resolves it once when it merges palettes, not per placement. A `tag`, `mob`, `loot`, `torch` or `damaged` key on a `frompalette` entry stays independent. Those do not come from the aliased character.

### How aliases resolve

The mod resolves aliases after every concrete entry is in place. It sweeps the palette set repeatedly until nothing new resolves. That has three consequences.

**Chains work, in any order.** `A` aliasing `B` aliasing a real block resolves correctly. It does not matter which palette in the merge holds each link, or what order they appear in.

**An alias follows overrides.** It resolves against the **final merged** value of the target character, not the value the target had in the file where you wrote the alias. If a later palette redefines the target, the alias silently picks up the new block. That is usually what you want, and occasionally a surprise.

**A concrete definition beats an alias, whatever the order.** This inverts the normal rule. Everywhere else in palette merging, later wins. Here, if character `X` is concretely defined in **any** palette in the set, an `X` alias in a later palette is skipped. You cannot override a real block with an alias.

!!! warning "A circular reference leaves the characters undefined, and reports nothing at load"
    `A` to `B` to `A`, or `A` to `A`, does not hang and does not overflow the stack. The resolver only makes progress when it can attach a character to a value that already exists, so a cycle never resolves and the sweep stops.

    Those characters are then **missing from the compiled palette**. The mod reports nothing at load time. The problem surfaces later, the first time a part uses one:

    ```
    Could not find entry 'A' in the palette for part 'mypack:my_part'!
    ```

    The message names the part rather than the palette that is actually broken. If you get it for a character you are certain you defined, check whether that character is an alias in a cycle.

## `torch` is off by default, and off means air

`torch: true` does not describe the block. It hands the character to a separate
pass, and the [Profile](profile.md)'s `generateLighting` decides whether that pass
runs at all.

| `generateLighting` | What the character becomes |
|---|---|
| `false`, **the default** | **`minecraft:air`.** The `block` you wrote is discarded and nothing is placed. |
| `true` | The position is queued, and after the chunk exists the mod places a real vanilla torch there. |

So a character that looks like a torch, in a palette that looks correct, generates
**nothing at all** in a profile that has not turned lighting on. This is not a
mistake in your pack. The mod's own `common` palette defines `T` as a torch the
same way, which is why the shipped buildings are unlit under a default profile.

```json title="the profile key that makes torch entries exist"
{ "lostcity": { "generateLighting": true } }
```

!!! warning "The attachment pass ignores your `block` value"
    When it does run, the pass places `minecraft:torch` or `minecraft:wall_torch`
    and nothing else. It looks straight down first, then at the cardinal
    neighbours, and picks whichever the first solid block supports.

    That means `torch: true` cannot give you a lantern, a soul torch, or a modded
    light. Those need a plain `block` entry with no `torch` key, and then you keep
    whatever `facing=` you wrote, with no attachment checking.

    Confirmed in game on 7.4.12: with `generateLighting` at its default, a part
    placing two torch characters produced no torch anywhere, and no log line.

## `loot` names a Condition, not a loot table

This is the single easiest key on the page to get wrong, because the obvious thing
to write looks right and fails hard.

```json
{ "char": "C", "block": "minecraft:chest", "loot": "chestloot" }
```

`chestloot` is a [Condition](condition.md). The mod looks the name up in its own
Condition registry, resolves it against the position being generated, and uses the
**resolved value** as the loot table. That is what the mod's own shipped palette
does, and `conditions/chestloot.json` is why a chest deep in a cellar holds
different loot from one on an upper floor:

```json title="the mod's own conditions/chestloot.json, abridged"
{
  "values": [
    { "factor": 8,  "value": "lostcities:chests/lostcitychest", "range": "4,100" },
    { "factor": 8,  "value": "lostcities:chests/lostcitychest", "range": "-100,-3" },
    { "factor": 20, "value": "lostcities:chests/raildungeonchest" }
  ]
}
```

!!! danger "Writing a loot table ID directly fails the chunk"
    `"loot": "minecraft:chests/simple_dungeon"` is not a slightly wrong value that
    yields an empty chest. There is no Condition by that name, so the mod throws:

    ```
    Error getting resource minecraft:chests/simple_dungeon!
    ```

    The throw happens in the **post-generation pass**, after the blocks are placed,
    so the visible result is a chunk whose chests exist and can be opened but are
    empty and render invisible, because their block entities were never finished.
    Confirmed in game on 7.4.12.

    To use a vanilla loot table, wrap it in a one-line Condition and name that:
    ```json title="conditions/mychestloot.json"
    { "values": [ { "factor": 1.0, "value": "minecraft:chests/simple_dungeon" } ] }
    ```

The mod rolls the loot lazily, after the whole chunk finishes placing, and only if
the block at that position is still unmodified. If a later part overwrites the
position first, the mod skips the roll silently.

## Why a chest generates empty

A `loot` key that looks correct and still produces an empty chest is normal, and there are five separate reasons. They are independent, so ruling one out does not rule out the rest.

| Cause | Where it is decided |
|---|---|
| `generateLoot` is `false` in the profile. Every chest generates empty. | Profile |
| `buildingWithoutLootChance`, default `0.2`. One building in five is chosen to get neither loot nor spawners, before any chest is considered. | Profile, applied per building |
| `chestWithoutLootChance`, default `0.2`. Of the chests that survive the above, one in five is still left empty. | Profile, applied per chest |
| The mod rolls loot **after** the whole chunk finishes placing, and skips the roll if anything overwrote that position first. A floor above, or the ruin pass, can take the chest away. | Generation order |
| The Condition named by `loot` resolves to a loot table that does not exist. The Condition itself resolved, so nothing throws. | Your JSON |

With both chances at their defaults, a chest in a randomly chosen building has roughly a **64%** chance of being filled, that is 0.8 multiplied by 0.8. Two empty chests in a row is not evidence of a broken palette.

!!! note "An empty chest that is also invisible is a different fault"
    A chest with no block entity renders as nothing at all, because a chest is drawn
    by its block entity rather than by a block model. You can still walk into the
    space and open it. That combination means generation threw before the chunk
    finished, not that the loot roll came up empty. Check the log.

!!! tip "Testing whether it is your JSON or the dice"
    Set `generateLoot: true`, `buildingWithoutLootChance: 0` and `chestWithoutLootChance: 0` in a test profile. Every eligible chest then fills. If yours is still empty after that, the fault is the loot table name or the overwrite case, not the chances.

## What counts as a valid character

Almost any character you can type is valid, provided it is a single UTF-16 code unit, that is U+0000 to U+FFFF. The mod reads files as UTF-8, so Greek, Cyrillic, CJK, box-drawing, arrows and accented Latin all work. You can paste them into the JSON directly instead of escaping them.

`char` is declared as a JSON string, not as a character, and the mod keeps only its **first UTF-16 code unit**. Nothing validates the rest.

| You write | What the mod registers |
|---|---|
| `"α"` | `α`. The normal case. |
| `"ab"` | `a`. The mod discards the `b` silently. |
| `"字"` | `字`. Any Basic Multilingual Plane character works. |
| `""` | A crash at datapack load, from a string index out of range. |
| `"😀"` | Not the emoji. See below. |

Every character key in every Lost Cities file behaves this way, not only in palettes. `filler`, `rubble` and the city style block characters all take the first code unit of a string.

!!! danger "An emoji fails in two separate ways, and one of them is silent"
    Java strings are UTF-16, so any character above U+FFFF, such as an emoji, most rare CJK, or a musical symbol, is stored as a **surrogate pair**: two code units for one character.

    1. **In a palette**, the mod keeps only the first half. Every emoji in the same range of 1024 code points collapses onto the **same** key, so 🚗 and 🚙 overwrite each other.
    2. **In a part's `slices`**, that character occupies **two** positions instead of one. It shifts every block after it in that layer by one column.

    The second failure is the dangerous one if you generate parts with a script. Python and JavaScript both count an emoji as length 1, so your generator writes what it believes is a 16-character row while the mod reads 17 code units. The file looks correct and the building comes out smeared diagonally.

    **Stay inside U+0000 to U+FFFF and neither failure can happen.**

### Which characters to pick

The mod's own `/lc exportpart` command assigns characters to new blocks from a fixed pool. It exhausts each tier before it moves to the next. The list is worth copying.

| Tier | Range | Count |
|---|---|---|
| 1 | Printable ASCII, except space, `"` and `\` | 92 |
| 2 | U+0370 to U+03FF, Greek and Coptic (`α β γ Δ Ω`) | 144 |
| 3 | U+0400 to U+04FF, Cyrillic (`а б в Я Ж`) | 256 |

```text title="Tier 1, in the exact order the exporter tries them"
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:'<>,.?/`~
```

That is 492 characters in total, far more than any part needs. The two ASCII omissions are deliberate. Both `"` and `\` need escaping inside a JSON string, which is an easy way to break a hand-written generator. Space is omitted because it already means air.

!!! tip "Prefer non-ASCII for your own entries"
    The mod merges your palette with its own, and a collision replaces the other entry silently rather than reporting an error. The merged palette for the standard style already claims **56 characters**, mostly ASCII. Starting your own entries in the Greek or Cyrillic range keeps you clear of anything the mod adds in a later version.

### Collisions and merge order

A `char` only has to be unique within the **merged** palette that a part actually sees. The mod builds that palette in this order, and each step overwrites the one before it:

1. The [Style](style.md)'s palettes, merged in the order the `randompalettes` groups are listed
2. The [Building](building.md)'s own `palette`, if it has one
3. The [Part](part.md)'s `palette` or `refpalette`, if it has one

So a part-local palette always wins, and a later `randompalettes` group beats an earlier one. The mod gives no warning on a collision. The newer entry replaces the older one.

An undefined character is not ignored. The mod throws during chunk generation:

```
Could not find entry 'ß' in the palette for part 'mypack:my_part'!
```

!!! note "Space is not hardcoded to air"
    `" "` maps to `minecraft:air` because the shipped `common` palette defines it that way, and every shipped style lists `common` first. It is not a rule in the code.

    There is one genuine special case. The mod skips a column that is **entirely** spaces from top to bottom without ever looking it up. So a part made only of spaces does not crash even with no space entry, but a wall with a doorway in it does. If you write a style from scratch, either include `common` or define `" "` yourself.

## The 128-slot rule for `blocks` and `variant`

A weighted list, whether `blocks` here or inside a [Variant](variant.md), fills a **fixed array of 128 slots**, in list order.

| Total weight | Result |
|---|---|
| Under 128 | The mod throws at palette load: `Not enough blocks in the random list`. |
| Exactly 128 | Every entry gets its exact stated share. |
| Over 128 | The entry that fills the last slot is cut short, and **every entry listed after it gets nothing**. Order matters, not only the sum. |

!!! example "A real example from the mod's own shipped content"
    ```json title="variants/stonebrick.json"
    {
      "blocks": [
        { "random": 9, "block": "minecraft:cracked_stone_bricks" },
        { "random": 8, "block": "minecraft:mossy_stone_bricks" },
        { "random": 1000, "block": "minecraft:stone_bricks" }
      ]
    }
    ```
    The total is 1017, not 128. In practice you get 9 slots of cracked, 8 of mossy, and the remaining 111 of plain stone bricks, because the `1000` is clipped to whatever is left.

    This is the mod author's own idiom: give the rare options small honest numbers, then put a large catch-all number **last** to fill the remainder. Put that catch-all anywhere but last and everything after it becomes unreachable.

## Stairs, fences and walls correct themselves on placement

Every block placed through a part goes through a neighbour-aware correction pass before it lands. It is the same logic Minecraft uses when a player places these blocks by hand.

- **Stairs** (`minecraft:*_stairs`): the mod always recalculates the `shape` property from whatever ends up next to the block. Matching stairs on the facing side or its opposite produce an outer or inner corner, and anything else produces `straight`. **The mod discards whatever `shape=` you write in a `block` string and replaces it.** This happens on every stair placement, not occasionally. If a corner comes out wrong, the recalculated shape does not match what the surrounding geometry produces. The palette entry was not ignored.
- **Fences, walls and similar connecting blocks**: the mod recalculates connections to neighbours the same way. This is expected and rarely surprising.
- **Structure void blocks**: the mod places nothing, silently.

!!! warning "Forcing an exact stair shape needs a workaround"
    The correction pass runs only during the terrain-generation call itself. So if you need a specific corner shape that the correction will not produce, the only reliable method is to place it after generation finishes.

    The [Command Blocks](../advanced/command-blocks.md) page shows the pattern: a palette entry places an auto-firing command block whose command forces the exact block state, which bypasses the palette-to-block path entirely.

## Rotation and the `lostcities:rotatable` tag

The mod places parts rotated and mirrored, not only as you authored them. A building reuses the same part on several sides, and streets, highways and rails reuse the same few shapes in whatever orientation the intersection needs. See [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md).

When the mod rotates a part, a block rotates with it only if that block is in the `lostcities:rotatable` block tag, or is a rail block. Rail shapes are remapped separately, and always.

**A block that is not in that tag keeps its original facing when the part rotates.** By default `lostcities:rotatable` contains exactly one entry: the vanilla `minecraft:stairs` tag, which covers every vanilla stair block. So a door, a furnace, a ladder, a banner or a modded directional block looks correct on the side the part was authored for, and wrong on every other side or rotation the part is reused on.

!!! tip "Fixing it"
    Add the block to `lostcities:rotatable` with a normal datapack tag merge. You need no code and no Lost Cities file.
    ```json title="data/<namespace>/tags/blocks/rotatable.json"
    {
      "values": ["minecraft:ladder", "minecraft:furnace"]
    }
    ```
    This merges into the existing tag rather than replacing it, exactly as any vanilla block tag does.

## Block tags the mod checks

Besides `rotatable`, five more tags in the `lostcities` namespace affect how palette blocks behave. All are ordinary datapack tags, and you extend them the same way.

| Tag | Default contents | Effect |
|---|---|---|
| `lostcities:notbreakable` | 4 blocks: bedrock, end portal, end portal frame, end gateway | Explosion and ruin damage always skip these, whatever `explosionMaxRadius` or the ruin settings say. |
| `lostcities:easybreakable` | 39 blocks, listed individually: glass, every stained glass and pane, tinted glass, glowstone, beacon, sea lantern, conduit | These break more readily under explosion and ruin damage than an untagged block. |
| `lostcities:needspoi` | 12 villager job-site blocks: barrel, smoker, blast furnace, loom, lectern and similar | Marks blocks that need point-of-interest registration when placed during generation, so villager AI linkage does not break silently. |
| `lostcities:foliage` | 6 vanilla tag references: leaves, flowers, bamboo blocks, logs, coral plants, saplings | Drives foliage-specific placement and decay handling. |
| `lostcities:lights` | 44 blocks, listed individually: torches, lanterns, glowstone, sea lantern, froglights, amethyst clusters, lava, fire and others | Used wherever the generator needs to know whether a block is a light source. |

!!! warning "These are hand-written lists, not computed ones"
    `lights` is a fixed list of 44 vanilla blocks. It is **not** every block with a light level above zero. `easybreakable` likewise names each glass block individually instead of referencing a glass tag.

    So a modded lamp, a modded glass, or any block added after these tags were written is **not** in them, and the generator treats it as an ordinary opaque block. If you build with modded light sources or glass, add them yourself with a tag merge, as shown for `rotatable` above.

## See also

- [Error Messages](../troubleshooting/errors.md) for the palette errors above, with their causes
- [Variant Reference](variant.md)
- [Style Reference](style.md) for how several palettes combine
- [Condition Reference](condition.md) for what a `mob` value points at
- [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md) for where part rotation comes from
- [Namespaces](../getting-started/namespaces.md)
