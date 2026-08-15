# 1.0.0

First public release. For Minecraft 1.20.1, Forge 47+, The Lost Cities 7.4.12.

Everything below is verified on a headless Forge server that boots a real world,
force loads a grid and reads the blocks back, rather than by eye.

## Diagnostics, on by default

These only change what is reported. None can alter block placement.

- **Faults name the building and its chunk**, enriched where that is still known
  rather than reported against whichever neighbour queried it. On a pack with three
  broken buildings, 78 undifferentiated failures became 3 named faults.
- **A fuller report beside each caught fault**, naming the profile, world style, city
  style, building, floor and cellar counts, and the whole cause chain. For an
  unresolved palette character it gives the code point and Unicode name, which a
  console cannot render.
- **Every asset file is checked when datapacks load**, with a file name and a line
  number. Nine rules, each one reproducing a real in-game failure statically.
- **`LostCitySphereFeature` gains the catch the terrain feature already has.** On
  `landscapeType` spheres, cavernspheres or space, a fault that would be logged per
  chunk was escaping instead. Measured: 21 escaping and a dead server, against 0
  escaping and 338 logged with it on.

## Authoring

- **Comments and trailing commas** in Lost Cities asset files and profiles.
- **The `.json5` extension**, so an editor stops underlining them. Where both names
  exist the `.json5` wins and the shadowed file is reported in the log and once in
  chat.
- **`/lcdev report`** names the profile, world style, city style, building and the
  part chosen for each level. `/lostcities debug` writes to the server console only
  and stops short of the palette.
- **`/lcdev char`** and **`/lcdev block`**, forwards and reverse, reporting the chunk
  and every named asset that defines the character. `U+XXXX` accepted, because a
  palette character is routinely one a chat box cannot take.
- **`/lcdev in <asset> char|block`** asks one named palette, part or building
  directly, with tab completion, and works from anywhere including outside a city.

## Repairs, off by default

Each changes what generates, so a world made with one enabled will not come out the
same without it.

- **`belowpart` tests the part below**, as its name says. It currently compiles to
  the same predicate as `inpart`, so a building gated on it fails every chunk it
  stands in.
- **`streetblocks.parts.full` becomes reachable.** The bound on the street type roll
  is one too large, so the shape is never chosen. Verified unreachable in 7.4.12
  through 10.0.1.

## Client, on by default, no effect on generation

- The **Cities button keeps its position** when the window is resized, instead of
  landing over the vanilla buttons.
- **Customize no longer crashes** the game after you have played a world. Leaving a
  world clears the profile list, `toggleProfile` rebuilds it lazily and `customize`
  did not.
- **Right-click on the profile button cycles backwards.** The button is a plain
  vanilla button whose handler accepts the left button only, so a right-click did
  nothing at all.

## Reported, not repaired

Lost Cities 7.4.12 ships `lostcities:bricks_desert_redsand` carrying
`"block": "minecraft:red_sandstone@2"`, a pre-flattening block id whose `@` is not
legal in a resource location. The throw lands while the palette is built rather than
while the character is read, so the file loses all three of its characters and not
only the one at fault.

Nothing in 7.4.12 references that palette, so nothing is broken until an author points
at it. The load-time check names the file, the line and the character.
