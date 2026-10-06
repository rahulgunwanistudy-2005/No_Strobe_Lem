import React from 'react';
import {act, fireEvent, render, waitFor} from '@testing-library/react-native';
import failing from '../../spec/examples/contract.hzt.json';
import valid from '../assets/raw/demo.hzt.json';
import {App} from '../src/App';
import {PlayerScreen} from '../src/ui/PlayerScreen';
import {VegaW3CPlayer} from '../src/player/VegaW3CPlayer';
import {defaultPreferences} from '../src/settings/preferences';
import type {CatalogItem} from '../src/catalog/api';
import type {PlayerEvent} from '../src/player/PlayerAdapter';
import {PlaybackError} from '../src/player/PlayerAdapter';
import {AsyncStorage} from '../src/player/TVPlatform';

jest.mock('react-native', () => {
  const actual = jest.requireActual('react-native');
  return Object.create(actual, {BackHandler: {value: {addEventListener: jest.fn(() => ({remove: jest.fn()}))}}});
});
jest.mock('../src/player/TVPlatform', () => {
  const {View} = require('react-native');
  return {AsyncStorage: {getItem: jest.fn(async () => null), setItem: jest.fn(async () => {})},
    useTVEventHandler: jest.fn(), TVFocusGuideView: View};
});
jest.mock('../src/player/VegaW3CPlayer', () => ({VegaW3CPlayer: jest.fn().mockImplementation(() => ({
  load: jest.fn(async () => {}), play: jest.fn(async () => {}), pause: jest.fn(), seek: jest.fn(),
  paused: true, currentTime: 0, duration: 12, playbackRate: 1,
  subscribe: jest.fn(() => () => {}), dispose: jest.fn(async () => {}),
}))}));
jest.mock('../src/player/VideoSurface', () => ({VideoSurface: ({onReady}: {onReady: () => void}) => {
  require('react').useEffect(onReady, [onReady]); return null;
}}));
jest.mock('../src/veil/VeilLayer', () => {
  const {View} = require('react-native');
  return {VeilLayer: ({blocked, scheduler, onReady}: {blocked: boolean; scheduler?: unknown; onReady: () => void}) => {
    require('react').useEffect(() => {if (!blocked && scheduler) {onReady();}}, [blocked, scheduler, onReady]);
    return <View testID={blocked ? 'blocked' : 'unblocked'} />;
  }};
});
const item: CatalogItem = {title: 'Fixture', video: '/video.mp4', duration_s: 12,
  tracks: {broadcast: {url: '/video.hzt.json', hazard_count: 0}, local: {url: '/local.hzt.json', hazard_count: 0}},
  content_id: valid.media.content_id, source_sha256: valid.media.source_sha256,
  attribution: {credit: 'Fixture', license: 'CC-BY', url: 'https://example.com/', changes: 'Test'}};
const props = {item, preferences: defaultPreferences, visible: true, onBack: jest.fn(), onSettings: jest.fn(), onRetry: jest.fn(), onCalibration: jest.fn()};
let logger: jest.SpyInstance;
beforeEach(() => {jest.clearAllMocks(); logger = jest.spyOn(console, 'error').mockImplementation(() => {});});
afterEach(() => {logger.mockRestore(); jest.restoreAllMocks();});

