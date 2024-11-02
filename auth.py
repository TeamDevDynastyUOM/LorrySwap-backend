import jwt
import connexion
from flask import jsonify
from connexion.exceptions import OAuthProblem
import datetime
from jwt import decode, ExpiredSignatureError, InvalidTokenError

SECRET_KEY = 'jHF4r3$4Df34@#LorrySwaP#@LkL0&$fKJd'

def bearer_info_func(token, required_scopes=None):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {
            "active": True,
            "client_id": data.get("client_id"),
            "username": data.get("username"),
            "scope": data.get("scope", ""),
            "sub": data.get("sub"),
            "aud": data.get("aud"),
            "iss": data.get("iss"),
            "exp": data.get("exp"),
            "iat": data.get("iat"),
            "extension_field": data.get("extension_field", "")
        }
    except jwt.ExpiredSignatureError:
        raise OAuthProblem("Token has expired!")
    except jwt.InvalidTokenError:
        raise OAuthProblem("Token is invalid!")


def verify_token(token, secret_key=SECRET_KEY):
    try:
        payload = decode(token, secret_key, algorithms=['HS256'])
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        return None


def auth_token_required(roles_required=None):
    def decorator(function):
        def wrapper(*args, **kwargs):
            auth = connexion.request.headers.get('Authorization')
            if not auth:
                return jsonify({"message": "Unauthorized"}), 401

            try:
                token_type, token = auth.split()
                if token_type != 'Bearer':
                    return jsonify({"message": "Unauthorized"}), 401

                payload = verify_token(token, SECRET_KEY)
                if not payload:
                    return jsonify({"message": "Unauthorized"}), 401

                user_roles = payload.get('roles', [])
                if roles_required and not any(role in user_roles for role in roles_required):
                    return jsonify({"message": "Forbidden"}), 403

                kwargs['user'] = payload  # Pass the payload as 'user' to the endpoint function
                kwargs['token_info'] = payload  # Pass the payload as 'token_info' to the endpoint function

            except ValueError:
                return jsonify({"message": "Unauthorized"}), 401

            return function(*args, **kwargs)
        return wrapper
    return decorator