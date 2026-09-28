let me, stops = [], routes = [], shuttle = null;
const panel = document.getElementById("driver-panel");

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}

function build() {
  panel.innerHTML = "";
  panel.append(el("h3", "Assigned shuttle: -"));
  panel.firstChild.id = "d-title";
  const dl = el("dl"); dl.id = "d-info";
  panel.appendChild(dl);

  const label = el("label", "Route"); label.htmlFor = "route-select";
  const sel = el("select"); sel.id = "route-select";
  routes.forEach((r) => {
    const o = el("option", r.name); o.value = r.id; sel.appendChild(o);
  });
  const start = el("button", "Start Trip", "primary"); start.id = "start-btn";
  const stop = el("button", "Stop Trip", "danger"); stop.id = "stop-btn";
  const row = el("div", undefined, "btnrow"); row.append(start, stop);
  panel.append(label, sel, row);

  start.onclick = async () => {
    try { await api("POST", "/api/trips/start", { shuttle_id: me.shuttle_id, route_id: Number(sel.value) }); showBanner(""); refresh(); }
    catch (e) { showBanner(e.message); }
  };
  stop.onclick = async () => {
    try { await api("POST", "/api/trips/stop", { shuttle_id: me.shuttle_id }); showBanner(""); refresh(); }
    catch (e) { showBanner(e.message); }
  };
}

function nearest(loc) {
  let best = null;
  stops.forEach((s) => {
    const d = haversineM(loc.latitude, loc.longitude, s.latitude, s.longitude);
    if (!best || d < best.d) best = { name: s.name, d };
  });
  return best;
}

function render() {
  const active = shuttle.status === "active";
  document.getElementById("d-title").textContent = "Assigned shuttle: " + shuttle.shuttle_number;
  const rows = [["Status", active ? "Trip in progress" : "Offline (no active trip)"]];
  if (active && shuttle.active_trip) {
    const route = routes.find((r) => r.id === shuttle.active_trip.route_id);
    if (route) {
      rows.push(["Route", route.name]);
      rows.push(["Final destination", route.stops[route.stops.length - 1].name]);
    }
  }
  if (active && shuttle.location) {
    const n = nearest(shuttle.location);
    rows.push(["Current location", shuttle.location.latitude.toFixed(5) + ", " + shuttle.location.longitude.toFixed(5)]);
    if (n) rows.push(["Near", n.name + " (" + Math.round(n.d) + " m)"]);
  } else if (active) {
    rows.push(["Current location", "Waiting for first update..."]);
  }
  const dl = document.getElementById("d-info");
  dl.innerHTML = "";
  rows.forEach(([k, v]) => { dl.append(el("dt", k), el("dd", v)); });
  document.getElementById("start-btn").disabled = active;
  document.getElementById("stop-btn").disabled = !active;
  document.getElementById("route-select").disabled = active;
}

async function refresh() {
  try {
    shuttle = await getJSON("/api/shuttles/" + me.shuttle_id);
    showBanner("");
    render();
  } catch (e) { showBanner("Connection problem - retrying... (" + e.message + ")"); }
}

requireUser(["driver", "admin"]).then(async (user) => {
  me = user;
  if (!me.shuttle_id) {
    panel.innerHTML = "";
    panel.append(el("p", "No shuttle is assigned to your account yet. Ask an administrator.", "muted"));
    return;
  }
  try {
    [stops, routes] = await Promise.all([getJSON("/api/stops"), getJSON("/api/routes")]);
  } catch (e) { showBanner("Could not load data: " + e.message); return; }
  if (routes.length === 0) { panel.textContent = "No routes are configured yet."; return; }
  build();
  refresh();
  setInterval(refresh, 2000);
}).catch(() => {});
