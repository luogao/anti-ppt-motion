#!/usr/bin/env python3
"""Create the shared teaching narration on macOS; never modifies existing assets."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TEXTS = {
    'T1': ['一个任务时，等待不明显。', '任务同时涌入，处理速度没变，', '等待就排成了队。'],
    'T2': ['同样三项任务，', 'A花三十秒，B花十秒。', '比较时，长度和时间要对应。'],
    'T3': ['这三个文件，原来要逐个移动。', '选中之后，一次归到同一个项目，', '状态也更新了。'],
}

def duration(file):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(file)], text=True).strip())

def create(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'manifest.json').exists():
        raise FileExistsError('Assets already exist; use a new output directory.')
    manifest = {'kind': 'synthetic-teaching-inputs', 'voice': 'macOS Tingting, 150 words/min', 'fps': 30, 'frames': 300, 'width': 1080, 'height': 1440, 'topics': {}}
    for topic, clauses in TEXTS.items():
        folder = root / topic
        folder.mkdir()
        lengths = []
        for index, text in enumerate(clauses):
            raw = folder / f'clause-{index}.aiff'
            subprocess.run(['say', '-v', 'Tingting', '-r', '150', '-o', str(raw), text], check=True)
            lengths.append(duration(raw))
        concat = folder / 'clauses.txt'
        concat.write_text(''.join(f"file 'clause-{i}.aiff'\n" for i in range(len(clauses))))
        speed = max(1.0, sum(lengths) / 9.5)
        output = folder / 'narration.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat), '-af', f'atempo={speed},apad', '-t', '10', '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(output)], check=True)
        cursor = 0
        cues = []
        for text, length in zip(clauses, lengths):
            end = cursor + length / speed
            cues.append({'start_s': round(cursor, 3), 'end_s': round(end, 3), 'text': text})
            cursor = end
        manifest['topics'][topic] = {'audio': f'{topic}/narration.wav', 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'duration_s': duration(output), 'tempo': speed, 'clauses': cues}
    (root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({k: {'duration_s': v['duration_s'], 'clauses': v['clauses']} for k, v in manifest['topics'].items()}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    create(parser.parse_args().output)
