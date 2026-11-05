#!/usr/bin/env python3
"""Create an offline, group-blind review page. The reveal key stays outside it."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import random
import shutil

QUESTIONS={'T1':'等待为什么出现？','T2':'谁更快，比较条件是什么？','T3':'操作前后改变了什么？'}

def build(batch,output):
    batch=Path(batch);output=Path(output)
    if output.exists() and any(output.iterdir()):raise FileExistsError('Use a new empty review directory.')
    output.mkdir(parents=True,exist_ok=True);(output/'clips').mkdir()
    manifest=json.loads((batch/'manifest.json').read_text())
    cases={(x['topic'],x['repeat'],x['arm']):x for x in manifest['results']}
    pairs=sorted({(t,r) for t,r,_ in cases})
    rng=random.Random(20261105);rng.shuffle(pairs)
    key={};cards=[];clip_index=0
    for index,(topic,rep) in enumerate(pairs,1):
        arms=list('AB');rng.shuffle(arms);clips=[]
        for arm in arms:
            clip_index+=1;clip=f'clip-{clip_index:02d}';key[clip]={'topic':topic,'repeat':rep,'arm':arm}
            source=batch/f'{topic}-r{rep}-{arm}'/'final/video.mp4'
            if source.exists():
                shutil.copy2(source,output/'clips'/f'{clip}.mp4')
                media=f'<video controls preload="metadata" playsinline src="clips/{clip}.mp4"></video>'
            else:media='<p class="failure">该次任务没有可播放终稿。请记录无法判断。</p>'
            clips.append(f'<article><h3>{clip}</h3>{media}<label>看完这一版，你的回答：<textarea name="{clip}-understanding" required placeholder="{escape(QUESTIONS[topic])} 不知道可以直写不知道。"></textarea></label></article>')
        ids=[f'clip-{clip_index-1:02d}',f'clip-{clip_index:02d}']
        choices=''.join(f'<label class="choice"><input type="radio" name="pair-{index}-preferred" value="{v}" required>{v}</label>' for v in [*ids,'差不多','无法判断'])
        cards.append(f'<section><h2>比较 {index} / {len(pairs)}</h2><p class="question">共同理解问题：{escape(QUESTIONS[topic])}</p><p>先正常播放并回答各自理解，再做比较；不知道组别时不要先查看公开结果索引。</p><div class="clips">'+''.join(clips)+f'</div><fieldset><legend>哪版更容易理解、叙事更连贯？</legend>{choices}</fieldset><label>理由与问题时间码（可记录阅读、声画、PPT 感）：<textarea name="pair-{index}-notes"></textarea></label></section>')
    protocol_hash=hashlib.sha256((batch/'manifest.json').read_bytes()).hexdigest()
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>反 PPT Skill · 匿名观看与理解记录</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f1e9;color:#253329;font:16px/1.8 system-ui,"PingFang SC",sans-serif}main{max-width:1100px;margin:auto;padding:38px 24px 80px}h1{font-size:30px;line-height:1.4}h2{font-size:23px}p{max-width:850px}.note{padding:18px 22px;background:#e6eee4;border-left:4px solid #487257}section{margin:30px 0;padding:24px;background:#fffef9;border:1px solid #d6ddd1}.clips{display:grid;grid-template-columns:1fr 1fr;gap:24px}video{display:block;width:100%;max-height:660px;background:#18211b}label{display:block;margin:14px 0}textarea,input[type=text],select{width:100%;font:inherit;padding:12px;border:1px solid #bac6b7;border-radius:4px;background:white}textarea{min-height:110px}fieldset{margin:20px 0;border:1px solid #cad4c6}.choice{display:inline-block;margin:8px 20px 8px 0}button{font:inherit;padding:14px 24px;background:#2f6149;color:white;border:0;border-radius:5px;cursor:pointer}.failure{padding:25px;background:#f6e7de}.question{font-weight:650}.saved{font-size:13px;color:#5c6a5e}@media(max-width:700px){.clips{grid-template-columns:1fr}main{padding:24px 16px}section{padding:17px}h1{font-size:25px}}
</style><main><h1>反 PPT Skill：匿名观看与理解记录</h1><p class="note">这是待填写的人类观看表，不包含预置分数或赢家。请按实际理解填写。评分只保存在你的浏览器；导出 JSON 后交回本次对话。参与过制作、已看过组别或结果，也请如实标记。</p><form id="review"><label>评价者代号（例如 R1，不填姓名或联系方式）：<input name="reviewer" type="text" required></label><label>是否参与制作或已知组别？<select name="involvement" required><option value="">请选择</option><option value="uninvolved-blind">未参与，未知组别</option><option value="involved-blind">参与过，当前未知组别</option><option value="labels-known">已知组别或看过结果</option></select></label>'''+''.join(cards)+'''<button type="submit">导出我的观看记录</button><p id="save-state" class="saved"></p></form><p>可播放成功不代表内容更好。理解、阅读、声画和个人偏好请分开说明；没有把握时可以选择无法判断。</p></main><script>
const form=document.querySelector('#review');const status=document.querySelector('#save-state');const storageKey='anti-ppt-review-PROTOCOL_HASH';
function values(){return Object.fromEntries(new FormData(form).entries())}
try{const old=JSON.parse(localStorage.getItem(storageKey)||'{}');for(const [name,value] of Object.entries(old)){const e=form.elements.namedItem(name);if(e)e.value=value}status.textContent='本页会在当前浏览器自动保存。'}catch(e){status.textContent='自动保存不可用，请及时导出。'}
form.addEventListener('input',()=>{try{localStorage.setItem(storageKey,JSON.stringify(values()))}catch(e){status.textContent='自动保存失败，请及时导出。'}});
form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;const data={protocol_manifest_sha256:'PROTOCOL_HASH',created_at:new Date().toISOString(),ratings:values()};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='anti-ppt-review-'+(data.ratings.reviewer||'anonymous').replace(/[^a-zA-Z0-9_-]/g,'_')+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
</script></html>'''
    html=html.replace('PROTOCOL_HASH',protocol_hash)
    (output/'index.html').write_text(html)
    (output.parent/(output.name+'-reveal-key.json')).write_text(json.dumps(key,ensure_ascii=False,indent=2))
    print(output/'index.html')
    return html,key

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch');p.add_argument('output');a=p.parse_args();build(a.batch,a.output)
