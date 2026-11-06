import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('resource_runner',ROOT/'eval/run.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class ResourceStageTests(unittest.TestCase):
    def test_only_skill_arm_receives_exact_resource_and_scene_is_not_rewritten(self):
        answer={'scene_tsx':'export const Scene=()=>null;','plan':'test fixture'}
        with tempfile.TemporaryDirectory() as d,patch.object(r,'render',return_value={'status':'fixture-only'}):
            for arm in 'AB':
                task=Path(d)/arm;task.mkdir();(task/'initial').mkdir();(task/'narration.wav').write_bytes(b'fixture')
                r.stage(task,'initial',answer,None,ROOT/'assets/scene-world.tsx' if arm=='B' else None)
                source=task/'initial/src/Scene.tsx';asset=task/'initial/src/scene-world.tsx'
                self.assertEqual(source.read_text(),answer['scene_tsx'])
                self.assertEqual(asset.exists(),arm=='B')
                if arm=='B':self.assertEqual(asset.read_bytes(),(ROOT/'assets/scene-world.tsx').read_bytes())

if __name__=='__main__':unittest.main()
