# 1.0.1

A compatibility fix for multiplayer. No changes to generation, commands, or file
handling.

## DevTool no longer has to be installed on both sides

Previously, a player without DevTool was refused when joining a server that had it,
and a player with it was refused by a server without it. That was never intended: the
mod adds no blocks, items or entities and sends nothing over the network, so the two
sides have nothing they need to agree on.

Either side can now have it independently.

**Which side needs it:**

- **Dedicated server.** Everything that matters runs here: reading `.json5` files,
  checking your files as they load, the improved error messages, and all `/lcdev`
  commands. Install it on the server.
- **Client.** Only the Lost Cities menu fixes are client-side, and those affect the
  world creation screen, which a dedicated server does not have. Installing it on the
  client is optional.
- **Singleplayer.** One install covers both.

If you are updating from 1.0.0 there is nothing else to do, and worlds are unaffected.
