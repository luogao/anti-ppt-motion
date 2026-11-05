#!/usr/bin/env python3
"""One post-v0.1 diagnostic pair; same generation helper, new 30s common task."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from run import ROOT, STARTER, BUNDLE_FILES, command, generation_prompt, model_call


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_stage(folder, answer, assets, args, common_root):
    shutil.copytree(STARTER/'src', folder/'src')
    (folder/'src/Root.tsx').write_text(common_root)
    (folder/'src/Scene.tsx').write_text(answer['scene_tsx'])
    (folder/'plan.md').write_text(answer['plan'])
    for name in ('package.json', 'package-lock.json', 'tsconfig.json'):
        shutil.copy2(STARTER/name, folder/name)
    (folder/'node_modules').symlink_to((STARTER/'node_modules').resolve(), target_is_directory=True)
    (folder/'public').mkdir();shutil.copy2(assets/'narration.wav', folder/'public/narration.wav')
    check = command([str(STARTER/'node_modules/.bin/tsc'), '--noEmit'], folder, folder/'typecheck.log')
    if check['exit_code']:return {'status':'typecheck_failed','typecheck':check}
    argv = [str(STARTER/'node_modules/.bin/remotion'),'render','src/index.ts','Bench','video.mp4',
            '--codec','h264','--crf','18','--concurrency','2','--log','error','--browser-executable',args.browser]
    argv = ['bash',args.browser_lock,'run','--task','scene-pilot-'+folder.parent.name+'-'+folder.name,
            '--est','3','--tree',str(folder),'--']+argv
    rendered = command(argv, folder, folder/'render.log')
    if rendered['exit_code']:return {'status':'render_failed','typecheck':check,'render':rendered}
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(folder/'video.mp4')],text=True))
    video = next(s for s in probe['streams'] if s['codec_type']=='video')
    if (video['width'],video['height'],int(video['nb_frames']))!=(1080,1440,900):
        return {'status':'integrity_failed','probe':probe}
    select = '+'.join(f'eq(n\\,{n})' for n in (0,150,300,450,600,750,885))
    subprocess.run(['ffmpeg','-v','error','-i',str(folder/'video.mp4'),'-vf','select='+select,
                    '-fps_mode','passthrough',str(folder/'frame-%02d.png')],check=True)
    audio = subprocess.check_output(['ffmpeg','-v','error','-i',str(folder/'video.mp4'),'-map','0:a:0','-ac','1','-ar','48000','-f','s16le','-'])
    return {'status':'rendered','typecheck':check,'render':rendered,'video_sha256':sha(folder/'video.mp4'),
            'decoded_audio_sha256':hashlib.sha256(audio).hexdigest(),'probe':probe}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--browser',required=True);parser.add_argument('--browser-lock',required=True)
    args=parser.parse_args();args.assets=args.assets.resolve();args.output=args.output.resolve()
    if args.output.exists() and any(args.output.iterdir()):raise FileExistsError('Use a new empty output directory.')
    args.output.mkdir(parents=True,exist_ok=True)
    inputs=json.loads((args.assets/'manifest.json').read_text())
    assert inputs['redistribution_confirmed'] is True and inputs['frames']==900
    assert sha(args.assets/'narration.wav')==inputs['audio_sha256']
    files=BUNDLE_FILES+['references/scene-grammar.md','examples/scene-pilot.md','eval/follow-up.md',
                       'eval/baseline.md','eval/run.py','eval/run_scene_pilot.py']
    files+=['examples/starter/'+n for n in ('package.json','package-lock.json','tsconfig.json','src/index.ts','src/Root.tsx','src/Scene.tsx')]
    frozen={name:sha(ROOT/name) for name in files}
    bundle='\n\n'.join(f'### {name}\n'+(ROOT/name).read_text() for name in BUNDLE_FILES+['references/scene-grammar.md'])
    common=(ROOT/'eval/baseline.md').read_text()+'\n\n'+(ROOT/'examples/scene-pilot.md').read_text()
    common+='\nActual common narration clauses:\n'+json.dumps(inputs['clauses'],ensure_ascii=False)
    common+='\nCommon Root: Bench, 1080x1440,30fps,900frames; sole Audio is narration.wav. React18.3.1/Remotion4.0.534.'
    common+='\nReturn JSON {plan:string,scene_tsx:string}; export Scene. Complete source under 320 lines, concise plan under 12 lines. Use installed dependencies and inline CSS/SVG. No tools, files, browsers, installation or other agents. Everything needed is in this input.'
    common_root=(STARTER/'src/Root.tsx').read_text()
    assert common_root.count('durationInFrames={300}')==1
    common_root=common_root.replace('durationInFrames={300}','durationInFrames={900}')
    (args.output/'common-Root.tsx').write_text(common_root)
    meta={'kind':'post-hoc diagnostic pilot, not formal confirmation','started_at_utc':datetime.now(timezone.utc).isoformat(),
          'model':'gpt-6.1-sol','effort':'medium','source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'common_prompt_sha256':hashlib.sha256(common.encode()).hexdigest(),'files':frozen,
          'input_manifest_sha256':sha(args.assets/'manifest.json'),'results':[],'human_blind_ratings':0}
    (args.output/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    for arm in 'BA':
        assert all(sha(ROOT/name)==digest for name,digest in frozen.items()),'Frozen source changed'
        task=args.output/arm;task.mkdir();prompt=generation_prompt(common,arm,bundle)
        result={'arm':arm,'stages':{}}
        print('START',arm,flush=True)
        answer,model=model_call(task/'initial',prompt,meta['model'],[])
        result['stages']['initial']={'model':model}
        if answer is not None:
            result['stages']['initial'].update(render_stage(task/'initial',answer,args.assets,args,common_root))
            logs='\n'.join(p.read_text()[-5000:] for p in (task/'initial').glob('*.log*'))
            review=prompt+'\nOne allowed equal-budget review. Current plan:\n'+answer['plan']+'\nCurrent source:\n'+answer['scene_tsx']
            review+='\nTechnical diagnostics:\n'+logs+'\nFrames at 0,5,10,15,20,25,29.5s. Inspect composition, identity, factual consistency and scene joins visible in these frames. You have not watched complete playback; do not claim timing or human understanding passed. Return complete revised source and concise change notes. No tools.'
            revised,review_model=model_call(task/'final',review,meta['model'],sorted((task/'initial').glob('frame-*.png')))
            result['stages']['final']={'model':review_model}
            if revised is not None:result['stages']['final'].update(render_stage(task/'final',revised,args.assets,args,common_root))
        final=result['stages'].get('final',{});result['status']=final.get('status',final.get('model',model)['status'])
        (task/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));meta['results'].append(result)
        (args.output/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        print('DONE',arm,result['status'],flush=True)
        if 'generation_infra_failed' in json.dumps(result) or 'protocol_or_response_failed' in json.dumps(result):
            raise RuntimeError('Pilot stopped on infrastructure/protocol failure; no quality verdict.')
    print('PILOT COMPLETE',flush=True)


if __name__=='__main__':main()
