---
claims: verified
---

# Configuration Reference

!!! tip "TL;DR"
    Lost Cities settings live in three places, and the file everyone reaches for first holds only three keys. Eleven more sit in a **per-world** file inside the save. Both use a section called `[profiles]`, whatever the comment above it says. [game test](../examples/claim-tests.md#cfg-1){.v .v-g} [code review](../examples/claim-tests.md#cfg-1){.v .v-c}

## The three places

| File | Scope | Holds |
|---|---|---|
| `config/lostcities/common.toml` | The whole install | 3 keys: the dimension wiring and two heightmap settings |
| `<world>/serverconfig/lostcities-server.toml` | **One world** | 11 keys: structure avoidance, caching, the teleporter bed |
| `config/lostcities/profiles/<name>.json` | The whole install | Profiles, rewritten on every launch |
[game test](../examples/claim-tests.md#cfg-1){.v .v-g} [code review](../examples/claim-tests.md#cfg-1){.v .v-c}

A setting edited in the wrong one of these does nothing and says nothing. `avoidVillages` in `common.toml` is ignored, because that key belongs to the world file, and Forge has no opinion about keys it was not expecting. [code review](../examples/claim-tests.md#cfg-1){.v .v-c}

!!! danger "The section is `[profiles]` in both files"
    Every key in both `.toml` files sits under `[profiles]`. The line above it reads `#General settings`, which is a **comment**, not a section name. [game test](../examples/claim-tests.md#cfg-2){.v .v-g} [code review](../examples/claim-tests.md#cfg-2){.v .v-c}

    Writing `[general]` instead does not produce an error. Forge finds the file does not match its spec and **rewrites the whole file to defaults**, which points `lostcities:lostcity` back at the `biosphere` profile. The symptom is a world that generates the wrong thing, not a config error. [game test](../examples/claim-tests.md#cfg-2){.v .v-g}

## `common.toml`

```toml title="config/lostcities/common.toml, at defaults"
#General settings
[profiles]
	dimensionsWithProfiles = ["lostcities:lostcity=biosphere", "lostworlds:abyss=biosphere_caves"]
	optimizedHeightmap = false
	heightSampleSize = 3
```

| Key | Default | Meaning |
|---|---|---|
| `dimensionsWithProfiles` | the two entries above | A list of `<dimension id>=<profile name>`. Every entry wires one dimension to one profile, and a dimension absent from the list generates no city |
| `optimizedHeightmap` | `false` | `true` swaps in a cheaper heightmap algorithm. The mod's own comment warns it may disagree with other terrain mods |
| `heightSampleSize` | `3` | How many chunks apart the heightmap is sampled. `1` samples every chunk, higher is faster and coarser |
[code review](../examples/claim-tests.md#cfg-3){.v .v-c}

!!! note "`heightSampleSize` does not default to what its comment says"
    The generated comment reads `Default is 1 which means every chunk is sampled`. The default written into the file is `3`. The comment describes the value's meaning, not the value the mod ships. [game test](../examples/claim-tests.md#cfg-3){.v .v-g} [code review](../examples/claim-tests.md#cfg-3){.v .v-c}

### `dimensionsWithProfiles` in detail

The left side is a dimension id, a full resource location. The right side is a profile name: a bare map key taken from a file name, **never** a resource location, so it takes no namespace and is matched case-sensitively. [code review](../examples/claim-tests.md#cfg-4){.v .v-c}

```toml
dimensionsWithProfiles = ["lostcities:lostcity=mycity"]
```

Two ways to get it wrong, and neither stops the game: [code review](../examples/claim-tests.md#cfg-4){.v .v-c}

| Mistake | Logged | Result |
|---|---|---|
| No `=` in the entry | `Bad format for config value: '<entry>'!` | The entry is skipped |
| A profile name no file provides | `Cannot find profile: <name> for dimension <dim>!` | That dimension is left without a profile |
[code review](../examples/claim-tests.md#cfg-4){.v .v-c}

!!! warning "Picking a profile on the world creation screen wires the overworld, not `lostcities:lostcity`"
    The **Cities** button on the world creation screen makes the **overworld** the Lost Cities world. `dimensionsWithProfiles` wires `lostcities:lostcity` instead. A [predefined city](predefined.md) pinned to the wrong one of those appears not to generate at all. [game test](../examples/claim-tests.md#cfg-5){.v .v-g}

## `lostcities-server.toml`

This file is written into the **save**, at `<world>/serverconfig/lostcities-server.toml`, so every world gets its own copy and a change to one world does not reach another. A new world starts from the defaults, not from the world you last edited. [game test](../examples/claim-tests.md#cfg-6){.v .v-g} [code review](../examples/claim-tests.md#cfg-6){.v .v-c}

| Key | Default | Meaning |
|---|---|---|
| `avoidStructures` | `mansion`, `jungle_pyramid`, `desert_pyramid`, `igloo`, `swamp_huts`, `pillager_outpost` | Structure ids a city will not be generated on top of |
| `avoidStructuresAdjacent` | `false` | `true` extends `avoidStructures` to the eight chunks around each one |
| `avoidVillages` | `true` | `true` keeps cities out of chunks holding a village |
| `avoidVillagesAdjacent` | `false` | `true` extends that to the chunks around a village |
| `avoidFlattening` | `true` | `true` leaves terrain unflattened around a spot a city was kept off, so the avoided structure is not left on a shelf |
| `cacheCleanupSeconds` | `300` | How long cached chunk data is kept. Range 1 to 86400 |
| `todoQueueSize` | `20` | Size of the generator's deferred-work queues. Range 1 to 100000 |
| `forceSaplingGrowth` | `true` | `true` grows saplings into trees during generation, at a cost |
| `specialBedBlock` | `minecraft:diamond_block` | The block that, placed under a bed, makes it a teleporter bed |
| `selectedProfile` | `""` | Written by the world creation screen. Not meant to be edited by hand |
| `selectedCustomJson` | `""` | Written by the customise screen. Not meant to be edited by hand |
[game test](../examples/claim-tests.md#cfg-6){.v .v-g} [code review](../examples/claim-tests.md#cfg-6){.v .v-c}

## The profiles folder

`config/lostcities/profiles/` is not a folder you own. On every launch the mod builds its standard profiles in code, **writes every one of them to disk**, and only then reads the folder back. [code review](../examples/claim-tests.md#cfg-7){.v .v-c}

| Question | Answer |
|---|---|
| Can I delete a default profile? | The file, yes. The profile, no. It is built in code and the file is written again on the next launch |
| Can I edit a default profile? | The edit survives until the next launch, then it is overwritten |
| Which one is exempt? | `customized`, and only that one. It is skipped by the write loop |
| Are my own profiles safe? | Yes. The write loop only touches profiles the mod itself defines |
[code review](../examples/claim-tests.md#cfg-7){.v .v-c}

To change a default, copy it to a new name and edit the copy. That is what the `__readonly__` note in each shipped file is telling you, and it is accurate: those files really are read-only in effect. <!-- noclaim -->

### `__readonly__`

Every profile the mod writes carries this key: [code review](../examples/claim-tests.md#cfg-8){.v .v-c}

```json
{
  "__readonly__": "This profile is read only and cannot be modified! If you want to make a new profile based on this then you can make a copy to a new name",
  "lostcity": { }
}
```

It is written and never read. Nothing in the mod looks the key up, and a profile is not made read-only by having it or writable by losing it. In a copy you make, keeping it and deleting it are the same thing, and deleting it is tidier because the sentence is no longer true of your file. [code review](../examples/claim-tests.md#cfg-8){.v .v-c}

## See also

- [Profile Reference](profile.md) for what goes inside a profile file
- [Namespaces](../getting-started/namespaces.md) for why a profile name takes no namespace while `worldStyle` does
- [How It All Connects](../getting-started/how-it-connects.md) <!-- noclaim -->
