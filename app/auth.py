from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

class Auth:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"

    def create_auth_token(self, wallet_address: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT token for a wallet address"""
        to_encode = {"sub": wallet_address}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # Default 7 day expiration
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_auth_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return the wallet address if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.JWTError:
            return None
