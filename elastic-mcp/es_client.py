import os
import threading

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ELASTIC_URLS = os.environ["ELASTIC_URL"]

ES_HOSTS = [ELASTIC_URLS]

class ElasticsearchClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, hosts=None):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ElasticsearchClient, cls).__new__(cls)
                    cls._instance._init_client(hosts)
        return cls._instance

    def _init_client(self, hosts):
        self.client = Elasticsearch(
            hosts or ES_HOSTS,
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )

    def get_client(self):
        return self.client