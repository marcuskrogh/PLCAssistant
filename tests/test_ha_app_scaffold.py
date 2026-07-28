"""HA App scaffold layout (SWD-123 / A3)."""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "plc_assistant"


def _package_files(root: pathlib.Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        files[str(path.relative_to(root))] = path.read_bytes()
    return files


def test_app_required_files_exist():
    for name in ("config.yaml", "Dockerfile", "run.sh", "README.md", "pyproject.toml"):
        path = APP / name
        assert path.is_file(), f"missing {path}"
    assert (APP / "plcassistant" / "__init__.py").is_file()


def test_dockerfile_installs_from_local_context():
    """Supervisor build context is the App folder; no git clone at build time."""
    text = (APP / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY plcassistant" in text
    assert "pip3 install" in text
    assert "git+https://" not in text
    assert "apk add" not in text


def test_bundled_package_matches_repo_root():
    """Bundled App copy must stay in sync with ./scripts/sync-ha-app-package.sh."""
    src = _package_files(ROOT / "plcassistant")
    dst = _package_files(APP / "plcassistant")
    assert src.keys() == dst.keys(), (
        f"file set mismatch; only_src={sorted(src.keys() - dst.keys())} "
        f"only_dst={sorted(dst.keys() - src.keys())}"
    )
    mismatched = sorted(k for k in src if src[k] != dst[k])
    assert not mismatched, f"content mismatch: {mismatched}"
    assert (APP / "pyproject.toml").read_bytes() == (ROOT / "pyproject.toml").read_bytes()


def test_config_ingress_and_port():
    data = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
    assert data["ingress"] is True
    assert data["ingress_port"] == 8099
    assert "8099/tcp" in data["ports"]
    assert data["slug"] == "plcassistant"
    assert "armv7" not in (data.get("arch") or [])
    maps = data.get("map") or []
    assert any(
        (isinstance(m, dict) and m.get("type") == "data")
        or m == "data:rw"
        or (isinstance(m, str) and m.startswith("data"))
        for m in maps
    )
    opts = data["options"]
    assert opts["mqtt_broker"] == "core-mosquitto"
    assert opts["instance_id"] == "default"


def test_run_sh_wires_ha_runtime():
    text = (APP / "run.sh").read_text(encoding="utf-8")
    assert "program.json" in text
    assert "plcassistant.app" in text
    assert "0.0.0.0" in text
    assert "--ha-runtime" in text or "PLCASSISTANT_HA_RUNTIME" in text
    assert "options.json" in text
