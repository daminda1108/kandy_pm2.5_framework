"""
training_logger.py — Persistent training log for Stage 2+3 sessions.

Appends structured Markdown entries for every training run and diagnostic.
Nothing is overwritten — the file is the canonical record of all training history.

Usage:
    from src.utils.training_logger import TrainingLogger
    logger = TrainingLogger()
    logger.append_session({...})
    logger.print_summary_table()
"""

import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Default log path (relative to project root)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_LOG_PATH = (
    Path(__file__).parents[2] / "results" / "training_log" / "STAGE23_TRAINING_LOG.md"
)

_HEADER = """\
# STAGE 2+3 TRAINING LOG
## Kandy PM2.5 Three-Stage Framework

**Project**: Kandy PM2.5 PINN — Undergrad Thesis (Daminda Alahakoon, U. Peradeniya)
**Created**: {created}

This file is the canonical record of all Stage 2 pre-training and Stage 3 fine-tuning
sessions for the Kandy physics-informed neural network. New entries are appended by
`TrainingLogger.append_session()` and `append_diagnostic()`. Nothing is ever overwritten.

### Format
Each entry follows a strict template parseable by `get_latest_session()`.
Interpretation codes in loss tables:
- ✅ = PASS   ⚠️ = WARNING   ❌ = FAIL

---
"""


# ─────────────────────────────────────────────────────────────────────────────
# Interpretation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _interp_pde(mean_val: float) -> str:
    if mean_val < 0.1:  return "Physics converged ✅"
    if mean_val < 1.0:  return "Physics partially converged ⚠️"
    return "Physics NOT converged ❌"


def _interp_data(mean_val: float) -> str:
    rmse = math.sqrt(max(mean_val, 0.0))
    tag  = "✅" if mean_val < 50 else ("⚠️" if mean_val < 100 else "❌")
    label = ("Data signal active" if mean_val < 50
             else ("Data weak — possible spatial collapse" if mean_val < 100
                   else "Data not learning"))
    return f"{label} {tag}  (RMSE ≈ {rmse:.1f} µg/m³)"


def _interp_kbound(mean_val: float) -> str:
    if mean_val < 0.01: return "Diffusivity in physical bounds ✅"
    return "Diffusivity violations present ⚠️"


def _interp_generic(mean_val: float) -> str:
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# TrainingLogger
# ─────────────────────────────────────────────────────────────────────────────

