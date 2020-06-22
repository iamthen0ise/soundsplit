python 3.7

```
virtualenv venv -p python3 \
&& source venv/bin/activate \
&& pip install -r requirements.txt
```

RUN:
```
python src/split.py  \
--input-file=input/input.mp3 \
--output-dir=output/ \
--appl-silence=500 \
--frame-length=4096 \
--hop-length=256 \
--split-trshld=40 \
--min-power=-30
```

```
python src/asr.py \
--input-dir=$(pwd)/output \
--iam=<Yandex cloud iam token> \
--folder-id=<Yandex cloud folder id> \
--output-file=$(pwd)/output/result.txt \
--limit=50
```

```
python src/text.py \
--text-input=$(pwd)/input/source.txt \
--test-sents=$(pwd)/output/result.txt \
--output-file=$(pwd)/output/similar.txt
```