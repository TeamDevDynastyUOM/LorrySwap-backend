import bcrypt

def hash_password(password):
    """
    Hashes a password using bcrypt.
    
    Parameters:
    - password (str): The password to hash.
    
    Returns:
    - hash (str): The hashed password (including the salt).
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Generate a salt and hash the password. The hash includes the salt.
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    
    return hashed.decode('utf-8')

# password + salt (hgfhaf25646551) -> hash() -> #21312sweqwe234523476281527ewtyqtuw -> to databse
# when loggin -> enterd password + salt get by stored hash -> hash() -> compare with stored hash


def verify_password(password, stored_hash):
    """
    Verifies a password against a hashed password using bcrypt.
    
    Parameters:
    - password (str): The password to verify.
    - stored_hash (str): The full bcrypt hash string from storage.
    
    Returns:
    - bool: True if the password matches the hash, False otherwise.
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    
    # Bcrypt verifies the password against the entire hash string (which includes the salt).
    return bcrypt.checkpw(password, stored_hash)
