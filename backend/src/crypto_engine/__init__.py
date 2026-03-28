"""crypto_engine — Diffie-Hellman, AES-GCM, and HMAC handshake library."""
from .handshake import DEFAULT_MESSAGE, Handshake, HandshakeComplete
from .parties import Party
from .primitives import (
    decrypt_aes_gcm,
    derive_key_hkdf,
    encrypt_aes_gcm,
    generate_dh_keypair,
    generate_dh_params,
    perform_key_exchange,
    sign_hmac,
    verify_hmac,
)

__all__ = [
    # Handshake orchestrator
    "Handshake",
    "HandshakeComplete",
    "DEFAULT_MESSAGE",
    # Party class
    "Party",
    # Primitives
    "generate_dh_params",
    "generate_dh_keypair",
    "perform_key_exchange",
    "derive_key_hkdf",
    "encrypt_aes_gcm",
    "decrypt_aes_gcm",
    "sign_hmac",
    "verify_hmac",
]
