import os
import threading

from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
DEFAULT_CHANNEL = os.environ["SLACK_CHANNEL"]


class SlackClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super(SlackClient, cls).__new__(cls)
                    instance.client = WebClient(token=SLACK_BOT_TOKEN)
                    cls._instance = instance
        return cls._instance

    def get_client(self) -> WebClient:
        return self.client


slack_instance = SlackClient()
