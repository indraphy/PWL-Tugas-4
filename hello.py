from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.response import Response

@view_config(route_name='hello', renderer='views/loginjj.jinja2')
def hello(request):
    return {}


if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('hello', '/')
        config.include('pyramid_jinja2')
        config.add_static_view(name='static', path='static')
        # config.add_view(hello_world, route_name='hello')
        config.scan()
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()