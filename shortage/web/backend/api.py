import time
try:
    import pync
except:  # noqa
    pync = None

import logging
from datetime import datetime
from pathlib import Path
from flask import Response
from twilio.twiml.messaging_response import MessagingResponse

from shortage.filesystem import default_storage, slugify  # noqa
from .base import app, serialized_flask_request, validate_twilio_request


logger = logging.getLogger(__name__)


class MessageData(object):
    __required_keys__ = (
        "Body",
        "From",
        "To",
    )

    __optional_keys__ = (
        "ApiVersion",
        "MessageSid",
        "SmsStatus",
        "SmsSid",
        "MessagingServiceSid",
        "AccountSid",
        "MessageStatus",
    )

    def __init__(self, request_data: dict):
        self.data = dict(request_data)
        self.data['requested_at'] = datetime.utcnow().isoformat()
        for key in self.__required_keys__:
            value = self.data.get(key)
            if not value:
                logger.error(
                    f'missing required key {key} from response: {self.data}',
                )
            setattr(self, key, value)

        for key in self.__optional_keys__:
            value = self.data.get(key)
            setattr(self, key, value)


def default_sms_handling():
    store_sms_request()
    resp = MessagingResponse()
    # resp.message("Ahoy! Thanks so much for your message.")
    return Response(str(resp), headers={'Content-Type': 'application/xml'})


def show_notification(body, title):
    if not pync:
        logger.warning('{title} - {body}')
        return

    try:
        pync.notify(body, title=title)
    except Exception as err:
        logger.debug(
            f'failed to show notification "{body}" (title={title}) - {err}'
        )


def store_sms_request() -> Path:
    storage = default_storage()
    logger.debug(f'storing SMS request')
    timestamp = str(time.time())
    raw = serialized_flask_request()
    message = MessageData(raw['data'])

    show_notification(message.Body, title=f'{message.To} SMS')
    key = message.To or 'webhook'
    return storage.add(key, timestamp, raw)


@validate_twilio_request
@app.route('/sms/in', methods=['GET', 'POST'])
def handle_sms_in():
    logger.warning('/sms/in')
    return default_sms_handling()


@app.route('/sms/status', methods=['GET', 'POST'])
def handle_status():
    logger.warning('/sms/status')
    return default_sms_handling()


@app.route('/sms/fallback', methods=['GET', 'POST'])
def handle_sms_fallback():
    logger.warning('/sms/fallback')
    return default_sms_handling()


@app.route('/', methods=['GET', 'POST'])
def index():
    logger.warning('/')
    return {
        'endpoints': [
            '/sms/in',
            '/sms/status',
            '/sms/fallback',
        ]
    }
