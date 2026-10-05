import contract from '../../spec/examples/contract.hzt.json';
import type {HazardTrack} from '../src/types/hazardtrack';
const fixture: HazardTrack = {...contract, format: 'hazardtrack', format_version: '1.0', profile: 'broadcast',
  media: {...contract.media, transfer: 'sdr'},
  verifier: {...contract.verifier, passes: true, offsets_checked_s: [-0.15, 0, 0.15]},
  events: [{id: 'event', kind: 'luma_flash', severity: 'fail', t_start: 1, t_end: 2,
    peak_changes_per_s: 8, peak_area_fraction: 1, peak_delta_cd_m2: 40, regime: 'absolute'}],
  veils: [{id: 'veil', t_on: 0.75, t_off: 2.25, ramp_in_s: 0.5, ramp_out_s: 0.5,
    alpha: 0.5, gray: 0.25, covers: ['event']}]};
import {loadTrack, parseTrack} from '../src/track/load';
import {parseWebvtt} from '../src/track/parseWebvtt';

const binding = {contentId: fixture.media.content_id, sourceSha256: fixture.media.source_sha256};
test('accepts the complete contract and ignores unknown fields', () => {
  expect(parseTrack({...fixture, future: 1}, binding).format).toBe('hazardtrack');
});
test.each([
  {...fixture, verifier: {...fixture.verifier, passes: false}},
  {...fixture, verifier: {...fixture.verifier, offsets_checked_s: []}},
  {...fixture, format_version: '2.0'},
  {...fixture, veils: [{...fixture.veils[0], alpha: 1.1}]},
  {...fixture, veils: [{...fixture.veils[0], ramp_in_s: 0}]},
  {...fixture, veils: [{...fixture.veils[0], covers: ['missing']}]},
  {...fixture, events: [...fixture.events, fixture.events[0]]},
  {...fixture, events: [{...fixture.events[0], t_end: 9999}]},
  {...fixture, generated_at: 'not-a-date'},
])('refuses malformed or unverified content', value => {expect(() => parseTrack(value)).toThrow();});
test('refuses a track belonging to another source', () => {
  expect(() => parseTrack(fixture, {...binding, contentId: 'other'})).toThrow();
  expect(() => parseTrack(fixture, {...binding, sourceSha256: 'f'.repeat(64)})).toThrow();
});
test('fetch failure never supplies a playable track', async () => {
  const fetcher = jest.spyOn(global, 'fetch').mockResolvedValue({ok: false, status: 404} as Response);
  await expect(loadTrack('http://localhost/track', binding)).rejects.toThrow('404');
  fetcher.mockRestore();
});
test('WebVTT portability reader preserves canonical cue payloads', () => {
  const {events, veils, ...metadata} = fixture;
  const vtt = 'WEBVTT\n\nNOTE hazardtrack\n' + JSON.stringify(metadata) +
    '\n\nNOTE hazardtrack-events\n' + JSON.stringify(events) +
    veils.map(cue => `\n\n${cue.id}\n00:00:00.000 --> 00:00:09.000\n${JSON.stringify(cue)}`).join('');
  expect(parseWebvtt(vtt).veils).toEqual(veils);
});
