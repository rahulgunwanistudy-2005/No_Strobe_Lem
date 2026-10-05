import React from 'react';
import {render, waitFor} from '@testing-library/react-native';
import contract from '../../spec/examples/contract.hzt.json';
import {App} from '../src/App';
import {VegaW3CPlayer} from '../src/player/VegaW3CPlayer';

jest.mock('../src/player/VegaW3CPlayer', () => ({VegaW3CPlayer: jest.fn().mockImplementation(() => ({
  load: jest.fn(async () => {}), play: jest.fn(async () => {}), pause: jest.fn(),
  subscribe: jest.fn(() => () => {}), dispose: jest.fn(async () => {}),
}))}));
jest.mock('../src/player/VideoSurface', () => ({VideoSurface: () => null}));
jest.mock('../src/veil/VeilLayer', () => {
  const {View} = require('react-native');
  return {VeilLayer: ({blocked}: {blocked: boolean}) => <View testID={blocked ? 'blocked' : 'unblocked'} />};
});
test('a failing verifier keeps video blocked and never loads or plays the native source', async () => {
  const fetcher = jest.spyOn(global, 'fetch')
    .mockResolvedValueOnce({ok: true, json: async () => ({title: 'Fixture', video: '/video.mp4',
      track: '/video.hzt.json', content_id: contract.media.content_id,
      source_sha256: contract.media.source_sha256})} as Response)
    .mockResolvedValueOnce({ok: true, json: async () => contract} as Response);
  const logger = jest.spyOn(console, 'error').mockImplementation(() => {});
  const screen = render(<App />);
  await waitFor(() => expect(screen.getByText('This track has not passed verification')).toBeTruthy());
  expect(screen.getByTestId('blocked')).toBeTruthy();
  const player = (VegaW3CPlayer as jest.Mock).mock.results[0].value;
  expect(player.load).not.toHaveBeenCalled();
  expect(player.play).not.toHaveBeenCalled();
  screen.unmount();
  expect(player.dispose).toHaveBeenCalledTimes(1);
  fetcher.mockRestore(); logger.mockRestore();
});
