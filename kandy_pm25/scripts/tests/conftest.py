"""Pytest path setup for the evidence-pipeline tests.

Adds the repo root (for `src.*` imports) and the scripts dir (for `city_config`,
`xichang_prod`, ... imports) to sys.path so the evidence modules import the same
way they do at runtime.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]      # .../kandy_pm25
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