class TrainingLogger:
    """
    Persistent append-only training log in Markdown format.

    Methods:
        append_session(session_dict)     — add a training session block
        append_diagnostic(diag_dict)     — add a diagnostic analysis block
        get_latest_session()             — parse and return most recent session dict
        get_session_count()              — count logged training sessions
        print_summary_table()            — print ASCII table to stdout
    """

    def __init__(self, log_path: str = None, wandb_run=None):
        """
        Args:
            log_path:  path to the Markdown log file (default: results/training_log/…)
            wandb_run: optional wandb.Run object. If provided, session summaries are
                       also pushed to W&B as run.summary values.
        """
        self.log_path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.wandb_run = wandb_run
        if not self.log_path.exists():
            self.log_path.write_text(
                _HEADER.format(created=datetime.now(timezone.utc).isoformat()),
                encoding="utf-8",
            )

    # ─────────────────────────────────────────────────────────────────────
    # append_session
    # ─────────────────────────────────────────────────────────────────────

    def append_session(self, session: dict) -> None:
        """
        Append a training session block to the log.

        Required keys in session dict:
          session_type, timestamp, platform, architecture_ver, n_epochs,
          wall_clock_sec, data_period, n_samples, loss_schedule, final_losses,
          checkpoints, recommended_ckpt, arch_mismatches, notes, verdict
        """
        n = self.get_session_count() + 1
        stype        = session.get("session_type",     "unknown")
        ts           = session.get("timestamp",        datetime.now(timezone.utc).isoformat())
        platform     = session.get("platform",         "unknown")
        arch_ver     = session.get("architecture_ver", "unknown")
        n_epochs     = session.get("n_epochs",         0)
        wall_s       = session.get("wall_clock_sec",   0.0)
        data_period  = session.get("data_period",      "unknown")
        n_samples    = session.get("n_samples",        0)
        sched        = session.get("loss_schedule",    {})
        fl           = session.get("final_losses",     {})
        checkpoints  = session.get("checkpoints",      [])
        rec_ckpt     = session.get("recommended_ckpt", "—")
        mismatches   = session.get("arch_mismatches",  [])
        notes        = session.get("notes",            "")
        verdict      = session.get("verdict",          "PASS — proceed")

        # Loss schedule table
        sched_rows = ""
        for key, val in sched.items():
            sched_rows += f"| {key} | {val} |\n"
        if not sched_rows:
            sched_rows = "| (not recorded) | — |\n"

        # Final losses table
        loss_keys_interp = {
            "L_pde":     _interp_pde,
            "L_data":    _interp_data,
            "L_bc":      _interp_generic,
            "L_k_bound": _interp_kbound,
            "L_total":   _interp_generic,
        }
        loss_rows = ""
        for key, interp_fn in loss_keys_interp.items():
            if key in fl:
                entry    = fl[key]
                mean_v   = entry.get("mean", float("nan")) if isinstance(entry, dict) else float(entry)
                std_v    = entry.get("std",  float("nan")) if isinstance(entry, dict) else 0.0
                interp   = interp_fn(mean_v)
                loss_rows += f"| {key} | {mean_v:.6f} | {std_v:.6f} | {interp} |\n"
        if not loss_rows:
            loss_rows = "| (not recorded) | — | — | — |\n"

        # Checkpoints list
        ckpt_list = "\n".join(f"- `{p}`" for p in checkpoints) or "*(none saved)*"

        # Architecture notes
        if mismatches:
            arch_notes = "\n".join(f"- {m}" for m in mismatches)
        else:
            arch_notes = "None — architecture consistent with config."

        block = f"""
---
## Session {n} — {stype}
**Timestamp**: {ts}
**Platform**: {platform}
**Architecture**: {arch_ver}
**Epochs**: {n_epochs}  |  **Wall-clock**: {wall_s:.1f}s  ({wall_s/60:.1f} min)
**Data**: {data_period}  ({n_samples:,} samples)

### Loss Schedule
| Component | Weight |
|---|---|
{sched_rows}
### Final Losses (last 20 epochs)
| Loss | Mean | Std | Interpretation |
|---|---|---|---|
{loss_rows}
### Checkpoints
{ckpt_list}
**Recommended for downstream use**: `{rec_ckpt}`

### Architecture Notes
{arch_notes}

### Expert Notes
{notes if notes else "*(none)*"}

### Verdict
**{verdict}**

"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(block)

        # ── Optional W&B summary ───────────────────────────────────────────
        if self.wandb_run is not None:
            try:
                summary = {
                    "session/type":         stype,
                    "session/arch_ver":     arch_ver,
                    "session/n_epochs":     n_epochs,
                    "session/wall_sec":     wall_s,
                    "session/verdict":      verdict,
                }
                for key in ("L_pde", "L_data", "L_bc", "L_k_bound", "L_total"):
                    if key in fl:
                        entry = fl[key]
                        mean_v = entry.get("mean", float("nan")) if isinstance(entry, dict) else float(entry)
                        summary[f"final/{key}"] = mean_v
                self.wandb_run.summary.update(summary)
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────
    # append_diagnostic
    # ─────────────────────────────────────────────────────────────────────

    def append_diagnostic(self, diagnostic: dict) -> None:
        """
        Append a diagnostic analysis block to the log.

        Required keys in diagnostic dict:
          diagnostic_type, timestamp, checkpoint_used, findings,
          pass_fail, recommended_action
        """
        diag_type    = diagnostic.get("diagnostic_type",     "unknown")
        ts           = diagnostic.get("timestamp",           datetime.now(timezone.utc).isoformat())
        ckpt         = diagnostic.get("checkpoint_used",     "—")
        findings     = diagnostic.get("findings",            [])
        pass_fail    = diagnostic.get("pass_fail",           {})
        rec_action   = diagnostic.get("recommended_action",  "")

        findings_text = "\n".join(f"- {f}" for f in findings) or "*(none recorded)*"

        pf_rows = ""
        for check, result in pass_fail.items():
            icon = "✅" if result == "PASS" else "❌"
            pf_rows += f"| {check} | {result} {icon} |\n"
        if not pf_rows:
            pf_rows = "| (none) | — |\n"

        block = f"""
