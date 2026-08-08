# Namespaces

!!! tip "TL;DR"
    Every Lost Cities asset has a full name: `namespace:path`. Leave the namespace off when *referencing* something, and Lost Cities assumes `lostcities:`. Get this wrong and your content just silently fails to load, no error.

No error, no crash, no log warning. The asset just isn't found. Worth understanding this before writing anything.

## What a name actually is

A resource location, `namespace:path`. Examples:

- `minecraft:stone`
- `lostcities:standard` (the built-in world style)
- `apocalypse:wasteland_city` (a custom world style in your own namespace)

File location decides the name. A file at:

```
data/apocalypse/lostcities/lostcities/worldstyles/wasteland_city.json
```

registers as `apocalypse:wasteland_city`. The folder right after `data/` **is** the namespace.

## The default namespace trap

Anywhere Lost Cities expects a *name* (a profile's `worldStyle` field, a world style's list of city styles, a building's `refpalette`, and so on), a bare name with no colon is assumed to mean `lostcities:<name>`.

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

    Your version replaces the mod's shipped one entirely. Simple, but global: anything else that expects the original `lostcities:standard` behavior breaks too. If two datapacks both try to override the same file, whichever loads last wins, and that order isn't obvious.

=== "Use your own namespace"

    Put your file under your own namespace instead:

    ```
    data/apocalypse/lostcities/lostcities/worldstyles/wasteland_city.json
    ```

    Nothing collides. But now **every reference to it, everywhere, needs the full `apocalypse:wasteland_city` name.**

Most modpacks should default to their own namespace. Override only when you deliberately want to replace a specific built-in default.

!!! warning "KubeJS defaults to the lostcities namespace"
    Generating Lost Cities content through KubeJS under the `lostcities` namespace overrides the mod's built-in defaults, by the same mechanism as above. That's a valid choice if you want it, just know it's what you're doing.

## See also

[Glossary](../glossary.md) for `namespace`, `resource location`, and `registry` if any of those were new.
