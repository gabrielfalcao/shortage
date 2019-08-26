import requests
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

# import http.client, urllib
# conn = http.client.HTTPSConnection("api.pushover.net:443")
# conn.request("POST", "/1/messages.json",
#   urllib.parse.urlencode({
#     "token": "APP_TOKEN",
#     "user": "USER_KEY",
#     "message": "hello world",
#   }), { "Content-type": "application/x-www-form-urlencoded" })
# conn.getresponse()


class PushOverClient(object):
    def __init__(self, token: str, user_key: str):
        self.token = token
        self.user_key = user_key
        self.base_url = f"https://api.pushover.net/1"

        self.http = requests.Session()

    def url(self, path):
        return urljoin(self.base_url, path)

    def send_notification(self, body: str, title: str):
        data = {
            "token": self.token,
            "user": self.user_key,
            "message": body,
            "title": title,
        }
        url = self.url("message.json")
        try:
            return self.http.post(url, data=data)
        except Exception as e:
            logger.exception(f"failed to POST to {url!r}: {e}")
