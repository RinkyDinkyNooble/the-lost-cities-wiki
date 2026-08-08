# City Style Reference

!!! tip "TL;DR"
    `citystyles/<name>.json`. A "theme": picks a [Style](style.md), sets building/street/park/rail behavior, and can inherit from another city style.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `inherit` | no | Name of another city style. Any field left unset here falls back to that one's value. |
| `style` | no | Name of a [Style](style.md) (palette combinator). |
| `stuff_tags` | no | List of tags controlling which StuffObjects can appear (reference page coming soon). Note the underscore, `"all"` is always included automatically. |
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
- [The Content Model](../getting-started/content-model.md)
- [Glossary](../glossary.md)
