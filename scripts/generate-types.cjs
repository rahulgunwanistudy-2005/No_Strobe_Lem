const fs = require('node:fs/promises');
const path = require('node:path');
const {compile} = require('json-schema-to-typescript');
const Ajv = require('ajv/dist/2020').default;
const addFormats = require('ajv-formats');
const standaloneCode = require('ajv/dist/standalone').default;

async function main() {
  const root = path.resolve(__dirname, '..');
  const source = JSON.parse(await fs.readFile(path.join(root, 'spec/schema/hazardtrack.schema.json'), 'utf8'));
  const types = await compile(source, 'HazardTrack', {
    bannerComment: '/* Generated from HazardTrack JSON Schema. Do not edit. */',
    style: {singleQuote: false},
  });
  const ajv = new Ajv({strict: false, allErrors: true, code: {source: true}});
  addFormats(ajv);
  const validator = standaloneCode(ajv, ajv.compile(source));
  const outputs = {
    'hazardtrack.ts': types,
    'hazardtrack.schema.json': JSON.stringify(source, null, 2) + '\n',
    'validateHazardTrack.js': '/* Generated runtime guard. Do not edit. */\n' + validator,
    'validateHazardTrack.d.ts': "import type {HazardTrack} from './hazardtrack';\n" +
      'declare const validate: { (value: unknown): value is HazardTrack; errors?: {message?: string}[] | null };\n' +
      'export = validate;\n',
  };
  for (const [name, content] of Object.entries(outputs)) {
    const output = path.join(root, 'tv/src/types', name);
    if (process.argv.includes('--check')) {
      if (await fs.readFile(output, 'utf8') !== content) {
        throw new Error(`Generated contract drift: ${name}; run npm run types:generate`);
      }
    } else {
      await fs.mkdir(path.dirname(output), {recursive: true});
      await fs.writeFile(output, content);
    }
  }
}
main().catch(error => {console.error(error.message); process.exitCode = 1;});
