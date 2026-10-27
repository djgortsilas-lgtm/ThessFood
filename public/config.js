/* Ρυθμίσεις εφαρμογής: κατηγορίες, υποκατηγορίες, χρώματα, πηγή δεδομένων. */
window.TF_CONFIG = {
  dataUrl: "data/places.json",
  center: [40.6265, 22.9500],
  zoom: 13,

  // Πλακίδια χάρτη. Προεπιλογή: OpenStreetMap (δωρεάν, χωρίς κλειδί).
  tiles: {
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },

  cats: {
    food:   { label: "Φαγητό", color: "#C8402A",
              glyph: '<path d="M8 3v7a2 2 0 0 0 4 0V3M10 3v18M17 3c-1.7 0-3 2.2-3 5s1.3 4 3 4v9"/>' },
    coffee: { label: "Καφές",  color: "#7B4A26",
              glyph: '<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM16 10h1.5a2.5 2.5 0 0 1 0 5H16M8 3c-.6 1 .6 2 0 3M12 3c-.6 1 .6 2 0 3"/>' },
    drink:  { label: "Ποτό",   color: "#5B3C9E",
              glyph: '<path d="M5 4h14l-7 8zM12 12v8M8 20h8M15 7.5l3-4"/>' },
  },

  // σειρά = σειρά εμφάνισης στα φίλτρα
  subs: {
    taverna:       { cat: "food",   label: "Ταβέρνα" },
    meze:          { cat: "food",   label: "Μεζεδοπωλείο / Τσιπουράδικο" },
    fish:          { cat: "food",   label: "Ψαροταβέρνα / Ουζερί" },
    grill:         { cat: "food",   label: "Ψητοπωλείο" },
    chicken:       { cat: "food",   label: "Κοτόπουλα" },
    mageireio:     { cat: "food",   label: "Μαγειρείο" },
    patsas:        { cat: "food",   label: "Πατσατζίδικο" },
    souvlaki:      { cat: "food",   label: "Γυράδικο / Σουβλατζίδικο" },
    restaurant:    { cat: "food",   label: "Εστιατόριο" },
    pizza:         { cat: "food",   label: "Πιτσαρία" },
    italian:       { cat: "food",   label: "Ιταλικό" },
    asian:         { cat: "food",   label: "Ασιατικό / Sushi" },
    international: { cat: "food",   label: "Έθνικ / Διεθνές" },
    burger:        { cat: "food",   label: "Burger" },
    sandwich:      { cat: "food",   label: "Σάντουιτς / Healthy" },
    vegan:         { cat: "food",   label: "Vegan / Χορτοφαγικό" },
    crepe:         { cat: "food",   label: "Κρεπερί" },
    fast_food:     { cat: "food",   label: "Fast food" },
    food_court:    { cat: "food",   label: "Food court" },
    bougatsa:      { cat: "food",   label: "Μπουγατσατζίδικο" },
    bakery:        { cat: "food",   label: "Φούρνος" },
    pastry:        { cat: "food",   label: "Ζαχαροπλαστείο" },
    ice_cream:     { cat: "food",   label: "Παγωτό" },

    cafe:          { cat: "coffee", label: "Καφετέρια" },
    takeaway:      { cat: "coffee", label: "Καφές take away" },
    brunch:        { cat: "coffee", label: "Brunch / Bistro" },
    coffee_roaster:{ cat: "coffee", label: "Καφεκοπτείο" },
    bubble_tea:    { cat: "coffee", label: "Bubble tea" },
    juice:         { cat: "coffee", label: "Χυμοί / Smoothies" },

    bar:           { cat: "drink",  label: "Μπαρ" },
    cocktail_bar:  { cat: "drink",  label: "Cocktail bar" },
    wine_bar:      { cat: "drink",  label: "Wine bar" },
    beer_bar:      { cat: "drink",  label: "Μπυραρία" },
    pub:           { cat: "drink",  label: "Pub" },
    club:          { cat: "drink",  label: "Club" },
  },

  cuisine: {
    greek: "Ελληνική", regional: "Τοπική", mediterranean: "Μεσογειακή", italian: "Ιταλική", pizza: "Πίτσα",
    burger: "Burger", kebab: "Κεμπάπ", souvlaki: "Σουβλάκι", gyros: "Γύρος", fish: "Ψάρι", seafood: "Θαλασσινά",
    sushi: "Sushi", japanese: "Ιαπωνική", chinese: "Κινέζικη", asian: "Ασιατική", thai: "Ταϊλανδέζικη",
    indian: "Ινδική", mexican: "Μεξικάνικη", coffee_shop: "Καφές", crepe: "Κρέπα", sandwich: "Σάντουιτς",
    ice_cream: "Παγωτό", vegan: "Vegan", vegetarian: "Χορτοφαγική", steak_house: "Steak house",
    grill: "Ψητά", bougatsa: "Μπουγάτσα", breakfast: "Πρωινό", brunch: "Brunch", international: "Διεθνής",
    lebanese: "Λιβανέζικη", middle_eastern: "Μέσης Ανατολής", turkish: "Τουρκική", french: "Γαλλική",
    spanish: "Ισπανική", american: "Αμερικάνικη", chicken: "Κοτόπουλο", pasta: "Ζυμαρικά", salad: "Σαλάτες",
    meze: "Μεζέδες", bubble_tea: "Bubble tea", donut: "Ντόνατς", cake: "Γλυκά", pastry: "Γλυκά", bakery: "Αρτοποιία",
  },

  /* Για Firestore αργότερα (προαιρετικό). Αν μείνει null, τα δεδομένα διαβάζονται από το dataUrl. */
  firebase: null,
};
