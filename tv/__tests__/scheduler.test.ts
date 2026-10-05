import fixture from '../../spec/examples/timeline_conformance.json';
import {veilTimeline, VeilScheduler} from '../src/veil/scheduler';

test('all 500 samples conform to the Python engine within 1e-6', () => {
  expect(fixture.samples).toHaveLength(500);
  for (const sample of fixture.samples) {
    const actual = veilTimeline(fixture.cues, sample.time);
    expect(Math.abs(actual.opacity - sample.alpha)).toBeLessThanOrEqual(1e-6);
    expect(Math.abs(actual.gray - sample.gray)).toBeLessThanOrEqual(1e-6);
  }
});
test('seek, pause and final frame use exactly the current media timeline', () => {
  const scheduler = new VeilScheduler(fixture.cues, fixture.duration_s);
  for (const sample of fixture.playback_cases) {
    expect(scheduler.at(sample.time).opacity).toBeCloseTo(sample.alpha, 6);
    expect(scheduler.at(sample.time).gray).toBe(sample.gray);
  }
  expect(scheduler.at(-10)).toEqual(scheduler.at(0));
  expect(scheduler.at(11)).toEqual(scheduler.at(10));
});
test('overlap tie picks the lower gray independently of cue order', () => {
  expect(veilTimeline(fixture.cues, 4.5)).toEqual({opacity: 0.7, gray: 0.25});
  expect(veilTimeline([...fixture.cues].reverse(), 4.5)).toEqual({opacity: 0.7, gray: 0.25});
  expect(() => veilTimeline(fixture.cues, Infinity)).toThrow();
});
