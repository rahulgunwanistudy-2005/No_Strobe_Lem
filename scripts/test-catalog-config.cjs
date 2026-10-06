const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const target = path.resolve(__dirname, '../tv/src/deployment.ts');
const original = fs.readFileSync(target);
const run = url => spawnSync(process.execPath, [path.resolve(__dirname, 'configure-catalog.cjs')], {
  env: {...process.env, NOSTROBE_CATALOG_URL: url}, encoding: 'utf8',
});
try {
  assert.equal(run('https://media.s3.ap-south-1.amazonaws.com/public/catalog.json').status, 0);
  const text = fs.readFileSync(target, 'utf8');
  assert.match(text, /"catalogBaseUrl": "https:\/\/media.s3.ap-south-1.amazonaws.com"/);
  assert.match(text, /"catalogPath": "\/public\/catalog.json"/);
  for (const url of ['http://example.com/catalog.json', 'https://user:pass@example.com/catalog.json',
    'https://example.com/catalog.json?secret=1', 'https://example.com/wrong.json']) {
    assert.notEqual(run(url).status, 0);
  }
} finally {fs.writeFileSync(target, original);}
console.log('Catalog build configuration checks passed');
