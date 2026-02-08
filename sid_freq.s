;         C    C#   D    D#   E    F    F#   G    G#   A    A#   B
SIDLO:
    !byte $15, $25, $37, $49, $5D, $72, $88, $9F, $B8, $D2, $EE, $0B  ; octave 0
    !byte $2A, $4B, $6E, $93, $BA, $E3, $0F, $3E, $6F, $A4, $DB, $16  ; octave 1
    !byte $54, $96, $DC, $26, $74, $C7, $1F, $7C, $DF, $47, $B6, $2C  ; octave 2
    !byte $A8, $2C, $B7, $4B, $E8, $8E, $3E, $F8, $BE, $8F, $6C, $57  ; octave 3
    !byte $50, $58, $6F, $96, $D0, $1C, $7C, $F0, $7B, $1E, $D9, $AE  ; octave 4
    !byte $A0, $AF, $DD, $2D, $A0, $38, $F8, $E1, $F6, $3B, $B2, $5C  ; octave 5
    !byte $40, $5E, $BB, $5A, $3F, $6F, $EF, $C2, $ED, $76, $63, $B9  ; octave 6
    !byte $7F, $BC, $75, $B4, $7F, $DF, $DE, $84, $D9, $ED, $C6, $00  ; octave 7 (H-7 missing)


;         C    C#   D    D#   E    F    F#   G    G#   A    A#   B
SIDHI:
    !byte $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $02  ; octave 0
    !byte $02, $02, $02, $02, $02, $02, $03, $03, $03, $03, $03, $04  ; octave 1
    !byte $04, $04, $04, $05, $05, $05, $06, $06, $06, $07, $07, $08  ; octave 2
    !byte $08, $09, $09, $0A, $0A, $0B, $0C, $0C, $0D, $0E, $0F, $10  ; octave 3
    !byte $11, $12, $13, $14, $15, $17, $18, $19, $1B, $1D, $1E, $20  ; octave 4
    !byte $22, $24, $26, $29, $2B, $2E, $30, $33, $36, $3A, $3D, $41  ; octave 5
    !byte $45, $49, $4D, $52, $57, $5C, $61, $67, $6D, $74, $7B, $82  ; octave 6
    !byte $8A, $92, $9B, $A4, $AE, $B8, $C3, $CF, $DB, $E8, $F6, $00  ; octave 7 (H-7 missing)

; semitone numbers
NOTE_C  = 0
NOTE_CS = 1   ; C#  (Db)
NOTE_D  = 2
NOTE_DS = 3   ; D#  (Eb)
NOTE_E  = 4
NOTE_F  = 5
NOTE_FS = 6   ; F#  (Gb)
NOTE_G  = 7
NOTE_GS = 8   ; G#  (Ab)
NOTE_A  = 9
NOTE_AS = 10  ; A#  (Bb)
NOTE_B  = 11

; flats (aliases)
NOTE_DB = NOTE_CS
NOTE_EB = NOTE_DS
NOTE_GB = NOTE_FS
NOTE_AB = NOTE_GS
NOTE_BB = NOTE_AS

; idx = (octave+1)*12 + semitone
!macro NOTEIDX semitone, octave {
    !byte ((octave + 1) * 12 + semitone)
}

; melody example (C major arpeggio)
ARP_C_MAJOR:
    NOTEIDX NOTE_C, 4     ; C-4  -> index 48
    NOTEIDX NOTE_E, 4     ; E-4  -> index 52
    NOTEIDX NOTE_G, 4     ; G-4  -> index 55
    NOTEIDX NOTE_C, 5     ; C-5  -> index 60
