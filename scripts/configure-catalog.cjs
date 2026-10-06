const fs = require('node:fs');
const path = require('node:path');
const destination = path.resolve(__dirname, '../tv/src/deployment.ts');
const catalog = process.env.NOSTROBE_CATALOG_URL;
const local = {
  catalogBaseUrl: 'http://127.0.0.1:8765',
  catalogPath: '/catalog.json',
  mediaBaseUrl: '/pkg/assets/raw',
};
let config = local;
if (catalog) {
  const url = new URL(catalog);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      !url.pathname.endsWith('/catalog.json')) {
    throw new Error('NOSTROBE_CATALOG_URL must be an HTTPS catalog.json URL without credentials or query');
  }
  config = {catalogBaseUrl: url.origin, catalogPath: url.pathname, mediaBaseUrl: url.origin};
}
const text = '// Generated public catalog configuration; contains no credentials.\n' +
  'export const deployment = ' + JSON.stringify(config, null, 2) + ' as const;\n';
if (process.argv.includes('--check')) {
  if (fs.readFileSync(destination, 'utf8') !== text) throw new Error('Catalog configuration drift');
} else fs.writeFileSync(destination, text);
