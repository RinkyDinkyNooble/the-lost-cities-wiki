# 1.1.0

Build a Lost Cities pack by building it in Minecraft, and open a pack you already
have by walking around inside it.

Nothing here changes world generation. The two optional fixes are still off by
default, and everything 1.0.1 did, it still does.

## Build a pack by building it

There is a new workshop dimension with a plot for every shape a pack can hold: 138
rows covering streets, highways, railways, monorails, parks, fountains, bridges,
stairs, fronts, rail dungeons, buildings, and every multibuilding footprint up to
10x10. Each plot sits on chunk boundaries, has its own floor colour, and has a
walkway around it.

```
/lcdev workshop build     lay the plots out
/lcdev workshop go        travel there
/lcdev workshop here      what the plot you are standing on is for
/lcdev workshop rows      every row, each one a place to click
```

Build in a plot with whatever you normally build with. Then:

```
/lcdev export mypack
```

That writes a complete datapack and the profile that goes with it. A pack made this
way generated a city with **10,672 gold blocks** in it.

Rows start at eight plots and grow as far as you want:

```
/lcdev workshop grow multibuilding/4x6 6
```

The bigger multibuilding footprints are listed but not laid out until you grow one,
since painting all of them would be several thousand chunks of floor for shapes most
packs never use. Ten is as wide as a multibuilding gets, and that limit is Lost
Cities' rather than this mod's: one is placed inside a single area of
`multisettings.areasize` chunks square, which is 10 in the shipped world style, and
a footprint wider than its area throws during generation instead of being skipped.

## Open a pack you already have

```
/lcdev import lostcities:standard
```

Lost Cities' own pack comes in as **42 assets on 42 plots, 714,240 blocks placed**,
growing the rows to make room. Streets arrive too, even though no city style in that
pack names a single street part: the shapes fall back to the parts generation uses,
so that is what the import follows. Those plots are marked to stay out of an export,
because a pack falling back to an asset is not a pack containing it.

Every plot it fills gets the settings that would export it again, so you can change
one building and compile the whole thing back out.

A building that lets the profile decide its height is shown as its alternatives
stacked one above the other, so you can see what it is actually made of rather than
one arbitrary floor of it.

You no longer have to quote a namespaced name. `lostcities:standard` used to stop at
the colon and report trailing data, with nothing to say that quotes would fix it.

## Settings that explain themselves

Every plot has a settings file beside your world, written as JSON5 with the meaning
of each key in a comment above it. Tab completion shows the same text, so the two
cannot drift apart.

```
/lcdev plot set floors 3
/lcdev plot set tops 4,6
/lcdev plot show          draw where each level starts, on the walkway
/lcdev plot keys          every setting this plot has, and what it does
```

Floor and cellar counts, roof variations, spawn weights and distance windows, city
style membership, where the palette goes, and an escape hatch for anything in the
format the settings do not name yet.

## Say what a profile key means

```
/lcdev key cityChance
```

You get the section it belongs to, its type, its range, its default, and what it
does. Three keys whose shipped comment is wrong are corrected rather than repeated.

## Better checking of your files

Two more faults are caught as your files load. A monorail part written as a list is
one: those three keys take a single name each, unlike the highway and railway keys
beside them, and a list there stops the whole world style loading. The other is an
inline palette written as a bare list instead of an object holding one, which is
worth knowing about because it does not fail. The file loads, the building
generates, and it comes out empty, because every character in it resolves to
nothing.

The check also copes with a file whose values are the wrong type. A number where
text belongs used to make it give up on that file and log `could not check`, so none
of the file's real faults were reported either. Now it reports what it finds and
says what the mismatched value should have been.

## On a server

Every `/lcdev` command needs permission level 2, which means `op` on a server and
cheats enabled in single player. This is a tool for building a pack rather than a
feature for players: it teleports between dimensions, writes tens of thousands of
blocks, and reads and writes files beside your world.

A client does not need the mod to join a server that has it. Command output goes to
whoever ran the command rather than to every operator, so two people can work
without filling each other's chat. Plot settings are files written per command with
no locking, so if two people edit the same plot at the same moment, the last write
wins. Different plots are fine.

## Chat output

Command output is laid out properly now: a heading, aligned keys and values,
positions you can click to teleport to, file paths you can click to copy, and
warnings that read as warnings.

The warning about a `.json5` shadowing a `.json` is one of those. It used to arrive
as a single block of text that the chat box broke into thirds wherever it ran out of
width. It is one line per file now, and names each pair once instead of twice.
