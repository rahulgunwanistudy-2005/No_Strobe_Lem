// HazardTrack 1.0 reader; validation completes before hosts enable playback.
export async function attachHazardTrack(video, overlay, url) {
  video.pause();
  const response = await fetch(url);
  if (!response.ok) throw new Error('HazardTrack download failed');
  const payload = (await response.text()).replace(/\r\n/g, '\n');
  let track;
  if (payload.startsWith('WEBVTT')) {
    const blocks = payload.trim().split(/\r?\n\s*\r?\n/);
    const metadata = blocks.find(block => block.startsWith('NOTE hazardtrack\n'));
    if (!metadata) throw new Error('Missing verification metadata');
    track = {...JSON.parse(metadata.split('\n').slice(1).join('\n')), veils: []};
    for (const block of blocks) {
      if (block.startsWith('NOTE') || block.startsWith('WEBVTT')) continue;
      const lines = block.split(/\r?\n/);
      if (lines.length !== 3 || !lines[1].includes(' --> ')) throw new Error('Invalid VTT cue');
      track.veils.push(JSON.parse(lines[2]));
    }
  } else track = JSON.parse(payload);
  if (track.format !== 'hazardtrack' || track.format_version !== '1.0' ||
      track.verifier?.passes !== true || !Array.isArray(track.verifier.residual_events) ||
      track.verifier.residual_events.length || track.unresolved_segments?.length)
    throw new Error('Unverified HazardTrack');
  if (!Array.isArray(track.veils)) throw new Error('Invalid veil list');
  for (const cue of track.veils) {
    if (typeof cue.id !== 'string' ||
        ![cue.t_on, cue.t_off, cue.ramp_in_s, cue.ramp_out_s, cue.alpha, cue.gray]
          .every(Number.isFinite) || cue.t_off <= cue.t_on || cue.ramp_in_s < .5 ||
        cue.ramp_out_s < .5 || cue.alpha < 0 || cue.alpha > 1 || cue.gray < 0 || cue.gray > 1)
      throw new Error('Invalid veil cue');
  }
  const metadataTrack = video.addTextTrack('metadata', 'HazardTrack');
  metadataTrack.mode = 'hidden';
  const cues = track.veils.map(cue => new VTTCue(Math.max(0, cue.t_on - cue.ramp_in_s),
    Math.max(.001, cue.t_off + cue.ramp_out_s), JSON.stringify(cue)));
  for (const cue of cues) metadataTrack.addCue(cue);
  let frame;
  function draw() {
    const t = video.currentTime;
    let best = {alpha: 0, gray: 0, id: ''};
    for (const cue of track.veils) {
      const alpha = cue.alpha * Math.max(0, Math.min(1,
        (t - cue.t_on + cue.ramp_in_s) / cue.ramp_in_s,
        (cue.t_off + cue.ramp_out_s - t) / cue.ramp_out_s));
      if (alpha > best.alpha || (alpha > 0 && alpha === best.alpha &&
          (cue.gray < best.gray || (cue.gray === best.gray && cue.id < best.id))))
        best = {...cue, alpha};
    }
    overlay.style.opacity = String(best.alpha);
    const gray = Math.round(best.gray * 255);
    overlay.style.backgroundColor = `rgb(${gray},${gray},${gray})`;
    frame = requestAnimationFrame(draw);
  }
  draw();
  return () => {
    video.pause(); cancelAnimationFrame(frame);
    for (const cue of cues) metadataTrack.removeCue(cue);
    metadataTrack.mode = 'disabled'; overlay.style.opacity = '1';
  };
}
