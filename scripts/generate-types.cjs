const fs = require("node:fs/promises");
const path = require("node:path");
const { compile } = require("json-schema-to-typescript");

async function main() {
  const root = path.resolve(__dirname, "..");
  const source = JSON.parse(await fs.readFile(path.join(root, "spec/schema/hazardtrack.schema.json"), "utf8"));
  const output = path.join(root, "spec/generated/hazardtrack.ts");
  const types = await compile(source, "HazardTrack", {
    bannerComment: "/* Generated from HazardTrack JSON Schema. Do not edit. */",
    style: { singleQuote: false },
  });
  if (process.argv.includes("--check")) {
    if (await fs.readFile(output, "utf8") !== types) throw new Error("Generated TypeScript contract drift; run npm run types:generate");
  } else {
    await fs.mkdir(path.dirname(output), { recursive: true });
    await fs.writeFile(output, types);
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
