import time
import logging
from collections import OrderedDict
from functools import wraps
from twilio.request_validator import RequestValidator
from flask import Flask, request, abort
from pathlib import Path
from flask_restplus import Resource, Api  # noqa
from twilio.twiml.messaging_response import MessagingResponse

from shortage.filesystem import default_storage
from shortage.networking.pushover import PushOverClient


class Application(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.config.from_object("shortage.config")

    @property
    def pushover(self):
        token = self.config.get('PUSHOVER_API_TOKEN')
        user_key = self.config.get('PUSHOVER_API_USER_KEY')
        return PushOverClient(token, user_key)


app = Application()


# api = Api(
#     app,
#     version='1.0',
#     title='Shortage',
#     description='SMS Inbox as a service',
# )
# sms = api.namespace('sms', description='Twilio Webhooks')

logger = logging.getLogger(__name__)


def serialized_flask_request():
    url = getattr(request, "url", None)
    method = getattr(request, "method", None)
    data = OrderedDict()

    if method:
        data["method"] = method

    if url:
        data["url"] = url

    data["data"] = {}
    data["headers"] = dict(request.headers)

    if request.data:
        data["data"] = request.data
    elif request.values:
        data["data"] = dict(request.values)
    elif request.form:
        data["data"] = dict(request.form)

    if request.args:
        data["args"] = request.args

    return data


class StorageAwareResource(Resource):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.storage = default_storage()

    def default_sms_handling(self):
        self.store_sms_request()
        return self.respond()

    def store_sms_request(self) -> Path:
        logger.debug(f"storing SMS request")
        timestamp = str(time.time())
        data = serialized_flask_request()
        return self.storage.add("sms", timestamp, data)

    def respond(self, **kw):
        resp = MessagingResponse()
        # resp.message("Ahoy! Thanks so much for your message.")
        return str(resp)


def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(app.config.get("TWILIO_AUTH_TOKEN"))

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get("X-TWILIO-SIGNATURE", ""),
        )

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid:
            return f(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function
