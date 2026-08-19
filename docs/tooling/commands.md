---
claims: verified
---

# Testing & Debugging Commands

!!! tip "TL;DR"
    `/lostcities <command>` (alias `/lost`). Six commands here are useful for checking your custom city actually works.

    | Command | Needs op? | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
    |---|---|
    | `debug`, `map`, `stats`, `saveprofile` | No, permission level 0 |
    | `locate`, `createbuilding` | **Yes**, permission level 1 |

!!! note "The in-game editor has its own page"
    The mod also ships six commands for live in-world editing: `createpart`, `editpart`, `resumeedit`, `exportpart`, `listparts` and `locatepart`. All six need permission level 1. They also need a world created with `editMode: true`, and they have some sharp edges, so [Editing and Tooling](editing.md) covers them instead.

    There is one more, `testfill`, which drops a 5×5×5 blob of random block states around you. It is a developer scratch command with no authoring use. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Seeing your changes

**There is no regenerate command.** Lost Cities ships nothing that rebuilds an existing chunk, and it registers no datapack reload listener, so: [code review](../examples/claim-tests.md#ns-10){.v .v-c}

| What you do | Does it pick up edited assets? | [code review](../examples/claim-tests.md#ns-10){.v .v-c}
|---|---|
| `/reload` | **No.** These registries are read once at world load, and 7.4.12 registers no reload listener. Vanilla does not reload them either. |
| Leave the world, rejoin (single player) | **Yes.** Logging out clears the mod's asset cache, so the next world load re-reads every file. |
| Restart the dedicated server | **Yes.** |
| Fly back to an already-generated chunk | **No, ever.** That chunk is saved to disk. Nothing regenerates it. |

So the loop is: edit files, quit to title, rejoin, **travel somewhere new** (or delete the region files, or start a fresh world). Testing in a throwaway world is usually faster than trying to invalidate an existing one. <!-- noclaim -->

!!! tip "Use `createbuilding` to skip the loop for a single building"
    [`/lostcities createbuilding`](#placing-a-specific-building-on-demand) places a building on the spot without waiting for city generation to roll it. It still reads the assets loaded at world load, so rejoin first. It removes the need to search for a chunk that happens to pick the building.

## Getting a real profile template

```
/lostcities saveprofile <name>
```

Writes one of the mod's built-in presets (not your world's active profile) to `<name>.json` in the server's working directory, fully populated with every key at its default value. No op requirement. This is the fastest way to get a complete, valid starting point instead of typing a [Profile](../reference/profile.md) from scratch, copy the keys you actually want to change into your own file. [code review](../examples/claim-tests.md#cfg-7){.v .v-c}

## Finding out why a chunk looks the way it does

```
/lostcities debug
```

Run standing in the chunk you want to inspect. Dumps everything the generator decided for that chunk, profile name, building type, floor/cellar count, city level, city style, street type, ruin height, highway levels, rail info, city-sphere data, explosion count, whether it is ocean, straight to the **server console**, not chat. On a dedicated server you need console/log access to see it; in singleplayer it still only goes to the game log, not the in-game chat overlay. This is the single richest diagnostic available, worth checking first for "why did not my city style/building apply here." [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```
/lostcities map
```

Also console-only. Prints a 41×41-chunk ASCII map centered on you: `B` = city chunk with a building, `+` = city chunk without one (street/plaza), `.` = highway, blank = neither. Good for a quick sanity check that cities and highways are actually generating at the density you expect, without flying around. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Reading the answer in chat, and asking about one file

`/lostcities debug` is the richest diagnostic the mod ships, and it writes to the
server console only. [The Lost Cities - DevTool](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/releases/tag/1.0.1),
a companion mod, answers the same questions in chat and adds the two the mod does not
expose: which part was chosen on each level, and what a character resolves to after
the palette merge. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```
/lcdev report
```

Profile, world style, city style, building, floor and cellar counts, and **the part
used on each level**, including the `parts2` overlay where one applies. That per-level
listing is the direct answer to "why did this condition not fire", which otherwise
takes a rebuild to find out. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```
/lcdev char G
/lcdev char U+0047
/lcdev block minecraft:gold_block
```

Forwards and in reverse. `char` reports what the character became in this chunk and
in every palette, part and building that defines it. `block` reports which characters
produce that block. The `U+XXXX` form exists because palette characters are routinely
symbols a chat box will not accept. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```
/lcdev in mypack:mystyle char G
```

Asks one named file rather than the chunk underfoot, with tab completion over
everything that carries a palette. This works outside a city, and in a dimension with
no Lost Cities profile at all, which is the situation you are in while editing a file
rather than standing in the result. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! note
    The DevTool is not required by Lost Cities and changes no generation on its own.
    It is listed here because these are debugging commands and the console-only
    limitation above is a real obstacle on a dedicated server.

## Checking generation is not lagging the server

```
/lostcities stats
```

Reports average/min/max city-chunk generation time in milliseconds, to chat this time. If a custom city style or a heavy palette is causing noticeable lag, this is the first thing to check. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Finding a specific building

```
/lostcities locate <buildingName>
```

Spirals outward from you, up to 30 chunks, and reports the first 6 matches to chat with coordinates. Useful for confirming a rare/special building you added actually generates somewhere nearby, without a full manual search. Building names are tab-completed live from your loaded registries, so custom buildings autocomplete correctly. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Placing a specific building on demand

```
/lostcities createbuilding <name> <floors> <cellars> <pos>
```

Force-places a registered [Building](../reference/building.md) at an exact position, bypassing normal city-generation selection entirely, useful for previewing a building you are actively authoring without waiting for city generation to roll it naturally. Floors accepts 1–20, cellars 0–10, independent of whatever min/max the building or city style define. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! warning "Crashes loudly on a bad palette reference"
    If any part the building references points at a palette character that does not resolve, this command throws a server-side error visible to whoever ran it, rather than a clean chat message. If you see a crash instead of a placed building, check your palette references first.

## See also

- [Error Messages](../troubleshooting/errors.md) if a command or a chunk throws
- [Profile Reference](../reference/profile.md)
- [Building Reference](../reference/building.md) <!-- noclaim -->