---
## Diagnostic — {diag_type}
**Timestamp**: {ts}
**Checkpoint**: `{ckpt}`

### Findings
{findings_text}

### Pass/Fail
| Check | Result |
|---|---|
{pf_rows}
### Recommended Action
{rec_action if rec_action else "*(none)*"}

"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(block)

    # ─────────────────────────────────────────────────────────────────────
    # get_latest_session
    # ─────────────────────────────────────────────────────────────────────

    def get_latest_session(self) -> dict:
        """
        Parse the log file and return the most recently appended session as a dict.
        Returns None if no sessions exist.
        """
        text = self.log_path.read_text(encoding="utf-8")
        # Find all session blocks (## Session N — ...)
        pattern = r"## Session (\d+) — (\S+)\n\*\*Timestamp\*\*: (.+?)\n\*\*Platform\*\*: (.+?)\n\*\*Architecture\*\*: (.+?)\n\*\*Epochs\*\*: (\d+)"
        matches = list(re.finditer(pattern, text))
        if not matches:
            return None
        m = matches[-1]
        return {
            "session_number":  int(m.group(1)),
            "session_type":    m.group(2),
            "timestamp":       m.group(3).strip(),
            "platform":        m.group(4).strip(),
            "architecture_ver": m.group(5).strip(),
            "n_epochs":        int(m.group(6)),
        }

    # ─────────────────────────────────────────────────────────────────────
    # get_session_count
    # ─────────────────────────────────────────────────────────────────────

    def get_session_count(self) -> int:
        """Return total number of training sessions logged."""
        text = self.log_path.read_text(encoding="utf-8")
        return len(re.findall(r"^## Session \d+", text, re.MULTILINE))

    # ─────────────────────────────────────────────────────────────────────
    # print_summary_table
    # ─────────────────────────────────────────────────────────────────────

    def print_summary_table(self) -> None:
        """Print a formatted ASCII table of all training sessions."""
        text = self.log_path.read_text(encoding="utf-8")

        # Parse session headers
        header_pat = re.compile(
            r"## Session (\d+) — (\S+)\n"
            r"\*\*Timestamp\*\*: (.+?)\n"
            r"\*\*Platform\*\*: (.+?)\n"
            r"\*\*Architecture\*\*: (.+?)\n"
            r"\*\*Epochs\*\*: (\d+)",
        )
        # Parse verdict
        verdict_pat = re.compile(r"\*\*Verdict\*\*\s*\n\*\*(.+?)\*\*")
        # Parse L_pde and L_data from loss table rows
        pde_pat  = re.compile(r"\| L_pde\s+\| ([\d.]+) \|")
        data_pat = re.compile(r"\| L_data\s+\| ([\d.]+) \|")

        sessions = list(header_pat.finditer(text))
        verdicts = list(verdict_pat.finditer(text))
        pde_vals  = list(pde_pat.finditer(text))
        data_vals = list(data_pat.finditer(text))

        if not sessions:
            print("No sessions logged yet.")
            return

        col_widths = [4, 24, 12, 28, 8, 12, 12, 20]
        headers    = ["#", "Type", "Date", "Architecture", "Epochs",
                      "L_pde", "L_data", "Verdict"]

        def _pad(s, w):
            s = str(s)
            return s[:w].ljust(w)

        sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(f" {_pad(h, w)} " for h, w in zip(headers, col_widths)) + "|"

        print("\n" + sep)
        print(header_row)
        print(sep)

        for i, m in enumerate(sessions):
            num      = m.group(1)
            stype    = m.group(2)
            ts       = m.group(3)[:10]   # date only
            arch     = m.group(5)
            epochs   = m.group(6)
            verdict  = verdicts[i].group(1)[:18] if i < len(verdicts) else "—"
            l_pde    = f"{float(pde_vals[i].group(1)):.4f}"  if i < len(pde_vals)  else "—"
            l_data   = f"{float(data_vals[i].group(1)):.4f}" if i < len(data_vals) else "—"

            row = "|" + "|".join(f" {_pad(v, w)} " for v, w in zip(
                [num, stype, ts, arch, epochs, l_pde, l_data, verdict],
                col_widths
            )) + "|"
            print(row)

        print(sep)
        print(f"  Total sessions: {len(sessions)}  |  Log: {self.log_path}\n")
