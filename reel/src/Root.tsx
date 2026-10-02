import {Composition} from 'remotion';
import {DrawerClip, DURATION} from './DrawerClip';

export const RemotionRoot = () => (
  <Composition
    id="DrawerClip"
    component={DrawerClip}
    durationInFrames={DURATION}
    fps={30}
    width={1080}
    height={1080}
  />
);
