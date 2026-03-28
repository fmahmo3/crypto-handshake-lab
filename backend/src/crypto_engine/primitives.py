"""Pure cryptographic functions for the handshake lab.

All functions are stateless — inputs in, outputs out. No side effects.
"""
from __future__ import annotations

import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.dh import (
    DHParameterNumbers,
    DHParameters,
    DHPrivateKey,
    DHPublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# ---------------------------------------------------------------------------
# RFC 3526 Group 14 — 2048-bit MODP Group
# https://www.rfc-editor.org/rfc/rfc3526#section-3
# Using a well-known group avoids slow on-the-fly parameter generation and
# lets the frontend label the group clearly for educational purposes.
# ---------------------------------------------------------------------------
_MODP_2048_P = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AACAA68FFFFFFFFFFFFFFFF",
    16,
)
_MODP_2048_G = 2


def generate_dh_params() -> DHParameters:
    """Return RFC 3526 Group 14 (2048-bit MODP) DH parameters.

    Using a pre-defined group avoids the ~10 second cost of generating
    a fresh 2048-bit safe prime at startup.
    """
    pn = DHParameterNumbers(p=_MODP_2048_P, g=_MODP_2048_G)
    return pn.parameters()


def generate_dh_keypair(parameters: DHParameters) -> tuple[DHPrivateKey, DHPublicKey]:
    """Generate a DH private/public key pair from the given parameters."""
    private_key = parameters.generate_private_key()
    return private_key, private_key.public_key()


def perform_key_exchange(
    private_key: DHPrivateKey,
    peer_public_key: DHPublicKey,
) -> bytes:
    """Compute the DH shared secret: own_private ^ peer_public mod p.

    Returns the shared secret as raw bytes (big-endian integer).
    """
    return private_key.exchange(peer_public_key)


def derive_key_hkdf(
    shared_secret: bytes,
    salt: bytes,
    info: bytes,
    length: int = 32,
) -> bytes:
    """Derive a fixed-length key from a shared secret using HKDF-SHA256.

    The ``info`` label distinguishes different keys derived from the same
    shared secret (e.g. ``b"encryption"`` vs ``b"authentication"``).
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(shared_secret)


def encrypt_aes_gcm(
    key: bytes,
    plaintext: bytes,
    aad: bytes | None = None,
) -> tuple[bytes, bytes]:
    """Encrypt *plaintext* with AES-256-GCM.

    Returns ``(nonce, ciphertext_with_tag)`` where the last 16 bytes of
    ``ciphertext_with_tag`` are the GCM authentication tag.

    A fresh 96-bit nonce is generated for every call — never reuse a nonce
    with the same key.
    """
    nonce = os.urandom(12)  # 96-bit nonce (NIST recommended for GCM)
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ciphertext_with_tag


def decrypt_aes_gcm(
    key: bytes,
    nonce: bytes,
    ciphertext_with_tag: bytes,
    aad: bytes | None = None,
) -> bytes:
    """Decrypt AES-256-GCM ciphertext and verify the authentication tag.

    Raises ``cryptography.exceptions.InvalidTag`` if the tag is invalid —
    either the key is wrong, the nonce is wrong, or the ciphertext was
    tampered with.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext_with_tag, aad)


def sign_hmac(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256 over *data* with *key*. Returns a 32-byte digest."""
    h = HMAC(key, hashes.SHA256())
    h.update(data)
    return h.finalize()


def verify_hmac(key: bytes, data: bytes, signature: bytes) -> bool:
    """Verify an HMAC-SHA256 signature in constant time.

    Returns ``True`` if *signature* is valid for *data* under *key*,
    ``False`` otherwise. Uses a constant-time comparison to prevent
    timing side-channel attacks.
    """
    h = HMAC(key, hashes.SHA256())
    h.update(data)
    try:
        h.verify(signature)
        return True
    except InvalidSignature:
        return False
