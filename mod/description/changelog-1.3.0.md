# 1.3.0

Two things a real pack does that an import used to lose: the variety between floors,
and the NBT a block carries.

Nothing here changes world generation.

## A tall building comes in with its middle intact

A building can name several parts for the same level. A band written as
`range: "9,12"` twice, naming a different part each time, is the pack telling the
generator to pick between them on every level in that band.

The import took the first match every time, so a band of four storeys came in as the
same storey four times. On a nine floor building with two alternates for its middle,
that is most of the building arriving wrong.

It steps through the candidates by level now, so the plot shows what the building is
actually made of. It does it the same way every time, so the same pack always
imports the same.

## Command blocks keep their commands

A palette entry can carry `tag`, a raw NBT compound, and that is the mechanism
behind the command-block technique: Lost Cities places the block already holding its
command, and with `auto` set it runs where it lands and turns itself into whatever it
was there to place. A pack built that way is mostly command blocks.

The import pasted the block and dropped the tag, so what arrived was an empty
command block that did nothing. It carries the tag now, and so does an export, which
means chests keep their loot tables and spawners keep their mobs as well.

By default a pasted command block is left unable to fire. A workshop is not a world,
and forty spawn commands going off while you are trying to look at a building is not
useful. The command is still there and still exports.

```
/lcdev import mypack:main run
```

`run` pastes them live, so they fire and resolve into whatever they place. `keep` and
`run` can be given together, in either order.
