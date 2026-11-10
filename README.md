# Πού πάμε; — Χάρτης εστίασης Θεσσαλονίκης

Χάρτης με καταστήματα εστίασης, καφέ και μπαρ στη Θεσσαλονίκη και στους γύρω δήμους.
Τρεις βασικές κατηγορίες (Φαγητό, Καφές, Ποτό) με ~30 υποκατηγορίες (ταβέρνα, μεζεδοπωλείο,
γυράδικο, μπουγατσατζίδικο, καφές take away, cocktail bar κ.λπ.).

## Δομή

```
thess-food/
  public/               ← ό,τι ανεβαίνει στο Firebase Hosting
    index.html, style.css, app.js
    config.js           ← κατηγορίες, υποκατηγορίες, χρώματα
    hours.js            ← ανάγνωση ωραρίου (για το «Ανοιχτά τώρα»)
    vendor/             ← Leaflet + MarkerCluster (τοπικά, χωρίς CDN)
    data/places.json    ← τα δεδομένα της εφαρμογής (παράγονται από το script)
  scripts/build_data.py ← μετατρέπει τα ακατέργαστα δεδομένα σε places.json
  data/
    overpass_query.txt  ← το ερώτημα για το OpenStreetMap
    raw/osm.json        ← τα ακατέργαστα δεδομένα OSM (από overpass-turbo)
    overrides.json      ← (προαιρετικό) δικές σου διορθώσεις / προσθήκες
  firebase.json, .firebaserc
```

## Ενημέρωση δεδομένων

1. Στο https://overpass-turbo.eu επικόλλησε το `data/overpass_query.txt`, Εκτέλεση,
   Εξαγωγή → raw OSM data → αποθήκευση ως `data/raw/osm.json`.
2. `python scripts/build_data.py`
3. Το script τυπώνει πόσα σημεία βγήκαν ανά κατηγορία, δήμο και πόσα έχουν τηλέφωνο, site, Instagram.

### Δικές σου διορθώσεις (overrides.json)

```json
{
  "n123456789": { "sub": "meze", "instagram": "https://www.instagram.com/..." },
  "x001": { "name": "Νέο μαγαζί", "cat": "coffee", "sub": "takeaway", "lat": 40.63, "lon": 22.94, "dimos": "Θεσσαλονίκης" }
}
```
Τα id που ξεκινούν από `x` είναι νέα σημεία που δεν υπάρχουν στο OSM.

## Τοπική δοκιμή

```
cd public
python -m http.server 8000
```
και άνοιγμα του http://localhost:8000 (με διπλό κλικ στο index.html δεν φορτώνουν τα δεδομένα).

## Ανέβασμα στο Firebase

1. Δημιουργία project στο https://console.firebase.google.com
2. `npm install -g firebase-tools` και `firebase login`
3. Στο `.firebaserc` βάλε το ID του project
4. `firebase deploy --only hosting`

Τα δεδομένα σερβίρονται ως στατικό αρχείο (`places.json`) από το Hosting: γρήγορο, δωρεάν και χωρίς όρια
αναγνώσεων. Το Firestore μπαίνει αργότερα, αν χρειαστεί σελίδα διαχείρισης ή φόρμα «πρότεινε μαγαζί».

## Πηγές

- **OpenStreetMap** (ODbL): θέση, όνομα, είδος, ωράριο, τηλέφωνο, site, social, κουζίνα, παροχές.
  Η αναφορά «© OpenStreetMap contributors» πρέπει να μένει ορατή.
