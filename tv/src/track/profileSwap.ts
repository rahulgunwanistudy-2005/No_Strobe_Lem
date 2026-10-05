import type {HazardTrack, Profile} from '../types/hazardtrack';
/** Only the most recent request may commit; the old verified track survives loading. */
export class ProfileSwap {
  private generation = 0;
  private staged?: HazardTrack;
  active?: HazardTrack;
  state: 'idle' | 'loading' | 'staged' | 'ready' | 'error' = 'idle';
  error?: unknown;
  async request(profile: Profile, load: () => Promise<HazardTrack>): Promise<boolean> {
    const generation = ++this.generation;
    this.staged = undefined; this.error = undefined; this.state = 'loading';
    try {
      const track = await load();
      if (generation !== this.generation) {return false;}
      if (track.profile !== profile) {throw new Error('HazardTrack does not match the selected profile');}
      this.staged = track; this.state = 'staged'; return true;
    } catch (error: unknown) {
      if (generation !== this.generation) {return false;}
      this.error = error; this.state = 'error'; return true;
    }
  }
  commit(): HazardTrack | undefined {
    if (this.state !== 'staged') {return undefined;}
    this.active = this.staged; this.staged = undefined; this.state = 'ready'; return this.active;
  }
  cancel(): void {++this.generation; this.staged = undefined; this.state = this.active ? 'ready' : 'idle';}
}
