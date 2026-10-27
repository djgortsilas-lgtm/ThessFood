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
