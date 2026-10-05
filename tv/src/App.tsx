import React, {useCallback, useEffect, useMemo, useState, useRef} from 'react';
import {AppState, Pressable, StyleSheet, Text, View} from 'react-native';
import {config, disclaimer} from './config';
import {VegaW3CPlayer} from './player/VegaW3CPlayer';
import {VideoSurface} from './player/VideoSurface';
import {loadTrack} from './track/load';
import type {HazardTrack} from './types/hazardtrack';
import {MediaClock} from './veil/mediaClock';
import {VeilScheduler} from './veil/scheduler';
import {VeilLayer} from './veil/VeilLayer';

interface DemoItem {title: string; video: string; track: string; content_id: string; source_sha256: string}
function demoItem(value: unknown): DemoItem {
  if (!value || typeof value !== 'object') {throw new Error('Invalid demo item');}
  const item = value as Record<string, unknown>;
  for (const key of ['title', 'video', 'track', 'content_id', 'source_sha256']) {
    if (typeof item[key] !== 'string' || !item[key]) {throw new Error('Invalid demo item');}
  }
  // Keep video and sidecar on the configured asset server.
  if (!String(item.video).startsWith('/') || !String(item.track).startsWith('/')) {throw new Error('Invalid asset paths');}
  return item as unknown as DemoItem;
}

