# 3.1.2-7.5

For The Lost Cities 7.5.1 to 7.5.6, on Minecraft 1.20.1 and Forge 47+.

Everything since `3.1.1-7.5`. A review of the whole mod: bug fixes, one of them data
loss, faster export and completion, and no new features.

| Your Lost Cities | Download |
|---|---|
| 7.4.12 | `3.0.0` |
| 7.5.1, 7.5.2, 7.5.3, 7.5.4, 7.5.5, 7.5.6 | `3.1.2-7.5` |

## Fixed: data loss

**`/lcdev export .. -f` deleted every export and every wipe backup.** An export name
of `..` named the mod's config folder, and `-f` deleted that tree before writing the
pack into it. A name now has to resolve to one folder directly inside the exports
folder, and may not start with a dot.

**Plot commands acted in whatever dimension the caller stood in.** Run from the
overworld over a plot's coordinates, `plot hide` cleared a ring of real blocks from
the bottom of the world to the top, and `plot show`, `plot set` and `export .. plot`
acted on the workshop plot sharing those coordinates. The console stands at the
overworld spawn, usually over the front desk. Plot commands now refuse outside the
workshop.

## Fixed: the load check

| Was | Now |
|---|---|
| Read buildings, palettes and parts only | Also Conditions and world styles, as the README always said |
| Called a list under a monorail key a load error | Lost Cities 1.20.1 ignores it and uses its default monorail parts; the message says so |
| Its level tests disagreed with the import's and with Lost Cities' | One reading, Lost Cities': `"top": "yes"` places the part on every level, and is reported |
| Checked a building's full height only | Every height between `minfloors` and `maxfloors`, since Lost Cities can roll any of them |
| A `.json5` in an early pack beat the `.json` a later pack put there to replace it | Pack order decides; `.json5` wins only inside one pack |

## Fixed: import, export and sync

| Was | Now |
|---|---|
| A layer written as several rows per line pasted row by row, mostly air | Rows are joined before reading, as Lost Cities does |
| A city style inheriting from itself crashed a player's command with a stack overflow | Refused, with the chain named |
| `minecraft:red_sandstone@2` imported as red sandstone | Warned and not pasted, since Lost Cities refuses the palette over it |
| Two profiles naming alternatives gave one's style with the other's threshold | Kept as a pair, first by profile name |
| A hand-edited `"factor": "lots"` or similar ended an export in "An unexpected error occurred" | Refused once, naming the plot and the key |
| A ledger giving one character to two cells loaded, and drew the wrong block | Refused, naming both cells |
| The ledger wrote every `=` in a block state as `=` | Written plainly |
| A settings value holding a quote made the next save unreadable | Escaped |
| Sync reported the front desk's `profile` block as unused, and a grown multibuilding row as naming no row | Neither |
| `workshop here` said "variation 9 of 8" on a grown row | Counts the plots laid out |
| The `[repairs]` comment in the config file said all default to false | Three of five default to true, and it says so |
| The client's profile button stepped through profiles in two orders | One order |

## Faster

Measured against 3.1.1 on the same server, idle before each timing.

| What | Before | After |
|---|---|---|
| Export | 949 ms | 783 ms |
| Wipe survey | 34 ms | 22 ms |
| Palette lookups behind completion | 6.2 ms | 2.8 ms |
| Workshop layout, per keystroke | 0.5 ms | 0.2 ms |

The last two grow with the pack, which is why they were worth doing at this size.

## Supported range

Now 7.5.1 through 7.5.6, closed at the top. 7.5.6 changes 39 classes and adds 9, all
chunk and highway planning. Every mixin injection point holds on it by exact
descriptor and call count, every Lost Cities call this mod makes is still there, it
declares no key the reference lacks, and the full check suite passes against it.
