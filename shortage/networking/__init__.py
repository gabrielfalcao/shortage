# -*- coding: utf-8 -*-
import json
import logging
import requests

from urllib.parse import urljoin


logger = logging.getLogger(__name__)


class PushOverClient(object):
    def __init__(self, token: str, user_key: str):
        self.token = token
        self.user_key = user_key
        self.base_url = f"https://api.pushover.net/"

        self.http = requests.Session()
        self.http.headers.update({
            'Content-Type': 'application/json'
        })

    def url(self, path):
        return urljoin(self.base_url, path)

    def send_notification(self, body: str, title: str):
        data = json.dumps({
            "token": self.token,
            "user": self.user_key,
            "message": body,
            "title": title,
        }, indent=2)
        url = self.url("/1/messages.json")
        logger.info(f"Calling pushover API\nPOST {url!r}\n{data}")
        try:
            response = self.http.post(url, data=data)
        except Exception as e:
            logger.exception(f"failed to POST to {url!r}: {e}")
            return

        logger.info(f"POST {url!r}: {response}")
        logger.info(f"response: {response.text}")