function ProtectedPlayer({onCalibration}: {onCalibration: (kind: 'sync' | 'compositing') => void}) {
  const [player] = useState(() => new VegaW3CPlayer());
  const [clock] = useState(() => new MediaClock());
  const [track, setTrack] = useState<HazardTrack>();
  const [title, setTitle] = useState('No Strobe-lem');
  const [surfaceReady, setSurfaceReady] = useState(false);
  const [veilReady, setVeilReady] = useState(false);
  const [mediaReady, setMediaReady] = useState(false);
  const [seeking, setSeeking] = useState(false);
  const [paused, setPaused] = useState(true);
  const [error, setError] = useState('');
  const [focused, setFocused] = useState('play');
  const resumeAfterSeek = useRef(false);
  const frames = useRef(new Set<number>());
  const afterPaint = useCallback((action: () => void) => {
    const first = requestAnimationFrame(() => {
      frames.current.delete(first);
      const second = requestAnimationFrame(() => {frames.current.delete(second); action();});
      frames.current.add(second);
    });
    frames.current.add(first);
  }, []);
  const scheduler = useMemo(() => track ? new VeilScheduler(track.veils, track.media.duration_s) : undefined, [track]);
  const fail = useCallback((failure: unknown) => {
    console.error(JSON.stringify({event: 'playback_error', message: failure instanceof Error ? failure.message : String(failure)}));
    player.pause();
    setError(failure instanceof Error ? failure.message : 'Playback unavailable');
  }, [player]);
  const readySurface = useCallback(() => setSurfaceReady(true), []);
  const readyVeil = useCallback(() => setVeilReady(true), []);

  useEffect(() => {
    let live = true;
    const pendingFrames = frames.current;
    const abort = new AbortController();
    let metadata: HazardTrack | undefined;
    const unsubscribe = player.subscribe(event => {
      if (event.type === 'loadedmetadata' || event.type === 'canplay') {
        if (!metadata || !Number.isFinite(event.duration) || Math.abs(event.duration - metadata.media.duration_s) > 1 / metadata.media.fps + 0.01) {
          fail(new Error('Video duration does not match its HazardTrack')); return;
        }
        if (event.type === 'canplay') {setMediaReady(true);}
      }
      clock.update(event);
      setPaused(event.paused);
      if (event.type === 'seeking') {setSeeking(true);}
      if (event.type === 'seeked') {
        afterPaint(() => {
          setSeeking(false);
          if (resumeAfterSeek.current) {
            resumeAfterSeek.current = false;
            afterPaint(() => {player.play().catch(fail);});
          }
        });
      }
      if (event.error) {fail(event.error);}
    });
    const background = AppState.addEventListener('change', state => {
      if (state !== 'active') {
        setSurfaceReady(false);
        player.dispose().catch(fail);
        setError('Playback stopped. Reopen the app to continue.');
      }
    });
    (async () => {
      const response = await fetch(config.catalogBaseUrl + config.itemPath, {signal: abort.signal});
      if (!response.ok) {throw new Error('Demo catalog unavailable');}
      const item = demoItem(await response.json());
      const loaded = await loadTrack(config.catalogBaseUrl + item.track,
        {contentId: item.content_id, sourceSha256: item.source_sha256}, abort.signal);
      if (!live) {return;}
      setTitle(item.title);
      clock.anchor({currentTime: 0, duration: loaded.media.duration_s, playbackRate: 1, paused: true});
      metadata = loaded;
      setTrack(loaded);
      await player.load(config.mediaBaseUrl + item.video);
    })().catch(failure => {if (live) {fail(failure);}});
    return () => {
      live = false; abort.abort(); unsubscribe(); background.remove();
      for (const frame of pendingFrames) {cancelAnimationFrame(frame);}
      pendingFrames.clear();
      player.dispose().catch(() => { /* UI has unmounted. */ });
    };
  }, [player, clock, fail, afterPaint]);

  const toggle = () => {
    if (!track || !surfaceReady || !veilReady || !mediaReady || seeking || error) {return;}
    if (!paused) {player.pause(); return;}
    if (Number.isFinite(player.duration) && Math.abs(player.duration - track.media.duration_s) > 1 / track.media.fps + 0.01) {
      fail(new Error('Video duration does not match its HazardTrack')); return;
    }
    player.play().catch(fail);
  };
  const seek = (delta: number) => {
    if (!track || error || seeking) {return;}
    const time = Math.max(0, Math.min(track.media.duration_s, clock.now() + delta));
    resumeAfterSeek.current = !player.paused;
    player.pause();
    setSeeking(true);
    afterPaint(() => {
      clock.anchor({currentTime: time, duration: track.media.duration_s, playbackRate: player.playbackRate, paused: true});
      player.seek(time);
    });
  };
  const canControl = Boolean(track && surfaceReady && veilReady && mediaReady && !seeking && !error);
  return <View style={styles.screen}>
    <View style={styles.video}>
      <VideoSurface player={player} onReady={readySurface} onError={fail} />
      <VeilLayer clock={clock} scheduler={scheduler} blocked={!track || !!error || seeking}
        onReady={readyVeil} onError={fail} nativeDriver={config.nativeVeilDriver} />
    </View>
    <View style={styles.panel}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.status}>{error || (track && surfaceReady && veilReady && mediaReady ? 'Broadcast · Verified flash reduction' : 'Loading verified playback…')}</Text>
      <View style={styles.controls}>
        {[['back', '−10 seconds', () => seek(-10)], ['play', paused ? 'Play' : 'Pause', toggle],
          ['forward', '+10 seconds', () => seek(10)]].map(([id, label, action]) =>
          <Pressable key={String(id)} hasTVPreferredFocus={focused === id && canControl}
            onFocus={() => setFocused(String(id))} onPress={action as () => void}
            disabled={!canControl}
            style={[styles.button, focused === id && styles.focus]} accessibilityRole="button">
            <Text style={styles.buttonText}>{String(label)}</Text>
          </Pressable>)}
      </View>
      {__DEV__ && <View style={styles.controls}>
        {(['sync', 'compositing'] as const).map(kind => <Pressable key={kind}
          onFocus={() => setFocused(kind)} onPress={() => onCalibration(kind)}
          style={[styles.button, focused === kind && styles.focus]}>
          <Text style={styles.buttonText}>Calibrate {kind}</Text>
        </Pressable>)}
      </View>}
      <Text style={styles.disclaimer}>{disclaimer}</Text>
    </View>
  </View>;
}
export function App() {
  const [calibration, setCalibration] = useState<'sync' | 'compositing'>();
  if (__DEV__ && calibration) {
    // Metro eliminates this debug-only branch and its module in release builds.
    const {CalibrationScreen} = require('./calibration/CalibrationScreen') as typeof import('./calibration/CalibrationScreen');
    return <CalibrationScreen kind={calibration} onExit={() => setCalibration(undefined)} />;
  }
  return <ProtectedPlayer onCalibration={setCalibration} />;
}
const styles = StyleSheet.create({
  screen: {flex: 1, backgroundColor: '#10141b'},
  video: {flex: 1, backgroundColor: '#000000'},
  panel: {paddingHorizontal: 48, paddingVertical: 20},
  title: {fontSize: 30, color: '#ffffff', fontWeight: '600'},
  status: {fontSize: 18, color: '#c8d6e5', marginVertical: 8},
  controls: {flexDirection: 'row', marginVertical: 8},
  button: {padding: 12, marginRight: 16, borderWidth: 3, borderColor: '#303a47', borderRadius: 8},
  focus: {borderColor: '#82d8c7'},
  buttonText: {color: '#ffffff', fontSize: 20},
  disclaimer: {color: '#afbdcc', fontSize: 14, marginTop: 8},
});
