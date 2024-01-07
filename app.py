import mimetypes
import pathlib
import urllib.parse
import json
import socket
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

BASE_DIR = pathlib.Path()
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000

env = Environment(loader=FileSystemLoader('templates'))




def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()

class HTTPHandler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        #self.send_html('message.html')
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()



    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message.html":
                self.send_html('message.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status_code=200):    
        self.send_response(status_code)
        self.send_header("Context-Type", "text/html")
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    #def render_temlate(self, filename, status_code=200):
    #    self.send_response(status_code)
    #    self.send_header("Context-Type", "text/html")
    #    self.end_headers()
    #    with open('index.json', 'r', encoding='utf-8') as fd:
    #        r = json.load(fd)
    #    template = env.get_template(filename)
    #    print(template)
    #    html = template.render(blogs=r)
    #    self.wfile.write(html.encode())




    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Context-Type", mime_type)
        else:
            self.send_header("Context-Type", "text/plain")
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    adress = ('', 3000)
    http_server = server(adress, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


#####
def data_dict_json(body) -> dict:
    body = urllib.parse.unquote_plus(body.decode())
    payload = {str(datetime.now()):{key: value for key, value in [el.split('=') for el in body.split('&')]}}
    return payload


def save_data(data):
    with open(BASE_DIR.joinpath('data/data.json'), 'r', encoding='utf-8') as f:
        loaded_dict = json.load(f)
    data_dict = data_dict_json(data)
    loaded_dict.update(data_dict)
    with open(BASE_DIR.joinpath('data/data.json'), 'w', encoding='utf-8') as f:
        json.dump(loaded_dict, f, ensure_ascii=False)

#####

def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind((server))

    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()

    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()