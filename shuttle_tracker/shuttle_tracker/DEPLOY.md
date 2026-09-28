# Deploying to Render (free tier)

## 1. Push to GitHub
    git init
    git add .
    git commit -m "Campus shuttle tracker"
    git branch -M main
    git remote add origin https://github.com/<your-username>/campus-shuttle-tracker.git
    git push -u origin main
(`.gitignore` already keeps `.env` and `shuttle.db` out of the repo.)

## 2. Create the service
1. Render dashboard -> New -> Blueprint -> pick the repo. Render reads `render.yaml`.
   (Or New -> Web Service, with build command `pip install -r requirements.txt` and
   start command `python seed.py && gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT app:app`.)
2. When prompted, enter the three passwords (admin, driver, student). Use passwords you
   will remember for the defense. `SECRET_KEY` is generated for you.
3. Deploy. Your app will be at https://campus-shuttle-tracker.onrender.com (or similar).

## 3. Check it
- Open `<your-url>/api/health` -> should show {"status":"ok"}.
- Open `<your-url>/login` and sign in with admin@campus.test / your admin password.

## Free tier behaviour (plan around this)
- The service sleeps after ~15 minutes without traffic; the first request afterwards
  takes 30-60 seconds. Open the site a few minutes BEFORE your defense.
- The filesystem is temporary: on every restart/redeploy the SQLite file is rebuilt from
  `seed.py`. Shuttles, stops or trips you added through the admin page are lost.
  For permanent changes, edit `seed.py` (e.g. your real campus coordinates) and redeploy.
- Running trips stop on restart, which is fine: just press Start Trip again.

## Environment variables
SECRET_KEY (auto), SEED_ADMIN_PASSWORD, SEED_DRIVER_PASSWORD, SEED_STUDENT_PASSWORD,
AVG_SPEED_KMH (default 20), SIM_INTERVAL_SEC (default 2).

## Optional: keep data permanently
Add a Render Disk (paid) mounted at /var/data and set DATABASE_PATH=/var/data/shuttle.db,
or move to PostgreSQL later. Not needed for the demo.
