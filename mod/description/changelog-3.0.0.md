# 3.0.0

A pack you can finish without leaving the game, and a workshop that stops moving under
you.

**Breaking: an existing workshop's coordinates change.** Export before upgrading,
import after. See the last section.

## Palettes no longer run out

Every distinct block state in a pack needs its own palette character, and the pool the
exporter drew from held 120 of them. Two ordinary buildings could exhaust it, and the
export refused with "ran out of palette characters". Setting a plot to use its own part
palette did not help, because the character came from one pool shared by the whole
workshop however a plot asked for its palette to be placed.

The pool now runs through the whole plane, about **40,000 characters**, against the
roughly 26,000 block states Minecraft ships. A pack of 1,174 distinct block states was
exported, loaded and generated to check it.

Characters are chosen to survive being written to a file and read back. Nothing blank,
nothing that reorders the text around it, nothing a normaliser would rewrite, nothing
above `U+FFFF` which Lost Cities reads as two cells, and nothing undefined. The old pool
contained three characters that failed one of those rules.

Nothing already lettered is re-lettered: the pool keeps its old beginning, so an
existing world carries on where it left off.

## A way out of the workshop

`/lcdev workshop leave` puts you back where you ran `go`. The position and the
dimension are recorded on the player before the teleport, so it survives a logout, and
running `go` twice does not overwrite it, so you cannot strand yourself. With nothing
recorded it sends you to world spawn rather than to a respawn point, since a respawn
point is a bed that may have been broken since.

## Conditions can be read

`loot` and `mob` in a palette name a **Condition**, not a loot table and not an entity,
and until now there was no way to see what one contained without opening somebody
else's pack.

```
/lcdev conditions             every Condition loaded
/lcdev condition chestloot    its entries, each one's share, and the test that places it
```

The asset check gained rules for them too: a missing or unreadable weight, a negative
one, weights totalling zero, and any key that is none of the thirteen tests the format
keeps.

## A pack's licence travels with the pack

An import shows what a pack's author said about reuse, read from `license.txt` in the
pack itself. An export carries those statements into what you build, one heading per
namespace, so a pack compiled out of somebody else's content does not ship with the
credit stripped out. `export plot` carries only that plot's.

A namespace that states nothing is reported as **nothing found**, which is not the same
as nothing being reserved.

## Choosing what reaches the pack

`tagkeys` decides which of a block's NBT is exported. Naming keys keeps only those,
prefixing one with `!` drops it and keeps the rest, and a dot reaches inside. So a chest
you opened while building does not ship its contents, and a loot chest does not ship a
seed that pins one roll into every copy. `/lcdev export mypack notags` drops all of it.

A conversion now belongs to a scope, so a placeholder block can mean different things on
different plots, chunks and levels, the narrower winning and adding to the wider.

`/lcdev export mypack plot` writes just the plot you are standing on, as a fragment with
no world style.

## Settings files edited outside the game

Values are read from the file every time, so an edit made in a text editor is already
what the next export compiles. `/lcdev workshop sync` is for the case a file describes a
plot the catalogue does not have: it finds it and grows the row to cover it.

It also reports a key nothing reads, at any depth. A mistyped key is an error nowhere
else: `floor` where `floors` was meant produces a one storey building and no complaint,
and that is now caught inside a chunk or level scope as well as beside them.

## Smaller

- Reading a large asset file was quadratic. On a 132 KB file that was 56ms; it is 1ms.
- A failed backup named the first thing it found rather than the error that caused it,
  in the message you read immediately before a wipe.
- The `full` street shape fix is measured: the shape draws nothing with it off and 1,504
  blocks with it on.
- Pressing Customize after having played a world no longer crashes the game.

## Upgrading

**An existing workshop's coordinates change.** Rows used to take no room until they held
plots, so growing one pushed every row after it, and anything already built was left at
coordinates belonging to a different plot. Rows now keep their band whether or not they
hold plots, which is what stops it happening again.

**Export before upgrading, import after.** The export is the only record of what was on
a plot that survives the move.
