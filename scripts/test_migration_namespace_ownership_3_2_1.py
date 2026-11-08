#!/usr/bin/env python3
"""Regression: namespace cleanup must not trust another entity's matching name."""
from __future__ import annotations

import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "sbc5_control_center"
LEGACY_DOMAIN = "rpi5_control_center_bridge"
OLDER_LEGACY_DOMAIN = "rpi5_fan_manager_bridge"


class Registry:
    def __init__(self, ownership: str, entry_id: str = "sbc5-main"):
        self.removed = []
        self.entities = {}
        for uid in ("sbc5_cpu_temperature", "sbc5_fan_rpm"):
            self.entities["sensor." + uid] = SimpleNamespace(
                entity_id="sensor." + uid,
                platform=ownership,
                unique_id=uid,
                config_entry_id=entry_id,
            )

    def async_get(self, entity_id):
        return self.entities.get(entity_id)

    def async_remove(self, entity_id):
        self.removed.append(entity_id)
        del self.entities[entity_id]


class FakeConfigEntries:
    def __init__(self):
        self.removed = []
        self.legacy = [SimpleNamespace(entry_id="old-bridge")]

    def async_entries(self, domain):
        return self.legacy if domain == LEGACY_DOMAIN else []

    async def async_remove(self, entry_id):
        self.removed.append(entry_id)
        self.legacy = []


def load_cleanup(source: str, reg: Registry):
    module = ast.parse(source)
    function = next(node for node in module.body
                    if isinstance(node, ast.AsyncFunctionDef) and
                    node.name == "_cleanup_rpi5_namespace_entries")
    fake_asyncio = SimpleNamespace(sleep=lambda _: asyncio.sleep(0))
    ns = {
        "asyncio": fake_asyncio,
        "er": SimpleNamespace(async_get=lambda hass: reg),
        "_LOGGER": logging.getLogger("test_migration"),
        "DOMAIN": DOMAIN,
        "LEGACY_DOMAIN": LEGACY_DOMAIN,
        "OLDER_LEGACY_DOMAIN": OLDER_LEGACY_DOMAIN,
        "_write_json_path": lambda *_: None,
    }
    compiled = ast.Module(body=[
        ast.ImportFrom(module="__future__",
                       names=[ast.alias(name="annotations")], level=0),
        function,
    ], type_ignores=[])
    exec(compile(ast.fix_missing_locations(compiled), "<test migration ownership>", "exec"), ns)
    return ns["_cleanup_rpi5_namespace_entries"]


async def run(source: str, *, platform=DOMAIN, config_entry_id="sbc5-main",
              wrong_uid=False, missing_state=False):
    reg = Registry(platform, config_entry_id)
    if wrong_uid:
        reg.entities["sensor.sbc5_fan_rpm"].unique_id = "unrelated"
    reg.entities["sensor.old_legacy"] = SimpleNamespace(
        entity_id="sensor.old_legacy", platform=LEGACY_DOMAIN,
        unique_id="old_legacy", config_entry_id="old-bridge"
    )
    entries = FakeConfigEntries()
    ready = {"sensor.sbc5_cpu_temperature", "sensor.sbc5_fan_rpm",
             "sensor.sbc5_control_center_update"}
    if missing_state:
        ready.remove("sensor.sbc5_fan_rpm")
    async def fake_executor(func, *args):
        return None
    hass = SimpleNamespace(
        config_entries=entries,
        states=SimpleNamespace(
            get=lambda entity_id: SimpleNamespace(state="ready") if entity_id in ready else None,
        ),
        config=SimpleNamespace(path=lambda *args: "/tmp/sbc5-migration-test-marker.json"),
        async_add_executor_job=fake_executor,
    )
    await load_cleanup(source, reg)(hass, SimpleNamespace(entry_id="sbc5-main"))
    return entries.removed, reg.removed


async def checks(source: str):
    for label, kwargs in [
        ("foreign platform", {"platform": "unrelated"}),
        ("foreign config entry", {"config_entry_id": "other-entry"}),
        ("foreign unique id", {"wrong_uid": True}),
        ("missing native state", {"missing_state": True}),
    ]:
        removed_entries, removed_entities = await run(source, **kwargs)
        assert not removed_entries and not removed_entities, (
            label, removed_entries, removed_entities)
    removed_entries, removed_entities = await run(source)
    assert removed_entries == ["old-bridge"]
    assert removed_entities == ["sensor.old_legacy"]


async def main():
    paths = [
        ROOT / "custom_components/sbc5_control_center/__init__.py",
        ROOT / "local_apps/sbc5_control_center/bridge/__init__.py",
    ]
    bodies = [path.read_text(encoding="utf-8") for path in paths]
    assert bodies[0] == bodies[1], "App bridge and canonical integration must be identical"
    for source in bodies:
        assert "_cleanup_rpi5_namespace_entries(hass, entry)" in source
        await checks(source)


if __name__ == "__main__":
    asyncio.run(main())
    print("SBC5 native registry ownership migration regression: PASS")
