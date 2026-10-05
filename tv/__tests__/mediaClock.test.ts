import {MediaClock} from '../src/veil/mediaClock';
import type {PlayerEvent, PlayerEventType} from '../src/player/PlayerAdapter';

let mono = 0;
let clock: MediaClock;
const event = (type: PlayerEventType, currentTime: number, paused = false, playbackRate = 1): PlayerEvent =>
  ({type, currentTime, duration: 20, paused, playbackRate});
beforeEach(() => {mono = 0; clock = new MediaClock(() => mono);});

test('interpolates steady playback and bounds prediction at duration', () => {
  clock.update(event('play', 2)); mono = 0.4;
  expect(clock.now()).toBeCloseTo(2.4);
  mono = 50; expect(clock.now()).toBe(20);
});
test('pause holds and resume anchors', () => {
  clock.update(event('play', 0)); mono = 2;
  clock.update(event('pause', 2, true)); mono = 10;
  expect(clock.now()).toBe(2);
  clock.update(event('play', 2)); mono = 11;
  expect(clock.now()).toBe(3);
});
test('seeks both directions and freezes while waiting for media', () => {
  clock.update(event('play', 2)); mono = 2;
  clock.update(event('seeking', 12)); mono = 3;
  expect(clock.now()).toBe(12);
  clock.update(event('seeked', 12)); mono = 4;
  expect(clock.now()).toBe(13);
  clock.update(event('seeked', 1)); expect(clock.now()).toBe(1);
  clock.update(event('waiting', 1)); mono = 9; expect(clock.now()).toBe(1);
  clock.update(event('playing', 1)); mono = 10; expect(clock.now()).toBe(2);
});
test('rate changes anchor at 1.5x', () => {
  clock.update(event('ratechange', 3, false, 1.5)); mono = 2;
  expect(clock.now()).toBe(6);
});
test('large drift is corrected without advancing a paused clock', () => {
  clock.update(event('play', 0)); mono = 1;
  clock.update(event('timeupdate', 0.6)); expect(clock.now()).toBe(0.6);
  mono = 2; expect(clock.now()).toBe(1.6);
  clock.update(event('pause', 1.6, true)); mono = 4;
  clock.update(event('timeupdate', 1.3, true)); mono = 5; expect(clock.now()).toBe(1.3);
});
test('ended holds the final frame and rejects invalid anchors', () => {
  clock.update(event('ended', 20, true)); mono = 100;
  expect(clock.now()).toBe(20);
  expect(() => clock.update(event('play', NaN))).toThrow();
});
