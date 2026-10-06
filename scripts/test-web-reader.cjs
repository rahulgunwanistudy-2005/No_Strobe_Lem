const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const root = require('node:path').resolve(__dirname, '..');
const source = fs.readFileSync(root + '/spec/examples/web/reader.js', 'utf8').replace('export async function', 'async function');
const fixture = JSON.parse(fs.readFileSync(root + '/spec/examples/timeline_conformance.json'));
const template = JSON.parse(fs.readFileSync(root + '/spec/examples/contract.hzt.json'));
let requested, callbacks = [], canceled = [];
const context = vm.createContext({
  fetch: async () => ({ok: true, text: async () => requested}),
  VTTCue: class {constructor(startTime, endTime, text) {Object.assign(this, {startTime, endTime, text});}},
  requestAnimationFrame: callback => {callbacks.push(callback); return callbacks.length;},
  cancelAnimationFrame: handle => canceled.push(handle),
});
vm.runInContext(source, context);
const makeVideo = () => ({currentTime: 0, paused: false, pause() {this.paused = true;},
  addTextTrack() {return this.metadata = {cues: [], addCue(cue) {this.cues.push(cue);},
    removeCue(cue) {this.cues = this.cues.filter(item => item !== cue);}};}});
(async () => {
  const track = {...template, veils: fixture.cues,
    verifier: {...template.verifier, passes: true, residual_events: []}, unresolved_segments: []};
  requested = JSON.stringify(track);
  const video = makeVideo(), overlay = {style: {opacity: '1'}};
  const cleanup = await context.attachHazardTrack(video, overlay, '/fixture.json');
  assert.equal(video.paused, true);
  assert.equal(video.metadata.mode, 'hidden');
  for (const sample of fixture.samples) {
    video.currentTime = sample.time;
    callbacks.shift()();
    assert.ok(Math.abs(Number(overlay.style.opacity) - sample.alpha) < 1e-6);
    assert.equal(overlay.style.backgroundColor, `rgb(${Math.round(sample.gray * 255)},${Math.round(sample.gray * 255)},${Math.round(sample.gray * 255)})`);
  }
  cleanup(); assert.equal(video.metadata.cues.length, 0); assert.equal(overlay.style.opacity, '1');
  const metadata = {...track}; delete metadata.veils;
  requested = 'WEBVTT\r\n\r\nNOTE hazardtrack\r\n' + JSON.stringify(metadata) + '\r\n\r\n' +
    track.veils.map((cue, i) => `${i}\r\n00:00:00.000 --> 00:00:10.000\r\n${JSON.stringify(cue)}`).join('\r\n\r\n');
  const second = makeVideo(); (await context.attachHazardTrack(second, {style: {}}, '/fixture.vtt'))();
  assert.equal(second.metadata.cues.length, 0);
  for (const malformed of [
    {...track, verifier: {...track.verifier, passes: false}},
    {...track, veils: [{...track.veils[0], alpha: 2}]},
    {...track, unresolved_segments: [{start: 1, end: 2}]},
  ]) {
    requested = JSON.stringify(malformed);
    await assert.rejects(context.attachHazardTrack(makeVideo(), {style: {opacity: '1'}}, '/bad.json'));
  }
  console.log('Web reader: 500 timeline samples, WebVTT and refusal gates passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
