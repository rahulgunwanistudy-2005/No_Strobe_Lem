import {parseTrack, TrackError} from './load';
import type {HazardTrack} from '../types/hazardtrack';

/** Portability only. JSON is the app's canonical reader. Payload times are authoritative. */
export function parseWebvtt(text: string): HazardTrack {
  const blocks = text.replace(/\r\n/g, '\n').trim().split(/\n\s*\n/);
  if (blocks.shift()?.trim() !== 'WEBVTT') {throw new TrackError('Missing WEBVTT header');}
  let metadata: Record<string, unknown> | undefined;
  let events: unknown = [];
  const veils: unknown[] = [];
  for (const block of blocks) {
    const lines = block.split('\n');
    if (lines[0] === 'NOTE hazardtrack') {
      metadata = JSON.parse(lines.slice(1).join('\n')) as Record<string, unknown>;
    } else if (lines[0] === 'NOTE hazardtrack-events') {
      events = JSON.parse(lines.slice(1).join('\n'));
    } else if (!lines[0].startsWith('NOTE')) {
      const timing = lines.findIndex(line => line.includes(' --> '));
      if (timing < 0 || lines.length !== timing + 2) {throw new TrackError('Invalid WebVTT cue');}
      veils.push(JSON.parse(lines[timing + 1]));
    }
  }
  if (!metadata) {throw new TrackError('Missing HazardTrack metadata');}
  return parseTrack({...metadata, events, veils});
}
