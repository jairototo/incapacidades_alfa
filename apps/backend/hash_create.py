from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "AdMin1234"

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): The plain text password to hash.
    
    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)  

print(hash_password(password))

print(pwd_context.verify(password, hash_password(password)))  # Should return True