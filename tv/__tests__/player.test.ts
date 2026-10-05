jest.mock('@amazon-devices/react-native-w3cmedia/dist/headless', () => ({VideoPlayer: jest.fn()}));
import {VegaW3CPlayer} from '../src/player/VegaW3CPlayer';
import type {VideoPlayer} from '@amazon-devices/react-native-w3cmedia/dist/headless';

function nativePlayer() {
  const native = {
    initialize: jest.fn(async () => {}), deinitialize: jest.fn(async () => {}),
    setSurfaceHandle: jest.fn(), clearSurfaceHandle: jest.fn(),
    addEventListener: jest.fn(), removeEventListener: jest.fn(),
    play: jest.fn(async () => {}), pause: jest.fn(), autoplay: false,
    src: '', currentTime: 0, duration: 10, playbackRate: 1, paused: true, error: null,
  };
  return {native, player: new VegaW3CPlayer(native as unknown as VideoPlayer)};
}
test('one initialization precedes surface and src; teardown is idempotent', async () => {
  const {native, player} = nativePlayer();
  await Promise.all([player.surfaceCreated('surface'), player.load('video.mp4')]);
  expect(native.initialize).toHaveBeenCalledTimes(1);
  expect(native.setSurfaceHandle).toHaveBeenCalledWith('surface');
  expect(native.src).toBe('video.mp4');
  await player.play();
  await Promise.all([player.dispose(), player.dispose()]);
  expect(native.clearSurfaceHandle).toHaveBeenCalledWith('surface');
  expect(native.deinitialize).toHaveBeenCalledTimes(1);
  expect(native.removeEventListener).toHaveBeenCalledTimes(12);
  await expect(player.play()).rejects.toThrow('closed');
});
test('unmount during initialization never attaches or assigns src', async () => {
  const {native, player} = nativePlayer();
  let resolve!: () => void;
  native.initialize.mockImplementation(() => new Promise<void>(done => {resolve = done;}));
  const loading = player.load('video.mp4');
  const closing = player.dispose(); resolve();
  await expect(loading).rejects.toThrow('closed');
  await closing;
  expect(native.src).toBe('');
  expect(native.setSurfaceHandle).not.toHaveBeenCalled();
  expect(native.deinitialize).toHaveBeenCalledTimes(1);
});
test('destroyed/recreated surface holds playback and rejects play until reattached', async () => {
  const {native, player} = nativePlayer();
  await player.surfaceCreated('one');
  player.surfaceDestroyed('one');
  await expect(player.play()).rejects.toThrow('surface');
  await player.surfaceCreated('two'); await player.play();
  expect(native.setSurfaceHandle).toHaveBeenLastCalledWith('two');
  player.seek(25); expect(native.currentTime).toBe(10);
  player.playbackRate = 1.5; expect(native.playbackRate).toBe(1.5);
  expect(() => {player.playbackRate = 0;}).toThrow();
  expect(() => player.seek(NaN)).toThrow();
  await player.dispose();
});
