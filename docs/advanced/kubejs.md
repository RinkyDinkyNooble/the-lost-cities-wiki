---
claims: verified
---

# KubeJS Integration

!!! info "Scope"
    This page covers loading Lost Cities assets through KubeJS instead of a datapack folder. Scripted generation and calling commands from generated content are not covered. <!-- noclaim -->

!!! tip "TL;DR"
    Lost Cities content is loaded through Minecraft's normal datapack registry system, and KubeJS merges anything under `kubejs/data/` into that same system. Drop your Lost Cities JSON there, no scripting, no separate datapack folder to manage. [code review](../examples/claim-tests.md#kjs-1){.v .v-c} [game test](../examples/claim-tests.md#kjs-2){.v .v-g}

## Why this works

Every Lost Cities asset type (world styles, city styles, buildings, and the rest) is registered as a real Minecraft dynamic registry entry, loaded the same way as vanilla recipes or loot tables, not through a Lost-Cities-specific file loader. Anything that can inject datapack JSON can add Lost Cities content. [code review](../examples/claim-tests.md#kjs-1){.v .v-c}

KubeJS's `data` folder is one such source, and it needs no separate datapack zip or folder structure inside a modpack. A file there is plain JSON, picked up automatically, with no JS involved. Assets moved out of a datapack and into `kubejs/data/` generated identically, down to the same failures in the same chunks. [game test](../examples/claim-tests.md#kjs-2){.v .v-g}

```
kubejs/data/<namespace>/lostcities/worldstyles/mystyle.json
```

Same file, same content, same rules as writing it directly into a datapack. [game test](../examples/claim-tests.md#kjs-2){.v .v-g}

## The namespace is the folder you choose

The two layouts are the same shape. [code review](../examples/claim-tests.md#kjs-3){.v .v-c}

```
kubejs/data/<namespace>/lostcities/<asset type>/<name>.json
<pack>/data/<namespace>/lostcities/<asset type>/<name>.json
```

There is no default and no implied namespace. The folder you create under `kubejs/data/` **is** the namespace, exactly as it is inside a datapack, and every reference to what you put there has to spell it. [code review](../examples/claim-tests.md#kjs-3){.v .v-c}

| Folder you create [code review](../examples/claim-tests.md#kjs-3){.v .v-c} | Assets register as | References must say |
|---|---|---|
| `kubejs/data/mypack/lostcities/...` | `mypack:<name>` | `mypack:<name>` |
| `kubejs/data/lostcities/lostcities/...` | `lostcities:<name>` | `<name>`, bare, and this **overrides the mod's own file of that name** |

The second row is a choice, not a default: writing `lostcities` as your folder puts your file at the same address as one the mod ships, and yours replaces it. [game test](../examples/claim-tests.md#ns-9){.v .v-g}

Everything on [Namespaces](../getting-started/namespaces.md) applies here unchanged, including what happens when a reference misses: it throws, and a profile's `worldStyle` that misses takes the server down. [game test](../examples/claim-tests.md#ns-4){.v .v-g} [code review](../examples/claim-tests.md#ns-4){.v .v-c}

## Where the profile goes

KubeJS holds datapack content. A Lost Cities **profile** is not datapack content: it is a config file, it lives at `config/lostcities/profiles/<name>.json`, and KubeJS has nothing to do with it. Wiring a profile to a dimension still happens in `config/lostcities/common.toml`. [code review](../examples/claim-tests.md#ns-8){.v .v-c}

## See also

- [Namespaces](../getting-started/namespaces.md)
- [Your First Custom City](../getting-started/first-city.md) <!-- noclaim -->
