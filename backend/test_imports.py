from passlib.context import CryptContext
from jose import JWTError, jwt

print("Imports successful!")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print("CryptContext created successfully!")
result = pwd_context.hash("test")
print(f"Hash works: {result[:20]}...")
