#!/usr/bin/env python3
"""Verify bundled historical evidence without a network or third-party package."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'docs/FROZEN_EVIDENCE.json').read_text())
    for name, expected in manifest['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid evidence path')
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing regular evidence file: ' + name)
        data = path.read_bytes()
        if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise ValueError('Evidence differs from the reviewed snapshot: ' + name)
    print(f"PASS: {len(manifest['files'])} frozen evidence files match their reviewed bytes.")


if __name__ == '__main__':
    main()
