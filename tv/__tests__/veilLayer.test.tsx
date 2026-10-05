import React from 'react';
import {Animated} from 'react-native';
import {act, render} from '@testing-library/react-native';
import {VeilLayer} from '../src/veil/VeilLayer';
import {MediaClock} from '../src/veil/mediaClock';

test('native ownership completes before a constant cue is primed or playback is enabled', () => {
  let complete: ((result: {finished: boolean}) => void) | undefined;
  const scheduled: Array<(time: number) => void> = [];
  const animation = jest.spyOn(Animated, 'timing').mockReturnValue({
    start: callback => {complete = callback;}, stop: jest.fn(), reset: jest.fn(),
  });
  const raf = jest.spyOn(global, 'requestAnimationFrame').mockImplementation(callback => {scheduled.push(callback); return scheduled.length;});
  const cancel = jest.spyOn(global, 'cancelAnimationFrame').mockImplementation(() => {});
  const opacity = jest.spyOn(Animated.Value.prototype, 'setValue');
  const ready = jest.fn();
  const screen = render(<VeilLayer clock={new MediaClock()} scheduler={{at: () => ({opacity: 0.1, gray: 0.25})}}
    blocked={false} onReady={ready} onError={jest.fn()} />);
  expect(scheduled).toHaveLength(0); expect(ready).not.toHaveBeenCalled();
  act(() => complete?.({finished: true}));
  act(() => scheduled.shift()?.(0));
  expect(opacity).toHaveBeenLastCalledWith(0.1); expect(ready).toHaveBeenCalledTimes(1);
  const writes = opacity.mock.calls.length;
  act(() => scheduled.shift()?.(16));
  expect(opacity).toHaveBeenCalledTimes(writes);
  screen.unmount();
  act(() => complete?.({finished: true}));
  expect(ready).toHaveBeenCalledTimes(1);
  animation.mockRestore(); raf.mockRestore(); cancel.mockRestore(); opacity.mockRestore();
});
