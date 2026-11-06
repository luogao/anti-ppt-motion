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
