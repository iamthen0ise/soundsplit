import argparse
import json
import logging
import re
import string
import os
import sys

import Levenshtein
from fuzzysearch import find_near_matches

from log import LOGGING_FMT

logger = logging.getLogger("text eval")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(LOGGING_FMT)
handler.setFormatter(formatter)
logger.addHandler(handler)


def normalize_text(text):
    normalized_text = text.lower()

    normalized_text = re.sub(r"\\d+", "", normalized_text)
    normalized_text = normalized_text.translate(
        str.maketrans("", "", string.punctuation)
    )
    normalized_text = normalized_text.strip()
    normalized_text = " ".join(normalized_text.split())
    return normalized_text


def get_fuzzymatches(sentence, text, q_factor, qmax, qstep):
    fuzzymatches = []
    while q_factor <= qmax:
        fuzzymatches = find_near_matches(sentence.lower(), text, max_l_dist=q_factor)
        if fuzzymatches:
            break
        q_factor += qstep
        if q_factor >= qmax:
            logger.warning(
                "Cannot continue fuzzing. Max Q-Factor reached."
                f"The sentence is `{sentence}`"
            )
            break
    return fuzzymatches


def get_distances(fuzzymatches, sentence):
    distances = []
    for match in fuzzymatches:
        distances.append((match, Levenshtein.distance(match.matched, sentence)))
    return sorted(distances, key=lambda x: x[1])


def dump_json(jsonfile, result_data):
    logger.info("Evaluating finished. Writing to JSON File")
    with open(jsonfile, "r+") as file:
        data = json.load(file)
        for (fname, values) in result_data.items():
            data[fname]["found"] = values["eval_string"]
            data[fname]["shift"] = values["shift"]
            data[fname]["diff"] = values["lev_dist"]
        file.seek(0)
        json.dump(data, file, ensure_ascii=False)

    logger.info(f"JSON file written. Resulting json file is {os.path.abspath(jsonfile)}")
    return True


def process(text_input, jsonfile, q_factor, qmax, qstep):
    result_data = {}

    with open(jsonfile, "r") as json_f:
        json_data = json.loads(json_f.read(), encoding="utf-8")

    with open(text_input, "r", encoding="utf-8") as text_f:
        text = text_f.read()

    normalized_text = normalize_text(text)

    logger.info("Start evaluating distance")

    total = len(json_data.items())
    for idx, (fname, item) in enumerate(json_data.items()):
        logger.info(f"Evaluating sentence {idx} of {total}")

        sentence = item.get("asr")
        if not sentence:
            continue

        fuzzymatches = get_fuzzymatches(
            sentence, normalized_text, q_factor, qmax, qstep
        )
        if not fuzzymatches:
            continue

        distances = get_distances(fuzzymatches, sentence)
        best = distances[0][0]

        ld = best.dist
        eval_str = best.matched
        shift = text.lower().find(eval_str)
        if shift == -1:
            shift = None

        result_data[fname] = {"lev_dist": ld, "shift": shift, "eval_string": eval_str}

    return dump_json(jsonfile, result_data)


def main():
    parser = argparse.ArgumentParser(
        description="""
        Find similar text.

        Q-Factor is Levenshtein Distance value.
        Default Q-Factor used for retrieve text chunks from source text file.
        If chunks cannot be retrieved, Q-Factor increases step by step by value of Q-Factor Step
        Until reach Maximal Q-Factor.

        Using default values of Q-Factor higher than 7 may slowdown the script.

    """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--text-input", type=str, help="Input TXT with source")
    parser.add_argument(
        "-j", "--jsonfile", type=str, help="Input JSON File with ASR results"
    )
    parser.add_argument(
        "-q", "--q-factor", type=int, default=5, help="Default Levenshtein distance"
    )
    parser.add_argument(
        "-qmax",
        "--q-factor-max",
        type=int,
        default=70,
        help="Step of Levenshtein distance increse",
    )
    parser.add_argument(
        "-qstep",
        "--q-factor-step",
        type=int,
        default=5,
        help="Max Possible Levenshtein distance",
    )

    args = parser.parse_args()

    kwargs = {
        "text_input": args.text_input,
        "jsonfile": args.jsonfile,
        "q_factor": args.q_factor,
        "qmax": args.q_factor_max,
        "qstep": args.q_factor_step,
    }

    process(**kwargs)


if __name__ == "__main__":
    main()
