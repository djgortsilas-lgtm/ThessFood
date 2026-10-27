(function () {
  const C = window.TF_CONFIG;
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const norm = s => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ς/g, "σ");

  const state = { cats: new Set(["food", "coffee", "drink"]), subs: new Set(), q: "", dimos: "", openNow: false, social: false, me: null, sel: null };
  let ALL = [], shown = [], markers = new Map(), selMarker = null, listLimit = 80;

  // ---------------------------------------------------------------- αγαπημένα (localStorage της συσκευής)
  const FAV_KEY = "tf_favs_v1";
  const Fav = {
    set: (() => { try { return new Set(JSON.parse(localStorage.getItem(FAV_KEY) || "[]")); } catch (e) { return new Set(); } })(),
    has(id) { return this.set.has(id); },
    toggle(id) {
      this.set.has(id) ? this.set.delete(id) : this.set.add(id);
      try { localStorage.setItem(FAV_KEY, JSON.stringify([...this.set])); } catch (e) {}
      this.sync();
      return this.set.has(id);
    },
    sync() {
      const n = ALL.length ? ALL.filter(p => this.set.has(p.id)).length : this.set.size;
      $("#favN").textContent = n;
    },
  };
  const HEART = '<path d="M12 20s-7-4.4-9-9.2C1.6 7.4 3.8 4 7.2 4c2 0 3.4 1.1 4.8 2.9C13.4 5.1 14.8 4 16.8 4c3.4 0 5.6 3.4 4.2 6.8C19 15.6 12 20 12 20z"/>';

  // ---------------------------------------------------------------- χάρτης
  const map = L.map("map", { zoomControl: false, preferCanvas: false }).setView(C.center, C.zoom);
  L.control.zoom({ position: "topright" }).addTo(map);
  // Πλακίδια χάρτη (αλλάζουν από το config.js -> tiles)
  const T = C.tiles || { url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' };
  L.tileLayer(T.url, { maxZoom: T.maxZoom || 19, subdomains: T.subdomains || "abc", attribution: T.attribution }).addTo(map);

  const cluster = L.markerClusterGroup({
    showCoverageOnHover: false, maxClusterRadius: 48, spiderfyOnMaxZoom: true, disableClusteringAtZoom: 18,
    iconCreateFunction(cl) {
      const n = { food: 0, coffee: 0, drink: 0 };
      cl.getAllChildMarkers().forEach(m => n[m.options.cat]++);
      const tot = cl.getChildCount();
      let acc = 0, stops = [];
      for (const k of ["food", "coffee", "drink"]) {
        const a = acc / tot * 360, b = (acc + n[k]) / tot * 360;
        if (n[k]) stops.push(`${C.cats[k].color} ${a}deg ${b}deg`);
        acc += n[k];
      }
      const size = tot < 10 ? 32 : tot < 100 ? 40 : tot < 1000 ? 48 : 56;
      return L.divIcon({
        className: "clu", iconSize: [size, size],
        html: `<div style="background:conic-gradient(${stops.join(",")})"><span>${tot}</span></div>`,
      });
    },
  });
  map.addLayer(cluster);

  const iconCache = {};
  function pinIcon(cat, sel) {
    const key = cat + (sel ? 1 : 0);
    if (iconCache[key]) return iconCache[key];
    const c = C.cats[cat];
    const svg = `<svg width="30" height="40" viewBox="0 0 30 40"><path d="M15 1C7.3 1 1 7 1 14.6 1 25 15 39 15 39s14-14 14-24.4C29 7 22.7 1 15 1z" fill="${c.color}" stroke="#fff" stroke-width="1.5"/>
      <g transform="translate(6.5 6) scale(.71)" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${c.glyph}</g></svg>`;
    return (iconCache[key] = L.divIcon({ className: "pin" + (sel ? " sel" : ""), html: svg, iconSize: [30, 40], iconAnchor: [15, 39], popupAnchor: [0, -34] }));
  }

  // ---------------------------------------------------------------- εικονίδια κατηγοριών στο πάνελ
  document.querySelectorAll(".cat").forEach(b => {
    b.querySelector(".cat-ico").innerHTML = `<svg viewBox="0 0 24 24">${C.cats[b.dataset.cat].glyph}</svg>`;
    b.addEventListener("click", () => {
      const k = b.dataset.cat;
      // πρώτο κλικ όταν είναι όλες ενεργές: απομονώνει τη μία
      if (state.cats.size === 3) state.cats = new Set([k]);
      else if (state.cats.has(k)) { state.cats.delete(k); if (!state.cats.size) state.cats = new Set(["food", "coffee", "drink"]); }
      else state.cats.add(k);
      for (const s of [...state.subs]) if (!state.cats.has(C.subs[s].cat)) state.subs.delete(s);
      syncCats(); renderSubs(); apply();
    });
  });
  function syncCats() {
    document.querySelectorAll(".cat").forEach(b => {
      const on = state.cats.has(b.dataset.cat);
      b.classList.toggle("on", on); b.setAttribute("aria-pressed", on);
    });
  }

  // ---------------------------------------------------------------- φόρτωση
  fetch(C.dataUrl).then(r => r.json()).then(d => {
    ALL = d.places.map(p => Object.assign(p, { _q: norm([p.name, p.name_en, p.address, p.cuisine, p.dimos, C.subs[p.sub]?.label, p.brand].join(" ")) }));
    $("#updated").textContent = d.generated ? `Ενημέρωση ${new Date(d.generated).toLocaleDateString("el-GR")}.` : "";
    if (ALL.some(p => p.gemi)) $("#gemiCredit").hidden = false;
    ALL.forEach(p => {
      const m = L.marker([p.lat, p.lon], { icon: pinIcon(p.cat), cat: p.cat, title: p.name, keyboard: false });
      m.on("click", () => select(p.id, false));
      markers.set(p.id, m);
    });
    const dimoi = [...new Set(ALL.map(p => p.dimos).filter(Boolean))].sort((a, b) => a.localeCompare(b, "el"));
    $("#dimos").insertAdjacentHTML("beforeend", dimoi.map(x => `<option value="${esc(x)}">Δήμος ${esc(x)}</option>`).join(""));
    Fav.sync(); renderSubs(); apply();
    const h = new URLSearchParams(location.hash.slice(1)).get("p");
    if (h && markers.has(h)) select(h, true);
  }).catch(err => {
    $("#count").textContent = "Τα δεδομένα δεν φορτώθηκαν. Έλεγξε ότι υπάρχει το αρχείο data/places.json.";
    console.error(err);
  });

  // ---------------------------------------------------------------- φίλτρα
  function base(p, ignoreSub) {
    if (!state.cats.has(p.cat)) return false;
    if (!ignoreSub && state.subs.size && !state.subs.has(p.sub)) return false;
    if (state.dimos && p.dimos !== state.dimos) return false;
    if (state.social && !(p.instagram || p.facebook || p.tiktok)) return false;
    if (state.favOnly && !Fav.has(p.id)) return false;
    if (state.openNow && Hours.isOpen(p.hours) !== true) return false;
    if (state.q) { for (const w of norm(state.q).split(/\s+/)) if (w && !p._q.includes(w)) return false; }
    return true;
  }

  function renderSubs() {
    const counts = {};
    ALL.forEach(p => { if (base(p, true)) counts[p.sub] = (counts[p.sub] || 0) + 1; });
    const keys = Object.keys(C.subs).filter(k => state.cats.has(C.subs[k].cat) && (counts[k] || state.subs.has(k)));
    $("#subs").innerHTML = keys.map(k => {
      const s = C.subs[k];
      return `<button class="sub${state.subs.has(k) ? " on" : ""}" data-sub="${k}" style="--sub-c:${C.cats[s.cat].color}" aria-pressed="${state.subs.has(k)}">${esc(s.label)}<i>${counts[k] || 0}</i></button>`;
    }).join("");
  }
  $("#subs").addEventListener("click", e => {
    const b = e.target.closest(".sub"); if (!b) return;
    const k = b.dataset.sub;
    state.subs.has(k) ? state.subs.delete(k) : state.subs.add(k);
    renderSubs(); apply();
  });

  let qt;
  $("#q").addEventListener("input", e => { clearTimeout(qt); qt = setTimeout(() => { state.q = e.target.value.trim(); renderSubs(); apply(); }, 180); });
  $("#dimos").addEventListener("change", e => { state.dimos = e.target.value; renderSubs(); apply(true); });
  $("#openNow").addEventListener("change", e => { state.openNow = e.target.checked; renderSubs(); apply(); });
  $("#withSocial").addEventListener("change", e => { state.social = e.target.checked; renderSubs(); apply(); });
  $("#favOnly").addEventListener("change", e => { state.favOnly = e.target.checked; renderSubs(); apply(state.favOnly); });

  function apply(fit) {
    shown = ALL.filter(p => base(p));
    const n = { food: 0, coffee: 0, drink: 0 };
    // μετρητές ανά κατηγορία, ανεξάρτητα από το ποιες κατηγορίες είναι ενεργές
    ALL.forEach(p => {
      const save = state.cats; state.cats = new Set([p.cat]);
      if (base(p, true)) n[p.cat]++;
      state.cats = save;
    });
    document.querySelectorAll(".cat").forEach(b => b.querySelector(".cat-n").textContent = n[b.dataset.cat].toLocaleString("el-GR"));

    cluster.clearLayers();
    cluster.addLayers(shown.map(p => markers.get(p.id)));
    if (fit && shown.length) map.fitBounds(L.latLngBounds(shown.map(p => [p.lat, p.lon])), { padding: [30, 30], maxZoom: 16 });
    listLimit = 80;
    renderList();
  }

  // ---------------------------------------------------------------- λίστα
  function dist(p) {
    if (!state.me) return null;
    const R = 6371, toR = x => x * Math.PI / 180;
    const dLa = toR(p.lat - state.me[0]), dLo = toR(p.lon - state.me[1]);
    const a = Math.sin(dLa / 2) ** 2 + Math.cos(toR(state.me[0])) * Math.cos(toR(p.lat)) * Math.sin(dLo / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }
  const fmtKm = d => d < 1 ? Math.round(d * 1000 / 10) * 10 + " μ." : d.toFixed(1).replace(".", ",") + " χλμ.";

  function renderList() {
    let arr = shown;
    if (state.me) arr = shown.map(p => [dist(p), p]).sort((a, b) => a[0] - b[0]).map(x => x[1]);
    else if (state.q) arr = [...shown].sort((a, b) => norm(a.name).startsWith(norm(state.q)) ? -1 : norm(b.name).startsWith(norm(state.q)) ? 1 : 0);
    $("#count").textContent = shown.length ? `${shown.length.toLocaleString("el-GR")} μέρη` : "";
    if (!arr.length) {
      $("#list").innerHTML = state.favOnly && !Fav.set.size
        ? `<li class="empty">Δεν έχεις αγαπημένα ακόμα. Άνοιξε ένα μαγαζί και πάτα την καρδιά για να το κρατήσεις εδώ.</li>`
        : `<li class="empty">Δεν βρέθηκε κάτι με αυτά τα φίλτρα. Δοκίμασε άλλη λέξη ή άναψε περισσότερες κατηγορίες.</li>`;
      return;
    }
    const html = arr.slice(0, listLimit).map(p => {
      const o = Hours.isOpen(p.hours);
      const side = state.me ? fmtKm(dist(p)) : o === true ? '<span class="st-open">Ανοιχτά</span>' : o === false ? '<span class="st-closed">Κλειστά</span>' : "";
      return `<li class="item" tabindex="0" data-id="${p.id}">
        <span class="dot" style="background:${C.cats[p.cat].color}"></span>
        <div><div class="item-name">${esc(p.name)}</div>
        <div class="item-meta">${esc(C.subs[p.sub]?.label || "")}${p.address ? ", " + esc(p.address.split(",")[0]) : p.dimos ? ", " + esc(p.dimos) : ""}</div></div>
        <div class="item-side">${side}</div>
        <button class="fav-btn${Fav.has(p.id) ? " on" : ""}" type="button" data-fav="${p.id}" aria-pressed="${Fav.has(p.id)}" aria-label="${Fav.has(p.id) ? "Αφαίρεση από" : "Προσθήκη στα"} αγαπημένα"><svg viewBox="0 0 24 24">${HEART}</svg></button></li>`;
    }).join("");
    $("#list").innerHTML = html + (arr.length > listLimit ? `<li class="more"><button class="link-btn" id="moreBtn">Δείξε άλλα ${Math.min(80, arr.length - listLimit)}</button></li>` : "");
  }
  $("#list").addEventListener("click", e => {
    if (e.target.id === "moreBtn") { listLimit += 80; renderList(); return; }
    const fb = e.target.closest(".fav-btn");
    if (fb) {
      e.stopPropagation();
      Fav.toggle(fb.dataset.fav);
      if (state.favOnly) apply(); else renderList();
      return;
    }
    const li = e.target.closest(".item"); if (li) select(li.dataset.id, true);
  });
  $("#list").addEventListener("keydown", e => { if (e.key === "Enter" && !e.target.closest(".fav-btn")) { const li = e.target.closest(".item"); if (li) select(li.dataset.id, true); } });

  // ---------------------------------------------------------------- λεπτομέρειες
  const ICO = {
    dir: '<path d="M12 2 3 21l9-5 9 5z"/>',
    tel: '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2"/>',
    web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    ig: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6"/>',
    fb: '<path d="M14 8h3V4h-3a4 4 0 0 0-4 4v3H7v4h3v6h4v-6h3l1-4h-4V8"/>',
    gm: '<path d="M12 21s-7-6.3-7-11.5A7 7 0 0 1 19 9.5C19 14.7 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    share: '<path d="M4 12v7h16v-7M12 3v12M7 8l5-5 5 5"/>',
  };
  const btn = (href, ico, label, cls = "") => `<a class="btn ${cls}" href="${esc(href)}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24">${ICO[ico]}</svg>${label}</a>`;
  const WH = { yes: "Πρόσβαση ΑμεΑ", limited: "Μερική πρόσβαση ΑμεΑ", no: "Χωρίς πρόσβαση ΑμεΑ" };

  function select(id, pan) {
    const p = ALL.find(x => x.id === id); if (!p) return;
    state.sel = id;
    if (selMarker) selMarker.setIcon(pinIcon(selMarker.options.cat));
    selMarker = markers.get(id);
    if (pan) {
      cluster.zoomToShowLayer(selMarker, () => { map.panTo([p.lat, p.lon]); selMarker.setIcon(pinIcon(p.cat, true)); });
    } else selMarker.setIcon(pinIcon(p.cat, true));
    history.replaceState(null, "", "#p=" + id);
    renderDetail(p);
    $("#panel").classList.add("open");
  }

  function renderDetail(p) {
    const c = C.cats[p.cat];
    const o = Hours.isOpen(p.hours);
    const tbl = Hours.table(p.hours);
    const today = (new Date().getDay() + 6) % 7;
    const gq = encodeURIComponent(p.name + (p.address ? ", " + p.address : "") + ", Θεσσαλονίκη");
    const cuisine = p.cuisine ? p.cuisine.split(/[;,]/).map(x => C.cuisine[x.trim()] || x.trim().replace(/_/g, " ")).join(", ") : null;

    const rows = [];
    if (p.address || p.dimos) rows.push(["Διεύθυνση", esc([p.address, p.dimos && "Δήμος " + p.dimos].filter(Boolean).join(" · "))]);
    if (p.hours) rows.push(["Ωράριο", (o === true ? '<span class="st-open">Ανοιχτά τώρα</span><br>' : o === false ? '<span class="st-closed">Κλειστά τώρα</span><br>' : "") +
      (tbl ? `<table class="hours">${tbl.map((r, i) => `<tr class="${i === today ? "today" : ""}"><td>${r[0]}</td><td>${r[1]}</td></tr>`).join("")}</table>` : esc(p.hours))]);
    if (p.phone) rows.push(["Τηλέφωνο", p.phone.split(";").map(t => `<a href="tel:${esc(t.replace(/\s/g, ""))}">${esc(t.trim())}</a>`).join("<br>")]);
    if (p.email) rows.push(["E-mail", `<a href="mailto:${esc(p.email)}">${esc(p.email)}</a>`]);
    if (p.website) rows.push(["Ιστότοπος", `<a href="${esc(p.website)}" target="_blank" rel="noopener">${esc(p.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, ""))}</a>`]);
    if (cuisine) rows.push(["Κουζίνα", esc(cuisine)]);
    if (p.brand && p.brand !== p.name) rows.push(["Αλυσίδα", esc(p.brand)]);

    const tags = [];
    const t = (v, yes, no) => { if (v === true) tags.push(`<span class="tag">${yes}</span>`); else if (v === false) tags.push(`<span class="tag neg">${yes}</span>`); };
    t(p.outdoor, "Τραπέζια έξω"); t(p.takeaway, "Take away"); t(p.delivery, "Delivery"); t(p.wifi, "Wi‑Fi"); t(p.cards, "Κάρτες");
    if (p.vegetarian === "yes" || p.vegetarian === "only") tags.push('<span class="tag">Χορτοφαγικές επιλογές</span>');
    if (p.vegan === "yes" || p.vegan === "only") tags.push('<span class="tag">Vegan επιλογές</span>');
    if (p.wheelchair && WH[p.wheelchair]) tags.push(`<span class="tag">${WH[p.wheelchair]}</span>`);
    if (p.smoking === "no") tags.push('<span class="tag">Χωρίς κάπνισμα</span>');
    if (p.smoking === "outside") tags.push('<span class="tag">Κάπνισμα μόνο έξω</span>');

    let gemi = "";
    if (p.gemi) {
      const g = p.gemi;
      gemi = `<div class="box"><h3>Στοιχεία ΓΕΜΗ</h3>
        ${g.legal_name ? `<p>${esc(g.legal_name)}</p>` : ""}
        ${g.gemi_no ? `<p>Αρ. ΓΕΜΗ: ${esc(g.gemi_no)}</p>` : ""}
        ${g.status ? `<p>Κατάσταση: ${esc(g.status)}</p>` : ""}
        ${g.founded ? `<p>Σύσταση: ${esc(g.founded)}</p>` : ""}
        ${g.kad ? `<p>Δραστηριότητα: ${esc(g.kad)}</p>` : ""}
        ${g.url ? `<p><a href="${esc(g.url)}" target="_blank" rel="noopener">Η καρτέλα στο ΓΕΜΗ</a></p>` : ""}</div>`;
    }

    const igSearch = `https://www.google.com/search?q=${encodeURIComponent(p.name + " Θεσσαλονίκη instagram")}`;

    $("#detail").style.setProperty("--c", c.color);
    $("#detail").innerHTML = `
      <button class="link-btn back" id="backBtn">Πίσω στη λίστα</button><br>
      <span class="d-sub">${esc(C.subs[p.sub]?.label || c.label)}</span>
      <div class="d-title"><h2>${esc(p.name)}</h2>
        <button class="fav-btn big${Fav.has(p.id) ? " on" : ""}" id="favBtn" type="button" aria-pressed="${Fav.has(p.id)}" aria-label="Αγαπημένο"><svg viewBox="0 0 24 24">${HEART}</svg></button></div>
      ${p.name_en ? `<div class="d-en">${esc(p.name_en)}</div>` : ""}
      <div class="d-actions">
        ${btn(`https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lon}`, "dir", "Οδηγίες", "primary")}
        ${btn(`https://www.google.com/maps/search/?api=1&query=${gq}`, "gm", "Google Maps")}
        ${p.phone ? `<a class="btn" href="tel:${esc(p.phone.split(";")[0].replace(/\s/g, ""))}"><svg viewBox="0 0 24 24">${ICO.tel}</svg>Κλήση</a>` : ""}
        ${p.instagram ? btn(p.instagram, "ig", "Instagram") : ""}
        ${p.facebook ? btn(p.facebook, "fb", "Facebook") : ""}
        ${p.website ? btn(p.website, "web", "Ιστότοπος") : ""}
        <button class="btn" id="shareBtn" type="button"><svg viewBox="0 0 24 24">${ICO.share}</svg>Κοινοποίηση</button>
      </div>
      <dl class="rows">${rows.map(r => `<dt>${r[0]}</dt><dd>${r[1]}</dd>`).join("")}</dl>
      ${tags.length ? `<div class="tags">${tags.join("")}</div>` : ""}
      ${gemi}
      <p class="src">
        ${!p.instagram ? `<a href="${igSearch}" target="_blank" rel="noopener">Αναζήτηση στο Instagram</a> · ` : ""}
        Πηγή: ${(p.src || ["osm"]).map(s => ({ osm: "OpenStreetMap", overture: "Overture Maps", gemi: "ΓΕΜΗ", manual: "χειροκίνητη καταχώριση" }[s] || s)).join(", ")}.
        ${p.osm ? `<a href="${esc(p.osm)}" target="_blank" rel="noopener">Λάθος στοιχείο; Διόρθωσέ το στο OSM</a>` : ""}
      </p>`;
    $("#list").hidden = true; $("#detail").hidden = false; $(".list-head").hidden = true;
    $("#detail").scrollTop = 0;
    $("#backBtn").onclick = closeDetail;
    $("#favBtn").onclick = () => {
      const on = Fav.toggle(p.id);
      $("#favBtn").classList.toggle("on", on); $("#favBtn").setAttribute("aria-pressed", on);
    };
    $("#shareBtn").onclick = async () => {
      const url = location.href;
      try { if (navigator.share) await navigator.share({ title: p.name, url }); else { await navigator.clipboard.writeText(url); $("#shareBtn").lastChild.textContent = "Ο σύνδεσμος αντιγράφηκε"; } } catch (e) {}
    };
  }
  function closeDetail() {
    $("#detail").hidden = true; $("#list").hidden = false; $(".list-head").hidden = false;
    if (state.favOnly) apply(); else renderList();  // ανανέωση καρδιών στη λίστα
    if (selMarker) selMarker.setIcon(pinIcon(selMarker.options.cat));
    selMarker = null; state.sel = null;
    history.replaceState(null, "", location.pathname);
  }
  document.addEventListener("keydown", e => { if (e.key === "Escape" && state.sel) closeDetail(); });

  // ---------------------------------------------------------------- GPS: στίγμα χρήστη
  // Κουμπί στον χάρτη: 1ο πάτημα -> εντοπισμός & παρακολούθηση, κεντράρει.
  // Όσο είναι κεντραρισμένος, ο χάρτης ακολουθεί τη θέση. Ξανά πάτημα: αν ο χρήστης έσυρε τον χάρτη,
  // ξανακεντράρει· αν ήδη ακολουθεί, σβήνει το GPS.
  const Gps = { watch: null, dot: null, ring: null, follow: false, first: true };
  const GPS_ICO = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.2" class="gps-core"/><circle cx="12" cy="12" r="7"/><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3"/></svg>';
  const GpsControl = L.Control.extend({
    options: { position: "topright" },
    onAdd() {
      const b = L.DomUtil.create("button", "gps-btn");
      b.type = "button"; b.title = "Η θέση μου"; b.setAttribute("aria-label", "Δείξε τη θέση μου");
      b.innerHTML = GPS_ICO;
      L.DomEvent.disableClickPropagation(b);
      L.DomEvent.on(b, "click", gpsClick);
      return b;
    },
  });
  map.addControl(new GpsControl());
  const gpsBtn = () => $(".gps-btn");
  function gpsState(s) { const b = gpsBtn(); b.classList.remove("busy", "on", "err"); if (s) b.classList.add(s); if (s !== "on") b.classList.remove("follow"); }
  function gpsToast(msg) {
    let t = $("#toast");
    if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add("show");
    clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 3500);
  }
  function gpsStop() {
    if (Gps.watch != null) navigator.geolocation.clearWatch(Gps.watch);
    Gps.watch = null; Gps.first = true; Gps.follow = false;
    if (Gps.dot) { Gps.dot.remove(); Gps.ring.remove(); Gps.dot = Gps.ring = null; }
    state.me = null; gpsState(null);
    $("#locate").textContent = "Κοντά μου";
    renderList();
  }
  function gpsUpdate(pos) {
    const ll = [pos.coords.latitude, pos.coords.longitude], acc = Math.min(pos.coords.accuracy || 50, 2000);
    state.me = ll;
    if (!Gps.dot) {
      Gps.ring = L.circle(ll, { radius: acc, className: "me-acc", interactive: false, weight: 1 }).addTo(map);
      Gps.dot = L.marker(ll, { icon: L.divIcon({ className: "", html: '<div class="me"></div>', iconSize: [18, 18] }), interactive: false, zIndexOffset: 1000 }).addTo(map);
    } else { Gps.dot.setLatLng(ll); Gps.ring.setLatLng(ll).setRadius(acc); }
    gpsState("on");
    if (Gps.first) { gpsCenter(); Gps.first = false; $("#locate").textContent = "Ταξινόμηση κατά απόσταση"; renderList(); }
    else if (Gps.follow) map.panTo(ll, { animate: true });
  }
  function gpsError(err) {
    if (err && err.code === 3 && Gps.dot) return;  // προσωρινό timeout ενώ ήδη έχουμε στίγμα
    gpsStop(); gpsState("err");
    gpsToast(err && err.code === 1 ? "Δεν δόθηκε άδεια τοποθεσίας. Άνοιξέ τη από τις ρυθμίσεις του browser." :
      location.protocol !== "https:" && location.hostname !== "localhost" ? "Η τοποθεσία θέλει σύνδεση https." : "Η τοποθεσία δεν είναι διαθέσιμη αυτή τη στιγμή.");
  }
  function gpsStart() {
    if (!navigator.geolocation) { gpsToast("Η συσκευή δεν υποστηρίζει εντοπισμό θέσης."); return; }
    gpsState("busy");
    Gps.watch = navigator.geolocation.watchPosition(gpsUpdate, gpsError, { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 });
  }
  function gpsClick() {
    if (Gps.watch == null) return gpsStart();
    if (!state.me) return;
    if (Gps.follow) gpsStop(); else gpsCenter();
  }
  function gpsCenter() { Gps.follow = true; gpsBtn().classList.add("follow"); map.setView(state.me, Math.max(map.getZoom(), 16)); }
  map.on("dragstart", () => { Gps.follow = false; gpsBtn().classList.remove("follow"); });  // ο χρήστης μετακίνησε τον χάρτη -> σταματά η «ακολούθηση»
  $("#locate").addEventListener("click", () => { if (Gps.watch == null) gpsStart(); else if (state.me) gpsCenter(); });

  // ---------------------------------------------------------------- κινητό
  $("#grip").addEventListener("click", () => $("#panel").classList.toggle("open"));
  $("#q").addEventListener("focus", () => $("#panel").classList.add("open"));
  map.on("click", () => $("#panel").classList.remove("open"));
})();
