"""Load and validate the YAML data set."""
from __future__ import annotations

import re

from dataclasses import dataclass, field
from pathlib import Path

import yaml

MECHANISMS = ("cut", "pierce", "crush", "ballistic")
THREATS = ("fragment", "pistol", "rifle", "rifle_ap")
# Names the combatant figures can draw (templates/figure.js); build.py checks they exist there.
FIG_NAMES = {
    "helmet": ("kettle", "bascinet", "sallet", "closed", "pot", "morion", "coif", "crested", "brodie", "adrian", "stahlhelm",
               "fj", "m1", "japanese", "soviet", "pasgt", "ach", "cap"),
    "hat": ("none", "hood", "broad_hat", "tricorne", "bicorne", "shako", "bearskin", "mitre", "round_hat", "kepi",
            "slouch", "feather", "headband", "czapka", "field_cap", "winter_cap", "pith", "boonie", "turban",
            "shemagh", "balaclava", "beret", "police_cap", "kabalak"),
    "icon": ("sword", "sabre", "dagger", "axe", "club", "spear", "bill", "poleaxe", "lance", "bow", "crossbow", "sling", "long_gun",
             "bayonet_gun", "musket_butt", "modern_rifle", "machine_gun", "smg", "pistol", "launcher", "grenade",
             "stick_grenade", "device", "rammer", "stake", "spade", "fist"),
    "beard": ("none", "stubble", "moustache", "beard"),
    "shield": ("heater", "round"),
}
LOOK_KEYS = ("colour", "trousers", "coat", "hat", "helmet", "beard", "shield")


COMMONS = "https://commons.wikimedia.org/wiki/File:"
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".webp", ".svg")


def commons_url(file: str) -> str:
    """Wikimedia Commons file page for an example's image (same as commonsUrl in roller.html)."""
    from urllib.parse import quote
    return COMMONS + quote(file.replace(" ", "_"), safe="!'*-._~")


def image_errors(where: str, img) -> list[str]:
    """An example's optional image: a Commons file name and a caption."""
    if img is None:
        return []
    if not isinstance(img, dict) or set(img) - {"file", "caption"}:
        return [f"{where}: image must be {{file, caption}}"]
    f, cap = img.get("file"), img.get("caption")
    errs = []
    if not (isinstance(f, str) and f.strip() and "/" not in f and not f.lower().startswith("file:")
            and f.lower().endswith(IMAGE_EXT)):
        errs.append(f"{where}: image file must be a Wikimedia Commons file name like 'Example.jpg' "
                    f"(no 'File:' prefix, no URL), got {f!r}")
    if not (isinstance(cap, str) and cap.strip()):
        errs.append(f"{where}: image needs a caption saying what it shows")
    return errs


def look_errors(where: str, look) -> list[str]:
    """Problems with a figure `look` (side, example or kit)."""
    if look is None:
        return []
    if not isinstance(look, dict):
        return [f"{where}: look must be a mapping"]
    out = []
    for k, v in look.items():
        if k not in LOOK_KEYS:
            out.append(f"{where}: unknown look key {k} (use {', '.join(LOOK_KEYS)})")
        elif k in ("colour", "trousers") and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(v)):
            out.append(f"{where}: look {k} must be a colour like #2f3f6e")
        elif k == "coat" and v != "skin":
            out.append(f"{where}: look coat can only be skin (bare chest)")
        elif k in FIG_NAMES and v not in FIG_NAMES[k]:
            out.append(f"{where}: look {k} {v} is not one the figures can draw ({', '.join(FIG_NAMES[k])})")
    return out
SEVERITIES = ("light", "serious", "critical")


class DataError(ValueError):
    pass


@dataclass
class Data:
    root: Path
    zones: list
    locations: list            # ordered list of dicts
    loc: dict                  # id -> location
    weapons: dict              # id -> weapon (ordered)
    tables: dict               # id -> table (ordered by file name)
    wounds: dict
    modifiers: dict = field(default_factory=dict)   # id -> modifier (ordered)
    armor: dict = field(default_factory=dict)       # materials, slots, kits (id -> kit)
    melee_everywhere: list = field(default_factory=list)
    melee_fallback: dict = field(default_factory=dict)
    conflicts: dict = field(default_factory=dict)   # battle group -> history, sides, examples
    wmult: dict = field(default_factory=dict)       # table id -> weapon id -> [multiplier per location]
    terrain: dict = field(default_factory=dict)     # terrain.yaml: hours_per_day, forces, terrain (id -> type), place_kinds
    maps: dict = field(default_factory=dict)        # travel map id -> map, `rows` = terrain rows as strings
    works: dict = field(default_factory=dict)       # works.yaml: camps, edge_works, hex_works
    weather: dict = field(default_factory=dict)     # weather.yaml: daylight, conditions, ground, rest, fatigue, climates
    disease: dict = field(default_factory=dict)     # disease.yaml: camp disease for travel-map forces
    units: dict = field(default_factory=dict)       # units.yaml: unit combat on the field map
    fields: dict = field(default_factory=dict)      # battlefield id -> battlefield (data/fields), `rows` = ground rows
    orders: dict = field(default_factory=dict)      # battlefield id -> the defenders' orders from the accounts (data/orders.yaml): hold, withdraw
    teams: dict = field(default_factory=dict)       # era id -> character generation tables (data/teams)
    equipment: dict = field(default_factory=dict)   # era id -> coins, a Day's pay and priced kit (data/equipment)
    money: dict = field(default_factory=dict)       # money.yaml: purse per career term, pay for a day's work
    jobs: dict = field(default_factory=dict)        # era id -> jobs between fights and a trouble table (data/jobs)
    replacements: dict = field(default_factory=dict)   # era id -> how losses are replaced, and a lost man's effects (data/replacements)
    events: dict = field(default_factory=dict)      # events on the march and in camp, by era (data/events.yaml)
    experience: dict = field(default_factory=dict)  # skills rising in play (data/experience.yaml)
    checks: dict = field(default_factory=dict)      # skill checks out of a fight (data/checks.yaml)
    ranks: dict = field(default_factory=dict)       # rank, pay, promotion and loot (data/ranks.yaml)
    training: dict = field(default_factory=dict)    # masters, teammates and drill (data/training.yaml)
    ageing: dict = field(default_factory=dict)      # decline, maturity, wear and worn out (data/ageing.yaml)
    loads: dict = field(default_factory=dict)       # carrying weight (data/loads.yaml)
    stress: dict = field(default_factory=dict)      # combat stress (data/stress.yaml)
    prisoners: dict = field(default_factory=dict)   # capture and captivity (data/prisoners.yaml)
    hazards: dict = field(default_factory=dict)     # swimming, climbing, falls, chases (data/hazards.yaml)
    languages: dict = field(default_factory=dict)   # tongues by army, bands, passing (data/languages.yaml)
    patrons: dict = field(default_factory=dict)     # standing, favours, a patron's fate (data/patrons.yaml)
    papers: dict = field(default_factory=dict)      # each era's game handouts and epilogues (data/papers.yaml)
    uses: dict = field(default_factory=dict)        # skills that do things on the travel map (data/uses.yaml)
    weights: dict = field(default_factory=dict)     # item weights, coin, pack animals (data/weights.yaml)
    supplies: dict = field(default_factory=dict)    # what a force carries between fights (data/supplies.yaml)
    kit: dict = field(default_factory=dict)         # boots and clothing wearing out (data/kit.yaml)
    warnings: list = field(default_factory=list)


YAML_FILES = "*.yaml"


