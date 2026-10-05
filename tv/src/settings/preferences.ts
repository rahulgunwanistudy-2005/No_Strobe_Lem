import {AsyncStorage} from '../player/TVPlatform';
import type {Profile} from '../types/hazardtrack';
export interface Preferences {profile: Profile; household: 'family' | 'kids'; warnAhead: boolean}
export const defaultPreferences: Preferences = {profile: 'broadcast', household: 'family', warnAhead: true};
export const preferenceKey = 'nostrobe.preferences.v1';
export function parsePreferences(raw: string | null): Preferences {
  if (raw === null) {return {...defaultPreferences};}
  const value: unknown = JSON.parse(raw);
  if (!value || typeof value !== 'object') {throw new Error('Saved settings are invalid');}
  const p = value as Record<string, unknown>;
  if (!['broadcast', 'local', 'kids'].includes(String(p.profile)) ||
      !['family', 'kids'].includes(String(p.household)) || typeof p.warnAhead !== 'boolean') {
    throw new Error('Saved settings are invalid');
  }
  return {profile: p.household === 'kids' ? 'kids' : p.profile as Profile,
    household: p.household as Preferences['household'], warnAhead: p.warnAhead};
}
export function chooseHousehold(p: Preferences, household: Preferences['household']): Preferences {
  return {...p, household, profile: household === 'kids' ? 'kids' : 'broadcast'};
}
export interface PreferenceStorage {getItem(key: string): Promise<string | null>; setItem(key: string, value: string): Promise<void>}
export class PreferenceStore {
  private writes: Promise<void> = Promise.resolve();
  constructor(private readonly storage: PreferenceStorage = AsyncStorage) {}
  async load(): Promise<Preferences> {return parsePreferences(await this.storage.getItem(preferenceKey));}
  save(p: Preferences): Promise<void> {
    const raw = JSON.stringify(p);
    const write = this.writes.catch(() => {}).then(() => this.storage.setItem(preferenceKey, raw));
    this.writes = write;
    return write;
  }
}
