# -*- coding: utf-8 -*-
"""Συγχώνευση Overture Maps Places (data/ext/overture.json) με τα σημεία OSM.
Καλείται από το build_data.py. Δεν τρέχει μόνο του.

- Κρατά μόνο taxonomy food_and_drink, χαρτογραφεί την κατηγορία Overture σε ψευδο-tags OSM
  και χρησιμοποιεί τον ίδιο classify() με το OSM (ίδιοι κανόνες ονομάτων).
- Αν ένα σημείο Overture ταιριάζει με σημείο OSM (κοντά + παρόμοιο όνομα) -> εμπλουτίζει το OSM
  (τηλ., site, e-mail, Facebook/Instagram, διεύθυνση) και ΔΕΝ μπαίνει ως νέο.
- Αλλιώς μπαίνει ως νέο σημείο (id "v..."), αν έχει confidence >= MIN_CONF_NEW.
"""
import json, math, os, re, unicodedata
from difflib import SequenceMatcher

MIN_CONF_NEW = 0.6      # ελάχιστη βεβαιότητα για νέο σημείο
MIN_CONF_ENRICH = 0.3   # ελάχιστη βεβαιότητα για εμπλουτισμό υπάρχοντος
MATCH_M = 80            # απόσταση για αντιστοίχιση με παρόμοιο όνομα
SAME_NAME_M = 200       # απόσταση για αντιστοίχιση με (σχεδόν) ίδιο όνομα

# Overture taxonomy.primary -> ψευδο-tags OSM (None = εκτός χάρτη)
CAT = {
    "cafe": {"amenity": "cafe"}, "coffee_shop": {"amenity": "cafe"},
    "tea_room": {"amenity": "cafe"},
    "breakfast_and_brunch_restaurant": {"amenity": "cafe", "cuisine": "brunch"},
    "smoothie_juice_bar": {"amenity": "cafe", "cuisine": "juice"},
    "bubble_tea_shop": {"amenity": "cafe", "cuisine": "bubble_tea"},
    "restaurant": {"amenity": "restaurant"}, "diner": {"amenity": "restaurant"},
    "food_and_drink": {"amenity": "restaurant", "_namecheck": True},
    "greek_restaurant": {"amenity": "restaurant", "cuisine": "greek"},
    "mediterranean_restaurant": {"amenity": "restaurant", "cuisine": "greek"},
    "comfort_food_restaurant": {"amenity": "restaurant", "cuisine": "greek"},
    "pizza_restaurant": {"amenity": "restaurant", "cuisine": "pizza"},
    "fast_food_restaurant": {"amenity": "fast_food"},
    "food_truck_stand": {"amenity": "fast_food"},
    "hot_dog_restaurant": {"amenity": "fast_food"},
    "doner_kebab_restaurant": {"amenity": "fast_food", "cuisine": "kebab"},
    "seafood_restaurant": {"amenity": "restaurant", "cuisine": "seafood"},
    "fish_and_chips_restaurant": {"amenity": "restaurant", "cuisine": "seafood"},
    "barbecue_restaurant": {"amenity": "restaurant", "cuisine": "grill"},
    "steakhouse": {"amenity": "restaurant", "cuisine": "grill"},
    "meat_restaurant": {"amenity": "restaurant", "cuisine": "grill"},
    "bar_and_grill_restaurant": {"amenity": "restaurant", "cuisine": "grill"},
    "burger_restaurant": {"amenity": "fast_food", "cuisine": "burger"},
    "chicken_restaurant": {"amenity": "fast_food", "cuisine": "chicken"},
    "sandwich_shop": {"amenity": "fast_food", "cuisine": "sandwich"},
    "bagel_shop": {"amenity": "fast_food", "cuisine": "sandwich"},
    "salad_bar": {"amenity": "fast_food", "cuisine": "salad"},
    "health_food_restaurant": {"amenity": "restaurant", "cuisine": "healthy"},
    "soup_restaurant": {"amenity": "restaurant"},
    "pancake_house": {"amenity": "fast_food", "cuisine": "crepe"},
    "italian_restaurant": {"amenity": "restaurant", "cuisine": "italian"},
    "vegetarian_restaurant": {"amenity": "restaurant", "cuisine": "vegetarian"},
    "vegan_restaurant": {"amenity": "restaurant", "cuisine": "vegan"},
    "bakery": {"shop": "bakery"},
    "dessert_shop": {"shop": "pastry"}, "donut_shop": {"shop": "pastry"},
    "cupcake_shop": {"shop": "pastry"}, "chocolatier": {"shop": "pastry"},
    "candy_store": {"shop": "pastry", "_namecheck": True},
    "ice_cream_shop": {"amenity": "ice_cream"}, "gelato_shop": {"amenity": "ice_cream"},
    "frozen_yogurt_shop": {"amenity": "ice_cream"},
    "food_court": {"amenity": "food_court"},
    "bar": {"amenity": "bar"}, "lounge": {"amenity": "bar"}, "hookah_bar": {"amenity": "bar"},
    "sports_bar": {"amenity": "bar"}, "dive_bar": {"amenity": "bar"}, "gay_bar": {"amenity": "bar"},
    "hotel_bar": {"amenity": "bar"}, "whiskey_bar": {"amenity": "bar"},
    "wine_bar": {"amenity": "bar", "drink:wine": "yes"},
    "cocktail_bar": {"amenity": "bar", "cocktails": "yes"},
    "beer_bar": {"amenity": "pub", "name_hint": "beer"}, "pub": {"amenity": "pub"},
    "gastropub": {"amenity": "pub"}, "brewery": {"amenity": "pub", "name_hint": "beer"},
    "beer_garden": {"amenity": "biergarten"},
    "night_club": {"amenity": "nightclub"}, "dance_club": {"amenity": "nightclub"},
}
ASIAN = ("asian", "sushi", "japanese", "chinese", "thai", "vietnamese", "korean", "indian",
         "burmese", "indonesian", "pan_asian", "asian_fusion", "noodle", "ramen", "poke")
