#!/usr/bin/env python3
"""Normalize rights-cleared narration and validate supplied clause timings."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TOPICS=('T1','T2','T3')

def validate_clauses(clauses,duration):
    if not clauses:raise ValueError('Supply actual clause timings; no inferred alignment.')
    previous=0.0
    for c in clauses:
        start=float(c['start_s']);end=float(c['end_s'])
        if not c.get('text') or start<previous or not start<end or end>duration+0.05:
            raise ValueError('Clause timings must be ordered, non-overlapping and within the source audio.')
        previous=end


def import_assets(config,output):
    config=Path(config);root=Path(output)
    data=json.loads(config.read_text())
    if data.get('redistribution_confirmed') is not True:
        raise ValueError('Public inputs require explicit confirmation of redistribution rights.')
    if set(data.get('topics',{})) != set(TOPICS):raise ValueError('Supply exactly T1, T2 and T3.')
    if root.exists() and any(root.iterdir()):raise FileExistsError('Use a new empty assets directory.')
    root.mkdir(parents=True,exist_ok=True)
    result={'kind':'rights-cleared-teaching-inputs','voice_source':data.get('voice_source','owner-supplied'),
            'redistribution_confirmed':True,'fps':30,'frames':300,'width':1080,'height':1440,'topics':{}}
    for topic in TOPICS:
        item=data['topics'][topic];source=Path(item['audio'])
        if not source.is_absolute():source=config.parent/source
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(source)],text=True))
        if not 0<duration<=10.05:raise ValueError('Narration must fit 10 seconds; do not silently truncate or retime.')
        validate_clauses(item['clauses'],duration)
        folder=root/topic;folder.mkdir();target=folder/'narration.wav'
        subprocess.run(['ffmpeg','-v','error','-i',str(source),'-af','apad','-t','10','-ar','48000','-ac','1','-c:a','pcm_s16le',str(target)],check=True)
        result['topics'][topic]={'audio':f'{topic}/narration.wav','sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                                 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'duration_s':10.0,'clauses':item['clauses']}
    (root/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_json');p.add_argument('output');a=p.parse_args();import_assets(a.input_json,a.output)
