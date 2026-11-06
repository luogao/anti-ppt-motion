const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'..');
const request=createRequire(path.join(root,'examples/starter/package.json'));
const ts=request('typescript');
const code=ts.transpileModule(fs.readFileSync(path.join(root,'assets/scene-world.tsx'),'utf8'),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.React,esModuleInterop:true,target:ts.ScriptTarget.ES2022}
}).outputText;
const mod={exports:{}};new Function('require','module','exports',code)(request,mod,mod.exports);
const {cameraAt,project}=mod.exports;
const shots=[{frame:10,x:100,y:50,zoom:3},{frame:50,x:300,y:150,zoom:.5}];
assert.deepEqual(cameraAt(0,shots),{x:100,y:50,zoom:3});
assert.deepEqual(cameraAt(60,shots),{x:300,y:150,zoom:.5});
assert.deepEqual(cameraAt(30,shots),{x:200,y:100,zoom:1.75});
assert.throws(()=>cameraAt(0,[]));
assert.throws(()=>cameraAt(NaN,shots));
assert.throws(()=>cameraAt(0,[shots[0],shots[0]]));
assert.throws(()=>cameraAt(0,[{frame:0,x:0,y:0,zoom:0}]));
// Equal vertical units retain their 3:1 ratio under the orthographic projection.
const baseline=project([0,0,0])[1];
assert.equal((baseline-project([0,0,300])[1])/(baseline-project([0,0,100])[1]),3);
console.log('Scene-world camera bounds, interpolation, invalid inputs and scale ratio: PASS');
