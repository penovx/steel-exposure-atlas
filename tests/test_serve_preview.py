from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from pipeline.serve_preview import ASSETS, REQUIRED_CONTROLS, handler_for, load_snapshot


class LocalPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in ASSETS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}', encoding='utf-8')
        controls = ''.join(f'<button id="{name}"></button>' for name in REQUIRED_CONTROLS)
        (self.root / 'index.html').write_text(
            f'<html><body><h1>Test atlas</h1>{controls}</body></html>', encoding='utf-8'
        )

    def snapshot(self):
        with patch('pipeline.serve_preview.git_value', return_value='test-only'):
            return load_snapshot(self.root)

    def test_identity_badge_does_not_modify_source_files(self) -> None:
        original = (self.root / 'index.html').read_bytes()
        files, info = self.snapshot()
        self.assertIn(b'PREVIEW', files['/'][0])
        self.assertIn(info['ui_id'].encode(), files['/'][0])
        self.assertEqual((self.root / 'index.html').read_bytes(), original)
        self.assertEqual(info['source_file_sha256']['index.html'], hashlib.sha256(original).hexdigest())
        self.assertFalse(info['data_publication_approved_by_this_tool'])

    def test_snapshot_bytes_survive_disk_change(self) -> None:
        files, first = self.snapshot()
        (self.root / 'src/app.js').write_text('changed', encoding='utf-8')
        _, second = self.snapshot()
        self.assertEqual(files['/src/app.js'][0], b'{}')
        self.assertNotEqual(first['ui_id'], second['ui_id'])

    def test_missing_navigation_is_a_startup_error(self) -> None:
        (self.root / 'index.html').write_text('<h1>Old</h1>', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'navigation update'):
            self.snapshot()

    def test_missing_data_is_a_startup_error(self) -> None:
        (self.root / 'public/data/gist-plants.v1.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Required local preview file is missing'):
            self.snapshot()

    def test_http_uses_snapshot_no_cache_and_allowlist(self) -> None:
        files, info = self.snapshot()
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(files, str(info['ui_id'])))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        client = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
        try:
            for method, path, expected in [
                ('GET', '/?preview=check', 200), ('HEAD', '/src/app.js', 200),
                ('GET', '/.git/config', 404), ('GET', '/%2e%2e/index.html', 404),
                ('GET', '/public/data/', 404), ('GET', '/favicon.ico', 204),
                ('GET', '/__preview__/status', 200),
            ]:
                with self.subTest(method=method, path=path):
                    client.request(method, path)
                    response = client.getresponse()
                    self.assertEqual(response.status, expected)
                    body = response.read()
                    if expected == 200:
                        self.assertIn('no-store', response.getheader('Cache-Control'))
                        self.assertEqual(response.getheader('X-Atlas-Preview'), info['ui_id'])
                    if method == 'HEAD':
                        self.assertEqual(body, b'')
                    if path == '/__preview__/status':
                        self.assertEqual(json.loads(body)['ui_id'], info['ui_id'])
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
