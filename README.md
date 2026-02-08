# C64 Digi to WAV

Scripts to covert between 4 bit (nibble) encoded audio and WAV PCM

### wav_to_c64_digi.py usage

1. Make a 256-byte kick at your “$00A0 ≈ 6 kHz” setting

```
python3 wav_to_c64_digi.py kick.wav kick.bin --speed 00A0 --region PAL --limit_bytes 256
```

2. Force exactly 6000 Hz (ignores CIA math)

```
python3 wav_to_c64_digi.py kick.wav kick_6k.bin --hz 6000 --limit_bytes 256
```

3. Also produce a monitor dump starting at $7400

```
python3 wav_to_c64_digi.py kick.wav kick.bin --speed 00A0 --limit_bytes 256 --dump kick_dump.txt --dump_addr 7400
```

4. If the nibble order sounds wrong on C64, flip it

```
python3 wav_to_c64_digi.py kick.wav kick.bin --hz 6000 --order lo
```

### c64_digi_to_wav.py usage

1. Use speed (00A0) with PAL timing (gives ~6158 Hz):

```
python3 c64_digi_to_wav.py kick.bin kick.wav --speed 00A0 --region PAL
```

2. Force exactly 6000 Hz (your “sounds closest” value):

```
python3 c64_digi_to_wav.py kick.bin kick_6000.wav --hz 6000
```

3. If the nibble order is reversed:

```
python3 c64_digi_to_wav.py kick.bin kick.wav --hz 6000 --order lo
```
