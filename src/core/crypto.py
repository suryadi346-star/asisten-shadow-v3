
"""
Cryptography Module - AES-256-GCM Encryption
Zero-knowledge encryption for notes
"""

import os
import base64
from typing import Tuple, Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

import config


class CryptoManager:
    """
    Advanced cryptography manager dengan AES-256-GCM

    Features:
    - AES-256-GCM encryption (authenticated encryption)
    - PBKDF2 key derivation
    - Unique salt per user
    - Unique IV per note
    - Zero-knowledge architecture
    """

    @staticmethod
    def generate_salt() -> bytes:
        """Generate random salt"""
        return os.urandom(config.SALT_SIZE)

    @staticmethod
    def generate_iv() -> bytes:
        """Generate random initialization vector"""
        return os.urandom(config.IV_SIZE)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: User's password
            salt: Unique salt

        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=config.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def encrypt(plaintext: str, password: str, salt: bytes = None) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt text using AES-256-GCM

        Args:
            plaintext: Text to encrypt
            password: Encryption password
            salt: Optional salt (generates new if not provided)

        Returns:
            Tuple of (ciphertext, iv, salt)
        """
        try:
            # Generate salt if not provided
            if salt is None:
                salt = CryptoManager.generate_salt()

            # Derive key from password
            key = CryptoManager.derive_key(password, salt)

            # Generate IV
            iv = CryptoManager.generate_iv()

            # Encrypt with AES-256-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(
                iv,
                plaintext.encode('utf-8'),
                None  # No additional authenticated data
            )

            return ciphertext, iv, salt

        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    @staticmethod
    def decrypt(ciphertext: bytes, password: str, iv: bytes, salt: bytes) -> str:
        """
        Decrypt ciphertext using AES-256-GCM

        Args:
            ciphertext: Encrypted data
            password: Decryption password
            iv: Initialization vector used for encryption
            salt: Salt used for key derivation

        Returns:
            Decrypted plaintext
        """
        try:
            # Derive key from password
            key = CryptoManager.derive_key(password, salt)

            # Decrypt with AES-256-GCM
            aesgcm = AESGCM(key)
            plaintext_bytes = aesgcm.decrypt(iv, ciphertext, None)

            return plaintext_bytes.decode('utf-8')

        except Exception as e:
            raise DecryptionError(f"Decryption failed: {str(e)}")

    @staticmethod
    def encrypt_to_storage(plaintext: str, password: str, salt: bytes = None) -> str:
        """
        Encrypt and encode to storage format: base64(iv + ciphertext + salt)

        Args:
            plaintext: Text to encrypt
            password: Encryption password
            salt: Optional salt

        Returns:
            Base64 encoded string ready for storage
        """
        ciphertext, iv, salt = CryptoManager.encrypt(plaintext, password, salt)

        # Combine: iv + ciphertext
        combined = iv + ciphertext

        # Encode to base64
        encoded = base64.b64encode(combined).decode('utf-8')
        salt_encoded = base64.b64encode(salt).decode('utf-8')

        # Return format: "salt:encrypted_data"
        return f"{salt_encoded}:{encoded}"

    @staticmethod
    def decrypt_from_storage(storage_data: str, password: str) -> str:
        """
        Decrypt from storage format

        Args:
            storage_data: Base64 encoded string from storage
            password: Decryption password

        Returns:
            Decrypted plaintext
        """
        try:
            # Split salt and encrypted data
            salt_encoded, encrypted_encoded = storage_data.split(':', 1)

            # Decode from base64
            salt = base64.b64decode(salt_encoded.encode('utf-8'))
            combined = base64.b64decode(encrypted_encoded.encode('utf-8'))

            # Split IV and ciphertext
            iv = combined[:config.IV_SIZE]
            ciphertext = combined[config.IV_SIZE:]

            # Decrypt
            return CryptoManager.decrypt(ciphertext, password, iv, salt)

        except Exception as e:
            raise DecryptionError(f"Failed to decrypt from storage: {str(e)}")

    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
        """
        Hash password for storage (not for encryption!)

        Args:
            password: Password to hash
            salt: Optional salt

        Returns:
            Tuple of (hash, salt) as base64 strings
        """
        if salt is None:
            salt = CryptoManager.generate_salt()

        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=config.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        hash_bytes = kdf.derive(password.encode('utf-8'))

        # Encode to base64
        hash_b64 = base64.b64encode(hash_bytes).decode('utf-8')
        salt_b64 = base64.b64encode(salt).decode('utf-8')

        return hash_b64, salt_b64

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """
        Verify password against stored hash

        Args:
            password: Password to verify
            stored_hash: Stored hash (base64)
            salt: Salt used for hashing (base64)

        Returns:
            True if password matches
        """
        try:
            # Decode salt
            salt_bytes = base64.b64decode(salt.encode('utf-8'))

            # Hash the input password
            new_hash, _ = CryptoManager.hash_password(password, salt_bytes)

            # Compare
            return new_hash == stored_hash

        except Exception:
            return False

    @staticmethod
    def generate_random_key(length: int = 32) -> str:
        """
        Generate random key for various purposes

        Args:
            length: Key length in bytes

        Returns:
            Base64 encoded random key
        """
        random_bytes = os.urandom(length)
        return base64.b64encode(random_bytes).decode('utf-8')


class EncryptionError(Exception):
    """Raised when encryption fails"""
    pass


class DecryptionError(Exception):
    """Raised when decryption fails"""
    pass


# ==================== UTILITY FUNCTIONS ====================

def encrypt_note(content: str, master_password: str, user_salt: bytes) -> str:
    """
    Quick function to encrypt note content

    Args:
        content: Note content
        master_password: User's master password
        user_salt: User's salt for key derivation

    Returns:
        Encrypted string ready for storage
    """
    return CryptoManager.encrypt_to_storage(content, master_password, user_salt)


def decrypt_note(encrypted_content: str, master_password: str) -> str:
    """
    Quick function to decrypt note content

    Args:
        encrypted_content: Encrypted content from storage
        master_password: User's master password

    Returns:
        Decrypted content
    """
    return CryptoManager.decrypt_from_storage(encrypted_content, master_password)


def test_encryption():
    """Test encryption/decryption"""
    password = "test_password_123"
    plaintext = "This is a secret note! 🔒"

    # Encrypt
    encrypted = CryptoManager.encrypt_to_storage(plaintext, password)
    print(f"Encrypted: {encrypted[:50]}...")

    # Decrypt
    decrypted = CryptoManager.decrypt_from_storage(encrypted, password)
    print(f"Decrypted: {decrypted}")

    assert plaintext == decrypted, "Encryption/Decryption failed!"
    print("✓ Encryption test passed!")


if __name__ == "__main__":
    test_encryption()
