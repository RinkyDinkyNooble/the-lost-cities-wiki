# Editing & Tooling

Two ways to actually build content: edit in-game, or build in Minecraft normally and convert.

## In-game edit mode

Set `editMode: true` in your [profile](../reference/profile.md)'s `lostcity` section. This puts the world in a special editing state where you build directly and the mod has commands to save what you built back out to JSON.

!!! warning "Not fully verified yet"
    We haven't traced the editor's actual behavior in code yet, only confirmed the flag exists and does something. Treat this section as a pointer, not a full guide, until it's been tested and written up properly.

## Building normally, then converting

The more common workflow: build a structure normally in creative mode (with WorldEdit or similar for copy/paste), export it as a schematic, then convert that schematic into Lost Cities part JSON with an external tool.

!!! info "Recommended tool: coming soon"
    A write-up of the recommended conversion workflow is planned here once the tool is ready to share.

## See also

[Profile Reference](../reference/profile.md) for `editMode` and related flags.
