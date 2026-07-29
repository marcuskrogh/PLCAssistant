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
    config_version = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))[
        "version"
    ]
    assert "COPY plcassistant" in text
    assert "COPY custom_components" in text
    assert "pip3 install" in text
    assert "git+https://" not in text
    assert "apk add" not in text
    assert "ARG BUILD_VERSION" in text
    assert "ARG BUILD_ARCH" in text
    assert "APP_VERSION" in text
    assert 'io.hass.version="${BUILD_VERSION}"' in text
    assert 'io.hass.type="app"' in text
    assert 'io.hass.arch="${BUILD_ARCH}"' in text
    assert f"ARG BUILD_VERSION={config_version}" in text
    assert "migrate_legacy_mqtt_subscribe.py" in text
    # Cache-bust RUN must appear before package/integration COPY.
    assert text.index("APP_VERSION") < text.index("COPY plcassistant")
    assert text.index("APP_VERSION") < text.index("COPY custom_components")


def test_migrate_legacy_script_exists():
    assert (APP / "migrate_legacy_mqtt_subscribe.py").is_file()


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
    assert int(data.get("timeout") or 0) >= 60
    watchdog = str(data.get("watchdog") or "")
    assert "[HOST]" in watchdog
    assert "[PORT:8099]" in watchdog
    assert watchdog.startswith(("http://", "tcp://"))
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
    assert "seeded default" in text
    assert "mqtt_broker=core-mosquitto" in text
    assert "install_thin_integration" in text
    assert "continuing App start" in text
    assert "migrate_legacy_mqtt_subscribe" in text
    assert "migrate_legacy_mqtt_subscribe.py" in text
    assert "bundled_integration_from_app" in text
    assert "hass.components" in text
    assert "/homeassistant" in text
    assert "custom_components/plcassistant" in text
    # Dead path under !needs_integration_sync must not re-check legacy migrate.
    assert "Belt-and-suspenders" not in text


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


def test_run_sh_continues_when_integration_install_fails(tmp_path: pathlib.Path):
    """Install failure must not abort Soft-PLC start (Supervisor job-group races)."""
    src = tmp_path / "src" / "plcassistant"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text('{"domain":"plcassistant","version":"0.1.6"}\n', encoding="utf-8")

    ha_config = tmp_path / "homeassistant"
    ha_config.mkdir()
    # Make custom_components a file so mkdir -p fails inside install_thin_integration.
    (ha_config / "custom_components").write_text("not-a-directory\n", encoding="utf-8")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
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

    env = {
        "PLCASSISTANT_DATA": str(data_dir),
        "PLCASSISTANT_HA_CONFIG": str(ha_config),
        "PLCASSISTANT_INTEGRATION_SRC": str(src),
        "PLCASSISTANT_HOST": "127.0.0.1",
        "PLCASSISTANT_PORT": "8099",
        "PATH": f"{bin_dir}:/usr/bin:/bin",
    }
    result = subprocess.run(
        ["sh", str(APP / "run.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "stub-runtime" in result.stdout
    assert "continuing App start" in (result.stdout + result.stderr)


def _fake_python(bin_dir: pathlib.Path) -> None:
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


_LEGACY_INIT = textwrap.dedent(
    '''\
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        unsub = await hass.components.mqtt.async_subscribe(
            topic, _make_out_handler(tag, entry.entry_id), qos=1
        )
        return True
    '''
)


def test_run_sh_migrates_legacy_hass_components_subscribe(tmp_path: pathlib.Path):
    """Even with a stale App image, migrate DST off hass.components."""
    src = tmp_path / "src" / "plcassistant"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text('{"domain":"plcassistant","version":"0.1.4"}\n', encoding="utf-8")
    (src / "__init__.py").write_text(_LEGACY_INIT, encoding="utf-8")

    ha_config = tmp_path / "homeassistant"
    dst = ha_config / "custom_components" / "plcassistant"
    dst.mkdir(parents=True)
    (dst / "manifest.json").write_text('{"domain":"plcassistant","version":"0.1.4"}\n', encoding="utf-8")
    (dst / "__init__.py").write_text(_LEGACY_INIT, encoding="utf-8")
    pycache = dst / "__pycache__"
    pycache.mkdir()
    (pycache / "stale.pyc").write_bytes(b"old")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "bundled_integration_from_app").write_text("0.1.7\n", encoding="utf-8")
    version_file = tmp_path / "APP_VERSION"
    version_file.write_text("0.1.7\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_python(bin_dir)

    env = {
        "PLCASSISTANT_DATA": str(data_dir),
        "PLCASSISTANT_HA_CONFIG": str(ha_config),
        "PLCASSISTANT_INTEGRATION_SRC": str(src),
        "PLCASSISTANT_APP_VERSION_FILE": str(version_file),
        "PLCASSISTANT_HOST": "127.0.0.1",
        "PLCASSISTANT_PORT": "8099",
        "PATH": f"{bin_dir}:/usr/bin:/bin",
    }
    result = subprocess.run(
        ["sh", str(APP / "run.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    init_text = (dst / "__init__.py").read_text(encoding="utf-8")
    assert "hass.components" not in init_text
    assert "from homeassistant.components.mqtt import async_subscribe" in init_text
    assert "await async_subscribe(\n            hass, topic," in init_text
    assert "migrated thin integration off hass.components" in result.stdout
    assert not (pycache / "stale.pyc").exists()


def test_run_sh_forces_sync_when_app_version_stamp_changes(tmp_path: pathlib.Path):
    """App version bump must re-copy even if file bytes already matched."""
    content_init = "from homeassistant.components.mqtt import async_subscribe\n"
    content_manifest = '{"domain":"plcassistant","version":"0.1.7"}\n'

    src = tmp_path / "src" / "plcassistant"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text(content_manifest, encoding="utf-8")
    (src / "__init__.py").write_text(content_init, encoding="utf-8")

    ha_config = tmp_path / "homeassistant"
    dst = ha_config / "custom_components" / "plcassistant"
    dst.mkdir(parents=True)
    # Byte-identical to SRC so only the App version stamp forces the sync.
    (dst / "manifest.json").write_text(content_manifest, encoding="utf-8")
    (dst / "__init__.py").write_text(content_init, encoding="utf-8")

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "bundled_integration_from_app").write_text("0.1.6\n", encoding="utf-8")
    version_file = tmp_path / "APP_VERSION"
    version_file.write_text("0.1.7\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_python(bin_dir)

    env = {
        "PLCASSISTANT_DATA": str(data_dir),
        "PLCASSISTANT_HA_CONFIG": str(ha_config),
        "PLCASSISTANT_INTEGRATION_SRC": str(src),
        "PLCASSISTANT_APP_VERSION_FILE": str(version_file),
        "PLCASSISTANT_HOST": "127.0.0.1",
        "PLCASSISTANT_PORT": "8099",
        "PATH": f"{bin_dir}:/usr/bin:/bin",
    }
    result = subprocess.run(
        ["sh", str(APP / "run.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "requires thin-integration sync" in result.stdout
    assert "thin integration installed/updated" in result.stdout
    assert (data_dir / "bundled_integration_from_app").read_text(encoding="utf-8").strip() == "0.1.7"