# εκτός: delicatessen, internet_cafe, winery, distillery, airport_lounge, κ.λπ. (δεν είναι στο CAT)

# λέξεις στο όνομα που δείχνουν ότι είναι όντως κατάστημα εστίασης (για γενικές κατηγορίες)
FOODWORDS = ("καφε", "cafe", "coffee", "ταβερν", "tavern", "σουβλ", "souvl", "γυρο", "gyro", "ψησταρ",
             "pizza", "πιτσ", "burger", "μεζε", "meze", "ουζερ", "τσιπουρ", "bar", "μπαρ", "εστιατ",
             "restaurant", "bistro", "κρεπ", "crep", "ζαχαροπλ", "pastry", "γλυκ", "sweet", "μπουγατσ",
             "bougats", "φουρν", "αρτοπ", "bakery", "brunch", "grill", "kitchen", "κουζιν", "food", "φαγ",
             "πατσα", "μαγειρ", "ψαρ", "fish", "sushi", "κοτοπουλ", "chicken", "καντιν")
NOT_SHOP = ("ξηρ", "καρπ", "nuts", "mini market", "market", "s.a.", "α.ε.", "ae ", "catering",
            "olive oil", "ελαιολαδ", "αβγα", "αυγα", "foods", "τυρ", "cheese", "κρεοπωλ", "χονδρ")

GR2LAT = str.maketrans({"α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i", "θ": "th",
                        "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p",
                        "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "ch", "ψ": "ps",
                        "ω": "o"})
STOP = {"to", "ta", "o", "i", "oi", "tou", "tis", "the", "cafe", "kafe", "bar", "restaurant", "estiatorio",
        "taverna", "tavern", "coffee", "kafeteria", "psistaria", "souvlakia", "and", "kai", "&", "by", "&amp;"}


