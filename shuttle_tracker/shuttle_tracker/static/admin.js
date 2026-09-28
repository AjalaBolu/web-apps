let drivers = [];
let lastShuttles = "", lastTrips = "";

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function fillTable(table, headers, rows) {
  table.innerHTML = "";
  const head = el("tr");
  headers.forEach((h) => head.appendChild(el("th", h)));
  table.appendChild(head);
  if (rows.length === 0) {
    const tr = el("tr"); const td = el("td", "Nothing to show yet."); td.colSpan = headers.length; td.className = "muted";
    tr.appendChild(td); table.appendChild(tr); return;
  }
  rows.forEach((cells) => {
    const tr = el("tr");
    cells.forEach((c) => { const td = el("td"); if (c instanceof Node) td.appendChild(c); else td.textContent = c; tr.appendChild(td); });
    table.appendChild(tr);
  });
}
async function act(fn) {
  try { await fn(); showBanner(""); } catch (e) { showBanner(e.message); }
}

function driverSelect(selectedId, includeNone) {
  const sel = el("select");
  const none = el("option", "Unassigned"); none.value = ""; sel.appendChild(none);
  drivers.forEach((d) => { const o = el("option", d.name); o.value = d.id; sel.appendChild(o); });
  sel.value = selectedId == null ? "" : String(selectedId);
  return sel;
}

async function loadShuttles() {
  const list = await getJSON("/api/shuttles");
  const sig = JSON.stringify(list.map((s) => [s.id, s.shuttle_number, s.driver_id, s.status]));
  if (sig === lastShuttles) return;  // avoid re-rendering (and closing dropdowns) when nothing changed
  lastShuttles = sig;
  const rows = list.map((s) => {
    const sel = driverSelect(s.driver_id);
    sel.onchange = () => act(async () => {
      await api("PUT", "/api/shuttles/" + s.id, { driver_id: sel.value ? Number(sel.value) : null });
    });
    const del = el("button", "Remove", "danger small");
    del.onclick = () => { if (confirm("Remove " + s.shuttle_number + "?")) act(async () => { await api("DELETE", "/api/shuttles/" + s.id); lastShuttles = ""; loadAll(); }); };
    return [s.shuttle_number, sel, s.status === "active" ? "Active" : "Offline", del];
  });
  fillTable(document.getElementById("shuttle-table"), ["Shuttle", "Driver", "Status", ""], rows);
}

async function loadTrips() {
  const trips = await getJSON("/api/trips?status=active");
  const sig = JSON.stringify(trips);
  if (sig === lastTrips) return;
  lastTrips = sig;
  fillTable(document.getElementById("trip-table"), ["Shuttle", "Route", "Started (UTC)"],
    trips.map((t) => [t.shuttle_number, t.route_name, t.start_time.replace("T", " ").slice(0, 19)]));
}

async function loadStops() {
  const stops = await getJSON("/api/stops");
  const rows = stops.map((s) => {
    const name = el("input"); name.value = s.name;
    const lat = el("input"); lat.value = s.latitude; lat.size = 10;
    const lng = el("input"); lng.value = s.longitude; lng.size = 10;
    const save = el("button", "Save", "small");
    save.onclick = () => act(async () => {
      await api("PUT", "/api/stops/" + s.id, { name: name.value, latitude: lat.value, longitude: lng.value });
      showBanner("");
      save.textContent = "Saved";
      setTimeout(() => (save.textContent = "Save"), 1200);
    });
    return [name, lat, lng, save];
  });
  fillTable(document.getElementById("stop-table"), ["Name", "Latitude", "Longitude", ""], rows);
}

async function loadAll() {
  try {
    await Promise.all([loadShuttles(), loadTrips()]);
    showBanner("");
  } catch (e) { showBanner("Connection problem - retrying... (" + e.message + ")"); }
}

document.getElementById("add-shuttle").onclick = () => act(async () => {
  const number = document.getElementById("new-shuttle").value.trim();
  const d = document.getElementById("new-driver").value;
  await api("POST", "/api/shuttles", { shuttle_number: number, driver_id: d ? Number(d) : null });
  document.getElementById("new-shuttle").value = "";
  lastShuttles = ""; loadAll();
});
document.getElementById("add-stop").onclick = () => act(async () => {
  await api("POST", "/api/stops", {
    name: document.getElementById("new-stop-name").value,
    latitude: document.getElementById("new-stop-lat").value,
    longitude: document.getElementById("new-stop-lng").value,
  });
  ["new-stop-name", "new-stop-lat", "new-stop-lng"].forEach((id) => (document.getElementById(id).value = ""));
  loadStops();
});

requireUser(["admin"]).then(async () => {
  try { drivers = await getJSON("/api/drivers"); } catch (e) { showBanner(e.message); }
  const nd = document.getElementById("new-driver");
  const none = el("option", "Unassigned"); none.value = ""; nd.appendChild(none);
  drivers.forEach((d) => { const o = el("option", d.name); o.value = d.id; nd.appendChild(o); });
  loadStops();
  loadAll();
  setInterval(loadAll, 3000);
}).catch(() => {});
