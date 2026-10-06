"""D-8 and one-source-per-task guards on the spatial-curve merge (2026-09-23).

Found while rehearsing the summary: the default deep-prediction directory (dl_out/) holds a
GPU-era pred_tabpfn_fold4.parquet that merge_deep would have merged silently (D-8 violation),
and E10 predictions in two byte-identical folder sets. Each test replays one of those on
synthetic files. No real result is read.
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "scripts"), str(REPO)]
import spatial_curve_analysis as A  # noqa: E402

CONSOLIDATE = REPO / "scripts" / "spatial_curve_tabpfn_consolidate.py"
KEYS = dict(frame="registered", rep=0, k=5, day=-1, seed=A.SEED)


def _rows(est, clusters=(1, 2), rho=0.5, designs=("Q1", "Q2")):
    return pd.DataFrame([dict(KEYS, design=d, cluster=c, est=e, rho=rho)
                         for c in clusters for d in designs for e in est])


def _q():
    return (pd.DataFrame(columns=["cluster", "rep", "holdout", "ordering", "k", "est", "rho"]),
            pd.DataFrame(columns=["cluster", "rep", "k", "day", "est", "rho"]))


def _merge(monkeypatch, *dirs):
    monkeypatch.setattr(A, "DEEP_DIRS", [Path(d) for d in dirs])
    monkeypatch.setattr(A, "FRAME_TAG", "")
    return A.merge_deep(*_q())


# ── merge_deep ────────────────────────────────────────────────────────────────────────────────
def test_raw_gpu_era_tabpfn_file_is_refused(tmp_path, monkeypatch):
    _rows(["E8", "E9"]).to_parquet(tmp_path / "pred_tabpfn_fold4.parquet")
    with pytest.raises(RuntimeError, match="D-8"):
        _merge(monkeypatch, tmp_path)


def test_consolidated_file_without_device_tag_is_refused(tmp_path, monkeypatch):
    _rows(["E8", "E9"]).to_parquet(tmp_path / "pred_tabpfn_consolidated_registered.parquet")
    with pytest.raises(RuntimeError, match="device"):
        _merge(monkeypatch, tmp_path)


def test_consolidated_cpu_file_and_e10_merge(tmp_path, monkeypatch):
    _rows(["E8", "E9"]).assign(device="cpu").to_parquet(
        tmp_path / "pred_tabpfn_consolidated_registered.parquet")
    _rows(["E10"]).to_parquet(tmp_path / "pred_convgnp_fold0_seed0.parquet")
    Q1, Q2, info = _merge(monkeypatch, tmp_path)
    assert set(Q1.est) == {"E8", "E9", "E10"} and len(Q1) == 6 and len(Q2) == 6
    assert len(info["sources"]) == 2


def test_byte_identical_copies_are_collapsed(tmp_path, monkeypatch):
    for d in ("fold0", "e10_fold0"):
        (tmp_path / d).mkdir()
        _rows(["E10"]).to_parquet(tmp_path / d / "pred_convgnp_fold0_seed0.parquet")
    Q1, _, _ = _merge(monkeypatch, tmp_path)
    assert len(Q1) == 2                                # not 4


def test_two_different_scorings_of_one_task_are_refused(tmp_path, monkeypatch):
    for d, rho in (("run_a", 0.5), ("run_b", 0.7)):
        (tmp_path / d).mkdir()
        _rows(["E10"], rho=rho).to_parquet(tmp_path / d / "pred_convgnp_fold0_seed0.parquet")
    with pytest.raises(RuntimeError, match="scored differently"):
        _merge(monkeypatch, tmp_path)


# ── consolidator ──────────────────────────────────────────────────────────────────────────────
def _consolidate(tmp_path, *extra):
    return subprocess.run([sys.executable, str(CONSOLIDATE), str(tmp_path / "in"),
                           "--out", str(tmp_path / "out"), *extra],
                          capture_output=True, text=True)


def _cities(tmp_path, clusters):
    f = tmp_path / "cities.parquet"
    pd.DataFrame({"frame": "registered", "cluster": list(clusters)}).to_parquet(f)
    return str(f)


def test_consolidator_excludes_gpu_era_and_tags_cpu(tmp_path):
    (tmp_path / "in").mkdir()
    _rows(["E8", "E9"]).to_parquet(tmp_path / "in" / "pred_tabpfn_fold-1_registered_cpu_g0.parquet")
    _rows(["E8", "E9"], rho=0.9).to_parquet(tmp_path / "in" / "partial_tabpfn_registered_run1.parquet")
    r = _consolidate(tmp_path, "--cities", _cities(tmp_path, [1, 2]))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "D-8 EXCLUDED" in r.stdout and "partial_tabpfn_registered_run1" in r.stdout
    out = pd.read_parquet(tmp_path / "out" / "pred_tabpfn_consolidated_registered.parquet")
    assert (out.device == "cpu").all() and (out.rho == 0.5).all()


def test_consolidator_refuses_a_registered_city_that_never_appears(tmp_path):
    (tmp_path / "in").mkdir()
    _rows(["E8", "E9"]).to_parquet(tmp_path / "in" / "pred_tabpfn_fold-1_registered_cpu_g0.parquet")
    r = _consolidate(tmp_path, "--cities", _cities(tmp_path, [1, 2, 3]))
    assert r.returncode == 3 and "missing" in r.stdout
    r = _consolidate(tmp_path, "--cities", _cities(tmp_path, [1, 2, 3]), "--allow-incomplete")
    assert r.returncode == 0


def test_consolidator_refuses_a_city_with_only_one_design(tmp_path):
    (tmp_path / "in").mkdir()
    _rows(["E8", "E9"], clusters=(1,)).to_parquet(tmp_path / "in" / "pred_tabpfn_x_cpu_g0.parquet")
    _rows(["E8", "E9"], clusters=(2,), designs=("Q1",)).to_parquet(
        tmp_path / "in" / "partial_tabpfn_x_cpu_g1.parquet")
    r = _consolidate(tmp_path)
    assert r.returncode == 3, r.stdout
    assert "('registered', 2)" in r.stdout            # named as incomplete, not half-merged


def test_consolidator_refuses_all_nan_outputs(tmp_path):
    """The 2026-09-24 failure: every row written, not one value finite (tabpfn 9.0.0 licence
    error swallowed by a bare except). Row counts looked healthy; the values did not exist."""
    (tmp_path / "in").mkdir()
    _rows(["E8", "E9"], rho=float("nan")).to_parquet(
        tmp_path / "in" / "pred_tabpfn_fold-1_registered_cpu_g0.parquet")
    r = _consolidate(tmp_path)
    assert r.returncode == 4 and "NO finite" in r.stdout, r.stdout


def test_same_named_files_in_two_folders_are_two_sources(tmp_path):
    """2026-09-24: sources were keyed by file NAME, so an archived run and the live run (same
    names, different folders) merged into one source and every task key doubled."""
    for d, rho in (("old", float("nan")), ("new", 0.5)):
        (tmp_path / "in" / d).mkdir(parents=True)
        _rows(["E8", "E9"], rho=rho).to_parquet(
            tmp_path / "in" / d / "pred_tabpfn_fold-1_registered_cpu_g0.parquet")
    r = _consolidate(tmp_path)
    assert "duplicate task keys" not in r.stdout, r.stdout
