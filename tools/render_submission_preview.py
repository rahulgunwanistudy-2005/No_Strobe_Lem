"""Render a nonflashing 20-second schematic; no source-video frames are used."""

from pathlib import Path

from matplotlib import get_data_path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def render() -> None:
    frames = []
    font = ImageFont.truetype(str(Path(get_data_path()) / "fonts/ttf/DejaVuSans.ttf"), 22)
    small = ImageFont.truetype(str(Path(get_data_path()) / "fonts/ttf/DejaVuSans.ttf"), 15)
    for index in range(100):
        time = index / 5
        opacity = 0.44 * max(0, min(1, (time - 6) / 1, (13 - time) / 1))
        frame = Image.new("RGB", (880, 360), "#101c2a")
        draw = ImageDraw.Draw(frame)
        draw.text((32, 22), "No Strobe-lem | Captions for your eyes", font=font, fill="#eaf4ff")
        draw.text(
            (32, 60),
            "Schematic only: a timed veil, no flashing footage",
            font=small,
            fill="#a9bacb",
        )
        draw.rounded_rectangle((32, 102, 320, 254), radius=12, fill="#344354")
        gray = round(52 * (1 - opacity) + 128 * opacity)
        draw.rounded_rectangle((32, 102, 320, 254), radius=12, fill=(gray, gray + 8, gray + 16))
        draw.text((48, 160), f"Veil opacity {opacity:.2f}", font=font, fill="#eaf4ff")
        draw.text((360, 104), "Continuous ramp + plateau", font=small, fill="#a9bacb")
        points = [(360, 240), (477, 240), (497, 144), (594, 144), (614, 240), (750, 240)]
        draw.line(points, fill="#8cf0d1", width=3)
        x = round(360 + time / 20 * 390)
        draw.line((x, 130, x, 258), fill="#eaf4ff", width=2)
        for x_pos, label in [(360, "0s"), (477, "6s"), (594, "12s"), (730, "20s")]:
            draw.text((x_pos, 268), label, font=small, fill="#a9bacb")
        draw.rounded_rectangle((32, 302, 848, 338), radius=8, fill="#1b2c3e")
        draw.text(
            (48, 311),
            "HazardTrack sidecar -> media clock -> uniform veil",
            font=small,
            fill="#c5d7e8",
        )
        frames.append(frame)
    output = ROOT / "docs/assets/veil-timeline.gif"
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output, save_all=True, append_images=frames[1:], duration=200, loop=0, optimize=False
    )
    frames[50].save(output.with_suffix(".png"))


if __name__ == "__main__":
    render()
