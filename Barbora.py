from requests.auth import HTTPBasicAuth
from requests.sessions import Session
from requests.cookies import RequestsCookieJar
import json
import time
import datetime
import inspect


class Barbora:

    def __init__(self, username: str, password: str, msteams_webhook: str = None):
        self._username = username
        self._password = password
        self._msteams_webhook = msteams_webhook
        self.api_base = 'https://barbora.lt/api/eshop/v1'
        self.locations = []

        # Initialize Cookie Jar
        self.cookie_jar = RequestsCookieJar()
        self.cookie_jar.set("region", "barbora.lt")

        # Create session
        self.session = Session()
        self.session.auth = HTTPBasicAuth('apikey', 'SecretKey')
        self.session.cookies = self.cookie_jar

    def _debug_status_code(self, response):
        print(f"{'.'*80}{response.status_code} - {response.reason} - {inspect.stack()[1][3]}")

    def _get_cookie(self) -> str:
        endpoint = f"{self.api_base}/user/login"
        payload = dict(email=self._username, password=self._password, rememberMe='true')
        response = self.session.post(url=endpoint, data=payload)
        self._debug_status_code(response)
        return response.cookies['.BRBAUTH']

    def _get_locations(self) -> None:
        response = self.session.get(url=f"{self.api_base}/user/address")
        self._debug_status_code(response)
        self.locations = response.json()['address']

    def _set_location(self, location_id: str) -> None:
        endpoint = f"{self.api_base}/cart/changeDeliveryAddress"
        payload = dict(deliveryAddressId=location_id, isWebRequest='true', forceToChangeAddressOnFirstTry='false')
        response = self.session.put(url=endpoint, data=payload)
        self._debug_status_code(response)

    def _get_time_table(self) -> list:
        endpoint = f"{self.api_base}/cart/deliveries"
        response = self.session.get(url=endpoint)
        self._debug_status_code(response)
        response_in_json = json.loads(response.text)
        timetable = response_in_json['deliveries'][0]['params']['matrix']
        return timetable

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
        self._debug_status_code(response)
        
        print("**************************************************")
        print(f"Sending MS Teams message: {response.status_code}")
        print("**************************************************")

    def run_once(self):
        self._get_cookie()
        self._get_locations()

        free_slots = list()
        for location in self.locations:
            self._set_location(location_id=location['id'])
            timetable = self._get_time_table()

            for day in timetable:
                for hour in day['hours']:
                    if hour['available']:
                        print(f"{hour['deliveryTime']} - Go go go! - {location['address']}")
                        free_slots.append(dict(name=str(hour['deliveryTime']), value=location['address']))

        if free_slots and self._msteams_webhook:
            self._send_message_to_msteams(facts=free_slots)

    def run_loop(self, delay_in_seconds=300):
        while True:
            print("==================================================")
            print(f"Starting job - {datetime.datetime.now()}")
            print("==================================================")

            try:
                self.run_once()
            except Exception as e:
                print(e)
            finally:
                time.sleep(delay_in_seconds)

