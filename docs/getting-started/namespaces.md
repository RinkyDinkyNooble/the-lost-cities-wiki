# Namespaces

!!! tip "TL;DR"
    Every Lost Cities asset has a full name: `namespace:path`. Leave the namespace off when *referencing* something, and the mod assumes `lostcities:`. Get this wrong and your content just silently fails to load, no error.

No error, no crash, no log warning. The asset just is not found. Worth understanding this before writing anything.

## What a name actually is

A resource location, `namespace:path`. Examples:

- `minecraft:stone`
- `lostcities:standard` (the built-in world style)
- `apocalypse:wasteland_city` (a custom world style in your own namespace)

File location decides the name. A file at:

```
data/apocalypse/lostcities/worldstyles/wasteland_city.json
```

registers as `apocalypse:wasteland_city`. The folder right after `data/` **is** the namespace.

### The exact folder layout

Lost Cities assets are Forge datapack registries, so the path is always:

```
data/<your namespace>/lostcities/<asset type>/<name>.json
     └── becomes the      └── fixed, this is  └── buildings, parts, palettes,
         namespace            the registry's      citystyles, worldstyles,
                              own namespace       styles, variants, conditions,
                                                  multibuildings, scattered,
                                                  stuff, predefinedcities,
                                                  predefinedspheres
```

The `lostcities` in the middle is **not** your namespace, it is part of the registry's identity, and it is there no matter whose pack the file is in. That is why the mod's own files sit at `data/lostcities/lostcities/parts/...`: the first `lostcities` is the pack, the second is the registry. Only the mod's own files get that doubled-up look. Yours will not.

## The default namespace trap

Anywhere the mod expects a *name* (a profile's `worldStyle` key, a world style's list of city styles, a building's `refpalette`, and so on), a bare name with no colon is assumed to mean `lostcities:<name>`.

```json title="Fails silently if your file isn't actually in the lostcities namespace"
{
  "worldStyle": "wasteland_city"
}
```

```json title="Works, because the namespace is explicit"
{
  "worldStyle": "apocalypse:wasteland_city"
}
```

**Rule of thumb:** if your file lives under `data/lostcities/...`, you can reference it bare. If it lives under `data/<your namespace>/...`, you must always include that namespace when referencing it from anywhere else.

## Two real strategies

=== "Override the defaults"

    Put your file at the **exact same path** as a built-in one:

    ```
    data/lostcities/lostcities/worldstyles/standard.json
    ```

    Your version replaces the mod's shipped one entirely. Simple, but global: anything else that expects the original `lostcities:standard` behaviour breaks too. If two datapacks both try to override the same file, whichever loads last wins, and that order is not obvious.

=== "Use your own namespace"

    Put your file under your own namespace instead:

    ```
    data/apocalypse/lostcities/worldstyles/wasteland_city.json
    ```

    Nothing collides. But now **every reference to it, everywhere, needs the full `apocalypse:wasteland_city` name.**

Most modpacks should default to their own namespace. Override only when you deliberately want to replace a specific built-in default.

### How an override actually resolves

Ordinary datapack rules, with one consequence worth spelling out:

- The pack **latest in load order wins**, and it wins **whole file**. There is no key-by-key merging between two files with the same name, unlike block tags (which do merge) or a city style's own [`inherit`](../reference/citystyle.md#inheritance) (which merges within one file's chain).
- So overriding `citystyle_config` to change one setting means restating everything else that file contained, not just the key you care about.
- Nothing warns you when an override happens. The losing file is simply never seen.

!!! warning "`/reload` does not pick up Lost Cities asset changes"
    These registries are read **once, when the world loads**. The mod registers no reload listener at all, and vanilla does not reload datapack registries on `/reload` either. Editing a part or palette and running `/reload` changes nothing.

    In single player, leaving the world and rejoining does clear the mod's asset cache, so the next chunks generated use your edits. On a dedicated server it takes a full server restart. See [Seeing your changes](../tooling/commands.md#seeing-your-changes).

!!! warning "KubeJS defaults to the lostcities namespace"
    Generating Lost Cities content through KubeJS under the `lostcities` namespace overrides the mod's built-in defaults, by the same mechanism as above. That is a valid choice if you want it, just know it is what you are doing.

## See also

- [Your First Custom City](first-city.md) for these paths in a working datapack
- [Glossary](../glossary.md) for `namespace`, `resource location`, and `registry` if any of those were new.
