/* Απλός αναγνώστης ωραρίου OSM (opening_hours) για τις συνηθισμένες μορφές:
   "Mo-Fr 08:00-22:00; Sa,Su 09:00-02:00", "24/7", "Mo-Su 10:00-15:00,18:00-24:00", "Su off".
   Ό,τι δεν καταλαβαίνει επιστρέφεται ως null (άγνωστο). */
(function () {
  const DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
  const GR = ["Δευ", "Τρι", "Τετ", "Πέμ", "Παρ", "Σάβ", "Κυρ"];

  function dayList(spec) {
    const out = new Set();
    for (const part of spec.split(",")) {
      const m = part.trim().match(/^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?$/);
      if (!m) return null;
      let a = DAYS.indexOf(m[1]), b = m[2] ? DAYS.indexOf(m[2]) : a;
      for (let i = a; ; i = (i + 1) % 7) { out.add(i); if (i === b) break; }
    }
    return out;
  }
  function mins(t) { const [h, m] = t.split(":").map(Number); return h * 60 + m; }

  // επιστρέφει πίνακα 7 ημερών με διαστήματα [από, έως] σε λεπτά (έως μπορεί > 1440)
  function parse(str) {
    if (!str) return null;
    str = str.trim();
    if (str === "24/7") return DAYS.map(() => [[0, 1440]]);
    const week = DAYS.map(() => null);
    for (let rule of str.split(";")) {
      rule = rule.trim();
      if (!rule) continue;
      if (/^PH|^SH|\bPH\b/.test(rule)) continue;              // αργίες: αγνοούνται
      let m = rule.match(/^([A-Za-z,\- ]+?)\s+(.+)$/);
      let days, times;
      if (m && /^(Mo|Tu|We|Th|Fr|Sa|Su)/.test(m[1])) { days = dayList(m[1].replace(/\s/g, "")); times = m[2]; }
      else if (/^\d/.test(rule)) { days = new Set([0, 1, 2, 3, 4, 5, 6]); times = rule; }
      else return null;
      if (!days) return null;
      times = times.trim();
      let iv = [];
      if (/^(off|closed)$/i.test(times)) iv = [];
      else {
        for (const r of times.split(",")) {
          const t = r.trim().match(/^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\+?$/);
          if (!t) return null;
          let a = mins(t[1]), b = mins(t[2]);
          if (b <= a) b += 1440;                                   // μετά τα μεσάνυχτα
          iv.push([a, b]);
        }
      }
      for (const d of days) week[d] = iv;
    }
    return week.some(Boolean) ? week.map(x => x || []) : null;
  }

  function fmt(m) { m = m % 1440; return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }

  // true / false / null (άγνωστο)
  function isOpen(str, when = new Date()) {
    const w = parse(str);
    if (!w) return null;
    const d = (when.getDay() + 6) % 7, now = when.getHours() * 60 + when.getMinutes();
    if (w[d].some(([a, b]) => now >= a && now < b)) return true;
    const prev = (d + 6) % 7;                                     // χθεσινό ωράριο που περνά τα μεσάνυχτα
    if (w[prev].some(([a, b]) => b > 1440 && now + 1440 < b)) return true;
    return false;
  }

  // Ελληνική εμφάνιση: λίστα [ημέρα, κείμενο]
  function table(str) {
    const w = parse(str);
    if (!w) return null;
    return w.map((iv, i) => [GR[i], iv.length ? iv.map(([a, b]) => fmt(a) + "–" + fmt(b)).join(", ") : "Κλειστά"]);
  }

  window.Hours = { parse, isOpen, table };
})();
