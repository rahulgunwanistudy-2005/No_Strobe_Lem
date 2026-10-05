import validate from '../types/validateHazardTrack';
import type {HazardTrack} from '../types/hazardtrack';

export class TrackError extends Error {
  constructor(message: string, public readonly kind: 'invalid' | 'missing' | 'network' = 'invalid') {super(message); this.name = 'TrackError';}
}
export interface MediaBinding {contentId: string; sourceSha256: string}

export function parseTrack(value: unknown, binding?: MediaBinding): HazardTrack {
  if (!validate(value)) {throw new TrackError('HazardTrack is invalid: ' + validate.errors?.map(error => error.message).join('; '));}
  const track = value;
  if (!track.verifier.passes || track.verifier.residual_events.length ||
      !track.verifier.offsets_checked_s.length || (track.unresolved_segments?.length ?? 0) > 0) {
    throw new TrackError('This track has not passed verification');
  }
  if (binding && (track.media.content_id !== binding.contentId || track.media.source_sha256 !== binding.sourceSha256)) {
    throw new TrackError('HazardTrack does not match this video');
  }
  const ids = new Set(track.events.map(event => event.id));
  if (ids.size !== track.events.length || new Set(track.veils.map(cue => cue.id)).size !== track.veils.length) {
    throw new TrackError('HazardTrack contains duplicate ids');
  }
  if (track.events.some(event => event.t_start >= event.t_end || event.t_end > track.media.duration_s) ||
      track.veils.some(cue => cue.t_on >= cue.t_off || cue.covers.some(id => !ids.has(id)))) {
    throw new TrackError('HazardTrack timing or event references are invalid');
  }
  return track;
}

export async function loadTrack(url: string, binding: MediaBinding, signal?: AbortSignal): Promise<HazardTrack> {
  const response = await fetch(url, {signal});
  if (!response.ok) {throw new TrackError(`Cannot load HazardTrack (${response.status})`,
    response.status === 404 || response.status === 410 ? 'missing' : 'network');}
  return parseTrack(await response.json(), binding);
}
