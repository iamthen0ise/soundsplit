import argparse
import io
import json
import logging
import os
import sys
from typing import List, Optional, Tuple

import librosa
import numpy as np
from pydub import AudioSegment

from log import LOGGING_FMT

logger = logging.getLogger("splitter")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOGGING_FMT)
handler.setFormatter(formatter)
logger.addHandler(handler)


silence_segment = AudioSegment.silent(duration=300)


def get_bounds(frame_idxs: List[float], frame_shift: int, frame_rate: int) -> Tuple[float, float]:
    """
        .. py:function:: get_bounds(frame_idxs, frame_shift, frame_rate)

        Count bounds for each frame.

        :param np.array frame_idxs: Detected frame indexes
        :param int frame_shift: Frame shift
        :param int frame_rate: Frame rate
        :return: Start and end bounds for each frame
        :rtype: tuple
    """
    start_idxs = [frame_idxs[0]]
    end_idxs = []

    shapeofidxs = np.shape(frame_idxs)
    for i in range(shapeofidxs[0] - 1):
        if (frame_idxs[i + 1] - frame_idxs[i]) != 1:
            end_idxs.append(frame_idxs[i])
            start_idxs.append(frame_idxs[i + 1])

    end_idxs.append(frame_idxs[-1])
    if end_idxs[-1] == start_idxs[-1]:
        end_idxs.pop()
        start_idxs.pop()
    if len(start_idxs) == len(end_idxs):
        logging.error("Error! Number of start indexes not matching number of end indexes")
        exit
    start_idxs = np.array(start_idxs)
    end_idxs = np.array(end_idxs)
    start_t = start_idxs * frame_shift / frame_rate  # type: ignore
    end_t = end_idxs * frame_shift / frame_rate  # type: ignore
    return start_t, end_t


def process(
    input_file: str,
    output_dir: str,
    samplerate: Optional[int],
    prefix: str,
    frame_length: int,
    frame_shift: int,
    q_factor: float,
    limit: Optional[int],
):
    """
        .. py:function:: process(
            input_file, output_dir, samplerate, prefix, frame_length, frame_shift, q_factor,  limit)

        Process audio from file and split it into chunks.
        Dumps metadata to json.

        :param str input_file: Input file path
        :param str output_dir: Path for output chunks and json file directory
        :param int [samplerate]: (Optional) Samplerate of input audio
        :param str prefix: Chunk file name prefix
        :param int frame_length: Frame length
        :param int frame_shift: Frame shift
        :param float q_factor: Quality Factor
        :param int [limit]: Input audio track length limit

        :return: 
        :rtype: None
    """
    logger.info("Loading audio")

    _, ext = os.path.splitext(input_file)
    ext = ext.replace(".", "")
    pydub_kwargs = {"format": ext}
    if ext == "mp3":
        pydub_kwargs["codec"] = ext
    elif ext == "ogg":
        pydub_kwargs["codec"] = "opus"

    audio_src, frame_rate = librosa.load(input_file, sr=samplerate, duration=limit)
    audio_src = librosa.util.normalize(audio_src)

    frame_len = int(frame_length * frame_rate / 1000)
    frame_shift = int(frame_shift * frame_rate / 1000)

    rms = librosa.feature.rms(audio_src, frame_length=frame_len, hop_length=frame_shift)
    rms = rms[0]
    rms = librosa.util.normalize(rms, axis=0)

    logger.info("Using RMS for peak detection")
    logger.info(f"Mean RMS is: {np.mean(rms)}")
    logger.info(f"RMS standard deviation is {np.std(rms)}")

    logger.info("Calculating Zero-Crossing rate")
    zero_x = librosa.feature.zero_crossing_rate(
        audio_src, frame_length=frame_len, hop_length=frame_shift, threshold=0
    )
    zero_x = zero_x[0]
    zero_x = librosa.util.normalize(zero_x, axis=0)

    logger.info(f"Mean Zero-Crossing rate is: {np.mean(zero_x)}")
    logger.info(f"Zero-Crossing rate standard deviation is {np.std(zero_x)}")

    frame_idxs = np.where(
        (rms > np.std(rms) * q_factor) | (zero_x > np.average(zero_x) * q_factor)
    )[0]

    logger.info("Calculating bounds for splitting.")

    start_t, end_t = get_bounds(frame_idxs, frame_shift, frame_rate)

    json_data = {}

    logger.info("Start splitting.")
    for idx, (start, end) in enumerate(zip(start_t, end_t)):  # type: ignore
        start_s = librosa.core.time_to_samples(start, frame_rate)
        end_s = librosa.core.time_to_samples(end, frame_rate)
        audio = audio_src[start_s:end_s]

        if len(audio) == 0:
            continue

        audio = librosa.util.normalize(audio)
        filename = prefix + "_{:05d}.{}".format(idx, ext)

        logger.info(f"Writing chunks: {filename}")

        buf = io.BytesIO()
        librosa.output.write_wav(buf, audio, frame_rate)

        try:
            sg = AudioSegment.from_wav(buf)
            sg = silence_segment + sg + silence_segment
            sg.export(os.path.join("output", filename), **pydub_kwargs)
            json_data[filename] = {
                "start": round(start, 1),
                "end": round(end, 1),
                "asr": None,
                "found": None,
                "shift": 0,
                "diff": 0,
            }

        except Exception as e:
            logger.error(e)
            continue

    logging.info("Split finished. Saving json file data")

    with open("output/result.json", "w") as json_file:
        json.dump(json_data, json_file)


def main():
    parser = argparse.ArgumentParser(
        description="""
            Split audio files by RMS energy and Zero-Crossing.

            Frame length is length of audio sample window
            Frame shift is a distance between audio samples

            Q-Factor is a factor used for smoothing RMS and Zero-Crossing peak values.
            e.g. if RMS=0.5 and Q-Factor=0.8 the resulting RMS would be 0.5*0.8

            Limit is a length of audio that should be splitter from start.

        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--input-file", type=str, help="Input file path")
    parser.add_argument("-o", "--output-dir", type=str, help="Ogg files dir")
    parser.add_argument(
        "-p", "--prefix", type=str, default="file", help="Output file name prefix"
    )
    parser.add_argument(
        "-fl", "--frame-length", type=int, default=1000, help="Librosa frame length"
    )
    parser.add_argument(
        "-fs", "--frame-shift", type=int, default=50, help="Librosa frame shift"
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=None, help="Source audio length from start"
    )
    parser.add_argument(
        "-sr", "--samplerate", type=int, default=None, help="Source audio samplerate"
    )
    parser.add_argument(
        "-q", "--q-factor", type=int, default=0.7, help="Qualify Factor"
    )

    args = parser.parse_args()
    kwargs = {
        "input_file": args.input_file,
        "output_dir": args.output_dir,
        "samplerate": args.samplerate,
        "prefix": args.prefix,
        "frame_length": args.frame_length,
        "frame_shift": args.frame_shift,
        "q_factor": args.q_factor,
        "limit": args.limit,
    }

    logger.info("settings loaded:")
    for k, v in kwargs.items():
        logger.info(f"{k}: {v}")

    process(**kwargs)


if __name__ == "__main__":
    main()
