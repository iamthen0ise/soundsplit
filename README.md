python 3.7

```
virtualenv venv -p python3 \
&& source venv/bin/activate \
&& pip install -r requirements.txt
```

RUN:

```
python src/split.py -i input/input.mp3 -o output/ -of mp3 -p chunk -fl 500 -fs 50 -l 300 -sr 44100
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
python src/text_eval.py -i input/source.txt -j output/result.json -q 3 -qmax 70 -qstep 5
```
