import type {VeilCue} from '../types/hazardtrack';

export interface TimelineScheduler {at(time: number): VeilTarget}
export interface VeilTarget {opacity: number; gray: number}

/** HazardTrack playback semantics; same arithmetic and tie order as Python. */
export function veilTimeline(cues: readonly VeilCue[], time: number): VeilTarget {
  if (!Number.isFinite(time)) {throw new Error('Timeline time must be finite');}
  let target: VeilTarget = {opacity: 0, gray: 0};
  let selected = '';
  for (const cue of cues) {
    const strength = Math.max(0, Math.min(1,
      (time - cue.t_on + cue.ramp_in_s) / cue.ramp_in_s,
      (cue.t_off + cue.ramp_out_s - time) / cue.ramp_out_s));
    const opacity = cue.alpha * strength;
    if (opacity > 0 && (opacity > target.opacity ||
      (opacity === target.opacity && (cue.gray < target.gray ||
        (cue.gray === target.gray && cue.id < selected))))) {
      target = {opacity, gray: cue.gray};
      selected = cue.id;
    }
  }
  return target;
}

export class VeilScheduler {
  constructor(private readonly cues: readonly VeilCue[], private readonly duration: number) {
    if (!Number.isFinite(duration) || duration <= 0) {throw new Error('Invalid media duration');}
  }
  at(time: number): VeilTarget {
    // Hold the last media frame at end; never remove its protection early.
    return veilTimeline(this.cues, Math.max(0, Math.min(this.duration, time)));
  }
}
