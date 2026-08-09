# City Style Reference

!!! tip "TL;DR"
    `citystyles/<name>.json`. A "theme": picks a [Style](style.md), sets building/street/park/rail behavior, and can inherit from another city style.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `inherit` | no | Name of another city style. Any field left unset here falls back to that one's value. |
| `style` | no | Name of a [Style](style.md) (palette combinator). |
| `stuff_tags` | no | List of tags controlling which [Stuff Objects](stuff.md) can appear. Note the underscore, `"all"` is always included automatically. |
| `explosionchance` | no | Float. |
| `generalblocks` | no | Ironbars/glowstone/leaves/rubbledirt override chars. |
| `buildingsettings` | no | `minfloors`, `mincellars`, `maxfloors`, `maxcellars`, `buildingchance`. Overrides the matching [Profile](profile.md) fields. |
| `corridorblocks` | no | `corridorchance`, roof/glass chars. |
| `parkblocks` | no | `parkchance`, `avoidfoliage`, `parkborder`, `parkelevation`, `parkstreetthreshold`, elevation/grass chars. |
| `railblocks` | no | `railmain` char. |
| `sphereblocks` | no | Inner/border/glass chars for city spheres. |
| `streetblocks` | no | `fountainchance`, `frontchance`, `width`, street/border/wall chars, plus a nested `parts` block for street part-name overrides. |
| `selectors` | no | Eight weighted lists: `buildings`, `bridges`, `parks`, `fountains`, `stairs`, `fronts`, `raildungeons`, `multibuildings`. |

!!! warning "The naming isn't consistent"
    Five of these use a `...blocks` suffix (`generalblocks`, `corridorblocks`, `parkblocks`, `railblocks`, `sphereblocks`, `streetblocks`), one uses `...settings` (`buildingsettings`). Not a typo on this page, that's genuinely how the mod names them. Copy exact key names, don't guess by pattern.

!!! note "railmain resolves once per chunk, not once per block"
    If `railmain` points at a weighted [Palette](palette.md) entry (`variant` or `blocks`) rather than a fixed `block`, the mod picks one random result and reuses it for the entire rail-bed strip in that chunk, it doesn't re-roll per block. On a long straight railway spanning many chunks, this shows up as solid-colored 16-block strips rather than block-by-block noise, since each chunk gets its own independent roll. The mod's own default city style points `railmain` at the `stonebrick` variant (mostly plain stone bricks, small chance of cracked or mossy), so most chunks look identical and occasionally a whole chunk-length strip stands out. This is how the resolution works, not something to work around unless you want every rail chunk to look uniform (use a fixed `block` instead of a weighted one).

## Inheritance

```json title="citystyle_desert.json"
{
  "inherit": "citystyle_standard",
  "generalblocks": { "leaves": "α" }
}
```

Everything except `leaves` comes from `citystyle_standard`. Only what you set here overrides it.

## See also

- [Profile Reference](profile.md) for what these fields override
- [Stuff Object Reference](stuff.md) for `stuff_tags`
- [The Content Model](../getting-started/content-model.md)
- [Glossary](../glossary.md)
