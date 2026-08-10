---
status: in-progress
---

# Command Blocks & Third-Party Mod Integration

!!! info "More integration patterns are planned"
    Everything below is accurate and works today. What is still to come is the wider mod-integration side: more worked patterns for reaching behaviour no Lost Cities field exposes.

!!! tip "TL;DR"
    A palette entry's `tag` field is raw NBT. Point `block` at `minecraft:command_block` and set `tag.Command`, and a palette character can run any command the moment that chunk generates. Everything on this page works in vanilla, no other mods required.

## Why this works

[Palette entries](../reference/palette.md) support an optional `tag` field: arbitrary NBT attached to the placed block. A command block's NBT includes a `Command` string. Combine them, and every place that character appears in a part generates a working, pre-configured command block.

`auto: 1` and `conditionMet: 1` are what make it fire on its own, with no redstone and no player nearby.

## The self-replacing pattern

The most useful version of this trick has the command block **overwrite itself**. `setblock ~ ~ ~ ... replace` targets the command block's own position, so the command runs once, the block it wanted appears, and the command block is gone in the same tick. Nothing is left behind for players to find.

```json title="A palette entry that becomes a stair with an exact, forced shape"
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

This is the reliable workaround for the stair-shape problem described on the [Palette page](../reference/palette.md#stairs-fences-and-walls-correct-themselves-on-placement). Normal generation always recalculates a stair's `shape` from its neighbours and discards whatever you wrote. A command block does not run during generation, it runs after, once the chunk is already placed and that correction pass has finished. Vanilla `/setblock` writes the block state you give it verbatim, with no neighbour-based recalculation, so the exact shape survives.

!!! warning "Clean up after yourself"
    If your command does not replace the command block, the command block **stays in the world**, visible and interactable. Either end with a self-replacing `setblock` like above, or replace it with air:
    ```
    setblock ~ ~ ~ minecraft:air replace
    ```
    Placing a decorative block elsewhere and then air-ing yourself out takes two command blocks, or one command block running a function.

## Other things vanilla commands can do here

Anything a command can do, on generation, with no player involved:

| Goal | Command shape |
|---|---|
| Force an exact block state the palette cannot express | `setblock ~ ~ ~ <state> replace` |
| Fill a small region | `fill ~ ~ ~ ~2 ~2 ~2 <block> replace` |
| Place something and clean up | `setblock ~ ~1 ~ <block>` then a second block air-ing the first |
| Run a datapack function | `function <namespace>:<path>` |
| Summon an entity | `summon <entity> ~ ~ ~ {...}` |

!!! note "Commands run per generated chunk"
    Every copy of that part, in every chunk, fires its own command block. Keep them cheap. A `fill` across a large area, or a function that scans blocks, multiplied by every generated city chunk, is a real performance problem.

## Extending it with commands from other mods

The same mechanism works with commands that do not exist in vanilla, as long as **whatever provides that command is installed and loaded when the block fires**. A modpack can register its own commands (KubeJS server scripts are the usual way) and then call them from a generated command block, which is how you reach behaviour no Lost Cities field exposes.

A worked case: placing another mod's block entity **pre-configured**, for example a passcode-locked door with its code already set. Nothing in Lost Cities can create and configure another mod's block entity, but a command that mod provides can.

!!! warning "Custom commands are not portable"
    A command that exists only because one modpack defined it silently does nothing anywhere else. The command block fires, the command fails, generation carries on, and you get an empty spot with no error. If you are following an example that uses an unfamiliar command, check whether it is vanilla before assuming it will work for you.

    Prefer the function approach below wherever it can do the job, since it travels with your datapack.

## Packaging logic in a vanilla function

Anything beyond one command should go in a **datapack function** rather than a chain of command blocks or a mod-specific command. Functions are vanilla, they live in the same datapack as your parts, and they cost you one palette entry instead of several.

```mcfunction title="data/mycity/functions/place_corner.mcfunction"
# runs at the command block's own position
setblock ~ ~1 ~ minecraft:lantern[hanging=true] replace
setblock ~ ~ ~ minecraft:smooth_quartz_stairs[facing=east,half=bottom,shape=outer_left] replace
```

```json title="The palette entry that calls it"
{
  "char": "ψ",
  "block": "minecraft:command_block[conditional=false,facing=west]",
  "tag": {
    "Command": "function mycity:place_corner",
    "auto": 1,
    "conditionMet": 1
  }
}
```

A function run from a command block inherits that block's position, so `~ ~ ~` inside the function is the command block itself. Put the line that replaces the command block **last**, so the rest has already run by the time it disappears.

Note the folder is `functions` (plural) on 1.20.1. It was renamed to `function` in 1.21, so a function copied from a newer pack will not be found.

This covers most of what people reach for a custom command to do: multiple blocks, entities, NBT, all in one palette character, and it works in any pack that has your datapack.

## Practical notes

- `auto` and `conditionMet` are vanilla command block NBT fields, not Lost Cities ones. Anything vanilla command blocks support works here.
- Command blocks need `enable-command-block=true` in `server.properties` on a dedicated server. If your generated command blocks do nothing on a server but work in singleplayer, check that first.
- The command runs with the command block's own permission level, not a player's.

## See also

- [Palette Reference](../reference/palette.md) for the `tag` field and the stair-shape mechanic
- [KubeJS Integration](kubejs.md)
