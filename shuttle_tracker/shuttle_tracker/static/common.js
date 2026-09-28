// Shared helpers: API calls with session handling, header/user bar.
const HOME = { student: "/", driver: "/driver", admin: "/admin" };

async function api(method, url, body) {
  const opts = { method, headers: {}, credentials: "same-origin" };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && url !== "/api/login") {
    location.href = "/login";
    throw new Error("Please log in.");
  }
  if (!res.ok) throw new Error(data.error || "Request failed (" + res.status + ")");
  return data;
}
const getJSON = (url) => api("GET", url);

// Returns the logged-in user. If their role is not allowed on this page, send them to their own page.
async function requireUser(allowedRoles) {
  const user = await getJSON("/api/me");
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    location.href = HOME[user.role];
    throw new Error("Redirecting...");
  }
  const bar = document.getElementById("user-info");
  if (bar) {
    bar.innerHTML = "";
    if (user.role === "admin") {
      [["Map", "/"], ["Admin", "/admin"]].forEach(([label, href]) => {
        const a = document.createElement("a");
        a.href = href; a.textContent = label; a.className = "navlink";
        bar.appendChild(a);
      });
    }
    const who = document.createElement("span");
    who.textContent = user.name + " (" + user.role + ")";
    const btn = document.createElement("button");
    btn.textContent = "Log out";
    btn.className = "linkbtn";
    btn.onclick = async () => { await api("POST", "/api/logout", {}).catch(() => {}); location.href = "/login"; };
    bar.append(who, btn);
  }
  return user;
}

function haversineM(lat1, lon1, lat2, lon2) {
  const R = 6371000, rad = (d) => (d * Math.PI) / 180;
  const a = Math.sin(rad(lat2 - lat1) / 2) ** 2 +
    Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(rad(lon2 - lon1) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function showBanner(msg) {
  const b = document.getElementById("banner");
  if (!b) return;
  b.textContent = msg;
  b.classList.toggle("hidden", !msg);
}
