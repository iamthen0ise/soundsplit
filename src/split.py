import argparse
import io
import json
import os
import sys

from pydub import AudioSegment

import librosa


def split(
    input_file,
    output_dir,
    appl_silence=500,
    frame_length=4096,
    hop_length=256,
    split_trshld=40,
    min_power=-30,
):

    silence_segment = AudioSegment.silent(duration=appl_silence)

    audio_src, samplerate = librosa.core.load(input_file)

    audio_chunks = librosa.effects.split(
        audio_src, top_db=split_trshld, frame_length=frame_length, hop_length=hop_length
    )

    cur_idx = 1
    json_data = []
    for (start, end) in audio_chunks:
        sys.stdout.write(f"\r Writing chunks {cur_idx} of {len(audio_chunks)}")
        audio = audio_src[start:end]
        if max(librosa.core.power_to_db(audio)) < min_power:
            continue
        if librosa.core.get_duration(audio) < float(0.5):
            continue
        else:
            start_sec = librosa.core.samples_to_time(start, samplerate)
            end_sec = librosa.core.samples_to_time(end, samplerate)
            audio, _ = librosa.effects.trim(audio, top_db=60)
            audio = librosa.util.normalize(audio)
            buf = io.BytesIO()
            filename = os.path.join(output_dir, "file_{:05d}.ogg".format(cur_idx))
            librosa.output.write_wav(buf, audio, samplerate)

            sg = AudioSegment.from_wav(buf)
            sg = silence_segment + sg + silence_segment

            sg.export(filename, "ogg")

            json_data.append(
                {
                    filename: {
                        "start": round(start_sec, 1),
                        "end": round(end_sec, 1),
                        "asr": "-",
                        "found": "-",
                        "shift": 0,
                        "diff": 0,
                    }
                }
            )
            sys.stdout.flush()
        cur_idx += 1

    with open("output/result.json", "w") as json_file:
        json.dump(json_data, json_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split audio files by silence.")
    parser.add_argument("--input-file", type=str, help="Input MP3 file")
    parser.add_argument("--output-dir", type=str, help="Ogg files dir")
    parser.add_argument(
        "--appl-silence", type=int, help="Applied silence for resulting chunk"
    )
    parser.add_argument("--frame-length", type=int, help="Librosa frame lenght")
    parser.add_argument(
        "--hop-length", type=int, help="Librosa interval between analysis frames"
    )
    parser.add_argument(
        "--split-trshld", type=int, help="Power diff used for split in dB"
    )
    parser.add_argument(
        "--min-power", type=int, help="Minimal power used for detect speech in dB"
    )

    args = parser.parse_args()

    split(
        input_file=args.input_file,
        output_dir=args.output_dir,
        appl_silence=args.appl_silence,
        frame_length=args.frame_length,
        hop_length=args.hop_length,
        split_trshld=args.split_trshld,
        min_power=args.min_power,
    )
