// Student dashboard: Leaflet map + polling the Flask API every few seconds.
const POLL_MS = 2000;
const ROUTE_COLORS = ["#2563eb", "#16a34a", "#9333ea", "#ea580c"];

let map;
let stops = [];
let routes = [];
let shuttles = [];
let etas = {};            // shuttle id -> ETA response (only when a destination is chosen)
let shuttleMarkers = {};  // shuttle id -> Leaflet marker
let selectedId = null;
let destId = null;

const $ = (id) => document.getElementById(id);

function formatEta(seconds) {
  if (seconds < 5) return "Arriving";
  const m = Math.floor(seconds / 60), s = seconds % 60;
  return m > 0 ? m + " min " + s + " s" : s + " s";
}

function nearestStop(loc) {
  let best = null;
  for (const s of stops) {
    const d = haversineM(loc.latitude, loc.longitude, s.latitude, s.longitude);
    if (!best || d < best.d) best = { name: s.name, d };
  }
  return best;
}

// ---------- map setup ----------
async function initMap() {
  map = L.map("map");
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  try {
    [stops, routes] = await Promise.all([getJSON("/api/stops"), getJSON("/api/routes")]);
  } catch (e) {
    map.setView([0, 0], 2);
    showBanner("Could not load campus data: " + e.message);
    return;
  }
  if (stops.length === 0) {
    map.setView([0, 0], 2);
    showBanner("No campus stops configured yet.");
    return;
  }

  routes.forEach((r, i) => {
    const pts = r.stops.map((s) => [s.latitude, s.longitude]);
    L.polyline(pts, { color: ROUTE_COLORS[i % ROUTE_COLORS.length], weight: 4, opacity: 0.6 })
      .addTo(map).bindTooltip(r.name, { sticky: true });
  });
  stops.forEach((s) => {
    L.circleMarker([s.latitude, s.longitude], { radius: 7, color: "#111827", fillColor: "#fff", fillOpacity: 1, weight: 2 })
      .addTo(map).bindTooltip(s.name, { permanent: false });
  });
  map.fitBounds(stops.map((s) => [s.latitude, s.longitude]), { padding: [40, 40] });

  const sel = $("destination");
  stops.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.id;
    o.textContent = s.name;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => {
    destId = sel.value ? Number(sel.value) : null;
    poll();
  });
}

// ---------- polling ----------
async function poll() {
  try {
    shuttles = await getJSON("/api/shuttles");
    etas = {};
    if (destId) {
      const active = shuttles.filter((s) => s.status === "active" && s.location);
      const results = await Promise.all(
        active.map((s) => getJSON("/api/eta/" + s.id + "?stop_id=" + destId).catch(() => null))
      );
      active.forEach((s, i) => { if (results[i]) etas[s.id] = results[i]; });
    }
    showBanner("");
  } catch (e) {
    showBanner("Connection problem - retrying... (" + e.message + ")");
    return;
  }
  render();
}

// ---------- rendering ----------
function render() {
  updateMarkers();
  renderList();
  renderDetail();
}

function updateMarkers() {
  const seen = new Set();
  shuttles.forEach((s) => {
    if (s.status !== "active" || !s.location) return;
    seen.add(s.id);
    const pos = [s.location.latitude, s.location.longitude];
    const cls = "shuttle-icon" + (s.id === selectedId ? " selected" : "");
    const num = s.shuttle_number.replace(/\D+/g, "") || s.id;
    if (!shuttleMarkers[s.id]) {
      const m = L.marker(pos, { icon: L.divIcon({ className: cls, html: "<div>" + num + "</div>", iconSize: [30, 30] }) });
      m.on("click", () => { selectedId = s.id; render(); });
      m.addTo(map);
      shuttleMarkers[s.id] = m;
    } else {
      shuttleMarkers[s.id].setLatLng(pos);
      shuttleMarkers[s.id].setIcon(L.divIcon({ className: cls, html: "<div>" + num + "</div>", iconSize: [30, 30] }));
    }
  });
  Object.keys(shuttleMarkers).forEach((id) => {
    if (!seen.has(Number(id))) { map.removeLayer(shuttleMarkers[id]); delete shuttleMarkers[id]; }
  });
}

function statusOf(s) {
  if (s.status !== "active") return { key: "offline", label: "Offline" };
  if (etas[s.id] && etas[s.id].arrived) return { key: "arrived", label: "Arrived" };
  return { key: "active", label: "Active" };
}

function renderList() {
  const box = $("shuttle-list");
  box.innerHTML = "";
  if (shuttles.length === 0) {
    box.innerHTML = '<p class="muted">No shuttles are registered yet.</p>';
    return;
  }
  shuttles.forEach((s) => {
    const st = statusOf(s);
    const item = document.createElement("div");
    item.className = "shuttle-item" + (s.id === selectedId ? " selected" : "");
    const row = document.createElement("div");
    row.className = "row";
    const name = document.createElement("strong");
    name.textContent = s.shuttle_number;
    const badge = document.createElement("span");
    badge.className = "status " + st.key;
    badge.textContent = st.label;
    row.append(name, badge);
    item.appendChild(row);

    const sub = document.createElement("div");
    sub.className = "muted";
    if (s.status !== "active") sub.textContent = "Not currently running";
    else if (!destId) sub.textContent = "Select a destination to see ETA";
    else if (etas[s.id]) sub.textContent = "ETA: " + formatEta(etas[s.id].eta_seconds);
    else sub.textContent = "Waiting for location...";
    item.appendChild(sub);

    item.addEventListener("click", () => { selectedId = s.id; render(); if (s.location) map.panTo([s.location.latitude, s.location.longitude]); });
    box.appendChild(item);
  });
}

function renderDetail() {
  const box = $("detail");
  const s = shuttles.find((x) => x.id === selectedId);
  if (!s) { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  const st = statusOf(s);
  const eta = etas[s.id];
  const route = s.active_trip ? routes.find((r) => r.id === s.active_trip.route_id) : null;
  const dest = stops.find((x) => x.id === destId);

  const rows = [["Status", st.label]];
  if (s.status !== "active") {
    rows.push(["Info", "This shuttle is offline and has no live location."]);
  } else if (!s.location) {
    rows.push(["Info", "Waiting for the first location update."]);
  } else {
    const near = nearestStop(s.location);
    rows.push(["Location", near ? "Near " + near.name + " (" + Math.round(near.d) + " m)" : "Unknown"]);
    rows.push(["Coordinates", s.location.latitude.toFixed(5) + ", " + s.location.longitude.toFixed(5)]);
    rows.push(["Route", route ? route.name : "-"]);
    rows.push(["Destination", dest ? dest.name : "Not selected"]);
    if (eta) rows.push(["Distance", Math.round(eta.distance_m) + " m"]);
  }

  box.innerHTML = "";
  const h = document.createElement("h3");
  h.textContent = s.shuttle_number;
  const dl = document.createElement("dl");
  rows.forEach(([k, v]) => {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v;
    dl.append(dt, dd);
  });
  box.append(h, dl);
  if (eta) {
    const big = document.createElement("p");
    big.className = "eta-big";
    big.textContent = eta.arrived ? "Arrived at " + eta.destination : "ETA " + formatEta(eta.eta_seconds);
    box.appendChild(big);
  }
}

// ---------- start ----------
requireUser().then(() => initMap()).then(() => {
  poll();
  setInterval(poll, POLL_MS);
}).catch(() => {});
