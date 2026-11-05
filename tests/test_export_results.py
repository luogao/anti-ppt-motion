import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('export_results', Path(__file__).resolve().parents[1]/'eval/export_results.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def manifest():
    result = {'phase': 'formal', 'results': []}
    for topic, repeat, arm in sorted(m.EXPECTED):
        stage = {'status': 'rendered', 'decoded_audio_sha256': topic,
                 'model': {'elapsed_s': 2, 'usage': {'input_tokens': 10, 'output_tokens': 3}}}
        result['results'].append({'topic': topic, 'repeat': repeat, 'arm': arm,
                                 'common_sha256': topic, 'audio_sha256': topic, 'status': 'rendered',
                                 'stages': {'initial': copy.deepcopy(stage), 'final': copy.deepcopy(stage)}})
    return result


class ExportTests(unittest.TestCase):
    def test_bundle_cannot_escape_source_directory(self):
        for name in ('../private.txt', '/tmp/private.txt'):
            with self.assertRaises(ValueError): m.local_file(Path('/tmp/bundle'), name)

    def test_all_versions_and_actual_usage_are_counted(self):
        summary = m.summarize(manifest())
        self.assertEqual(summary['rendered_versions'], 24)
        self.assertEqual(summary['tasks'][0]['input_tokens'], 20)
        self.assertIsNone(summary['billing_usd'])

    def test_incomplete_batch_cannot_look_complete(self):
        data = manifest(); data['results'].pop()
        with self.assertRaises(ValueError): m.summarize(data)

    def test_mismatched_audio_is_rejected(self):
        data = manifest(); data['results'][0]['stages']['final']['decoded_audio_sha256'] = 'different'
        with self.assertRaises(ValueError): m.summarize(data)

    def test_failed_output_is_preserved_and_counted(self):
        data = manifest(); case = data['results'][0]
        case['status'] = 'render_failed'; case['stages']['final']['status'] = 'render_failed'
        summary = m.summarize(data)
        self.assertEqual(summary['rendered_tasks'], 11)
        self.assertEqual(summary['rendered_versions'], 23)
        self.assertEqual(summary['tasks'][0]['status'], 'render_failed')


if __name__ == '__main__': unittest.main()
