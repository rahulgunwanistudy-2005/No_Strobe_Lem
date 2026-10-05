const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '../tv');
const mode = process.argv[2];
if (!['Debug', 'Release'].includes(mode)) throw new Error('Choose Debug or Release');
const names = ['sync.mp4', 'compositing.mp4'];
const destinations = names.map(name => path.join(root, 'assets/raw', name));
if (destinations.some(file => fs.existsSync(file))) {
  throw new Error('Calibration files must live in calibration-assets, not release assets/raw');
}
// The SDK retains copied raw assets between builds; a clean Release staging tree
// prevents a prior Debug package from leaking calibration stimuli into Release.
if (mode === 'Release') fs.rmSync(path.join(root, 'build'), {recursive: true, force: true});
try {
  if (mode === 'Debug') {
    for (let i = 0; i < names.length; i++) {
      fs.copyFileSync(path.join(root, 'calibration-assets', names[i]), destinations[i]);
    }
  }
  const result = spawnSync('react-native', ['build-vega', '--build-type', mode], {cwd: root, stdio: 'inherit'});
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
} finally {
  if (mode === 'Debug') for (const file of destinations) fs.rmSync(file, {force: true});
}
