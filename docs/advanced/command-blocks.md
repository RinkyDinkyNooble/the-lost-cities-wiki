# Command Blocks & Third-Party Mod Integration

!!! tip "TL;DR"
    A palette entry's `tag` field is raw NBT. Point `block` at `minecraft:command_block` and set `tag.Command`, and a palette character can run any command on generation, including commands from other mods.

## Why this works

[Palette entries](../reference/palette.md) support an optional `tag` field, arbitrary NBT attached to the placed block. A command block's NBT includes a `Command` string. Combine them and every place that character appears in a part generates a working, pre-configured command block.

```json
{
  "char": "Á",
  "block": "minecraft:command_block[conditional=false,facing=west]",
  "tag": {
    "Command": "/placeKeypad ...",
    "auto": 1,
    "conditionMet": 1
  }
}
```

`auto: 1` and `conditionMet: 1` make it fire automatically once generation places it, no redstone or player interaction needed.

## What this unlocks

Anything the command has access to. Two real examples, both from production use:

- **Third-party mod integration**: a custom `/placeKeypad` command (defined via a command-registering mod like KubeJS server scripts) that hooks into SecurityCraft to generate a passcode-locked keypad door, something no Lost Cities palette field could do on its own.
- **Forcing an exact stair shape**: a custom `/placeBlockEntity <blockstate> {}` command (also your own, not built into Lost Cities or vanilla) to force an exact block state directly. This specifically works around the stair shape auto-correction described on the [Palette](../reference/palette.md) page: generation always recalculates a placed stair's shape from its neighbors, but a command block only fires after generation finishes, so the auto-correction pass has already run and won't touch what the command places.

## Practical notes

- `auto`/`conditionMet` are vanilla command block NBT fields, not Lost Cities specific. Anything vanilla command blocks support, this supports.
- This only works if the command actually exists on the server when the block fires (a custom command from another mod's script needs that mod loaded).

## See also

[Palette Reference](../reference/palette.md)