def _plain(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


def key(name):
    """Όνομα σε λατινικά, χωρίς τόνους/σημεία/γενικές λέξεις -> για σύγκριση OSM/Overture."""
    s = _plain(name).translate(GR2LAT)
    s = s.replace("ou", "u").replace("ch", "h").replace("ph", "f").replace("y", "i").replace("ee", "i")
    toks = [t for t in re.split(r"[^a-z0-9]+", s) if t and t not in STOP]
    return " ".join(toks)


def similar(a, b):
    ka, kb = key(a), key(b)
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 1.0
    if len(min(ka, kb, key=len)) >= 4 and (ka in kb or kb in ka):
        return 0.9
    return SequenceMatcher(None, ka, kb).ratio()


def dist_m(lat1, lon1, lat2, lon2):
    dx = (lon2 - lon1) * 111320 * math.cos(math.radians((lat1 + lat2) / 2))
    dy = (lat2 - lat1) * 110540
    return math.hypot(dx, dy)


class Grid:
    """Απλό χωρικό ευρετήριο (κελιά ~250 m)."""
    S = 0.0025

    def __init__(self):
        self.cells = {}

    def add(self, p):
        k = (int(p["lat"] / self.S), int(p["lon"] / self.S))
        self.cells.setdefault(k, []).append(p)

    def near(self, lat, lon):
        i, j = int(lat / self.S), int(lon / self.S)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                yield from self.cells.get((i + di, j + dj), ())


def pseudo_tags(o):
    tax = o.get("taxonomy") or {}
    prim = tax.get("primary") or o.get("basic_category") or ""
    t = dict(CAT.get(prim) or {})
    if not t:
        if prim.endswith("_restaurant"):
            t = {"amenity": "restaurant",
                 "cuisine": "asian" if any(a in prim for a in ASIAN) else "international"}
        else:
            return None, prim
    if t.pop("name_hint", None):
        t["amenity"] = "biergarten"
    name = o.get("name") or ""
    n = _plain(name)
    if any(w in n for w in NOT_SHOP):
        return None, prim
    if t.pop("_namecheck", False) and not any(w in n for w in FOODWORDS):
        return None, prim
    t["name"] = name
    return t, prim


def split_links(o):
    fb = ig = tt = web = None
    for u in (o.get("socials") or []) + (o.get("websites") or []):
        lu = (u or "").lower()
        if "facebook.com" in lu or "fb.com" in lu:
            fb = fb or u
        elif "instagram.com" in lu:
            ig = ig or u
        elif "tiktok.com" in lu:
            tt = tt or u
        elif lu.startswith("http") and not web:
            web = u
    return web, fb, ig, tt


def addr_of(o):
    for a in o.get("addresses") or []:
        parts = [a.get("freeform"), " ".join(x for x in [a.get("postcode"), a.get("locality")] if x)]
        s = ", ".join(x for x in parts if x)
        if s:
            return s
    return None


def phone_of(o):
    ph = [p for p in (o.get("phones") or []) if p]
    return ph[0] if ph else None


def find_match(grid, name, lat, lon):
    best, best_s = None, 0.0
    for p in grid.near(lat, lon):
        d = dist_m(lat, lon, p["lat"], p["lon"])
        if d > SAME_NAME_M:
            continue
        s = max(similar(name, p["name"]), similar(name, p.get("name_en") or ""))
        ok = (s >= 0.95 and d <= SAME_NAME_M) or (s >= 0.75 and d <= MATCH_M)
        if ok and s - d / 2000 > best_s:
            best, best_s = p, s - d / 2000
    return best


def enrich(p, o):
    """Συμπληρώνει μόνο τα κενά πεδία του p από το Overture o."""
    web, fb, ig, tt = split_links(o)
    vals = {"phone": phone_of(o), "website": web, "facebook": fb, "instagram": ig, "tiktok": tt,
            "email": (o.get("emails") or [None])[0], "address": addr_of(o)}
    added = 0
    for k, v in vals.items():
        if v and not p.get(k):
            p[k] = v
            added += 1
    p.setdefault("src", ["osm"])
    if "overture" not in p["src"]:
        p["src"].append("overture")
    p["ovt"] = o["id"]
    return added


def merge(places, path, classify, find_dimos, include):
    if not os.path.exists(path):
        print("Overture: δεν βρέθηκε", path, "- παραλείπεται (τρέξε scripts/fetch_overture.py)")
        return places
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    grid = Grid()
    for p in places:
        grid.add(p)

    stats = dict(total=0, food=0, closed=0, lowconf=0, outside=0, matched=0, fields=0, new=0, skipped_cat=0)
    from collections import Counter
    unknown = Counter()
    rows = sorted(data["places"], key=lambda o: -(o.get("confidence") or 0))
    for o in rows:
        stats["total"] += 1
        tax = o.get("taxonomy") or {}
        if not tax.get("hierarchy") or tax["hierarchy"][0] != "food_and_drink":
            continue
        stats["food"] += 1
        if o.get("operating_status") in ("permanently_closed", "temporarily_closed"):
            stats["closed"] += 1
            continue
        name = (o.get("name") or "").strip()
        if not name or o.get("lat") is None:
            continue
        t, prim = pseudo_tags(o)
        if t is None:
            stats["skipped_cat"] += 1
            unknown[prim] += 1
            continue
        conf = o.get("confidence") or 0
        if conf < MIN_CONF_ENRICH:
            stats["lowconf"] += 1
            continue
        lat, lon = o["lat"], o["lon"]
        m = find_match(grid, name, lat, lon)
        if m is not None:
            if "ovt" not in m:  # αλλιώς είναι διπλό μέσα στο ίδιο το Overture
                stats["matched"] += 1
                stats["fields"] += enrich(m, o)
            continue
        if conf < MIN_CONF_NEW:
            stats["lowconf"] += 1
            continue
        dimos = find_dimos(lon, lat)
        if dimos not in include:
            stats["outside"] += 1
            continue
        cat, sub = classify(t)
        web, fb, ig, tt = split_links(o)
        p = {
            "id": "v" + o["id"][:16],
            "name": name,
            "cat": cat, "sub": sub,
            "lat": round(lat, 6), "lon": round(lon, 6),
            "dimos": dimos,
            "address": addr_of(o),
            "phone": phone_of(o),
            "email": (o.get("emails") or [None])[0],
            "website": web, "facebook": fb, "instagram": ig, "tiktok": tt,
            "brand": o.get("brand"),
            "ovt_cat": prim,
            "conf": round(conf, 2),
            "src": ["overture"],
            "ovt": o["id"],
        }
        p = {k: v for k, v in p.items() if v not in (None, "", [])}
        places.append(p)
        grid.add(p)
        stats["new"] += 1
    print("Overture %s:" % data.get("release"), stats)
    if unknown:
        print("  εκτός (κατηγορία/όνομα):", unknown.most_common(12))
    return places
