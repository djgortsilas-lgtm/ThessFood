# -*- coding: utf-8 -*-
"""
Μετατροπή των ακατέργαστων δεδομένων OpenStreetMap (όλα τα data/raw/*.json)
στο αρχείο της εφαρμογής public/data/places.json.

Χρήση:  python scripts/build_data.py
Προαιρετικά: data/overrides.json  -> χειροκίνητες διορθώσεις/προσθήκες ανά id
             data/gemi.json       -> στοιχεία ΓΕΜΗ ανά id (από enrich_gemi.py)
"""
import json, os, re, sys, unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "osm.json")
OUT = os.path.join(ROOT, "public", "data", "places.json")
OVR = os.path.join(ROOT, "data", "overrides.json")
GEMI = os.path.join(ROOT, "data", "gemi.json")
OVT = os.path.join(ROOT, "data", "ext", "overture.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Δήμοι του πολεοδομικού συγκροτήματος (ονόματα όπως στο OSM, χωρίς "Δήμος ")
METRO = {
    "Θεσσαλονίκης", "Καλαμαριάς", "Πυλαίας - Χορτιάτη", "Νεάπολης - Συκεών",
    "Παύλου Μελά", "Αμπελοκήπων - Μενεμένης", "Κορδελιού - Ευόσμου",
    "Θέρμης", "Θερμαϊκού", "Δέλτα", "Ωραιοκάστρου", "Χαλκηδόνος", "Λαγκαδά", "Βόλβης",
}
# Δήμοι που μπαίνουν στον χάρτη (οι πιο απομακρυσμένοι μένουν εκτός)
INCLUDE = {
    "Θεσσαλονίκης", "Καλαμαριάς", "Πυλαίας - Χορτιάτη", "Νεάπολης - Συκεών",
    "Παύλου Μελά", "Αμπελοκήπων - Μενεμένης", "Κορδελιού - Ευόσμου",
    "Θέρμης", "Θερμαϊκού", "Δέλτα", "Ωραιοκάστρου",
}


def norm(s):
    s = (s or "").lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("ς", "σ")


def has(text, *words):
    t = norm(text)
    return any(norm(w) in t for w in words)


# ------------------------------------------------------------------ κατηγορίες
def classify(t):
    """Επιστρέφει (κύρια κατηγορία, υποκατηγορία)."""
    a = t.get("amenity", "")
    shop = t.get("shop", "")
    name = " ".join([t.get("name", ""), t.get("name:el", ""), t.get("name:en", "")])
    cui = norm(t.get("cuisine", "")).replace(" ", "")
    c = set(re.split(r"[;,]", cui)) if cui else set()

    def cu(*ks):
        return any(k in c for k in ks)

    # ---- Ποτό
    if a == "nightclub":
        return "drink", "club"
    if a == "biergarten" or (a == "pub" and has(name, "beer", "μπυρ", "brew")):
        return "drink", "beer_bar"
    if a == "pub":
        return "drink", "pub"
    if a == "bar":
        if has(name, "wine", "κρασ", "οινο", "vino", "vin ") or t.get("drink:wine") == "yes":
            return "drink", "wine_bar"
        if has(name, "cocktail", "κοκτειλ", "mixology") or t.get("cocktails") == "yes":
            return "drink", "cocktail_bar"
        if has(name, "beer", "μπυρ", "brew", "taproom", "draft", "ζυθ"):
            return "drink", "beer_bar"
        if has(name, "rakadiko", "ρακαδ", "τσιπουρ", "τσηπουρ", "ουζερ", "ouzer", "μεζεδ", "mezed", "οψοποι"):
            return "food", "meze"
        return "drink", "bar"

    # ---- Καφές
    if shop == "coffee":
        return "coffee", "coffee_roaster"
    if a == "cafe":
        if has(name, "μπουγατσ", "bougats") or cu("bougatsa"):
            return "food", "bougatsa"
        if has(name, "ουζερ", "ouzer", "τσιπουρ", "τσηπουρ", "μεζεδ", "mezed", "ρακαδ"):
            return "food", "meze"
        if cu("juice", "smoothie") or has(name, "juice", "χυμ"):
            return "coffee", "juice"
        if cu("bubble_tea") or has(name, "bubble"):
            return "coffee", "bubble_tea"
        if t.get("takeaway") == "only" or has(name, "take away", "takeaway", "to go", "coffee island",
                                                "coffee lab", "mikel", "everest", "coffeeway", "gregorys",
                                                "grigoris", "γρηγορη", "κοτσιανι"):
            return "coffee", "takeaway"
        if has(name, "brunch", "bistro", "μπιστρο") or cu("brunch", "breakfast"):
            return "coffee", "brunch"
        if cu("crepe") or has(name, "κρεπ", "crep"):
            return "food", "crepe"
        return "coffee", "cafe"

    # ---- Γλυκά / αρτοποιήματα
    if cu("bugatsa") or has(name, "μπουγατσ", "bougats", "bugats"):
        return "food", "bougatsa"
    if a == "ice_cream" or cu("ice_cream", "gelato", "frozen_yogurt"):
        return "food", "ice_cream"
    if shop in ("pastry", "confectionery"):
        if has(name, "μπουγατσ", "bougats"):
            return "food", "bougatsa"
        return "food", "pastry"
    if shop == "bakery":
        if has(name, "μπουγατσ", "bougats"):
            return "food", "bougatsa"
        return "food", "bakery"

    # ---- Φαγητό
    if a == "food_court":
        return "food", "food_court"
    if has(name, "μπουγατσ", "bougats") or cu("bougatsa"):
        return "food", "bougatsa"
    if a in ("fast_food", "restaurant"):
        if cu("juice", "smoothie") or has(name, "juice", "χυμ"):
            return "coffee", "juice"
        if cu("donut", "dessert", "cake", "waffle", "loukoumades") or has(name, "λουκουμα", "ντονατ", "donut", "waffle", "βαφλ"):
            return "food", "pastry"
        if has(name, "πατσα", "patsa"):
            return "food", "patsas"
        if cu("chicken") or has(name, "κοτοπουλ", "κοτα ", "κοτα", "chicken", "rooster", "κοκορ", "αλεκτωρ"):
            return "food", "chicken"
        if has(name, "goody", "everest", "γρηγορη", "grigoris", "mikel"):
            return "food", "burger" if has(name, "goody") else "sandwich"
        if cu("kebab", "souvlaki", "gyros", "gyro", "greek_souvlaki", "shawarma") or \
                has(name, "γυρο", "γυρισμ", "σουβλ", "souvlak", "gyro", "kebab", "κεμπαπ", "κεμπαμπ", "καλαμακ", "οβελισ",
                        "πανσετ", "καρβουν", "σχαρα", "λαδοκολλ", "πιτα ", "πιτογυρ"):
            return "food", "souvlaki"
        if cu("burger") or has(name, "burger", "μπεργκερ"):
            return "food", "burger"
        if cu("pizza") or has(name, "pizza", "πιτσ", "pizzeria"):
            return "food", "pizza"
        if cu("crepe") or has(name, "κρεπ", "crep"):
            return "food", "crepe"
        if cu("sushi", "japanese", "chinese", "asian", "thai", "vietnamese", "korean", "indian", "noodle",
              "ramen", "poke", "wok") or has(name, "sushi", "wok", "noodle", "ramen", "poke", "asian"):
            return "food", "asian"
        if cu("fish", "seafood") or has(name, "ψαρ", "θαλασσιν", "οστρακ", "fish", "seafood", "ουζερ", "ouzer"):
            return "food", "fish"
        if has(name, "μαγειρ", "mageir") or cu("μαγειρευτα", "home_cooking"):
            return "food", "mageireio"
        if has(name, "μεζε", "mezed", "τσιπουρ", "τσηπουρ", "tsipour", "ρακαδ", "rakad", "ουζ", "ouzo", "κουτουκ", "koutouk"):
            return "food", "meze"
        if has(name, "ταβερν", "tavern", "taverna") or cu("greek_taverna"):
            return "food", "taverna"
        if cu("steak_house", "grill", "barbecue", "bbq", "meat") or has(name, "ψησταρ", "ψητοπωλ", "grill", "κρεατ", "steak"):
            return "food", "grill"
        if cu("italian", "pasta") or has(name, "trattoria", "osteria", "pasta"):
            return "food", "italian"
        if cu("sandwich", "bagel", "wrap", "salad", "healthy") or has(name, "sandwich", "σαντουιτσ", "wrap"):
            return "food", "sandwich"
        if cu("vegan", "vegetarian") or has(name, "vegan"):
            return "food", "vegan"
        if cu("mexican", "lebanese", "middle_eastern", "turkish", "arab", "falafel", "french", "spanish",
              "international", "american", "georgian", "armenian", "ethiopian", "peruvian"):
            return "food", "international"
        if cu("greek", "regional", "mediterranean"):
            return "food", "taverna" if a == "restaurant" else "fast_food"
        if a == "fast_food":
            return "food", "fast_food"
        return "food", "restaurant"
    return "food", "restaurant"


# ------------------------------------------------------------------ γεωμετρία
def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def build_rings(rel):
    """Ενώνει τα outer ways ενός relation σε κλειστούς δακτυλίους."""
    segs = [[(p["lon"], p["lat"]) for p in m["geometry"]]
            for m in rel.get("members", []) if m.get("type") == "way" and m.get("role", "outer") in ("outer", "") and m.get("geometry")]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s + ring[1:]
                elif s[0] == ring[0]:
                    ring = s[::-1] + ring[1:]
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        rings.append(ring)
    return rings


def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def dimos_name(t):
    n = t.get("name:el") or t.get("name", "")
    return re.sub(r"^Δήμος\s+", "", n).strip()


# ------------------------------------------------------------------ βοηθητικά
def clean_url(u):
    if not u:
        return None
    u = u.strip().split(";")[0].strip()
    if not re.match(r"^https?://", u):
        u = "https://" + u
    return u


def social(t, key, base):
    v = t.get("contact:" + key) or t.get(key)
    if not v:
        return None
    v = v.strip().split(";")[0]
    if v.startswith("http"):
        return v
    return base + v.lstrip("@")


def first(t, *keys):
    for k in keys:
        if t.get(k):
            return t[k].strip()
    return None


def address(t):
    street = t.get("addr:street")
    num = t.get("addr:housenumber")
    pc = t.get("addr:postcode")
    city = t.get("addr:city")
    parts = []
    if street:
        parts.append(street + (" " + num if num else ""))
    if pc or city:
        parts.append(" ".join(x for x in [pc, city] if x))
    return ", ".join(parts) or None


def yes(t, k):
    v = t.get(k)
    if v in ("yes", "only", "designated"):
        return True
    if v == "no":
        return False
    return None


def main():
    # διαβάζει ΟΛΑ τα .json του data/raw (π.χ. dimoi.json + katastimata.json)
    import glob
    files = sorted(glob.glob(os.path.join(os.path.dirname(RAW), "*.json")))
    if not files:
        sys.exit("Δεν βρέθηκε κανένα .json στο " + os.path.dirname(RAW))
    raw, els = {}, []
    for fn in files:
        with open(fn, encoding="utf-8") as f:
            r = json.load(f)
        n = len(r.get("elements", []))
        print("Αρχείο:", os.path.basename(fn), n, "στοιχεία" + ("  <-- ΑΔΕΙΟ, αγνοείται" if not n else ""))
        raw = raw or r
        els += r.get("elements", [])

    dimoi = []
    for e in els:
        if e["type"] == "relation" and e.get("tags", {}).get("admin_level") == "7":
            rings = build_rings(e)
            if rings:
                dimoi.append((dimos_name(e["tags"]), rings, bbox(rings)))
    print("Δήμοι:", len(dimoi), sorted(d[0] for d in dimoi))

    def find_dimos(lon, lat):
        for name, rings, (x0, y0, x1, y1) in dimoi:
            if x0 <= lon <= x1 and y0 <= lat <= y1:
                if any(point_in_ring(lon, lat, r) for r in rings):
                    return name
        return None

    overrides = json.load(open(OVR, encoding="utf-8")) if os.path.exists(OVR) else {}
    gemi = json.load(open(GEMI, encoding="utf-8")) if os.path.exists(GEMI) else {}

    places, seen = [], set()
    skipped_noname = skipped_area = 0
    for e in els:
        if e["type"] == "relation" and e.get("tags", {}).get("admin_level") == "7":
            continue
        t = e.get("tags", {})
        if not (t.get("amenity") or t.get("shop")):
            continue
        name = t.get("name:el") or t.get("name") or t.get("brand")
        if not name:
            skipped_noname += 1
            continue
        if "lat" in e:
            lat, lon = e["lat"], e["lon"]
        elif "center" in e:
            lat, lon = e["center"]["lat"], e["center"]["lon"]
        else:
            continue
        pid = e["type"][0] + str(e["id"])
        if pid in seen:
            continue
        seen.add(pid)
        dimos = find_dimos(lon, lat) if dimoi else None
        if dimoi and dimos not in INCLUDE:
            skipped_area += 1
            continue
        cat, sub = classify(t)
        p = {
            "id": pid,
            "name": name.strip(),
            "name_en": t.get("name:en") if t.get("name:en") and t.get("name:en") != name else None,
            "cat": cat,
            "sub": sub,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "dimos": dimos,
            "address": address(t),
            "phone": first(t, "contact:phone", "phone", "contact:mobile", "mobile"),
            "email": first(t, "contact:email", "email"),
            "website": clean_url(first(t, "contact:website", "website", "url")),
            "instagram": social(t, "instagram", "https://www.instagram.com/"),
            "facebook": social(t, "facebook", "https://www.facebook.com/"),
            "tiktok": social(t, "tiktok", "https://www.tiktok.com/@"),
            "hours": t.get("opening_hours"),
            "cuisine": t.get("cuisine"),
            "brand": t.get("brand"),
            "outdoor": yes(t, "outdoor_seating"),
            "takeaway": yes(t, "takeaway"),
            "delivery": yes(t, "delivery"),
            "wheelchair": t.get("wheelchair"),
            "smoking": t.get("smoking"),
            "wifi": True if t.get("internet_access") in ("wlan", "yes", "wifi") else None,
            "cards": True if t.get("payment:cards") == "yes" or t.get("payment:credit_cards") == "yes" else None,
            "vegetarian": t.get("diet:vegetarian"),
            "vegan": t.get("diet:vegan"),
            "wikidata": t.get("wikidata") or t.get("brand:wikidata"),
            "src": ["osm"],
            "osm": "https://www.openstreetmap.org/%s/%s" % (e["type"], e["id"]),
        }
        if pid in gemi:
            p["gemi"] = gemi[pid]
            p["src"].append("gemi")
        if pid in overrides:
            p.update(overrides[pid])
            p["src"].append("manual")
        places.append({k: v for k, v in p.items() if v not in (None, "", [])})

    # Overture Maps Places (Meta/Foursquare/Microsoft): εμπλουτισμός + νέα σημεία
    from merge_overture import merge
    if dimoi:
        places = merge(places, OVT, classify, find_dimos, INCLUDE)
        for p in places:
            if p["id"].startswith("v") and p["id"] in overrides:
                p.update(overrides[p["id"]])
                p["src"].append("manual")
        places = [p for p in places if not p.get("hidden")]

    # χειροκίνητες προσθήκες (ids που ξεκινούν με "x")
    for pid, ov in overrides.items():
        if pid.startswith("x") and pid not in seen:
            ov = dict(ov, id=pid, src=["manual"])
            places.append(ov)

    if not places:
        sys.exit("\nΔεν βρέθηκε κανένα κατάστημα — το places.json ΔΕΝ άλλαξε. "
                 "Κατέβασε τα δεδομένα με το tools/download_osm.html.")
    places.sort(key=lambda p: (p["cat"], p["sub"], p["name"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = {
        "generated": date.today().isoformat(),
        "osm_timestamp": raw.get("osm3s", {}).get("timestamp_osm_base"),
        "count": len(places),
        "places": places,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    from collections import Counter
    print("Σημεία:", len(places), "| χωρίς όνομα:", skipped_noname, "| εκτός περιοχής:", skipped_area)
    print("Κατηγορίες:", Counter(p["cat"] for p in places))
    print("Υποκατηγορίες:", Counter(p["sub"] for p in places).most_common())
    print("Δήμοι:", Counter(p.get("dimos") for p in places).most_common())
    print("Πηγές:", Counter("+".join(p.get("src", [])) for p in places).most_common())
    for k in ("phone", "website", "instagram", "facebook", "email", "hours", "address"):
        print("  με %-10s %5d" % (k, sum(1 for p in places if p.get(k))))


if __name__ == "__main__":
    main()
