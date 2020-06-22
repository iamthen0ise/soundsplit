import urllib.request
import json
import os

import argparse
import re


def transcribe_ogg(input_dir, output_file, iam_token, folder_id, limit=None):
    result_strings = []

    work_dir = os.listdir(input_dir)
    work_dir.sort()

    if len(work_dir) < 1:
        raise Exception("No files in input dir. Exit")

    for filename in work_dir[:limit]:
        _, ext = os.path.splitext(filename)
        if not ext == ".ogg":
            continue

        with open(os.path.join(input_dir, filename), "rb") as f:
            data = f.read()

        params = "&".join(["topic=general", "folderId=%s" % folder_id, "lang=ru-RU"])
        try:
            url = urllib.request.Request(
                "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?%s" % params,
                data=data,
            )
            url.add_header("Authorization", "Bearer %s" % iam_token)

            responseData = urllib.request.urlopen(url).read().decode("UTF-8")
            decodedData = json.loads(responseData)
        except Exception:
            print("Error, file is ", filename)
            continue

        if decodedData.get("error_code") is None:
            phrase = decodedData.get("result")
            print(phrase, "————", filename)
            result_strings.append(phrase)

    with open(output_file, "w") as file:
        for item in result_strings:
            file.write(f"{item}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ASR for audio files.")
    parser.add_argument("--input-dir", type=str, help="Ogg files dir")
    parser.add_argument("--output-file", type=str, help="Output file")
    parser.add_argument("--iam", type=str, help="YC IAM Token")
    parser.add_argument("--folder-id", type=str, help="YC Folder ID")
    parser.add_argument("--limit", type=int, help="Limit files to transcribe")

    args = parser.parse_args()

    input_dir = args.input_dir
    iam_token = args.iam
    folder_id = args.folder_id
    output_file = args.output_file
    limit = args.limit

    transcribe_ogg(input_dir, output_file, iam_token, folder_id, limit)

