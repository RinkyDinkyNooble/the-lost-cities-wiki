# Testing & Debugging Commands

!!! tip "TL;DR"
    `/lostcities <command>` (alias `/lost`). Six commands here are useful for checking your custom city actually works: `locate`, `debug`, `map`, `stats`, `createbuilding`, `saveprofile`. All need server op, except `map` and `stats`.

!!! note "In-game editing isn't covered here"
    Lost Cities also ships commands for live in-world editing (`createpart`, `editpart`, `resumeedit`, `exportpart`, `listparts`, `locatepart`). That workflow isn't documented on this wiki yet.

## Getting a real profile template

```
/lostcities saveprofile <name>
```

Writes one of the mod's built-in presets (not your world's active profile) to `<name>.json` in the server's working directory, fully populated with every field at its default value. No op requirement. This is the fastest way to get a complete, valid starting point instead of typing a [Profile](../reference/profile.md) from scratch, copy the fields you actually want to change into your own file.

## Finding out why a chunk looks the way it does

```
/lostcities debug
```

Run standing in the chunk you want to inspect. Dumps everything the generator decided for that chunk, profile name, building type, floor/cellar count, city level, city style, street type, ruin height, highway levels, rail info, city-sphere data, explosion count, whether it's ocean, straight to the **server console**, not chat. On a dedicated server you need console/log access to see it; in singleplayer it still only goes to the game log, not the in-game chat overlay. This is the single richest diagnostic available, worth checking first for "why didn't my city style/building apply here."

```
/lostcities map
```

Also console-only. Prints a 41×41-chunk ASCII map centered on you: `B` = city chunk with a building, `+` = city chunk without one (street/plaza), `.` = highway, blank = neither. Good for a quick sanity check that cities and highways are actually generating at the density you expect, without flying around.

## Checking generation isn't lagging the server

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

Force-places a registered [Building](../reference/building.md) at an exact position, bypassing normal city-generation selection entirely, useful for previewing a building you're actively authoring without waiting for city generation to roll it naturally. Floors accepts 1–20, cellars 0–10, independent of whatever min/max the building or city style define.

!!! warning "Crashes loudly on a bad palette reference"
    If any part the building references points at a palette character that doesn't resolve, this command throws a server-side error visible to whoever ran it, rather than a clean chat message. If you see a crash instead of a placed building, check your palette references first.

## See also

- [Profile Reference](../reference/profile.md)
- [Building Reference](../reference/building.md)
