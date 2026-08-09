---
status: in-progress
---

# KubeJS Integration

!!! info "This page is still being written"
    What's here is accurate and enough to get content loading. Deeper KubeJS integration (scripted generation, custom commands called from generated content) is planned.

!!! tip "TL;DR"
    Lost Cities content is loaded through Minecraft's normal datapack registry system, and KubeJS auto-merges anything under `kubejs/data/` into that same system. Drop your Lost Cities JSON there, no scripting, no separate datapack folder to manage.

## Why this works

Confirmed from the mod's own source: every Lost Cities asset type (world styles, city styles, buildings, and the rest) is registered as a real Minecraft dynamic registry entry, loaded the same way as vanilla recipes or loot tables, not through some Lost-Cities-specific file loader. Anything that can inject datapack JSON can add Lost Cities content. KubeJS's `data` folder is one of the simplest ways to do that inside a single modpack, since it needs no separate datapack zip or folder structure.

```
kubejs/data/<namespace>/lostcities/worldstyles/mystyle.json
```

Same file, same content, same rules as writing it directly into a datapack. No JS required, it's a plain JSON file KubeJS picks up automatically.

## The namespace gotcha still applies

Whatever `<namespace>` you use here still follows the same [namespacing rules](../getting-started/namespaces.md) as everywhere else. Use `lostcities` and you override the mod's built-in defaults. Use your own pack's namespace and you don't. Neither is wrong, just know which one you're doing.

## See also

[Namespaces](../getting-started/namespaces.md)
