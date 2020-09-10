import json

import requests


class SymblAI:
    def __init__(self, message='Test'):
        self.appId = '544d5a39794f35756f3146715672323355716e4930787576574f367875757366'
        self.appSecret = '57626a73517443717a49654a536c4d415841494e5639666748594c354f396f4b4130726637366c61547a364f5930336138445f61633439537871523963714c2d'
        self.token = self._getToken()

        self._sendText(message)

    def _getToken(self):
        data = {
            "type": "application",
            "appId": self.appId,
            "appSecret": self.appSecret
        }
        res = requests.post('https://api.symbl.ai/oauth2/token:generate', json=data)
        return json.loads(res.text)['accessToken']

    def _sendText(self, message):
        headers = {
            "Content-Type": 'application/json',
            "x-api-key": self.token
        }
        data = {
            "messages": [{"payload": {"content": message}}],
            "intents": [{
                "intent": "interested"
            },
                {
                    "intent": "do_not_call"
                },
                {
                    "intent": "not_interested"
                }]
        }
        res = requests.post('https://api.symbl.ai/v1/process/text', headers=headers, json=data)
        self.conversationId = json.loads(res.text)['conversationId']
        self.jobId = json.loads(res.text)['jobId']

    def getTopics(self):
        headers = {
            "x-api-key": self.token
        }
        res = requests.get(f'https://api.symbl.ai/v1/conversations/{self.conversationId}/topics', headers=headers)
        topics = []
        for item in json.loads(res.text)['topics']:
            topics.append(item['text'])
        print('Topics: ', topics)
        return topics

    def getIntents(self):
        headers = {
            "x-api-key": self.token
        }
        res = requests.get(f'https://api.symbl.ai/v1/conversations/{self.conversationId}/intents', headers=headers)
        try:
            resData = json.loads(res.text)['intents'][0]
        except IndexError:
            err = {'error': 'Not detected intents'}
            print(err)
            return err

        intent = resData['intent']
        alternativesList = resData['alternatives']
        print('Intent: ', intent, '  Score: ', resData['score'])
        print('Alternative: ', alternativesList)
        return json.loads(res.text)


if __name__ == '__main__':
    s = SymblAI(message="""Please don't call me, I am not interested""")
    s.getTopics()
    s.getIntents()
