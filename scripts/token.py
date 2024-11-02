import jwt
import datetime
from jwt import decode, ExpiredSignatureError


def generate_token(user_id, roles, secret_key):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    payload = {
        'exp': expiration_time,
        'iat': datetime.datetime.utcnow(),
        'sub': user_id,
        'roles': roles
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


