# -*- coding: utf-8 -*-
"""
Αντιστοίχιση επιχειρήσεων ΓΕΜΗ (data/ext/gemi_raw.json, από fetch_gemi.py)
με τα σημεία του χάρτη (public/data/places.json).

Χρήση:  python scripts/enrich_gemi.py      (μετά: python scripts/build_data.py)
Έξοδος: data/gemi.json               -> { id σημείου: στοιχεία ΓΕΜΗ }
        data/ext/gemi_unmatched.csv  -> επιχειρήσεις ΓΕΜΗ χωρίς σημείο (για έλεγχο / μελλοντική προσθήκη)

Κανόνες αντιστοίχισης (με σειρά ισχύος):
  1. ίδιο τηλέφωνο           (το τηλέφωνο να μην το μοιράζονται > 3 σημεία, π.χ. αλυσίδες)
  2. ίδιο e-mail             (ίδιος περιορισμός)
  3. όνομα/διακριτικός τίτλος ≥ 0.85 + ίδιος δήμος + ίδια οδός ή Τ.Κ.
  4. όνομα ≥ 0.95, ίδιος δήμος, μοναδικό όνομα στον δήμο
Προσωπικά στοιχεία (ονόματα προσώπων, ΑΦΜ) ΔΕΝ περνούν στον χάρτη· σε ατομικές
επιχειρήσεις δεν εμφανίζεται η επωνυμία (είναι ονοματεπώνυμο).
"""
import csv, json, os, re, sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_overture import key, similar, _plain  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "ext", "gemi_raw.json")
PLACES = os.path.join(ROOT, "public", "data", "places.json")
OUT = os.path.join(ROOT, "data", "gemi.json")
UNM = os.path.join(ROOT, "data", "ext", "gemi_unmatched.csv")
PUBLIC_URL = "https://publicity.businessportal.gr/company/%s"

LEGAL = re.compile(r"\b(μονοπροσωπη|ιδιωτικη|κεφαλαιουχικη|εταιρεια|εταιρια|περιορισμενησ|ευθυνησ|ανωνυμη|"
                   r"ομορρυθμη|ετερορρυθμη|αστικη|κοινωνια|ικε|επε|οε|εε|αε|ι\.κ\.ε|ε\.π\.ε|ο\.ε|ε\.ε|α\.ε|"
                   r"και σια|μ\.ικε|ike|epe|oe|ee|ae|single member|private company|limited|company|partnership)\b\.?")


def phone_keys(s):
    out = set()
    for part in re.split(r"[;,/]", s or ""):
        d = re.sub(r"\D", "", part)
        if d.startswith("0030"):
            d = d[4:]
        elif d.startswith("30") and len(d) == 12:
            d = d[2:]
        if len(d) == 10:
            out.add(d)
    return out


def email_key(s):
    s = (s or "").strip().lower()
    return s if "@" in s else None


def dimos_key(s):
    s = _plain(s or "").split("/")[0]
    return re.sub(r"[^a-zα-ω]", "", s.replace("ς", "σ"))


def street_toks(s):
    """Σημαντικές λέξεις οδού (≥4 γράμματα) σε μορφή key()."""
    return {t for t in key(re.sub(r"\d+", " ", s or "")).split() if len(t) >= 4}


def strip_legal(n):
    s = _plain(n).replace("ς", "σ")
    s = re.sub(r"\(.*?\)", " ", s)
    s = LEGAL.sub(" ", s)
    return re.sub(r"[-–\s]+", " ", s).strip(" -.")


def sentence(s):
    s = (s or "").strip()
    return s[:1] + s[1:].lower() if s else s


def main_act(c):
    cur = [a for a in c.get("activities") or [] if not a.get("dtTo")]
    main = [a for a in cur if a.get("type") == "Κύρια"] or cur
    return main[0]["activity"] if main else {}


def main_activity(c):
    return main_act(c).get("descr")


# κύρια δραστηριότητα που ταιριάζει με κατάστημα εστίασης/καφέ/γλυκών/αρτοποιείου
FOOD_KAD = ("56", "1071", "1072", "1052", "1082", "4711", "4721", "4722", "4724", "4725", "4729")


