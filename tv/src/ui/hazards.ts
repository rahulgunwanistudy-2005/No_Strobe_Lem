import type {HazardTrack} from '../types/hazardtrack';
export interface HazardSegment {id: string; start: number; end: number; kind: 'veiled' | 'warn' | 'unresolved'}
export interface HazardTick extends HazardSegment {left: number; width: number}
export function hazardSegments(track: HazardTrack): HazardSegment[] {
  const covered = new Set(track.veils.flatMap(cue => cue.covers));
  return [
    ...track.veils.map(cue => ({id: cue.id, start: Math.max(0, cue.t_on - cue.ramp_in_s),
      end: Math.min(track.media.duration_s, cue.t_off + cue.ramp_out_s), kind: 'veiled' as const})),
    ...track.events.filter(event => event.severity === 'warn' && !covered.has(event.id))
      .map(event => ({id: event.id, start: event.t_start, end: event.t_end, kind: 'warn' as const})),
    ...(track.unresolved_segments ?? []).map((segment, i) => ({id: `unresolved_${i}`,
      start: segment.start, end: Math.min(track.media.duration_s, segment.end + 0.25), kind: 'unresolved' as const})),
  ].sort((a, b) => a.start - b.start || a.id.localeCompare(b.id));
}
export function hazardTicks(track: HazardTrack): HazardTick[] {
  return hazardSegments(track).map(segment => ({...segment, left: segment.start / track.media.duration_s,
    width: Math.max(0, segment.end - segment.start) / track.media.duration_s}));
}
export function hazardAhead(track: HazardTrack | undefined, time: number, warn: boolean): HazardSegment | undefined {
  if (!track) {return undefined;}
  return hazardSegments(track).filter(segment => segment.kind !== 'warn' &&
    (warn || segment.kind === 'unresolved') && time >= segment.start - 3 && time < segment.end)
    .sort((a, b) => Number(b.kind === 'unresolved') - Number(a.kind === 'unresolved') || a.start - b.start)[0];
}
/** Skip the whole overlapping cluster; never land inside a later overlapping veil. */
export function skipTarget(track: HazardTrack, segment: HazardSegment): number {
  let target = segment.end;
  const segments = hazardSegments(track).filter(value => value.kind !== 'warn');
  for (let i = 0; i < segments.length; i++) {
    const next = segments.find(value => value.start <= target && value.end > target);
    if (!next) {break;}
    target = next.end;
  }
  return Math.min(track.media.duration_s, target);
}
export function formatTime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
