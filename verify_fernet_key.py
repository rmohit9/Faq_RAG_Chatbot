import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), 'chatbot', '.env'))

# Load the same encryption key used by EncryptedTextField
ENCRYPTION_KEY = os.environ.get("DJANGO_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise Exception("DJANGO_ENCRYPTION_KEY environment variable not set")

# Validate Fernet key format
try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
    print("✅ Fernet key is valid")
except Exception as e:
    raise Exception(f"❌ Invalid Fernet key: {e}")

# Generate test token and check prefix
test_value = "Test Fernet token generation"
encrypted_bytes = cipher_suite.encrypt(test_value.encode('utf-8'))
encrypted_string = encrypted_bytes.decode('utf-8')

print(f"Test encrypted token: {encrypted_string[:50]}...")
print(f"Token starts with gAAAAAB: {encrypted_string.startswith('gAAAAAB')}")
print(f"Token length (expected ~88): {len(encrypted_string)}")

# Verify decryption works
decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
decrypted_string = decrypted_bytes.decode('utf-8')
print(f"✅ Decryption successful: {decrypted_string == test_value}")