def food_main(c):
    return main_act(c).get("id", "").startswith(FOOD_KAD)


# ονόματα που είναι γενικά (περιοχή/είδος) -> δεν αρκούν μόνα τους για αντιστοίχιση
GENERIC = set(key("θεσσαλονικη thessaloniki salonica καλαμαρια ουζερι μεζεδοπωλειο τσιπουραδικο καφενειο "
                  "καφενες ψητοπωλειο σουβλατζιδικο σουβλακι γυρος πιτσαρια pizzeria pizza ζαχαροπλαστειο "
                  "φουρνος αρτοποιειο grill house snack καντινα κυλικειο μπουγατσα γλυκα espresso club "
                  "lounge food street city center central port λιμανι πλατεια παραλια εστια").split())


def generic_name(n):
    toks = key(n).split()
    return not toks or all(t in GENERIC for t in toks)


# μακροσκελή προθέματα ΚΑΔ -> πιο σύντομη περιγραφή
KAD_PREFIX = [
    "ΥΠΗΡΕΣΙΕΣ ΠΑΡΟΧΗΣ ΓΕΥΜΑΤΩΝ ΚΑΙ ΠΟΤΩΝ ΑΠΟ ", "ΥΠΗΡΕΣΙΕΣ ΠΑΡΟΧΗΣ ΓΕΥΜΑΤΩΝ ΑΠΟ ",
    "ΥΠΗΡΕΣΙΕΣ ΠΑΡΟΧΗΣ ΓΛΥΚΩΝ, ΠΑΓΩΤΩΝ ΚΛΠ ΑΠΟ ", "ΥΠΗΡΕΣΙΕΣ ΠΟΥ ΠΑΡΕΧΟΝΤΑΙ ΑΠΟ ", "ΥΠΗΡΕΣΙΕΣ ",
]


def kad_text(c):
    s = (main_activity(c) or "").strip()
    for pre in KAD_PREFIX:
        if s.startswith(pre):
            s = s[len(pre):]
            break
    s = re.sub(r"\s*[\[(]ΠΟΥ (ΔΕΝ )?ΥΠΑΓΕΤΑΙ.*?[\])]", "", s)   # παραπομπές σε ΦΕΚ
    return s or None


def names_of(c):
    """Ονόματα για σύγκριση: διακριτικοί τίτλοι + επωνυμία (χωρίς νομική μορφή)."""
    ns = list(c.get("coTitlesEl") or []) + list(c.get("coTitlesEn") or [])
    if not is_sole(c):
        ns += [strip_legal(c.get("coNameEl") or "")] + [strip_legal(x) for x in c.get("coNamesEn") or []]
    return [n for n in ns if n and len(key(n)) >= 3]


def is_sole(c):
    lt = _plain((c.get("legalType") or {}).get("descr", ""))
    return "ατομ" in lt


def info(c, how):
    founded = c.get("incorporationDate") or ""
    g = {
        "title": (c.get("coTitlesEl") or c.get("coTitlesEn") or [None])[0],
        "legal_name": None if is_sole(c) else c.get("coNameEl"),
        "legal_form": "Ατομική επιχείρηση" if is_sole(c) else (c.get("legalType") or {}).get("descr"),
        "gemi_no": c.get("arGemi"),
        "status": (c.get("status") or {}).get("descr"),
        "founded": founded[:4] or None,
        "kad": kad_text(c),
        "url": PUBLIC_URL % c.get("arGemi"),
        "match": how,
        # για συμπλήρωση μόνο όπου λείπουν (το κάνει το build_data.py)
        "_phone": c.get("phone"),
        "_email": (c.get("email") or "").strip().lower() or None,
        "_website": c.get("url"),
    }
    return {k: v for k, v in g.items() if v}


