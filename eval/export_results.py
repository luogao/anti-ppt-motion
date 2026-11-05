#!/usr/bin/env python3
"""Export the complete formal batch through a public-file allowlist."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {(t, r, a) for t in ('T1', 'T2', 'T3') for r in (1, 2) for a in 'AB'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root, name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not (root / path).resolve().is_relative_to(root.resolve()):
        raise ValueError('Public bundle paths must stay within their source directory.')
    return root / path


def summarize(manifest):
    cases = manifest['results']
    keys = [(c['topic'], c['repeat'], c['arm']) for c in cases]
    if len(keys) != 12 or set(keys) != EXPECTED or manifest['phase'] != 'formal':
        raise ValueError('Export requires exactly the 12 formal tasks, including failures.')
    if any(not set(c['stages']).issubset({'initial', 'final'}) for c in cases):
        raise ValueError('Unknown stage in formal batch.')
    for topic in ('T1', 'T2', 'T3'):
        for repeat in (1, 2):
            pair = [c for c in cases if c['topic'] == topic and c['repeat'] == repeat]
            for field in ('common_sha256', 'audio_sha256'):
                if len({c[field] for c in pair}) != 1:
                    raise ValueError(f'Pair input mismatch: {topic} r{repeat} {field}')
            audio = [c['stages']['final']['decoded_audio_sha256'] for c in pair
                     if c['stages'].get('final', {}).get('status') == 'rendered']
            if len(set(audio)) > 1:
                raise ValueError(f'Final decoded audio differs: {topic} r{repeat}')
    rows = []
    for c in cases:
        models = [s['model'] for s in c['stages'].values()]
        rows.append({'id': f"{c['topic']}-r{c['repeat']}-{c['arm']}", 'arm': c['arm'],
                     'status': c['status'],
                     'initial': c['stages']['initial'].get('status', 'not-rendered'),
                     'final': c['stages'].get('final', {}).get('status', 'not-rendered'),
                     'model_elapsed_s': round(sum(m['elapsed_s'] for m in models), 3),
                     'input_tokens': sum(m.get('usage', {}).get('input_tokens', 0) for m in models),
                     'output_tokens': sum(m.get('usage', {}).get('output_tokens', 0) for m in models)})
    return {'tasks': rows, 'rendered_tasks': sum(r['status'] == 'rendered' for r in rows),
            'rendered_versions': sum(s.get('status') == 'rendered' for c in cases for s in c['stages'].values()),
            'human_review': 'pending; no human ratings collected', 'billing_usd': None,
            'quality_effect': 'unknown; technical success does not establish improvement'}


def export(batch, assets, output):
    batch, assets, output = Path(batch), Path(assets), Path(output)
    manifest = json.loads((batch / 'manifest.json').read_text())
    summary = summarize(manifest)
    inputs = json.loads((assets / 'manifest.json').read_text())
    if inputs.get('redistribution_confirmed') is not True:
        raise ValueError('Public narration authorization missing.')
    if digest(assets / 'manifest.json') != manifest['asset_manifest_sha256']:
        raise ValueError('Asset manifest differs from frozen input.')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Use a new empty output directory.')
    output.mkdir(parents=True, exist_ok=True)
    for name, expected in manifest['files'].items():
        source = local_file(ROOT, name)
        if digest(source) != expected:
            raise ValueError(f'Frozen source changed: {name}')
        target = output / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copy2(ROOT / 'LICENSE', output / 'source/LICENSE')
    shutil.copy2(assets / 'manifest.json', output / 'inputs.json')
    for item in inputs['topics'].values():
        paths = [(item['audio'], item['sha256'])]
        if item.get('fixture'):
            paths.append((item['fixture']['path'], item['fixture']['sha256']))
        for name, expected in paths:
            source = local_file(assets, name)
            if digest(source) != expected:
                raise ValueError('Input path or hash mismatch.')
            target = output / 'inputs' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    cards = []
    for case in manifest['results']:
        ident = f"{case['topic']}-r{case['repeat']}-{case['arm']}"
        stages = []
        for stage, result in case['stages'].items():
            source = batch / ident / stage
            target = output / 'cases' / ident / stage
            target.mkdir(parents=True)
            names = ['prompt.txt', 'plan.md', 'src/Scene.tsx']
            if result.get('status') == 'rendered':
                if digest(source / 'video.mp4') != result['video_sha256']:
                    raise ValueError(f'Output video changed: {ident}/{stage}')
                names += ['video.mp4', 'frame-01.png', 'frame-02.png', 'frame-03.png']
            for name in names:
                path = source / name
                if not path.exists():
                    continue
                if path.suffix in ('.txt', '.md', '.tsx'):
                    text = path.read_text()
                    if any(s in text for s in ('/Users/', 'Bearer ', 'api_key', 'voice_id', 'reference_id')):
                        raise ValueError(f'Private marker in public text: {ident}/{stage}/{name}')
                (target / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target / name)
            url = f'cases/{ident}/{stage}'
            media = (f'<video controls playsinline preload="metadata" data-stage="{stage}" src="{url}/video.mp4"></video>'
                     if result.get('status') == 'rendered' else '<p>此版本没有可播放输出，失败状态保留。</p>')
            stages.append(f'<article><h3>{stage} · {escape(result.get("status", "not-rendered"))}</h3>{media}'
                          f'<a href="{url}/src/Scene.tsx">Scene 源码</a> · <a href="{url}/prompt.txt">输入</a> · '
                          f'<a href="{url}/plan.md">模型说明</a></article>')
        cards.append(f'<section><h2>{ident}</h2><div class="versions">'+''.join(stages)+'</div></section>')
    shutil.copy2(batch / 'manifest.json', output / 'batch.json')
    if (batch / 'source-provenance.json').exists():
        shutil.copy2(batch / 'source-provenance.json', output / 'source-provenance.json')
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    (output / 'REPRODUCE.md').write_text('''# Replay or rerender this experiment

Open index.html to watch every available initial and final output. Serve this
directory with a static server that supports HTTP byte ranges if your browser
cannot seek local videos. The anonymous human review form is a separate package.

To rerender one saved Scene (not generate a new model answer):

1. Copy source/examples/starter to a new local directory; run npm ci --ignore-scripts.
2. Replace src/Scene.tsx with cases/T1-r1-A/final/src/Scene.tsx (or another case).
3. Create public/ and copy inputs/T1/narration.wav to public/narration.wav.
   For T3 also copy inputs/T3/product-flow.mp4 to public/product-flow.mp4.
4. Run npm run check, then npx remotion render src/index.ts Bench video.mp4
   --codec h264 --crf 18 --concurrency 2 --browser-executable /path/to/chromium.

Use the matching topic's audio. The shared Root supplies it; do not add a second
narration track. The frozen environment was macOS, Node 26.11.1, Remotion 4.0.534
and Chromium 1223. System font and OS differences can affect pixels. Regenerating
with the same prompt is a new stochastic sample, not byte-identical reproduction.

batch.json preserves the original local revision record. source-provenance.json
maps its unpublished cache cleanup to public commit 962135a; frozen input hashes
are unchanged. source/ contains the exact frozen input bytes, not current drafts.

MIT covers original instructions and source code. Narration was owner-authorized
for public inspection and reproduction of this experiment; it is not part of
the Skill's MIT code license. Use your own cleared narration for other projects.
There is no commercial music or third-party product footage in these inputs.

No human ratings are included. Browser technical logs and model-generated notes
must not be counted as human understanding or preference votes. Dollar billing
is unknown. No quality improvement claim follows from a successful render.
''')
    rows = ''.join(f'<tr><td>{r["id"]}</td><td>{escape(r["initial"])} / {escape(r["final"])}</td><td>{r["model_elapsed_s"]:.1f}</td>'
                   f'<td>{r["input_tokens"]:,} / {r["output_tokens"]:,}</td></tr>' for r in summary['tasks'])
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>反 PPT Skill · 全量实验</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4eee3;color:#241a14;font:16px/1.8 system-ui,"PingFang SC",sans-serif}main{max-width:1160px;margin:auto;padding:32px 20px 80px}h1{line-height:1.3}.note{background:#fffaf4;padding:20px;border-left:4px solid #ff4f1f}section{margin:35px 0;border-top:1px solid #bfb4a1;padding-top:20px}.versions{display:grid;grid-template-columns:1fr 1fr;gap:25px}video{display:block;width:100%;max-height:700px;background:#241a14}a{color:#a33e21}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border-bottom:1px solid #d5cab8;text-align:left}.table{overflow:auto}button{font:inherit;padding:12px;margin:10px 8px 10px 0;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}@media(max-width:700px){.versions{grid-template-columns:1fr}main{padding:24px 16px}h1{font-size:26px}}
</style><main><h1>反 PPT Skill · 12 次正式任务</h1><p class="note">A 共享技术基线；B 额外加载 Skill。3 个题目 × 2 次重复 × 2 组，首稿与一次等预算复核后的终稿均保留。技术成功不代表理解改善。真人观看记录尚未收集，当前没有质量赢家。</p><p>主视频案例预先固定为 T1-r1。数据、界面都是教学模拟。模型复核只收到 0 / 5 / 9.5 秒静帧，不是完整播放。公开附件排除临时系统配音、账号标识、密钥、原始执行日志及依赖缓存。</p><p><a href="summary.json">汇总 JSON</a> · <a href="batch.json">完整机器状态</a> · <a href="inputs.json">共同素材与口播时序</a> · <a href="source/eval/protocol.md">冻结协议</a> · <a href="source-provenance.json">源码版本说明</a></p><p>模型调用耗时不含编译与渲染；Token 是实际事件用量，不能直接当账单。美元费用未知。初始与复核均计入每个任务。</p><div class="table"><table><tr><th>任务</th><th>首稿 / 终稿</th><th>模型秒数</th><th>输入 / 输出 Token</th></tr>'''+rows+'''</table></div><h2>播放技术自检</h2><p>此按钮静音正常速度播放全部可用终稿，并定位每片 0、5、9.5 秒。只验证浏览器播放与定位，不代替人类观看或盲评。</p><button id="qa">开始终稿播放自检</button><button id="save">导出技术自检记录</button><pre id="qa-status">未运行</pre>'''+''.join(cards)+'''</main><script>
const button=document.querySelector('#qa'),status=document.querySelector('#qa-status');let records=[];
function wait(v,event){return new Promise((ok,fail)=>{const timer=setTimeout(()=>{clean();fail(Error(event+' timeout'))},18000);function clean(){clearTimeout(timer);v.removeEventListener(event,done);v.removeEventListener('error',bad)}function done(){clean();ok()}function bad(){clean();fail(Error('media error'))}v.addEventListener(event,done,{once:true});v.addEventListener('error',bad,{once:true})})}
button.onclick=async()=>{button.disabled=true;records=[];for(const v of document.querySelectorAll('video[data-stage="final"]')){const row={src:v.getAttribute('src'),seeks:[]};try{v.muted=true;v.currentTime=0;const ended=wait(v,'ended');await v.play();await ended;row.ended=v.ended;row.duration=v.duration;row.width=v.videoWidth;row.height=v.videoHeight;if(Math.abs(v.duration-10)>.05||v.videoWidth!==1080||v.videoHeight!==1440)throw Error('media dimensions or duration mismatch');for(const time of [.001,5,9.5]){const sought=wait(v,'seeked');v.currentTime=time;await sought;row.seeks.push(v.currentTime);if(Math.abs(v.currentTime-time)>.15)throw Error('seek mismatch')}row.status='pass'}catch(e){v.pause();row.status='fail';row.error=String(e)}records.push(row);status.textContent=JSON.stringify(records,null,2)}button.disabled=false};
document.querySelector('#save').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({kind:'browser-technical-check-not-human-rating',batch_manifest_sha256:'BATCH_HASH',created_at:new Date().toISOString(),records},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='playback-check.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
</script></html>'''
    html = html.replace('BATCH_HASH', digest(batch / 'manifest.json'))
    (output / 'index.html').write_text(html)
    checksums = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output / 'sha256.json').write_text(json.dumps(checksums, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch'); parser.add_argument('assets'); parser.add_argument('output')
    args = parser.parse_args()
    print(json.dumps(export(args.batch, args.assets, args.output), ensure_ascii=False, indent=2))
