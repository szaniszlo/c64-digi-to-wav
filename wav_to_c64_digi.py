#!/usr/bin/env python3
import argparse
import wave
import re
from pathlib import Path
import numpy as np

PAL_CIA_HZ  = 985248.0
NTSC_CIA_HZ = 1022727.0

def parse_hex16(s: str) -> int:
    s = s.strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    return int(s, 16)

def hz_from_speed(speed: int, region: str) -> float:
    base = PAL_CIA_HZ if region.upper() == "PAL" else NTSC_CIA_HZ
    if speed <= 0:
        raise ValueError("speed must be > 0")
    return base / float(speed)

def read_wav_mono_float(path: Path) -> tuple[np.ndarray, int]:
    """Return mono float32 array in [-1,1] and sample rate."""
    with wave.open(str(path), "rb") as wf:
        ch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sampwidth != 2:
        raise SystemExit(f"Only 16-bit PCM WAV supported (sampwidth=2). Got {sampwidth} bytes.")

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

    if ch == 2:
        data = data.reshape(-1, 2).mean(axis=1)
    elif ch != 1:
        raise SystemExit(f"Only mono or stereo WAV supported. Got {ch} channels.")

    # Normalize int16 to [-1, 1]
    data /= 32768.0
    return data, sr

def resample_linear(x: np.ndarray, src_sr: int, dst_sr: float) -> np.ndarray:
    """Simple linear resampler (good enough for 4-bit digis)."""
    if dst_sr <= 0:
        raise ValueError("dst_sr must be > 0")
    if src_sr == dst_sr:
        return x

    ratio = dst_sr / float(src_sr)
    n_out = int(np.round(len(x) * ratio))
    if n_out <= 0:
        return np.zeros(0, dtype=np.float32)

    # positions in input
    t = np.linspace(0, len(x) - 1, n_out, dtype=np.float32)
    i0 = np.floor(t).astype(np.int32)
    i1 = np.minimum(i0 + 1, len(x) - 1)
    frac = t - i0
    y = (1.0 - frac) * x[i0] + frac * x[i1]
    return y.astype(np.float32)

def float_to_nibbles(x: np.ndarray, center: float = 7.5, gain: float = 1.0, dither: float = 0.0) -> np.ndarray:
    """
    Map float audio [-1,1] to 4-bit values [0..15].
    center=7.5 means x=0 maps around mid-scale.
    gain scales before quantization.
    dither is uniform noise amplitude in LSB units (0..1 typical).
    """
    # Apply gain and clip
    y = np.clip(x * gain, -1.0, 1.0)

    # Optional dither in "nibble steps": 1 step corresponds to 2/15 in [-1,1] if centered,
    # but we implement dither in the nibble domain after mapping for simplicity.
    # Map [-1,1] -> [0,15] with center at 7.5:
    # y = -1 -> 0, y = +1 -> 15
    n = (y + 1.0) * 7.5  # 0..15

    if dither > 0.0:
        n = n + (np.random.uniform(-0.5, 0.5, size=n.shape).astype(np.float32) * dither)

    n = np.rint(n).astype(np.int32)
    n = np.clip(n, 0, 15).astype(np.uint8)
    return n

def pack_nibbles(nibbles: np.ndarray, order: str = "hi") -> bytes:
    """Pack 2 nibbles into one byte."""
    if len(nibbles) % 2 != 0:
        nibbles = np.append(nibbles, np.uint8(7))  # pad with mid value

    hi = nibbles[0::2]
    lo = nibbles[1::2]

    if order == "hi":
        packed = (hi << 4) | lo
    else:  # "lo" means low nibble first in time
        packed = (lo << 4) | hi

    return packed.astype(np.uint8).tobytes()

def make_monitor_dump(data: bytes, start_addr: int = 0x7400, prefix: str = ">C:") -> str:
    """16 bytes/line, grouped 4 bytes with double-spaces, plus ASCII column."""
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        addr = start_addr + i

        # build 4 groups of up to 4 bytes each
        groups = []
        for g in range(0, len(chunk), 4):
            grp = chunk[g:g+4]
            groups.append(" ".join(f"{b:02x}" for b in grp))

        hex_col = "  ".join(groups)  # two spaces between 4-byte groups

        # pad hex column so ASCII aligns (16 bytes => "xx " * 15 + "xx" plus extra group spaces)
        lines.append(f"{prefix}{addr:04x}  {hex_col:<47}")

    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Convert mono 16-bit WAV to C64 $D418 packed-nibble digi (.bin).")
    ap.add_argument("input_wav", type=Path, help="Input WAV (16-bit PCM, mono or stereo).")
    ap.add_argument("output_bin", type=Path, help="Output raw digi bytes (.bin).")
    ap.add_argument("--speed", type=str, default=None, help="CIA timer value hex (e.g. 00A0).")
    ap.add_argument("--region", choices=["PAL", "NTSC"], default="PAL", help="Clock basis for --speed.")
    ap.add_argument("--hz", type=float, default=None, help="Target sample rate (nibbles/sec). Overrides --speed.")
    ap.add_argument("--order", choices=["hi", "lo"], default="hi", help="Nibble time order within each byte.")
    ap.add_argument("--gain", type=float, default=1.0, help="Gain before quantization (try 0.8..1.5).")
    ap.add_argument("--dither", type=float, default=0.0, help="Uniform dither in nibble LSB units (0..1).")
    ap.add_argument("--limit_bytes", type=int, default=None, help="Trim/pad output to this many bytes.")
    ap.add_argument("--dump", type=Path, default=None, help="Also write a monitor-style text dump here.")
    ap.add_argument("--dump_addr", type=str, default="7400", help="Start address for dump (hex, default 7400).")
    args = ap.parse_args()

    x, src_sr = read_wav_mono_float(args.input_wav)

    print

    if args.hz is not None:
        dst_hz = float(args.hz)
    elif args.speed is not None:
        dst_hz = hz_from_speed(parse_hex16(args.speed), args.region)
    else:
        dst_hz = 8000.0

    # Resample to nibble rate
    y = resample_linear(x, src_sr, dst_hz)

    # Quantize to 4-bit nibbles
    n = float_to_nibbles(y, gain=args.gain, dither=args.dither)

    # Pack into bytes
    packed = pack_nibbles(n, order=args.order)

    # Optional trim/pad to exact byte length
    if args.limit_bytes is not None:
        b = bytearray(packed)
        if len(b) >= args.limit_bytes:
            packed = bytes(b[:args.limit_bytes])
        else:
            packed = bytes(b + bytes([0x77]) * (args.limit_bytes - len(b)))  # pad with mid-ish pattern

    args.output_bin.write_bytes(packed)

    print(f"Input WAV SR         : {src_sr} Hz")
    print(f"Target nibble rate   : {dst_hz:.2f} Hz")
    print(f"Generated nibbles    : {len(n)}")
    print(f"Output bytes         : {len(packed)}")
    if args.speed:
        print(f"Speed ({args.region})        : 0x{parse_hex16(args.speed):04x}")

    if args.dump is not None:
        start_addr = int(args.dump_addr, 16)
        dump_text = make_monitor_dump(packed, start_addr=start_addr)
        args.dump.write_text(dump_text)
        print(f"Wrote dump text      : {args.dump}")

if __name__ == "__main__":
    main()