def main():
    if not os.path.exists(RAW):
        sys.exit("Λείπει το " + RAW + " — τρέξε πρώτα: python scripts/fetch_gemi.py")
    comps = json.load(open(RAW, encoding="utf-8"))["companies"]
    places = json.load(open(PLACES, encoding="utf-8"))["places"]
    print("ΓΕΜΗ:", len(comps), "| σημεία:", len(places))

    by_phone, by_mail, by_dimos = defaultdict(list), defaultdict(list), defaultdict(list)
    for p in places:
        for k in phone_keys(p.get("phone")):
            by_phone[k].append(p)
        e = email_key(p.get("email"))
        if e:
            by_mail[e].append(p)
        for t in set(key(p["name"]).split()):
            if len(t) >= 3:
                by_dimos[(dimos_key(p.get("dimos")), t[:4])].append(p)
    name_count = Counter((dimos_key(p.get("dimos")), key(p["name"])) for p in places)

    best = {}   # place id -> (score, company, how)
    unmatched = []
    stats = Counter()
    for c in comps:
        cands = []   # (score, place, how)
        names = names_of(c)
        food = food_main(c)
        for k in phone_keys(c.get("phone")):
            ps = by_phone.get(k, [])
            if 0 < len(ps) <= 3:
                for p in ps:
                    s = max([similar(n, p["name"]) for n in names] or [0])
                    if food or s >= 0.5:      # μη-εστίαση ως κύρια: θέλει και όνομα
                        cands.append((3 + s, p, "phone"))
        e = email_key(c.get("email"))
        if e and 0 < len(by_mail.get(e, [])) <= 3:
            for p in by_mail[e]:
                s = max([similar(n, p["name"]) for n in names] or [0])
                if food or s >= 0.5:
                    cands.append((2.5 + s, p, "email"))
        if not cands and names:
            dk = dimos_key((c.get("municipality") or {}).get("descr"))
            st = street_toks(c.get("street"))
            zc = (c.get("zipCode") or "").replace(" ", "")
            pool = {}
            for n in names:
                for t in key(n).split():
                    if len(t) >= 3:
                        for p in by_dimos.get((dk, t[:4]), []):
                            pool[p["id"]] = p
            for p in pool.values():
                s = max(similar(n, p["name"]) for n in names)
                if s < 0.85:
                    continue
                addr = p.get("address") or ""
                same_st = bool(st & street_toks(addr))
                same_zip = bool(zc) and zc in addr.replace(" ", "")
                if generic_name(p["name"]):
                    if same_st and s >= 0.95:     # γενικό όνομα: μόνο με ίδια οδό
                        cands.append((1 + s, p, "name+address"))
                    continue
                if same_st or same_zip:
                    cands.append((1 + s + (0.2 if same_st else 0), p, "name+address"))
                elif s >= 0.95 and name_count[(dk, key(p["name"]))] == 1 and len(key(p["name"])) >= 7:
                    cands.append((s, p, "name"))
        if not cands:
            unmatched.append(c)
            continue
        sc, p, how = max(cands, key=lambda x: x[0])
        stats[how] += 1
        if p["id"] not in best or best[p["id"]][0] < sc:
            best[p["id"]] = (sc, c, how)

    out = {pid: info(c, how) for pid, (sc, c, how) in best.items()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    with open(UNM, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ΑρΓΕΜΗ", "Διακριτικός τίτλος", "Επωνυμία", "Οδός", "Αριθμός", "ΤΚ", "Δήμος", "Τηλέφωνο",
                    "E-mail", "Site", "Κύρια δραστηριότητα", "Σύσταση"])
        for c in unmatched:
            w.writerow([c.get("arGemi"), " | ".join(c.get("coTitlesEl") or []), c.get("coNameEl"), c.get("street"),
                        c.get("streetNumber"), c.get("zipCode"), (c.get("municipality") or {}).get("descr"),
                        c.get("phone"), c.get("email"), c.get("url"), main_activity(c), c.get("incorporationDate")])

    print("Αντιστοιχίσεις ανά κανόνα:", dict(stats))
    print("Σημεία με στοιχεία ΓΕΜΗ:", len(out), "| επιχειρήσεις χωρίς σημείο:", len(unmatched))
    print("->", OUT)
    print("->", UNM)


if __name__ == "__main__":
    main()
