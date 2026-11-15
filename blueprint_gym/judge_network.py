"""Offline, byte-audited task derivatives for future network-restricted trials.

Harbor 0.26 supports [environment].network_mode='allowlist' and allowed_hosts.
This prepares policy, not a claim that a provider firewall has been exercised.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import tempfile
import tomllib

POLICY = {'network_mode': 'allowlist', 'allowed_hosts': ['inference.verda.com']}
VERSION = 'blueprint-judge-egress-v1'
TASK_PATH = re.compile(r'(?:tasks/bp-\d{2}-(?:clean|scan|vector)|science_demo/tasks/science-a-\d{2})\Z')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_protocol_destination(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if any(output.is_relative_to(root/p) for p in ('tasks', 'science_demo/tasks')):
        raise ValueError('Protocol output must be outside the frozen task trees')


def _restricted_config(raw):
    original = tomllib.loads(raw.decode('utf-8'))
    env = original.get('environment', {})
    verifier = original.get('verifier', {})
    if env.get('network_mode') != 'public' or 'allowed_hosts' in env:
        raise ValueError('Expected the frozen public agent environment baseline')
    if any(k in original.get('agent', {}) for k in ('network_mode', 'allowed_hosts')):
        raise ValueError('Agent phase override would bypass the reviewed baseline')
    if (verifier.get('environment_mode') != 'separate'
            or verifier.get('environment', {}).get('network_mode') != 'no-network'
            or verifier.get('network_mode', 'no-network') != 'no-network'
            or verifier.get('allowed_hosts')):
        raise ValueError('Trusted verifier must remain separate and no-network')
    text = raw.decode('utf-8')
    block = re.search(r'(?ms)^\[environment\]\s*\n(.*?)(?=^\[|\Z)', text)
    if block is None:
        raise ValueError('Missing environment table')
    replacement, count = re.subn(r'(?m)^network_mode[ \t]*=[ \t]*"public"[ \t]*$',
        'network_mode = "allowlist"\nallowed_hosts = ["inference.verda.com"]', block[1])
    if count != 1:
        raise ValueError('Expected one explicit public network mode')
    derived = text[:block.start(1)] + replacement + text[block.end(1):]
    expected = deepcopy(original)
    expected['environment'].update(POLICY)
    if tomllib.loads(derived) != expected:
        raise ValueError('Task derivative changed fields beyond the network baseline')
    return derived.encode('utf-8')


def isolate_protocol_tasks(root, configs, output):
    """Copy task bytes, rewrite only agent egress, return configs and provenance.

    Reject symlinks/special files before reading them. Copies are independent
    regular files, not links into the frozen task set. Config paths are absolute
    so running the generated command from another directory cannot select an
    unrestricted task with a similar name.
    """
    root, output = Path(root).resolve(), Path(output).resolve()
    validate_protocol_destination(root, output)
    if not configs or not configs[0].get('tasks'):
        raise ValueError('Protocol must contain explicit tasks')
    entries = configs[0]['tasks']
    for config in configs:
        if config['tasks'] != entries:
            raise ValueError('All controls must use the identical task collection')
        for agent in config['agents']:
            if agent.get('model_name') and (agent.get('base_url') != 'https://inference.verda.com/v1'
                    or agent.get('kwargs', {}).get('skip_install') is not True):
                raise ValueError('Restricted trials require the reviewed Verda endpoint and preinstalled agent')
    selected = []
    seen = set()
    for entry in entries:
        relative = entry.get('path', '')
        if set(entry) != {'path'} or not isinstance(relative, str) or not TASK_PATH.fullmatch(relative):
            raise ValueError('Only explicit frozen task paths are accepted')
        if relative in seen:
            raise ValueError('Duplicate task path')
        seen.add(relative)
        source = root / relative
        part = root
        for name in Path(relative).parts:
            part = part / name
            if part.is_symlink():
                raise ValueError('Symlink in task source')
        if not source.is_dir():
            raise ValueError('Missing task source')
        files = []
        for item in sorted(source.rglob('*')):
            mode = item.lstat().st_mode
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise ValueError('Task source must contain only regular files and directories')
            files.append(item.relative_to(source).as_posix())
        if 'task.toml' not in files:
            raise ValueError('Missing task.toml')
        _restricted_config((source/'task.toml').read_bytes())
        selected.append((relative, source, files))
    destination = output / 'tasks'
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    staging = Path(tempfile.mkdtemp(prefix='.task-stage-', dir=output))
    records = []
    replacements = {}
    try:
        for relative, source, files in selected:
            target = staging / source.name
            if target.exists():
                raise ValueError('Task names must be unique')
            hashes = {}
            for name in files:
                path = source / name
                raw = path.read_bytes()
                derived = _restricted_config(raw) if name == 'task.toml' else raw
                copied = target / name
                copied.parent.mkdir(parents=True, exist_ok=True)
                copied.write_bytes(derived)
                copied.chmod(stat.S_IMODE(path.stat().st_mode))
                hashes[name] = {'source_sha256': _sha(raw), 'derived_sha256': _sha(derived)}
            final = destination / source.name
            records.append({'source': relative, 'derived': str(final), 'files': hashes})
            replacements[relative] = str(final)
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    derived_configs = deepcopy(configs)
    for config in derived_configs:
        config['tasks'] = [{'path': replacements[e['path']]} for e in entries]
    snapshot = {'version': VERSION, 'network_policy': deepcopy(POLICY),
                'verifier_network_mode': 'no-network', 'runtime_egress_verified': False,
                'tasks': records,
                'limitations': [
                    'Docker/Modal outbound enforcement and model-provider connectivity have not been executed for this policy.',
                    'Docker allowlists require Harbor egress control and supported daemon kernel capabilities.',
                    'Image builds may download dependencies; the running agent may reach only the listed model API host.',
                    'Blocked runtime dependency downloads must be investigated, never silently changed to public networking.',
                    'Public answers may already be memorized; network restrictions do not establish uncontaminated evaluation.',
                    'These are new network-policy task derivatives; the historical 160 trials used the frozen original tasks.']}
    snapshot['files_manifest_sha256'] = _sha(json.dumps(records, sort_keys=True).encode())
    return derived_configs, snapshot