test('catalog selection with failing verifier keeps video blocked and never loads or plays native source', async () => {
  const bad = {...failing, media: valid.media};
  jest.spyOn(global, 'fetch').mockResolvedValueOnce({ok: true, json: async () => ({version: 1, items: [item]})} as Response)
    .mockResolvedValueOnce({ok: true, json: async () => bad} as Response);
  const screen = render(<App />);
  await waitFor(() => expect(screen.getByLabelText('Fixture')).toBeTruthy());
  fireEvent.press(screen.getByLabelText('Fixture'));
  await waitFor(() => expect(screen.getByText('This track has not passed verification')).toBeTruthy());
  expect(screen.getByTestId('blocked')).toBeTruthy();
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  expect(player.load).not.toHaveBeenCalled(); expect(player.play).not.toHaveBeenCalled();
  screen.unmount(); expect(player.dispose).toHaveBeenCalledTimes(1);
});
test('stored Kids household is restored before the catalog becomes interactive', async () => {
  (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce('{"profile":"broadcast","household":"kids","warnAhead":false}');
  jest.spyOn(global, 'fetch').mockResolvedValueOnce({ok: true, json: async () => ({version: 1, items: [item]})} as Response);
  const screen = render(<App />);
  await waitFor(() => expect(screen.getByLabelText('Settings · kids')).toBeTruthy());
  fireEvent.press(screen.getByLabelText('Settings · kids'));
  expect(screen.getByLabelText('Warn me before hazards · Off')).toBeTruthy();
  screen.unmount();
});
test('storage read failure applies Kids and explains the fallback', async () => {
  (AsyncStorage.getItem as jest.Mock).mockRejectedValueOnce(new Error('disk read'));
  jest.spyOn(global, 'fetch').mockResolvedValueOnce({ok: true, json: async () => ({version: 1, items: [item]})} as Response);
  const screen = render(<App />);
  await waitFor(() => expect(screen.getByText(/Saved settings could not be read/)).toBeTruthy());
  expect(screen.getByLabelText('✓ Kids household')).toBeTruthy();
  expect(screen.getByLabelText('✓ Kids')).toBeTruthy();
  screen.unmount();
});
test('missing track defaults to pause for Kids, explicit choice keeps banner and does not autoplay', async () => {
  const screen = render(<PlayerScreen {...props} item={{...item, tracks: {}}}
    preferences={{...defaultPreferences, profile: 'kids', household: 'kids'}} />);
  await waitFor(() => expect(screen.getByText(/Kids defaults/)).toBeTruthy());
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  expect(player.load).not.toHaveBeenCalled(); expect(player.play).not.toHaveBeenCalled();
  fireEvent.press(screen.getByLabelText('Continue without protection'));
  await waitFor(() => expect(player.load).toHaveBeenCalledTimes(1));
  expect(screen.getByText('Not analyzed — no protection')).toBeTruthy(); expect(player.play).not.toHaveBeenCalled();
  screen.unmount();
});
test('profile swap replaces only the sidecar, preserves playback position and ignores mismatched profile', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValueOnce({ok: true, json: async () => valid} as Response)
    .mockResolvedValueOnce({ok: true, json: async () => ({...valid, profile: 'local'})} as Response)
    .mockResolvedValueOnce({ok: true, json: async () => valid} as Response);
  const screen = render(<PlayerScreen {...props} />);
  await waitFor(() => expect(screen.getByText('broadcast · Verified flash reduction')).toBeTruthy());
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  const listener = player.subscribe.mock.calls[0][0] as (event: PlayerEvent) => void;
  act(() => listener({type: 'timeupdate', currentTime: 5, duration: 12, paused: true, playbackRate: 1}));
  screen.rerender(<PlayerScreen {...props} preferences={{...defaultPreferences, profile: 'local'}} />);
  await waitFor(() => expect(screen.getByText('local · Verified flash reduction')).toBeTruthy());
  expect(player.load).toHaveBeenCalledTimes(1); expect(player.seek).not.toHaveBeenCalled();
  screen.rerender(<PlayerScreen {...props} preferences={{...defaultPreferences, profile: 'kids'}}
    item={{...item, tracks: {...item.tracks, kids: {url: '/kids.hzt.json', hazard_count: 0}}}} />);
  await waitFor(() => expect(screen.getByText('HazardTrack does not match the selected profile')).toBeTruthy());
  expect(screen.getByTestId('blocked')).toBeTruthy(); expect(player.load).toHaveBeenCalledTimes(1);
  screen.unmount();
});
test('network error offers retry and never loads video', async () => {
  jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Network request failed'));
  const screen = render(<PlayerScreen {...props} />);
  await waitFor(() => expect(screen.getByText('Network request failed')).toBeTruthy());
  fireEvent.press(screen.getByLabelText('Retry playback')); expect(props.onRetry).toHaveBeenCalled();
  expect((VegaW3CPlayer as jest.Mock).mock.results[0].value.load).not.toHaveBeenCalled(); screen.unmount();
});


test('verified autoplay waits for native metadata and seeks keep a shield until veil propagation', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValue({ok: true, json: async () => valid} as Response);
  const screen = render(<PlayerScreen {...props} />);
  await waitFor(() => expect(screen.getByText('broadcast · Verified flash reduction')).toBeTruthy());
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  const listener = player.subscribe.mock.calls[0][0] as (event: PlayerEvent) => void;
  expect(player.play).not.toHaveBeenCalled();
  act(() => listener({type: 'canplay', currentTime: 0, duration: 12, paused: true, playbackRate: 1}));
  await waitFor(() => expect(player.play).toHaveBeenCalledTimes(1));
  const {useTVEventHandler} = require('../src/player/TVPlatform');
  fireEvent(screen.getByRole('adjustable'), 'focus');
  const handler = (useTVEventHandler as jest.Mock).mock.calls.at(-1)[0];
  act(() => handler({eventType: 'right', eventKeyAction: 0}));
  expect(screen.getByTestId('blocked')).toBeTruthy();
  await waitFor(() => expect(player.seek).toHaveBeenCalledWith(10));
  act(() => listener({type: 'seeked', currentTime: 10, duration: 12, paused: true, playbackRate: 1}));
  await waitFor(() => expect(screen.getByTestId('unblocked')).toBeTruthy());
  screen.unmount();
});

