"""What a palette character may be, judged from what Lost Cities does with one.

Shared by `check-palette-pool.py` and `make-stress-pack.py`.

**This deliberately restates `PaletteLedger.safe` rather than asking the mod which
characters it considers safe.** A check that imported the mod's own answer would
agree with it however wrong it was. The rules here are written from what Lost Cities
does with a character, so the two have to arrive at the same set by separate routes.
If a rule changes on one side, the checks are meant to fail.

Kept in one place because there are two callers now. The rules are subtle enough
that one fixed here and not there would be a silent divergence, which is the thing
this file exists to prevent.
"""
import unicodedata

# The pool as it stood before it was widened to the plane. Nothing reads this but
# the checks: it is here so they can prove they are working past the old limit
# rather than passing because a fixture got smaller. A set rather than a list
# because it is only ever asked whether it holds a character, and how many.
OLD_POOL = frozenset("',<>?]"
                     + "".join(chr(c) for c in range(0x391, 0x3AA))
                     + "".join(chr(c) for c in range(0x3B1, 0x3CA))
                     + "".join(chr(c) for c in range(0x410, 0x450)))


def unsafe(c):
    """Why this character has no business in a slice row, or None.

    Each of these is a way for a pack to be wrong without anything saying so, which
    is why this names the reason rather than returning a bare boolean.
    """
    if len(c) != 1:
        return "is %d characters, not one" % len(c)
    if ord(c) > 0xFFFF:
        return ("is U+%04X, past the plane. Lost Cities reads a row with "
                "toCharArray(), so this counts as two cells" % ord(c))
    if 0xD800 <= ord(c) <= 0xDFFF:
        return "is an unpaired surrogate"
    if c == " ":
        return "is the air character"
    if c.isspace() or unicodedata.category(c) in ("Zs", "Zl", "Zp"):
        return "is blank, so the cell is invisible in the row"
    if c in ('"', "\\"):
        return "needs escaping inside a JSON string"
    if unicodedata.category(c) in ("Cc", "Cf", "Co", "Cs", "Cn"):
        return "is category %s, which has no glyph" % unicodedata.category(c)
    if unicodedata.category(c) in ("Mn", "Me", "Mc"):
        return "is a combining mark, so it attaches to the cell before it"
    if unicodedata.bidirectional(c) in ("R", "AL"):
        return "is right to left, so the row renders out of order"
    for form in ("NFC", "NFD"):
        if not unicodedata.is_normalized(form, c):
            return ("is rewritten by %s, so a tool that normalises the pack turns "
                    "one cell into another" % form)
    return None
