import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {AppState, StyleSheet, Text, View} from 'react-native';
import {useTVEventHandler} from '../player/TVPlatform';
import {assetUrl} from '../catalog/api';
import type {CatalogItem} from '../catalog/api';
import {config} from '../config';
import {VegaW3CPlayer} from '../player/VegaW3CPlayer';
import {VideoSurface} from '../player/VideoSurface';
import type {Preferences} from '../settings/preferences';
import {loadTrack, TrackError} from '../track/load';
import {ProfileSwap} from '../track/profileSwap';
import type {HazardTrack} from '../types/hazardtrack';
import {MediaClock} from '../veil/mediaClock';
import {VeilLayer} from '../veil/VeilLayer';
import {VeilScheduler} from '../veil/scheduler';
import {FocusButton} from './FocusButton';
import {HazardAheadChip} from './HazardAheadChip';
import {HazardScrubber} from './HazardScrubber';
import {hazardAhead, skipTarget} from './hazards';

const unprotectedScheduler = {at: () => ({opacity: 0, gray: 0})};
export function PlayerScreen({item, preferences, visible, onBack, onSettings, onRetry, onCalibration}: {
  item: CatalogItem; preferences: Preferences; visible: boolean; onBack: () => void; onSettings: () => void;
  onRetry: () => void; onCalibration: (kind: 'sync' | 'compositing') => void;
}) {
  const [player] = useState(() => new VegaW3CPlayer());
  const [clock] = useState(() => new MediaClock());
  const [swap] = useState(() => new ProfileSwap());
  const [track, setTrack] = useState<HazardTrack>();
  const metadata = useRef<HazardTrack | undefined>(undefined);
  const [surfaceReady, setSurfaceReady] = useState(false);
  const [veilReady, setVeilReady] = useState(false);
  const [mediaReady, setMediaReady] = useState(false);
  const [seeking, setSeeking] = useState(false);
  const [swapping, setSwapping] = useState(false);
  const [pending, setPending] = useState(true);
  const [paused, setPaused] = useState(true);
  const [error, setError] = useState('');
  const [missing, setMissing] = useState(false);
  const [unprotected, setUnprotected] = useState(false);
  const [time, setTime] = useState(0);
  const [chrome, setChrome] = useState(true);
  const [scrubbing, setScrubbing] = useState(false);
  const sourceLoaded = useRef(false), autoStarted = useRef(false), resumeAfterSeek = useRef(false);
  const seekPending = useRef(false), seekIssued = useRef(false);
  const frames = useRef(new Set<number>()), lastInput = useRef(performance.now());
  const live = useRef(true);
  const afterPaint = useCallback((action: () => void) => {
    const first = requestAnimationFrame(() => {
      frames.current.delete(first);
      const second = requestAnimationFrame(() => {frames.current.delete(second); if (live.current) {action();}});
      frames.current.add(second);
    });
    frames.current.add(first);
  }, []);
  const fail = useCallback((failure: unknown) => {
    if (!live.current) {return;}
    player.pause(); setPaused(true); setUnprotected(false);
    resumeAfterSeek.current = false;
    seekPending.current = false; seekIssued.current = false;
    const message = failure instanceof Error ? failure.message : 'Playback unavailable. Please retry.';
    console.error(JSON.stringify({event: 'playback_error', content_id: item.content_id, message}));
    setError(message);
  }, [player, item.content_id]);
  const readySurface = useCallback(() => setSurfaceReady(true), []);
  const readyVeil = useCallback(() => setVeilReady(true), []);
  const scheduler = useMemo(() => track ? new VeilScheduler(track.veils, track.media.duration_s) :
    unprotected ? unprotectedScheduler : undefined, [track, unprotected]);

  useEffect(() => {
    live.current = true;
    const pendingFrames = frames.current;
    const unsubscribe = player.subscribe(event => {
      if (event.type === 'loadedmetadata' || event.type === 'canplay') {
        const duration = metadata.current?.media.duration_s ?? item.duration_s;
        const tolerance = metadata.current ? 1 / metadata.current.media.fps + 0.01 : 0.1;
        if (!Number.isFinite(event.duration) || Math.abs(event.duration - duration) > tolerance) {
          fail(new Error('Video duration does not match the selected title')); return;
        }
        if (event.type === 'canplay') {setMediaReady(true);}
      }
      clock.update(event); setPaused(event.paused);
      if (event.type === 'seeking') {setSeeking(true);}
      if (event.type === 'seeked') {
        if (!seekPending.current || !seekIssued.current) {return;}
        seekIssued.current = false;
        afterPaint(() => {
          if (!seekPending.current) {return;}
          setSeeking(false);
          if (resumeAfterSeek.current) {
            resumeAfterSeek.current = false;
            afterPaint(() => {
              if (!seekPending.current) {return;}
              seekPending.current = false;
              if (live.current) {player.play().catch(fail);}
            });
          } else {seekPending.current = false;}
        });
      }
      if (event.error) {fail(new Error('Unsupported media or playback failure. ' + event.error.message));}
    });
    const background = AppState.addEventListener('change', state => {
      if (state !== 'active') {
        player.pause(); setSurfaceReady(false);
        fail(new Error('Playback stopped while the app was in the background. Retry to continue.'));
      }
    });
    const timer = setInterval(() => {
      setTime(clock.now());
      setChrome(player.paused || performance.now() - lastInput.current < 4000);
    }, 100);
    return () => {
      live.current = false; unsubscribe(); background.remove(); clearInterval(timer); swap.cancel();
      for (const frame of pendingFrames) {cancelAnimationFrame(frame);}
      pendingFrames.clear(); player.dispose().catch(() => {});
    };
  }, [player, clock, fail, afterPaint, swap, item.duration_s]);

  useEffect(() => {
    const abort = new AbortController();
    let current = true;
    setPending(true); setMissing(false); setError(''); setUnprotected(false);
    // Existing verification remains active while the requested sidecar is fetched.
    swap.request(preferences.profile, async () => {
      const entry = item.tracks[preferences.profile];
      if (!entry) {throw new TrackError('Not analyzed — no protection', 'missing');}
      const loaded = await loadTrack(assetUrl(entry.url),
        {contentId: item.content_id, sourceSha256: item.source_sha256}, abort.signal);
      if (Math.abs(loaded.media.duration_s - item.duration_s) > 1 / loaded.media.fps + 0.01) {
        throw new TrackError('HazardTrack duration does not match this title');
      }
      return loaded;
    }).then(latest => {
      if (!current || !latest) {return;}
      if (swap.state === 'error') {
        setPending(false); player.pause(); setPaused(true); setTrack(undefined); metadata.current = undefined;
        if (swap.error instanceof TrackError && swap.error.kind === 'missing') {setMissing(true);}
        else {fail(swap.error);}
        return;
      }
      afterPaint(() => {
        if (!current) {return;}
        const loaded = swap.commit();
        if (!loaded) {return;}
        setSwapping(true); setVeilReady(false); metadata.current = loaded; setTrack(loaded);
        afterPaint(() => {if (current) {setSwapping(false); setPending(false);}});
        if (!sourceLoaded.current) {
          sourceLoaded.current = true;
          clock.anchor({currentTime: 0, duration: loaded.media.duration_s, playbackRate: 1, paused: true});
          player.load(assetUrl(item.video, true)).catch(fail);
        }
      });
    });
    return () => {current = false; abort.abort(); swap.cancel();};
  }, [item, preferences.profile, swap, player, clock, fail, afterPaint]);

  const canControl = Boolean((track || unprotected) && surfaceReady && veilReady && mediaReady && !seeking && !swapping && !error && !missing);
  useEffect(() => {
    if (canControl && !pending && !autoStarted.current && !unprotected) {
      autoStarted.current = true; player.play().catch(fail);
    }
  }, [canControl, pending, player, fail, unprotected]);
  const showChrome = () => {lastInput.current = performance.now(); setChrome(true);};
  const toggle = () => {
    showChrome(); if (!canControl) {return;}
    if (!player.paused) {player.pause();} else {player.play().catch(fail);}
  };
  const seekTo = (target: number) => {
    if (!canControl || seekPending.current) {return;}
    seekPending.current = true;
    const value = Math.max(0, Math.min(item.duration_s, target));
    resumeAfterSeek.current = !player.paused;
    player.pause(); setSeeking(true);
    afterPaint(() => {
      if (!seekPending.current) {return;}
      clock.anchor({currentTime: value, duration: item.duration_s, playbackRate: player.playbackRate, paused: true});
      try {seekIssued.current = true; player.seek(value);}
      catch (failure: unknown) {fail(failure);}
    });
  };
  const segment = useMemo(() => hazardAhead(track, time, preferences.warnAhead), [track, time, preferences.warnAhead]);
  useTVEventHandler(event => {
    if (!visible || event.eventKeyAction === 1) {return;}
    showChrome();
    if (event.eventType === 'playpause') {toggle();}
    if (event.eventType === 'menu') {onSettings();}
    if ((scrubbing || !chrome) && (event.eventType === 'left' || event.eventType === 'right')) {
      seekTo(clock.now() + (event.eventType === 'left' ? -10 : 10));
    }
  });
  const acceptUnprotected = () => {
    // A missing sidecar never triggers autoplay. This explicit choice is visible in every profile.
    setMissing(false); setUnprotected(true); setVeilReady(false); autoStarted.current = true;
    if (!sourceLoaded.current) {
      sourceLoaded.current = true;
      clock.anchor({currentTime: 0, duration: item.duration_s, playbackRate: 1, paused: true});
      player.load(assetUrl(item.video, true)).catch(fail);
    }
  };
  return <View style={styles.screen}>
    <VideoSurface player={player} onReady={readySurface} onError={fail} />
    <VeilLayer clock={clock} scheduler={scheduler} blocked={(!track && !unprotected) || !!error || missing || seeking || swapping}
      onReady={readyVeil} onError={fail} nativeDriver={config.nativeVeilDriver} />
    {unprotected && <View style={styles.banner}><Text style={styles.alert}>Not analyzed — no protection</Text></View>}
    {(chrome || error || missing || pending) && visible && <View style={styles.chrome}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.status}>{error ? 'Protected playback unavailable' : missing ? 'Not analyzed — no protection' :
        pending ? `Loading ${preferences.profile} viewing profile…` : unprotected ? 'Unprotected playback selected' : `${track?.profile} · Verified flash reduction`}</Text>
      {!!error && <Text accessibilityRole="alert" style={styles.alert}>{error}</Text>}
      {missing ? <>
        <Text style={styles.alert}>No matching analysis is available. Playback is paused. {preferences.profile === 'kids' ? 'Kids defaults to keeping this title paused.' : 'Continue only if you choose unprotected playback.'}</Text>
        <View style={styles.row}><FocusButton label="Keep paused · Back to catalog" preferred onPress={onBack} />
          <FocusButton label="Continue without protection" onPress={acceptUnprotected} /></View>
      </> : <>
        <View style={styles.row}>
          <FocusButton label="Catalog" onPress={onBack} />
          <FocusButton label={paused ? 'Play' : 'Pause'} preferred onPress={toggle} disabled={!canControl} />
          <FocusButton label={`Settings · ${preferences.profile}`} onPress={onSettings} />
          {!!error && <FocusButton label="Retry playback" onPress={onRetry} />}
        </View>
        <HazardScrubber track={track} duration={item.duration_s} time={time} disabled={!canControl}
          onFocus={() => {setScrubbing(true); showChrome();}} onBlur={() => setScrubbing(false)} onSeek={delta => seekTo(clock.now() + delta)} />
      </>}
      {__DEV__ && <View style={styles.row}>{(['sync', 'compositing'] as const).map(kind =>
        <FocusButton key={kind} label={`Calibrate ${kind}`} onPress={() => onCalibration(kind)} />)}</View>}
    </View>}
    {visible && <View style={styles.chip}><HazardAheadChip segment={segment} disabled={!canControl}
      onSkip={() => {if (track && segment) {showChrome(); seekTo(skipTarget(track, segment));}}} /></View>}
  </View>;
}
const styles = StyleSheet.create({screen: {flex: 1, backgroundColor: '#000'},
  chrome: {position: 'absolute', bottom: 24, left: 36, right: 36, zIndex: 20, backgroundColor: '#101c2a', padding: 20, borderRadius: 14},
  title: {color: '#fff', fontSize: 28, fontWeight: '600'}, status: {color: '#8cf0d1', fontSize: 18, marginVertical: 8},
  row: {flexDirection: 'row'}, alert: {color: '#ffcb69', fontSize: 20, marginVertical: 8},
  banner: {position: 'absolute', top: 18, left: 36, zIndex: 20, backgroundColor: '#101c2a', padding: 12},
  chip: {position: 'absolute', top: 20, right: 36, zIndex: 21},
});
