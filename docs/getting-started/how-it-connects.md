# How It All Connects

Every guide for Lost Cities jumps straight into writing JSON for buildings and palettes. That's the wrong place to start. None of that content does anything until it's wired into a running world, and the wiring is the part nobody explains.

There are three separate layers involved, and they talk to each other through plain names, not through anything Minecraft enforces for you. Get a name wrong anywhere in this chain and nothing errors, your content just quietly never loads.

## The three layers

**1. Content.** Your buildings, parts, palettes, city styles, and world styles, written as JSON under `data/<namespace>/lostcities/lostcities/`. This is what most people mean when they say "custom city," and it's what most of this wiki's reference section covers. It's loaded through Minecraft's regular datapack registry system, the same mechanism vanilla uses for recipes and loot tables.

**2. Profile.** A profile is a separate JSON file at `config/lostcities/profiles/<name>.json`. It does two things: it names exactly one world style to use, and it carries around a hundred generation-behavior settings that live outside the datapack system entirely, things like how often cities spawn, how tall buildings get, how much ruin damage there is, and what kind of landscape it is (normal ground, floating islands, glass spheres in a void, and so on).

**3. Dimension wiring.** A single line in `config/lostcities/common.toml` maps a dimension to a profile by name:

```toml
dimensionsWithProfiles = [
    "lostcities:lostcity=biosphere",
    "lostworlds:abyss=biosphere_caves"
]
```

The format is `<dimension id>=<profile name>`. This is the actual switch. Change this line, and a dimension starts using a different profile, which points at a different world style, which pulls in a different set of city styles, buildings, and palettes.

So the full chain, in order, looks like this:

```
dimension  →  profile (config)  →  worldStyle name  →  WorldStyle (datapack)  →  city style selection  →  buildings, parts, palettes
```

Everything downstream of "WorldStyle" is the content layer this wiki's reference section documents in detail. Everything upstream of it is config, and it's just as necessary.

## Profiles are worth reading before you write your own

On first launch, Lost Cities writes out its built-in profiles to `config/lostcities/profiles/` and then reloads whatever's actually sitting in that folder, including your edits. That means the shipped profiles aren't just examples, they're the live files the mod ships and maintains. Seventeen of them exist, covering things like a wasteland with no water, a drowned atlantis-style city with the sea level raised, glass biosphere domes, and a deliberately rare-cities mode. Before writing a profile from scratch, it's worth opening a few of these and seeing what a complete one actually looks like.

Two profiles you'll see referenced (`bio_wasteland`, `void_outside`) aren't meant to be selected directly. They're marked private and exist only to define what generates *outside* the glass spheres in the sphere-based profiles. If you build a spheres-style profile of your own, you'll likely want a private outside-profile too.

!!! tip "The setting you actually want to change first"
    If you already have a `worldStyle` you want to test, the fastest path is: copy an existing profile, change its `worldStyle` field to your world style's name, then point `dimensionsWithProfiles` at your copy. You don't need to touch the datapack content at all to verify the wiring works.

## Two ways to attach city generation to a world

Lost Cities ships a dedicated dimension (`lostcities:lostcity`) that uses its own custom chunk generator. That's the cleanest option if you want cities in their own separate world.

But if you want city generation layered into your existing overworld instead, which is likely what you actually want for a modpack, Lost Cities also ships two Forge biome modifiers that inject its generation as a *feature* into any biome tagged `#minecraft:is_overworld`. No custom dimension required. This is almost certainly the mechanism you'd reach for if your goal is "put ruined cities into the normal world," rather than "give players a separate Lost Cities dimension to travel to."

## About landscape types

A profile's landscape type (`floating`, `space`, `cavern`, and so on) controls more than city generation, it expects a matching terrain generator underneath it. Several of the built-in profiles say as much directly: the `floating` profile expects floating-island terrain, `space` expects a void, `cavern` expects an underground world. Lost Cities does not generate that base terrain itself. That comes from **Lost Worlds**, a separate mod by the same author. If you want anything other than the default landscape, plan on pairing the two.

## Where to go next

Once you understand this page, the rest of the wiki is mostly reference material you'll come back to as needed rather than read start to finish. The content model page (coming soon) walks through how a world style, city style, and building actually compose together.
