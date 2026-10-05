import {VideoPlayer} from '@amazon-devices/react-native-w3cmedia/dist/headless';
import {PlaybackError, playerEvents} from './PlayerAdapter';
import type {PlayerAdapter, PlayerEvent, PlayerEventType} from './PlayerAdapter';

/** Owns one native player; initialization, surface callbacks and teardown race safely. */
export class VegaW3CPlayer implements PlayerAdapter {
  private readonly native: VideoPlayer;
  private initialization?: Promise<void>;
  private closing?: Promise<void>;
  private ready = false;
  private closed = false;
  private surface?: string;
  private attached?: string;
  private listeners = new Set<(event: PlayerEvent) => void>();
  private handlers = new Map<PlayerEventType, () => void>();

  constructor(native: VideoPlayer = new VideoPlayer()) {this.native = native;}
  get currentTime(): number {return this.ready ? this.native.currentTime : 0;}
  get duration(): number {return this.ready ? this.native.duration : NaN;}
  get playbackRate(): number {return this.ready ? this.native.playbackRate : 1;}
  set playbackRate(rate: number) {
    this.assertOpen();
    if (!this.ready || !Number.isFinite(rate) || rate <= 0) {throw new PlaybackError('load', 'Invalid playback rate');}
    this.native.playbackRate = rate;
  }
  get paused(): boolean {return !this.ready || this.native.paused;}

  private assertOpen(): void {
    if (this.closed) {throw new PlaybackError('closed', 'Player is closed');}
  }
  private initialize(): Promise<void> {
    this.assertOpen();
    if (!this.initialization) {
      this.initialization = this.native.initialize().then(() => {
        this.ready = true;
        if (this.closed) {return;}
        this.native.autoplay = false;
        for (const type of playerEvents) {
          const handler = () => this.emit(type);
          this.handlers.set(type, handler);
          this.native.addEventListener(type, handler);
        }
        this.attach();
      }).catch((error: unknown) => {
        throw new PlaybackError('initialize', error instanceof Error ? error.message : 'Player initialization failed');
      });
    }
    return this.initialization;
  }
  private emit(type: PlayerEventType): void {
    const event: PlayerEvent = {type, currentTime: this.currentTime, duration: this.duration,
      playbackRate: this.playbackRate, paused: this.paused};
    if (type === 'error') {
      event.error = new PlaybackError('media', this.native.error?.message || `Video playback failed (code ${this.native.error?.code ?? 'unknown'})`);
    }
    for (const listener of this.listeners) {listener(event);}
  }
  private attach(): void {
    if (this.ready && !this.closed && this.surface && this.surface !== this.attached) {
      if (this.attached) {this.native.clearSurfaceHandle(this.attached);}
      this.native.setSurfaceHandle(this.surface);
      this.attached = this.surface;
    }
  }
  async surfaceCreated(handle: string): Promise<void> {
    this.assertOpen();
    this.surface = handle;
    await this.initialize();
    try {this.attach();}
    catch (error: unknown) {throw new PlaybackError('surface', error instanceof Error ? error.message : 'Cannot attach surface');}
  }
  surfaceDestroyed(handle: string): void {
    if (this.surface === handle) {this.surface = undefined;}
    if (this.attached === handle && this.ready) {
      this.native.pause();
      this.native.clearSurfaceHandle(handle);
      this.attached = undefined;
      this.emit('waiting');
    }
  }
  async load(url: string): Promise<void> {
    await this.initialize();
    this.assertOpen();
    try {
      this.native.pause();
      this.native.src = url;
    } catch (error: unknown) {
      throw new PlaybackError('load', error instanceof Error ? error.message : 'Cannot load video');
    }
  }
  async play(): Promise<void> {
    this.assertOpen();
    if (!this.ready || !this.attached) {throw new PlaybackError('surface', 'Video surface is not ready');}
    try {await this.native.play();}
    catch (error: unknown) {throw new PlaybackError('play', error instanceof Error ? error.message : 'Cannot play video');}
  }
  pause(): void {if (this.ready && !this.closed) {this.native.pause();}}
  seek(time: number): void {
    this.assertOpen();
    if (!Number.isFinite(time) || time < 0 || !this.ready) {throw new PlaybackError('load', 'Invalid seek');}
    this.native.currentTime = Number.isFinite(this.duration) ? Math.min(this.duration, time) : time;
  }
  subscribe(listener: (event: PlayerEvent) => void): () => void {
    this.listeners.add(listener);
    return () => {this.listeners.delete(listener);};
  }
  dispose(): Promise<void> {
    if (this.closing) {return this.closing;}
    this.closed = true;
    this.closing = (async () => {
      try {await this.initialization;}
      catch {return;} // Initialization error has already reached the caller.
      if (!this.ready) {return;}
      try {
        this.native.pause();
        if (this.attached) {this.native.clearSurfaceHandle(this.attached);}
      } finally {
        for (const [type, handler] of this.handlers) {this.native.removeEventListener(type, handler);}
        this.listeners.clear();
        this.handlers.clear();
        this.attached = undefined;
        try {await this.native.deinitialize();} finally {this.ready = false;}
      }
    })();
    return this.closing;
  }
}
