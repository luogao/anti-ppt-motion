#!/usr/bin/env python3
"""Test the actual Skill package, including its disclosed reusable source asset."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import run as r

BUNDLE=r.BUNDLE_FILES+['references/scene-grammar.md','references/shot-recipes.md','assets/scene-world.tsx']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--browser',required=True);p.add_argument('--browser-lock',required=True)
    args=p.parse_args();args.assets=args.assets.resolve();args.output=args.output.resolve()
    if args.output.exists() and any(args.output.iterdir()):raise FileExistsError('Use a new empty output directory.')
    inputs=json.loads((args.assets/'manifest.json').read_text())
    assert inputs['redistribution_confirmed'] is True and inputs['frames']==300
    audio=args.assets/inputs['topics']['T2']['audio']
    assert audio.resolve().is_relative_to(args.assets) and r.sha(audio.read_bytes())==inputs['topics']['T2']['sha256']
    files=BUNDLE+['eval/baseline.md','eval/resource-pilot.md','eval/run_resource_pilot.py','eval/run.py','examples/comparison.md']
    files+=['examples/starter/'+f for f in ['package.json','package-lock.json','tsconfig.json','src/index.ts','src/Root.tsx','src/Scene.tsx','src/Fixture.tsx']]
    frozen={f:r.sha((r.ROOT/f).read_bytes()) for f in files}
    bundle='\n\n'.join(f'### {f}\n'+(r.ROOT/f).read_text() for f in BUNDLE)
    bundle+='\n\nFor this explicit-loading test, the bundled source asset is also mounted unchanged as src/scene-world.tsx. You may import its exports. The model still authors src/Scene.tsx; do not import other absent local files.'
    common=r.common_prompt('T2',inputs['topics']['T2']['clauses'])
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'common-prompt.txt').write_text(common)
    meta={'kind':'resource-backed Skill post-hoc pilot','started_at_utc':datetime.now(timezone.utc).isoformat(),
          'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.ROOT,text=True).strip(),
          'model':'gpt-6.1-sol','effort':'medium','files':frozen,
          'common_prompt_sha256':r.sha(common.encode()),'audio_sha256':r.sha(audio.read_bytes()),
          'treatment':'B receives Skill instructions and its reusable scene-world source; not a text-only treatment',
          'results':[],'human_blind_ratings':0}
    manifest=args.output/'manifest.json';manifest.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    for arm in 'AB':
        assert all(r.sha((r.ROOT/f).read_bytes())==s for f,s in frozen.items()),'Frozen input changed'
        task=args.output/arm;task.mkdir();shutil.copy2(audio,task/'narration.wav')
        prompt=r.generation_prompt(common,arm,bundle)
        resource=r.ROOT/'assets/scene-world.tsx' if arm=='B' else None
        result={'arm':arm,'common_prompt_sha256':meta['common_prompt_sha256'],'audio_sha256':meta['audio_sha256'],
                'skill_resource_sha256':r.sha(resource.read_bytes()) if resource else None,'stages':{}}
        print('START',arm,flush=True)
        answer,model=r.model_call(task/'initial',prompt,meta['model'],[])
        result['stages']['initial']={'model':model}
        if answer is not None:
            result['stages']['initial'].update(r.stage(task,'initial',answer,args,skill_resource=resource))
            diagnostics='\n'.join((task/'initial'/f).read_text()[-6000:] for f in ['typecheck.log','typecheck.log.stderr','render.log','render.log.stderr'] if(task/'initial'/f).exists())
            review=prompt+'\nOne allowed review. Current plan:\n'+answer['plan']+'\nCurrent source:\n'+answer['scene_tsx']
            review+='\nTechnical diagnostics:\n'+diagnostics+'\nThree attached frames, when available, are at 0,5,9.5s. Check factual consistency, readability, composition and scene changes observable in these stills. You have not watched the full video. Do not claim human understanding or full playback validation. Return the complete revised source and concise change notes. No tools.'
            revised,model=r.model_call(task/'final',review,meta['model'],sorted((task/'initial').glob('frame-*.png')))
            result['stages']['final']={'model':model}
            if revised is not None:result['stages']['final'].update(r.stage(task,'final',revised,args,skill_resource=resource))
        final=result['stages'].get('final',{});result['status']=final.get('status',model['status'])
        for name in result['stages']:
            source=task/name/'src/Scene.tsx';response=task/name/'response.json'
            if source.exists():
                assert source.read_text()==json.loads(response.read_text())['scene_tsx'],'Generated Scene was altered'
                result['stages'][name]['scene_sha256']=r.sha(source.read_bytes())
        (task/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));meta['results'].append(result)
        manifest.write_text(json.dumps(meta,ensure_ascii=False,indent=2));print('DONE',arm,result['status'],flush=True)
        if 'generation_infra_failed' in json.dumps(result) or 'protocol_or_response_failed' in json.dumps(result):
            raise RuntimeError('Stop on infrastructure/protocol failure; no quality conclusion.')
    print('RESOURCE PILOT COMPLETE',flush=True)

if __name__=='__main__':main()
