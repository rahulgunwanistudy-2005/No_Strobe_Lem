import fixture from '../assets/raw/demo.hzt.json';
import {hazardAhead, hazardTicks, skipTarget} from '../src/ui/hazards';
import {ProfileSwap} from '../src/track/profileSwap';
import {chooseHousehold, defaultPreferences, parsePreferences, PreferenceStore, preferenceKey} from '../src/settings/preferences';
import {assetUrl, parseCatalog} from '../src/catalog/api';
import type {HazardTrack} from '../src/types/hazardtrack';
jest.mock('../src/player/TVPlatform', () => ({AsyncStorage: {getItem: jest.fn(), setItem: jest.fn()}}));
const track = fixture as HazardTrack;

test('chip boundaries, warning toggle, pause-equivalent time and unresolved priority', () => {
  expect(hazardAhead(track, 0, true)?.id).toBe('illustrative_overlay');
  expect(hazardAhead(track, 7.99, true)?.id).toBe('illustrative_overlay');
  expect(hazardAhead(track, 8, true)).toBeUndefined();
  expect(hazardAhead(track, 4, false)).toBeUndefined();
  const unresolved = {...track, unresolved_segments: [{start: 5, end: 7, covers: [], reason: 'fixture'}]};
  expect(hazardAhead(unresolved, 1.999, false)).toBeUndefined();
  expect(hazardAhead(unresolved, 2, false)?.kind).toBe('unresolved');
  expect(hazardAhead(unresolved, 4, true)?.kind).toBe('unresolved');
  expect(hazardAhead(unresolved, 7.25, false)).toBeUndefined();
});
test('ticks distinguish covered warnings, warning-only events and unresolved tails', () => {
  const event = {id: 'warn', severity: 'warn' as const, t_start: 9, t_end: 11, kind: 'extended_flashing' as const,
    peak_changes_per_s: 3, peak_area_fraction: 0.3, peak_delta_cd_m2: null, regime: 'absolute' as const};
  const values = hazardTicks({...track, events: [event], unresolved_segments: [{start: 10, end: 11, covers: [], reason: 'fixture'}]});
  expect(values.map(tick => tick.kind)).toEqual(['veiled', 'warn', 'unresolved']);
  expect(values[0]).toMatchObject({left: 2 / 12, width: 6 / 12});
  expect(values[2].width).toBeCloseTo(1.25 / 12);
  expect(hazardTicks({...track, events: [event], veils: [{...track.veils[0], covers: ['warn']}]})).toHaveLength(1);
});
test('skip exits chained overlapping veils, including tails, and clamps at end', () => {
  const overlap = {...track, veils: [track.veils[0], {...track.veils[0], id: 'next', t_on: 7, t_off: 11.8}]};
  const segment = hazardAhead(overlap, 0, true)!;
  expect(skipTarget(overlap, segment)).toBe(12);
  expect(skipTarget(track, segment)).toBe(8);
});
test('profile swaps keep the active track, stage until frame commit, ignore stale responses and reject mismatches', async () => {
  const swap = new ProfileSwap();
  await swap.request('broadcast', async () => track); expect(swap.active).toBeUndefined();
  expect(swap.commit()).toBe(track);
  let finish!: (value: HazardTrack) => void;
  const old = swap.request('local', () => new Promise(resolve => {finish = resolve;}));
  expect(swap.active).toBe(track); expect(swap.state).toBe('loading');
  const kids = {...track, profile: 'kids' as const};
  await swap.request('kids', async () => kids); expect(swap.active).toBe(track);
  swap.commit(); finish({...track, profile: 'local'});
  expect(await old).toBe(false); expect(swap.active).toBe(kids);
  await swap.request('local', async () => track);
  expect(swap.state).toBe('error'); expect(swap.active).toBe(kids); expect(swap.commit()).toBeUndefined();
});
test('cancelled or failed swap cannot replace verification', async () => {
  const swap = new ProfileSwap();
  let finish!: (value: HazardTrack) => void;
  const pending = swap.request('broadcast', () => new Promise(resolve => {finish = resolve;}));
  swap.cancel(); finish(track); expect(await pending).toBe(false); expect(swap.commit()).toBeUndefined();
  await swap.request('broadcast', async () => {throw new Error('network');}); expect(swap.state).toBe('error');
});
test('Kids household automatically selects Kids, persists warning choice, validates stored data', () => {
  expect(chooseHousehold(defaultPreferences, 'kids').profile).toBe('kids');
  expect(parsePreferences('{"profile":"broadcast","household":"kids","warnAhead":false}')).toEqual({profile: 'kids', household: 'kids', warnAhead: false});
  expect(() => parsePreferences('{"profile":"raw"}')).toThrow();
  expect(parsePreferences(null)).toEqual(defaultPreferences);
});
test('settings writes remain ordered after a slow write and recover from failure', async () => {
  const writes: string[] = []; let release!: () => void;
  const storage = {getItem: jest.fn(async () => null), setItem: jest.fn(async (_key: string, value: string) => {
    writes.push(value); if (writes.length === 1) {await new Promise<void>(resolve => {release = resolve;});}
  })};
  const store = new PreferenceStore(storage);
  const first = store.save(defaultPreferences); const second = store.save(chooseHousehold(defaultPreferences, 'kids'));
  await Promise.resolve(); await Promise.resolve(); expect(writes).toHaveLength(1);
  release(); await Promise.all([first, second]); expect(JSON.parse(writes[1]).profile).toBe('kids');
  storage.setItem.mockRejectedValueOnce(new Error('disk')); await expect(store.save(defaultPreferences)).rejects.toThrow('disk');
  await store.save(defaultPreferences); expect(storage.setItem).toHaveBeenLastCalledWith(preferenceKey, JSON.stringify(defaultPreferences));
});
test('catalog bindings and URL policy reject broken entries without rewriting URLs', () => {
  expect(parseCatalog({version: 1, items: []})).toEqual([]);
  expect(() => parseCatalog({version: 1, items: [{tracks: {}}]})).toThrow();
  for (const path of ['//evil/video', '/../video', '/a\\b', 'http://evil/video', '/a/../video']) {expect(() => assetUrl(path)).toThrow();}
  expect(assetUrl('https://example.com/video.mp4', true)).toBe('https://example.com/video.mp4');
});

test('skip traverses unresolved and veiled overlaps without landing in either', () => {
  const mixed = {...track, unresolved_segments: [{start: 6, end: 9, covers: [], reason: 'fixture'}],
    veils: [track.veils[0], {...track.veils[0], id: 'last', t_on: 9, t_off: 10, ramp_out_s: 0.5}]};
  const first = hazardAhead(mixed, 0, true)!;
  expect(skipTarget(mixed, first)).toBe(10.5);
});

test('HTTPS HLS catalog URLs retain their exact source binding', () => {
  const item = {content_id: track.media.content_id, source_sha256: track.media.source_sha256,
    title: 'HLS fixture', duration_s: track.media.duration_s, video: 'https://media.example/vod/index.m3u8',
    tracks: {}, attribution: {credit: 'Fixture', license: 'Test', url: 'https://example.com/', changes: 'None'}};
  expect(parseCatalog({version: 1, items: [item]})[0].video).toBe(item.video);
});

test('catalog rejects credential and fragment URLs but permits signed HTTPS HLS', () => {
  for (const url of ['https://user:password@example.com/a', 'https://example.com/a#b', 'https://example.com/a\\b']) {
    expect(() => assetUrl(url)).toThrow();
  }
  expect(assetUrl('https://example.com/a.m3u8?token=fixture', true)).toBe('https://example.com/a.m3u8?token=fixture');
});
