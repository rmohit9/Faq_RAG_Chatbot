import os
from base64 import urlsafe_b64encode, urlsafe_b64decode
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from cryptography.fernet import Fernet, InvalidToken

# --- Key Management (Example: Environment Variable) ---
# In a real application, use a KMS or more robust secret management.
# Ensure this key is generated once and kept secret.
# Example: Fernet.generate_key().decode()
ENCRYPTION_KEY = os.environ.get("DJANGO_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        "DJANGO_ENCRYPTION_KEY environment variable not set. "
        "Please generate a Fernet key and set it."
    )

cipher_suite = Fernet(ENCRYPTION_KEY)

class EncryptedTextField(models.TextField):
    """
    A custom Django model field that encrypts text data before saving to the database
    and decrypts it when retrieved. Uses Fernet symmetric encryption.
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        # Debug: Track field usage
        import inspect
        caller_frame = inspect.currentframe().f_back.f_back
        model_class = caller_frame.f_locals.get('self', None).__class__.__name__ if caller_frame.f_locals.get('self') else 'Unknown'
        print(f"EncryptedTextField.from_db_value called for {model_class} with value: {value[:50]}...")
        try:
            # Decrypt directly (stored value is Fernet's URL-safe base64 string)
            print(f"EncryptedTextField.from_db_value: Attempting to decrypt value: {value[:50]}...")
            decrypted_bytes = cipher_suite.decrypt(urlsafe_b64decode(value))
            decrypted_value = decrypted_bytes.decode('utf-8')
            print(f"EncryptedTextField.from_db_value: Decrypted successfully: {decrypted_value[:50]}...")
            return decrypted_value
        except InvalidToken:
            # Handle cases where decryption fails (e.g., wrong key, corrupted data)
            # You might want to log this or return a placeholder
            print(f"Warning: Could not decrypt data for {model_class}: {value}")
            return "[ENCRYPTION_ERROR]"
        except Exception as e:
            print(f"Error during decryption for {model_class}: {e}")
            return "[DECRYPTION_FAILED]"

    def to_python(self, value):
        # This is called when loading from fixtures or forms
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        # Debug: Track field usage
        import inspect
        caller_frame = inspect.currentframe().f_back.f_back
        model_class = caller_frame.f_locals.get('self', None).__class__.__name__ if caller_frame.f_locals.get('self') else 'Unknown'
        print(f"EncryptedTextField.get_prep_value called for {model_class} with value: {value[:50]}...")
        try:
            # Ensure value is bytes before encryption
            if isinstance(value, str):
                value = value.encode('utf-8')
            # Encrypt (Fernet returns URL-safe base64 bytes; decode to string for storage)
            encrypted_bytes = cipher_suite.encrypt(value)
            encrypted_value = encrypted_bytes.decode('utf-8')
            print(f"EncryptedTextField.get_prep_value returning encrypted value: {encrypted_value[:50]}...")
            return encrypted_value
        except Exception as e:
            print(f"Error during encryption in get_prep_value: {str(e)}")
            return value

    def get_db_prep_save(self, value, connection):
        # Debug: Track field usage
        import inspect
        caller_frame = inspect.currentframe().f_back.f_back
        model_class = caller_frame.f_locals.get('self', None).__class__.__name__ if caller_frame.f_locals.get('self') else 'Unknown'
        print(f"EncryptedTextField.get_db_prep_save called for {model_class} with value: {value[:50]}...")
        prep_value = self.get_prep_value(value)
        print(f"EncryptedTextField.get_db_prep_save returning value: {prep_value[:50]}...")
        return prep_value

    def value_to_string(self, obj):
        # Used for serialization (e.g., Django's dumpdata)
        value = self.value_from_object(obj)
        return self.get_prep_value(value)
