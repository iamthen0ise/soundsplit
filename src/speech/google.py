from google.cloud import speech_v1
from google.cloud.speech_v1.gapic import enums


def transcribe_google(audio_data, language, sample_rate):
    client = speech_v1.SpeechClient()

    sample_rate_hertz = sample_rate
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    config = {
        "language": language,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
    }
    with audio_data as f:
        content = f.read()
    audio = {"content": content}

    response = client.recognize(config, audio)
    for result in response.results:
        alternative = result.alternatives[0]

    return alternative
