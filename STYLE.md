# Style guide

This wiki is written in the register used for aviation technical documentation: short active
sentences, one idea each, and one approved term per concept. The goal is that a reader under
pressure, reading in a second language, or skimming for one answer, cannot misread a sentence.

It is not full ASD-STE100. The wiki keeps its plain-spoken directness and its willingness to say
that something is broken. What it drops is idiom, metaphor, hedging and variation for variety.

## Sentences

| Rule | Do | Do not |
|---|---|---|
| One idea per sentence | "The mod reads the file. It throws if the key is absent." | "The mod reads the file, throwing if the key is absent, which you will see as a crash." |
| Active voice, named actor | "The mod overwrites the profile." | "The profile gets overwritten." |
| Imperative for instructions | "Set `maxfloors` to 3." | "You would want to set `maxfloors` to 3." |
| Present tense for behaviour | "The palette resolves aliases last." | "The palette will resolve aliases last." |
| No contractions | `does not`, `cannot`, `it is` | `doesn't`, `can't`, `it's` |
| Digits for numbers | "6 blocks", "3 floors" | "six blocks", "three floors" |
| No idiom or metaphor | "This is where the rule is easy to get wrong." | "This is where it bites." |

Keep procedural sentences under about 20 words. Descriptive sentences may run to about 25. If a
sentence needs a second comma to survive, split it.

## Warnings

State the consequence, then the action. The reader must learn the risk before the instruction.

```
!!! danger "Undefined `support` crashes world generation"
    The mod throws `NullPointerException` when a part references a `support` block that no
    palette defines. Define the character in a palette that is in scope for the part.
```

Do not open a warning with background. Do not end one with the consequence.

## Approved terms

Use the left column every time. The right column lists what to avoid, including words this wiki
previously used interchangeably.

| Use | Not | Note |
|---|---|---|
| the mod | Lost Cities, the game | "Lost Cities" names the product, on first mention and in prose about the project. "The mod" is the actor in every behaviour statement. |
| Minecraft | the game, vanilla | Only for behaviour that is Minecraft's, not the mod's. |
| key | field, property, setting | A JSON key. "Field" is for Java only, and the wiki does not document Java. |
| value | setting | What a key is set to. |
| entry | element, item, record | One object inside a JSON array. |
| part | segment, piece, section | A building part, the unit stored in `parts/`. |
| building part | part asset | Use in full when naming the asset type. |
| city style, world style | citystyle, worldstyle in prose | Backtick the single word only when naming the folder, the JSON key, or the registry type. |
| floor index | floor number | The signed index. Index 0 is the ground floor. Cellars are negative. |
| floor count | number of floors | A quantity. State whether it includes index 0. |
| slice | layer string, row | One string in `slices`. |
| datapack | data pack, resource pack | One word. A resource pack is a different thing. |
| silently | quietly, without warning | For behaviour that produces no error and no log line. |
| throws | errors out | The mod raises an exception. Name the exception. |
| crashes world generation | crashes, breaks | The user-visible effect of an uncaught throw during generation. |
| fails | breaks | A non-fatal failure. Say what the observable result is. |
| does nothing | is ignored, is a no-op | Use when a key parses but has no consumer. |

## Field tables

Every reference table uses the same three columns: `Key`, `Type`, `Meaning`, plus `Default` and
`Range` where they apply.

The **Meaning** cell must tie the value to the behaviour. It states what happens, and for which
value. A cell that only names the topic is wrong.

| Verdict | Cell |
|---|---|
| Wrong | `avoidWater` : "Replace all water with air." |
| Right | `avoidWater` : "If `true`, any liquid block a part places becomes air instead. Water already in the world is not affected." |

For a boolean, say what `true` does. Say what `false` does only when it is not simply the absence
of the `true` behaviour. For an enum, say what each accepted value does. For a sentinel number, say
what the sentinel means, for example `-1` means unset and `0` disables the feature.

## Claims

Every statement of behaviour must be traceable to the mod's code for the version the page declares.
Do not restate a key's name as its meaning. Do not repeat the mod's own comments as fact. A comment
describes intent; the code describes behaviour, and this wiki documents behaviour.

When a claim cannot be proved, either leave it out or mark it clearly as unconfirmed and say what
was checked.

## Punctuation

Do not use the em dash. Use a full stop, a colon, or brackets. Restructure the sentence if none of
those fit. The en dash is permitted between two numbers in a range, and nowhere else.
