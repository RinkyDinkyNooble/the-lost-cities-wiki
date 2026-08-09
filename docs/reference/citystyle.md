# City Style Reference

!!! tip "TL;DR"
    `citystyles/<name>.json`. A "theme": picks a [Style](style.md), sets building/street/park/rail behavior, and can inherit from another city style. **Inheritance behaves differently for selectors than for everything else**, see [Inheritance](#inheritance).

## Fields

| Key | Required | Meaning |
|---|---|---|
| `inherit` | no | Name of another city style to build on. See [Inheritance](#inheritance). |
| `style` | no | Name of a [Style](style.md) (palette combinator). This is what decides how the city *looks*. |
| `stuff_tags` | no | List of tags controlling which [Stuff Objects](stuff.md) can appear. Note the underscore, `"all"` is always included automatically. |
| `explosionchance` | no | Float. |
| `generalblocks` | no | Ironbars/glowstone/leaves/rubbledirt override chars. |
| `buildingsettings` | no | `minfloors`, `mincellars`, `maxfloors`, `maxcellars`, `buildingchance`. Overrides the matching [Profile](profile.md) fields, and is in turn narrowed by each [Building](building.md)'s own bounds. |
| `corridorblocks` | no | `corridorchance`, roof/glass chars. |
| `parkblocks` | no | `parkchance`, `avoidfoliage`, `parkborder`, `parkelevation`, `parkstreetthreshold`, elevation/grass chars. |
| `railblocks` | no | `railmain` char. |
| `sphereblocks` | no | Inner/border/glass chars for city spheres. |
| `streetblocks` | no | `fountainchance`, `frontchance`, `width`, street/border/wall chars, plus a nested `parts` block for [street part-name overrides](../concepts/infrastructure-parts.md). |
| `selectors` | no | Eight weighted lists: `buildings`, `bridges`, `parks`, `fountains`, `stairs`, `fronts`, `raildungeons`, `multibuildings`. |

!!! warning "The naming isn't consistent"
    Five of these use a `...blocks` suffix (`generalblocks`, `corridorblocks`, `parkblocks`, `railblocks`, `sphereblocks`, `streetblocks`), one uses `...settings` (`buildingsettings`). Not a typo on this page, that's genuinely how the mod names them. Copy exact key names, don't guess by pattern.

!!! note "railmain resolves once per chunk, not once per block"
    If `railmain` points at a weighted [Palette](palette.md) entry (`variant` or `blocks`) rather than a fixed `block`, the mod picks one random result and reuses it for the entire rail-bed strip in that chunk, it doesn't re-roll per block. On a long straight railway spanning many chunks, this shows up as solid-colored 16-block strips rather than block-by-block noise, since each chunk gets its own independent roll. The mod's own default city style points `railmain` at the `stonebrick` variant (mostly plain stone bricks, small chance of cracked or mossy), so most chunks look identical and occasionally a whole chunk-length strip stands out. This is how the resolution works, not something to work around unless you want every rail chunk to look uniform (use a fixed `block` instead of a weighted one).

## Inheritance

`inherit` names one other city style. Chains work: a style can inherit from a style that inherits from another, and the whole chain resolves.

**The important part: there are two completely different merge behaviours depending on the field.**

| Field group | Behaviour |
|---|---|
| `selectors` (all eight lists) and `stuff_tags` | **Additive.** The parent's entries are appended to yours. You end up with both. |
| Everything else (`style`, all the `...blocks` chars, `buildingsettings`, all the chances) | **Child wins per field.** Any individual value you don't set is taken from the parent. |
| `streetblocks.parts` | **All or nothing**, see the warning below. |

### Selectors accumulate, they do not replace

This surprises nearly everyone. If a parent lists eight buildings and your child lists three, the resulting pool is **eleven entries**, not three. There is no way to remove or narrow a parent's selector list, only to add to it.

Worse, if your three entries name buildings the parent also names, those buildings appear **twice** in the pool, so their effective weight is the sum of both factors, not your value.

```json title="Parent"
{ "selectors": { "buildings": [
  { "factor": 1.0, "value": "house" },
  { "factor": 1.0, "value": "tower" }
] } }
```
```json title="Child, inheriting the above"
{ "inherit": "parent", "selectors": { "buildings": [
  { "factor": 5.0, "value": "house" }
] } }
```
The child's pool is `house` at 5.0, `house` at 1.0, and `tower` at 1.0. `house` is effectively weight 6.0 against `tower`'s 1.0, not 5-to-1.

**If you need a genuinely different building list, don't inherit from a style that has one.** Inherit from a minimal base (or nothing) and declare the full list yourself.

!!! warning "`streetblocks.parts` is the exception: it's all-or-nothing"
    Every other nested field merges key by key, so setting `streetblocks.border` alone keeps the parent's `streetblocks.wall`. **`streetblocks.parts` doesn't work that way.** Writing any `parts` block at all, even one with a single key, discards the parent's entire `parts` block. Keys you didn't restate fall back to the mod's hardcoded defaults, not the parent's values. Restate every key you want to keep.

## How the shipped city styles are organized

The five city styles the mod ships are worth reading before writing your own, because the layering is deliberate:

```
citystyle_config          ← only { "streetblocks": { "width": 8 } }
      ↑
citystyle_common          ← all block characters, all eight selectors, stuff_tags
      ↑           ↑              ↑
citystyle_    citystyle_    citystyle_border
standard      desert        (adds buildingsettings + its own selectors)
```

And the two most-used ones are two lines each:

```json title="citystyle_standard.json, in full"
{
  "style": "standard",
  "inherit": "citystyle_common"
}
```
```json title="citystyle_desert.json, in full"
{
  "style": "desert",
  "inherit": "citystyle_common"
}
```

Three things worth taking from this:

**1. A "desert city" is not made of different buildings.** `citystyle_standard` and `citystyle_desert` differ by exactly one field: which [Style](style.md) they point at. Same buildings, same street rules, same selectors, different palettes. The visual identity of a city comes from the palette layer, not from authoring a separate set of buildings. If you want a themed city, your first move should be a new Style plus palettes, not new buildings.

**2. `citystyle_config` exists to be overridden.** It sits at the bottom of the chain and contains one setting. Its whole purpose is to give modpack authors a tiny file to override (via the [`lostcities` namespace](../getting-started/namespaces.md)) that changes street width everywhere without touching or copying anything else. It's a deliberate hook, not an accident, and it's a pattern worth copying: put the knobs you expect people to tweak in their own small file at the base of the chain.

**3. `citystyle_border` is what city edges use.** It inherits `citystyle_common` but adds `buildingsettings` with `maxfloors: 1`, `maxcellars: 1`, `buildingchance: 0.2`, low, sparse buildings. This is the style paired with the [`cityStyleThreshold`/`cityStyleAlternative`](profile.md#cities) profile fields to fade a dense downtown out into low outskirts. If you want that effect, this is the working example to copy.

Note that `citystyle_border` also restates all the block characters it would have inherited anyway. That's harmless duplication, not something you need to imitate.

### Writing your own

The practical decision is what to inherit from:

| Goal | Approach |
|---|---|
| Retheme an existing city (different materials, same content) | `inherit: "citystyle_common"`, set `style` to your own [Style](style.md). Two lines, exactly like `citystyle_desert`. |
| Add a few buildings on top of the defaults | `inherit: "citystyle_common"` and list only your additions in `selectors.buildings`, they get appended to the built-in ones. |
| Use *only* your own buildings | **Don't inherit from `citystyle_common`.** Its selectors would be merged in and you'd keep getting vanilla buildings. Declare everything yourself. |
| Change only street width globally | Override `citystyle_config` in the `lostcities` namespace. |

## Example: minimal retheme

```json title="citystyle_wasteland.json"
{
  "inherit": "citystyle_common",
  "style": "mypack:wasteland",
  "buildingsettings": {
    "buildingchance": 0.5
  }
}
```

Everything comes from `citystyle_common` except the palette Style and the building density. Note `buildingsettings` merges per field here, so setting only `buildingchance` leaves the parent's floor and cellar bounds intact.

## See also

- [Style Reference](style.md) for the palette layer that gives a city style its look
- [Profile Reference](profile.md) for what these fields override
- [Building Reference](building.md) for the bounds that narrow `buildingsettings` further
- [Streets, Highways, Rails & Monorails](../concepts/infrastructure-parts.md) for `streetblocks.parts`
- [Stuff Object Reference](stuff.md) for `stuff_tags`
- [Glossary](../glossary.md)
