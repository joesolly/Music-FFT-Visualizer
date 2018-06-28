from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
import selectors
from jinja2 import Template

from visualization import Visualization

if hasattr(selectors, 'PollSelector'):
    _ServerSelector = selectors.PollSelector
else:
    _ServerSelector = selectors.SelectSelector


class Server(BaseHTTPRequestHandler):
    isLeaf = True

    def __init__(self, *args, **kwargs):
        with open('index.html', 'r') as f:
            self.index = Template(f.read())
        super(Server, self).__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", 'text/html; charset=utf-8')
        self.end_headers()
        template_args = {
            'visualization_method_choices': Visualization.VISUALIZATION_METHOD_CHOICES,
        }
        self.wfile.write(bytes(self.index.render(**template_args), 'utf-8'))

    def do_POST(self):
        visualization_method = str(self.rfile.peek(), 'utf-8').split('=')[-1]
        if visualization_method in Visualization.VISUALIZATION_METHODS:
            self.server.callback(visualization_method)

        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", self.path)
        self.end_headers()


class CustomHTTPServer(HTTPServer):

    def callback(self, *args, **kwargs):
        self.custom_callback(*args, **kwargs)

    def serve_once(self, callback):
        self.custom_callback = callback
        with _ServerSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            ready = selector.select(.0001)
            if ready:
                self._handle_request_noblock()
