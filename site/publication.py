"""Publish complete Pages directories with locking and crash rollback.

The journal is written before moving the old release. An interrupted transaction
always rolls back on the next build; no mixture of old/new files is accepted.
Only directories carrying our complete, verified file inventory are replaceable.
"""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

OWNER = 'smart-compass-pages-v1'


def inventory(directory):
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('Symlink in Pages release: ' + str(path))
        if path.is_file() and path != directory/'build-info.json':
            data = path.read_bytes()
            if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise RuntimeError('Unmaterialized LFS file: ' + str(path))
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(data).hexdigest()
    return result


def verify(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError('Pages release must be a real directory: ' + str(directory))
    try:
        record = json.loads((directory/'build-info.json').read_text())
    except (OSError, ValueError) as exc:
        raise RuntimeError('Refusing to replace an unowned Pages directory: ' + str(directory)) from exc
    if record.get('publisher') != OWNER or not record.get('files'):
        raise RuntimeError('Pages directory lacks the publication inventory: ' + str(directory))
    if record['files'] != inventory(directory):
        raise RuntimeError('Pages file inventory/hash mismatch: ' + str(directory))
    if not {'index.html', 'estimates.json', '.nojekyll'} <= set(record['files']):
        raise RuntimeError('Incomplete Pages release: ' + str(directory))
    return record


def seal(directory, record):
    record = dict(record, publisher=OWNER, files=inventory(directory))
    (directory/'build-info.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
    verify(directory)


def _sync_directory(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_journal(path, record):
    fd, temporary = tempfile.mkstemp(prefix=path.name+'-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def lock(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent/('.'+output.name+'.lock')).open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another Pages build is running for ' + str(output)) from exc
        yield


def recover(output):
    journal = output.parent/('.'+output.name+'.transaction.json')
    previous = output.parent/('.'+output.name+'.previous')
    if not journal.exists():
        if previous.exists():
            # A crash after committing the journal deletion can leave the old
            # release. Both releases must verify before retiring the older one.
            verify(output)
            verify(previous)
            shutil.rmtree(previous)
        return
    record = json.loads(journal.read_text())
    name = record.get('stage', '')
    if (record.get('publisher') != OWNER or Path(name).name != name
            or not name.startswith('.'+output.name+'.stage-')
            or not isinstance(record.get('had_previous'), bool)):
        raise RuntimeError('Invalid Pages publication journal; retained for inspection')
    stage = output.parent/name
    _restore(output, previous, stage, record['had_previous'])
    journal.unlink()
    _sync_directory(output.parent)
    if stage.exists():
        shutil.rmtree(stage)


def _restore(output, previous, stage, had_previous):
    if previous.exists():
        verify(previous)
        if output.exists():
            verify(output)
            if stage.exists():
                raise RuntimeError('Conflicting Pages recovery directories; previous release retained')
            # Rename the rejected release instead of deleting it in place. A
            # second interruption during recovery still leaves whole directories.
            os.replace(output, stage)
        os.replace(previous, output)
    elif had_previous:
        verify(output)
    elif output.exists():
        verify(output)
        if stage.exists():
            raise RuntimeError('Conflicting Pages recovery directories')
        os.replace(output, stage)


def publish(output, render, unchanged):
    output = Path(output).absolute()
    if output.is_symlink():
        raise RuntimeError('Refusing a symlink as the Pages output directory')
    output = output.resolve()
    with lock(output):
        recover(output)
        if output.is_dir() and not any(output.iterdir()):
            output.rmdir()
        if output.exists():
            verify(output)
        stage = Path(tempfile.mkdtemp(prefix='.'+output.name+'.stage-', dir=output.parent))
        journal = output.parent/('.'+output.name+'.transaction.json')
        previous = output.parent/('.'+output.name+'.previous')
        try:
            render(stage)
            verify(stage)
            unchanged()
            # Make all staged bytes durable before the publication journal.
            for path in stage.rglob('*'):
                if path.is_file():
                    with path.open('rb') as stream:
                        os.fsync(stream.fileno())
            for directory in sorted((p for p in stage.rglob('*') if p.is_dir()),
                                    key=lambda p: len(p.parts), reverse=True):
                _sync_directory(directory)
            _sync_directory(stage)
            _write_journal(journal, {'publisher': OWNER, 'stage': stage.name,
                                    'had_previous': output.exists()})
            try:
                if output.exists():
                    os.replace(output, previous)
                    _sync_directory(output.parent)
                os.replace(stage, output)
                _sync_directory(output.parent)
                journal.unlink()
                _sync_directory(output.parent)
            except BaseException:
                if journal.exists():
                    recover(output)
                elif previous.exists():
                    _restore(output, previous, stage, True)
                raise
            if previous.exists():
                shutil.rmtree(previous)
        finally:
            if stage.exists() and not journal.exists():
                shutil.rmtree(stage)