- **ΓΕΜΗ Open Data** (ODC-BY): επωνυμία, αρ. ΓΕΜΗ, κατάσταση, ΚΑΔ. Χρειάζεται προσωπικό api_key
  (αίτημα στο https://opendata.businessportal.gr/register). Αναζήτηση ανά ΚΑΔ 56.10 / 56.30 και δήμο.
- **Instagram/Facebook**: οι σύνδεσμοι από το OSM· για όσα δεν έχουν, η καρτέλα δίνει κουμπί αναζήτησης.


## Overture Maps (session 2, 27/10/2026)
Δεύτερη πηγή, ανοιχτή (CDLA-Permissive-2.0): Overture Maps Places — κυρίως σελίδες Facebook/Meta, λίγα Foursquare/Microsoft.
1. `python scripts/fetch_overture.py` → `data/ext/overture.json` (όλα τα places του bbox, ~30 MB, θέλει `pip install duckdb`).
2. `python scripts/build_data.py` → συγχώνευση με OSM μέσα από `scripts/merge_overture.py`:
   - ταίριασμα OSM↔Overture: παρόμοιο όνομα (μεταγραφή ελληνικά→λατινικά) σε ≤80 μ., ή ίδιο όνομα σε ≤200 μ. → συμπληρώνει τηλ./site/FB/IG/e-mail/διεύθυνση στο σημείο OSM.
   - τα υπόλοιπα μπαίνουν ως νέα σημεία με id `v…` (αν confidence ≥ 0.6).
   - για να κρύψεις ένα λάθος/κλειστό σημείο: στο `data/overrides.json` → `{"v...": {"hidden": true}}`.
Το `data/places_osm_only_backup.json` είναι το places.json πριν το Overture.

## Αγαπημένα & GPS
- Αγαπημένα: καρδιά στη λίστα και στην καρτέλα, φίλτρο «♥ Αγαπημένα». Αποθήκευση στο `localStorage` (κλειδί `tf_favs_v1`), μόνο στη συσκευή.
- GPS: κουμπί κάτω από το zoom. 1ο πάτημα: εντοπισμός + ακολούθηση· αν σύρεις τον χάρτη, πάτημα = ξανακεντράρισμα· πάτημα ενώ ακολουθεί = σβήσιμο. Θέλει https (Firebase OK) ή localhost.


## ΓΕΜΗ (session 3, 09/11/2026)
Κλειδί στο `data/gemi_key.txt` (ΔΕΝ ανεβαίνει στο Firebase — μόνο ο φάκελος public/). Όριο API: 8 κλήσεις/λεπτό.
Όλα μαζί: **gemi_update.bat** (λήψη → αντιστοίχιση → build). Ή βήμα-βήμα:
1. `python scripts/fetch_gemi.py` → `data/ext/gemi_raw.json`: όλες οι ΕΝΕΡΓΕΣ επιχειρήσεις Π.Ε. Θεσσαλονίκης με ΚΑΔ 56.xx (εκτός catering 56.2x). ~9.600 εγγραφές, ~7 λεπτά.
2. `python scripts/enrich_gemi.py` → `data/gemi.json` (id σημείου → στοιχεία) + `data/ext/gemi_unmatched.csv` (ΓΕΜΗ χωρίς σημείο).
   Κανόνες: ίδιο τηλέφωνο → ίδιο e-mail → όνομα/διακριτικός τίτλος ≥0.85 + ίδιος δήμος + ίδια οδός/ΤΚ → όνομα ≥0.95 μοναδικό στον δήμο.
   Τηλέφωνο/e-mail που μοιράζονται >3 σημεία (αλυσίδες) αγνοούνται. Αν η κύρια δραστηριότητα δεν είναι εστίαση/τρόφιμα, θέλει και ομοιότητα ονόματος.
   Γενικά ονόματα (π.χ. «Θεσσαλονίκη», «Ουζερί») αντιστοιχίζονται μόνο με ίδια οδό.
3. `python scripts/build_data.py` → καρτέλα «Στοιχεία ΓΕΜΗ» στο σημείο + συμπλήρωση τηλ./e-mail/site ΜΟΝΟ όπου λείπουν.
Ιδιωτικότητα: στον χάρτη δεν περνούν ονόματα προσώπων ούτε ΑΦΜ· σε ατομικές επιχειρήσεις δεν φαίνεται η επωνυμία (ονοματεπώνυμο).
Αντίγραφο πριν το ΓΕΜΗ: `data/places_before_gemi_backup.json`.


## GitHub Pages + εβδομαδιαία αυτόματη ενημέρωση
Workflow: `.github/workflows/update-and-deploy.yml`
- Κάθε Κυριακή ~04:20 (ώρα Ελλάδας): fetch_osm.py → fetch_overture.py → fetch_gemi.py → build → enrich_gemi.py → build → commit `public/data/places.json` + `data/gemi.json` → ανέβασμα του φακέλου `public/` στο Pages.
- Χειροκίνητα: GitHub → Actions → «Ενημέρωση & ανέβασμα χάρτη» → Run workflow.
- Push στο main: ανεβαίνει η εφαρμογή χωρίς νέα λήψη.
- Αν αποτύχει OSM/Overture: η σελίδα μένει ως είχε. Αν αποτύχει μόνο το ΓΕΜΗ: κρατιέται το προηγούμενο `data/gemi.json`.
- Το κλειδί ΓΕΜΗ είναι GitHub Secret με όνομα `GEMI_API_KEY` (Settings → Secrets and variables → Actions).
- `scripts/fetch_osm.py` = ό,τι κάνει το `tools/download_osm.html`, χωρίς browser.
- Πριν δουλέψεις τοπικά: `git pull` (το bot γράφει νέα δεδομένα κάθε εβδομάδα).
