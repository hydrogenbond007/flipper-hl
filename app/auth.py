import jwt
from datetime import datetime, timedelta

class Auth:
    def __init__(self, secret_key):
        self.secret_key = secret_key
    
    def generate_auth_token(self, wallet_address):
        payload = {
            'wallet_address': wallet_address,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_auth_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['wallet_address']
        except:
            return None
