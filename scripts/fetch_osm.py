# -*- coding: utf-8 -*-
"""
Λήψη δεδομένων OpenStreetMap (όρια δήμων + καταστήματα) από Overpass -> data/raw/osm.json
Ίδια ερωτήματα με το tools/download_osm.html, αλλά χωρίς browser (για GitHub Actions / γραμμή εντολών).
Χρήση:  python scripts/fetch_osm.py
"""
import json, os, sys, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "osm.json")
SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
BBOX = "40.50,22.75,40.75,23.15"
QUERIES = {
    "όρια δήμων": '[out:json][timeout:180];rel["boundary"="administrative"]["admin_level"="7"](%s);out geom;' % BBOX,
    "καταστήματα": '[out:json][timeout:180];(nwr["amenity"~"^(restaurant|cafe|bar|pub|fast_food|ice_cream|'
                   'biergarten|food_court|nightclub)$"](%s);nwr["shop"~"^(bakery|pastry|coffee|confectionery)$"](%s););'
                   'out center tags;' % (BBOX, BBOX),
}


def run(label, q):
    for rnd in range(1, 4):
        for s in SERVERS:
            print("%s: %s (γύρος %d)" % (label, urllib.parse.urlparse(s).netloc, rnd), flush=True)
            try:
                req = urllib.request.Request(s, data=urllib.parse.urlencode({"data": q}).encode(),
                                             headers={"User-Agent": "thess-food/1.0 (+github pages map)"})
                with urllib.request.urlopen(req, timeout=240) as r:
                    j = json.loads(r.read().decode("utf-8"))
                if j.get("elements"):
                    print("  OK", len(j["elements"]), "στοιχεία", flush=True)
                    return j
                print("  0 στοιχεία", j.get("remark", ""), flush=True)
            except Exception as e:
                print("  σφάλμα:", e, flush=True)
            time.sleep(5)
        time.sleep(30)
    sys.exit(label + ": κανένας server δεν έδωσε δεδομένα")


def main():
    parts = [run(l, q) for l, q in QUERIES.items()]
    n_shops = len(parts[1]["elements"])
    if n_shops < 1500:   # προστασία: μην αντικαταστήσεις καλά δεδομένα με μισά
        sys.exit("Ύποπτα λίγα καταστήματα (%d) — δεν αποθηκεύτηκε." % n_shops)
    out = {"version": 0.6, "osm3s": parts[1].get("osm3s"), "elements": parts[0]["elements"] + parts[1]["elements"]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("Αποθηκεύτηκαν", len(out["elements"]), "στοιχεία ->", OUT)


if __name__ == "__main__":
    main()
