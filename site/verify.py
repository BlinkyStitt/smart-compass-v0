"""Verify a complete local/live Pages artifact, or an explicitly isolated UI study.

The study mode tests the calculator and playback implementation with real sample
files and existing clips. It cannot satisfy the full local/live release gates.
"""

import argparse
from contextlib import contextmanager
import fcntl
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request

from publication import verify

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent


@contextmanager
def server(directory):
    class Handler(SimpleHTTPRequestHandler):
        def send_head(self):
            self.byte_range = None
            path = Path(self.translate_path(self.path))
            header = self.headers.get('Range')
            if not header or not path.is_file():
                return super().send_head()
            # Chromium seeks MP4s using byte ranges. The standard Python server
            # ignores Range, so it is not a faithful media playback fixture.
            size = path.stat().st_size
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', header)
            if match and any(match.groups()):
                first, last = match.groups()
                start = int(first) if first else max(0, size - int(last))
                end = min(int(last), size - 1) if first and last else size - 1
                if 0 <= start <= end < size:
                    stream = path.open('rb')
                    stream.seek(start)
                    self.byte_range = (start, end)
                    self.send_response(206)
                    self.send_header('Content-Type', self.guess_type(str(path)))
                    self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                    self.send_header('Content-Length', str(end - start + 1))
                    self.end_headers()
                    return stream
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None

        def copyfile(self, source, output):
            if self.byte_range is None:
                return super().copyfile(source, output)
            remaining = self.byte_range[1] - self.byte_range[0] + 1
            while remaining:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    raise OSError('Media file changed while serving a range')
                output.write(chunk)
                remaining -= len(chunk)

        def handle(self):
            try:
                super().handle()
            except (BrokenPipeError, ConnectionResetError):
                # Chromium cancels in-flight media ranges when a context closes.
                pass

        def log_message(self, *args):
            pass

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Accept-Ranges', 'bytes')
            super().end_headers()
    http = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(directory)))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{http.server_port}/'
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


def fixture(directory):
    for name in ('calculator.js', 'energy.mjs', 'electrical-inputs.json', 'styles.css', 'app.js'):
        shutil.copyfile(HERE / name, directory / name)
    samples = ROOT / '.build/energy-samples'
    shutil.copyfile(samples / 'manifest.json', directory / 'pattern-samples.json')
    (directory / 'pattern-data').mkdir()
    manifest = json.loads((samples / 'manifest.json').read_text())
    for record in manifest['sets']:
        if Path(record['file']).name != record['file']:
            raise ValueError('Unsafe study sample path')
        shutil.copyfile(samples / record['file'], directory / 'pattern-data' / record['file'])
    for name, source in [('narrow', 'designs/stacked/exports/infinity-rainbow.mp4'),
                         ('silver', 'designs/stacked/exports/infinity-rainbow-silver.mp4')]:
        shutil.copyfile(ROOT / source, directory / (name + '.mp4'))
    (directory / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Calculator study fixture</title>
<link rel="stylesheet" href="styles.css"><script src="app.js" defer></script>
<script src="calculator.js" type="module"></script><main class="wrap">
<h1>Isolated calculator and playback study — not a release</h1>
<section id="films" data-player data-autoplay><div class="film"><video controls autoplay muted loop playsinline preload="metadata" src="narrow.mp4" aria-label="Narrow rainbow"></video><a href="narrow.mp4">Open narrow MP4</a></div>
<a href="silver.mp4">Open silver MP4</a><button id="play" data-play>Play</button><button id="replay" data-replay>Restart</button>
<p id="play-status" class="play-status" role="status"></p></section><section id="energy-calculator" class="energy-calculator" aria-label="One-cell energy calculator"></section>
</main></html>''')


def probe(url, directory, *, study=False, webkit=False):
    env = dict(os.environ)
    env.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / '.build/browser-cache'))
    checks = [('browser_verify.mjs', env, 180)]
    if not study:
        checks.append(('test_layout.cjs', env, 180))
    if webkit:
        # Linux WebKit uses software video decoding on hosted runners.
        checks.append(('test_layout.cjs', dict(env, GALLERY_BROWSER='webkit'), 360))
    for script, environment, timeout in checks:
        command = ['node', str(HERE / script), url, str(directory)]
        with subprocess.Popen(command, cwd=ROOT, env=environment) as process:
            try:
                result = process.wait(timeout=timeout)
            except BaseException:
                # Playwright's SIGTERM handler closes its detached browser group.
                # subprocess.run(timeout=...) sends SIGKILL and bypasses that cleanup.
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                raise
            if result:
                raise subprocess.CalledProcessError(result, command)


def live(url, expected):
    record = verify(expected)
    base = url.rstrip('/') + '/'
    if urllib.parse.urlparse(base).scheme not in ('https', 'http'):
        raise ValueError('Live URL must use HTTP or HTTPS')
    def fetch(name):
        request = urllib.request.Request(urllib.parse.urljoin(base, name) + '?verify=' + record['commit'],
                                         headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    if json.loads(fetch('build-info.json')) != record:
        raise RuntimeError('Live revision, provenance or file inventory differs from the reviewed artifact')
    for name, wanted in record['files'].items():
        if hashlib.sha256(fetch(name)).hexdigest() != wanted:
            raise RuntimeError('Live asset is stale/mixed: ' + name)
    probe(base, expected)
    print('LIVE PAGES PASS: exact artifact hashes, calculator and playback')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    modes.add_parser('study')
    local = modes.add_parser('local')
    local.add_argument('--directory', type=Path, required=True)
    local.add_argument('--webkit', action='store_true', help='also run gallery playback in WebKit')
    remote = modes.add_parser('live')
    remote.add_argument('--url', required=True)
    remote.add_argument('--expected', type=Path, required=True)
    args = parser.parse_args()
    (ROOT / '.build').mkdir(exist_ok=True)
    with (ROOT / '.build/browser.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another browser verification is running') from exc
        if args.mode == 'live':
            live(args.url, args.expected.resolve())
        elif args.mode == 'local':
            directory = args.directory.resolve()
            verify(directory)
            with server(directory) as url:
                probe(url, directory, webkit=args.webkit)
            print('LOCAL PAGES PASS: complete artifact, calculator and playback')
        else:
            subprocess.run(['node', str(HERE / 'energy.mjs'), '--check'], cwd=ROOT, check=True)
            with tempfile.TemporaryDirectory(prefix='calculator-study-', dir=ROOT / '.build') as temporary:
                directory = Path(temporary)
                fixture(directory)
                with server(directory) as url:
                    probe(url, directory, study=True)
            print('STUDY BROWSER PASS: isolated calculator/playback fixtures; no assembly or release acceptance')


if __name__ == '__main__':
    main()
