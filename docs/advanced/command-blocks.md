---
status: in-progress
---

# Command Blocks & Third-Party Mod Integration

!!! tip "TL;DR"
    A palette entry's `tag` field is raw NBT. Point `block` at `minecraft:command_block` and set `tag.Command`, and a palette character can run any command the moment that chunk generates. Everything on this page works in vanilla, no other mods required.

## Why this works

[Palette entries](../reference/palette.md) support an optional `tag` field: arbitrary NBT attached to the placed block. A command block's NBT includes a `Command` string. Combine them, and every place that character appears in a part generates a working, pre-configured command block.

`auto: 1` and `conditionMet: 1` are what make it fire on its own, with no redstone and no player nearby.

## The self-replacing pattern

The most useful version of this trick has the command block **overwrite itself**. `setblock ~ ~ ~ ... replace` targets the command block's own position, so the command runs once, the block it wanted appears, and the command block is gone in the same tick. Nothing is left behind for players to find.

```json title="A palette entry that becomes a stair with an exact, forced shape"
{
  "char": "Á",
  "block": "minecraft:command_block[conditional=false,facing=west]",
  "tag": {
    "Command": "setblock ~ ~ ~ minecraft:smooth_quartz_stairs[facing=east,half=bottom,shape=outer_left] replace",
    "auto": 1,
    "conditionMet": 1
  }
}
```

This is the reliable workaround for the stair-shape problem described on the [Palette page](../reference/palette.md#stairs-fences-and-walls-auto-correct-on-placement). Normal generation always recalculates a stair's `shape` from its neighbors and discards whatever you wrote. A command block doesn't run during generation, it runs after, once the chunk is already placed and that correction pass has finished. Vanilla `/setblock` writes the block state you give it verbatim, with no neighbor-based recalculation, so the exact shape survives.

!!! warning "Clean up after yourself"
    If your command doesn't replace the command block, the command block **stays in the world**, visible and interactable. Either end with a self-replacing `setblock` like above, or replace it with air:
    ```
    setblock ~ ~ ~ minecraft:air replace
    ```
    Placing a decorative block elsewhere and then air-ing yourself out takes two command blocks, or one command block running a function.

## Other things vanilla commands can do here

Anything a command can do, on generation, with no player involved:

| Goal | Command shape |
|---|---|
| Force an exact block state the palette can't express | `setblock ~ ~ ~ <state> replace` |
| Fill a small region | `fill ~ ~ ~ ~2 ~2 ~2 <block> replace` |
| Place something and clean up | `setblock ~ ~1 ~ <block>` then a second block air-ing the first |
| Run a datapack function | `function <namespace>:<path>` |
| Summon an entity | `summon <entity> ~ ~ ~ {...}` |

!!! note "Commands run per generated chunk"
    Every copy of that part, in every chunk, fires its own command block. Keep them cheap. A `fill` across a large area, or a function that scans blocks, multiplied by every generated city chunk, is a real performance problem.

## Extending it with commands from other mods

The same mechanism works with commands that don't exist in vanilla, as long as **whatever provides that command is installed and loaded when the block fires**. A modpack can register its own commands (KubeJS server scripts are the usual way) and then call them from a generated command block, which is how you reach behavior no Lost Cities field exposes.

A real production example: a modpack-defined `/placeKeypad` command that places a SecurityCraft passcode-locked keypad door, pre-configured, at generation time. Nothing in Lost Cities can place and configure another mod's block entity, but a command can.

!!! warning "Custom commands are not portable"
    A command like `/placeKeypad` only exists because that specific modpack defined it. Copying a palette entry that calls it into a different pack silently does nothing (the command block fires, the command fails, generation continues). If you're following an example that uses an unfamiliar command, check whether it's vanilla before assuming it will work for you.

For a working reference of what registering such a command looks like, the modpack this wiki's author maintains keeps its command definitions in `kubejs/server_scripts/` at [RinkyDinkyNooble/apocalypse-begins-zombie-apocalypse](https://github.com/RinkyDinkyNooble/apocalypse-begins-zombie-apocalypse).

## Practical notes

- `auto` and `conditionMet` are vanilla command block NBT fields, not Lost Cities ones. Anything vanilla command blocks support works here.
- Command blocks need `enable-command-block=true` in `server.properties` on a dedicated server. If your generated command blocks do nothing on a server but work in singleplayer, check that first.
- The command runs with the command block's own permission level, not a player's.

## See also

- [Palette Reference](../reference/palette.md) for the `tag` field and the stair-shape mechanic
- [KubeJS Integration](kubejs.md)
