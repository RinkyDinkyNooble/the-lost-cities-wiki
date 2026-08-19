---
claims: verified
---

# Streets, Highways, Rails & Monorails

!!! tip "TL;DR"
    Streets, highways, rails and monorails each expect a set of default **part names** to exist. Any of those names can point at a custom part instead. Streets, highways and railways also accept a **list** of parts, sampled at random per placement. Monorails accept one name only.

This is a contract, not a suggestion. If a part named `street_full` does not exist and nothing overrides that name, that piece of infrastructure does not generate. [game test](../examples/claim-tests.md#cty-9){.v .v-g}

## One shape can have several parts

The single most common assumption is that each street shape is locked to exactly one part. It is not. **Streets, highways, and railways accept either a single name or a list of names**, and the mod picks one at random each time it places that piece: [game test](../examples/claim-tests.md#cty-2){.v .v-g}

```json title="Both forms are valid in the same object"
{
  "streetblocks": {
    "parts": {
      "full":     ["street_full", "mypack:street_full_cracked", "mypack:street_full_grassy"],
      "straight": "mypack:street_straight_wide"
    }
  }
}
```

| Category | Multiple variants? | How one is chosen | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|
| Streets | **Yes**, list or single string | Uniform random, every entry equally likely |
| Highways | **Yes**, list or single string | Uniform random |
| Railways | **Yes**, list or single string | Uniform random |
| Monorails | **No**, single string only | n/a |

Passing a list to a monorail key is a datapack load error, not a silent fallback. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! note "There is no weighting"
    Unlike [building selectors](../reference/citystyle.md) or [Conditions](../reference/condition.md), these lists have no `factor` key. Every entry in the list is equally likely. If you want one variant to be rare, you cannot express that here, list it once among many common ones, or use a [Variant](../reference/variant.md) inside the palette instead (see [below](#varying-the-material-instead-of-the-part)).

Adjacent chunks roll independently, with no attempt to match neighbours. Two touching straight-street chunks can and often will pick different variants, so **variants need to line up seamlessly at chunk edges** or the seams will be obvious. Do not count on predicting which variant a given chunk gets before you visit it; once a chunk is generated it is saved, so it will not change afterward. [game test](../examples/claim-tests.md#cty-2){.v .v-g}

## Where each override goes

The two families live in **different files**, which is easy to get wrong: [code review](../examples/claim-tests.md#ref-1){.v .v-c}

=== "Streets → City Style"

    ```json title="citystyles/<name>.json"
    {
      "streetblocks": {
        "parts": {
          "full":     ["street_full"],
          "straight": ["street_straight"],
          "end":      ["street_end"],
          "bend":     ["street_bend"],
          "t":        ["street_t"],
          "none":     ["street_none"],
          "all":      ["street_all"]
        }
      }
    }
    ```

    Because streets are a City Style property, and a [World Style](../reference/worldstyle.md) can pick city styles per biome, **streets can vary by biome**: give `citystyle_desert` its own `streetblocks.parts` and desert cities get different roads. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

=== "Highways, rails, monorails → World Style"

    ```json title="worldstyles/<name>.json"
    {
      "outsidestyle": "outside",
      "citystyles": [ ... ],
      "parts": {
        "highways": {
          "tunnel": ["highway_tunnel", "mypack:highway_tunnel_lit"],
          "open":   "highway_open"
        },
        "railways": {
          "railshorizontal": ["rails_horizontal", "mypack:rails_horizontal_broken"]
        },
        "monorails": {
          "both": "mypack:monorails_both_neon"
        }
      }
    }
    ```

    These are one set per world style, resolved with no biome input, so **highways, rails, and monorails cannot vary by biome**. The only way to differentiate them is a separate world style entirely. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## The part name keys

Any key you leave out keeps its default part name. The keys are not always spelled like the part names they default to. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

### Streets

| Key | Default part | Used when | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|
| `full` | `street_full` | **Never. See below.** |
| `straight` | `street_straight` | 2 connections, opposite sides |
| `bend` | `street_bend` | 2 connections, adjacent sides |
| `t` | `street_t` | 3 connections |
| `all` | `street_all` | 4 connections (crossroads) |
| `end` | `street_end` | 1 connection |
| `none` | `street_none` | 0 connections |

The key is literally `"t"`, not `"tsplit"`. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! danger "`full` never generates. Setting it does nothing."
    A street chunk is assigned one of 3 street types. `PARK` is chosen by
    `parkchance`. Otherwise the mod picks at random from the remaining types:

    ```
    streetType = StreetType.values()[ random.nextInt(0, StreetType.values().length - 2) ]
    ```

    `StreetType` has 3 constants, `NORMAL`, `FULL` and `PARK`, so this is
    `nextInt(0, 1)`. The upper bound is exclusive, so the only value it can return
    is `0`, which is `NORMAL`. **`FULL` is never assigned anywhere in the mod.** [game test](../examples/claim-tests.md#cty-4){.v .v-g}

    The 6 other keys above are reached through the connection count and work
    normally. Only `full` is unreachable. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    Verified unreachable in 7.4.12, 7.5.1, 8.4.1, 9.5.1 and 10.0.1. The subtraction
    looks like it should be 1 rather than 2, so this reads as an off-by-one in the
    mod, not a design decision. [code review](../examples/claim-tests.md#key-1){.v .v-c}

    Confirmed in game: a city style whose `full` key pointed at 2 clearly marked
    parts produced neither marker anywhere across a world of streets. [game test](../examples/claim-tests.md#cty-4){.v .v-g}

### Highways

| Key | Default part | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|
| `tunnel` | `highway_tunnel` |
| `open` | `highway_open` |
| `bridge` | `highway_bridge` |
| `tunnel_bi` | `highway_tunnel_bi` |
| `open_bi` | `highway_open_bi` |
| `bridge_bi` | `highway_bridge_bi` |

`_bi` ("bidirectional") is used where an X highway and a Z highway meet at the same level. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### Railways

Sixteen keys. Note they are all lowercase with no separators, while the default part names they map to are snake_case, an easy source of silent typos. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Default part | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|
| `stationunderground` | `station_underground` |
| `stationopen` | `station_open` |
| `stationopenroof` | `station_openroof` |
| `stationundergroundstairs` | `station_underground_stairs` |
| `stationstaircase` | `station_staircase` |
| `stationstaircasesurface` | `station_staircase_surface` |
| `railshorizontal` | `rails_horizontal` |
| `railshorizontalend` | `rails_horizontal_end` |
| `railshorizontalwater` | `rails_horizontal_water` |
| `railsvertical` | `rails_vertical` |
| `railsverticalwater` | `rails_vertical_water` |
| `rails3split` | `rails_3split` |
| `railsbend` | `rails_bend` |
| `railsflat` | `rails_flat` |
| `railsdown1` | `rails_down1` |
| `railsdown2` | `rails_down2` |

A surface station gets one extra step. The mod flips a fair coin between the `stationopen` and `stationopenroof` lists, then draws a variant at random from whichever list won. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### Monorails

| Key | Default part | List allowed | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|
| `both` | `monorails_both` | No |
| `vertical` | `monorails_vertical` | No |
| `station` | `monorails_station` | No |

## Rules your custom parts must follow

!!! danger "A typo in a part name fails in two very different ways"
    | Category | If the named part does not exist |
    |---|---|
    | **Streets** | The mod logs a warning, and **that chunk simply gets no street layer**. There is no crash and no fallback, just a gap in the road. In a list of 3 where one name is wrong, roughly 1 in 3 of those street chunks silently comes out broken. |
    | **Highways, railways, monorails** | The mod throws and world generation stops. Loud, but at least obvious. |

    There is never a fallback to the default part name. Check your spelling, and remember that a bare name means `lostcities:<name>`, so your own parts need your namespace. See [Namespaces](../getting-started/namespaces.md). [game test](../examples/claim-tests.md#cty-9){.v .v-g}

!!! warning "The silent warn-and-skip is wider than streets"
    Streets are the most visible case. The mod uses the same warn-and-skip lookup for every one of these:

    fountains, parks, stairs, rail dungeons, building fronts, and a city sphere's `centerpart`. [game test](../examples/claim-tests.md#cty-7){.v .v-g}

    A wrong name in any of them produces `Cannot find '<name>' in minecraft:root!` as a log **warning** and then nothing at that spot. If a park or a fountain never appears and no error is raised, check the log before you check your selectors. [game test](../examples/claim-tests.md#cty-6){.v .v-g}

**An infrastructure part must be exactly 16×16.** A street, highway, railway or monorail part fills its whole chunk, so anything else leaves gaps or corrupts. Larger than 16 is the dangerous case: a write past column 15 wraps back into the same chunk instead of spilling into the next one. All 32 default infrastructure parts are 16×16. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

This is a rule about these four families, not about parts in general. A [building front](../reference/citystyle.md#front-parts-are-deliberately-not-16-by-16) is deliberately a narrow strip, and the mod ships three of them at 2×16 and 3×16. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

**Author variants in the same orientation as the part they replace.** The mod picks the rotation from the road layout, not from your part, so a `street_bend` variant gets rotated by the same rule the built-in one does. If your bend is drawn facing a different way than the original, it will be rotated wrongly at three quarters of the corners in your world. `full`, `none`, and `all` are never rotated, so those can safely be asymmetric. [unverified](../examples/claim-tests.md#ref-3){.v .v-u}

**Reuse the palette characters the category expects.** A highway part expects its `support` character, and a rail part expects the rail palette. A part that references a character its palette does not define throws during generation. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

For streets, the character that matters is the city style's `street`. Its `streetbase` and `streetvariant` neighbours look like they belong in the same list, but neither is read during generation. See [City Style](../reference/citystyle.md#keys). What a street is actually built from is the characters inside the street **part**, resolved against the merged palette like any other part. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Varying the material instead of the part

If the goal is "my streets look too repetitive," authoring several near-identical parts is usually the harder path. The [Style](../reference/style.md) and [Variant](../reference/variant.md) systems already randomize *blocks* underneath a single part: <!-- noclaim -->

```json title="variants/blackstone.json (shipped with the mod)"
{
  "blocks": [
    { "random": 32,   "block": "minecraft:polished_blackstone_bricks" },
    { "random": 32,   "block": "minecraft:cracked_polished_blackstone_bricks" },
    { "random": 1000, "block": "minecraft:polished_blackstone" }
  ]
}
```

That gives per-block variation with weighting, which flat part lists cannot do, and it costs one file instead of several parts. Use part lists when the *shape* differs (a roundabout, a collapsed section, a checkpoint), and variants when only the *material* differs. [game test](../examples/claim-tests.md#pal-3){.v .v-g}

!!! note "The mod ships zero examples of the list form"
    None of the built-in world styles or city styles override these part names at all, they all run on exactly one variant per slot. The feature is real and present in the code, it just has no demonstration in the default content, which is why it is widely assumed not to exist.

## An inheritance trap for street parts

City style `inherit` handles `streetblocks.parts` as one unit: writing **any** `parts` block at all, even a partial one, stops the parent's `parts` from being inherited. Keys you did not list fall back to the hardcoded defaults, not to the parent's overrides. [game test](../examples/claim-tests.md#cty-3){.v .v-g}

If a parent city style overrides `full` and `bend`, and your child overrides only `full`, the child's `bend` reverts to the built-in `street_bend`, it does not keep the parent's. Restate every key you want to keep. See [City Style: Inheritance](../reference/citystyle.md#inheritance). [game test](../examples/claim-tests.md#cty-3){.v .v-g}

## See also

- [World Style Reference](../reference/worldstyle.md)
- [City Style Reference](../reference/citystyle.md)
- [Building Part Reference](../reference/part.md) <!-- noclaim -->
