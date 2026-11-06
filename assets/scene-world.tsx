import React from 'react';
import {interpolate} from 'remotion';

export type Vec3 = [number, number, number];
export type Shot = {frame:number; x:number; y:number; zoom:number};
export const project = ([x,y,z]:Vec3):[number,number] => [x-.65*y,.34*x+.48*y-z];
const vertices = (ps:Vec3[]) => ps.map(p=>project(p).join(',')).join(' ');

export function cameraAt(frame:number,shots:Shot[]):Omit<Shot,'frame'> {
 if(!Number.isFinite(frame)||!shots.length||shots.some((s,i)=>![s.frame,s.x,s.y,s.zoom].every(Number.isFinite)||s.zoom<=0||(i>0&&s.frame<=shots[i-1].frame)))
  throw new Error('Camera shots need finite, increasing frames and positive zoom.');
 const index=shots.findIndex(s=>s.frame>=frame);
 if(index<=0){const {x,y,zoom}=shots[index<0?shots.length-1:0];return {x,y,zoom};}
 const a=shots[index-1],b=shots[index];
 const p=interpolate(frame,[a.frame,b.frame],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const t=p*p*(3-2*p),mix=(a:number,b:number)=>a+(b-a)*t;
 return {x:mix(a.x,b.x),y:mix(a.y,b.y),zoom:mix(a.zoom,b.zoom)};
}

export const CameraGroup:React.FC<{frame:number;shots:Shot[];width:number;height:number;children:React.ReactNode}> = ({frame,shots,width,height,children}) => {
 const {x,y,zoom}=cameraAt(frame,shots);
 return <g transform={`translate(${width/2-x*zoom} ${height/2-y*zoom}) scale(${zoom})`}>{children}</g>;
};

export const WorldBlock:React.FC<{at:Vec3;width:number;depth:number;height:number;colors:[string,string,string];opacity?:number}> = ({at:[x,y,z],width:w,depth:d,height:h,colors,opacity=1}) => {
 const a:Vec3=[x-w/2,y-d/2,z],b:Vec3=[x+w/2,y-d/2,z],c:Vec3=[x+w/2,y+d/2,z],e:Vec3=[x-w/2,y+d/2,z];
 const top=(p:Vec3):Vec3=>[p[0],p[1],p[2]+h];
 return <g opacity={opacity}>
  <polygon points={vertices([e,c,top(c),top(e)])} fill={colors[1]}/>
  <polygon points={vertices([b,c,top(c),top(b)])} fill={colors[2]}/>
  <polygon points={vertices([top(a),top(b),top(c),top(e)])} fill={colors[0]}/>
 </g>;
};

export type ComparisonLane = {label:string; values:number[]};
export function comparisonLayout(lanes:ComparisonLane[]) {
 if(lanes.length!==2 || !lanes[0].values.length || lanes[0].values.length!==lanes[1].values.length ||
    lanes.some(l=>!l.label || l.values.some(v=>!Number.isFinite(v)||v<=0)))
  throw new Error('Comparison needs two labeled lanes with the same positive task count.');
 const rows=lanes.map((lane,row)=>{
  let start=0;
  const parts=lane.values.map((value,index)=>{const part={value,index,start,end:start+value};start=part.end;return part;});
  return {...lane,row,y:row*520,total:start,parts};
 });
 return {rows,maxTotal:Math.max(...rows.map(r=>r.total)),unit:40};
}

// The preset supplies spatial assembly and a shared measuring pass; content and timing come from the caller.
export const ComparisonWorld:React.FC<{frame:number;lanes:ComparisonLane[];assemble:[number,number];measure:[number,number];unitLabel:string}> = ({frame,lanes,assemble,measure,unitLabel}) => {
 if(![...assemble,...measure].every(Number.isFinite)||assemble[1]<=assemble[0]||measure[1]<=measure[0])
  throw new Error('Preset timing ranges need finite increasing frames.');
 const {rows,maxTotal,unit}=comparisonLayout(lanes);
 const p=interpolate(frame,assemble,[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const scan=interpolate(frame,measure,[0,maxTotal*unit],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const line=(ps:Vec3[])=>ps.map((v,i)=>(i?'L':'M')+project(v).join(' ')).join(' ');
 const gridStep=Math.max(1,Math.ceil(maxTotal/6));
 return <g>
  <WorldBlock at={[maxTotal*unit/2,240,-28]} width={maxTotal*unit+600} depth={1050} height={24} colors={['#F1E5D0','#BFAA88','#DDCBAA']}/>
  {Array.from({length:7},(_,i)=>{const x=i*maxTotal*unit/6;return <path key={'grid'+i} d={line([[x,-220,0],[x,760,0]])} stroke="#D4C2A6" strokeWidth="2"/>})}
  {rows.map(row=><g key={row.label}>
   <path d={line([[0,row.y,4],[maxTotal*unit,row.y,4]])} fill="none" stroke="#C3B499" strokeWidth="10"/>
   <path d={line([[0,row.y-100,2],[0,row.y+100,2]])} stroke="#8B7559" strokeWidth="5"/>
   {row.parts.map(part=>{
    const local=Math.min(1,Math.max(0,(p*row.parts.length-part.index)*1.25));
    const eased=local*local*(3-2*local),z=16+(1-eased)*220;
    const at:Vec3=[(part.start+part.value/2)*unit-(1-eased)*180,row.y,z];
    const label=project([at[0],at[1],z+100]);
    return <g key={part.index} opacity={Math.min(1,local*5)}>
     <WorldBlock at={at} width={part.value*unit} depth={130} height={90} colors={row.row===0?['#FF955E','#BC4D25','#E46B35']:['#7DCCC3','#275E5F','#408B87']}/>
     <text x={label[0]} y={label[1]+22} textAnchor="middle" fill="#241A14" fontSize="68" fontWeight="700">{part.value}{unitLabel}</text>
    </g>;
   })}
   <text x={project([-100,row.y,50])[0]} y={project([-100,row.y,50])[1]} textAnchor="end" fill="#241A14" fontSize="90" fontWeight="700">{row.label}</text>
   <text x={project([row.total*unit+80,row.y,50])[0]} y={project([row.total*unit+80,row.y,50])[1]} fill="#241A14" fontSize="80" fontWeight="700">{row.total}{unitLabel}</text>
  </g>)}
  {Array.from({length:Math.floor(maxTotal/gridStep)+1},(_,i)=>{const value=i*gridStep,pos=project([value*unit,-160,0]);return <text key={'tick'+i} x={pos[0]} y={pos[1]} textAnchor="middle" fill="#79664E" fontSize="50">{value}</text>})}
  <path d={line([[scan,-160,125],[scan,650,125]])} stroke="#FF4F1F" strokeWidth="6" opacity={frame>=measure[0]&&frame<=measure[1]?0.7:0}/>
 </g>;
};
