import {execFileSync} from 'node:child_process';
import {readFileSync, readdirSync} from 'node:fs';
import {join} from 'node:path';

test('generated types and bundled runtime schema have no drift', () => {
  expect(() => execFileSync(process.execPath, ['../scripts/generate-types.cjs', '--check'], {cwd: process.cwd()})).not.toThrow();
});
test('platform dependencies are isolated inside player', () => {
  const scan = (directory: string) => {
    for (const entry of readdirSync(directory, {withFileTypes: true})) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) {scan(path);}
      else if (/\.[jt]sx?$/.test(path) && !path.includes('/player/')) {
        expect(readFileSync(path, 'utf8')).not.toMatch(/(?:from\s*|require\()['"]@amazon-devices\//);
      }
    }
  };
  scan(join(process.cwd(), 'src'));
});

test('viewer copy avoids prohibited claims and default/raw playback has no release path', () => {
  const sources: string[] = [];
  const scan = (directory: string) => {
    for (const entry of readdirSync(directory, {withFileTypes: true})) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) {scan(path);}
      else if (/\.[jt]sx?$/.test(path)) {sources.push(readFileSync(path, 'utf8'));}
    }
  };
  scan(join(process.cwd(), 'src'));
  expect(sources.join('\n')).not.toMatch(/seizure-proof|prevents seizures|medically safe|certified|Harding-compliant/i);
  expect(sources.join('\n')).not.toMatch(/rawMode|rawPlayback|allowRaw|unmitigatedMode/);
  const app = readFileSync(join(process.cwd(), 'src/App.tsx'), 'utf8');
  expect(app).toMatch(/if \(__DEV__ && calibration\)/);
});
