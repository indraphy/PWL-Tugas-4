from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.authorization import ACLAuthorizationPolicy
import pymysql
import jwt
import datetime

# Koneksi ke database MySQL

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='movies',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
    
def authenticate_user(login, password):
    # Note the below will not work, its just an example of returning a user
    # object back to the JWT creation.
    # login_query = session.query(User).\
    #     filter(User.login == login).\
    #     filter(User.password == password).first()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(sql, (login, password))
        login_query = cursor.fetchone()

    if login_query:
        user_dict = {
            'userid': login_query['id'],
            'user_name': login_query['username'],
        }
        # An example of login_query.roles would be a list
        # print(login_query.roles)
        # ['admin', 'reports']
        return user_dict
    else:
        # If we end up here, no logins have been found
        return None

@view_config(route_name='login', renderer='json')
def login(request):
    '''Create a login view
    '''
    login = request.POST['login']
    password = request.POST['password']
    print(login, password)
    with connection.cursor() as cursor:
        sql = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(sql, (login, password))
        user = cursor.fetchone()
    if user:
        payload = {
            'sub': user['id'],
            'name': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
        }
        encode = jwt.encode(payload, 'secret', algorithm='HS256')
        set_cookie = request.response.set_cookie('token', encode)
        return {
            'result': 'ok',
            'token': encode
        }
    else:
        return {
            'result': 'error',
            'token': None
        }

@view_config(route_name='hello', renderer="json")
def hello(request):
    authorization_header = request.cookies.get('token')
    if authorization_header:
        # token = authorization_header.split('Bearer ')[1]
        decoded_user = jwt.decode(authorization_header, 'secret', algorithms=['HS256'])
        # print(decoded_user)
        
        # Retrieve the refresh token from the database based on the user's ID
        with connection.cursor() as cursor:
            sql = "SELECT refresh_token FROM tokens WHERE user_id=%s"
            cursor.execute(sql, (decoded_user['sub'],))
            result = cursor.fetchone()

        if result:
            # If refresh token is valid, return the response
            return {'greet': 'Welcome'}
        else:
            request.response.status = 401  # Unauthorized
            return {'greet': 'Unauthorized', 'name': '', 'error': 'Refresh token not found'}
    return {
        'greet': 'Unauthorized', 'name': '', 'error': 'Token not found'
    }

if __name__ == "__main__":
    with Configurator() as config:
        config = Configurator(settings={'jwt.secret': 'secret'})
        config.add_route('login', '/login')
        config.add_route('hello', '/welcome')
        config.scan()
        config.set_authorization_policy(ACLAuthorizationPolicy())
        config.add_static_view(name='static', path='static')
        config.include('pyramid_jwt')
        config.set_jwt_authentication_policy(config.get_settings()['jwt.secret'])
        
        app = config.make_wsgi_app()
    # Menjalankan aplikasi pada server lokal
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()