import React, {useEffect, useRef, useState} from 'react';
import {Animated, StyleSheet, View} from 'react-native';
import type {MediaClock} from './mediaClock';
import type {TimelineScheduler} from './scheduler';

/** No extra easing: each frame applies the already-ramped media timeline value. */
export function VeilLayer({clock, scheduler, blocked, onReady, onError, nativeDriver = true}: {
  clock: MediaClock; scheduler?: TimelineScheduler; blocked: boolean;
  onReady: () => void; onError: (error: unknown) => void; nativeDriver?: boolean;
}) {
  const opacity = useRef(new Animated.Value(1)).current;
  const [gray, setGray] = useState(0);
  const currentGray = useRef(0);
  useEffect(() => {
    let frame = 0;
    let live = true;
    let primed = false;
    let lastOpacity: number | undefined;
    // Establish native ownership; subsequent setValue calls send exact targets.
    // Native is the default; the explicit driver option is for device calibration/fallback.
    // eslint-disable-next-line @amazon-devices/kepler/animated
    const animation = Animated.timing(opacity, {toValue: 1, duration: 0, useNativeDriver: nativeDriver});
    animation.start();
    const tick = () => {
      if (!live) {return;}
      try {
        const target = blocked || !scheduler ? {opacity: 1, gray: 0} : scheduler.at(clock.now());
        if (target.gray !== currentGray.current) {
          currentGray.current = target.gray;
          setGray(target.gray);
        }
        if (target.opacity !== lastOpacity) {
          opacity.setValue(target.opacity);
          lastOpacity = target.opacity;
        }
        if (!primed && scheduler && !blocked) {primed = true; onReady();}
        frame = requestAnimationFrame(tick);
      } catch (error: unknown) {
        opacity.setValue(1);
        onError(error);
      }
    };
    frame = requestAnimationFrame(tick);
    return () => {live = false; cancelAnimationFrame(frame); animation.stop();};
  }, [clock, scheduler, blocked, opacity, onReady, onError, nativeDriver]);
  const code = Math.round(gray * 255);
  return <>
    {blocked && <View pointerEvents="none" testID="playback-shield" style={styles.shield} />}
    <Animated.View pointerEvents="none" testID="veil-layer"
    style={[styles.veil, {opacity, backgroundColor: `rgb(${code},${code},${code})`}]} />
  </>;
}
const styles = StyleSheet.create({shield: {...StyleSheet.absoluteFillObject, zIndex: 11, backgroundColor: '#000000'}, veil: {...StyleSheet.absoluteFillObject, zIndex: 10}});
