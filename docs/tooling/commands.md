# Testing & Debugging Commands

!!! tip "TL;DR"
    `/lostcities <command>` (alias `/lost`). Six commands here are useful for checking your custom city actually works.

    | Command | Needs op? |
    |---|---|
    | `debug`, `map`, `stats`, `saveprofile` | No, permission level 0 |
    | `locate`, `createbuilding` | **Yes**, permission level 1 |

!!! note "The in-game editor has its own page"
    Lost Cities also ships six commands for live in-world editing (`createpart`, `editpart`, `resumeedit`, `exportpart`, `listparts`, `locatepart`). They need a world created with `editMode: true` and have some sharp edges, so they are covered on [Editing & Tooling](editing.md) instead.

    There is one more, `testfill`, which drops a 5×5×5 blob of random block states around you. It is a developer scratch command with no authoring use.

## Seeing your changes

**There is no regenerate command.** Lost Cities ships nothing that rebuilds an existing chunk, and it registers no datapack reload listener, so:

| What you do | Does it pick up edited assets? |
|---|---|
| `/reload` | **No.** These registries are read once at world load. Vanilla does not reload them either. |
| Leave the world, rejoin (single player) | **Yes.** Logging out clears the mod's asset cache, so the next world load re-reads every file. |
| Restart the dedicated server | **Yes.** |
| Fly back to an already-generated chunk | **No, ever.** That chunk is saved to disk. Nothing regenerates it. |

So the loop is: edit files, quit to title, rejoin, **travel somewhere new** (or delete the region files, or start a fresh world). Testing in a throwaway world is usually faster than trying to invalidate an existing one.

!!! tip "Use `createbuilding` to skip the loop for a single building"
    [`/lostcities createbuilding`](#placing-a-specific-building-on-demand) places a building on the spot without waiting for city generation to roll it. It still reads the assets loaded at world load, so you'd rejoin first, but you do not have to go hunting for a chunk that happens to pick your building.

## Getting a real profile template

```
/lostcities saveprofile <name>
```

Writes one of the mod's built-in presets (not your world's active profile) to `<name>.json` in the server's working directory, fully populated with every field at its default value. No op requirement. This is the fastest way to get a complete, valid starting point instead of typing a [Profile](../reference/profile.md) from scratch, copy the fields you actually want to change into your own file.

## Finding out why a chunk looks the way it does

```
/lostcities debug
```

Run standing in the chunk you want to inspect. Dumps everything the generator decided for that chunk, profile name, building type, floor/cellar count, city level, city style, street type, ruin height, highway levels, rail info, city-sphere data, explosion count, whether it is ocean, straight to the **server console**, not chat. On a dedicated server you need console/log access to see it; in singleplayer it still only goes to the game log, not the in-game chat overlay. This is the single richest diagnostic available, worth checking first for "why did not my city style/building apply here."

```
/lostcities map
```

Also console-only. Prints a 41×41-chunk ASCII map centered on you: `B` = city chunk with a building, `+` = city chunk without one (street/plaza), `.` = highway, blank = neither. Good for a quick sanity check that cities and highways are actually generating at the density you expect, without flying around.

## Checking generation is not lagging the server

```
/lostcities stats
```

Reports average/min/max city-chunk generation time in milliseconds, to chat this time. If a custom city style or a heavy palette is causing noticeable lag, this is the first thing to check.

## Finding a specific building

```
/lostcities locate <buildingName>
```

Spirals outward from you, up to 30 chunks, and reports the first 6 matches to chat with coordinates. Useful for confirming a rare/special building you added actually generates somewhere nearby, without a full manual search. Building names are tab-completed live from your loaded registries, so custom buildings autocomplete correctly.

## Placing a specific building on demand

```
/lostcities createbuilding <name> <floors> <cellars> <pos>
```

Force-places a registered [Building](../reference/building.md) at an exact position, bypassing normal city-generation selection entirely, useful for previewing a building you are actively authoring without waiting for city generation to roll it naturally. Floors accepts 1–20, cellars 0–10, independent of whatever min/max the building or city style define.

!!! warning "Crashes loudly on a bad palette reference"
    If any part the building references points at a palette character that does not resolve, this command throws a server-side error visible to whoever ran it, rather than a clean chat message. If you see a crash instead of a placed building, check your palette references first.

## See also

- [Error Messages](../troubleshooting/errors.md) if a command or a chunk throws
- [Profile Reference](../reference/profile.md)
- [Building Reference](../reference/building.md)
