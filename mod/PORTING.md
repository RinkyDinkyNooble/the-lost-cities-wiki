# Porting

Where a port to another loader, Minecraft version or Lost Cities version has to
touch the source, and where it does not.

## Packages

| Package | Depends on | On a port |
|---|---|---|
| `core` | Java, Gson, jsr305, slf4j | Moves unchanged. No `net.minecraft`, no loader, no Lost Cities import |
| `platform` | Forge | Rewritten per loader: the `@Mod` entry, config spec, event wiring, version reads |
| `mixin` | Lost Cities and Minecraft internals | Re-targeted per Lost Cities version. Run `tools/check-mixin-targets.py` first |
| `json5` | Minecraft resources | Follows Minecraft's resource API. The text rules are `core/Json5Text` |
| `workshop`, `validate`, `command`, `chat`, `client`, `diagnostics` | Minecraft and Lost Cities API | Follows the API; the logic they share with no game type is in `core` |

## Traps

| Trap | Where |
|---|---|
| On 1.21 `ResourceLocation`'s constructor is private; `fromNamespaceAndPath`, `parse` and `tryParse` replace it | 6 calls in `json5/Json5`, `workshop/Attribution`, `Conditions`, `Importer`, `Workshop` |
| DataFixerUpper's `optionalFieldOf` is strict from 1.21: a wrong-typed field is a load error, not an absent one | `core/Levels` treats a wrong type as no test, and the monorail fallback relies on the same leniency. Both are 1.20.1 facts |
| A mixin target can move while the build stays green; the mixin then fails to apply or is refused at boot | `tools/check-mixin-targets.py` reads the jars and answers by descriptor and call count |
| The checks boot one Lost Cities version | `"checks"` in `testrig/versions.json` |
