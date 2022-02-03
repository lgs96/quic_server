#
# demo application for http3_server.py
#

import datetime
import os
from urllib.parse import urlencode
import PIL.Image as Image
import io
import time
import numpy as np
from datetime import datetime
import subprocess
import shlex

import httpbin
from asgiref.wsgi import WsgiToAsgi
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response, JSONResponse, RedirectResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocketDisconnect

#import inference

ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.environ.get("STATIC_ROOT", os.path.join(ROOT, "htdocs"))
STATIC_URL = "/"
LOGS_PATH = os.path.join(STATIC_ROOT, "logs")
QVIS_URL = "https://qvis.quictools.info/"

templates = Jinja2Templates(directory=os.path.join(ROOT, "templates"))

prev_remote_time = 0
current_remote_time = 0
prve_local_time = 0
current_local_time = 0
rtt = 0
min_rtt = 9999

time_shift = 0

async def homepage(request):
    """
    Simple homepage.
    """
    await request.send_push_promise("/style.css")
    
    print('Goodsol: ')
    return templates.TemplateResponse("index.html", {"request": request})


async def echo(request):
    """
    HTTP echo endpoint.
    """
    global time_shift

    content = await request.body()
    media_type = request.headers.get("content-type")
    #print('Content bytes: ', len(content)/1024 'KB')
    #image = Image.open(io.BytesIO(content))
    print('Time shift: ', time_shift)
    content_upload_time = current_milli_time()
    #print('Content upload time: ', content_upload_time, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    #prediction = inference.run_inference(content)
    inference_finished_time = current_milli_time()
    #print('Inference finished time: ', inference_finished_time, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    print('Inference time: ', inference_finished_time - content_upload_time)
    response = JSONResponse({'downlink_start':inference_finished_time, 'inference_start': content_upload_time})

    print(response)

    return response

def current_milli_time():
    return round(time.time() * 1000)

async def ntp_start(request):
    """
    HTTP ntp application.
    """
    android_time = await request.json()

    global prev_remote_time
    global current_remote_time
    global rtt
    global min_rtt
    global prev_local_time
    global current_local_time
    global time_shift

    print('NTP log: ',android_time)

    prev_remote_time = current_remote_time
    current_remote_time = android_time['time']
    rtt = android_time['rtt'] 
    prev_local_time = current_local_time
    current_local_time = current_milli_time()
    time_shift = prev_local_time - (prev_remote_time + rtt/2)

    print('Time shift: ', time_shift)                                                                                                                    
    print('Prev remote: ', datetime.fromtimestamp(prev_remote_time/1000), 'Prev local: ', datetime.fromtimestamp(prev_local_time/1000))
    print('Current: ', datetime.fromtimestamp(current_local_time/1000))

    if np.abs(time_shift) > 100:
        min_rtt = 9999

    if rtt > 0 and rtt < min_rtt:
        min_rtt = rtt
        current_local_time = current_local_time - time_shift +20                                                        
        _linux_set_time(current_local_time/1000)

    return Response('Hi', media_type='text/plain')

def _linux_set_time(time_tuple):
    time_string = datetime.fromtimestamp(time_tuple).isoformat()

    sudoPassword = 'glaakstp'
    cmd = 'date -s %s' %(time_string)
    #print('echo %s|sudo -S %s' % (sudoPassword, cmd))
    p = os.system('echo %s|sudo -S %s' % (sudoPassword, cmd))
    #p = os.system('sudo -S %s' % (cmd))
    #subprocess.call(shlex.split("timedatectl set-ntp false"))  # May be necessary
    #subprocess.call(shlex.split("sudo date -s '%s'" % time_string))
    #subprocess.call(shlex.split("sudo hwclock -w"))
    print('Time fixed')
    
async def file_upload(request):
    global min_rtt
    global time_shift
    
    min_rtt = 9999

    content = await request.body()
    media_type = request.headers.get("content-type")
    #print('Content bytes: ', len(content)/1024 'KB')
    #image = Image.open(io.BytesIO(content))
    print('Time shift: ', time_shift)
    
    content_upload_time = current_milli_time()
    response = JSONResponse({'upload_finished': content_upload_time})

    return response
   
async def dummy_upload(request):
    global min_rtt
    global time_shift
    
    min_rtt = 9999

    #content = await request.body()
    #media_type = request.headers.get("content-type")
    #print('Content bytes: ', len(content)/1024 'KB')
    #image = Image.open(io.BytesIO(content))
    #print('Time shift: ', time_shift)
    
    #content_upload_time = current_milli_time()
    #response = JSONResponse({'dummy_finished': content_upload_time})

    #return response

    
async def dummy_upload(request):
    global min_rtt
    global time_shift
    
    #min_rtt = 9999

    #content = await request.body()
    #media_type = request.headers.get("content-type")
    #print('Content bytes: ', len(content)/1024 'KB')
    #image = Image.open(io.BytesIO(content))
    #print('Time shift: ', time_shift)
    
    #content_upload_time = current_milli_time()
    #response = JSONResponse({'upload_finished': content_upload_time})

    #return response
    
starlette = Starlette(
    routes=[
        Route("/echo", echo, methods=["POST"]),
        Route("/ntp_start", ntp_start, methods=["POST"]),
        Route("/file_upload", file_upload, methods=["POST"]),
        Route("/dummy_upload", dummy_upload, methods=["POST"]),
    ] 
)


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    await starlette(scope, receive, send)
