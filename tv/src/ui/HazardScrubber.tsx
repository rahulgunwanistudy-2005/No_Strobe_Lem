import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import {TVFocusGuideView} from '../player/TVPlatform';
import type {HazardTrack} from '../types/hazardtrack';
import {formatTime, hazardTicks} from './hazards';
export function HazardScrubber({track, duration, time, onFocus, onBlur, onSeek, disabled}: {
  track?: HazardTrack; duration: number; time: number; onFocus: () => void; onBlur: () => void; onSeek: (delta: number) => void; disabled: boolean;
}) {
  const [focused, setFocused] = React.useState(false);
  const ticks = track ? hazardTicks(track) : [];
  return <TVFocusGuideView trapFocusLeft trapFocusRight><View focusable={!disabled} accessible
    onFocus={() => {setFocused(true); onFocus();}} onBlur={() => {setFocused(false); onBlur();}} accessibilityRole="adjustable"
    accessibilityLabel={`Playback position ${formatTime(time)} of ${formatTime(duration)}. Left or right seeks ten seconds.`}
    accessibilityActions={[{name: 'increment'}, {name: 'decrement'}]}
    onAccessibilityAction={event => {if (!disabled) {onSeek(event.nativeEvent.actionName === 'increment' ? 10 : -10);}}}
    accessibilityValue={{min: 0, max: duration, now: time}} style={[styles.box, focused && styles.focus]}>
    <View style={styles.rail}><View style={[styles.progress, {width: `${Math.min(100, time / duration * 100)}%`}]} />
      {ticks.map(tick => <View key={`${tick.kind}_${tick.id}`} style={[styles.tick, {
        left: `${tick.left * 100}%`, width: `${Math.max(tick.width * 100, 0.5)}%`,
      }, tick.kind === 'warn' ? styles.warn : styles.veiled]}>{tick.kind === 'unresolved' && <Text style={styles.stripe}>{'////'}</Text>}</View>)}
    </View>
    <Text style={styles.text}>{formatTime(time)} elapsed · −{formatTime(duration - time)} remaining</Text>
    <Text style={styles.legend}>Left / right to seek · Red: veiled · Amber: warning · Striped: unresolved</Text>
  </View></TVFocusGuideView>;
}
const styles = StyleSheet.create({box: {padding: 12, borderWidth: 2, borderColor: '#536d80', borderRadius: 8},
  focus: {borderColor: '#8cf0d1'}, warn: {backgroundColor: '#ffcb69'}, veiled: {backgroundColor: '#fa7a83'},
  rail: {height: 12, backgroundColor: '#445769', marginVertical: 12}, progress: {height: 12, backgroundColor: '#8cf0d1'},
  tick: {position: 'absolute', height: 18, top: -3, minWidth: 3}, stripe: {color: '#0e1823', fontSize: 12},
  row: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'},
  text: {color: '#fff', fontSize: 18}, legend: {color: '#c6d3df', fontSize: 15},
});
