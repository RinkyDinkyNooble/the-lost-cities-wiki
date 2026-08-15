# JSON5 test packs

Three datapacks and two profiles, generated from one definition by
[generate.py](generate.py) so they cannot drift apart. All three are built to produce
the **same** three towers, so any difference between them is a fault rather than a
design choice.

| Pack | Every asset is |
|---|---|
| `j5-pure-json` | `.json` |
| `j5-pure-json5` | `.json5` |
| `j5-fighting` | both, and the `.json` twin is wrong wherever a wrong answer can be seen in blocks |

The `.json5` packs need [The Lost Cities - DevTool](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/mod).
`j5-pure-json` needs nothing but Lost Cities 7.4.12 and is the control: it proves the
towers are correct without the extension in play at all.

## Install

Copy a pack folder, or a zip of it, into `saves/<world>/datapacks/`, or add it on the
world creation screen under **Data Packs**. One at a time: all three use the namespace
`j5` and the same asset names, so they are alternatives.

Copy the profile into `config/lostcities/profiles/`, then restart. Lost Cities reads
that folder once at startup. Copy one to test a pack alone, or both to see the
profile override.

Then press **Cities** on the world creation screen and cycle to `jsonfive`.

`/reload` does not work. Lost Cities does not re-read its own assets on one.

## What should happen

Three towers, two chunks apart, about 24 blocks tall, on ground near y 71:

```
/tp @s 136 110 136
```

| x | Correct | A wrong colour means |
|---|---|---|
| 136 | Gold | diamond, the building `.json` won; redstone, the part or palette `.json` won |
| 168 | Diamond | as above |
| 200 | Lapis | as above |

Redstone is the tell. Every `.json` twin that can be wrong places it.

Both a `minecraft:overworld` and a `lostcities:lostcity` predefined city ship in each
pack, so the same pack works whether the profile is selected on the world creation
screen or wired up through `dimensionsWithProfiles`.

The two profiles differ only in `description`, so neither changes what generates.
`/lcdev report` prints that field, which is the only way to tell which file won.

## Measured

Each pack on a headless server, same seed, same profile, same probes.

| Pack | Probes | Failed chunks | Override warnings |
|---|---|---|---|
| `j5-pure-json` | 8 / 8 | none | 0 |
| `j5-pure-json5` | 8 / 8 | none | 0 |
| `j5-fighting` | 8 / 8 | none | 12, one per shadowed file |

The 12 cover every asset kind that can be shadowed: worldstyle, citystyle, palette,
both predefined cities, three parts, three buildings, and the profile.

## What cannot be `.json5`

`pack.mcmeta`, and only that. Minecraft reads it to decide whether the folder is a
datapack at all, before any mod code runs.
