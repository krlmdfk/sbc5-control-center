#!/usr/bin/env python3
"""Release gates: stable 3.2.1 needs explicit hardware approval and strict ZIP."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
rel = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
aut = (ROOT / ".github/workflows/auto-release.yml").read_text(encoding="utf-8")
val = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
ready = (ROOT / "scripts/test_global_release_readiness_3_2_0.py").read_text(encoding="utf-8")

data = yaml.safe_load(rel)
steps = data["jobs"]["release"]["steps"]
names = {step["name"]: (i, step) for i, step in enumerate(steps) if "name" in step}
assert len(names) == len([step for step in steps if "name" in step])
index, guard = names["Block unverified publication"]
assert guard["if"] == "${{ !inputs.dry_run }}"
assert guard["env"]["HARDWARE_VERIFIED"] == "${{ inputs.hardware_verified }}"
assert guard["env"]["FIELD_TEST_ACKNOWLEDGED"] == "${{ inputs.field_test_acknowledged }}"
assert guard["env"]["RELEASE_CHANNEL"] == "${{ inputs.release_channel }}"
assert 'if [ "$RELEASE_CHANNEL" = "stable" ]; then' in guard["run"]
assert 'test "$HARDWARE_VERIFIED" = "true"' in guard["run"]
assert 'elif [ "$RELEASE_CHANNEL" = "field_test" ]; then' in guard["run"]
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in guard["run"]
assert "3.2.1" in guard["run"]
inputs = data.get("on", data.get(True))["workflow_dispatch"]["inputs"]
assert inputs["dry_run"]["default"] is True
assert inputs["hardware_verified"]["default"] is False
assert inputs["field_test_acknowledged"]["default"] is False
assert set(inputs["release_channel"]["options"]) == {"stable", "field_test"}
for release_name in ("Publish main GitHub Release", "Publish HACS integration Release"):
    body = names[release_name][1]["run"]
    assert "--prerelease" in body and "--latest" in body, release_name
    assert 'inputs.release_channel' in body, release_name

publish_names = [
    "Clone and synchronize HACS repository",
    "Commit and push main release metadata",
    "Publish main GitHub Release",
    "Publish HACS integration Release",
    "Verify HACS repository token",
    "Require HACS token for publication",
]
for name in publish_names:
    i, step = names[name]
    assert i > index
    assert step.get("if") == "${{ !inputs.dry_run }}", name

verify_i, verify = names["Validate prepared release strictly"]
zip_i, zip_step = names["Build and verify install/update package"]
assert verify_i < zip_i
assert verify["run"].strip() == "python scripts/validate_release.py --strict-manifest-hashes"
for text in ("build_local_update.py", "--verify-only", "zip_security_preflight.py", "sha256sum"):
    assert text in zip_step["run"], text
assert zip_i < names["Upload preflight artifact"][0]
assert "build_release_zip.py" not in rel

# A failed HACS validation must not force a second release attempt to
# overwrite an already synchronized integration or block resumption.
assert 'if [ "$HACS_CURRENT" != "$CURRENT_VERSION" ] && [ "$HACS_CURRENT" != "$VERSION" ]; then' in rel
assert 'if git diff --cached --quiet; then' in rel
assert 'if [ "$HACS_CURRENT" != "$VERSION" ]; then' in rel
assert 'if [ "$HACS_CURRENT" = "$VERSION" ]; then' in rel
assert 'non-documentation file: $changed_path' in rel
assert 'git diff --cached --name-only -z' in rel
assert 'README.md|info.md|"RELEASE_NOTES_${VERSION}.md")' in rel
assert 'git commit -m "Release ${VERSION}"' in rel
assert 'echo "HACS_SHA=$(git rev-parse HEAD)" >> "$GITHUB_ENV"' in rel

for name in ("Upload preflight artifact", "Publish main GitHub Release"):
    assert "SBC5_UPDATE_" in str(names[name][1])
    assert ".zip.sha256" in str(names[name][1])

assert 'if [ "$version" != "3.2.0" ]; then' in aut
assert "test_release_workflow_3_2_1_gates.py" in val
assert 'version in {"3.1.37", "3.2.0"}' not in ready
assert 'version.startswith("3.2.")' in ready
assert 'assert manifest["version"] == "3.2.0"' not in val
print("3.2.1 stable release gate regression: PASS")
