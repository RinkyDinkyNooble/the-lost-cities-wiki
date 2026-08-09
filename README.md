# The Lost Cities Wiki

An in-depth, unofficial guide to building custom cities with [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Minecraft mod by McJty.

**Read it at [https://rinkydinkynoble.github.io/the-lost-cities-wiki/](https://rinkydinkynooble.github.io/the-lost-cities-wiki/)**

## What this is

The mod's own documentation lives at [mcjty.eu](https://mcjty.eu/docs/mods/lost-cities) and is worth reading. This site exists to go further: the parts you only find out by reading the decompiled source, breaking things, or asking around.

Everything here is verified against **Lost Cities 7.4.12 / Minecraft 1.20.1 (Forge)**, against the mod's actual code and shipped content rather than against other documentation. Where a claim comes from a specific behaviour, the page says what that behaviour is and what happens when you get it wrong.

Some things you won't find elsewhere:

- Why buildings crash chunk generation with `Misconfiguration! Floor were generated...`, and the real rule behind it
- That city style `inherit` is **additive** for selectors, so you cannot narrow an inherited building list
- That street part names accept a **list**, and the mod ships zero examples of it
- What a palette `char` may legally be, and why emoji break in two separate ways
- An [index of every error message](https://rinkydinkynoble.github.io/the-lost-cities-wiki/troubleshooting/errors/) the mod throws, with causes and fixes

## Layout

| Path | What's in it |
|---|---|
| `docs/` | The wiki itself, MkDocs Material |
| `docs/examples/first-city/` | A complete, working example datapack |
| `docs/examples/validate.py` | Checks a datapack against the rules the wiki documents |
| `.github/workflows/docs.yml` | Strict build gate, then deploy to Pages |

## Running it locally

```bash
pip install -r requirements.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000>.

To check a change the way CI does:

```bash
mkdocs build --strict && python docs/examples/validate.py
```

`--strict` turns any broken internal link into a build failure. The validator checks the example datapack still satisfies every rule the wiki states, which is how the docs and the example are kept from drifting apart.

## Contributing

Corrections are very welcome, especially ones backed by the mod's actual behaviour. If a page is wrong, saying **what you observed** and **which version** is more useful than anything else.

Four pages are marked in-progress in the navigation. Each says what's still missing rather than pretending to be complete.

## Licence

[CC0 1.0](LICENSE). Use it however you like, no attribution required.

Not affiliated with or endorsed by McJty. The Lost Cities is McJty's work; this is an independent guide to it.
