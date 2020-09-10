import os
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums

def recognize(storage_uri, creditionals_json='config/config-google.json', language_code="en-US", sample_rate_hertz=24000):

    if creditionals_json:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creditionals_json

    client = speech_v1p1beta1.SpeechClient()
    language_code = language_code
    sample_rate_hertz = sample_rate_hertz

    encoding = enums.RecognitionConfig.AudioEncoding.MP3
    config = {
        "language_code": language_code,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
        "enable_word_time_offsets": True,
    }
    audio = {"uri": storage_uri}

    print(' [x] Start recognize')
    operation = client.long_running_recognize(config, audio)
    response = operation.result()
    result_text = ''

    for result in response.results:
        alternative = result.alternatives[0]
        for word in alternative.words:
            result_text += word.word + ' '

    print(' [x] Text from recognize' + result_text)
    return result_text

if __name__ == '__main__':
    r = recognize(storage_uri='gs://suptitle-kvando.appspot.com/husen/2.mp3', creditionals_json='config-google.json', language_code='ru-RU')