---
status: in-progress
claims: verified
---

# KubeJS Integration

!!! info "Scope"
    This page covers loading Lost Cities assets through KubeJS instead of a datapack folder. Scripted generation and calling commands from generated content are not covered.

!!! tip "TL;DR"
    Lost Cities content is loaded through Minecraft's normal datapack registry system, and KubeJS merges anything under `kubejs/data/` into that same system. Drop your Lost Cities JSON there, no scripting, no separate datapack folder to manage.

## Why this works

Every Lost Cities asset type (world styles, city styles, buildings, and the rest) is registered as a real Minecraft dynamic registry entry, loaded the same way as vanilla recipes or loot tables, not through a Lost-Cities-specific file loader. Anything that can inject datapack JSON can add Lost Cities content. [code review](../examples/claim-tests.md#kjs-1){.v .v-c}

KubeJS's `data` folder is one of the simplest ways to do that inside a single modpack, since it needs no separate datapack zip or folder structure.

```
kubejs/data/<namespace>/lostcities/worldstyles/mystyle.json
```

Same file, same content, same rules as writing it directly into a datapack. No JS required, it is a plain JSON file KubeJS picks up automatically. [unverified](../examples/claim-tests.md#kjs-2){.v .v-u}

## The namespace is the folder you choose

The two layouts are the same shape:

```
kubejs/data/<namespace>/lostcities/<asset type>/<name>.json
<pack>/data/<namespace>/lostcities/<asset type>/<name>.json
```

There is no default and no implied namespace. The folder you create under `kubejs/data/` **is** the namespace, exactly as it is inside a datapack, and every reference to what you put there has to spell it. [code review](../examples/claim-tests.md#kjs-3){.v .v-c}

| Folder you create | Assets register as | References must say |
|---|---|---|
| `kubejs/data/mypack/lostcities/...` | `mypack:<name>` | `mypack:<name>` |
| `kubejs/data/lostcities/lostcities/...` | `lostcities:<name>` | `<name>`, bare, and this **overrides the mod's own file of that name** |

The second row is a real choice, not a default: writing `lostcities` as your folder puts your file at the same address as one the mod ships, and yours replaces it. Pick it deliberately or not at all. [code review](../examples/claim-tests.md#kjs-3){.v .v-c}

Everything on [Namespaces](../getting-started/namespaces.md) applies here unchanged, including what happens when a reference misses: it throws, and a profile's `worldStyle` that misses takes the server down. [game test](../examples/claim-tests.md#ns-4){.v .v-g} [code review](../examples/claim-tests.md#ns-4){.v .v-c}

## Where the profile goes

KubeJS holds datapack content. A Lost Cities **profile** is not datapack content: it is a config file, it lives at `config/lostcities/profiles/<name>.json`, and KubeJS has nothing to do with it. Wiring a profile to a dimension still happens in `config/lostcities/common.toml`. [code review](../examples/claim-tests.md#ns-8){.v .v-c}

## See also

- [Namespaces](../getting-started/namespaces.md)
- [Your First Custom City](../getting-started/first-city.md)
