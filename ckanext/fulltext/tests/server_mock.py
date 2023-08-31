import os
import socket
import requests
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer


NAME = "localhost"
PORT = 5009


DATA_PATH = DATA_PATH = os.getcwd()+"/ckanext/fulltext/tests/data/"
SERVER_URL = f'http://{NAME}:{PORT}/test'
data = b"text"


class RequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def log_error(self, format, *args):
        pass

    # GET
    def do_GET(self):
        self.send_response(requests.codes.ok)
        self.send_header('Content-Type', 'application/rdf+xml; charset=utf-8')
        self.end_headers()
        self.wfile.write(data)

    # POST
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.send_response(200)
        self.wfile.write("".encode("utf-8"))  # send back to client

    def do_HEAD(self):
        self.send_response(requests.codes.ok)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()


class ServerMock(threading.Thread):
    def __init__(self, port):
        # init thread
        self._stop_event = threading.Event()
        self.thread_name = self.__class__
        self.server = HTTPServer((NAME, port), RequestHandler)
        threading.Thread.__init__(self, name=self.thread_name, target=self.run)
        self.setDaemon(True)

    def set_text(self, text):
        global data
        if isinstance(text, bytes):
            data = text
        else:
            data = text.encode("utf-8")

    def set_file(self, path):
        global data
        with open(path, 'rb') as f:
            data = f.read()

    def run(self):
        try:
            self.server.serve_forever()
        except socket.error:
            print('shutdown')

    def close(self):
        self.server.shutdown()