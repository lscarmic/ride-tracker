# Ride Tracker

A self-updating trip map. Drop a GPX file into `gpx/` and the map at your
GitHub Pages URL rebuilds itself in about a minute.

## One-time setup (~5 minutes)

1. Create a **public** repo on github.com (e.g. `ride-tracker`).
2. Upload the contents of this folder to it (drag everything onto
   "uploading an existing file" on the repo page — include the `.github`
   folder; if dragging misses it, create the file
   `.github/workflows/build.yml` manually and paste its contents).
3. Repo **Settings → Pages** → Source: "Deploy from a branch" →
   Branch: `main`, folder `/ (root)` → Save.
4. Repo **Settings → Actions → General** → Workflow permissions →
   select **Read and write permissions** → Save.
5. Your map is live at `https://<username>.github.io/ride-tracker/`

## Daily use (from your phone)

1. Export the day's ride from REVER as GPX.
2. On github.com, open the repo → `gpx` folder → **Add file → Upload files**.
3. Done. The Action rebuilds `data.json`; the page updates in ~1 minute.
   (Pages itself can take another minute or two to refresh.)

Notes:
- Legs are ordered and colored by filename — keep the `01 …`, `02 …` naming.
- Avoid `>` or `<` in filenames.
- To test a rebuild without uploading: repo → Actions → "Rebuild map" → Run workflow.
