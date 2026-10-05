import {config} from '../config';
import type {Profile} from '../types/hazardtrack';

export interface CatalogItem {
  content_id: string; source_sha256: string; title: string; duration_s: number;
  video: string; poster?: string; description?: string;
  tracks: Partial<Record<Profile, {url: string; hazard_count: number}>>;
  attribution: {credit: string; license: string; url: string; changes: string};
}
export class CatalogError extends Error {
  constructor(message: string) {super(message); this.name = 'CatalogError';}
}
const object = (value: unknown): Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {throw new CatalogError('Catalog has invalid data');}
  return value as Record<string, unknown>;
};
function string(value: unknown): string {
  if (typeof value !== 'string' || !value.trim()) {throw new CatalogError('Catalog has missing text');}
  return value;
}
export function assetUrl(path: string, media = false): string {
  if (/^https:\/\/[^/\s]+\//.test(path)) {return path;}
  if (!/^\/(?!\/)/.test(path) || /[\\\s?#]/.test(path) || path.split('/').includes('..')) {
    throw new CatalogError('Unsupported catalog asset URL');
  }
  return (media ? config.mediaBaseUrl : config.catalogBaseUrl) + path;
}
export function parseCatalog(value: unknown): CatalogItem[] {
  const catalog = object(value);
  if (catalog.version !== 1 || !Array.isArray(catalog.items)) {throw new CatalogError('Unsupported catalog format');}
  const items = catalog.items.map((raw): CatalogItem => {
    const item = object(raw), tracks = object(item.tracks), attribution = object(item.attribution);
    const parsed: CatalogItem = {
      content_id: string(item.content_id), source_sha256: string(item.source_sha256), title: string(item.title),
      duration_s: Number(item.duration_s), video: string(item.video), tracks: {},
      attribution: {credit: string(attribution.credit), license: string(attribution.license),
        url: string(attribution.url), changes: string(attribution.changes)},
    };
    if (!Number.isFinite(parsed.duration_s) || parsed.duration_s <= 0 || !/^[a-f0-9]{64}$/.test(parsed.source_sha256)) {
      throw new CatalogError('Invalid catalog media binding');
    }
    assetUrl(parsed.video, true);
    if (item.poster !== undefined) {parsed.poster = string(item.poster); assetUrl(parsed.poster);}
    if (item.description !== undefined) {parsed.description = string(item.description);}
    for (const profile of ['broadcast', 'local', 'kids'] as const) {
      if (tracks[profile] === undefined || tracks[profile] === null) {continue;}
      const entry = object(tracks[profile]);
      const url = string(entry.url), count = entry.hazard_count;
      assetUrl(url);
      if (typeof count !== 'number' || !Number.isInteger(count) || count < 0) {throw new CatalogError('Invalid hazard count');}
      parsed.tracks[profile] = {url, hazard_count: count};
    }
    return parsed;
  });
  if (new Set(items.map(item => item.content_id)).size !== items.length) {throw new CatalogError('Duplicate catalog title');}
  return items;
}
export async function loadCatalog(signal?: AbortSignal): Promise<CatalogItem[]> {
  const response = await fetch(config.catalogBaseUrl + config.catalogPath, {signal});
  if (!response.ok) {throw new CatalogError(`Catalog unavailable (${response.status}). Please retry.`);}
  return parseCatalog(await response.json());
}