test('same-turn seek storm issues one seek and ignores premature completion', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValue({ok: true, json: async () => valid} as Response);
  const screen = render(<PlayerScreen {...props} />);
  await waitFor(() => expect(screen.getByText('broadcast · Verified flash reduction')).toBeTruthy());
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  const listener = player.subscribe.mock.calls[0][0] as (event: PlayerEvent) => void;
  act(() => listener({type: 'canplay', currentTime: 0, duration: 12, paused: true, playbackRate: 1}));
  await waitFor(() => expect(player.play).toHaveBeenCalledTimes(1));
  const {useTVEventHandler} = require('../src/player/TVPlatform');
  fireEvent(screen.getByRole('adjustable'), 'focus');
  const handler = (useTVEventHandler as jest.Mock).mock.calls.at(-1)[0];
  act(() => {
    for (let i = 0; i < 30; i++) {handler({eventType: 'right', eventKeyAction: 0});}
    listener({type: 'seeked', currentTime: 0, duration: 12, paused: true, playbackRate: 1});
  });
  expect(screen.getByTestId('blocked')).toBeTruthy();
  await waitFor(() => expect(player.seek).toHaveBeenCalledTimes(1));
  expect(player.seek).toHaveBeenCalledWith(10);
  expect(screen.getByTestId('blocked')).toBeTruthy();
  act(() => listener({type: 'seeked', currentTime: 10, duration: 12, paused: true, playbackRate: 1}));
  await waitFor(() => expect(screen.getByTestId('unblocked')).toBeTruthy());
  screen.unmount();
});

test('native seek exception stays covered and offers retry', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValue({ok: true, json: async () => valid} as Response);
  const screen = render(<PlayerScreen {...props} />);
  await waitFor(() => expect(screen.getByText('broadcast · Verified flash reduction')).toBeTruthy());
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  const listener = player.subscribe.mock.calls[0][0] as (event: PlayerEvent) => void;
  act(() => listener({type: 'canplay', currentTime: 0, duration: 12, paused: true, playbackRate: 1}));
  await waitFor(() => expect(player.play).toHaveBeenCalledTimes(1));
  player.seek.mockImplementationOnce(() => {throw new Error('Native seek failed');});
  const {useTVEventHandler} = require('../src/player/TVPlatform');
  fireEvent(screen.getByRole('adjustable'), 'focus');
  act(() => (useTVEventHandler as jest.Mock).mock.calls.at(-1)[0]({eventType: 'right', eventKeyAction: 0}));
  await waitFor(() => expect(screen.getByText('Native seek failed')).toBeTruthy());
  expect(screen.getByTestId('blocked')).toBeTruthy();
  expect(player.play).toHaveBeenCalledTimes(1);
  screen.unmount();
});

test('media error cancels a seek queued before native dispatch', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValue({ok: true, json: async () => valid} as Response);
  const screen = render(<PlayerScreen {...props} />);
  await waitFor(() => expect(screen.getByText('broadcast · Verified flash reduction')).toBeTruthy());
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  const listener = player.subscribe.mock.calls[0][0] as (event: PlayerEvent) => void;
  act(() => listener({type: 'canplay', currentTime: 0, duration: 12, paused: true, playbackRate: 1}));
  await waitFor(() => expect(player.play).toHaveBeenCalledTimes(1));
  const {useTVEventHandler} = require('../src/player/TVPlatform');
  fireEvent(screen.getByRole('adjustable'), 'focus');
  jest.useFakeTimers();
  try {
    act(() => {
      (useTVEventHandler as jest.Mock).mock.calls.at(-1)[0]({eventType: 'right', eventKeyAction: 0});
      listener({type: 'error', currentTime: 0, duration: 12, paused: true, playbackRate: 1,
        error: new PlaybackError('media', 'Media interrupted')});
    });
    act(() => {jest.advanceTimersByTime(100);});
    expect(screen.getByText('Unsupported media or playback failure. Media interrupted')).toBeTruthy();
    expect(screen.getByTestId('blocked')).toBeTruthy();
    expect(player.seek).not.toHaveBeenCalled();
    expect(player.play).toHaveBeenCalledTimes(1);
  } finally {jest.useRealTimers(); screen.unmount();}
});
