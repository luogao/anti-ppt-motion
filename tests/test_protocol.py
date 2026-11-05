import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('runner',ROOT/'eval/run.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class ProtocolTests(unittest.TestCase):
    def test_treatment_is_only_added_context(self):
        common=r.common_prompt('T1',[]);bundle=r.skill_bundle()
        a=r.generation_prompt(common,'A',bundle);b=r.generation_prompt(common,'B',bundle)
        self.assertEqual(a,common)
        self.assertTrue(b.startswith(a))
        self.assertNotIn('Explicitly loaded anti-ppt-motion Skill',a)
        self.assertIn(bundle,b)
    def test_formal_pairs_are_balanced(self):
        cases=[(t,rep,arm) for t,rep,order in r.ORDER for arm in order]
        self.assertEqual(len(cases),12)
        self.assertEqual(len(set(cases)),12)
        for topic in r.TOPICS:
            for arm in 'AB':self.assertEqual(sum(t==topic and a==arm for t,_,a in cases),2)
    def test_tool_use_invalidates_text_only_trial(self):
        events=[{'type':'item.completed','item':{'type':'command_execution'}},{'type':'turn.completed','usage':{}}]
        with self.assertRaises(ValueError):r.validate_events('\n'.join(map(json.dumps,events)))
    def test_no_completion_is_not_success(self):
        with self.assertRaises(ValueError):r.validate_events('{"type":"turn.failed"}')
    def test_usage_is_actual_event_data(self):
        out=r.validate_events('{"type":"turn.completed","usage":{"input_tokens":123,"output_tokens":45}}')
        self.assertEqual(out['usage']['input_tokens'],123)
    def test_linked_skill_references_stay_local_and_exist(self):
        import re
        for path in re.findall(r'\]\((references/[^)]+)\)',(ROOT/'SKILL.md').read_text()):
            target=(ROOT/path).resolve()
            self.assertTrue(target.is_relative_to(ROOT))
            self.assertTrue(target.is_file())

if __name__=='__main__':unittest.main()
