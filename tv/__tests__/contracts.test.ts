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
