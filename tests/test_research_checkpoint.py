# 파일명: tests/test_research_checkpoint.py
# 임포트
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# 실제 저장·복원 블록을 직접 실행한다.
WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/continuous-research.yml'


def block(name):
    text = WORKFLOW.read_text(encoding='utf-8')
    section = text.split('      - name: ' + name + '\n', 1)[1]
    code = section.split("          @'\n", 1)[1].split("          '@ | python -", 1)[0]
    return '\n'.join(line[10:] for line in code.splitlines())


# 저장, 실패 기록, 재개, 변조 거부 검증
class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'workspace'
        self.results = self.root / 'strategy_lab/results'
        self.results.mkdir(parents=True)
        self.state = self.base / 'runner/research-state'
        self.state.mkdir(parents=True)
        self.key = os.urandom(32)
        self.env = {'BBOT_LOCAL_ROOT': str(self.root), 'RUNNER_TEMP': str(self.base / 'runner'),
                    'STATE_KEY': base64.b64encode(self.key).decode(), 'BBOT_INITIAL_SEED': '0',
                    'GITHUB_STEP_SUMMARY': str(self.base / 'summary.md')}
        self.context = patch.dict(os.environ, self.env)
        self.context.start()
        self.addCleanup(self.context.stop)
        self.restore_code = block('Restore encrypted persistent research branch')
        self.save_code = block('Save encrypted original checkpoint for next hosted run')
        (self.results / 'pass.json').write_text('{"status":"PASS"}')
        (self.results / 'fail.json').write_text('{"status":"FAIL","reason":"gate"}')
        (self.results / 'candidate.py').write_text('# original candidate\n')

    def save(self):
        exec(compile(self.save_code, 'workflow-save', 'exec'), {})

    def restore(self):
        exec(compile(self.restore_code, 'workflow-restore', 'exec'), {})

    def index(self):
        data = (self.state / 'checkpoint.index.enc').read_bytes()
        return json.loads(AESGCM(self.key).decrypt(data[:12], data[12:], b'BBOT_RESEARCH_INDEX_V3'))

    def test_pass_fail_and_candidate_round_trip(self):
        expected = {p.name: p.read_bytes() for p in self.results.iterdir()}
        self.save()
        for name in expected:
            (self.results / name).unlink()
        self.restore()
        for name, data in expected.items():
            self.assertEqual((self.results / name).read_bytes(), data)
        self.assertNotIn(b'candidate.py', (self.state / 'checkpoint.index.enc').read_bytes())

    def test_unchanged_files_reuse_ciphertext_and_changed_failure_is_retained(self):
        self.save()
        self.restore()
        before = self.index()
        objects = {p.name: p.read_bytes() for p in (self.state / 'objects').iterdir()}
        (self.results / 'fail.json').write_text('{"status":"FAIL","reason":"new gate"}')
        self.save()
        after = self.index()
        name = 'strategy_lab/results/pass.json'
        self.assertEqual(before['files'][name], after['files'][name])
        name = 'strategy_lab/results/fail.json'
        self.assertNotEqual(before['files'][name]['sha256'], after['files'][name]['sha256'])
        for name, data in objects.items():
            self.assertEqual((self.state / 'objects' / name).read_bytes(), data)

    def test_object_corruption_and_missing_object_fail_closed(self):
        self.save()
        record = self.index()['files']['strategy_lab/results/fail.json']
        path = self.state / 'objects' / (record['objects'][0] + '.enc')
        original = path.read_bytes()
        path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
        with self.assertRaises(SystemExit):
            self.restore()
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.restore()

    def test_wrong_key_rejected(self):
        self.save()
        with patch.dict(os.environ, {'STATE_KEY': base64.b64encode(os.urandom(32)).decode()}):
            with self.assertRaises(InvalidTag):
                self.restore()

    def test_legacy_checkpoint_migrates_without_deleting_history(self):
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('strategy_lab/results/.hosted_mtimes.json', '{}')
            archive.writestr('strategy_lab/results/legacy-fail.json', '{"status":"FAIL"}')
        nonce = os.urandom(12)
        cipher = nonce + AESGCM(self.key).encrypt(nonce, memory.getvalue(), b'BBOT_RESEARCH_STATE_V1')
        old = self.state / 'checkpoint.000.enc'
        old.write_bytes(cipher)
        (self.state / 'checkpoint.json').write_text(json.dumps({'schema':'BBOT_ENCRYPTED_CHECKPOINT_V2', 'parts':1, 'sha256':hashlib.sha256(cipher).hexdigest()}))
        self.restore()
        self.save()
        self.assertEqual(old.read_bytes(), cipher)
        self.assertIn('strategy_lab/results/legacy-fail.json', self.index()['files'])

    def test_large_file_split_and_restore(self):
        payload = os.urandom(31 * 1024 * 1024)
        target = self.results / 'large.bin'
        target.write_bytes(payload)
        self.save()
        record = self.index()['files']['strategy_lab/results/large.bin']
        self.assertEqual(len(record['objects']), 2)
        self.assertTrue(all(p.stat().st_size <= 30 * 1024**2 for p in (self.state / 'objects').iterdir()))
        target.unlink()
        self.restore()
        self.assertEqual(target.read_bytes(), payload)


if __name__ == '__main__':
    unittest.main()
