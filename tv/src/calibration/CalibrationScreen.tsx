import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';
import {config} from '../config';
import {VegaW3CPlayer} from '../player/VegaW3CPlayer';
import {VideoSurface} from '../player/VideoSurface';
import {MediaClock} from '../veil/mediaClock';
import {VeilLayer} from '../veil/VeilLayer';
import {CalibrationTimeline, parseCalibration} from './timeline';
import type {CalibrationDescriptor} from './timeline';

/** Debug-only lab; instant cues can never pass the production reader. No autoplay. */
export function CalibrationScreen({kind, onExit}: {kind: 'sync' | 'compositing'; onExit: () => void}) {
  const [player] = useState(() => new VegaW3CPlayer());
  const [clock] = useState(() => new MediaClock());
  const [descriptor, setDescriptor] = useState<CalibrationDescriptor>();
  const [ready, setReady] = useState(false);
  const [primed, setPrimed] = useState(false);
  const [paused, setPaused] = useState(true);
  const [error, setError] = useState('');
  const [focus, setFocus] = useState('play');
  const timeline = useMemo(() => descriptor ? new CalibrationTimeline(descriptor) : undefined, [descriptor]);
  const fail = useCallback((reason: unknown) => {console.error(JSON.stringify({event: 'calibration_error', message: String(reason)})); player.pause(); setError(String(reason));}, [player]);
  const surfaceReady = useCallback(() => setReady(true), []);
  const veilReady = useCallback(() => setPrimed(true), []);
  useEffect(() => {
    let live = true;
    const abort = new AbortController();
    const unsubscribe = player.subscribe(event => {
      clock.update(event); setPaused(event.paused); if (event.error) {fail(event.error);}
    });
    (async () => {
      const response = await fetch(config.catalogBaseUrl + `/calibration/${kind}.json`, {signal: abort.signal});
      if (!response.ok) {throw new Error('Calibration assets unavailable');}
      const item = parseCalibration(await response.json(), __DEV__);
      if (!live) {return;}
      clock.anchor({currentTime: 0, duration: item.duration_s, playbackRate: 1, paused: true});
      setDescriptor(item); await player.load(config.mediaBaseUrl + '/' + item.video.split('/').pop());
    })().catch(reason => {if (live) {fail(reason);}});
    return () => {live = false; abort.abort(); unsubscribe(); player.dispose().catch(() => {});};
  }, [kind, player, clock, fail]);
  const actions: {id: string; label: string; run: () => void}[] = [
    {id: 'play', label: paused ? 'Play' : 'Pause', run: () => {if (paused) {player.play().catch(fail);} else {player.pause();}}},
    {id: 'seek', label: 'Seek to 8 s', run: () => player.seek(8)},
    {id: 'restart', label: 'Restart', run: () => player.seek(0)},
    {id: 'exit', label: 'Exit calibration', run: onExit},
  ];
  return <View style={styles.screen}>
    <View style={styles.video}>
      <VideoSurface player={player} onReady={surfaceReady} onError={fail} />
      <VeilLayer clock={clock} scheduler={timeline} blocked={!descriptor || !!error}
        onReady={veilReady} onError={fail} nativeDriver={config.nativeVeilDriver} />
    </View>
    <Text style={styles.text}>Calibration only · {kind} · {error || 'Small-area pulses / slow ramps. Record only the video rectangle.'}</Text>
    <View style={styles.row}>{actions.map(action => <Pressable key={action.id}
      hasTVPreferredFocus={focus === action.id && ready && primed} onFocus={() => setFocus(action.id)}
      disabled={action.id !== 'exit' && (!ready || !primed || !!error)}
      onPress={action.run} style={[styles.button, focus === action.id && styles.focus]}>
      <Text style={styles.text}>{action.label}</Text>
    </Pressable>)}</View>
  </View>;
}
const styles = StyleSheet.create({
  screen: {flex: 1, backgroundColor: '#10141b'}, video: {flex: 1, backgroundColor: '#000000'},
  row: {flexDirection: 'row', padding: 12}, text: {color: '#ffffff', fontSize: 18, margin: 8},
  button: {borderWidth: 3, borderColor: '#303a47', marginRight: 16, borderRadius: 8},
  focus: {borderColor: '#82d8c7'},
});