def _read(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _optional(path: Path, default):
    """A data file that may be absent (older data sets): its contents, or `default`."""
    return _read(path) if path.exists() else default


def _read_dir(folder: Path, rows_of: str | None = None) -> dict:
    """Every YAML file in a folder, by id; rows_of: the key whose text is split into `rows`."""
    out = {}
    for p in sorted(folder.glob(YAML_FILES)) if folder.exists() else []:
        x = _read(p)
        if rows_of:
            x["rows"] = [r for r in str(x.get(rows_of, "")).split("\n") if r.strip()]
        out[x["id"]] = x
    return out


def load(root: str | Path = "data") -> Data:
    root = Path(root)
    body = _read(root / "body.yaml")
    wfile = _read(root / "weapons.yaml")
    weapons = wfile["weapons"]
    wounds = _read(root / "wounds.yaml")
    tables = [_read(p) for p in sorted((root / "tables").glob(YAML_FILES))]
    tables.sort(key=lambda t: t.get("order", 999))   # stable: file name breaks ties
    mods = _read(root / "modifiers.yaml") if (root / "modifiers.yaml").exists() else {"modifiers": []}
    armor = _read(root / "armor.yaml") if (root / "armor.yaml").exists() else {"materials": {}, "slots": {}, "kits": []}
    conflicts = (_read(root / "conflicts.yaml") or {}).get("conflicts", {}) if (root / "conflicts.yaml").exists() else {}
    terrain = _read(root / "terrain.yaml") if (root / "terrain.yaml").exists() else {"hours_per_day": 8, "fight_within": 1, "forces": {}, "terrain": [], "place_kinds": {}}
    terrain = {**terrain, "terrain": {t["id"]: t for t in terrain["terrain"]}}
    works = _optional(root / "works.yaml", {"camps": {}, "edge_works": {}, "hex_works": {}})
    weather = _optional(root / "weather.yaml", {})
    disease = _optional(root / "disease.yaml", {})
    units = _optional(root / "units.yaml", {})
    maps = _read_dir(root / "maps", "terrain")
    fields = _read_dir(root / "fields", "ground")
    orders = _optional(root / "orders.yaml", {})
    _apply_orders(fields, orders)
    _apply_accounts(fields, _optional(root / "accounts.yaml", {}))
    teams = _read_dir(root / "teams")
    equipment = _read_dir(root / "equipment")
    money = _optional(root / "money.yaml", {})
    jobs = _read_dir(root / "jobs")
    replacements = _read_dir(root / "replacements")
    events = _optional(root / "events.yaml", {})
    experience = _optional(root / "experience.yaml", {})
    checks = _optional(root / "checks.yaml", {})
    ranks = _optional(root / "ranks.yaml", {})
    training = _optional(root / "training.yaml", {})
    ageing = _optional(root / "ageing.yaml", {})
    loads = _optional(root / "loads.yaml", {})
    stress = _optional(root / "stress.yaml", {})
    prisoners = _optional(root / "prisoners.yaml", {})
    hazards = _optional(root / "hazards.yaml", {})
    languages = _optional(root / "languages.yaml", {})
    patrons = _optional(root / "patrons.yaml", {})
    papers = _optional(root / "papers.yaml", {})
    uses = _optional(root / "uses.yaml", {})
    weights = _optional(root / "weights.yaml", {})
    supplies = _optional(root / "supplies.yaml", {})
    kit = _optional(root / "kit.yaml", {})

    data = Data(
        root=root,
        zones=body["zones"],
        locations=body["locations"],
        loc={l["id"]: l for l in body["locations"]},
        weapons={w["id"]: w for w in weapons},
        tables={t["id"]: t for t in tables},
        wounds=wounds,
        modifiers={m["id"]: m for m in mods.get("modifiers", [])},
        armor={**armor, "kits": {k["id"]: k for k in armor.get("kits", [])}},
        melee_everywhere=wfile.get("melee_everywhere", []),
        melee_fallback=wfile.get("melee_fallback", {}),
        conflicts=conflicts,
        terrain=terrain,
        maps=maps,
        works=works,
        weather=weather,
        disease=disease,
        units=units,
        fields=fields,
        orders=orders,
        teams=teams,
        equipment=equipment,
        money=money,
        jobs=jobs,
        replacements=replacements,
        events=events,
        experience=experience,
        checks=checks,
        ranks=ranks,
        training=training,
        ageing=ageing,
        loads=loads,
        stress=stress,
        prisoners=prisoners,
        hazards=hazards,
        languages=languages,
        patrons=patrons,
        papers=papers,
        uses=uses,
        weights=weights,
        supplies=supplies,
        kit=kit,
    )
    for t in data.tables.values():
        if "regions" in t and "weights" not in t:
            t["weights"] = expand_regions(data, t)
        t.setdefault("native", "gunfire")
        t.setdefault("weapon_bias", "raw")
        t.setdefault("armor", "allowed" if t.get("variant") == "adjusted" else "baked_in")
        t.setdefault("assumes_shield", False)
    validate(data)
    compute_multipliers(data)
    return data


# --------------------------------------------------------------------------
# Weapon availability and location multipliers
# --------------------------------------------------------------------------
def available_weapons(d: Data, tid: str) -> list[str]:
    """The table's own weapons, those it borrows from another table (`borrowed`), the
    close-combat weapons of its era (`era_melee`), then those offered everywhere."""
    t = d.tables[tid]
    own = list(t["weapons"]) + [w for w in t.get("borrowed") or {} if w not in t["weapons"]]
    own += [w for w in t.get("era_melee") or [] if w not in own]
    return own + [w for w in d.melee_everywhere if w not in own]


def resolve_table(d: Data, tid: str, wid: str) -> str:
    """Table whose location data a weapon uses: a close-combat weapon on a table of another
    kind of fighting rolls on the era's melee table (melee_fallback)."""
    w, t = d.weapons[wid], d.tables[tid]
    if wid not in t["weapons"] and wid in (t.get("borrowed") or {}):
        return t["borrowed"][wid]                     # e.g. guns at Lützen roll on the Peninsular table
    kind = w.get("melee")
    if not kind:
        return tid
    if wid in t["weapons"] and kind in natives(t):
        return tid                                    # the table records this kind of fighting
    if w.get("melee_table"):
        return w["melee_table"]                       # e.g. sword, bayonet -> Visby table
    return tid if kind == t["native"] else d.melee_fallback[kind]


def natives(t: dict) -> set[str]:
    """Kinds of fighting a table's own data records: `native` plus any `also_native`
    (e.g. a Napoleonic table recording musket, sabre and bayonet wounds)."""
    return {t["native"], *(t.get("also_native") or [])}


def sourced(d: Data, t: dict, weapons: list[str]) -> dict:
    """Per-weapon location data from the source (`weapon_regions`): each listed weapon's
    multipliers turn the table's pooled weights into that weapon's own distribution.
    Weapons without their own data use the pooled odds."""
    base = [float(t["weights"].get(l["id"], 0)) for l in d.locations]
    tb = sum(base)
    out = {}
    for w in weapons:
        regs = (t.get("weapon_regions") or {}).get(w)
        if not regs:
            out[w] = [1.0] * len(base)
            continue
        ww = expand_regions(d, {"id": f"{t['id']}:{w}", "regions": regs})
        wv = [float(ww[l["id"]]) for l in d.locations]
        tw = sum(wv)
        out[w] = [(x / tw) / (b / tb) if b > 0 else 0.0 for x, b in zip(wv, base)]
    return out


def raw_bias(d: Data, wid: str) -> list[float]:
    w = d.weapons[wid]
    zb, lb = w.get("zone_bias") or {}, w.get("loc_bias") or {}
    return [float(zb.get(l["zone"], 1.0)) * float(lb.get(l["id"], 1.0)) for l in d.locations]


def recentre(d: Data, t: dict, weapons: list[str]) -> dict:
    """Find per-location corrections c so that the mix-weighted average of every
    weapon's distribution (base x bias x c) equals the source's base distribution."""
    base = [float(t["weights"].get(l["id"], 0)) for l in d.locations]
    tb = sum(base)
    base = [b / tb for b in base]
    mix = [(m["weapon"], float(m["pct"])) for m in t.get("weapon_mix") or [] if m.get("weapon")]
    tm = sum(p for _, p in mix)
    mix = [(w, p / tm) for w, p in mix]
    bias = {w: raw_bias(d, w) for w in set(weapons) | {w for w, _ in mix}}
    c = [1.0] * len(base)
    for _ in range(500):
        avg = [0.0] * len(base)
        for w, p in mix:
            v = [b * x * k for b, x, k in zip(base, bias[w], c)]
            z = sum(v)
            for i, x in enumerate(v):
                avg[i] += p * x / z
        err = max((abs(a - b) for a, b in zip(avg, base) if b > 0), default=0)
        c = [k * (b / a) if a > 0 and b > 0 else k for k, a, b in zip(c, avg, base)]
        if err < 1e-12:
            break
    else:
        d.warnings.append(f"tables/{t['id']}: weapon re-centring did not fully converge (max error {err:.2e})")
    return {w: [x * k for x, k in zip(bias[w], c)] for w in weapons}


def compute_multipliers(d: Data) -> None:
    need = {tid: set() for tid in d.tables}
    for tid in d.tables:
        for wid in available_weapons(d, tid):
            need[resolve_table(d, tid, wid)].add(wid)
    for tid, t in d.tables.items():
        ws = sorted(need[tid])
        mode = t["weapon_bias"]
        if mode == "pooled":
            d.wmult[tid] = {w: [1.0] * len(d.locations) for w in ws}
        elif mode == "recentred":
            d.wmult[tid] = recentre(d, t, ws)
        elif mode == "sourced":
            d.wmult[tid] = sourced(d, t, ws)
        else:
            d.wmult[tid] = {w: raw_bias(d, w) for w in ws}


def slot_layers(v) -> list[tuple[str, int, int]]:
    """Normalise a kit slot to [(material, lo, hi)] d100 bands; anything above the last hi is a gap."""
    if v is None:
        return []
    if isinstance(v, str):
        return [(v, 1, 100)]
    items = v if isinstance(v, list) else [v]
    out, lo = [], 1
    for i, it in enumerate(items):
        cover = int(it.get("cover", 101 - lo))
        if cover < 1:
            raise ValueError("cover must be at least 1")
        out.append((it["material"], lo, lo + cover - 1))
        lo += cover
    return out


def region_value(r: dict) -> float:
    return float(r["pct"] if "pct" in r else r["count"])


def expand_regions(d: Data, t: dict) -> dict:
    """Turn a source's coarse region totals into location weights.

    Each region: {pct or count, zone: <zone> | locs: [ids], split: {id: share} (optional)}.
    Counts (raw case numbers from a source) are normalised; percentages should sum to ~100.
    Without a split, the region's pct is shared by the locations' body.yaml exposure.
    """
    w = {l["id"]: 0.0 for l in d.locations}
    for r in t["regions"]:
        if "zone" in r:
            ids = [l["id"] for l in d.locations if l["zone"] == r["zone"]]
        else:
            ids = list(r["locs"])
        unknown = [i for i in ids if i not in d.loc] + [i for i in (r.get("split") or {}) if i not in ids]
        if unknown:
            raise DataError(f"tables/{t['id']}: region {r.get('label', r)} has unknown or out-of-region locations {unknown}")
        share = r.get("split") or {i: d.loc[i].get("exposure", 1.0) for i in ids}
        tot = sum(share.values())
        for i in ids:
            w[i] += region_value(r) * share.get(i, 0) / tot
    total = sum(region_value(x) for x in t["regions"]) + float(t.get("excluded_pct", 0))
    uses_pct = any("pct" in x for x in t["regions"])
    if uses_pct and any("count" in x for x in t["regions"]):
        raise DataError(f"tables/{t['id']}: regions mix pct and count")
    if uses_pct and abs(total - 100) > 2.0:   # sources often round to whole percents
        d.warnings.append(f"tables/{t['id']}: region totals sum to {total:g}%, normalised to 100")
    return w


def validate(d: Data) -> None:
    errors, warn = [], d.warnings
    classes = d.wounds["classes"]

    # body map
    ids = [l["id"] for l in d.locations]
    if len(ids) != len(set(ids)):
        errors.append("body.yaml: duplicate location ids")
    for l in d.locations:
        if l["zone"] not in d.zones:
            errors.append(f"body.yaml: {l['id']} has unknown zone {l['zone']}")
        if l["class"] not in classes:
            errors.append(f"body.yaml: {l['id']} has class {l['class']} missing from wounds.yaml")

    # wound classes
    for cid, c in classes.items():
        for sev in SEVERITIES:
            if sev not in c:
                errors.append(f"wounds.yaml: class {cid} missing severity {sev}")

    # battle map: every weapon has a reach, a range or is off the map
    CB = d.wounds["combat"]
    bands = CB.get("range", [])
    for wid, w in d.weapons.items():
        kinds = [k for k in ("reach", "range", "off_map") if k in w]
        if len(kinds) != 1:
            errors.append(f"weapons.yaml: {wid} needs exactly one of reach, range or off_map (has {kinds or 'none'})")
        elif "reach" in w and not (isinstance(w["reach"], int) and w["reach"] >= 1):
            errors.append(f"weapons.yaml: {wid} reach must be a whole number of hexes, 1 or more")
        elif "range" in w:
            r = w["range"]
            if not (isinstance(r, list) and len(r) == len(bands) and all(isinstance(x, int) and x >= 1 for x in r)
                    and r == sorted(set(r))):
                errors.append(f"weapons.yaml: {wid} range must be {len(bands)} increasing hex counts, one per band in wounds.yaml combat.range")
    for wid in CB.get("line_of_fire", {}).get("arcing", []):
        if "range" not in d.weapons.get(wid, {}):
            errors.append(f"wounds.yaml: combat.line_of_fire.arcing names {wid}, which is not a weapon with a range")
    impairs = set(d.wounds["vocabulary"]["impair"])
    mv = CB["move"]
    for k in ("halved_by", "crawl_by", "no_run_by"):
        for i in mv[k]:
            if i not in impairs:
                errors.append(f"wounds.yaml: combat.move.{k} names unknown impairment {i}")
    for s in mv["no_move_states"]:
        if s not in CB["states"]:
            errors.append(f"wounds.yaml: combat.move.no_move_states names unknown state {s}")

    # travel: terrain types and maps
    TT = d.terrain["terrain"]
    keys = {}
    for tid, t in TT.items():
        if len(str(t.get("key", ""))) != 1:
            errors.append(f"terrain.yaml: {tid} key must be one character")
        elif t["key"] in keys:
            errors.append(f"terrain.yaml: {tid} and {keys[t['key']]} share key {t['key']!r}")
        keys[t["key"]] = tid
        if t.get("cost") is not None and not (isinstance(t["cost"], (int, float)) and t["cost"] > 0 and round(t["cost"] * 100) == t["cost"] * 100):
            errors.append(f"terrain.yaml: {tid} cost must be positive with at most two decimals, or null for impassable")
        if not (isinstance(t.get("colour"), list) and len(t["colour"]) == 2):
            errors.append(f"terrain.yaml: {tid} colour must be [light, dark]")
    fw = d.terrain.get("fight_within", 1)
    if not isinstance(fw, int) or isinstance(fw, bool) or fw < 0:
        errors.append("terrain.yaml: fight_within must be a whole number of hexes, 0 or more")
    for fid, f in d.terrain["forces"].items():
        if not (isinstance(f.get("kmh"), (int, float)) and f["kmh"] > 0):
            errors.append(f"terrain.yaml: force type {fid} needs a positive kmh")
        for t in f.get("cannot_enter", []):
            if t not in TT:
                errors.append(f"terrain.yaml: force type {fid} cannot_enter names unknown terrain {t}")
    for mid, m in d.maps.items():
        rows = m["rows"]
        if not rows or len({len(r) for r in rows}) != 1:
            errors.append(f"maps/{mid}: terrain rows must all be the same length")
            continue
        bad = sorted({ch for r in rows for ch in r} - set(keys))
        if bad:
            errors.append(f"maps/{mid}: unknown terrain keys {bad}")
        cols, nrows = len(rows[0]), len(rows)
        inside = lambda h: isinstance(h, list) and len(h) == 2 and 0 <= h[0] < cols and 0 <= h[1] < nrows
        if not (isinstance(m.get("hex_km"), (int, float)) and m["hex_km"] > 0):
            errors.append(f"maps/{mid}: hex_km must be positive")
        for pl in m.get("places", []):
            if pl.get("kind") not in d.terrain["place_kinds"]:
                errors.append(f"maps/{mid}: place {pl.get('name')} has unknown kind {pl.get('kind')}")
            if set(pl.get("depot") or []) - {fo.get("side") for fo in m.get("forces", [])}:
                errors.append(f"maps/{mid}: place {pl.get('name')} is a depot of a side with no force on the map")
            if not inside(pl.get("hex")):
                errors.append(f"maps/{mid}: place {pl.get('name')} is off the map")
            elif ("depth" in pl or "current" in pl) and not (keys.get(rows[pl["hex"][1]][pl["hex"][0]]) == "ford" and pl.get("depth", 0) > 0 and pl.get("current", -1) >= 0):
                errors.append(f"maps/{mid}: place {pl.get('name')} sets a ford's depth and current: both, on a ford hex")
        for fo in m.get("forces", []):
            if fo.get("type") not in d.terrain["forces"]:
                errors.append(f"maps/{mid}: force {fo.get('name')} has unknown type {fo.get('type')}")
            if not inside(fo.get("hex")):
                errors.append(f"maps/{mid}: force {fo.get('name')} is off the map")
            elif TT[keys.get(rows[fo['hex'][1]][fo['hex'][0]], 'open')].get("cost") is None:
                errors.append(f"maps/{mid}: force {fo.get('name')} starts on impassable terrain")
            if not (isinstance(fo.get("men"), int) and fo["men"] >= 1):
                errors.append(f"maps/{mid}: force {fo.get('name')} needs men, a whole number of 1 or more")
            if not isinstance(fo.get("tools"), bool):
                errors.append(f"maps/{mid}: force {fo.get('name')} needs tools: true or false")

    # calendar and weather
    WX = d.weather
    if WX:
        winds = [w["id"] for w in WX["winds"]]
        for cid, c in WX["conditions"].items():
            if c.get("min_wind") and c["min_wind"] not in winds:
                errors.append(f"weather.yaml: condition {cid} min_wind {c['min_wind']} is not a wind")
        for row in WX["intensity"]:
            for k in ("rain", "snow"):
                if row[k] not in WX["conditions"]:
                    errors.append(f"weather.yaml: intensity names unknown condition {row[k]}")
        errors += _light_errors(WX)
        errors += _cold_errors(d)
        for kid, cl in WX["climates"].items():
            for k in ("high", "low", "rain", "fog"):
                if len(cl.get(k, [])) != 12:
                    errors.append(f"weather.yaml: climate {kid} {k} needs 12 months")
        for k in ("mud", "snow"):
            for t in WX["march"][k]:
                if t not in TT:
                    errors.append(f"weather.yaml: march.{k} names unknown terrain {t}")
        for wid, w in d.weapons.items():
            if w.get("ignition") and w["ignition"] not in WX["battle"]["misfire"]:
                errors.append(f"weapons.yaml: {wid} ignition {w['ignition']} is not in weather.yaml battle.misfire")
        for mid, m in d.maps.items():
            if not re.fullmatch(r"-?\d{1,4}-\d{2}-\d{2}", str(m.get("start_date", ""))):
                errors.append(f"maps/{mid}: start_date must be YYYY-MM-DD")
            if m.get("calendar") not in ("julian", "gregorian"):
                errors.append(f"maps/{mid}: calendar must be julian or gregorian")
            if not (isinstance(m.get("latitude"), (int, float)) and -66 <= m["latitude"] <= 66):
                errors.append(f"maps/{mid}: latitude must be between -66 and 66")
            if m.get("climate") not in WX["climates"]:
                errors.append(f"maps/{mid}: climate must be one of {sorted(WX['climates'])}")
            if not isinstance(m.get("climate_shift", 0), (int, float)):
                errors.append(f"maps/{mid}: climate_shift must be a number")

    errors += [f"{kind}/{k}: period must be a name" for kind, items in (("maps", d.maps), ("fields", d.fields))
               for k, x in items.items() if "period" in x and not (isinstance(x["period"], str) and x["period"].strip())]

    # camp disease
    if d.weather.get("wind_points"):
        errors += _wind_errors(d)

    if d.disease:
        errors += _disease_errors(d, TT)

    # unit combat
    if d.units:
        errors += _units_errors(d)
        errors += _fields_errors(d)
    for T in d.teams.values():
        errors += _team_errors(d, T)
    for E in d.equipment.values():
        errors += _equipment_errors(d, E)
    for J in d.jobs.values():
        errors += _jobs_errors(d, J)
    for R in d.replacements.values():
        errors += _replacement_errors(d, R)
    if d.events:
        errors += _events_errors(d)
    if d.checks:
        errors += _checks_errors(d)
    if d.ranks:
        errors += _ranks_errors(d)
    if d.weights:
        errors += _weights_errors(d)
    if d.supplies:
        errors += _supplies_errors(d)
    if d.kit:
        errors += _kit_errors(d)
    if d.ageing:
        AG, stats = d.ageing, {"str", "agi", "end", "wits", "nerve", "pres"}
        fr = [b.get("from") for b in AG.get("decline", [])]
        if not fr or fr != sorted(fr) or fr[0] != 0:
            errors.append("ageing.yaml: decline bands must rise from 0")
        for b in AG.get("decline", []):
            for k, v in b.items():
                if k != "from" and (k not in stats or not (isinstance(v, list) and len(v) == 2 and v[0] >= 1 and v[1] >= 1)):
                    errors.append(f"ageing.yaml: decline {b.get('from')} {k} must be [dice, sides] of a characteristic")
        for k in ("pres", "wits", "nerve"):
            if not isinstance((AG.get("maturity") or {}).get(k, {}).get("cap"), int):
                errors.append(f"ageing.yaml: maturity {k} needs to and cap")
        EN = AG.get("enlist") or {}
        for eid, E in (EN.get("eras") or {}).items():
            spans = [E, *(E.get("regions") or {}).values()]
            if eid not in d.teams or any(not (0 < x.get("min", E["min"]) < x.get("max", E["max"])) for x in spans):
                errors.append(f"ageing.yaml: enlist {eid} needs a known era and min under max")
        if EN and not all(0 <= v.get(k, 0) <= 100 for v in EN.get("shares", {}).values() for k in ("under", "older")):
            errors.append("ageing.yaml: enlist shares must be 0-100")
    if d.loads:
        LD = d.loads
        ups = [b.get("upto") for b in LD.get("bands", [])]
        if not ups or ups != sorted(ups) or any(not (0 < b.get("march", 0) <= 100) for b in LD["bands"]):
            errors.append("loads.yaml: bands must rise, each with a march % 1-100")
        if [r.get("from") for r in LD.get("strength", [])][:1] != [0]:
            errors.append("loads.yaml: strength rows must start from 0")
        for eid, E in (LD.get("eras") or {}).items():
            if eid not in d.teams:
                errors.append(f"loads.yaml: unknown era {eid}")
            if set(E.get("kg", {})) != set(LD.get("orders", {})) or E.get("fights_in") not in LD.get("orders", {}):
                errors.append(f"loads.yaml: {eid} needs kg for every order and a fights_in order")
    if d.stress:
        SX = d.stress
        if [r.get("id") for r in SX.get("results", [])] != ["shaken", "strained", "exhaustion", "severe"]:
            errors.append("stress.yaml: results must be shaken, strained, exhaustion, severe")
        for k, t in (SX.get("treatment") or {}).items():
            if set(t.get("rtd", {})) != {"shaken", "strained", "exhaustion", "severe"} or not (t.get("strain") == "all" or isinstance(t.get("strain"), (int, float))):
                errors.append(f"stress.yaml: treatment {k} needs rtd for every state and a strain lifted")
            if any(e not in d.teams for e in t.get("eras", [])):
                errors.append(f"stress.yaml: treatment {k} names an unknown era")
        for e, n in (SX.get("names") or {}).items():
            if e not in d.teams or len(n) != 3:
                errors.append(f"stress.yaml: names for {e} must be three, for a known era")
    if d.hazards:
        HZ = d.hazards
        if any(e not in d.teams for e in HZ.get("swimmers", {})):
            errors.append("hazards.yaml: swimmers names an unknown era")
        if len(HZ["swim"]["load"]) != 6 or len(HZ["climb"]["load"]) != 6:
            errors.append("hazards.yaml: swim and climb load need one figure for each of the six load bands")
        for r in HZ["falls"]["heights"]:
            if len(r["bands"]) != 5 or r["bands"] != sorted(r["bands"]):
                errors.append(f"hazards.yaml: fall row {r['name']} needs five rising bands")
        for k, l in HZ["falls"]["landings"].items():
            if l["zones"][-1][0] != 100:
                errors.append(f"hazards.yaml: landing {k} zones must reach 100")
    if d.languages:
        LG = d.languages
        known = set(LG["tongues"])
        for eid, armies in LG.get("armies", {}).items():
            if eid not in d.teams:
                errors.append(f"languages.yaml: unknown era {eid}")
                continue
            regions = {r["id"] for r in d.teams[eid]["regions"]}
            for rid, A in armies.items():
                if rid not in regions:
                    errors.append(f"languages.yaml: {eid} has no army {rid}")
                if sum(s for _, s in A["own"]) != 100:
                    errors.append(f"languages.yaml: {eid} {rid} own tongues must share 100")
                for t in [t for t, _ in A["own"]] + [t for t, _, _ in A.get("others", [])] + [A.get("enemy")]:
                    if t not in known:
                        errors.append(f"languages.yaml: {eid} {rid} names an unknown tongue {t}")
                for t, _, (lo, hi) in A.get("others", []):
                    if t in known and hi > LG["tongues"][t].get("cap", LG["max"]):
                        errors.append(f"languages.yaml: {eid} {rid} {t} range passes its cap")
            for r in d.teams[eid]["regions"]:
                if r["id"] not in armies:
                    errors.append(f"languages.yaml: {eid} army {r['id']} has no tongues")
        for a, b, _ in LG.get("related", []):
            if a not in known or b not in known:
                errors.append(f"languages.yaml: related names an unknown tongue ({a}, {b})")
        for m, t in (LG.get("maps") or {}).items():
            for x in (t if isinstance(t, list) else [t]):
                if x not in known and x != "none":
                    errors.append(f"languages.yaml: map {m} names an unknown tongue {x}")
        if not isinstance(LG.get("place_km", 0), (int, float)) or LG.get("place_km", 0) < 0:
            errors.append("languages.yaml: place_km must be a number of km, 0 or more")
        for mid, m in d.maps.items():
            for pl in m.get("places") or []:
                ts = pl.get("tongues")
                if ts is not None and not (isinstance(ts, list) and ts and all(x in known for x in ts)):
                    errors.append(f"maps/{mid}: place {pl.get('name')} tongues must be a list of known tongues")
        traits = {o[k]["text"] for T in d.teams.values() for o in T["origins"] for k in ("trait", "drawback")}
        for t in LG.get("traits", {}):
            if t not in traits:
                errors.append(f"languages.yaml: no background has the trait {t!r}")
    for k in (d.training or {}).get("courses", []):
        for eid in k["eras"]:
            if eid not in d.teams:
                errors.append(f"training.yaml: course {k['id']} names an unknown era {eid}")
            elif k.get("rank") and k["rank"] not in {r["id"] for r in ((d.ranks or {}).get("eras", {}).get(eid) or {}).get("ladder", [])}:
                errors.append(f"training.yaml: course {k['id']} opens {k['rank']}, not a rank in {eid}")
    errors += _papers_errors(d)
    if d.patrons:
        PT, diffs = d.patrons, {x["id"] for x in d.checks.get("difficulty", [])}
        for f in PT["favours"]:
            if f["difficulty"] not in diffs:
                errors.append(f"patrons.yaml: favour {f['id']} has an unknown difficulty")
        for eid, rows in PT.get("fate", {}).items():
            if eid not in d.teams:
                errors.append(f"patrons.yaml: fate for an unknown era {eid}")
            if any(r["id"] not in PT["fates"] for r in rows) or sum(r["chance"] for r in rows) > 100:
                errors.append(f"patrons.yaml: {eid} fates must be known and total at most 100")
        if any(f["clients"] not in ("heir", "half", "ruin", "choose") for f in PT["fates"].values()):
            errors.append("patrons.yaml: a fate's clients must be heir, half, ruin or choose")
    if d.prisoners:
        for eid, cs in (d.prisoners.get("eras") or {}).items():
            if eid not in d.teams:
                errors.append(f"prisoners.yaml: unknown era {eid}")
            for c in cs:
                k, s_ = c.get("capture", [0, 0])
                if not (0 <= k <= s_ <= 100) or not all(isinstance(c.get(x), (int, float)) for x in ("release", "hazard", "escape", "home", "recapture")):
                    errors.append(f"prisoners.yaml: {eid} {c.get('id')} needs capture bands and release, hazard, escape, home, recapture")
    if d.training:
        TR, skills = d.training, {s["id"] for T in d.teams.values() for s in T["skills"]}
        for m in TR.get("masters", []):
            if (m.get("skill") not in skills and m.get("skill") != "tongue") or not (isinstance(m.get("fee"), (int, float)) and m["fee"] >= 0) or not set(m.get("places") or []) <= JOB_PLACES:
                errors.append(f"training.yaml: master {m.get('name')} needs a known skill, a fee and known places")
        for k in ("master_skill", "teammate_gap"):
            if not isinstance(TR.get(k), int):
                errors.append(f"training.yaml: {k} must be a whole number")
    if d.experience:
        X = d.experience
        g = X.get("gain")
        if not (isinstance(g, list) and len(g) == 2 and all(isinstance(v, int) for v in g) and 1 <= g[0] <= g[1]):
            errors.append("experience.yaml: gain must be [low, high], whole numbers from 1")
        for k in ("season_days", "days_a_year"):
            if not (isinstance(X.get(k), int) and X[k] > 0):
                errors.append(f"experience.yaml: {k} must be a positive whole number")
    errors += _ground_seed_errors(d, TT)

    # camps and works
    WK = d.works
    EW, HW = WK.get("edge_works", {}), WK.get("hex_works", {})
    for k in ("work_share", "camp_area_min", "evening_hours"):
        if not (isinstance(WK.get(k), (int, float)) and WK[k] > 0):
            errors.append(f"works.yaml: {k} must be positive")
    for ft in d.terrain["forces"]:
        if ft not in WK.get("camp_area", {}):
            errors.append(f"works.yaml: camp_area has no entry for force type {ft}")
    for cid, c in WK.get("camps", {}).items():
        for w in c.get("works", []):
            if w not in EW and w not in HW:
                errors.append(f"works.yaml: camp {cid} names unknown work {w}")
        for t in c.get("terrain", []):
            if t not in TT:
                errors.append(f"works.yaml: camp {cid} names unknown terrain {t}")
        if c.get("layout") not in (None, "stakes", "fortified"):
            errors.append(f"works.yaml: camp {cid} layout must be stakes or fortified")
        laid = {None: set(), "stakes": {"stakes"}, "fortified": {"ditch", "bank", "palisade", "gate"}}.get(c.get("layout"))
        if laid is not None and set(c.get("works", [])) != laid:
            errors.append(f"works.yaml: camp {cid} works must be what its layout builds: {sorted(laid) or 'none'}")
    for wid, w in EW.items():
        if w.get("cover_side", "both") not in ("both", "high"):
            errors.append(f"works.yaml: {wid} cover_side must be both or high")
    for wid, w in {**EW, **HW}.items():
        if w.get("breach") is not None and not (isinstance(w["breach"], int) and w["breach"] >= 1):
            errors.append(f"works.yaml: {wid} breach must be a whole number of man-rounds or null")

    # lethality presets
    LT = d.wounds.get("lethality") or {}
    if LT.get("default") not in (LT.get("presets") or {}):
        errors.append("wounds.yaml: lethality.default must name one of lethality.presets")
    for pid, pr in (LT.get("presets") or {}).items():
        if not (isinstance(pr.get("fate"), int) and pr["fate"] >= 0 and float(pr.get("blood", 0)) >= 1
                and isinstance(pr.get("stop_bonus"), int) and isinstance(pr.get("stop_critical_only"), bool)):
            errors.append(f"wounds.yaml: lethality preset {pid} needs fate (>= 0), blood (>= 1), stop_bonus and stop_critical_only")

    # weapons
    for wid, w in d.weapons.items():
        mech = w.get("mechanisms", {})
        bad = set(mech) - set(MECHANISMS)
        if bad:
            errors.append(f"weapons.yaml: {wid} unknown mechanisms {sorted(bad)}")
        if sum(mech.values()) != 100:
            errors.append(f"weapons.yaml: {wid} mechanisms sum to {sum(mech.values())}, not 100")
        if w.get("choose") and len([m for m, v in mech.items() if v]) < 2:
            errors.append(f"weapons.yaml: {wid} has choose but fewer than two mechanisms")
        for z in w.get("zone_bias", {}):
            if z not in d.zones:
                errors.append(f"weapons.yaml: {wid} zone_bias has unknown zone {z}")
        for lid in w.get("loc_bias", {}) or {}:
            if lid not in d.loc:
                errors.append(f"weapons.yaml: {wid} loc_bias has unknown location {lid}")

    # tables
    for tid, t in d.tables.items():
        w = t.get("weights", {})
        unknown = set(w) - set(d.loc)
        if unknown:
            errors.append(f"tables/{tid}: unknown locations {sorted(unknown)}")
        missing = set(d.loc) - set(w)
        if missing:
            warn.append(f"tables/{tid}: no weight for {sorted(missing)} (treated as 0)")
        if any(v < 0 for v in w.values()):
            errors.append(f"tables/{tid}: negative weight")
        if sum(w.values()) <= 0:
            errors.append(f"tables/{tid}: weights sum to zero")
        for wid in t.get("weapons", []):
            if wid not in d.weapons:
                errors.append(f"tables/{tid}: unknown weapon {wid}")
        for wid in t.get("era_melee") or []:
            if wid not in d.weapons or not d.weapons[wid].get("melee_table"):
                errors.append(f"tables/{tid}: era_melee {wid} needs a close-combat weapon with a melee_table")
        for wid, src in (t.get("borrowed") or {}).items():
            if wid not in d.weapons or src not in d.tables or wid not in d.tables[src]["weapons"]:
                errors.append(f"tables/{tid}: borrowed {wid} needs a weapon that table {src} lists as its own")

    # modifiers
    sides = {"L", "R", "C"}
    for mid, m in d.modifiers.items():
        for z in m.get("zone", {}) or {}:
            if z not in d.zones:
                errors.append(f"modifiers.yaml: {mid} unknown zone {z}")
        for sd in m.get("side", {}) or {}:
            if sd not in sides:
                errors.append(f"modifiers.yaml: {mid} unknown side {sd}")
        for lid in m.get("loc", {}) or {}:
            if lid not in d.loc:
                errors.append(f"modifiers.yaml: {mid} unknown location {lid}")
        for part in ("zone", "side", "loc"):
            if any(v < 0 for v in (m.get(part) or {}).values()):
                errors.append(f"modifiers.yaml: {mid} negative multiplier")

    # armour
    mats, slots = d.armor.get("materials", {}), d.armor.get("slots", {})
    for mid, mat in mats.items():
        for mech in MECHANISMS:
            if not isinstance(mat.get(mech), int) or not 0 <= mat[mech] <= 3:
                errors.append(f"armor.yaml: material {mid} needs {mech} steps 0-3")
    body_slots = {l["armor"] for l in d.locations}
    for s_ in body_slots - set(slots):
        warn.append(f"armor.yaml: body slot {s_} not listed under slots")
    for mid, mat in mats.items():
        for th, v in (mat.get("threats") or {}).items():
            if th not in THREATS or not isinstance(v, int) or not 0 <= v <= 3:
                errors.append(f"armor.yaml: material {mid} threat {th} must be one of {THREATS} with steps 0-3")
    for kid, kit in d.armor.get("kits", {}).items():
        for slot, v in (kit.get("slots") or {}).items():
            if slot not in body_slots:
                errors.append(f"armor.yaml: kit {kid} unknown slot {slot}")
            try:
                layers = slot_layers(v)
            except (TypeError, KeyError, ValueError) as e:
                errors.append(f"armor.yaml: kit {kid} slot {slot}: {e}")
                continue
            for mat, lo, hi in layers:
                if mat not in mats:
                    errors.append(f"armor.yaml: kit {kid} unknown material {mat}")
            if layers and layers[-1][2] > 100:
                errors.append(f"armor.yaml: kit {kid} slot {slot} layers exceed 100%")
            if any(hi % 10 for _, _, hi in layers):
                errors.append(f"armor.yaml: kit {kid} slot {slot} covers must be in tens (read on the attack's units digit)")
    for wid, w in d.weapons.items():
        if w.get("threat") and w["threat"] not in THREATS:
            errors.append(f"weapons.yaml: {wid} threat must be one of {THREATS}")
        if w.get("mechanisms", {}).get("ballistic") and not w.get("threat"):
            errors.append(f"weapons.yaml: {wid} has a ballistic mechanism but no threat level")
    for wid, w in d.weapons.items():
        for mech in (w.get("armor_defeat") or {}):
            if mech not in MECHANISMS:
                errors.append(f"weapons.yaml: {wid} armor_defeat unknown mechanism {mech}")

    for kind, tid in d.melee_fallback.items():
        if tid not in d.tables:
            errors.append(f"weapons.yaml: melee_fallback {kind} -> unknown table {tid}")
        elif d.tables[tid]["native"] != kind:
            errors.append(f"weapons.yaml: melee_fallback {kind} -> {tid}, whose native fighting is {d.tables[tid]['native']}")
    for wid in d.melee_everywhere:
        if wid not in d.weapons or not d.weapons[wid].get("melee"):
            errors.append(f"weapons.yaml: melee_everywhere {wid} must be a weapon with a melee kind")
    for wid, w in d.weapons.items():
        mt = w.get("melee_table")
        if mt and (mt not in d.tables or w.get("melee") not in natives(d.tables[mt])):
            errors.append(f"weapons.yaml: {wid} melee_table {mt} must be a table whose native fighting is {w.get('melee')}")
        for m in w.get("fallback_mods") or []:
            if m not in d.modifiers:
                errors.append(f"weapons.yaml: {wid} fallback_mods names unknown situation {m}")
            elif mt and m not in (d.tables[mt].get("modifiers") or []):
                errors.append(f"weapons.yaml: {wid} fallback_mods {m} is not offered on {mt}")
        if w.get("melee") and w["melee"] not in ("armed", "unarmed"):
            errors.append(f"weapons.yaml: {wid} melee must be armed or unarmed")
    for wid, w in d.weapons.items():
        if w.get("icon") and w["icon"] not in FIG_NAMES["icon"]:
            errors.append(f"weapons.yaml: {wid} icon {w['icon']} is not one the figures can draw")
    for kid, kit in d.armor.get("kits", {}).items():
        errors += look_errors(f"armor.yaml: kit {kid}", kit.get("look"))
    for kid, kit in d.armor.get("kits", {}).items():
        if "shield" in kit and not isinstance(kit["shield"], bool):
            errors.append(f"armor.yaml: kit {kid} shield must be true or false")
    for tid, t in d.tables.items():
        if t["assumes_shield"] and "no_shield" not in (t.get("modifiers") or []):
            errors.append(f"tables/{tid}: assumes_shield needs the no_shield situation in its modifiers")
    # conflict histories
    battles = {t.get("battle") for t in d.tables.values()}
    for b in sorted(battles - set(d.conflicts)):
        warn.append(f"conflicts.yaml: no history for table group '{b}'")
    for b, c in d.conflicts.items():
        if b not in battles:
            errors.append(f"conflicts.yaml: '{b}' matches no table's battle group")
        offered = set(d.melee_everywhere)
        for t in d.tables.values():
            if t.get("battle") == b:
                offered |= set(t["weapons"])
        sides = {sd["name"] for sd in c.get("sides") or []}
        for mp in (c.get("map") if isinstance(c.get("map"), list) else [c.get("map")]):
            if mp is None:
                continue
            bb = mp.get("bbox") if isinstance(mp, dict) else None
            if not (isinstance(bb, list) and len(bb) == 4 and bb[0] < bb[2] and bb[1] < bb[3]
                    and -180 <= bb[0] and bb[2] <= 180 and -90 <= bb[1] and bb[3] <= 90):
                errors.append(f"conflicts.yaml: {b} map bbox must be [west, south, east, north] in degrees")
            for site in (mp.get("sites") or []) if isinstance(mp, dict) else []:
                if not (isinstance(site, dict) and site.get("name") and -90 <= float(site.get("lat", 999)) <= 90
                        and -180 <= float(site.get("lon", 999)) <= 180):
                    errors.append(f"conflicts.yaml: {b} map site {site} needs name, lat and lon")
        for sd in c.get("sides") or []:
            errors += look_errors(f"conflicts.yaml: {b} side {sd['name']}", sd.get("look"))
        for ex in c.get("examples") or []:
            errors += look_errors(f"conflicts.yaml: {b} example {ex['name']}", ex.get("look"))
            errors += image_errors(f"conflicts.yaml: {b} example {ex['name']}", ex.get("image"))
            if ex["kit"] not in d.armor["kits"]:
                errors.append(f"conflicts.yaml: {b} example '{ex['name']}' has unknown kit {ex['kit']}")
            if ex["weapon"] not in d.weapons:
                errors.append(f"conflicts.yaml: {b} example '{ex['name']}' has unknown weapon {ex['weapon']}")
            elif ex.get("elsewhere"):
                if not any(ex["weapon"] in t["weapons"] for t in d.tables.values()):
                    errors.append(f"conflicts.yaml: {b} example '{ex['name']}' is marked elsewhere but no table offers {ex['weapon']}")
            elif ex["weapon"] not in offered:
                warn.append(f"conflicts.yaml: {b} example '{ex['name']}' carries {ex['weapon']}, which no table in the group offers")
            if sides and ex.get("side") not in sides:
                errors.append(f"conflicts.yaml: {b} example '{ex['name']}' names unknown side {ex.get('side')}")
        covered = {ex.get("side") for ex in c.get("examples") or []}
        for sd in sorted(sides - covered):
            errors.append(f"conflicts.yaml: {b} side '{sd}' has no example combatant")
    seen = {}
    for tid, t in d.tables.items():
        if t["native"] not in ("armed", "unarmed", "gunfire"):
            errors.append(f"tables/{tid}: native must be armed, unarmed or gunfire")
        if t["weapon_bias"] not in ("raw", "recentred", "pooled", "sourced"):
            errors.append(f"tables/{tid}: weapon_bias must be raw, recentred, pooled or sourced")
        for k in t.get("also_native") or []:
            if k not in ("armed", "unarmed", "gunfire") or k == t["native"]:
                errors.append(f"tables/{tid}: also_native {k} must be another of armed, unarmed, gunfire")
        for wid, regs in (t.get("weapon_regions") or {}).items():
            if wid not in t["weapons"]:
                errors.append(f"tables/{tid}: weapon_regions for {wid}, which the table does not list")
                continue
            try:
                ww = expand_regions(d, {"id": f"{tid}:{wid}", "regions": regs})
            except DataError as e:
                errors.append(str(e)); continue
            gaps = [l for l, v in ww.items() if v > 0 and not t["weights"].get(l)]
            if gaps:
                errors.append(f"tables/{tid}: {wid} has hits at {gaps}, where the pooled table has none")
        if t.get("weapon_regions") and t["weapon_bias"] != "sourced":
            errors.append(f"tables/{tid}: weapon_regions needs weapon_bias: sourced")
        if t["armor"] not in ("allowed", "baked_in"):
            errors.append(f"tables/{tid}: armor must be allowed or baked_in")
        if t["weapon_bias"] == "recentred" and not any(m.get("weapon") for m in t.get("weapon_mix") or []):
            errors.append(f"tables/{tid}: recentred needs a weapon_mix that names weapons")
        for m in t.get("weapon_mix") or []:
            if m.get("weapon") and m["weapon"] not in d.weapons:
                errors.append(f"tables/{tid}: weapon_mix names unknown weapon {m['weapon']}")
            if not m.get("weapon") and not m.get("label"):
                errors.append(f"tables/{tid}: weapon_mix entries need a weapon or a label")
        key = (t.get("battle"), t.get("label", t["name"]))
        if key in seen:
            errors.append(f"tables/{tid}: label '{key[1]}' duplicates {seen[key]} in group '{key[0]}'")
        seen[key] = tid
    for tid, t in d.tables.items():
        mix = t.get("weapon_mix") or []
        if mix and abs(sum(m["pct"] for m in mix) - 100) > 1:
            errors.append(f"tables/{tid}: weapon_mix must sum to 100")
        for mid in t.get("modifiers") or []:
            if mid not in d.modifiers:
                errors.append(f"tables/{tid}: unknown modifier {mid}")
    for mech, spec in (d.wounds["severity"].get("by_mechanism") or {}).items():
        if mech not in MECHANISMS:
            errors.append(f"wounds.yaml: severity table for unknown mechanism {mech}")
        covered = [z for tbl in spec["tables"] for z in tbl["zones"]]
        if sorted(covered) != sorted(d.zones):
            errors.append(f"wounds.yaml: {mech} severity tables must cover each zone once")
        for tbl in spec["tables"]:
            nums = sorted(n for t in tbl["tiers"] for n in range(t["d100"][0], t["d100"][1] + 1))
            if nums != list(range(1, 101)):
                errors.append(f"wounds.yaml: {mech} severity table {tbl['zones']} must cover 1-100 exactly once")
    for m in MECHANISMS:
        if m not in d.wounds["mechanisms"]:
            errors.append(f"wounds.yaml: no rules for mechanism {m}")

    if errors:
        raise DataError("\n".join(errors))


DISEASE_FACTORS = {"poor", "good", "staying", "crowded", "marsh", "town", "upland", "warm", "hot", "cold_wet", "plague"}


def _disease_errors(d: Data, terrain: dict) -> list[str]:
    """disease.yaml: the track, hygiene and care for every camp, terrains, and each disease."""
    D, errors = d.disease, []
    steps = D.get("steps", [])
    if steps[:1] != ["healed"] or len(steps) < 3:
        errors.append("disease.yaml: steps must start with healed")
    errors += [f"disease.yaml: {k} must be one of the steps" for k in ("unfit_from", "carried_from") if D.get(k) not in steps]
    errors += _disease_camp_errors(d)
    errors += [f"disease.yaml: in_fight.{k} is not a step" for k in D.get("in_fight", {}) if k not in steps]
    for k, ts in D.get("terrain_factors", {}).items():
        errors += [f"disease.yaml: terrain_factors.{k} names unknown terrain {t}" for t in ts if t not in terrain]
    for did, x in D.get("diseases", {}).items():
        errors += _one_disease_errors(did, x, steps)
    if "wounds" in D:
        errors += _wound_track_errors(d, steps)
    return errors


def _wound_track_errors(d: Data, steps: list) -> list[str]:
    """disease.yaml wounds: the two cases, starting steps, fever chances and care."""
    W, errors = d.disease["wounds"], []
    V = d.wounds["vocabulary"]
    for k in ("wound", "fever"):
        if not isinstance(W.get(k, {}).get("virulence"), int):
            errors.append(f"disease.yaml: wounds.{k} needs a whole-number virulence")
    if set(W.get("start", {})) != {"light", "serious", "critical"} or any(v not in steps for v in W["start"].values()):
        errors.append("disease.yaml: wounds.start must give a step for light, serious and critical")
    if any(k not in V["lethal"]["order"] or v not in steps for k, v in W.get("clock_step", {}).items()):
        errors.append("disease.yaml: wounds.clock_step must map lethalities to steps")
    if set(W.get("fever_chance", {})) != set(V["infection"]["order"]):
        errors.append("disease.yaml: wounds.fever_chance needs every infection risk")
    if set(W.get("fever_care", {})) != set(d.disease.get("recovery", {}).get("care", {})):
        errors.append("disease.yaml: wounds.fever_care needs every care level")
    lo, hi = (W.get("fever_after") or [0, -1])[:2]
    if not (isinstance(lo, int) and isinstance(hi, int) and 1 <= lo <= hi):
        errors.append("disease.yaml: wounds.fever_after must be [low, high] days")
    return errors


def _disease_camp_errors(d: Data) -> list[str]:
    D, errors = d.disease, []
    for k in ("camp_hygiene", "camp_care"):
        errors += [f"disease.yaml: {k} has no entry for {camp}" for camp in ["none", *d.works.get("camps", {})] if camp not in D.get(k, {})]
    if any(v not in D.get("hygiene", []) for v in D.get("camp_hygiene", {}).values()):
        errors.append("disease.yaml: camp_hygiene must use the hygiene levels")
    if any(v not in D.get("recovery", {}).get("care", {}) for v in D.get("camp_care", {}).values()):
        errors.append("disease.yaml: camp_care must use the recovery care levels")
    return errors


def _one_disease_errors(did: str, x: dict, steps: list) -> list[str]:
    errors = []
    lo, hi = (x.get("incubation") or [0, -1])[:2]
    if not (isinstance(lo, int) and isinstance(hi, int) and 1 <= lo <= hi):
        errors.append(f"disease.yaml: {did} incubation must be [low, high] days")
    ups = [r.get("upto") for r in x.get("peak", [])]
    if not ups or ups != sorted(ups) or ups[-1] != 100 or any(r.get("step") not in steps[1:] for r in x["peak"]):
        errors.append(f"disease.yaml: {did} peak must rise to 100 and name steps past healed")
    bad = [k for k in [*x.get("mods", {}), *x.get("needs", [])] if k not in DISEASE_FACTORS]
    if bad:
        errors.append(f"disease.yaml: {did} uses unknown factors {bad}")
    if not isinstance(x.get("virulence"), int) or not isinstance(x.get("base"), (int, float)):
        errors.append(f"disease.yaml: {did} needs a whole-number virulence and a number for base")
    return errors


def _units_errors(d: Data) -> list[str]:
    """units.yaml: qualities, tempos, missile weapons, deaths and morale."""
    U, errors = d.units, []
    for q, v in U.get("quality", {}).items():
        if not all(isinstance(v.get(k), int) for k in ("attack", "defence", "nerve")):
            errors.append(f"units.yaml: quality {q} needs whole-number attack, defence and nerve")
    for k in ("melee", "missile", "rout"):
        if not (isinstance(U.get(k, {}).get("tempo"), (int, float)) and U[k]["tempo"] > 0):
            errors.append(f"units.yaml: {k}.tempo must be positive")
    for wid in U.get("missile", {}).get("rate", {}):
        if wid not in d.weapons or "range" not in d.weapons[wid]:
            errors.append(f"units.yaml: missile rate for {wid}, which is not a weapon with a range")
    order = d.wounds["vocabulary"]["lethal"]["order"]
    errors += [f"units.yaml: dead_if names unknown lethality {x}" for x in U.get("dead_if", []) if x not in order]
    errors += [f"units.yaml: modern_fire names unknown weapon {w}" for w in U.get("modern_fire", {}).get("weapons", []) if w not in d.weapons]
    if not isinstance(U.get("rout", {}).get("exchanges"), int):
        errors.append("units.yaml: rout.exchanges must be a whole number")
    return errors + _units_extra_errors(d)


def _units_extra_errors(d: Data) -> list[str]:
    """units.yaml: the ground, heroes and the aftermath."""
    U, errors = d.units, []
    G = U.get("ground", {})
    if G and ("open" not in G or not all(isinstance(g.get("move"), int) and g["move"] >= 1 for g in G.values())):
        errors.append("units.yaml: ground needs open, and a whole-number move of 1 or more for each kind")
    if "heroes" in U and not all(isinstance(U["heroes"].get(k), (int, float)) and U["heroes"][k] > 0 for k in ("tempo", "exposure")):
        errors.append("units.yaml: heroes.tempo and heroes.exposure must be positive")
    errors += _limb_errors(d) + _commander_errors(d) + _self_play_errors(d) + _narrator_errors(d) + _orders_errors(d)
    saved = U.get("aftermath", {}).get("saved", {})
    if saved and set(saved.get("hours", {})) != set(d.disease.get("recovery", {}).get("care", {})):
        errors.append("units.yaml: aftermath.saved.hours needs every care level")
    errors += _medevac_errors(U)
    for wid in U.get("line_of_fire", {}).get("arcing", []):
        if wid not in d.weapons or "range" not in d.weapons[wid]:
            errors.append(f"units.yaml: line_of_fire.arcing names {wid}, which is not a weapon with a range")
    cc = U.get("line_of_fire", {}).get("crest_clear", 1)
    if not isinstance(cc, int) or cc < 0:
        errors.append("units.yaml: line_of_fire.crest_clear must be a whole number of 0 or more")
    return errors + _pikes_errors(d) + _indirect_errors(d) + _assault_errors(d) + _guns_errors(d)


def _medevac_errors(units: dict) -> list[str]:
    """units.yaml aftermath.medevac: each kind's name, hours and minutes (% 0-100) and fallback; each battle's kind known."""
    ME = units.get("aftermath", {}).get("medevac") or {}
    kinds = ME.get("kinds") or {}

    def ok(k, v):
        return v.get("name") and all(isinstance(v.get(x), int) and 0 <= v[x] <= 100 for x in ("hours", "minutes")) and v.get("fallback", k) in kinds
    return ([f"units.yaml: aftermath.medevac.kinds.{k} needs a name and hours and minutes (% 0-100) and a known fallback" for k, v in kinds.items() if not ok(k, v)]
            + [f"units.yaml: aftermath.medevac.battles.{b} names unknown kind {k}" for b, k in (ME.get("battles") or {}).items() if k not in kinds])


def _sapper_errors(d: Data) -> list:
    """mines.sappers: exchanges to lay and to clear, whole numbers of 1 or more;
    commander.sappers.clear_of, 0 or more; and commander.creep's numbers, 1 or more."""
    SP = (d.units.get("mines") or {}).get("sappers") or {}
    cr = (d.units.get("commander") or {}).get("creep") or {}
    bad_cr = [f"units.yaml: commander.creep.{k} must be a whole number of 1 or more" for k in ("near", "step", "every", "lines")
              if not (isinstance(cr.get(k), int) and cr[k] >= 1)]
    clear = ((d.units.get("commander") or {}).get("sappers") or {}).get("clear_of")
    bad = [] if isinstance(clear, int) and clear >= 0 else ["units.yaml: commander.sappers.clear_of must be a whole number of 0 or more"]
    return bad_cr + bad + [f"units.yaml: mines.sappers.{k} must be a whole number of 1 or more" for k in ("lay", "clear")
                  if not (isinstance(SP.get(k), int) and SP[k] >= 1)]


def _narrator_errors(d: Data) -> list[str]:
    """units.yaml narrator: voices as text, each war's voice known, whole-number limits, and each
    provider an https address with a model (which may be empty)."""
    N = d.units.get("narrator")
    if not N:
        return []
    V = N.get("voices") or {}
    errors = [f"units.yaml: narrator.voices.{k} needs a name and a style (text)" for k, v in V.items()
              if not (isinstance(v, dict) and all(isinstance(v.get(x), str) and v[x].strip() for x in ("name", "style")))]
    errors += [f"units.yaml: narrator.battles.{b} names unknown voice {v}" for b, v in (N.get("battles") or {}).items() if v not in V]
    if N.get("default") not in V:
        errors.append("units.yaml: narrator.default must name a voice")
    errors += [f"units.yaml: narrator.{k} must be a whole number of 1 or more" for k in ("words", "max_tokens", "context")
               if not (isinstance(N.get(k), int) and N[k] >= 1)]
    errors += [f"units.yaml: narrator.providers.{k} needs an https url and a model" for k, p in (N.get("providers") or {}).items()
               if not (str(p.get("url", "")).startswith("https://") and isinstance(p.get("model"), str))]
    errors += [f"units.yaml: narrator.providers needs {k}" for k in ("anthropic", "openai") if k not in (N.get("providers") or {})]
    return errors


def _self_play_errors(d: Data) -> list[str]:
    """units.yaml commander.self_play: limit and held, whole numbers of 1 or more; commander.spot:
    moves 1 or more, safe 0 or more."""
    K = d.units.get("commander") or {}
    sp, spot = K.get("self_play") or {}, K.get("spot") or {}
    errors = [f"units.yaml: commander.self_play.{k} must be a whole number of 1 or more" for k in ("limit", "held", "after_phases", "most", "secure")
              if not (isinstance(sp.get(k), int) and sp[k] >= 1)]
    if not (isinstance(spot.get("moves"), int) and spot["moves"] >= 1 and isinstance(spot.get("safe"), int) and spot["safe"] >= 0):
        errors.append("units.yaml: commander.spot needs moves (1 or more) and safe (0 or more), whole numbers")
    reach = (K.get("route") or {}).get("reach")
    if not (isinstance(reach, int) and reach >= 0):
        errors.append("units.yaml: commander.route.reach must be a whole number of 0 or more")
    return errors


def _stall_errors(commander: dict) -> list[str]:
    """units.yaml commander.stall: moves (a positive whole number) and down (a % of 0 or more)."""
    st = commander.get("stall") or {}
    if isinstance(st.get("moves"), int) and st["moves"] > 0 and isinstance(st.get("down"), (int, float)) and st["down"] >= 0:
        return []
    return ["units.yaml: commander.stall needs moves (a positive whole number) and down (a % of 0 or more)"]


EPILOGUE_KINDS = ("alive", "dead", "deserted")
EPILOGUE_WHEN = ("any", "lasting", "whole")


def _papers_errors(d: Data) -> list[str]:
    """data/papers.yaml: for each team era, its handouts' titles and look, and its epilogues: for each kind
    (alive, dead, deserted) rows of {w (weight), text, when: any | lasting | whole, regions (optional)}."""
    P = (d.papers or {}).get("eras")
    if not P:
        return []
    errors = [f"papers.yaml: no team era {eid}" for eid in P if eid not in d.teams]
    for eid, E in P.items():
        if eid in d.teams:
            errors += _era_papers_errors(d, eid, E)
    return errors


def _era_papers_errors(d: Data, eid: str, era: dict) -> list[str]:
    """One era's papers: a title for each of its three handouts, and rows for each kind of epilogue."""
    where, docs = f"papers.yaml: {eid}", era.get("docs") or {}
    errors = [f"{where}: docs needs a title for {k}" for k in ("muster", "surgeon", "discharge") if not isinstance((docs.get(k) or {}).get("title"), str)]
    regions = {r["id"] for r in d.teams[eid]["regions"]}
    for kind in EPILOGUE_KINDS:
        rows = (era.get("epilogues") or {}).get(kind)
        if not isinstance(rows, list) or not rows:
            errors.append(f"{where}: epilogues needs rows for {kind}")
            continue
        errors += [f"{where}: {kind}: {e}" for e in (_epilogue_row_error(r, regions) for r in rows) if e]
    return errors


def _epilogue_row_error(r, regions: set) -> str | None:
    """One epilogue row: w (a whole number), text and when (any, lasting or whole), and known regions if it names them."""
    if not (isinstance(r, dict) and isinstance(r.get("text"), str) and isinstance(r.get("w"), int) and r["w"] > 0 and r.get("when", "any") in EPILOGUE_WHEN):
        return "a row needs w (a whole number), text and when (any, lasting or whole)"
    unknown = set(r.get("regions") or []) - regions
    return f"a row names unknown regions {sorted(unknown)}" if unknown else None


def _apply_accounts(fields: dict, accounts: dict) -> None:
    """Each battlefield's accounts from data/accounts.yaml (where the accounts disagree, as a choice on the field map)."""
    unknown = sorted(set(accounts or {}) - set(fields))
    if unknown:
        raise DataError(f"accounts.yaml: no battlefield {', '.join(unknown)} in data/fields")
    for fid, a in (accounts or {}).items():
        fields[fid]["accounts"] = a


def _apply_orders(fields: dict, orders: dict) -> None:
    """Mark each battlefield's units with their orders from data/orders.yaml: hold (fight where
    it stands) and withdraw {at, to} (from that exchange, fall back to a hex or a map edge)."""
    for fid, o in (orders or {}).items():
        _mark_orders({u["name"]: u for u in (fields.get(fid) or {}).get("units", [])}, o or {})


def _mark_orders(units: dict, o: dict) -> None:
    """One battlefield's orders onto its units (by name)."""
    for name in o.get("hold") or []:
        if name in units:
            units[name]["hold"] = True
    for u in units.values():                      # fight_on: sides the accounts show fighting to the end (no surrender)
        if u.get("side") in (o.get("fight_on") or []):
            u["fights_on"] = True
    for w in o.get("withdraw") or []:
        if w.get("unit") in units:
            units[w["unit"]]["withdraw"] = {"at": w["at"], "to": w["to"]}


def _orders_errors(d: Data) -> list[str]:
    """data/orders.yaml: each battlefield and unit named exists; a withdrawal has a whole-number
    exchange of 1 or more and a hex on the map or a map edge (N, S, E, W)."""
    errors = []
    for fid, o in (d.orders or {}).items():
        o, F = o or {}, d.fields.get(fid)
        if F is None:
            errors.append(f"orders.yaml: no battlefield {fid}")
            continue
        names = {u["name"] for u in F.get("units", [])}
        errors += [f"orders.yaml: {fid} has no unit {n!r}" for n in [*(o.get("hold") or []), *[w.get("unit") for w in o.get("withdraw") or []]]
                   if n not in names]
        for w in o.get("withdraw") or []:
            errors += _withdraw_errors(fid, w, F["size"])
        errors += [f"orders.yaml: {fid} fight_on side {k!r} must be 0 or 1" for k in o.get("fight_on") or [] if k not in (0, 1)]
    return errors


def _withdraw_errors(fid: str, w: dict, size: list) -> list[str]:
    """One withdrawal: a whole-number exchange of 1 or more, and a hex on the map or a map edge."""
    errors, to, (cols, rows) = [], w.get("to"), size
    if not (isinstance(w.get("at"), int) and w["at"] >= 1):
        errors.append(f"orders.yaml: {fid} {w.get('unit')!r}: at must be a whole number of 1 or more")
    on_map = isinstance(to, list) and len(to) == 2 and 0 <= to[0] < cols and 0 <= to[1] < rows
    if not (to in ("N", "S", "E", "W") or on_map):
        errors.append(f"orders.yaml: {fid} {w.get('unit')!r}: to must be a hex on the map or N, S, E or W")
    return errors


def _pursuit_errors(commander: dict) -> list[str]:
    """units.yaml commander.pursuit.rally: a whole number of 0 or more."""
    rally = (commander.get("pursuit") or {}).get("rally")
    return [] if isinstance(rally, int) and rally >= 0 else ["units.yaml: commander.pursuit.rally must be a whole number of 0 or more"]


def _commander_errors(d: Data) -> list[str]:
    """units.yaml commander: by-quality tables, charge odds by stance, whole-number weights and
    real weapons (storm: weapons that shoot)."""
    K = d.units.get("commander")
    if not K:
        return []
    qs, errors = set(d.units["quality"]), []
    tables = [(k, K.get(k)) for k in ("hesitate", "cover", "flank", "sense", "reserve", "mines")] + [(f"charge_odds.{s}", (K.get("charge_odds") or {}).get(s)) for s in ("attack", "hold")]
    for name, t in tables:
        if not isinstance(t, dict) or set(t) != qs or not all(isinstance(v, int) and v >= 0 for v in t.values()):
            errors.append(f"units.yaml: commander.{name} needs a whole number of 0 or more for each quality")
    errors += [f"units.yaml: commander.{k} must be a whole number of 0 or more" for k in ("closing", "in_range", "too_close", "keep_off", "stand_off", "remember", "hurt", "shaken", "threat", "gap", "give_way")
               if not (isinstance(K.get(k), int) and K[k] >= 0)]
    if not (isinstance(K.get("tries"), int) and K["tries"] > 0):
        errors.append("units.yaml: commander.tries must be a positive whole number")
    errors += _pursuit_errors(K)
    errors += _stall_errors(K)
    if not (isinstance((d.units.get("dig_in") or {}).get("exchanges"), int) and d.units["dig_in"]["exchanges"] >= 1):
        errors.append("units.yaml: dig_in.exchanges must be a whole number of 1 or more")
    errors += _sapper_errors(d)
    O = K.get("objective") or {}
    errors += [f"units.yaml: commander.objective.{k} must be a whole number of 0 or more" for k in ("radius", "hold", "guard", "bonus")
               if not (isinstance(O.get(k), int) and O[k] >= 0)]
    errors += _rout_errors(d)
    errors += [f"units.yaml: commander.storm names {w}, not a weapon that shoots" for w in K.get("storm", []) if "range" not in d.weapons.get(w, {})]
    return errors + [f"units.yaml: commander.ground_with names unknown weapon {w}" for w in K.get("ground_with", []) if w not in d.weapons]


def _rout_errors(d: Data) -> list[str]:
    """units.yaml rout (how far a broken unit runs through its friends, and how much it jostles
    them), escalade (ladders) and how far a placed battery displaces."""
    R, errors = d.units.get("rout") or {}, []
    shift = (d.units.get("indirect") or {}).get("displace_shift")
    if not (isinstance(shift, int) and shift >= 1):
        errors.append("units.yaml: indirect.displace_shift must be a whole number of hexes, 1 or more")
    if not (isinstance(R.get("through", 1), int) and R.get("through", 1) >= 1):
        errors.append("units.yaml: rout.through must be a whole number of 1 or more")
    if not (isinstance(R.get("jostle", 0), (int, float)) and 0 <= R.get("jostle", 0) <= 1):
        errors.append("units.yaml: rout.jostle must be a share from 0 to 1")
    E = d.units.get("escalade") or {}
    if not (isinstance(E.get("share"), (int, float)) and 0 < E["share"] <= 1 and isinstance(E.get("penalty"), int) and E["penalty"] >= 0
            and isinstance(E.get("cross"), int) and E["cross"] >= 1):
        errors.append("units.yaml: escalade needs share (over 0, at most 1), penalty (a whole % of 0 or more) and cross (whole hexes, 1 or more)")
    return errors


def _field_care_errors(d: Data, heroes: dict) -> list[str]:
    """Heroes carried back, medics, cautery and quarter (units.yaml heroes)."""
    errors = [f"units.yaml: heroes.{k} must be a positive whole number" for k in ("bearers", "back_after")
              if k in heroes and not (isinstance(heroes[k], int) and heroes[k] > 0)]
    med = heroes.get("medic")
    if med is not None and (set(med) != set(d.units["quality"]) or not all(isinstance(v, int) and 0 <= v <= 100 for v in med.values())):
        errors.append("units.yaml: heroes.medic needs a % (0-100) for each quality")
    wars = {t.get("battle") for t in d.tables.values()}
    errors += [f"units.yaml: heroes.cautery.battles names {w}, the war of no wound table" for w in (heroes.get("cautery") or {}).get("battles", []) if w not in wars]
    Q = heroes.get("quarter") or {}
    if Q and "default" not in Q:
        errors.append("units.yaml: heroes.quarter needs a default")
    errors += [f"units.yaml: heroes.quarter names {w}, the war of no wound table" for w in Q if w != "default" and w not in wars]
    errors += [f"units.yaml: heroes.quarter.{w} must be a % (0-100)" for w, v in Q.items() if not (isinstance(v, int) and 0 <= v <= 100)]
    return errors + _aid_post_errors(heroes.get("aid_post"))


def _aid_post_errors(post: dict | None) -> list[str]:
    """heroes.aid_post: first_aid a %, pace a positive whole number of hexes, overrun 0 or more."""
    if post is None:
        return []
    ok = isinstance(post.get("first_aid"), int) and 0 <= post["first_aid"] <= 100 and isinstance(post.get("pace"), int) and post["pace"] > 0 \
        and isinstance(post.get("overrun"), int) and post["overrun"] >= 0
    return [] if ok else ["units.yaml: heroes.aid_post needs first_aid (a %), pace (hexes, 1 or more) and overrun (hexes, 0 or more)"]


def _limb_errors(d: Data) -> list[str]:
    """Heroes lamed (units.yaml heroes.lamed, carried) and one-armed (wounds.yaml
    combat.one_arm against weapons' two_handed)."""
    H, imp = d.units.get("heroes", {}), d.wounds["combat"]["impair"]
    errors = [f"units.yaml: heroes.lamed names unknown impairment {x}" for x in H.get("lamed", []) if x not in imp]
    if "carried" in H and not (isinstance(H["carried"], (int, float)) and 0 < H["carried"] <= 1):
        errors.append("units.yaml: heroes.carried must be more than 0 and at most 1")
    errors += [f"wounds.yaml: combat.one_arm names unknown impairment {x}" for x in d.wounds["combat"].get("one_arm", []) if x not in imp]
    errors += _field_care_errors(d, H)
    return errors + [f"weapons.yaml: {w}.two_handed must be true or false" for w, x in d.weapons.items() if not isinstance(x.get("two_handed", False), bool)]


def _assault_errors(d: Data) -> list[str]:
    """units.yaml assault: known works and weapons, each means a knock and struck % (0 to 100)."""
    A = d.units.get("assault")
    if not A:
        return []
    errors = [f"units.yaml: assault.works names unknown hex work {w}" for w in A.get("works", []) if w not in d.works.get("hex_works", {})]
    errors += [f"units.yaml: assault names unknown weapon {w}" for w in (A.get("weapon"), A.get("fallback")) if w not in d.weapons]
    pct = lambda v: isinstance(v, (int, float)) and 0 <= v <= 100
    errors += [f"units.yaml: assault means {k} needs knock and struck % (0 to 100)" for k, m in A.get("means", {}).items()
               if not (pct(m.get("knock")) and pct(m.get("struck")))]
    return errors


def _guns_errors(d: Data) -> list[str]:
    """units.yaml artillery: shots for each kind of gun from round, shell and canister; a fuse
    figure for every quality; whole-number closing rounds."""
    A = d.units.get("artillery") or {}
    if "shots" not in A:
        return []
    errors = [f"units.yaml: artillery.shots {k} names an unknown shot" for k, v in A["shots"].items()
              if not v or any(x not in ("round", "shell", "canister") for x in v)]
    errors += [f"units.yaml: artillery.shots has no {k} guns" for k in ("smoothbore", "howitzer", "rifled") if k not in A["shots"]]
    F = A.get("set_fuse") or {}
    errors += [f"units.yaml: artillery.set_fuse.quality has no {q}" for q in d.units.get("quality", {}) if q not in F.get("quality", {})]
    if not all(isinstance(F.get(k), int) for k in ("ranged", "within")) or not isinstance(A.get("closing"), int):
        errors.append("units.yaml: artillery needs whole-number set_fuse.ranged, set_fuse.within and closing")
    return errors


def _pikes_errors(d: Data) -> list[str]:
    """units.yaml melee.pikes: known weapons and formations, a whole-number attack."""
    U = d.units
    P = U.get("melee", {}).get("pikes")
    if not P:
        return []
    ok = (all(w in d.weapons for w in P.get("weapons", [])) and all(f in U.get("formations", {}) for f in P.get("formations", []))
          and isinstance(P.get("attack"), int))
    return [] if ok else ["units.yaml: melee.pikes needs known weapons and formations and a whole-number attack"]


def _indirect_errors(d: Data) -> list[str]:
    """units.yaml indirect: tree bursts on known ground, smoke for every wind, a counter % per kind."""
    I, errors = d.units.get("indirect") or {}, []
    if not I:
        return errors
    errors += [f"units.yaml: indirect.tree_burst names unknown ground {g}" for g in I.get("tree_burst", {}).get("ground", []) if g not in d.units.get("ground", {})]
    winds = {w["id"] for w in d.weather.get("winds", [])}
    if winds and set(I.get("smoke", {}).get("lasts", {})) != winds:
        errors.append("units.yaml: indirect.smoke.lasts needs every wind")
    errors += [f"units.yaml: indirect kind {k} needs a counter % (0 to 100)" for k, v in I.get("kinds", {}).items()
               if not isinstance(v.get("counter"), (int, float)) or not 0 <= v["counter"] <= 100]
    errors += [f"units.yaml: indirect kind {k} needs whole-number crew and displace, and serve from 1 to crew" for k, v in I.get("kinds", {}).items()
               if not v.get("air") and not (isinstance(v.get("crew"), int) and isinstance(v.get("serve"), int) and isinstance(v.get("displace"), int) and 1 <= v["serve"] <= v["crew"])]
    errors += _air_errors(d, I) + _vehicle_errors(d)
    errors += [f"units.yaml: indirect kind {k} illum must be a whole number of hexes" for k, v in I.get("kinds", {}).items()
               if not (isinstance(v.get("illum", 0), int) and v.get("illum", 0) >= 0)]
    if winds and set(I.get("smoke", {}).get("drift", {})) != winds:
        errors.append("units.yaml: indirect.smoke.drift needs every wind")
    if not all(isinstance(I.get("counter_battery", {}).get(k), int) for k in ("among", "near", "near_struck")):
        errors.append("units.yaml: indirect.counter_battery needs whole-number among, near and near_struck")
    return errors


def _rider_fire_errors(veh: dict) -> list[str]:
    """vehicles.rider_fire: ports and hull shares (0-1), when a kind has ports or rides."""
    F = veh.get("rider_fire") or {}
    if not any(k.get("ports") or k.get("rides") for k in veh.get("kinds", {}).values()) or all(isinstance(F.get(x), (int, float)) and 0 <= F[x] <= 1 for x in ("ports", "hull")):
        return []
    return ["units.yaml: vehicles.rider_fire needs ports and hull (shares 0-1) when a kind has ports or rides"]


def _small_arms_errors(veh: dict) -> list[str]:
    """vehicles.small_arms: rate and mg above 0, when an armour has a small %."""
    S = veh.get("small_arms") or {}
    if not any("small" in a for a in veh.get("armour", {}).values()) or all(isinstance(S.get(x), (int, float)) and S[x] > 0 for x in ("rate", "mg")):
        return []
    return ["units.yaml: vehicles.small_arms needs rate and mg (aimed shots a man, above 0) when an armour has a small %"]


def _fire_control_errors(vehicles: dict) -> list[str]:
    """units.yaml vehicles.fire_control: each kind a whole-number range and hit bands reaching it;
    by_war naming kinds that exist."""
    F = vehicles.get("fire_control") or {}
    kinds = {k: v for k, v in F.items() if k != "by_war"}
    errors = [f"units.yaml: vehicles.fire_control.{k} needs a whole-number range and hit bands [[hexes, %], ...] up to it" for k, v in kinds.items()
              if not (isinstance(v, dict) and isinstance(v.get("range"), int) and isinstance(v.get("hit"), list) and v["hit"] and v["hit"][-1][0] == v["range"])]
    errors += [f"units.yaml: vehicles.fire_control.by_war names unknown fire control {x}" for x in (F.get("by_war") or {}).values() if x not in kinds]
    return errors


def _vehicle_errors(d: Data) -> list[str]:
    """units.yaml vehicles: kinds with a crew, move and known armour (and a gun with a range, rate,
    an indirect kind for its high explosive and hit bands); armour %s; anti-armour weapons and
    ground kinds that exist."""
    V = d.units.get("vehicles")
    if not V:
        return []
    errors = [f"units.yaml: vehicles.kinds.{k} needs whole-number crew and move and a known armour" for k, v in V.get("kinds", {}).items()
              if not (isinstance(v.get("crew"), int) and v["crew"] > 0 and isinstance(v.get("move"), int) and v.get("armour") in V.get("armour", {}))]
    errors += [f"units.yaml: vehicles.kinds.{k}.gun needs range, rate, he (an indirect kind) and hit bands" for k, v in V.get("kinds", {}).items()
               if "gun" in v and not (isinstance(v["gun"].get("range"), int) and isinstance(v["gun"].get("rate"), int)
                                      and v["gun"].get("he") in d.units["indirect"]["kinds"] and v["gun"].get("hit"))]
    errors += [f"units.yaml: vehicles.armour.{k} needs rpg, atgm, gun, shell and mine" for k, a in V.get("armour", {}).items()
               if not all(isinstance(a.get(x), (int, float)) for x in ("rpg", "atgm", "gun", "shell", "mine"))]
    errors += [f"units.yaml: vehicles.anti_armour.{w} needs a known weapon, a rate and an armour row (rpg or atgm)" for w, a in V.get("anti_armour", {}).items()
               if w not in d.weapons or not isinstance(a, dict) or not isinstance(a.get("rate"), (int, float)) or a.get("row") not in ("rpg", "atgm")]
    errors += _small_arms_errors(V) + _rider_fire_errors(V)
    errors += [f"units.yaml: vehicles.kinds.{k}.{x} must be a whole number above 0" for k, v in V.get("kinds", {}).items() for x in ("carry", "tows")
               if x in v and not (isinstance(v[x], int) and v[x] > 0)]
    if not all(isinstance((V.get("aspect") or {}).get(x), (int, float)) for x in ("flank", "rear")):
        errors.append("units.yaml: vehicles.aspect needs flank and rear")
    D = V.get("damage") or {}
    parts = all(isinstance((D.get(p) or {}).get(x), int) for p in ("turret_hit", "hull_hit") for x in ("immobilised", "gun"))
    if not (isinstance(D.get("turret"), int) and parts) or not isinstance(V.get("riders_struck"), int):
        errors.append("units.yaml: vehicles.damage needs turret (a %) and turret_hit and hull_hit (immobilised and gun %), and vehicles.riders_struck a whole number")
    errors += [f"units.yaml: vehicles.ground names unknown ground {g}" for g in V.get("ground", {}) if g not in d.units["ground"]]
    errors += _fire_control_errors(V)
    return errors + _at_mine_errors(d)


def _at_mine_errors(d: Data) -> list[str]:
    """units.yaml anti_tank_guns (known weapons, a crew, rounds, a gun as a vehicle's), gun_shields
    (known weapons, a cover %) and mines (a known weapon, kinds with men and vehicles %)."""
    A, M, errors = d.units.get("anti_tank_guns"), d.units.get("mines"), _shield_errors(d)
    if A:
        g = A.get("gun") or {}
        if not (all(w in d.weapons for w in A.get("weapons", [])) and isinstance(A.get("crew"), int) and A["crew"] > 0 and A.get("crew_weapon") in d.weapons
                and isinstance(g.get("range"), int) and isinstance(g.get("rate"), int) and g.get("he") in d.units["indirect"]["kinds"] and g.get("hit")):
            errors.append("units.yaml: anti_tank_guns needs known weapons, a crew, a known crew_weapon and a gun (range, rate, he, hit)")
        if not (isinstance(A.get("rounds"), int) and A["rounds"] > 0):
            errors.append("units.yaml: anti_tank_guns.rounds must be a whole number above 0")
    if M:
        if M.get("weapon") not in d.weapons or not isinstance(M.get("attack"), int):
            errors.append("units.yaml: mines needs a known weapon and an attack %")
        errors += [f"units.yaml: mines.kinds.{k} needs men and vehicles (% 0-100)" for k, v in (M.get("kinds") or {}).items()
                   if not all(isinstance(v.get(x), int) and 0 <= v[x] <= 100 for x in ("men", "vehicles"))]
    return errors


def _shield_errors(d: Data) -> list[str]:
    """units.yaml gun_shields: known weapons (and optional ones) and a cover % (0-100)."""
    S = d.units.get("gun_shields")
    if S and not (all(w in d.weapons for w in S.get("weapons", []) + S.get("optional", [])) and isinstance(S.get("cover"), int) and 0 <= S["cover"] <= 100):
        return ["units.yaml: gun_shields needs known weapons and a cover % (0-100)"]
    return []


def _run_errors(d: Data, ind: dict) -> list[str]:
    """indirect.air.runs: each a length, struck and knock %, aircraft kinds, and known wars."""
    wars, errors = {t.get("battle") for t in d.tables.values()}, []
    for name, r in ((ind.get("air") or {}).get("runs") or {}).items():
        if not (isinstance(r.get("length"), int) and r["length"] >= 1 and isinstance(r.get("struck"), int) and isinstance(r.get("knock"), int)
                and all(ind.get("kinds", {}).get(k, {}).get("air") for k in r.get("kinds", []))):
            errors.append(f"units.yaml: indirect.air.runs.{name} needs length, struck and knock, and kinds that are aircraft")
        errors += [f"units.yaml: indirect.air.runs.{name}.wars names {w}, the war of no wound table" for w in r.get("wars", []) if w not in wars]
    return errors


def _air_errors(d: Data, ind: dict) -> list[str]:
    """units.yaml: aircraft (indirect.air: weather and light they are grounded in; a kind's log
    name `shot`) and landing by air (heliborne)."""
    A = ind.get("air") or {}
    errors = [f"units.yaml: indirect kind {k} shot must be [one, many]" for k, v in ind.get("kinds", {}).items()
              if "shot" in v and not (isinstance(v["shot"], list) and len(v["shot"]) == 2 and all(isinstance(x, str) for x in v["shot"]))]
    errors += [f"units.yaml: indirect.air.grounded names unknown weather {c}" for c in A.get("grounded", []) if c not in d.weather.get("conditions", {})]
    errors += [f"units.yaml: indirect.air.night names unknown light {x}" for x in A.get("night", []) if x not in (d.weather.get("light") or {}).get("levels", {})]
    G, FAC = A.get("ground_fire") or {}, A.get("fac") or {}
    if any(ind.get("kinds", {}).get(k, {}).get("air") for k in ind.get("kinds", {})) and not (
            all(isinstance(G.get(k), (int, float)) and G[k] >= 0 for k in ("reach", "mg", "rocket", "rifles", "cap", "aa", "aa_reach", "aa_cap", "downed"))
            and all(w in d.weapons for w in G.get("aa_weapons", []))
            and all(w in d.weapons for w in G.get("rockets", [])) and isinstance(FAC.get("danger"), int) and isinstance(FAC.get("scatter"), int) and FAC["scatter"] >= 1):
        errors.append("units.yaml: indirect.air needs ground_fire (reach, mg, rocket, rifles, cap, aa, aa_reach, downed; rockets and aa_weapons: known weapons) and fac (danger, scatter at least 1)")
    errors += _run_errors(d, ind)
    H = d.units.get("heliborne")
    if H and not all(isinstance(H.get(k), int) and H[k] >= 0 for k in ("aircraft", "carry", "turnaround", "at_once", "hit", "downed", "blocked", "hot", "zone")):
        errors.append("units.yaml: heliborne needs whole numbers aircraft, carry, turnaround, at_once, hit, downed, blocked, hot and zone")
    return errors


def _ground_seed_errors(d: Data, terrain: dict) -> list[str]:
    """wounds.yaml combat.ground.seed: travel terrain -> shares of each ground kind, rises, top."""
    G = d.wounds["combat"].get("ground", {})
    errors = []
    for tid, x in G.get("seed", {}).items():
        where = f"wounds.yaml: combat.ground.seed.{tid}"
        if tid not in terrain:
            errors.append(f"{where} names unknown terrain")
        shares = {k: v for k, v in x.items() if k not in ("rises", "top")}
        errors += [f"{where}: {k} is not a ground kind" for k in shares if k not in G["kinds"] or k == "open"]
        if any(not isinstance(v, (int, float)) or v < 0 for v in shares.values()) or sum(shares.values()) > 0.8:
            errors.append(f"{where}: shares must be 0 or more and add up to 0.8 at most")
        if x.get("rises", 0) and not 1 <= x.get("top", 0) <= G["max_level"]:
            errors.append(f"{where}: top must be 1 to {G['max_level']}")
    for what, T in G.get("through", {}).items():
        errors += [f"wounds.yaml: combat.ground.through.{what} names unknown terrain {t}"
                   for t in T.get("hexes", []) + T.get("links", []) if t not in terrain]
    return errors


EQUIPMENT_CATS = {"weapon", "ammunition", "armour", "horse", "clothing", "light", "shelter", "navigation", "fire", "rope",
                  "first_aid", "food", "lodging", "travel", "gear", "service", "pay"}


def _equipment_errors(d: Data, E: dict) -> list[str]:
    """data/equipment: an era's coins (units or decimal, a Day in base units or none) and priced
    rows (whole base units or a low-high range; a source unless approx; links to known armour
    kits and weapons; armies of the era)."""
    where, errors = f"equipment/{E['id']}", []
    if E["id"] not in d.teams:
        errors.append(f"{where}: no team tables for this era")
    regions = {r["id"] for r in d.teams.get(E["id"], {}).get("regions", [])}
    C = E.get("currencies") or {}
    for cid, c in C.items():
        if bool(c.get("units")) == bool(c.get("decimal")):
            errors.append(f"{where}: currency {cid} needs units or decimal, not both")
        if c.get("units") and [u["of"] for u in c["units"]] != sorted((u["of"] for u in c["units"]), reverse=True):
            errors.append(f"{where}: currency {cid} units must run largest first")
        if c.get("day") is not None and (not isinstance(c["day"], int) or c["day"] <= 0):
            errors.append(f"{where}: currency {cid} day must be a whole number of base units")
        if not c.get("coin"):
            errors.append(f"{where}: currency {cid} needs a coin family")
    cur = E.get("currency") or {}
    if cur.get("default") not in C:
        errors.append(f"{where}: currency.default names an unknown currency")
    errors += [f"{where}: currency for unknown army {r}" for r in cur if r != "default" and r not in regions]
    errors += [f"{where}: army {r} paid in unknown currency {c}" for r, c in cur.items() if c not in C]
    ids = [r["id"] for r in E.get("items", [])]
    errors += [f"{where}: duplicate item {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for r in E.get("items", []):
        at = f"{where}: {r['id']}"
        p = r.get("price")
        ok = isinstance(p, int) or (isinstance(p, list) and len(p) == 2 and all(isinstance(x, int) for x in p) and p[0] <= p[1])
        if not ok or (isinstance(p, int) and p < 0):
            errors.append(f"{at}: price must be whole base units or [low, high]")
        if r.get("cat") not in EQUIPMENT_CATS:
            errors.append(f"{at}: unknown category {r.get('cat')}")
        if r.get("in") and r["in"] not in C:
            errors.append(f"{at}: unknown currency {r['in']}")
        if not r.get("approx") and not r.get("source"):
            errors.append(f"{at}: needs a source, or approx: true")
        for key, known in (("kit", d.armor["kits"]), ("weapon", d.weapons)):
            links = r.get(key)
            links = [links] if isinstance(links, str) else (links or [])
            errors += [f"{at}: {key} {x} is not in {'armor.yaml' if key == 'kit' else 'weapons.yaml'}" for x in links if x not in known]
        errors += [f"{at}: unknown army {x}" for x in r.get("regions", []) if x not in regions]
    K = E.get("keep")
    if K is not None:
        known = set(ids)
        specs = [("keep", K)] + [(f"keep.regions.{r}", v) for r, v in (K.get("regions") or {}).items()]
        errors += [f"{where}: keep for unknown army {r}" for r in (K.get("regions") or {}) if r not in regions]
        for at, spec in specs:
            for part in ("food", "bed"):
                x = spec.get(part)
                if x is None:
                    if at == "keep":
                        errors.append(f"{where}: keep needs a {part}")
                    continue
                if x.get("row") not in known:
                    errors.append(f"{where}: {at}.{part} names unknown item {x.get('row')}")
                if not isinstance(x.get("times", 1), int) or x.get("times", 1) < 1:
                    errors.append(f"{where}: {at}.{part} times must be a whole number, 1 or more")
    return errors


def _replacement_errors(d: Data, R: dict) -> list[str]:
    """data/replacements: an era's assigned replacements (terms, a wait in days) and men to hire
    (terms low-high, a cost in Days), each for some armies, careers and places, with a source
    unless approx; and the practice with a lost man's effects (share, heirs or lost)."""
    where, errors = f"replacements/{R['id']}", []
    T = d.teams.get(R["id"])
    if not T:
        return [f"{where}: no team tables for this era"]
    regions, careers = {r["id"] for r in T["regions"]}, {c["id"] for c in T["careers"]}
    ids = [r["id"] for k in ("assigned", "hire") for r in R.get(k, [])]
    errors += [f"{where}: duplicate {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for kind in ("assigned", "hire"):
        for r in R.get(kind, []):
            at = f"{where}: {r['id']}"
            errors += [f"{at}: unknown army {x}" for x in r.get("regions", []) if x not in regions]
            cs = r.get("careers", "any")
            if cs != "any" and (not isinstance(cs, list) or any(c not in careers for c in cs)):
                errors.append(f"{at}: careers must be any or the era's careers")
            t = r.get("terms")
            ok = (isinstance(t, int) and 1 <= t <= 3) or (isinstance(t, list) and len(t) == 2 and all(isinstance(x, int) for x in t) and 1 <= t[0] <= t[1] <= 3)
            if not ok:
                errors.append(f"{at}: terms must be 1-3 or [low, high]")
            if kind == "assigned":
                w = r.get("wait")
                if not (isinstance(w, list) and len(w) == 2 and all(isinstance(x, int) and x >= 0 for x in w) and w[0] <= w[1]):
                    errors.append(f"{at}: wait must be [low, high] days")
            else:
                if not isinstance(r.get("cost"), (int, float)) or r["cost"] < 0 or not isinstance(r.get("per_term", 0), (int, float)):
                    errors.append(f"{at}: cost (and per_term) must be Days")
            if r.get("places") and not set(r["places"]) <= JOB_PLACES:
                errors.append(f"{at}: unknown place in {r['places']}")
            if not r.get("approx") and not r.get("source"):
                errors.append(f"{at}: needs a source, or approx: true")
    E = R.get("effects") or {}
    for at, e in [("default", E.get("default"))] + list((E.get("regions") or {}).items()):
        if at != "default" and at not in regions:
            errors.append(f"{where}: effects for unknown army {at}")
        if not e or e.get("practice") not in ("share", "heirs", "lost"):
            errors.append(f"{where}: effects {at} practice must be share, heirs or lost")
    return errors


def _events_errors(d: Data) -> list[str]:
    """data/events.yaml: periods name eras; each era's rates are chances (0-1) per man per day by
    activity, with a source or approx; its incident rows rise to 100, for known force types."""
    E, errors, where = d.events, [], "events"
    eras = E.get("eras") or {}
    errors += [f"{where}: period {p} names unknown era {e}" for p, e in (E.get("periods") or {}).items() if e not in eras]
    errors += [f"{where}: era {e} has no team tables" for e in eras if e not in d.teams]
    tos = [r.get("to") for r in E.get("injury", [])]
    if not tos or tos != sorted(tos) or tos[-1] != 100 or any(r.get("step") not in d.disease.get("steps", []) for r in E.get("injury", [])):
        errors.append(f"{where}: injury rows must rise to 100 with known steps")
    ftypes = set(d.terrain.get("forces", {}))
    for mid, m in d.maps.items():
        errors += [f"{where}: map {mid} force {f.get('name')} names unknown era {f['era']}" for f in m.get("forces", []) if f.get("era") and f["era"] not in eras]
    for e, x in eras.items():
        for kind, r in (x.get("rates") or {}).items():
            at = f"{where}: {e} {kind}"
            if kind not in ("desert", "straggle", "injury", "horses"):
                errors.append(f"{at}: unknown kind")
            for a in ("camp", "march", "withdraw"):
                v = r.get(a)
                if not isinstance(v, (int, float)) or not 0 <= v <= 1:
                    errors.append(f"{at}: {a} must be a chance 0-1")
            if not r.get("approx") and not r.get("source"):
                errors.append(f"{at}: needs a source, or approx: true")
        if not isinstance(x.get("incident", 0), (int, float)) or not 0 <= x.get("incident", 0) <= 100:
            errors.append(f"{where}: {e} incident must be a % 0-100")
        rows = x.get("incidents") or []
        tos = [r.get("to") for r in rows]
        if rows and (tos != sorted(tos) or tos[-1] != 100):
            errors.append(f"{where}: {e} incidents must rise to 100")
        for r in rows:
            if r.get("types") and not set(r["types"]) <= ftypes:
                errors.append(f"{where}: {e} incident {r.get('to')} has unknown types {r['types']}")
            lo = r.get("lose")
            if lo is not None and not (isinstance(lo, list) and len(lo) == 2 and 0 <= lo[0] <= lo[1]):
                errors.append(f"{where}: {e} incident {r.get('to')} lose must be [low, high]")
    for c, x in (E.get("conditions") or {}).items():
        at = f"{where}: condition {c}"
        if c not in ("hungry", "unpaid"):
            errors.append(f"{at}: unknown condition")
        for k, v in x.items():
            if k in ("source", "approx"):
                continue
            if k not in ("desert", "straggle", "injury", "horses"):
                errors.append(f"{at}: unknown kind {k}")
            elif not (isinstance(v, (int, float)) and v > 0):
                errors.append(f"{at}: {k} must be a positive multiplier")
        if not x.get("approx") and not x.get("source"):
            errors.append(f"{at}: needs a source, or approx: true")
    for t, bands in (E.get("horses_march") or {}).items():
        if t not in ("mounted", "wagons"):
            errors.append(f"{where}: horses_march names {t}, not mounted or wagons")
        for b in bands:
            if not (isinstance(b.get("below"), (int, float)) and 0 < b["below"] <= 1 and isinstance(b.get("pct"), int) and 0 < b["pct"] <= 100):
                errors.append(f"{where}: horses_march {t} bands need below (0-1) and pct (1-100)")
    return errors


def _ranks_errors(d: Data) -> list[str]:
    """data/ranks.yaml: each era's ladder (pay, years, a known difficulty), its regional pay the
    ladder's length, careers it starts or pays known to the era; loot finds rising to 100; each
    era's loot rules for an era with team tables."""
    R, where, errors = d.ranks, "ranks.yaml", []
    diffs = {x["id"] for x in (d.checks or {}).get("difficulty", [])} or {"ordinary"}
    for eid, E in (R.get("eras") or {}).items():
        at = f"{where}: {eid}"
        T = d.teams.get(eid)
        if not T:
            errors.append(f"{at}: no team tables for this era")
            continue
        careers, regions = {c["id"] for c in T["careers"]}, {r["id"] for r in T["regions"]}
        if E.get("honours"):
            continue
        L = E.get("ladder") or []
        ids = [r.get("id") for r in L]
        if not L or len(set(ids)) != len(ids):
            errors.append(f"{at}: needs a ladder of distinct ranks")
        for k, r in enumerate(L):
            if not (isinstance(r.get("pay"), (int, float)) and r["pay"] > 0):
                errors.append(f"{at}: {r.get('id')} pay must be positive")
            if k and (r.get("diff") not in diffs or not isinstance(r.get("years", 0), (int, float))):
                errors.append(f"{at}: {r.get('id')} needs a known diff and years")
        for reg, arr in (E.get("pay_by") or {}).items():
            if reg not in regions or len(arr) != len(L):
                errors.append(f"{at}: pay_by {reg} must be a region of the era with one pay a rank")
        for car, rid in (E.get("start") or {}).items():
            if car not in careers or rid not in ids:
                errors.append(f"{at}: start {car}: {rid} names an unknown career or rank")
        for car in (E.get("career_pay") or {}):
            if car not in careers:
                errors.append(f"{at}: career_pay names unknown career {car}")
        for reg, cp in (E.get("career_pay_by") or {}).items():
            if reg not in {r["id"] for r in d.teams[eid]["regions"]} or set(cp) - careers:
                errors.append(f"{at}: career_pay_by {reg} names an unknown region or career")
        if not 0 < E.get("kept", 1) <= 1:
            errors.append(f"{at}: kept must be 0-1")
    tos = [f.get("to") for f in R.get("finds", [])]
    if R.get("finds") and (tos != sorted(tos) or tos[-1] != 100):
        errors.append(f"{where}: finds must rise to 100")
    for eid, L in (R.get("loot") or {}).items():
        if eid not in d.teams:
            errors.append(f"{where}: loot for unknown era {eid}")
        if not 0 < L.get("keep", 1) <= 1:
            errors.append(f"{where}: loot {eid} keep must be 0-1")
    return errors


def _kit_errors(d: Data) -> list[str]:
    """data/kit.yaml: boot and clothing lives for every era; wear thresholds and steps; patterns."""
    import re
    K, where, errors = d.kit, "kit.yaml", []
    for k in ("boots", "clothing"):
        life = (K.get(k) or {}).get("life") or {}
        if set(life) != set(d.teams) or any(v <= 0 for v in life.values()):
            errors.append(f"{where}: {k} life needs every era, each over 0")
    if not (0 < K.get("worn", 0) < 1 and 0 < K.get("mend", 0) <= 1):
        errors.append(f"{where}: worn and mend must be 0-1")
    for k, pat in (K.get("renew") or {}).items():
        try:
            re.compile(pat)
        except re.error:
            errors.append(f"{where}: renew {k} does not compile")
    return errors


def _supplies_errors(d: Data) -> list[str]:
    """data/supplies.yaml: rations and water for every era, rising need bands, known water
    terrain, positive medical and train figures."""
    S, where, errors = d.supplies, "supplies.yaml", []
    for k in ("rations", "water"):
        c = (S.get(k) or {}).get("carried") or {}
        if set(c) != set(d.teams) or any(v <= 0 for v in c.values()):
            errors.append(f"{where}: {k} carried needs every era, each over 0")
    ups = [b.get("upto") for b in (S.get("water") or {}).get("need", [])]
    if not ups or ups != sorted(ups):
        errors.append(f"{where}: water need bands must rise")
    if set((S.get("water") or {}).get("sources", [])) - set(d.terrain["terrain"]):
        errors.append(f"{where}: water sources must be known terrain")
    if not all((S.get(k) or {}).get(x, 0) > 0 for k, x in (("medical", "cases"), ("train", "serves"), ("train", "rations"))):
        errors.append(f"{where}: medical cases and the train's figures must be over 0")
    return errors


def _weight_pattern_errors(w: dict, where: str) -> list[str]:
    """weights.yaml patterns: each compiles and has a weight."""
    import re
    errors = []
    for p in w.get("patterns", []):
        try:
            re.compile(p.get("match", ""))
        except re.error:
            errors.append(f"{where}: pattern {p.get('match')!r} does not compile")
        if not (isinstance(p.get("kg"), (int, float)) and p["kg"] > 0):
            errors.append(f"{where}: pattern {p.get('match')!r} needs a weight")
    return errors


def _weights_errors(d: Data) -> list[str]:
    """data/weights.yaml: patterns that compile with a weight; category weights; a coin weight an era
    known; animals with unique ids, a pattern, a load and forage; road and mud factors 0-1."""
    W, where = d.weights, "weights.yaml"
    errors = _weight_pattern_errors(W, where)
    if any(not (isinstance(v, (int, float)) and v >= 0) for v in (W.get("categories") or {}).values()):
        errors.append(f"{where}: category weights must be 0 or more")
    bad = sorted(set(W.get("coin_kg_day") or {}) - set(d.equipment))
    if bad:
        errors.append(f"{where}: coin_kg_day names unknown eras {bad}")
    ids = [a.get("id") for a in W.get("animals", [])]
    if len(set(ids)) != len(ids):
        errors.append(f"{where}: animal ids must be unique")
    for a in W.get("animals", []):
        if not (a.get("match") and a.get("load", 0) > 0 and a.get("forage", -1) >= 0):
            errors.append(f"{where}: animal {a.get('id')} needs a pattern, a load and forage")
    if not all(0 < W.get(k, 1) <= 1 for k in ("off_road", "mud")):
        errors.append(f"{where}: off_road and mud must be 0-1")
    return errors


def _checks_errors(d: Data) -> list[str]:
    """data/checks.yaml: difficulties with whole modifiers; haggle figures; each use names a skill
    some era has (or a characteristic), a known difficulty, a known skill or characteristic
    against it, and its results."""
    C, where, errors = d.checks, "checks.yaml", []
    stats = {"str", "agi", "end", "wits", "nerve", "pres"}
    skills = {s["id"] for T in d.teams.values() for s in T["skills"]}
    if not (0 < C.get("critical_fraction", 0) < 1) or not (isinstance(C.get("fumble_from"), int) and 1 < C["fumble_from"] <= 100):
        errors.append(f"{where}: critical_fraction must be 0-1 and fumble_from 2-100")
    diffs = [x.get("id") for x in C.get("difficulty", [])]
    if "ordinary" not in diffs or len(set(diffs)) != len(diffs) or any(not isinstance(x.get("mod"), int) for x in C.get("difficulty", [])):
        errors.append(f"{where}: difficulties need unique ids, an ordinary one, and whole modifiers")
    H = C.get("haggle") or {}
    if H and not (isinstance(H.get("seller"), int) and -1 < H.get("win", 0) < 0 and -1 < H.get("critical", 0) <= H.get("win", 0)):
        errors.append(f"{where}: haggle needs a seller skill and win/critical as falls in price (critical at least win)")
    ids = set()
    for u in C.get("uses", []):
        at = f"{where}: use {u.get('id')}"
        if u.get("id") in ids:
            errors.append(f"{at}: id used twice")
        ids.add(u.get("id"))
        if u.get("skill") not in skills | stats:
            errors.append(f"{at}: unknown skill {u.get('skill')}")
        if u.get("difficulty") not in diffs:
            errors.append(f"{at}: unknown difficulty {u.get('difficulty')}")
        ag = u.get("against")
        if ag is not None and not ((ag.get("skill") in skills or ag.get("stat") in stats) and isinstance(ag.get("value"), int)):
            errors.append(f"{at}: against needs a known skill or stat and a value")
        if not all(u.get(k) for k in ("name", "what", "success", "failure", "fumble")):
            errors.append(f"{at}: needs name, what, success, failure and fumble")
    return errors


JOB_PLACES = {"town", "city", "village", "camp", "road", "frontier", "sea"}
JOB_TERMS = {"day", "week", "month", "contract"}


def _jobs_errors(d: Data, J: dict) -> list[str]:
    """data/jobs: an era's jobs (a skill of the era or none, a least skill, pay in quarter Days,
    a term, places, who, risk, a source unless approx) and a d10 trouble table."""
    where, errors = f"jobs/{J['id']}", []
    T = d.teams.get(J["id"])
    if not T:
        return [f"{where}: no team tables for this era"]
    skills, careers = {s["id"] for s in T["skills"]}, {c["id"] for c in T["careers"]}
    ids = [j["id"] for j in J.get("jobs", [])]
    errors += [f"{where}: duplicate job {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for j in J.get("jobs", []):
        at = f"{where}: {j['id']}"
        if j.get("skill") is not None and j["skill"] not in skills:
            errors.append(f"{at}: unknown skill {j['skill']}")
        if not isinstance(j.get("min", 0), int) or not 0 <= j.get("min", 0) <= T["skill_max"]:
            errors.append(f"{at}: min must be a skill level 0-{T['skill_max']}")
        p = j.get("pay")
        if not isinstance(p, (int, float)) or p < 0 or abs(p * 4 - round(p * 4)) > 1e-9:
            errors.append(f"{at}: pay must be Days in quarters (0, 0.25, 0.5, 1.75 ...); 0 for an unpaid volunteer")
        if j.get("term") not in JOB_TERMS:
            errors.append(f"{at}: term must be one of {sorted(JOB_TERMS)}")
        if j.get("term") == "contract":
            days = j.get("days")
            if not (isinstance(days, list) and len(days) == 2 and all(isinstance(x, int) and x > 0 for x in days) and days[0] <= days[1]):
                errors.append(f"{at}: a contract needs days: [low, high]")
        if j.get("lump") and j.get("term") != "contract":
            errors.append(f"{at}: a lump sum is paid only for a contract")
        if not j.get("places") or any(x not in JOB_PLACES for x in j["places"]):
            errors.append(f"{at}: places must be some of {sorted(JOB_PLACES)}")
        who = j.get("who", "any")
        if who != "any" and (not isinstance(who, list) or any(x not in careers for x in who)):
            errors.append(f"{at}: who must be any, or careers of this era")
        if not isinstance(j.get("risk", 0), int) or not 0 <= j.get("risk", 0) <= 100:
            errors.append(f"{at}: risk must be a % from 0 to 100")
        if not j.get("approx") and not j.get("source"):
            errors.append(f"{at}: needs a source, or approx: true")
    trouble = J.get("trouble", [])
    if [t.get("roll") for t in trouble] != list(range(1, len(trouble) + 1)) or len(trouble) != 10:
        errors.append(f"{where}: trouble must be a d10 table, rows 1-10 in order")
    errors += [f"{where}: {j['id']}: board must be true or false" for j in J.get("jobs", []) if not isinstance(j.get("board", False), bool)]
    return errors


def _team_errors(d: Data, era: dict) -> list[str]:
    """data/teams: an era's character generation tables."""
    T = era
    where, errors = f"teams/{T['id']}", []
    chars, skills = {c["id"] for c in T["characteristics"]}, {s["id"] for s in T["skills"]}
    if len(T["array"]) != len(chars):
        errors.append(f"{where}: array needs one figure for each characteristic")
    errors += [f"{where}: skill {s['id']} is based on unknown characteristic {s['of']}" for s in T["skills"] if s["of"] not in chars]
    errors += [f"{where}: weapon_skill names unknown weapon {w} or skill {s}" for w, s in T["weapon_skill"].items() if w not in d.weapons or s not in skills]
    errors += [f"{where}: defence names unknown skill {s}" for s in T["defence"] if s not in skills]
    for o in T["origins"]:
        errors += _team_mod_errors(where, o["name"], o, chars, skills)
    for r in T["regions"]:
        if r["table"] not in d.tables:
            errors.append(f"{where}: region {r['id']} names unknown table {r['table']}")
        errors += _women_errors(T, where, r)
    if any(o.get("who") not in (None, "m", "f") for o in T["origins"]):
        errors.append(f"{where}: an origin's who must be m or f")
    for c in T["careers"]:
        errors += _career_errors(d, T, where, c, chars, skills)
    errors += _template_errors(T, where)
    if [r["to"] for r in T["old_wound"]][-1] != 100 or set(T["lasting_from"].values()) - chars:
        errors.append(f"{where}: old_wound must end at 100 and lasting_from name characteristics")
    return errors


def _women_career_errors(w: dict, where: str, rid: str) -> list[str]:
    """A women block's per-career settings: `disguised` and `shares` name its open careers."""
    errors, open_ = [], set(w.get("careers") or [])
    hid = w.get("disguised")
    if isinstance(hid, list) and set(hid) - open_:
        errors.append(f"{where}: region {rid} women disguised must name its open careers")
    shares = w.get("shares") or {}
    if set(shares) - open_ or any(not 0 < v <= 100 for v in shares.values()):
        errors.append(f"{where}: region {rid} women shares must name its open careers, each over 0 and at most 100")
    return errors


def _women_errors(tables: dict, where: str, r: dict) -> list[str]:
    """A region's women block: known careers, a share (%) between 0 and 100 or null, name lists,
    and enough origins for a woman (shared or her own)."""
    W, careers = r.get("women"), {c["id"] for c in tables["careers"]}
    if not W:
        return []
    errors = []
    if not W.get("careers") or set(W["careers"]) - careers:
        errors.append(f"{where}: region {r['id']} women needs careers, all known")
    if W.get("share") is not None and not 0 < W["share"] <= 100:
        errors.append(f"{where}: region {r['id']} women share must be over 0 and at most 100 (or null)")
    errors += _women_career_errors(W, where, r["id"])
    if any(k in W and not W[k] for k in ("names", "bynames")) or not W.get("source"):
        errors.append(f"{where}: region {r['id']} women name lists must not be empty, and the block needs a source")
    if not [o for o in tables["origins"] if o.get("who", "f") == "f"]:
        errors.append(f"{where}: women need origins (shared or who: f)")
    return errors


def _template_errors(tables: dict, where: str) -> list[str]:
    """Team templates: 4 to 6 slots of known careers; followers of known careers and quality table."""
    careers, quality, errors = {c["id"] for c in tables["careers"]}, tables.get("followers", {}).get("quality", {}), []
    for t in tables["templates"]:
        if not 4 <= len(t["slots"]) <= 6 or any(cid not in careers or n < 1 for cid, n in t["slots"]):
            errors.append(f"{where}: template {t['id']} needs 4 to 6 slots of known careers, each with a term or more")
        if any(cid not in careers or n < 0 for cid, n in t.get("followers", [])) or t.get("follower_quality", "default") not in quality:
            errors.append(f"{where}: template {t['id']} followers need known careers and a known quality table")
    return errors


def _team_mod_errors(where: str, name: str, o: dict, chars: set, skills: set) -> list[str]:
    """An origin: its skill, trait and drawback name known skills and characteristics."""
    keys = [o["gain"]] + [k for m in (o["trait"], o["drawback"]) for k in m if k != "text"]
    return [f"{where}: origin {name} names unknown {k}" for k in keys if k not in chars | skills]


def _career_errors(d: Data, era: dict, where: str, c: dict, chars: set, skills: set) -> list[str]:
    """A career: its skills, array order, term rows (ending at 100), kits and weapons per region."""
    T, errors = era, []
    if c["main"] not in skills or c["second"] not in skills or set(c["prefers"]) != chars:
        errors.append(f"{where}: career {c['id']} needs a known main skill and prefers naming every characteristic once")
    rows = c["terms"]
    if rows[-1]["to"] != 100 or any(r["skill"] not in skills for r in rows) or [r["to"] for r in rows] != sorted(r["to"] for r in rows):
        errors.append(f"{where}: career {c['id']} terms must rise to 100 and name known skills")
    for r in T["regions"]:
        kit, wpn = c["kit"].get(r["id"], c["kit"]["default"]), c["weapon"].get(r["id"], c["weapon"]["default"])
        if kit not in d.armor["kits"] or wpn not in available_weapons(d, r["table"]) or c["wound_weapon"] not in available_weapons(d, r["table"]):
            errors.append(f"{where}: career {c['id']} in {r['id']}: kit {kit}, weapon {wpn} or wound weapon {c['wound_weapon']} not usable there")
    return errors


ANY_PERIOD = "Any period"


def periods(d: Data) -> dict:
    """The period each campaign map and battlefield is listed under in the pickers: {maps: {id:
    period}, fields: {id: period}, order: [period, ...]}. A file's own `period`, else a
    battlefield's wound table's conflict (its `battle` group), else for a map the period of a
    battlefield on it; a map with none is "Any period". The order is by the earliest start date
    of the maps in each period (a battlefield counts its map's), "Any period" last."""
    fields = {fid: f.get("period") or d.tables[f["table"]]["battle"] for fid, f in d.fields.items()}
    maps = {}
    for mid, m in d.maps.items():
        on = [fid for fid, f in d.fields.items() if (f.get("travel") or {}).get("map") == mid]
        maps[mid] = m.get("period") or (fields[on[0]] if on else ANY_PERIOD)
    year = lambda mid: str(d.maps[mid].get("start_date", "9999"))[:4]
    first = {}
    for mid, p in maps.items():
        first[p] = min(first.get(p, "9999"), year(mid))
    for fid, p in fields.items():
        mid = (d.fields[fid].get("travel") or {}).get("map")
        first[p] = min(first.get(p, "9999"), year(mid) if mid in d.maps else "9999")
    order = sorted((p for p in first if p != ANY_PERIOD), key=lambda p: (first[p], p)) + ([ANY_PERIOD] if ANY_PERIOD in first else [])
    return {"maps": maps, "fields": fields, "order": order}


def _fields_errors(d: Data) -> list[str]:
    """data/fields: battlefields for the field map, each with its ground, works, weather and
    (optionally) the armies as drawn up."""
    from .units import battlefield, battlefield_units, _fits   # here: units imports this module
    errors = _marker_default_errors(d)
    for fid, f in d.fields.items():
        where = f"fields/{fid}"
        st = f.get("stances")
        if st is not None and not (isinstance(st, list) and len(st) == 2 and all(x in ("attack", "hold") for x in st)):
            errors.append(f"{where}: stances must be two of attack or hold")
        if "ends" in f and not (isinstance(f["ends"], int) and not isinstance(f["ends"], bool) and f["ends"] >= 1):
            errors.append(f"{where}: ends must be a whole number of exchanges, 1 or more")
        bad = _field_shape_errors(d, f, where)
        errors += bad or _field_unit_errors(d, f, where, battlefield, battlefield_units, _fits)
        errors += _field_marker_errors(d, f, where)
        errors += _account_errors(f, where)
    return errors


def _account_errors(f: dict, where: str) -> list[str]:
    """A battlefield's accounts (where the accounts disagree, as a choice on the field map): each an id, a
    question and two or more options (data/accounts.yaml), the first the game's own (no changes); an option's
    changes scale a side's men (side, scale), set or scale a unit's (unit, men or scale), or move a phase (phase, at)."""
    A = f.get("accounts")
    if A is None:
        return []
    if not isinstance(A, list) or not A:
        return [f"{where}: accounts must be a list"]
    errors, ids = [], set()
    for q in A:
        qid = q.get("id") if isinstance(q, dict) else None
        if not (isinstance(qid, str) and qid and qid not in ids and isinstance(q.get("question"), str)):
            errors.append(f"{where}: each account needs its own id and a question")
            continue
        ids.add(qid)
        errors += _question_errors(f, q, f"{where}: account {qid}")
    return errors


def _question_errors(f: dict, q: dict, where: str) -> list[str]:
    """One question's options: two or more, each with a label; the first changes nothing, each other has changes."""
    opts = q.get("options")
    if not (isinstance(opts, list) and len(opts) >= 2 and all(isinstance(o, dict) and isinstance(o.get("label"), str) for o in opts)):
        return [f"{where} needs two or more options, each with a label"]
    errors = [f"{where}: the first option is the game's own and changes nothing"] if opts[0].get("changes") else []
    for o in opts[1:]:
        errors += [f"{where}, {o['label']!r}: {e}" for e in _change_errors(f, o.get("changes"))]
    return errors


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def _change_error(c, units: set, ats: dict) -> str | None:
    """One change, as _account_errors says (a moved phase is moved in ats), or what is wrong with it."""
    if not isinstance(c, dict):
        return "each change must be a mapping"
    if "side" in c:
        ok = c["side"] in (0, 1) and _num(c.get("scale")) and set(c) == {"side", "scale"}
        return None if ok else "a side change is side (0 or 1) and scale (more than 0)"
    if "unit" in c:
        ok = c["unit"] in units and len(set(c) & {"men", "scale"}) == 1 and _num(c.get("men", c.get("scale")))
        return None if ok else f"a unit change names a unit of the field ({c.get('unit')!r}) and its men or scale"
    if "phase" in c:
        if c["phase"] not in ats or not isinstance(c.get("at"), int):
            return f"a phase change names a phase of the field ({c.get('phase')!r}) and its new exchange"
        ats[c["phase"]] = c["at"]
        return None
    return "a change is to a side, a unit or a phase"


def _change_errors(f: dict, changes) -> list[str]:
    """One option's changes; a moved phase must still come after the one before and before the next."""
    if not (isinstance(changes, list) and changes):
        return ["changes must be a list of one or more"]
    units = {u.get("name") for u in f.get("units", [])}
    ats = {p["name"]: p["at"] for p in f.get("phases") or []}
    errors = [e for e in (_change_error(c, units, ats) for c in changes) if e]
    seq = list(ats.values())
    if any(b <= a for a, b in zip(seq, seq[1:])) or (seq and seq[0] != 1):
        errors.append("the phases, as moved, must still begin at 1 and rise")
    return errors


MARKER_LABELS = ("names", "ids", "both")


def _marker_settings_errors(m, where: str) -> list[str]:
    """Marker settings: labels (names, ids or both), strength and size (true or false), all optional."""
    if not isinstance(m, dict) or set(m) - {"labels", "strength", "size"}:
        return [f"{where}: markers takes only labels, strength and size"]
    errors = [f"{where}: markers.labels must be names, ids or both"] if "labels" in m and m["labels"] not in MARKER_LABELS else []
    return errors + [f"{where}: markers.{k} must be true or false" for k in ("strength", "size") if k in m and not isinstance(m[k], bool)]


def _marker_default_errors(d: Data) -> list[str]:
    """units.yaml markers: the default settings, the unit types and the size marks."""
    M = d.units.get("markers")
    if not isinstance(M, dict) or not M.get("types") or not M.get("sizes"):
        return ["units.yaml: markers needs types and sizes"]
    return _marker_settings_errors({k: M[k] for k in ("labels", "strength", "size") if k in M}, "units.yaml")


def _phase_errors(f: dict, where: str) -> list[str]:
    """A battlefield's phases: each a name, the exchange it begins (the first 1, then rising), an
    optional note, and the units or batteries on call it brings on (the field's own, each in one phase only)."""
    P = f.get("phases")
    if P is None:
        return []
    if not isinstance(P, list) or not P:
        return [f"{where}: phases must be a list"]
    names = {u.get("name") for u in f.get("units", [])} | {s.get("name") for s in f.get("support", [])}
    seen, ats = set(), [st.get("at") for st in P]
    errors = [f"{where}: phase {i + 1} needs a name and its exchange (the first 1, each later than the one before)"
              for i, st in enumerate(P) if not _phase_ok(st, ats[i - 1] if i else 0, first=not i)]
    for i, st in enumerate(P):
        for n in st.get("arrive", []):
            if n not in names or n in seen:
                errors.append(f"{where}: phase {i + 1} brings on {n!r}, which is not a unit or battery of the field, or comes in another phase")
            seen.add(n)
    return errors


def _phase_ok(st: dict, before, first: bool) -> bool:
    """One phase's name and exchange: a name, and an exchange later than the one before (1 for the first)."""
    at, last = st.get("at"), before if isinstance(before, int) else 0
    return isinstance(st.get("name"), str) and bool(st["name"]) and isinstance(at, int) and at > last and (at == 1 or not first)


def _phase_when_errors(d: Data, f: dict, where: str) -> list[str]:
    """A battlefield's phases that begin on an event (when) or set the weather."""
    units = {u.get("name") for u in f.get("units", [])}
    errors = []
    for i, st in enumerate(f.get("phases") or []):
        if not isinstance(st, dict):
            continue
        if "when" in st and not _when_ok(st["when"], units, i):
            errors.append(f"{where}: phase {i + 1} begins when {{fires: a unit of the field, wait: exchanges}} or {{after: exchanges after the phase before}}")
        if "weather" in st and not _weather_ok(d, st["weather"]):
            errors.append(f"{where}: phase {i + 1} sets the weather as cond (a weather.yaml condition) and wind, both optional")
    return errors


def _when_ok(on, units: set, i: int) -> bool:
    """A phase's when: {fires: a unit of the field, wait (whole exchanges)}, or {after: n} (not the first phase)."""
    if not isinstance(on, dict):
        return False
    if set(on) <= {"fires", "wait"}:
        return on.get("fires") in units and isinstance(on.get("wait", 0), int)
    return set(on) == {"after"} and isinstance(on["after"], int) and i > 0


def _weather_ok(d: Data, w) -> bool:
    """A phase's weather: cond (a weather.yaml condition) and wind (a wind), either or both."""
    winds = {x["id"] for x in d.weather.get("winds", [])}
    if not isinstance(w, dict) or not set(w) <= {"cond", "wind"}:
        return False
    return ("cond" not in w or w["cond"] in d.weather.get("conditions", {})) and ("wind" not in w or w["wind"] in winds)


def _field_marker_errors(d: Data, f: dict, where: str) -> list[str]:
    """A battlefield's markers settings and entry edges, and each unit's type and size if it sets them."""
    M = d.units.get("markers") or {}
    errors = _marker_settings_errors(f["markers"], where) if "markers" in f else []
    e = f.get("entry")
    if e is not None and not (isinstance(e, list) and len(e) == 2 and all(x in ("N", "S", "E", "W") for x in e) and e[0] != e[1]):
        errors.append(f"{where}: entry must be two different edges (N, S, E or W), side A's first")
    errors += _phase_errors(f, where)
    errors += [f"{where}: phase {i + 1} sets unknown light {st['light']!r}" for i, st in enumerate(f.get("phases") or [])
               if isinstance(st, dict) and "light" in st and st["light"] not in (d.weather.get("light") or {}).get("levels", {})]
    errors += _phase_when_errors(d, f, where)
    for u in f.get("units", []):
        if "type" in u and u["type"] not in M.get("types", {}):
            errors.append(f"{where}: unit {u.get('name')}: type must be one of {', '.join(M.get('types', {}))}")
        if "size" in u and u["size"] not in M.get("sizes", {}):
            errors.append(f"{where}: unit {u.get('name')}: size must be one of {', '.join(M.get('sizes', {}))}")
    return errors


def _field_shape_errors(d: Data, f: dict, where: str) -> list[str]:
    """A battlefield's size, ground letters, sides, table, weather and works."""
    size = f.get("size")
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(x, int) and x > 0 for x in size)):
        return [f"{where}: size must be [cols, rows], whole numbers"]
    errors, keys = [], {g.get("key") for g in d.units.get("ground", {}).values()}
    if len(f["rows"]) != size[1] or any(len(r.strip()) != size[0] for r in f["rows"]):
        errors.append(f"{where}: ground needs {size[1]} rows of {size[0]} letters")
    bad = sorted({ch for r in f["rows"] for ch in r.strip()} - keys)
    if bad:
        errors.append(f"{where}: unknown ground letters {bad}")
    if len(f.get("sides", [])) != 2:
        errors.append(f"{where}: sides needs two names")
    if f.get("table") not in d.tables:
        errors.append(f"{where}: unknown table {f.get('table')}")
    errors += _field_weather_errors(d, f, where)
    errors += _field_travel_errors(d, f, where)
    works = f.get("works") or {}
    for kind, label, known in (("hexes", "hex", d.works.get("hex_works", {})), ("edges", "edge", d.works.get("edge_works", {}))):
        errors += [f"{where}: unknown {label} work {w.get('type')}" for w in works.get(kind, []) if w.get("type") not in known]
    kinds = (d.units.get("indirect") or {}).get("kinds", {})
    errors += [f"{where}: support {s.get('name')} needs a side (0 or 1), a known kind and tubes" for s in f.get("support", [])
               if s.get("side") not in (0, 1) or s.get("kind") not in kinds or not isinstance(s.get("tubes"), int) or s["tubes"] < 1]
    errors += [f"{where}: support {s.get('name')} place must be a hex [column, row] and its kind must have a range" for s in f.get("support", [])
               if "place" in s and not (isinstance(s["place"], list) and len(s["place"]) == 2 and all(isinstance(x, int) for x in s["place"])
                                        and (kinds.get(s.get("kind")) or {}).get("range"))]
    return errors


def _cold_errors(d: Data) -> list[str]:
    """weather.yaml cold (levels with a below, jam and move; jams known weapons) and disease.yaml
    frostbite (its peak steps on the track)."""
    C, F, errors = d.weather.get("cold") or {}, (d.disease or {}).get("frostbite"), []
    errors += [f"weather.yaml: cold.levels.{k} needs a name and numbers below, jam and move" for k, v in C.get("levels", {}).items()
               if not (v.get("name") and all(isinstance(v.get(x), (int, float)) for x in ("below", "jam", "move")))]
    errors += [f"weather.yaml: cold.jams names unknown weapon {w}" for w in C.get("jams", []) if w not in d.weapons]
    if F:
        errors += [f"disease.yaml: frostbite peak step {x.get('step')} is not on the track" for x in F.get("peak", []) if x.get("step") not in d.disease["steps"]]
    return errors


def _night_vision_errors(nv: dict) -> list[str]:
    """weather.yaml light.night_vision: kits and a kit device, devices with a name, sight and aim,
    vehicles' devices known, and the infrared beam's reach."""
    errors, devs = [], nv.get("devices") or {}
    if not (isinstance(nv.get("kits"), list) and nv.get("kit_device") in devs) or any(
            not (v.get("name") and isinstance(v.get("sight"), int) and isinstance(v.get("aim"), int)) for v in devs.values()):
        errors.append("weather.yaml: light.night_vision needs kits, a kit_device among its devices, and devices with a name, sight and aim")
    errors += [f"weather.yaml: light.night_vision.vehicles.{w} names unknown device {v}" for w, v in (nv.get("vehicles") or {}).items() if v not in devs]
    if not (isinstance(nv.get("beam"), int) and nv["beam"] >= 1):
        errors.append("weather.yaml: light.night_vision.beam must be a whole number of 1 or more")
    return errors


def _light_errors(wx: dict) -> list[str]:
    """weather.yaml light: levels with a name, a sight in battle hexes (or null) and an aim %;
    day among them; weather that shows the moon among the conditions."""
    L = wx.get("light")
    if not L:
        return []
    errors = [f"weather.yaml: light.levels.{k} needs a name, sight (a number or null) and aim (a number)"
              for k, v in L.get("levels", {}).items()
              if not (v.get("name") and (v.get("sight") is None or isinstance(v["sight"], int)) and isinstance(v.get("aim"), int))]
    if "day" not in L.get("levels", {}):
        errors.append("weather.yaml: light.levels needs day")
    errors += [f"weather.yaml: light.moon_shows names unknown condition {c}" for c in L.get("moon_shows", []) if c not in wx["conditions"]]
    errors += [f"weather.yaml: light.levels.{k} needs move and lost (numbers)" for k, v in L.get("levels", {}).items()
               if not (isinstance(v.get("move"), int) and isinstance(v.get("lost"), int))]
    F = L.get("fixed_line") or {}
    errors += _night_vision_errors(L.get("night_vision") or {})
    if not (isinstance(F.get("width"), int) and isinstance(F.get("aim"), int)):
        errors.append("weather.yaml: light.fixed_line needs width and aim")
    return errors + [f"weather.yaml: light.{k} must be a number" for k in ("dusk_hours", "moon_from", "lasts", "flare", "flash", "lost_for") if not isinstance(L.get(k), (int, float))]


def _field_weather_errors(d: Data, f: dict, where: str) -> list[str]:
    """A battlefield's weather: a known condition, and its wind direction and the compass point
    at the top of its map among the wind points."""
    errors, wx = [], f.get("weather") or {}
    if wx and wx.get("cond") not in d.weather.get("conditions", {}):
        errors.append(f"{where}: unknown weather {wx.get('cond')}")
    if wx.get("cold") and wx["cold"] not in ((d.weather.get("cold") or {}).get("levels") or {}):
        errors.append(f"{where}: unknown cold {wx.get('cold')}")
    if wx.get("light", "day") not in (d.weather.get("light") or {}).get("levels", {"day": 1}):
        errors.append(f"{where}: unknown light {wx.get('light')}")
    pts = d.weather.get("wind_points", [])
    if pts and (wx.get("dir", pts[0]) not in pts or f.get("up", "N") not in pts):
        errors.append(f"{where}: weather.dir and up must be compass points {pts}")
    return errors


def _field_travel_errors(d: Data, f: dict, where: str) -> list[str]:
    """The travel-map link: a known map and place, a reach in hexes, and the two sides."""
    t = f.get("travel")
    if t is None:
        return []
    m = d.maps.get(t.get("map"))
    if m is None:
        return [f"{where}: travel.map {t.get('map')} is not a travel map"]
    errors = []
    if t.get("place") not in {p["name"] for p in m.get("places", [])}:
        errors.append(f"{where}: travel.place {t.get('place')} is not a place on {t['map']}")
    if not (isinstance(t.get("within"), int) and t["within"] >= 0):
        errors.append(f"{where}: travel.within must be a whole number of hexes, 0 or more")
    if len(t.get("sides", [])) != 2:
        errors.append(f"{where}: travel.sides needs two side names")
    return errors


def _unit_spec_errors(d: Data, f: dict, where: str, u: dict) -> list[str]:
    """One unit as drawn up: side and men, arms the tables offer, armour, quality, formation, guns."""
    U, errors = d.units, []
    if u.get("side") not in (0, 1) or not isinstance(u.get("men"), int) or u["men"] < 1:
        errors.append(f"{where}: unit {u.get('name')} needs side 0 or 1 and men")
    if u.get("weapon") not in available_weapons(d, f["table"]) or u.get("kit") not in d.armor["kits"]:
        errors.append(f"{where}: unit {u.get('name')} has a weapon the {f['table']} tables do not offer, or an unknown kit")
    if u.get("quality") not in U["quality"] or u.get("formation") not in U["formations"]:
        errors.append(f"{where}: unit {u.get('name')} has an unknown quality or formation")
    if u.get("guns", "smoothbore") not in ("smoothbore", "rifled", "howitzer"):
        errors.append(f"{where}: unit {u.get('name')} has guns other than smoothbore, rifled or howitzer")
    vk = (U.get("vehicles") or {}).get("kinds", {})
    if ("vehicle" in u) != (u.get("formation") == "armour") or ("vehicle" in u and u["vehicle"] not in vk):
        errors.append(f"{where}: unit {u.get('name')}: a vehicle unit needs a known vehicle kind and the armour formation, and only it")
    return errors


def _objective_errors(f: dict, where: str) -> list[str]:
    """A battlefield's objective: a hex on the map, the army that attacked it (0 or 1) and a name."""
    o = f.get("objective")
    if o is None:
        return []
    at = o.get("at")
    on = isinstance(at, list) and len(at) == 2 and 0 <= at[0] < f["size"][0] and 0 <= at[1] < f["size"][1]
    radius = o.get("radius", 1)
    if on and o.get("side") in (0, 1) and isinstance(o.get("name"), str) and o["name"] and isinstance(radius, int) and radius >= 1:
        return []
    return [f"{where}: objective needs at (a hex on the map), side (0 or 1: the army that attacked it), a name, and radius a whole number of 1 or more if given"]


def _flag_errors(f: dict, where: str) -> list[str]:
    """A battlefield's units' true-or-false marks: fac (a forward air controller), ladders."""
    names = {"fac": "fac (a forward air controller)", "ladders": "ladders"}
    return [f"{where}: unit {u.get('name')}: {names[k]} must be true or false" for u in f.get("units", []) for k in names
            if k in u and not isinstance(u[k], bool)]


def _fc_errors(d: Data, f: dict, where: str) -> list[str]:
    """Each battlefield unit's fire control (fc) and armour, if it gives them: a known fire control,
    on a vehicle kind that has one (a tank); a known armour, on a vehicle."""
    V = d.units.get("vehicles") or {}
    fcs, kinds = {k for k in (V.get("fire_control") or {}) if k != "by_war"}, V.get("kinds") or {}
    armours = set(V.get("armour") or {})
    errors = [f"{where}: unit {u.get('name')}: fc (fire control) must be one of {sorted(fcs)}, on a tank" for u in f.get("units", [])
              if "fc" in u and (u["fc"] not in fcs or not (kinds.get(u.get("vehicle") or "") or {}).get("fc"))]
    return errors + [f"{where}: unit {u.get('name')}: armour must be one of {sorted(armours)}, on a vehicle" for u in f.get("units", [])
                     if "armour" in u and (u["armour"] not in armours or not u.get("vehicle"))]


def _via_errors(f: dict, where: str) -> list[str]:
    """Each battlefield unit's route (via), if it has one: a list of hexes on the map."""
    def on_map(h) -> bool:
        return isinstance(h, list) and len(h) == 2 and all(isinstance(x, int) for x in h) and 0 <= h[0] < f["size"][0] and 0 <= h[1] < f["size"][1]
    return [f"{where}: unit {u.get('name')}: via (its route) must be a list of hexes on the map" for u in f.get("units", [])
            if "via" in u and not (isinstance(u["via"], list) and u["via"] and all(on_map(h) for h in u["via"]))]


def _dump_errors(f: dict, where: str) -> list[str]:
    """The supply dumps a battlefield places, if any: each a hex on the map and a side (0 or 1)."""
    def ok(m) -> bool:
        h = m.get("at") if isinstance(m, dict) else None
        return (isinstance(h, list) and len(h) == 2 and all(isinstance(x, int) for x in h) and 0 <= h[0] < f["size"][0]
                and 0 <= h[1] < f["size"][1] and m.get("side") in (0, 1))
    dumps = f.get("dumps") or []
    if not isinstance(dumps, list):
        return [f"{where}: dumps must be a list of supply dumps"]
    return [f"{where}: dumps must each be {{at: a hex on the map, side: 0 or 1}}" for m in dumps if not ok(m)]


def _field_unit_errors(d: Data, f: dict, where: str, battlefield, battlefield_units, fits) -> list[str]:
    """The armies as drawn up: known arms, armour and formations, each unit standing where it can."""
    errors = [e for u in f.get("units", []) for e in _unit_spec_errors(d, f, where, u)]
    lz = f.get("lz") or []
    errors += _objective_errors(f, where)
    errors += [f"{where}: lz must be hexes on the map" for h in lz
               if not (isinstance(h, list) and len(h) == 2 and 0 <= h[0] < f["size"][0] and 0 <= h[1] < f["size"][1])]
    errors += [f"{where}: unit {u.get('name')} lands must be the number of a landing zone (0 to {len(lz) - 1})" for u in f.get("units", [])
               if "lands" in u and not (isinstance(u["lands"], int) and 0 <= u["lands"] < len(lz))]
    errors += _via_errors(f, where)
    errors += _dump_errors(f, where)
    errors += _fc_errors(d, f, where)
    errors += [f"{where}: unit {u.get('name')}: fixed (a machine gun's fixed line) must be a hex on the map, for a machine gun" for u in f.get("units", [])
               if "fixed" in u and not (isinstance(u["fixed"], list) and len(u["fixed"]) == 2 and 0 <= u["fixed"][0] < f["size"][0]
                                        and 0 <= u["fixed"][1] < f["size"][1] and u.get("weapon") in (d.units.get("machine_guns") or {}).get("weapons", []))]
    devices = set((d.weather.get("light", {}).get("night_vision") or {}).get("devices") or {}) | {"none"}
    errors += [f"{where}: unit {u.get('name')}: nv (a night-vision device) must be one of {', '.join(sorted(devices))}" for u in f.get("units", [])
               if "nv" in u and u["nv"] not in devices]
    errors += _flag_errors(f, where)
    if errors:
        return errors
    field, units = battlefield(d, f["id"]), battlefield_units(d, f["id"])
    for i, u in enumerate(units):
        if not fits(d, units, i, u, tuple(f["size"]), field):
            errors.append(f"{where}: unit {u['name']} does not fit where it stands")
    return errors


def _wind_errors(d: Data) -> list[str]:
    """weather.yaml: eight wind points, each climate's prevailing winds summing to 100, and
    whole-number reach and into_wind for each wind."""
    WX, errors = d.weather, []
    if len(WX["wind_points"]) != 8:
        errors.append("weather.yaml: wind_points needs eight compass points, N first, clockwise")
    for cid, cl in WX.get("climates", {}).items():
        if len(cl.get("wind_from", [])) != 8 or sum(cl.get("wind_from", [])) != 100:
            errors.append(f"weather.yaml: climate {cid} wind_from needs eight % summing to 100")
    for w in WX.get("winds", []):
        if not all(isinstance(w.get(k), int) and w[k] >= 0 for k in ("reach", "into_wind")):
            errors.append(f"weather.yaml: wind {w.get('id')} needs whole-number reach and into_wind")
    return errors
