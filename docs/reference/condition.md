---
claims: verified
---

# Condition Reference

!!! tip "TL;DR"
    `conditions/<name>.json` holds a weighted table that picks a value based on where you are. A [Building](building.md) reuses the same test keys on its part list, so this page covers both.

!!! note "`belowpart` needs 7.4.12"
    The key was added in 7.4.12 and is absent in 8.2.2. See
    [Key availability](../versions/key-availability.md).

## File shape

```json
{
  "values": [
    { "factor": 1.0, "value": "some_string", "inbiome": "minecraft:desert" }
  ]
}
```

The mod collects every entry whose tests pass, then picks one `value` at random. `factor` weights that pick. If no entry matches, the condition returns nothing. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! note "Weighted here, unweighted in a Building"
    A Building reuses these test keys but not the weighting. A Condition entry requires `factor` and weights the pick by it. A Building part entry has no `factor` key at all, so every matching part is equally likely.

## The shared test keys

A Condition entry and a Building part entry accept the same 13 test keys. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Type | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|
| `top` | bool | If `true`, matches only when the floor index is at or above the building's top floor. If `false`, matches every other floor. |
| `ground` | bool | If `true`, matches only floor index 0. If `false`, matches every other floor. |
| `cellar` | bool | If `true`, matches only a negative floor index. If `false`, matches index 0 and above. |
| `isbuilding` | bool | If `true`, matches only where a building stands. If `false`, matches only where none does. |
| `issphere` | bool | If `true`, matches only inside a city sphere. If `false`, matches only outside one. |
| `floor` | int | Matches when the floor index equals this number exactly. |
| `chunkx` | int | Matches when the absolute chunk X coordinate equals this number. |
| `chunkz` | int | Matches when the absolute chunk Z coordinate equals this number. |
| `range` | string | Matches when the floor index falls between the two numbers, including both ends. |
| `inpart` | string or list | Matches when the current part name is in this set. **Never matches from a Building's `parts` list.** See below. |
| `belowpart` | string or list | **Does not work.** It tests the current part, not the one below. See below. |
| `inbuilding` | string or list | Matches when the current building name is in this set. |
| `inbiome` | string or list | Matches when the current biome is in this set. |

Every key is optional. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

**Setting several keys on one entry means all of them must pass.** The mod chains tests with a logical AND and never with an OR. To express "either A or B", write two separate entries. [game test](../examples/claim-tests.md#cnd-1){.v .v-g}

An entry with no test keys always matches. That is the standard way to write a fallback. An unconditioned entry guarantees that something always matches, which is what prevents the [missing-part failure](building.md#floor-coverage-the-most-common-failure) on a building. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## `belowpart` and `inpart` in a Building

!!! bug "`belowpart` tests the current part, not the part below it"
    `ConditionContext` is given the part below and stores it in a field called
    `belowPart`. **That field has no accessor and is never read.** The predicate the
    mod builds for `belowpart` calls `getPart()`, which is the same method the
    `inpart` predicate calls. The two tests are identical.

    So `belowpart` is not a weaker version of what this page used to describe. It is
    `inpart` under a second name. [game test](../examples/claim-tests.md#cnd-4){.v .v-g} [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    Present in **7.4.12, 7.5.1, 8.4.1, 9.5.1 and 10.0.1**. Version 8.2.2 does not
    declare the key at all, which is the only release where writing it is an error
    rather than a silent no-op. [code review](../examples/claim-tests.md#key-1){.v .v-c}

    Confirmed in game on 7.4.12, twice. A three-part chain selected by what sits
    beneath each floor failed every chunk. A second, non-failing probe then measured
    the difference directly: a two-level building whose first entry is gated
    `belowpart: "<none>"` and whose second is gated on the part below it came out
    **gold on both levels with no diamond at all**, which is only possible if
    `belowpart` is reading the current part. [game test](../examples/claim-tests.md#cnd-4){.v .v-g}

There is a second, separate problem, and it applies to `inpart` too. [game test](../examples/claim-tests.md#cnd-5){.v .v-g}

When the mod fills a building's floors, the `ConditionContext` it builds is given
the literal string `<none>` as the current part. It has to be: it is deciding which
part to use, so there is no current part yet. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| Where the condition is evaluated | What `inpart` and `belowpart` see [game test](../examples/claim-tests.md#cnd-5){.v .v-g} |
|---|---|
| A [Building](building.md)'s `parts` list | Always `<none>` |
| A Condition named by a palette's `loot` or `mob` | The real part being placed |

**In a Building's `parts` list, neither key can ever match anything except the
literal `<none>`.** Any entry carrying one is dead, and if the floors it was meant
to cover have no other entry, every chunk holding that building fails. [game test](../examples/claim-tests.md#cnd-5){.v .v-g}

Use `floor`, `range`, `ground` and `top` to select parts by height. They are the
only level tests that work in a building. [game test](../examples/claim-tests.md#cnd-1){.v .v-g}

`inpart` is genuinely useful in a Condition reached from a palette, which is where
the mod's own content uses this family of keys. Confirmed in game on 7.4.12: a
palette `loot` key pointing at a Condition whose only matching entry was gated
`inpart` resolved to that entry's table, so the real part name does reach it. [game test](../examples/claim-tests.md#cnd-6){.v .v-g}

`range` works there too, and indexes by storey. A Condition with `range: "0,0"` and
`range: "1,100"` gave one loot table on the ground floor and the other two storeys
up. That is the mechanism behind the mod's own `chestloot`, which uses `"4,100"` and
`"-100,-3"` to give cellars different loot from upper floors. [game test](../examples/claim-tests.md#cnd-7){.v .v-g}

## Writing `range`

`range` is a string holding two integers separated by a comma. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

```json
{ "range": "9,12" }
```

Both ends are included, so this matches floor indices 9, 10, 11 and 12. Negative numbers work the same way. `"-2,-1"` matches the two deepest cellars. [game test](../examples/claim-tests.md#cnd-2){.v .v-g}

!!! warning "A malformed `range` either throws or is silently misread"
    The mod splits the string on commas, then reads the first two pieces as integers. It throws `Bad range specification: <l1>,<l2>!` when that fails.

    | You write | Result [game test](../examples/claim-tests.md#cnd-3){.v .v-g} |
    |---|---|
    | `"9,12"` | Matches floors 9 to 12. |
    | `"9"` | Throws. There is no second number. |
    | `"9, 12"` | Throws. The space makes `" 12"` a non-number. |
    | `"abc,def"` | Throws. Neither piece is a number. |
    | `"1,2,3"` | **Does not throw.** The mod uses `1,2` and discards the `3`. |

    The last row is the dangerous one. A third number produces no error and no log line, and the floor range you get is not the one you wrote. [game test](../examples/claim-tests.md#cnd-3){.v .v-g}

!!! note "`l1` and `l2` are not something you type"
    The names `l1` and `l2` appear only in the mod's error message, `Bad range specification: <l1>,<l2>!`, where they stand in for the two numbers. Write real integers.

## Example

```json
{
  "values": [
    { "factor": 3.0, "value": "desert_wall", "inbiome": ["minecraft:desert", "minecraft:badlands"] },
    { "factor": 1.0, "value": "default_wall" }
  ]
}
```

In a desert or badlands biome both entries match, so `desert_wall` wins 3 times out of 4. In every other biome the first entry fails its `inbiome` test, so `default_wall` is the only candidate and always wins. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## See also

- [Building Reference](building.md) for how these same keys gate part selection
- [Matchers](../concepts/matchers.md) for the different `if_all` and `if_any` shape used elsewhere <!-- noclaim -->
