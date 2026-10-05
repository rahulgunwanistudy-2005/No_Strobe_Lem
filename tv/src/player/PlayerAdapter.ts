export const playerEvents = [
  'timeupdate', 'seeking', 'seeked', 'play', 'playing', 'pause',
  'ratechange', 'waiting', 'ended', 'error', 'loadedmetadata', 'canplay',
] as const;
export type PlayerEventType = (typeof playerEvents)[number];

export class PlaybackError extends Error {
  constructor(public readonly code: 'initialize' | 'load' | 'play' | 'surface' | 'media' | 'closed', message: string) {
    super(message);
    this.name = 'PlaybackError';
  }
}
export interface PlayerSnapshot {
  currentTime: number;
  duration: number;
  playbackRate: number;
  paused: boolean;
}
export interface PlayerEvent extends PlayerSnapshot {
  type: PlayerEventType;
  error?: PlaybackError;
}
export interface PlayerAdapter extends PlayerSnapshot {
  load(url: string): Promise<void>;
  play(): Promise<void>;
  pause(): void;
  seek(time: number): void;
  subscribe(listener: (event: PlayerEvent) => void): () => void;
  dispose(): Promise<void>;
}
