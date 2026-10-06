# Network usage plan: SLT Fibre Starter (from 2026-10-04)

## The connection (verified on slt.lk, 2026-10-04)
- **Package:** SLT-Mobitel Fibre Starter, Rs. 2,950/month + tax, up to 100 Mbps down / 50 Mbps up.
- **Anytime quota:** **80 GB per month**, no rollover mentioned. Extra GB Rs. 60–100 per GB.
- **Free night data:** "Free data from 12 midnight to 7 am". The user first said midnight to 4 am; the
  official page says 7 am. ⚠ **Confirm in the MySLT app** (it shows the night-time usage counter
  separately) before relying on 04:00–07:00.
- **The catch:** "throttling condition of the main package will be applicable" to the free night data. Once
  the 80 GB anytime quota is exhausted the line drops to **64 kbps**, and on this wording that applies at
  night as well. **Protecting the 80 GB is what keeps the free nights usable.**
- Sources: https://www.slt.lk/en/broadband/packages ; https://pariganaka.com/the-end-of-data-anxiety-all-you-need-to-know-about-slt-mobitels-new-unlimited-fibre-services/ (19 Jan 2026).

## What the project actually costs (measured 2026-10-04)
| job | objects | bytes | binding constraint |
|---|---|---|---|
| OpenAQ S3 daily files | 1 per station-day | median **~740 B** each (plus ~1–2 KB HTTP/TLS overhead) | request count and latency, not volume |
| existing confirmation OpenAQ download | ~0.5 M | 41 MB on disk | |
| existing spatial-curve raw | ~0.7 M | 159 MB on disk | |
| **A** full-network ladder (cap 40, discovery + confirmation) | ~2 M | **~3–6 GB** on the wire | ~7 h at 64 workers (82 GET/s measured on the old line) |
| **B** spatial-curve full records | ~2–3 M | **~4–8 GB** | ~8–10 h |
| GEE predictor pulls | per city-year | MB | GEE quotas, not the line |
| Kaggle dataset uploads | per version | tens to hundreds of MB; **a version re-uploads every file** (gotcha #26) | upload volume |

So the redo fits easily inside the free window; at the measured request rate it needs about **2–3 nights**.

## Rules
1. **Heavy jobs only inside 00:05–06:45 SLST** through `scripts/night_window.sh` (15-minute margins at each
   end). This covers bulk downloads, full re-ingests and Kaggle dataset uploads above ~200 MB. If MySLT shows the
   window ends at 04:00, run with `NIGHT_STOP=03:50`.
2. **Daytime project traffic is kept small** (API calls, kernel pushes, GEE queries, small outputs), so the
   80 GB serves normal household use. The runner logs each night's total traffic; a daytime job expected to
   exceed **2 GB** waits for the night.
3. **Every heavy job is resumable and atomic per unit** (temp file + `os.replace`), checks
   `night_guard.check()` before each unit, and exits 75 to resume the next night.
4. **Never re-download what is on disk**: cache by object; verify with checksums or row counts.
5. **Kaggle**: upload at night; keep datasets split so a version does not re-upload large unchanged files.
6. **The PC must stay on overnight.** Sleep while plugged in is a Windows setting the user changes; the desktop
   app's keep-awake can be requested for a session.
7. **Check the month's usage** in MySLT before each multi-night job, and after it finishes.
