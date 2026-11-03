"""Dependency-free unit regressions for the SBC5 registry migration routines.

Extracts just the migration functions from real source code so tests can run
without a fully installed Home Assistant environment.
"""
from __future__ import annotations
import ast
import json
import logging
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "custom_components/sbc5_control_center/__init__.py").read_text()
DOMAIN = "sbc5_control_center"
PREDICTOR_NATIVE_IDS = {
    "sbc5_ai_thermal_forecast_30s",
    "sbc5_ai_thermal_forecast_60s",
    "sbc5_ai_thermal_forecast_120s",
    "sbc5_ai_thermal_predictor_confidence",
}

class Registry:
    def __init__(self, *entries):
        self.entities = {e.entity_id: e for e in entries}
        self.deleted = []
        self.renamed = []
    def async_get(self, entity_id):
        return self.entities.get(entity_id)
    def async_remove(self, entity_id):
        assert entity_id in self.entities
        self.deleted.append(entity_id)
        self.entities.pop(entity_id)
    def async_update_entity(self, entity_id, *, new_entity_id=None, **kw):
        entry = self.entities.pop(entity_id)
        if new_entity_id:
            assert new_entity_id not in self.entities
            self.renamed.append((entity_id, new_entity_id))
            entry.entity_id = new_entity_id
            self.entities[new_entity_id] = entry
        else:
            self.entities[entity_id] = entry

def make_entry(entity_id, platform, unique_id):
    return SimpleNamespace(entity_id=entity_id, platform=platform, unique_id=unique_id)

def load_function(name, registry):
    module = ast.parse(SOURCE)
    function = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
    isolate = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), function], type_ignores=[])
    namespace = dict(
        er=SimpleNamespace(async_get=lambda hass: registry),
        _LOGGER=logging.getLogger(__name__),
        DOMAIN=DOMAIN,
        PREDICTOR_NATIVE_IDS=PREDICTOR_NATIVE_IDS,
    )
    exec(compile(ast.fix_missing_locations(isolate), "<isolated SBC5 migration>", "exec"), namespace)
    return namespace[name]

class MigrationTest(unittest.TestCase):
    def test_unrelated_canonical_owner_same_unique_id_does_not_delete_native(self):
        uid = "sbc5_cpu_frequency"
        foreign = make_entry("sensor."+uid, "other_integration", uid)
        native = make_entry("sensor.my_cpu_frequency", DOMAIN, uid)
        r=Registry(foreign,native)
        load_function("_canonicalize_native_entity_registry",r)(SimpleNamespace())
        self.assertIs(r.async_get(foreign.entity_id), foreign)
        self.assertIs(r.async_get(native.entity_id), native)
        self.assertEqual(r.deleted, [])
        self.assertEqual(r.renamed, [])
    def test_free_canonical_id_is_restored(self):
        uid="sbc5_cpu_frequency"
        entry=make_entry("sensor.my_cpu_frequency",DOMAIN,uid)
        r=Registry(entry)
        load_function("_canonicalize_native_entity_registry",r)(SimpleNamespace())
        self.assertIs(r.async_get("sensor."+uid),entry)
        self.assertEqual(r.deleted,[])
    def test_native_duplicates_only(self):
        uid="sbc5_cpu_frequency"
        primary=make_entry("sensor."+uid,DOMAIN,uid)
        duplicate=make_entry("sensor.my_cpu_frequency",DOMAIN,uid)
        r=Registry(primary,duplicate)
        load_function("_canonicalize_native_entity_registry",r)(SimpleNamespace())
        self.assertIs(r.async_get(primary.entity_id),primary)
        self.assertEqual(r.deleted,["sensor.my_cpu_frequency"])
    def test_template_only_predictor_migration(self):
        uid="sbc5_ai_thermal_forecast_30s"
        good=make_entry("sensor."+uid,"template",uid)
        foreign=make_entry("sensor.foreign", "other_integration",uid)
        native=make_entry("sensor.native",DOMAIN,uid)
        wrong=make_entry("sensor.wrong","template","other_id")
        r=Registry(good,foreign,native,wrong)
        hass=SimpleNamespace(data={})
        load_function("_migrate_predictor_template_entities",r)(hass)
        self.assertEqual(r.deleted,["sensor."+uid])
        self.assertIn(foreign.entity_id,r.entities)
        self.assertIn(native.entity_id,r.entities)
        self.assertIn(wrong.entity_id,r.entities)
        self.assertEqual(hass.data[DOMAIN]["entity_id_overrides"][uid],"sensor."+uid)
    def test_repairs_executor_and_issue_deletion_separation(self):
        path=ROOT/"custom_components/sbc5_control_center/repairs.py"
        source=path.read_text()
        tree=ast.parse(source)
        cl=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="RestartRepairFlow")
        method=next(x for x in cl.body if isinstance(x,ast.AsyncFunctionDef) and x.name=="async_step_init")
        calls=[node for node in ast.walk(method) if isinstance(node,ast.Call)]
        exec_jobs=[c for c in calls if isinstance(c.func,ast.Attribute) and c.func.attr=="async_add_executor_job"]
        self.assertEqual(len(exec_jobs),2)
        self.assertEqual({c.args[0].attr for c in exec_jobs},{"_read_marker","_clear_marker"})
        for call in exec_jobs:
            self.assertTrue(any(isinstance(n,ast.Await) and n.value is call for n in ast.walk(method)))
        self.assertTrue(any(isinstance(c.func,ast.Attribute) and c.func.attr=="async_delete_issue" for c in calls))
        self.assertNotIn("await ir.async_delete_issue",source)
    def test_version_metadata(self):
        manifest=json.loads((ROOT/"custom_components/sbc5_control_center/manifest.json").read_text())
        const=(ROOT/"custom_components/sbc5_control_center/const.py").read_text()
        self.assertIn(f'APP_VERSION = "{manifest["version"]}"',const)
        self.assertEqual(manifest["version"],"3.1.36")

if __name__=="__main__":
    unittest.main()
