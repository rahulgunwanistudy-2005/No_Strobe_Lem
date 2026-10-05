import type {PlayerEvent, PlayerSnapshot} from '../player/PlayerAdapter';

declare const performance: {now(): number};

/** Monotonic seconds; prediction stops during pause, seek, buffering and end. */
export class MediaClock {
  private media = 0;
  private mono: number;
  private rate = 1;
  private duration = Infinity;
  private advancing = false;

  constructor(private readonly monotonic: () => number = () => performance.now() / 1000) {
    this.mono = monotonic();
  }

  now(): number {
    const elapsed = this.advancing ? Math.max(0, this.monotonic() - this.mono) * this.rate : 0;
    return Math.max(0, Math.min(this.duration, this.media + elapsed));
  }

  anchor(snapshot: PlayerSnapshot, advancing = !snapshot.paused): void {
    if (!Number.isFinite(snapshot.currentTime) || !Number.isFinite(snapshot.playbackRate) || snapshot.playbackRate <= 0) {
      throw new Error('Invalid media clock anchor');
    }
    this.duration = Number.isFinite(snapshot.duration) && snapshot.duration > 0 ? snapshot.duration : Infinity;
    this.media = Math.max(0, Math.min(this.duration, snapshot.currentTime));
    this.mono = this.monotonic();
    this.rate = snapshot.playbackRate;
    this.advancing = advancing;
  }

  update(event: PlayerEvent): void {
    if (event.type === 'timeupdate') {
      const predicted = this.now();
      // Re-anchor every observation; retain continuous prediction for small jitter.
      const currentTime = Math.abs(predicted - event.currentTime) > 0.1 ? event.currentTime : predicted;
      this.anchor({...event, currentTime}, this.advancing && !event.paused);
      return;
    }
    const hold = ['pause', 'waiting', 'seeking', 'ended', 'error'].includes(event.type);
    this.anchor(event, !hold && !event.paused);
  }
}
