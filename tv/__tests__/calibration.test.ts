import {CalibrationTimeline, parseCalibration} from '../src/calibration/timeline';
import {parseTrack} from '../src/track/load';

const descriptor = {format: 'nostrobe-calibration', version: 1, production: false,
  kind: 'sync', video: '/calibration/sync.mp4', fps: 30, duration_s: 24,
  cues: [{id: 'pulse', t_on: 2, t_off: 2.5, alpha: 0.5, gray: 0.5}]};
test('instant lab cues require development mode and cannot pass the production reader', () => {
  expect(() => parseCalibration(descriptor, false)).toThrow('release');
  expect(() => parseTrack(descriptor)).toThrow();
  const timeline = new CalibrationTimeline(parseCalibration(descriptor, true));
  expect(timeline.at(1.99)).toEqual({opacity: 0, gray: 0});
  expect(timeline.at(2)).toEqual({opacity: 0.5, gray: 0.5});
  expect(timeline.at(2.5)).toEqual({opacity: 0, gray: 0});
});
test('the lab guard rejects malformed and production descriptors', () => {
  expect(() => parseCalibration({...descriptor, production: true}, true)).toThrow();
  expect(() => parseCalibration({...descriptor, cues: [{...descriptor.cues[0], alpha: NaN}]}, true)).toThrow();
});
