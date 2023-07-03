import json
import requests


def push_notification(to, message):
    try:
        url = 'https://fcm.googleapis.com/fcm/send'
        headers = {'content-type': 'application/json', 'Authorization': 'key=AAAA_vecyqc:APA91bFV5LQsC3YQi0nJCs8RR2PUb8m4zJTIsVA5as5d1VUBm2GtWcar5IukxTvrHuietOmx9313c6Q557g7YP_EBakC6KWrhgck-HPTMk-nd72I4U-YFLYOtZkLX3oELeuI6TqmnlUq'
        }
        payload = {
            'to': to,
            'data': {
                'body': message
            }}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        print("notification sent")
    except:
        print("Except notification not sent")
        pass
