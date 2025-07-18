import os

bind = "0.0.0.0:4000"
worker_class = "sync"
# Single worker for shared memory state
workers = 1
# Multiple threads per worker for concurrency
threads = int(os.environ["GUNICORN_THREADS"])
loglevel = "debug"
capture_output = True
accesslog = "/var/log/gunicorn/access_log"
acceslogformat = "%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog = "/var/log/gunicorn/error_log"
