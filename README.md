# The Lost Cities Wiki

An unofficial, community guide to building custom cities with [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Minecraft mod by McJty.

**Read it at [rinkydinkynooble.github.io/the-lost-cities-wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/)**

Not affiliated with or endorsed by McJty. The Lost Cities is his work, and he answers questions in Discord daily on top of writing it. This is an independent guide, meant to sit alongside his documentation rather than replace it.

## The mod's own documentation

Read these first. They are the authoritative sources:

- [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities), the general documentation
- [asset-datapack page](https://www.mcjty.eu/docs/mods/lost-cities/asset-datapack), on the datapack asset system
- [`asset_structure.md`](https://github.com/McJtyMods/LostCities/blob/1.20/docs/asset_structure.md), a key-by-key reference

## What this adds

Depth on the parts you hit while authoring: what a value does rather than what a key is called, what happens when you get it wrong, and which log line to expect.

Claims are checked one of two ways, and pages say which:

| How | What it means |
|---|---|
| Read from the mod | The behaviour was traced through the compiled code of the version named on the page. |
| Run in a world | The behaviour was reproduced in game, and the result is on [Claim Tests](https://rinkydinkynooble.github.io/the-lost-cities-wiki/examples/claim-tests/). |

Testing has corrected several pages here and turned up two mod bugs. Those are on [Known Issues](https://rinkydinkynooble.github.io/the-lost-cities-wiki/troubleshooting/known-issues/) with the evidence.

## Version coverage

| Target | State |
|---|---|
| Lost Cities **7.4.12**, Minecraft 1.20.1, Forge | Primary. Read from the mod and run in a world. |
| **7.5.1**, Minecraft 1.20.1, Forge | Read from the mod and run in a world. The 7.4.12 claim-test pack passes unchanged on it. |
| 8.x, 9.x, 10.x on NeoForge | In progress. Key and default differences are mapped; behaviour is not yet tested. |
| Before 5.3.29 | Out of scope. Those versions load content from inside the jar rather than from datapacks. |

The [Versions](https://rinkydinkynooble.github.io/the-lost-cities-wiki/versions/) section states which pages apply to which release. 7.5.1 through 10.0.1 declare the same 160 profile keys and 231 datapack keys, so one set of pages covers all four.

## Layout

| Path | Contents |
|---|---|
| `docs/` | The wiki, built with MkDocs Material |
| `docs/examples/first-city/` | A complete example datapack that loads as it is |
| `docs/examples/wiki-test7/` | A claim-test pack, pinned to fixed coordinates |
| `docs/examples/validate.py` | Checks a datapack against the rules the wiki documents |
| `docs/examples/mod-keys.json` | The mod's real codec and profile keys, extracted from the jars |
| `STYLE.md` | Writing rules |
| `CONTRIBUTING.md` | How to report or send a correction |

## Running it locally

```bash
pip install -r requirements.txt
```

```bash
mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## The checks

Two gates run in CI on every push, and they block the Pages deploy:

```bash
mkdocs build --strict
```

```bash
python docs/examples/validate.py docs/examples/first-city
```

`--strict` turns a broken internal link or anchor into a build failure.

`validate.py` checks a datapack against the wiki, and the wiki against the mod:

- **The example still obeys the rules.** Every rule the wiki states is a check here, so the shipped example cannot drift from the pages that describe it. Pages that inline a whole example file are compared byte for byte.
- **Every documented key exists.** Reference tables are checked against `mod-keys.json`, which holds the keys the mod's codecs actually declare, extracted from the jars. A key the wiki documents that the mod does not have is an error, and so is a key marked optional that the codec requires.
- **Level coverage is computed, not assumed.** Levels run from `-cellars` to `maxfloors` inclusive, so `maxfloors: 3` is a four-storey building. The validator works out which levels no part matches and names them, because that mistake fails every chunk holding the building and its neighbours.
- **Known-dead keys are rejected.** Keys that parse and then do nothing are errors, with a pointer to why.

Together they stop the docs, the example, and the mod's real schema from drifting apart.

## Testing claims in a world

`docs/examples/wiki-test7/` is a datapack whose only job is to be checked. A predefined city pins it to fixed chunk coordinates, so every test has a block address rather than needing to be found.

It also runs unattended on a headless Forge server: force load the grid, then read the result back over RCON, using a filtered `/clone` to count blocks. Setup and the probe list are on [Claim Tests](https://rinkydinkynooble.github.io/the-lost-cities-wiki/examples/claim-tests/).

Adding a probe for something the wiki asserts and nobody has run is the most useful contribution available.

## Contributing

Corrections are welcome, especially ones backed by something you observed. State **what you observed** and **which mod version**. You do not need to work out why.

See [CONTRIBUTING.md](CONTRIBUTING.md), and [STYLE.md](STYLE.md) before writing prose.

## Licence

[CC0 1.0](LICENSE). No rights reserved, no attribution required.
