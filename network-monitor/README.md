# Hybrid Cloud-Based Network Monitoring System

Final-year project MVP. Local Python agent collects device metrics → sends over HTTPS to a
cloud-hosted Flask API → stored in PostgreSQL → shown on a web dashboard with threshold-based alerts.

## Project structure

```
network-monitor/
├── app/                  # Cloud backend + dashboard (deploy this folder)
│   ├── app.py            # Flask app: API routes, dashboard routes, alert engine
│   ├── models.py         # SQLAlchemy models: User, Device, Metric, Alert
│   ├── config.py         # Env-var-driven config (thresholds, secrets, DB URL)
│   ├── templates/        # Dashboard HTML (Jinja)
│   ├── static/style.css
│   ├── requirements.txt
│   └── Procfile          # gunicorn start command for Railway/Render
└── agent/                # Runs locally on each monitored device
    ├── agent.py           # Main loop
    ├── metrics.py          # psutil-based system metrics
    ├── network.py          # Latency via ping
    ├── api_client.py       # Sends data to backend
    ├── config.py
    ├── logger.py
    └── requirements.txt
```

## 1. Local test (already verified working)

```bash
cd app
pip install -r requirements.txt
export ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=changeme123 AGENT_API_KEY=dev-agent-key-change-me
python3 app.py
```
Visit http://localhost:5000, log in with the admin credentials above.

## 2. Deploy to Render

1. Push this repo (with the `network-monitor/` subfolder, if applicable) to GitHub.
2. On [render.com](https://render.com) → New → **PostgreSQL**. Create it, then open it and copy the
   **Internal Database URL** shown on its page (starts with `postgres://`) — you'll need it in step 5.
3. New → **Web Service** → connect the same GitHub repo.
4. Set:
   - **Root Directory**: `app` (or `network-monitor/app` if you put this inside another repo)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. In the service's **Environment** tab, add:
   - `DATABASE_URL` — paste the Internal Database URL you copied in step 2
   - `SECRET_KEY` — any long random string
   - `AGENT_API_KEY` — any long random string (agents will need this exact value)
   - `ADMIN_EMAIL` / `ADMIN_PASSWORD` — your login for the demo
   - (optional) `CPU_THRESHOLD`, `MEMORY_THRESHOLD`, `DISK_THRESHOLD`, `LATENCY_THRESHOLD`
6. Click **Create Web Service** — Render builds and deploys automatically using the `Procfile`/start command.
7. Once deployed, Render gives you a public URL like `https://your-app.onrender.com`.
8. Visit `/login` on that URL to confirm the dashboard loads.

**Note on Render's free tier:** free web services spin down after 15 minutes of inactivity and take
~30-60 seconds to wake up on the next request. Fine for a live demo where you're actively hitting it,
but worth knowing so a "slow" first load doesn't look like a bug during your defense.

## 3. Run the agent on your test/demo machines

```bash
cd agent
pip install -r requirements.txt
export MONITOR_API_URL=https://your-app.up.railway.app
export MONITOR_API_KEY=<same AGENT_API_KEY you set in Railway>
python3 agent.py
```

Run this on 2-3 machines (or the same machine with different `device_uid` overrides if you only
have one laptop — see note below) and watch them appear on the dashboard within ~15 seconds.

**Only one physical machine for the demo?** Temporarily hardcode a different `device_uid` in
`metrics.get_device_uid()` for each terminal you run the agent in — this simulates multiple devices
without needing multiple machines, and is honestly reportable as a *simulated multi-device demo*
per your project's rule about not overstating what's real (section 17 of your spec).

## 4. Trigger a demo alert

While the agent is running, spike CPU on the test machine (e.g. run a CPU-bound loop, or a stress
tool) — within one polling interval the dashboard's device status and the Alerts page will show a
`high_cpu` alert automatically, and it auto-resolves once usage drops back under threshold.

## What's simulated vs. real (be upfront about this in your report)

- Multi-device demo may use one physical machine reporting under multiple `device_uid`s — real
  metric collection, simulated topology.
- Email notifications for alerts are **not implemented** in this MVP — alerts surface on the
  dashboard only. Flag this as a documented future enhancement (spec allows this).
- HTTPS is provided by Railway/Render's platform TLS termination, not custom certificate handling.

## What's already tested (verified locally before handoff)

- Agent → API auth via `X-API-Key`, rejects invalid keys (401)
- Metrics ingestion creates/updates device + metric rows
- Threshold breach automatically creates an alert; recovery automatically resolves it
- JWT login issues valid tokens; API routes reject missing/invalid tokens (401)
- All four dashboard pages (overview, devices, device detail w/ chart, alerts) render correctly
