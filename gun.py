# -*- coding: utf-8 -*-
import os
import logging
import logging.handlers
from logging.handlers import WatchedFileHandler
import os

import gevent.monkey
gevent.monkey.patch_all()

import multiprocessing

backlog = 512  
debug = True
loglevel = 'debug'
bind = '0.0.0.0:443'
bind ='127.0.0.1:8888'
pidfile = 'log/gunicorn.pid'
logfile = 'log/debug.log'
#certfile = './2_lyl.qianqiulin.com.crt'
#keyfile = '3_lyl.qianqiulin.com.key'

chdir = '/home/lyl/pythonService'

#daemon = True 

#启动的进程数
workers = multiprocessing.cpu_count() * 2 + 1 
worker_class = 'gunicorn.workers.ggevent.GeventWorker'
threads = 4

x_forwarded_for_header = 'X-FORWARDED-FOR'


