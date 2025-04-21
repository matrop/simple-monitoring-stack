import logging
import requests

from settings import ALLOY_URL, ALLOY_HEADERS

class AlloyHandler(logging.Handler):
    def __init__(self, labels=None):
        super().__init__()
        self.url = ALLOY_URL
        self.labels = labels or {"app": "api"}
        self.headers = ALLOY_HEADERS
        
    def emit(self, record):
        try:
            log_entry = {
                "streams": [{
                    "stream": self.labels,
                    "values": [[
                        str(int(record.created * 1e9)),  # Nanosecond timestamp
                        self.format(record)
                    ]]
                }]
            }
            requests.post(self.url, json=log_entry, headers=self.headers)
        except Exception:
            self.handleError(record)

