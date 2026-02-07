#!/usr/bin/env python3
import argparse
import wave
import re
from pathlib import Path

PAL_CIA_HZ  = 985248.0
NTSC_CIA_HZ = 1022727.0

def parse_hex16(s: str) -> int:
    s = s.strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    return int(s, 16)

def extract_bytes_from_monitor_dump(text: str) -> bytes:
    """
    Extract raw bytes from a VICE/C64-style monitor dump.

    Works even if the hex bytes are grouped with extra spaces.
    Ignores the PETSCII/ASCII column because those tokens won't match 2-hex-digit bytes.
    """
    out = bytearray()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        tokens = line.split()
        if not tokens:
            continue

        # Expect first token like >C:7400 (or C:7400, .:7400, etc.)
        # We won't depend on exact prefix; just skip the first token if it contains a colon + hex address.
        start_idx = 0
        if ":" in tokens[0]:
            start_idx = 1

        for t in tokens[start_idx:]:
            # Only accept pure byte tokens like "7f", "F0", etc.
            if len(t) == 2 and all(c in "0123456789abcdefABCDEF" for c in t):
                out.append(int(t, 16))
            # else: ignore (PETSCII column etc.)

    return bytes(out)

def bytes_to_nibbles(data: bytes, order: str):
    nibbles = []
    if order == "hi":
        for b in data:
            nibbles.append((b >> 4) & 0x0F)
            nibbles.append(b & 0x0F)
    else:
        for b in data:
            nibbles.append(b & 0x0F)
            nibbles.append((b >> 4) & 0x0F)
    return nibbles

def nibbles_to_pcm16(nibbles, center=7.5):
    out = bytearray()
    for n in nibbles:
        x = (n - center) / center
        x = max(-1.0, min(1.0, x))
        s = int(round(x * 32767))
        out += int(s & 0xFFFF).to_bytes(2, "little", signed=False)
    return bytes(out)

def hz_from_speed(speed: int, region: str) -> float:
    base = PAL_CIA_HZ if region == "PAL" else NTSC_CIA_HZ
    return base / speed

def main():
    ap = argparse.ArgumentParser(
        description="Convert C64 monitor dump ($D418 digis) to WAV"
    )
    ap.add_argument("input", type=Path, help="Text file with monitor dump")
    ap.add_argument("output", type=Path, help="Output WAV file")
    ap.add_argument("--speed", type=str, help="CIA timer value (hex, e.g. 00A0)")
    ap.add_argument("--hz", type=float, help="Override sample rate directly")
    ap.add_argument("--region", choices=["PAL", "NTSC"], default="PAL")
    ap.add_argument("--order", choices=["hi", "lo"], default="hi")
    ap.add_argument("--center", type=float, default=7.5)
    args = ap.parse_args()

    text = args.input.read_text()
    data = extract_bytes_from_monitor_dump(text)

    if not data:
        raise SystemExit("No bytes extracted from input")

    if args.hz is not None:
        hz = args.hz
    elif args.speed is not None:
        hz = hz_from_speed(parse_hex16(args.speed), args.region)
    else:
        hz = 8000.0

    nibbles = bytes_to_nibbles(data, args.order)
    pcm16 = nibbles_to_pcm16(nibbles, args.center)

    with wave.open(str(args.output), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(round(hz)))
        wf.writeframes(pcm16)

    print(f"Bytes extracted : {len(data)}")
    print(f"Samples         : {len(nibbles)}")
    print(f"Sample rate     : {hz:.2f} Hz")
    print(f"Wrote           : {args.output}")

if __name__ == "__main__":
    main()
