# How It All Connects

!!! tip "TL;DR"
    A dimension points at a **profile** (config). A profile picks a **world style** (datapack). A world style picks **city styles**, which pull in **buildings, parts, and palettes**. Get any name wrong along that chain and nothing crashes, your content just never loads.

Most guides jump straight to writing building JSON. Skip that. None of it does anything until it's wired into a world, and that wiring is what nobody explains.

## The three layers

| Layer | Where it lives | What it does |
|---|---|---|
| **Content** | `data/<namespace>/lostcities/lostcities/` | Your buildings, parts, palettes, city styles, world styles. Loaded as normal datapack JSON. |
| **Profile** | `config/lostcities/profiles/<name>.json` | Picks *one* world style. Also holds ~100 behavior knobs: city frequency, building height, ruin damage, landscape type. |
| **Dimension wiring** | `config/lostcities/common.toml` | One line mapping a dimension to a profile by name. This is the actual switch. |

```toml title="config/lostcities/common.toml"
dimensionsWithProfiles = [
    "lostcities:lostcity=biosphere",
    "lostworlds:abyss=biosphere_caves"
]
```

Format: `<dimension id>=<profile name>`. Change this line and that dimension starts using a different profile, which points at a different world style, which pulls in different city styles, buildings, and palettes.

**Full chain:**

```
dimension → profile (config) → world style name → World Style (datapack) → city styles → buildings, parts, palettes
```

Everything left of "World Style" is config. Everything right of it is the content this wiki's reference section covers.

!!! tip "Fastest way to test"
    Copy an existing profile, change its `worldStyle` field, point `dimensionsWithProfiles` at your copy. No need to touch datapack content just to check the wiring works.

## Profiles: read the built-in ones first

On first launch, Lost Cities writes its 17 built-in profiles to `config/lostcities/profiles/`, then reloads whatever's actually there, including your edits. They're not just examples, they're live files the mod ships and maintains.

- **wasteland** — no water, high ruin chance
- **atlantis** — drowned cities, sea level raised
- **biosphere** — jungle in glass domes on barren land
- **space** — glass bubbles floating in a void

Two profiles (`bio_wasteland`, `void_outside`) are private, they only define what generates *outside* the glass spheres in sphere-based profiles. Build your own spheres profile, and you'll likely want a private outside-profile too.

## Attaching to a world: two options

=== "Dedicated dimension"

    Lost Cities ships `lostcities:lostcity`, its own dimension with a custom chunk generator. Clean if you want cities in a separate world.

=== "Inject into the existing world"

    Two Forge biome modifiers ship with the mod, adding Lost Cities generation as a **feature** to any `#minecraft:is_overworld` biome. No custom dimension needed. This is almost certainly what you want if the goal is "ruined cities in my normal world," not "a separate dimension players travel to."

## Landscape type needs a matching terrain mod

A profile's landscape type (`floating`, `space`, `cavern`, ...) expects matching terrain underneath it, and Lost Cities doesn't generate that terrain itself. That's **Lost Worlds**, a separate mod by the same author. Want anything but the default landscape? Plan on pairing both mods.

## See also

- [Namespaces](namespaces.md) — how names like `worldStyle` actually resolve, and a real gotcha with KubeJS
- [Glossary](../glossary.md) — quick definitions for any term above
