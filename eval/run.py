#!/usr/bin/env python3
"""Run the fixed explicit-loading A/B comparison. Outputs and media stay outside git."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / 'examples/starter'
TOPICS = {'T1': 'queue.md', 'T2': 'comparison.md', 'T3': 'product-flow.md'}
ORDER = [('T1',1,'AB'),('T1',2,'BA'),('T2',1,'BA'),('T2',2,'AB'),('T3',1,'AB'),('T3',2,'BA')]
SCHEMA = {'type':'object','properties':{'plan':{'type':'string'},'scene_tsx':{'type':'string'}},'required':['plan','scene_tsx'],'additionalProperties':False}
BUNDLE_FILES = ['SKILL.md','references/motion-methods.md','references/anti-patterns.md','references/review.md']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def skill_bundle():
    return '\n\n'.join(f'### {name}\n'+(ROOT/name).read_text() for name in BUNDLE_FILES)


def common_prompt(topic, cues):
    return ((ROOT/'eval/baseline.md').read_text()+'\n\n'+(ROOT/'examples'/TOPICS[topic]).read_text()
        +'\n\nActual shared narration clause timings:\n'+json.dumps(cues,ensure_ascii=False)
        +'\n\nThe shared Root adds narration.wav and registers Bench (1080x1440,30fps,300 frames).'
        +' Export a React component named Scene from src/Scene.tsx. React 18.3.1 / Remotion 4.0.534.'
        +' For T3 you may use public/product-flow.mp4 (muted teaching fixture); the same source is available in both arms.'
        +'\nReturn JSON with plan and scene_tsx. Write the complete source in scene_tsx, with no Markdown fences.'
        +' Make a polished, coherent and readable motion video for the brief. Keep the source under 220 lines and the plan under 6 sentences. Use inline CSS/SVG and installed dependencies.'
        +' Do not call tools, read files, start browsers, install software or spawn other agents. Everything needed is in this input.')


def generation_prompt(common, arm, bundle):
    assert arm in ('A','B')
    return common + ('\n\nExplicitly loaded anti-ppt-motion Skill and references:\n'+bundle if arm=='B' else '')


def validate_events(text):
    events = [json.loads(line) for line in text.splitlines() if line.strip()]
    forbidden = {'command_execution','file_change','mcp_tool_call','web_search','tool_call'}
    observed = [e.get('item',{}).get('type') for e in events]
    if any(kind in forbidden for kind in observed):
        raise ValueError('PROTOCOL: the text-only generation invoked a tool')
    turns = [e for e in events if e.get('type')=='turn.completed']
    if not turns:
        raise ValueError('No completed model turn')
    return {'usage':turns[-1].get('usage',{}),'observed_item_types':observed,'transport_errors':[e.get('message','') for e in events if e.get('type')=='error']}


def command(argv, cwd, log, timeout=600, stdin=None):
    start=time.monotonic()
    with open(str(log)+'.stderr','w') as err, open(log,'w') as stdout:
        proc=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                              stdout=stdout,stderr=err,text=True,start_new_session=True)
        try:
            proc.communicate(stdin,timeout=timeout)
            rc=proc.returncode
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate()
            rc=124
    return {'exit_code':rc,'elapsed_s':round(time.monotonic()-start,3)}


def model_call(folder, prompt, model, images):
    folder.mkdir()
    (folder/'prompt.txt').write_text(prompt)
    (folder/'schema.json').write_text(json.dumps(SCHEMA))
    output=folder/'response.json'
    argv=['codex','--no-daemon','-a','never','exec','--ignore-user-config','--ephemeral',
          '--skip-git-repo-check','--sandbox','read-only','--model',model,
          '-c','model_reasoning_effort="medium"','-c','features.skip_host_skill_discovery=true',
          '-c','features.memories=false','-c','features.plugins=false','-c','features.multi_agent=false',
          '-c','project_doc_max_bytes=0','--json','--output-schema',str(folder/'schema.json'),
          '--output-last-message',str(output),'-C',str(folder)]
    for image in images:argv.extend(['--image',str(image)])
    argv.append('-')
    result=command(argv,folder,folder/'events.jsonl',stdin=prompt)
    if result['exit_code']:
        return None,{**result,'status':'generation_infra_failed'}
    try:
        observed=validate_events((folder/'events.jsonl').read_text())
        answer=json.loads(output.read_text())
        if set(answer)!= {'plan','scene_tsx'} or not isinstance(answer['scene_tsx'],str):
            raise ValueError('Invalid response shape')
        if 'export' not in answer['scene_tsx'] or 'Scene' not in answer['scene_tsx']:
            raise ValueError('Scene export missing')
    except (ValueError,OSError) as error:
        return None,{**result,'status':'protocol_or_response_failed','error':str(error)}
    return answer,{**result,**observed,'prompt_sha256':sha(prompt.encode()),'status':'generated'}


def render(folder, args):
    check=command([str(STARTER/'node_modules/.bin/tsc'),'--noEmit'],folder,folder/'typecheck.log')
    if check['exit_code']:
        return {'status':'typecheck_failed','typecheck':check}
    renderer=[str(STARTER/'node_modules/.bin/remotion'),'render','src/index.ts','Bench','video.mp4',
              '--codec','h264','--crf','18','--concurrency','2','--log','error','--browser-executable',args.browser]
    if args.browser_lock:
        renderer=['bash',args.browser_lock,'run','--task','anti-ppt-'+folder.parent.name+'-'+folder.name,'--est','3','--tree',str(folder),'--']+renderer
    result=command(renderer,folder,folder/'render.log')
    if result['exit_code']:
        return {'status':'render_failed','typecheck':check,'render':result}
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(folder/'video.mp4')],text=True))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=next((s for s in info['streams'] if s['codec_type']=='audio'),None)
    if (video['width'],video['height'],int(video.get('nb_frames',0))) != (1080,1440,300) or audio is None:
        return {'status':'integrity_failed','typecheck':check,'render':result,'probe':info}
    subprocess.run(['ffmpeg','-v','error','-i',str(folder/'video.mp4'),'-vf','select=eq(n\\,0)+eq(n\\,150)+eq(n\\,285)',
                    '-fps_mode','passthrough',str(folder/'frame-%02d.png')],check=True)
    return {'status':'rendered','typecheck':check,'render':result,'video_sha256':sha((folder/'video.mp4').read_bytes()),
            'video':{k:video.get(k) for k in ['width','height','r_frame_rate','nb_frames','duration','codec_name']},
            'audio':{k:audio.get(k) for k in ['duration','sample_rate','channels','codec_name']},
            'decoded_audio_sha256':sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(folder/'video.mp4'),'-map','0:a:0','-ac','1','-ar','48000','-f','s16le','-']))}


def stage(task, name, answer, args, skill_resource=None):
    folder=task/name
    shutil.copytree(STARTER/'src',folder/'src')
    for file in ['package.json','tsconfig.json','package-lock.json']:
        shutil.copy2(STARTER/file,folder/file)
    (folder/'node_modules').symlink_to(STARTER/'node_modules',target_is_directory=True)
    (folder/'public').mkdir()
    shutil.copy2(task/'narration.wav',folder/'public/narration.wav')
    if (task/'product-flow.mp4').exists():shutil.copy2(task/'product-flow.mp4',folder/'public/product-flow.mp4')
    (folder/'src/Scene.tsx').write_text(answer['scene_tsx'])
    if skill_resource is not None:
        shutil.copy2(skill_resource,folder/'src/scene-world.tsx')
    (folder/'plan.md').write_text(answer['plan'])
    return render(folder,args)


def run_task(topic,rep,arm,root,assets,manifest,args,bundle):
    task=root/f'{topic}-r{rep}-{arm}'
    task.mkdir()
    audio=assets/manifest['topics'][topic]['audio']
    assert sha(audio.read_bytes())==manifest['topics'][topic]['sha256']
    shutil.copy2(audio,task/'narration.wav')
    if topic=='T3':
        fixture=assets/'T3/product-flow.mp4'
        assert sha(fixture.read_bytes())==manifest['topics']['T3']['fixture']['sha256']
        shutil.copy2(fixture,task/'product-flow.mp4')
    common=common_prompt(topic,manifest['topics'][topic]['clauses'])
    prompt=generation_prompt(common,arm,bundle)
    result={'topic':topic,'repeat':rep,'arm':arm,'common_sha256':sha(common.encode()),'audio_sha256':sha(audio.read_bytes()),'stages':{}}
    print(f'START {task.name}',flush=True)
    answer,model=model_call(task/'initial',prompt,args.model,[])
    result['stages']['initial']={'model':model}
    if answer is not None:
        initial=stage(task,'initial',answer,args)
        result['stages']['initial'].update(initial)
        images=sorted((task/'initial').glob('frame-*.png'))
        diagnostics='\n'.join((task/'initial'/f).read_text()[-6000:] for f in ['typecheck.log','typecheck.log.stderr','render.log','render.log.stderr'] if (task/'initial'/f).exists())
        review=prompt+'\n\nOne allowed review pass. Current plan:\n'+answer['plan']+'\nCurrent source:\n'+answer['scene_tsx']
        review+='\nTechnical diagnostics:\n'+diagnostics+'\nThree attached frames (when available) are at 0, 5 and 9.5 seconds. Check readability, factual consistency and clarity. Improve issues you can observe; preserve working facts. You have not watched the complete video; do not claim playback or human comprehension validation. Return the complete revised source and a brief account of observed changes. No tools.'
        revised,review_model=model_call(task/'final',review,args.model,images)
        result['stages']['final']={'model':review_model}
        if revised is not None:result['stages']['final'].update(stage(task,'final',revised,args))
    final=result['stages'].get('final',{})
    result['status']=final.get('status',final.get('model',model).get('status','failed'))
    (task/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(f'DONE {task.name} {result["status"]}',flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['pilot','formal'],required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model',default='gpt-6.1-sol')
    parser.add_argument('--browser',required=True)
    parser.add_argument('--browser-lock')
    args=parser.parse_args()
    args.assets=args.assets.resolve();args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=True)
    if any(args.output.iterdir()):raise SystemExit('Use a new empty output directory.')
    manifest=json.loads((args.assets/'manifest.json').read_text())
    bundle=skill_bundle()
    files=BUNDLE_FILES+['eval/baseline.md','eval/protocol.md','eval/run.py']+['examples/'+x for x in TOPICS.values()]
    files+=['examples/starter/'+x for x in ['package.json','package-lock.json','tsconfig.json','src/index.ts','src/Root.tsx','src/Scene.tsx','src/Fixture.tsx']]
    frozen={name:sha((ROOT/name).read_bytes()) for name in files}
    meta={'started_at_utc':datetime.now(timezone.utc).isoformat(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'node':subprocess.check_output(['node','--version'],text=True).strip(),'phase':args.phase,'model':args.model,'reasoning_effort':'medium','cli':subprocess.check_output(['codex','--version'],text=True).strip(),
          'skill_sha256':sha(bundle.encode()),'files':frozen,'asset_manifest_sha256':sha((args.assets/'manifest.json').read_bytes()),
          'method':'explicit-context-loading; tool-free structured code generation; uniform frame-assisted revision',
          'limitations':['Host discovery skip uses an under-development CLI flag.','No human quality ratings at generation time.','Review model receives frames, not complete video playback.'],
          'results':[]}
    (args.output/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    order=[('T1',0,'AB')] if args.phase=='pilot' else ORDER
    for topic,rep,arms in order:
        for arm in arms:
            if any(sha((ROOT/name).read_bytes())!=value for name,value in frozen.items()):raise RuntimeError('Frozen input changed; stop batch.')
            result=run_task(topic,rep,arm,args.output,args.assets,manifest,args,bundle)
            meta['results'].append(result)
            (args.output/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
            if 'generation_infra_failed' in json.dumps(result):
                meta['batch_status']='BLOCKED_INFRA'
                (args.output/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
                raise RuntimeError('Generation infrastructure failed; batch stopped without a quality verdict.')
            if 'protocol_or_response_failed' in json.dumps(result):raise RuntimeError('Protocol or response failed; audit before continuing.')
    print('BATCH COMPLETE',args.phase,flush=True)

if __name__=='__main__':main()
