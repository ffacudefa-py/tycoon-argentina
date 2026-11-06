#!/usr/bin/env bash
# Corta coin.mp3 (5 golpes de moneda separados por silencios) en 5 sonidos sueltos:
# assets/audio/coin_0..4.wav (mono, 44,1 kHz, -6 dB, fundido de 40 ms al final).
# Sfx.play("coin") elige uno distinto cada vez y le varía el tono.
# Uso: tools/audio/split_coin.sh [ruta/a/coin.mp3]
set -euo pipefail
SRC="${1:-$HOME/Descargas/coin.mp3}"
cd "$(dirname "$0")/../.."
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -ac 1 -ar 44100 "$TMP/full.wav"
i=0
# Inicio y fin de cada golpe (medidos con silencedetect a -40 dB).
for seg in "0.0 0.47" "1.04 1.47" "2.035 2.48" "3.03 3.45" "4.03 4.44"; do
  set -- $seg
  d=$(python3 -c "print(round($2-$1,3))")
  fo=$(python3 -c "print(round($2-$1-0.04,3))")
  ffmpeg -hide_banner -loglevel error -y -ss "$1" -t "$d" -i "$TMP/full.wav" \
    -af "volume=-6dB,afade=t=out:st=$fo:d=0.04" -c:a pcm_s16le "assets/audio/coin_$i.wav"
  i=$((i+1))
done
echo "listo: assets/audio/coin_0..4.wav"
