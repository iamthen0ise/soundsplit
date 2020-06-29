import io
import json
import urllib.request
from typing import Union


def transcribe_yandex(audio_data: io.BytesIO, iam_token: str, folder_id: str, language: str) -> Union[str, None]:
    """
        .. py:function:: transcribe_google(audio_data, language, sample_rate)

        Transcribe given audio fragment in Google Speech API

        :param io.BytesIO audio_data: Audio fragment
        :param str iam_token: IAM Token for Yandex Cloud
        :param str folder_id: Folder id for Yandex Cloud
        :param str language: Language Code

        :return: String of first recognized result
        :rtype: str
    """
    params = f"topic=general&folderId={folder_id}&lang={language}"
    url = urllib.request.Request(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        data=audio_data,  # type: ignore
    )
    url.add_header("Authorization", "Bearer %s" % iam_token.strip())

    response_data = urllib.request.urlopen(url).read().decode("UTF-8")
    decoded_data = json.loads(response_data)

    if decoded_data.get("error_code") is None:
        return decoded_data.get("result")
    return None
