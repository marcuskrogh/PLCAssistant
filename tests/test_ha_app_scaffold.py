"""HA App scaffold layout (SWD-123 / A3)."""

from __future__ import annotations

import pathlib
import subprocess
import textwrap

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
    assert (APP / "custom_components" / "plcassistant" / "manifest.json").is_file()


def test_dockerfile_installs_from_local_context():
    """Supervisor build context is the App folder; no git clone at build time."""
    text = (APP / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY plcassistant" in text
    assert "COPY custom_components" in text
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

    int_src = _package_files(ROOT / "custom_components" / "plcassistant")
    int_dst = _package_files(APP / "custom_components" / "plcassistant")
    assert int_src.keys() == int_dst.keys()
    mismatched = sorted(k for k in int_src if int_src[k] != int_dst[k])
    assert not mismatched, f"integration mismatch: {mismatched}"


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
    assert any(
        (isinstance(m, dict) and m.get("type") == "homeassistant_config" and m.get("read_only") is False)
        or m == "homeassistant_config:rw"
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
    assert "install_thin_integration" in text
    assert "/homeassistant" in text
    assert "custom_components/plcassistant" in text


def test_run_sh_auto_installs_integration(tmp_path: pathlib.Path):
    """Smoke the App entrypoint copy logic against a fake HA config mount."""
    src = tmp_path / "src" / "plcassistant"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text('{"domain":"plcassistant","version":"0.1.3"}\n', encoding="utf-8")
    (src / "README.md").write_text("bundled\n", encoding="utf-8")

    ha_config = tmp_path / "homeassistant"
    ha_config.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    run_sh = APP / "run.sh"
    env = {
        "PLCASSISTANT_DATA": str(data_dir),
        "PLCASSISTANT_HA_CONFIG": str(ha_config),
        "PLCASSISTANT_INTEGRATION_SRC": str(src),
        "PLCASSISTANT_HOST": "127.0.0.1",
        "PLCASSISTANT_PORT": "8099",
    }
    # Fake python3 so the final `exec python3 -m plcassistant.app` is a no-op,
    # while comparison/install still uses the real interpreter.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_python = bin_dir / "python3"
    fake_python.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env sh
            if [ "$1" = "-m" ] && [ "$2" = "plcassistant.app" ]; then
              echo stub-runtime
              exit 0
            fi
            exec /usr/bin/python3 "$@"
            """
        ),
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    env["PATH"] = f"{bin_dir}:/usr/bin:/bin"

    result = subprocess.run(
        ["sh", str(run_sh)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    dst = ha_config / "custom_components" / "plcassistant" / "manifest.json"
    assert dst.is_file()
    assert "0.1.3" in dst.read_text(encoding="utf-8")
    assert (data_dir / "integration_needs_core_restart").is_file()
    assert "thin integration installed/updated" in result.stdout

    # Second run should report up to date and clear the restart stamp.
    result2 = subprocess.run(
        ["sh", str(run_sh)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result2.returncode == 0, result2.stderr + result2.stdout
    assert "already up to date" in result2.stdout
    assert not (data_dir / "integration_needs_core_restart").exists()
