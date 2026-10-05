import React from 'react';
import {StyleSheet} from 'react-native';
// W3C Media is supplied by Vega; project doctor verifies its OS-version mapping.
// eslint-disable-next-line @amazon-devices/kepler/sdl-package-version-check-imports
import {KeplerVideoSurfaceView} from '@amazon-devices/react-native-w3cmedia';
import type {VegaW3CPlayer} from './VegaW3CPlayer';

export function VideoSurface({player, onReady, onError}: {
  player: VegaW3CPlayer; onReady: () => void; onError: (error: unknown) => void;
}) {
  return <KeplerVideoSurfaceView style={StyleSheet.absoluteFill} scalingmode="fit"
    onSurfaceViewCreated={handle => {player.surfaceCreated(handle).then(onReady).catch(onError);}}
    onSurfaceViewDestroyed={handle => player.surfaceDestroyed(handle)} />;
}
