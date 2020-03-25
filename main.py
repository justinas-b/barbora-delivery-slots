import requests
from requests.auth import HTTPBasicAuth
import json
import time
import datetime
import os


class Barbora():

    def __init__(self, username: str, password: str, msteams_webhook: str):
        self.api_auth = HTTPBasicAuth('apikey', 'SecretKey')
        self._username = username
        self._password = password
        self._msteams_webhook = msteams_webhook
        self.api_base = 'https://barbora.lt/api/eshop/v1'
        self.cookies = dict(region='barbora.lt')
        self.locations = [
            {'name': 'PC Akropolis (Ozo g. 25)',        'id': '1f287574-a3c3-4adf-9d18-9c94b421669a'},
            {'name': 'Maxima baze (Savanoriu pr. 247)', 'id': '166a9cdd-cdad-4307-83c6-1a9fd5b8f4d1'},
            {'name': 'Statoil (Ukmerges g. 231)',       'id': '0101f26d-0281-db2f-bcd6-8b70de847ad2'},
            {'name': 'PC Ozas (Ozo g. 18)',             'id': '7f22a3c0-b977-4bba-b173-e28d7d3b06d0'},
        ]

    def _get_cookie(self) -> str:
        endpoint = f"{self.api_base}/user/login"
        payload = dict(email=self._username, password=self._password, rememberMe='true')
        response = requests.post(url=endpoint, data=payload, auth=self.api_auth, cookies=self.cookies)
        return response.cookies['.BRBAUTH']

    def _set_location(self, location_id: str) -> None:
        endpoint = f"{self.api_base}/cart/changeDeliveryAddress"
        payload = dict(deliveryAddressId=location_id, isWebRequest='true', forceToChangeAddressOnFirstTry='false')
        response = requests.put(url=endpoint, auth=self.api_auth, cookies=self.cookies, data=payload)

    def _get_time_table(self) -> list:
        endpoint = f"{self.api_base}/cart/deliveries"
        response = requests.get(url=endpoint, auth=self.api_auth, cookies=self.cookies)
        response_in_json = json.loads(response.text)
        timetable = response_in_json['deliveries'][0]['params']['matrix']
        return timetable

    def _process_data(self):
        self.cookies['.BRBAUTH'] = self._get_cookie()
        free_slots = list()

        for location in self.locations:
            self._set_location(location_id=location['id'])
            timetable = self._get_time_table()

            for day in timetable:
                for hour in day['hours']:
                    if hour['available']:
                        print(f"{hour['deliveryTime']} - Go go go! - {location['name']}")
                        free_slots.append(dict(name=str(hour['deliveryTime']), value=location['name']))
                    else:
                        # free_slots.append(dict(name=str(hour['deliveryTime']), value=location['name']))
                        print(f"{hour['deliveryTime']} - No no no! - {location['name']}")

        if free_slots:
            self._send_message_to_msteams(facts=free_slots)

    def _send_message_to_msteams(self, facts):
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": "Available slots for delivery @ Barbora",
            "sections": [
                {
                    "activityTitle": "Available slots for delivery @ Barbora",
                    "facts": facts,
                    "markdown": True
                }
            ],
        }

        response = requests.post(url=self._msteams_webhook, json=payload)
        print("**************************************************")
        print(f"Sending MS Teams message: {response.status_code}")
        print("**************************************************")

    def run_loop(self, delay_in_seconds=300):
        while True:
            print("==================================================")
            print(f"Starting job - {datetime.datetime.now()}")
            print("==================================================")

            try:
                self._process_data()
            except Exception as e:
                print(e)
            finally:
                time.sleep(delay_in_seconds)


barbora = Barbora(
    username=os.getenv("username"),
    password=os.getenv("password"),
    msteams_webhook=os.getenv("webhook")
)
barbora.run_loop()
