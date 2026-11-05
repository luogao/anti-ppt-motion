import React from 'react';
import {AbsoluteFill, Composition, interpolate, registerRoot, useCurrentFrame} from 'remotion';
const Fixture: React.FC = () => {
  const f=useCurrentFrame();
  const p=interpolate(f,[94,184],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <AbsoluteFill style={{background:'#eef1eb',fontFamily:'Arial, sans-serif',color:'#23352c',padding:70}}>
    <div style={{fontSize:30,color:'#5d6f63'}}>教学界面 · 非真实产品</div>
    <div style={{fontSize:64,fontWeight:700,marginTop:25}}>文件归类</div>
    <div style={{position:'absolute',left:70,top:240,width:940,height:1050,background:'white',border:'2px solid #cad3c9',borderRadius:24}}/>
    <div style={{position:'absolute',left:120,top:285,fontSize:36}}>未归类　{f<184?3:0}</div>
    <div style={{position:'absolute',left:120,top:815,width:840,height:380,border:'3px solid #7c9c85',borderRadius:20,background:'#edf4eb',padding:30,fontSize:36}}>项目：我的视频　{f<184?0:3}</div>
    {['方案.md','素材.png','镜头.tsx'].map((name,i)=><div key={name} style={{position:'absolute',left:120+i*282,top:415+505*p,width:252,height:160,border:f>=94?'4px solid #39795d':'2px solid #d2d9cf',background:'#f9faf7',borderRadius:14,padding:24,fontSize:30}}><div style={{fontSize:40,marginBottom:13}}>▤</div>{name}</div>)}
    <div style={{position:'absolute',left:120,top:650,padding:'20px 30px',fontSize:32,borderRadius:12,background:'#39795d',color:'white'}}>{f<94?'选择文件':f<184?'归入项目':'已完成'}</div>
  </AbsoluteFill>;
};
registerRoot(()=> <Composition id="Fixture" component={Fixture} width={1080} height={1440} fps={30} durationInFrames={300}/>);
