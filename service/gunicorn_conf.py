bind = "0.0.0.0:4000"
worker_class = "eventlet"
loglevel = "debug"
capture_output = True
accesslog = "/var/log/gunicorn/access_log"
acceslogformat = "%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog = "/var/log/gunicorn/error_log"
