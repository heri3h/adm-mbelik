# Gunicorn production configuration file
import multiprocessing

bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5

accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"
