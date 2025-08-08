import os

bind = "0.0.0.0:8080"
worker_class = "eventlet"
# Single worker for shared memory state
workers = 1
# Multiple threads per worker for concurrency
threads = int(os.environ.get("GUNICORN_THREADS", 4))
loglevel = "info"
capture_output = True
accesslog = "-"
errorlog = "-"

# JSON access log format
access_log_format = '{"timestamp": "%(t)s", "remote_addr": "%(h)s", "method": "%(m)s", "url": "%(U)s%(q)s", "protocol": "%(H)s", "status": %(s)s, "response_length": %(b)s, "referer": "%(f)s", "user_agent": "%(a)s", "response_time": %(D)s}'  # noqa: E501
