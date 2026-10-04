// HazardTrack 1.0 reference overlay; deliberately never starts video playback.
export async function attachHazardTrack(video, overlay, url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('HazardTrack download failed');
  const track = await response.json();
  if (track.format !== 'hazardtrack' || track.format_version !== '1.0' ||
      track.verifier?.passes !== true || track.verifier.residual_events.length ||
      track.unresolved_segments?.length) throw new Error('Unverified HazardTrack');
  if (!Array.isArray(track.veils)) throw new Error('Invalid veil list');
  for (const cue of track.veils) {
    if (![cue.t_on, cue.t_off, cue.ramp_in_s, cue.ramp_out_s, cue.alpha, cue.gray]
      .every(Number.isFinite) || cue.t_off <= cue.t_on || cue.ramp_in_s < .5 ||
      cue.ramp_out_s < .5 || cue.alpha < 0 || cue.alpha > 1 || cue.gray < 0 || cue.gray > 1)
      throw new Error('Invalid veil cue');
  }
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
    overlay.style.backgroundColor = `rgb(${best.gray * 255},${best.gray * 255},${best.gray * 255})`;
    frame = requestAnimationFrame(draw);
  }
  draw();
  return () => { cancelAnimationFrame(frame); overlay.style.opacity = '0'; };
}
