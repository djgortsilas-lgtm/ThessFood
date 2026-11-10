# -*- coding: utf-8 -*-
"""
Λήψη από το ΓΕΜΗ (Open Data API) όλων των ΕΝΕΡΓΩΝ επιχειρήσεων εστίασης
(ΚΑΔ 56.xx, εκτός catering 56.2x) της Π.Ε. Θεσσαλονίκης.

Χρήση:  python scripts/fetch_gemi.py
Κλειδί: μεταβλητή περιβάλλοντος GEMI_API_KEY ή αρχείο data/gemi_key.txt
Έξοδος: data/ext/gemi_raw.json
Όριο API: 8 κλήσεις / λεπτό -> το script περιμένει μόνο του.
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "ext", "gemi_raw.json")
BASE = "https://opendata-api.businessportal.gr/api/opendata/v1"
PREFECTURE = "19"      # ΘΕΣΣΑΛΟΝΙΚΗΣ
STATUS_ACTIVE = "3"    # Ενεργή
PAGE = 200


def api_key():
    k = os.environ.get("GEMI_API_KEY")
    fn = os.path.join(ROOT, "data", "gemi_key.txt")
    if not k and os.path.exists(fn):
        k = open(fn, encoding="utf-8").read().strip()
    if not k:
        sys.exit("Λείπει το κλειδί ΓΕΜΗ (data/gemi_key.txt ή GEMI_API_KEY).")
    return k


KEY = api_key()
_last = [0.0]


def get(path, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(8):
        wait = 7.8 - (time.time() - _last[0])          # <= 8 κλήσεις/λεπτό
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, headers={"api_key": KEY, "Accept": "application/json",
                                                   "User-Agent": "thess-food/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                reset = int(e.headers.get("RateLimit-Reset") or 60)
                print("  όριο κλήσεων — αναμονή %ss" % reset, flush=True)
                time.sleep(reset + 1)
                continue
            if e.code >= 500:
                time.sleep(15); continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(15)
    sys.exit("Αποτυχία κλήσης: " + url)


def main():
    print("Λήψη λίστας ΚΑΔ...", flush=True)
    acts = get("/metadata/activities")
    codes = sorted({a["id"] for a in acts
                    if a["id"].startswith("56") and not a["id"].startswith("562")})
    print("ΚΑΔ εστίασης:", len(codes), flush=True)

    base = {"prefectures": PREFECTURE, "statuses": STATUS_ACTIVE,
            "activities": ",".join(codes), "resultsSize": PAGE}
    out, offset, total = {}, 0, None
    while total is None or offset < total:
        j = get("/companies", dict(base, resultsOffset=offset))
        total = j["searchMetadata"]["totalCount"]
        res = j.get("searchResults") or []
        for r in res:
            out[r["arGemi"]] = r
        print("  %5d / %d" % (min(offset + PAGE, total), total), flush=True)
        if not res:
            break
        offset += PAGE

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"fetched": time.strftime("%Y-%m-%d"), "count": len(out),
                   "companies": list(out.values())}, f, ensure_ascii=False)
    print("Αποθηκεύτηκαν", len(out), "επιχειρήσεις ->", OUT)


if __name__ == "__main__":
    main()
