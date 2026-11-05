import React from 'react';
import {AbsoluteFill, Audio, Composition, staticFile} from 'remotion';
import {Scene} from './Scene';
const Video: React.FC = () => <AbsoluteFill><Scene/><Audio src={staticFile('narration.wav')}/></AbsoluteFill>;
export const Root: React.FC = () => <Composition id="Bench" component={Video} durationInFrames={300} fps={30} width={1080} height={1440}/>;
