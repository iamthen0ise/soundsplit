import urllib.request
import json


def transcribe_yandex(audio_data, iam_token, folder_id, language):
    params = f"topic=general&folderId={folder_id}&lang={language}"
    url = urllib.request.Request(
        "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?%s" % params,
        data=audio_data,
    )
    url.add_header("Authorization", "Bearer %s" % iam_token.strip())

    response_data = urllib.request.urlopen(url).read().decode("UTF-8")
    decoded_data = json.loads(response_data)

    if decoded_data.get("error_code") is None:
        return decoded_data.get("result")
