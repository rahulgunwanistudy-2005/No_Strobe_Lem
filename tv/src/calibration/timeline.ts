import type {VeilTarget} from '../veil/scheduler';

export interface CalibrationCue {id: string; t_on: number; t_off: number; alpha: number; gray: number}
export interface CalibrationDescriptor {
  format: 'nostrobe-calibration'; version: 1; production: false;
  kind: 'sync' | 'compositing'; video: string; duration_s: number; fps: number;
  cues: CalibrationCue[];
}
export function parseCalibration(value: unknown, development: boolean): CalibrationDescriptor {
  if (!development) {throw new Error('Calibration is excluded from release playback');}
  if (!value || typeof value !== 'object') {throw new Error('Invalid calibration');}
  const item = value as CalibrationDescriptor;
  if (item.format !== 'nostrobe-calibration' || item.version !== 1 || item.production !== false ||
      !['sync', 'compositing'].includes(item.kind) || typeof item.video !== 'string' ||
      !item.video.startsWith('/calibration/') || !Number.isFinite(item.duration_s) || item.duration_s <= 0 ||
      item.fps !== 30 || !Array.isArray(item.cues) || item.cues.some(cue =>
        !Number.isFinite(cue.t_on) || !Number.isFinite(cue.t_off) || cue.t_off <= cue.t_on ||
        !Number.isFinite(cue.alpha) || cue.alpha < 0 || cue.alpha > 1 ||
        !Number.isFinite(cue.gray) || cue.gray < 0 || cue.gray > 1)) {
    throw new Error('Invalid calibration descriptor');
  }
  return item;
}
export class CalibrationTimeline {
  constructor(private readonly descriptor: CalibrationDescriptor) {}
  at(time: number): VeilTarget {
    const cue = this.descriptor.cues.find(value => time >= value.t_on && time < value.t_off);
    return cue ? {opacity: cue.alpha, gray: cue.gray} : {opacity: 0, gray: 0};
  }
}
