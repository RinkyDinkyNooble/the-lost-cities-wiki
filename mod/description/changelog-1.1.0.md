# 1.1.0

Build a Lost Cities pack by building it in Minecraft, and open an existing pack by
walking around inside it.

Everything from 1.0.1 is unchanged. Nothing here alters world generation, and the
two optional fixes are still off by default.

## Build a pack by building it

A new workshop dimension lays out a plot for every shape a pack can hold: 45 rows
covering streets, highways, railways, monorails, parks, fountains, bridges, stairs,
fronts, rail dungeons, buildings and every multibuilding footprint. Each plot is
chunk aligned, floor marked in its own colour, and separated by a walkway.

```
/lcdev workshop build     lay the plots out
/lcdev workshop go        travel there
/lcdev workshop here      what the plot you are standing on is for
```

Build in a plot with whatever you normally build with. When you are done:

```
/lcdev export mypack
```

That writes a complete datapack, plus the profile that goes with it. A pack made
this way generated a city with **10,672 gold blocks** in it on the first try.

## Open a pack you already have

```
/lcdev import lostcities:standard
```

Lost Cities' own pack comes in as **42 assets on 42 plots, 714,240 blocks placed**,
growing the catalogue to 143 plots to make room. Every plot it fills gets the
settings that would export it again, so you can change one building and compile the
whole thing back out.

Buildings that let the profile decide their height are shown as their alternatives
stacked one above the other, so you can see what the building is actually made of
rather than one arbitrary floor of it.

## Settings that explain themselves

Every plot has a settings file next to your world, written as JSON5 with the
meaning of each key in a comment above it. The same text is what tab completion
shows, so the two cannot drift apart.

```
/lcdev plot set floors 3
/lcdev plot set tops 4,6
/lcdev plot show          draw where each level starts, on the walkway
/lcdev plot keys          every setting this plot has, and what it does
```

Floor and cellar counts, roof variations, spawn weights and distance windows, city
style membership, where the palette goes, and an escape hatch for anything the
format has that the settings do not name yet.

## Say what a profile key means

```
/lcdev key cityChance
```

Gives the section it belongs to, its type, its range, its default and what it
actually does. Three keys whose shipped comment is wrong are corrected rather than
repeated.

## Two more checks on your files as they load

- A **monorail part written as a list**. The three monorail keys take one name each,
  unlike the highway and railway keys beside them, and a list there stops the whole
  world style loading.
- An **inline palette written as a bare list** instead of an object holding one.
  This one is worth knowing about: it does not fail. The file loads, the building
  generates, and it is empty, because every character in it resolves to nothing.

## Chat output

Command output is laid out properly now: a heading, aligned key and value pairs,
positions you can click to teleport to, file paths you can click to copy, and
warnings that read as warnings.
