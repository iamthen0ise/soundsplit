Requirements:

```
python 3.7
ffmpeg
```

Installation:

```bash
virtualenv venv -p python3 \
&& source venv/bin/activate \
&& pip install -r requirements.txt

```

RUN:

Audio Split

```bash
usage: split.py [-h] [-i INPUT_FILE] [-o OUTPUT_DIR] [-p PREFIX]
                [-fl FRAME_LENGTH] [-fs FRAME_SHIFT] [-l LIMIT]
                [-sr SAMPLERATE] [-q Q_FACTOR]

            Split audio files by RMS energy and Zero-Crossing.

            Frame length is length of audio sample window
            Frame shift is a distance between audio samples

            Q-Factor is a factor used for smoothing RMS and Zero-Crossing peak values.
            e.g. if RMS=0.5 and Q-Factor=0.8 the resulting RMS would be 0.5*0.8

            Limit is a length of audio that should be splitter from start.
```

Example:

```bash
python src/split.py --input-file <input file path> \
--output-dir <output dir path> \
--prefix <prefix> \
--frame-length 500 \
--frame-shift 50 \
--limit 300 \
--samplerate 44100 \
--q-factor 0.7
```

ASR

```bash
usage: asr.py [-h] [-i INPUT_DIR] [-ll LANGUAGE] [-l LIMIT] [-j JSONFILE]
              [--iam IAM] [--folder-id FOLDER_ID]

            Process ASR for audio files.

            ** CREDENTIALS **

            Please specify `--iam` and `--folder-id` for Yandex Services.
            See https://cloud.yandex.ru/docs/iam/operations/iam-token/create for reference.

            For Google Speech To Text use environmental variables and config as described here —
            https://cloud.google.com/speech-to-text/docs/libraries#linux-or-macos
```

Example:

```bash
python src/asr.py \
--input-dir <dir with splitted chunks> \
--iam <Yandex cloud iam token> \
--folder-id <Yandex cloud folder id> \
--language ru-RU \
--limit 50 \
--jsonfile <path to resulting json file>
```

TEXT EVALUATION

```bash
usage: text_eval.py [-h] [-i TEXT_INPUT] [-j JSONFILE] [-q Q_FACTOR]
                    [-qmax Q_FACTOR_MAX] [-qstep Q_FACTOR_STEP]

        Find similar text.

        Q-Factor is Levenshtein Distance value.
        Default Q-Factor used for retrieve text chunks from source text file.
        If chunks cannot be retrieved, Q-Factor increases step by step by value of Q-Factor Step
        Until reach Maximal Q-Factor.

        Using default values of Q-Factor higher than 7 may slowdown the script.
```

Example:

```bash
python src/text_eval.py \
--text-input <file with text source path> \
--jsonfile <result json file path \
--q-factor 3 \
--q-factor-max 70 \
--q-factor-step 5
```
