import argparse
import io
import json
import logging
import os
import sys
from typing import Union

import pydub

from log import LOGGING_FMT
from speech.google import transcribe_google
from speech.yandex import transcribe_yandex

logger = logging.getLogger("asr")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(LOGGING_FMT)
handler.setFormatter(formatter)
logger.addHandler(handler)


SUPPORTED_EXT = [".wav", ".aiff", ".ogg", ".mp3", ".m4a", ".wma"]


def prepare_file(filename: str, to: str = "ogg") -> Union[io.BytesIO, None]:
    """
        .. py:function:: prepare_file(filename, to)

        Convert audio fragment to compatible format for sending to ASR engines

        :param str filename: File name
        :param str to: Output format (default="ogg")

        :return: BytesIO Object with audiofile data
        :rtype: io.BytesIO
    """
    _, ext = os.path.splitext(filename)
    if ext not in SUPPORTED_EXT:
        return None

    buf = io.BytesIO()
    audio = pydub.AudioSegment.from_file(filename)

    if to == "ogg":
        return audio.export(buf, "ogg", "opus", parameters=["-strict", "-2"])
    return audio.export(buf, ext.replace(".", ""))


def process(input_dir: str, iam_token: str, folder_id: str, jsonfile: str, language: str, limit: int = None) -> None:
    """
        .. py:function:: process(input_dir, iam_token, folder_id, jsonfile, language, limit)

        Processing input audio fragments through ASR engine and resulting into JSON File

        :param str input_dir: Path to directory with audio chunks
        :param str iam_token: IAM Token for Yandex Cloud
        :param str folder_id: Folder id for Yandex Cloud
        :param str jsonfile: Path to JSON File
        :param str language: Language Code, e.g. ru-RU, en-US
        :param int limit: Limit of processing files.


        :return: None
        :rtype: None
    """
    logger.info("Preparing for transcribation")
    work_dir = os.listdir(input_dir)
    work_dir.sort()

    result_data = {}

    if len(work_dir) < 1:
        raise Exception("No files in input dir. Exit")

    total = len(work_dir[:limit])
    for idx, filename in enumerate(work_dir[:limit]):
        logger.info(f"Transcribing file {idx} of {total}")
        file = prepare_file(os.path.join(input_dir, filename))
        if not file:
            continue

        with file as f:
            audio_data = f.read()

        try:
            if language == "ru-RU":
                result = transcribe_yandex(audio_data, iam_token, folder_id, language)
            else:
                result = transcribe_google(audio_data, language, sample_rate=48000)
            result_data[filename] = result
        except Exception as e:
            logger.error(f"Error while transcribing chunk {filename}", e)
            continue

    logger.info("Transcribing finished. Saving result to json file")

    with open(jsonfile, "r+") as file:  # type: ignore
        data = json.load(file)  # type: ignore
        for (fname, asr_string) in result_data.items():
            data[fname]["asr"] = asr_string
        file.seek(0)  # type: ignore
        json.dump(data, file, ensure_ascii=False)  # type: ignore


def main():
    parser = argparse.ArgumentParser(
        description="""
            Process ASR for audio files.

            ** CREDENTIALS **

            Please specify `--iam` and `--folder-id` for Yandex Services.
            See https://cloud.yandex.ru/docs/iam/operations/iam-token/create for reference.

            For Google Speech To Text use environmental variables and config as described here —
            https://cloud.google.com/speech-to-text/docs/libraries#linux-or-macos
    """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-i", "--input-dir", type=str, help="Input files dir")
    parser.add_argument("-ll", "--language", type=str, help="Language")
    parser.add_argument("-l", "--limit", type=int, help="Limit files to transcribe")
    parser.add_argument("-j", "--jsonfile", type=str, help="Path to resulting jsonfile")
    parser.add_argument("--iam", type=str, help="YC IAM Token")
    parser.add_argument("--folder-id", type=str, help="YC Folder ID")

    args = parser.parse_args()

    language = args.language
    if not language:
        logger.error("Please specify language code of input audio file.")
        exit(1)

    if language == "ru-RU" and not all((args.iam, args.folder_id)):
        logger.error(
            "Please provide both Yandex Cloud IAM Token and Folder ID."
            "See https://cloud.yandex.ru/docs/iam/operations/iam-token/create"
        )
        exit(1)

    elif language == "en-US" and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.error(
            "Please export GOOGLE_APPLICATION_CREDENTIALS to environment."
            "See https://cloud.google.com/speech-to-text/docs/libraries#linux-or-macos"
        )
        exit(1)

    kwargs = {
        "input_dir": args.input_dir,
        "iam_token": args.iam,
        "folder_id": args.folder_id,
        "language": args.language,
        "limit": args.limit,
        "jsonfile": args.jsonfile,
    }

    logger.info("settings loaded:")
    for k, v in kwargs.items():
        if k in ("iam_token", "folder_id") and v:
            logger.info(f"{k}: [hidden]")
        else:
            logger.info(f"{k}: {v}")

    process(**kwargs)


if __name__ == "__main__":
    main()
