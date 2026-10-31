"""Recoverable publication of a native export set and its owning manifest.

Callers hold their existing build lock. Keep a durable copy of every replaced
file before touching the release. A pending journal rejects freshness; the next
build rolls back before taking its input snapshot. Recovery is idempotent even
if the recovery process itself is interrupted.
"""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

OWNER = 'smart-compass-native-publication-v1'


def sync(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def target(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or '\\' in name:
        raise RuntimeError('Unsafe native publication path: ' + name)
    path = root / name
    for entry in (path, *path.parents):
        if entry == root:
            break
        if entry.is_symlink():
            raise RuntimeError('Symlink in native publication path: ' + name)
    if path.exists() and not path.is_file():
        raise RuntimeError('Native publication target is not a file: ' + name)
    return path


def pending(transaction):
    return (transaction / 'journal.json').exists()


def recover(root, transaction):
    journal = transaction / 'journal.json'
    if not journal.exists():
        return
    record = json.loads(journal.read_text())
    if record.get('publisher') != OWNER or not isinstance(record.get('files'), dict):
        raise RuntimeError('Invalid native publication journal; retained for inspection')
    # Check all backup bytes before restoring any of them.
    for name, previous in record['files'].items():
        target(root, name)
        if previous is not None:
            backup = target(transaction / 'previous', name)
            if hashlib.sha256(backup.read_bytes()).hexdigest() != previous:
                raise RuntimeError('Native rollback backup changed: ' + name)
    for name, previous in record['files'].items():
        path = target(root, name)
        if previous is None:
            path.unlink(missing_ok=True)
            if path.parent.exists():
                sync(path.parent)
        else:
            atomic_write(path, (transaction / 'previous' / name).read_bytes())
    journal.unlink()
    sync(transaction)
    shutil.rmtree(transaction / 'previous')


def publish(root, transaction, files, retired, manifest, validate):
    """Install file bytes (manifest last), or retain the entire preceding set."""
    root, transaction = Path(root), Path(transaction)
    transaction.mkdir(parents=True, exist_ok=True)
    recover(root, transaction)
    if manifest not in files or manifest in retired:
        raise ValueError('Publication must include its manifest')
    if set(files) & set(retired):
        raise ValueError('Cannot replace and retire the same native file')
    previous = transaction / 'previous'
    # A crash before the journal was written leaves only an unused backup.
    if previous.exists():
        shutil.rmtree(previous)
    previous.mkdir()
    record = {'publisher': OWNER, 'files': {}}
    for name in sorted(set(files) | set(retired)):
        path = target(root, name)
        if path.exists():
            data = path.read_bytes()
            atomic_write(previous / name, data)
            record['files'][name] = hashlib.sha256(data).hexdigest()
        else:
            record['files'][name] = None
    for directory in sorted((p for p in previous.rglob('*') if p.is_dir()),
                            key=lambda p: len(p.parts), reverse=True):
        sync(directory)
    sync(previous)
    sync(transaction)
    atomic_write(transaction / 'journal.json', (json.dumps(record, sort_keys=True) + '\n').encode())
    try:
        for name in sorted(set(files) - {manifest}):
            atomic_write(target(root, name), files[name])
        for name in sorted(retired):
            path = target(root, name)
            path.unlink(missing_ok=True)
            if path.parent.exists():
                sync(path.parent)
        atomic_write(target(root, manifest), files[manifest])
        validate()
    except BaseException:
        recover(root, transaction)
        raise
    # The durable journal removal is the commit point. Backups can be retired
    # after a crash here without rolling the successful release back.
    (transaction / 'journal.json').unlink()
    sync(transaction)
    shutil.rmtree(previous)
