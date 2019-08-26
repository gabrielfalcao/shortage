import click
import coloredlogs
import logging
from twilio.rest import Client
from shortage.web.backend.api import app

logger = logging.getLogger(__name__)


@click.group()
def shortage():
    coloredlogs.install(level="DEBUG", logger=logging.getLogger())


@shortage.command(name="web")
@click.option("--host", type=str, default="127.0.0.1")
@click.option("--port", type=int, default=3000)
@click.option("--debug", is_flag=True, default=False)
def run(debug=False, port=3000, host="0.0.0.0"):
    """runs the web app"""
    app.run(debug=debug, port=port, host=host)


@shortage.command(name="sms")
@click.option("--receiver", type=str, default="+18482259204")
@click.option("--to", type=str, default="+18482259319")
@click.argument("body")
def sms(receiver, to, body):
    """runs the web app"""
    coloredlogs.install(level="DEBUG", logger=logging.getLogger())

    account_sid = app.config.get("TWILIO_ACCOUNT_SID")
    auth_token = app.config.get("TWILIO_AUTH_TOKEN")

    if not account_sid:
        logger.error("TWILIO_ACCOUNT_SID is not configured")
        raise SystemExit(1)

    if not auth_token:
        logger.error("TWILIO_AUTH_TOKEN is not configured")
        raise SystemExit(1)

    client = Client(account_sid, auth_token)
    print(client.messages.create(body=body, from_=receiver, to=to))
