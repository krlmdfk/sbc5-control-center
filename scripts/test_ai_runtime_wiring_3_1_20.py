#!/usr/bin/env python3
"""Regression guard for the SBC5 AI runtime layer chain."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"

docker = (APP / "Dockerfile").read_text(encoding="utf-8")
v5 = (APP / "ai_cooling_v5.py").read_text(encoding="utf-8")
v51 = (APP / "ai_cooling_v5_1.py").read_text(encoding="utf-8")
v52 = (APP / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
wrapper = (APP / "ai_cooling.py").read_text(encoding="utf-8")

assert "COPY ai_cooling_legacy.py /ai_cooling_legacy.py" in docker
assert "COPY ai_cooling.py /ai_cooling_v4.py" in docker
assert "COPY thermal_predictor_v3.py /thermal_predictor_v3.py" in docker
assert "COPY thermal_active_policy.py /thermal_active_policy.py" in docker
assert "COPY ai_cooling_v5.py /ai_cooling_v5.py" in docker
assert "COPY ai_cooling_v5_1.py /ai_cooling_v5_1.py" in docker
assert "COPY ai_cooling_v5_2.py /ai_cooling.py" in docker
assert 'Path("/ai_cooling_v4.py")' in v5
assert 'Path("/ai_cooling_v5.py")' in v51
assert 'Path("/ai_cooling_v5_1.py")' in v52
assert 'Path("/ai_cooling_legacy.py")' not in v5.split("def _legacy_path", 1)[1].split("def _load_legacy", 1)[0]
assert "import thermal_predictor_v3 as _tpv3" in wrapper
assert "_legacy._thermal_predictor = _thermal_predictor" in wrapper
print("AI runtime wiring through Thermal Predictor guided v5.2: PASS")
