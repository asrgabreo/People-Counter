#11-13coming led=3
#13-11going  led=5
from ubidots import ApiClient
import io
import picamera
import logging
import socketserver
import time
import requests
from picamera import PiCamera
from time import sleep
from threading import Condition
from http import server
import RPi.GPIO as GPIO 

##Messaging service fas2sms initializations
try:
 url = "https://www.fast2sms.com/dev/bulk"
 payload = "sender_id=FSTSMS&message=CHECKED IN&language=english&route=p&number$
 headers = {
 'authorization': "eaiAvBJyQz2K51wdjhZFlGIWtmpErnsMUP3bS6o8ORNgXc4L0YGxW9H8eDyZ$
 'Content-Type': "application/x-www-form-urlencoded",
 'Cache-Control': "no-cache",
 }
except:
 print "connection problem"
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN) 
GPIO.setup(13, GPIO.IN)        #Read input from PIR motion sensor
GPIO.setup(3, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.output(3,0)
time.sleep(0.1)
GPIO.output(5,0)
time.sleep(0.1)
pe=0
pl=0
x=0
t=0
i=0
PAGE="""\
<html>
<head>
<title>Raspberry Pi - Surveillance Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Surveillance Camera</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    #camera.rotation = 90
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()

while True:
  x=t
  t=pe-pl                       #total persons
  if(x!=t):
   print ("persons inside",t)
  elif (GPIO.input(11) == 0) and (GPIO.input(13) == 0):
       GPIO.output(5, False)
       GPIO.output(3, True)
       pe+=1
       print("entries",pe)
       time.sleep(1.5)
       response = requests.request("POST", url, data=payload, headers=headers)
  elif (GPIO.input(13) == 0) and (GPIO.input(11) == 0):
       GPIO.output(5, 1)
       GPIO.output(3, 0)
       time.sleep(1.5)
       pl+= 1
       print ("exits",pl)
       time.sleep(1.5)  

