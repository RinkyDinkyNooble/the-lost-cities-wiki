#!/usr/bin/env python3
"""Validate a Lost Cities datapack against the rules documented in this wiki.

Every check below corresponds to a documented rule. If a check fails here, either
the datapack is wrong or the wiki page it came from is wrong. Usage:

    python docs/examples/validate.py docs/examples/first-city
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

# Findings quote palette characters, which are routinely Greek, Cyrillic or CJK.
# A Windows console defaults to cp1252 and would abort on the first one.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

errors: list[str] = []
warnings: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        err(path.name, f"not valid JSON: {exc}")
        return None


def check_palette(path: Path, data) -> set[str]:
    """palette.md: char is one UTF-16 code unit; weighted lists must reach 128."""
    chars: set[str] = set()
    for entry in data.get("palette", []):
        c = entry.get("char")
        if c is None:
            err(path.name, "palette entry has no 'char'")
            continue
        if c == "":
            err(path.name, "palette entry has an empty 'char'; the mod throws at load")
            continue
        # The mod keeps the first UTF-16 code unit and discards the rest, so that
        # is the key everything else has to be judged against.
        units = len(c.encode("utf-16-le")) // 2
        key = c[0]
        if "\ud800" <= key <= "\udfff":
            err(path.name, f"char {c!r} starts above U+FFFF (emoji?); the mod keeps "
                           "only the leading surrogate, so every character in the "
                           "same block of 1024 collapses onto one key")
        elif units != 1:
            warn(path.name, f"char {c!r} is {units} code units; the mod registers "
                            f"{key!r} and discards the rest silently")
        if key in chars:
            err(path.name, f"duplicate char {key!r} within one file")
        chars.add(key)

        # loot and mob both name a Condition. An asset name comes from a file name,
        # so it can never contain a slash, and a mob is never a block state.
        for key, looks_like in (("loot", "loot table"), ("mob", "entity")):
            value = entry.get(key)
            if isinstance(value, str) and "/" in value:
                err(path.name, f"char {key!r} on {c!r}: {value!r} is a "
                               f"{looks_like} ID, but '{key}' names a Condition. "
                               "Wrap it in a one-entry condition and name that. "
                               f"Generation throws 'Error getting resource {value}!'")

        kinds = [k for k in ("block", "variant", "blocks", "frompalette") if k in entry]
        if len(kinds) != 1:
            err(path.name, f"char {c!r} must have exactly one of block/variant/blocks/frompalette, has {kinds}")

        if "blocks" in entry:
            total = sum(b.get("random", 0) for b in entry["blocks"])
            if total < 128:
                err(path.name, f"char {c!r} weighted list totals {total}, must reach 128")
            running = 0
            for i, b in enumerate(entry["blocks"]):
                if running >= 128:
                    err(path.name, f"char {c!r} entry #{i} ({b.get('block')}) is unreachable, 128 slots already filled")
                running += b.get("random", 0)
    return chars


def check_part(path: Path, data) -> set[str]:
    """part.md: 16x16, rows exactly xsize long, zsize rows, counted in UTF-16 units."""
    xs, zs = data.get("xsize"), data.get("zsize")
    if xs != 16 or zs != 16:
        err(path.name, f"xsize/zsize are {xs}/{zs}, must both be 16")
    used: set[str] = set()
    for si, layer in enumerate(data.get("slices", [])):
        if len(layer) != zs:
            err(path.name, f"slice {si} has {len(layer)} rows, expected zsize={zs}")
        for ri, row in enumerate(layer):
            units = len(row.encode("utf-16-le")) // 2
            if units != xs:
                err(path.name, f"slice {si} row {ri} is {units} UTF-16 units, expected xsize={xs}")
            used.update(row)
    n = len(data.get("slices", []))
    if n != 6:
        warn(path.name, f"{n} slices; a floor level is 6 blocks tall, so anything else over/underfills")
    if "metadata" in data:
        err(path.name, "key is 'meta', not 'metadata'")
    return used


CONDITION_KEYS = {"top", "ground", "cellar", "isbuilding", "issphere", "floor",
                  "chunkx", "chunkz", "range", "inpart", "belowpart", "inbuilding",
                  "inbiome"}
# The subset whose outcome is decided purely by the level index, so coverage can
# be computed instead of guessed at.
LEVEL_KEYS = {"top", "ground", "cellar", "floor", "range"}


# Integer.parseInt: an optional sign and digits, with no space either side.
INTEGER = re.compile(r"[+-]?\d+")

# The default profile's buildingMaxCellars, which decides the cellar count of a
# building that declares no cellar bounds.
DEFAULT_MAX_CELLARS = 3


def range_pieces(text: str) -> list[str]:
    """The pieces between commas with the empty ones dropped.

    ConditionContext splits with StringUtils.split(text, ','), in the 7.4.12 and
    7.5.4 jars alike, so "0,,2" is the range 0 to 2 and not an error.
    """
    return [p for p in str(text).split(",") if p]


def parse_range(text: str):
    """condition.md: the first two pieces read as integers exactly as written.

    None where the mod throws 'Bad range specification'. Integer.parseInt does not
    trim, so "0, 2" throws, where Python's int() would have read it. A third number
    is read past silently, so it does not count against the range here.
    """
    pieces = range_pieces(text)
    if len(pieces) < 2 or not all(INTEGER.fullmatch(p) for p in pieces[:2]):
        return None
    return int(pieces[0]), int(pieces[1])


# Every level test is an optional field, and the codec library Minecraft 1.20.1
# ships reads a value it cannot parse as absent. What it can parse follows JsonOps:
# a boolean test also takes a number, true when its byte value is not zero; a number
# test takes a boolean as 1 or 0; `range` takes only a string. Anything else is no
# test at all, so `"top": "yes"` places a part on every level.

def as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return (int(value) & 0xFF) != 0
    return None


def as_int(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return None


def matches_level(ref: dict, level: int, top_index: int) -> bool:
    """Whether one part reference matches a level. Tests chain with AND, never OR."""
    ground = as_bool(ref.get("ground"))
    if ground is not None and (level == 0) != ground:
        return False
    top = as_bool(ref.get("top"))
    if top is not None and (level >= top_index) != top:
        return False
    cellar = as_bool(ref.get("cellar"))
    if cellar is not None and (level < 0) != cellar:
        return False
    floor = as_int(ref.get("floor"))
    if floor is not None and level != floor:
        return False
    if isinstance(ref.get("range"), str):
        bounds = parse_range(ref["range"])
        return bounds is not None and bounds[0] <= level <= bounds[1]
    return True


def check_level_tests(where: str, ref: dict, reported: set[str]) -> None:
    """A level test the codec cannot read, and a range that throws or misleads."""
    for key in ("ground", "top", "cellar", "floor"):
        read = as_int if key == "floor" else as_bool
        if key in ref and key not in reported and read(ref[key]) is None:
            reported.add(key)
            err(where, f"'{key}' is written as {json.dumps(ref[key])}, which is not "
                       f"{'a number' if key == 'floor' else 'true or false'}. The mod "
                       f"reads it as no test, so the part is placed as if '{key}' "
                       "were not there")
    if "range" not in ref:
        return
    text = ref["range"]
    if not isinstance(text, str):
        err(where, f"'range' is written as {json.dumps(text)}, which is not text. The "
                   "mod reads it as no range, so the part applies at every level")
    elif parse_range(text) is None:
        err(where, f"range {text!r} does not parse; the mod throws "
                   f"'Bad range specification: {text}!'")
    elif len(range_pieces(text)) > 2:
        warn(where, f"range {text!r} has more than two numbers. The mod reads the "
                    "first two and discards the rest silently")


def check_building(path: Path, data) -> None:
    """building.md: filler required; parts must cover every level from -cellars to floors."""
    if "filler" not in data:
        err(path.name, "'filler' is required")
    parts = data.get("parts", [])
    if not parts:
        err(path.name, "'parts' is required and must not be empty")
        return
    for key, lo, hi in (("minfloors", 0, 60), ("maxfloors", 0, 60),
                        ("mincellars", 0, 20), ("maxcellars", 0, 20)):
        if key in data and not (lo <= data[key] <= hi):
            err(path.name, f"{key}={data[key]} outside the {lo}-{hi} window")
    dead_keys_seen: set[str] = set()
    wrong_types_seen: set[str] = set()
    for ref in parts:
        check_level_tests(path.name, ref, wrong_types_seen)
        # A building's floor loop passes "<none>" as the current part, and the
        # belowpart predicate reads the current part rather than the one below,
        # so neither key can ever match from here.
        for key in ("inpart", "belowpart"):
            if key in ref and key not in dead_keys_seen:
                dead_keys_seen.add(key)
                err(path.name, f"part reference uses '{key}', which never matches "
                               "from a building's parts list: the floor loop has no "
                               "current part yet and passes '<none>'"
                               + (". 'belowpart' additionally tests the current part "
                                  "rather than the one below, in every version that "
                                  "declares it" if key == "belowpart" else ""))

    has_fallback = any(not (CONDITION_KEYS & set(p)) for p in parts)
    if has_fallback:
        return

    # Without a fallback, every level has to be covered by a condition. That is
    # only provable when the conditions depend on nothing but the level index.
    unprovable = {k for p in parts for k in (CONDITION_KEYS - LEVEL_KEYS) & set(p)}
    if unprovable:
        err(path.name, "no unconditioned part reference, and coverage cannot be "
                       f"proven because {sorted(unprovable)} depend on more than the "
                       "level index; add a fallback entry with no conditions")
        return

    # The profile rolls a height and the building's bounds clamp it: maxfloors is a
    # min() and minfloors a max() applied after it. So the tallest the building
    # can be is the larger of the two, and every height from the lower bound up to
    # that is reachable, not only the tallest. Same for cellars, where an undeclared
    # bound leaves the default profile's.
    top_to = max(data.get("maxfloors", -1), data.get("minfloors", -1))
    if top_to < 0:
        err(path.name, "no unconditioned part reference, and no 'maxfloors', so the "
                       "profile decides the height and will eventually roll past "
                       "whatever the conditions cover")
        return
    top_from = min(data["minfloors"], top_to) if "minfloors" in data else 0
    declared = "maxcellars" in data or "mincellars" in data
    deep_to = (max(data.get("maxcellars", -1), data.get("mincellars", -1))
               if declared else DEFAULT_MAX_CELLARS)
    deep_from = min(data["mincellars"], deep_to) if "mincellars" in data else 0

    # Tallest first, so a building failing at its full height is reported as such.
    for deepest in range(deep_from, deep_to + 1):
        for top in range(top_to, top_from - 1, -1):
            uncovered = [lvl for lvl in range(-deepest, top + 1)
                         if not any(matches_level(p, lvl, top) for p in parts)]
            if not uncovered:
                continue
            if top == top_to:
                at = (f"Levels run from -{deepest} to {top} INCLUSIVE, so "
                      f"'maxfloors': {top} is a {top + 1}-storey building.")
            else:
                at = (f"It can generate {top + 1} storey{'s' if top else ''} tall "
                      f"with {deepest} cellar{'' if deepest == 1 else 's'}, not only "
                      "at its full height, and at that height these levels match "
                      "nothing.")
            if deepest and not declared:
                at += (" It declares no cellar bounds, so the profile decides how "
                       "many, and the default profile allows up to "
                       f"{DEFAULT_MAX_CELLARS}.")
            err(path.name, f"levels {uncovered} match no part. {at} Generation "
                           "throws 'Misconfiguration! Floor were generated for a "
                           "building where no part condition matches!'")
            return


def check_stuff(path: Path, data) -> None:
    """stuff.md: both min/max pairs are used as random(max-min), so max must exceed min."""
    for lo, hi in (("mincount", "maxcount"), ("minheight", "maxheight")):
        if lo in data and hi in data and data[hi] <= data[lo]:
            err(path.name, f"{hi} ({data[hi]}) must be strictly greater than {lo} ({data[lo]})")
    if data.get("attempts", 1) < 1:
        err(path.name, "attempts must be at least 1 or nothing is ever placed")


# Wiki pages that reproduce a shipped example file in full, as page -> asset.
# Keeping these byte-identical is the point: a reader copying from the page and a
# reader copying from the bundle must end up with the same file.
EMBEDDED_COPIES = {
    "docs/getting-started/first-city.md":
        "data/mycity/lostcities/parts/tower_floor.json",
}


def check_embedded_copies(root: Path) -> None:
    """Any page that inlines a whole example file must match it exactly."""
    import re

    repo = Path(__file__).resolve().parents[2]
    for page_rel, asset_rel in EMBEDDED_COPIES.items():
        page = repo / page_rel
        asset = root / asset_rel
        if not page.is_file() or not asset.is_file():
            # Only meaningful when validating the bundle these pages document.
            continue
        fence = re.search(
            r'```json title="[^"]*%s"\n(.*?)\n```' % re.escape(asset_rel.split("/")[-1]),
            page.read_text(encoding="utf-8"),
            re.S,
        )
        if fence is None:
            err(page_rel, f"no fenced copy of {asset_rel} found; the page and the bundle "
                          "are meant to carry the same file")
            continue
        if fence.group(1) != asset.read_text(encoding="utf-8").rstrip("\n"):
            err(page_rel, f"the inlined copy of {asset_rel} has drifted from the real file")


def check_key_availability_pointers() -> None:
    """Every key the availability page attributes to a page must be on that page.

    The availability table names a key and links the reference page that documents
    it. Nothing else ties the two together, so a key filed under the wrong asset
    reads as authoritative while sending the reader to a page that never mentions
    it. This catches exactly that.
    """
    import re

    repo = Path(__file__).resolve().parents[2]
    page = repo / "docs" / "versions" / "key-availability.md"
    if not page.is_file():
        return
    cache: dict[Path, str] = {}
    for row in page.read_text(encoding="utf-8").split("\n"):
        if not row.startswith("|"):
            continue
        link = re.search(r"\]\((\.\./[\w/\-]+\.md)\)", row)
        if link is None:
            continue
        target = (page.parent / link.group(1)).resolve()
        if target not in cache:
            cache[target] = target.read_text(encoding="utf-8") if target.is_file() else ""
        body = cache[target]
        cells = row.split("|")
        for key in re.findall(r"`([A-Za-z_#][\w]*)`", cells[-2] if len(cells) > 2 else ""):
            if f"`{key}`" not in body:
                err("versions/key-availability.md",
                    f"key `{key}` is filed under {link.group(1)}, "
                    "which never mentions it")


# Which asset class backs each reference page's top-level key table. Only pages
# whose table describes one asset appear here; pages that document several nested
# objects are checked by name lookup instead.
PAGE_ASSET = {
    "building.md": "BuildingRE",
    "citystyle.md": "CityStyleRE",
    "worldstyle.md": "WorldStyleRE",
    "part.md": "BuildingPartRE",
    "condition.md": "ConditionRE",
    "multibuilding.md": "MultiBuildingRE",
    "scattered.md": "ScatteredRE",
    "stuff.md": "StuffSettingsRE",
    "style.md": "StyleRE",
    "variant.md": "VariantRE",
    "palette.md": "PaletteRE",
}

# Reference pages whose tables are not datapack keys, so mod-keys.json has nothing
# to say about them. config.md documents Forge TOML settings, which are declared in
# a ForgeConfigSpec rather than a codec.
NON_CODEC_PAGES = {"config.md"}


def check_against_mod_keys() -> None:
    """Check the reference tables against the keys the mod's codecs actually declare.

    Two failures matter to a reader. A key the wiki documents that the mod does not
    have sends them to write something that cannot load. A key marked optional that
    the codec requires does the same, more quietly.
    """
    import json as _json
    import re

    here = Path(__file__).resolve().parent
    truth_file = here / "mod-keys.json"
    if not truth_file.is_file():
        return
    truth = _json.loads(truth_file.read_text(encoding="utf-8"))["versions"]
    base = truth["7.4.12"]
    # A key is real if any documented version declares it, anywhere.
    real = {k for v in truth.values() for cls in v["codec"].values() for k in cls}
    real |= {k for v in truth.values() for k in v["profile"]}
    # Part meta names are read by name from generation code, not declared in a codec.
    real |= {"support", "nowater", "dontconnect", "z1", "z2"}

    ref = here.parents[1] / "docs" / "reference"
    if not ref.is_dir():
        return
    for page in sorted(ref.glob("*.md")):
        if page.name in NON_CODEC_PAGES:
            continue
        asset = base["codec"].get(PAGE_ASSET.get(page.name, ""), {})
        cols = None
        for line in page.read_text(encoding="utf-8").split("\n"):
            s = line.strip()
            if not s.startswith("|"):
                cols = None
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            low = [c.lower() for c in cells]
            if "key" in low:
                cols = (low.index("key"),
                        low.index("required") if "required" in low else None)
                continue
            if cols is None or "---" in s or cols[0] >= len(cells):
                continue
            names = re.findall(r"`([A-Za-z_][\w]*)`", cells[cols[0]])
            for name in names:
                if name not in real:
                    err(f"reference/{page.name}",
                        f"documents `{name}`, which no version's codec declares")
            if cols[1] is None or cols[1] >= len(cells) or len(names) != 1:
                continue
            name = names[0]
            if name not in asset:
                continue
            documented_required = "yes" in cells[cols[1]].lower()
            actually_required = asset[name] == "required"
            if documented_required != actually_required:
                err(f"reference/{page.name}",
                    f"`{name}` is documented as "
                    f"{'required' if documented_required else 'optional'}, "
                    f"but the 7.4.12 codec says it is {asset[name]}")


def check_building_palette_scope(root: Path) -> None:
    """building.md: filler and rubble resolve against the BUILDING's palette.

    The building's palette is the style's palettes plus the building's own
    refpalette or palette. A refpalette on a part is not in that set. Getting this
    wrong loads cleanly, generates parts correctly, and then throws a
    NullPointerException in ChunkDriver.correct the moment a door is placed, once
    per chunk, mostly without a stack trace.
    """
    ns_root = root / "data"
    if not ns_root.is_dir():
        return
    # char -> palettes in this pack that define it
    defined: dict[str, set[str]] = {}
    for ns_dir in sorted(ns_root.iterdir()):
        pal_dir = ns_dir / "lostcities" / "palettes"
        if not pal_dir.is_dir():
            continue
        for path in sorted(pal_dir.glob("*.json")):
            data = load(path)
            if not isinstance(data, dict):
                continue
            name = f"{ns_dir.name}:{path.stem}"
            for entry in data.get("palette", []):
                if isinstance(entry, dict) and "char" in entry:
                    defined.setdefault(entry["char"], set()).add(name)

    for ns_dir in sorted(ns_root.iterdir()):
        bld_dir = ns_dir / "lostcities" / "buildings"
        if not bld_dir.is_dir():
            continue
        for path in sorted(bld_dir.glob("*.json")):
            data = load(path)
            if not isinstance(data, dict):
                continue
            own = set()
            ref = data.get("refpalette")
            if isinstance(ref, str):
                own.add(ref if ":" in ref else f"lostcities:{ref}")
            has_inline = isinstance(data.get("palette"), list)
            for key in ("filler", "rubble"):
                ch = data.get(key)
                if not isinstance(ch, str) or ch not in defined:
                    continue  # absent, or supplied by the style, which is not visible here
                if has_inline:
                    continue
                if not (own & defined[ch]):
                    err(path.name,
                        f"`{key}` is {ch!r}, defined in {sorted(defined[ch])}, but this "
                        "building references none of those. A part's refpalette does not "
                        "reach filler or rubble. Add refpalette to the building")


def check_profiles(root: Path) -> None:
    """A profile key must sit in the section the mod registered it under.

    Sections are the mod's own config categories. A key in the wrong section is not
    an error the mod reports: it is simply never found, so the key runs at its
    default and the profile looks like it was ignored.
    """
    import json as _json

    truth_file = Path(__file__).resolve().parent / "mod-keys.json"
    profile_dir = root / "profile"
    if not truth_file.is_file() or not profile_dir.is_dir():
        return
    known = _json.loads(truth_file.read_text(encoding="utf-8"))["versions"]["7.4.12"]["profile"]
    for path in sorted(profile_dir.glob("*.json")):
        data = load(path)
        if not isinstance(data, dict):
            continue
        for section, body in data.items():
            if not isinstance(body, dict):
                continue  # the root 'public' flag is a bare value
            for key in body:
                if key not in known:
                    err(f"profile/{path.name}",
                        f"`{key}` is not a profile key in 7.4.12")
                elif known[key]["section"] != section:
                    err(f"profile/{path.name}",
                        f"`{key}` is in section '{section}' but belongs in "
                        f"'{known[key]['section']}', so the mod will never read it")

        # The profile's worldStyle is resolved OUTSIDE the catch that makes every
        # other asset mistake survivable, so naming one this pack does not ship
        # crashes the server rather than failing a chunk.
        style = data.get("lostcity", {}).get("worldStyle")
        if isinstance(style, str) and ":" in style:
            ns, name = style.split(":", 1)
            if (root / "data" / ns).is_dir():
                if not (root / "data" / ns / "lostcities" / "worldstyles"
                        / f"{name}.json").is_file():
                    err(f"profile/{path.name}",
                        f"worldStyle '{style}' is in this pack's namespace but no "
                        f"worldstyles/{name}.json defines it. This CRASHES the "
                        "server, it does not fail a chunk: the world style is "
                        "resolved before the generation try/catch")

        # A profile name has to be lowercase letters only. Anything else and the
        # world creation screen silently does not offer it.
        if not path.stem.isalpha() or not path.stem.islower():
            err(f"profile/{path.name}",
                f"profile name '{path.stem}' is not lowercase letters only, so it "
                "will not appear as a choice on the world creation screen")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "first-city")
    data_dir = root / "data"
    if not data_dir.is_dir():
        print(f"no data/ directory under {root}")
        return 2

    declared_chars: set[str] = set()
    used_chars: set[str] = set()
    part_names: set[str] = set()

    for ns_dir in sorted(data_dir.iterdir()):
        lc = ns_dir / "lostcities"
        if not lc.is_dir():
            warn(ns_dir.name, "no 'lostcities' directory; assets live at data/<ns>/lostcities/<type>/")
            continue
        for type_dir in sorted(lc.iterdir()):
            for f in sorted(type_dir.glob("*.json")):
                data = load(f)
                if data is None:
                    continue
                kind = type_dir.name
                if kind == "palettes":
                    declared_chars |= check_palette(f, data)
                elif kind == "parts":
                    used_chars |= check_part(f, data)
                    part_names.add(f"{ns_dir.name}:{f.stem}")
                elif kind == "buildings":
                    check_building(f, data)
                elif kind == "stuff":
                    check_stuff(f, data)

    check_embedded_copies(root)
    check_profiles(root)
    check_building_palette_scope(root)
    check_key_availability_pointers()
    check_against_mod_keys()

    # A space is air only because the shipped 'common' palette says so.
    unknown = used_chars - declared_chars - {" "}
    if unknown:
        warn("parts", "chars not defined by this pack's own palettes (must come from the "
                      f"style's merged palette or generation throws): {sorted(unknown)}")

    for line in warnings:
        print(f"  warn  {line}")
    for line in errors:
        print(f" ERROR  {line}")
    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
