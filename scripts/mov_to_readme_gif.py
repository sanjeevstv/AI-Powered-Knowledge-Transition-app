#!/usr/bin/env python3
"""Convert first 30s of a .mov to a README-friendly GIF (scaled, reduced FPS)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_mov", type=Path)
    p.add_argument("output_gif", type=Path)
    p.add_argument("--seconds", type=float, default=30.0, help="Max clip length")
    p.add_argument("--width", type=int, default=720, help="Output width in px")
    p.add_argument("--fps", type=int, default=8, help="Output GIF FPS")
    args = p.parse_args()

    if not args.input_mov.is_file():
        print(f"Missing input: {args.input_mov}", file=sys.stderr)
        return 1

    args.output_gif.parent.mkdir(parents=True, exist_ok=True)

    reader = imageio.get_reader(str(args.input_mov), "ffmpeg")
    meta = reader.get_meta_data() or {}
    fps_src = float(meta.get("fps", 30) or 30)
    step = max(1, int(round(fps_src / args.fps)))
    max_idx = int(args.seconds * fps_src)

    frames: list[np.ndarray] = []
    for idx, frame in enumerate(reader):
        if idx >= max_idx:
            break
        if idx % step != 0:
            continue
        img = Image.fromarray(frame).convert("RGB")
        w, h = img.size
        if w > args.width:
            nh = int(h * (args.width / w))
            img = img.resize((args.width, nh), Image.Resampling.LANCZOS)
        frames.append(np.asarray(img))

    reader.close()

    if not frames:
        print("No frames extracted; check ffmpeg plugin / video codec.", file=sys.stderr)
        return 1

    imageio.mimsave(
        str(args.output_gif),
        frames,
        format="GIF",
        fps=args.fps,
        loop=0,
    )
    size_kb = args.output_gif.stat().st_size / 1024
    print(f"Wrote {args.output_gif} ({len(frames)} frames, ~{size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
