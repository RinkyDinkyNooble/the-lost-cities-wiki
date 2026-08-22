# 1.2.0

Starting a second city no longer leaves the first one lying around, tab completion
stops lagging on a big modpack, and a lookup that matches hundreds of assets answers
in a few lines instead of hundreds.

Nothing here changes world generation. The two optional fixes are still off by
default.

## Importing a second city

An import fills the plots its own pack needs and leaves the rest alone, because you
may have built on those by hand. That had a consequence nobody was told about:
importing a second city on top of a first left the first one's plots exactly where
they were, so the workshop held two cities and the next export wrote both into one
pack.

The import now counts the plots it did not touch that already hold something, and
says so. When you want a clean slate:

```
/lcdev workshop clear
```

On its own that reports what emptying would cost, in plots and blocks, and changes
nothing. Add `confirm` and it writes a full backup pack to
`config/lostcitiesdevtool/backups/<timestamp>/` before it empties anything. The
backup is a real pack, so `/lcdev import` puts it straight back.

If the backup cannot be written the wipe stops rather than going ahead without one.
`clear confirm anyway` is the way past that, and it is two words deep on purpose.

Your pack's own settings survive a wipe, since the namespace and pack name are yours
rather than any imported city's, and so does the palette ledger, so the next export
letters the same blocks the same way instead of producing a whole-file diff.

## Tab completion on a large pack

Completing `/lcdev import` asked the server to read and parse every Lost Cities file
it had loaded, once for every character typed and again for every backspace. On a
server holding 911 assets that was **99 ms a keystroke**, so typing one world style
name cost close to two seconds of server time.

The listing is now read once per datapack load and reused. Measured on the same
server, the same completion costs **0.1 ms**. An edit is still picked up: the cache
is tied to the datapack load itself, so `/reload` rebuilds it.

## Lookups that match everything

`/lcdev char` and `/lcdev block` search every palette, part and building loaded. On
one pack that is a handful of lines. On a modpack it was hundreds, and on a server
with 600 assets that could not be built, `/lcdev char` answered with **552 lines**
and the reply was large enough to be cut off in transit.

Both now print the first dozen matches and count the rest. Assets that could not be
built are named up to five, then counted. `/lcdev in <asset>` still asks about one
asset on its own.
