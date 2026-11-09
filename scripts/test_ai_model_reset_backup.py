#!/usr/bin/env python3
"""Verify explicit AI reset creates a durable intact backup or aborts."""
import hashlib
import json
import tempfile
from pathlib import Path

from sys import path as sys_path
ROOT = Path(__file__).resolve().parents[1]
sys_path.insert(0, str(ROOT / 'local_apps' / 'sbc5_control_center'))
from config_ui import backup_ai_model_before_reset


def sha(b):
    return hashlib.sha256(b).hexdigest()


with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    model = base / 'ai_cooling_model.json'
    backups = base / 'backups'
    assert backup_ai_model_before_reset(model, backups) is None

    payload = json.dumps({'schema': 5, 'observations_total': 40072,
                          'qualified_samples_total': 1169, 'bins': {}}).encode()
    model.write_bytes(payload)
    result = backup_ai_model_before_reset(model, backups)
    backup = Path(result['backup'])
    assert backup.exists() and backup.read_bytes() == payload
    assert model.read_bytes() == payload, 'backup operation must not alter original'
    assert result['sha256'] == sha(payload)
    assert result['bytes'] == len(payload)
    assert len(list(backups.glob('*.json'))) == 1

    # A corrupted existing model is also preserved, never silently erased.
    model.write_bytes(b'invalid existing model')
    result2 = backup_ai_model_before_reset(model, backups)
    assert Path(result2['backup']).read_bytes() == b'invalid existing model'
    assert len(list(backups.glob('*.json'))) == 2

    model.unlink()
    model.symlink_to(backup)
    try:
        backup_ai_model_before_reset(model, backups)
    except ValueError:
        pass
    else:
        raise AssertionError('symlink model must be rejected')

print('AI model reset safety backup: PASS')
