"""Tests for pure cryptographic primitive functions."""
import pytest

from crypto_engine.primitives import (
    decrypt_aes_gcm,
    derive_key_hkdf,
    encrypt_aes_gcm,
    generate_dh_keypair,
    generate_dh_params,
    perform_key_exchange,
    sign_hmac,
    verify_hmac,
)


# ---------------------------------------------------------------------------
# DH parameter generation
# ---------------------------------------------------------------------------


def test_dh_params_uses_rfc3526_group14():
    params = generate_dh_params()
    pn = params.parameter_numbers()
    assert pn.g == 2
    assert pn.p.bit_length() == 2048


def test_dh_params_is_deterministic():
    """Same well-known group should come back every time."""
    p1 = generate_dh_params().parameter_numbers().p
    p2 = generate_dh_params().parameter_numbers().p
    assert p1 == p2


# ---------------------------------------------------------------------------
# DH key-pair generation
# ---------------------------------------------------------------------------


def test_generate_keypair_returns_valid_keys():
    params = generate_dh_params()
    private_key, public_key = generate_dh_keypair(params)
    p = params.parameter_numbers().p
    assert 1 < private_key.private_numbers().x < p
    assert 1 < public_key.public_numbers().y < p


def test_keypair_is_unique_each_call():
    params = generate_dh_params()
    _, pub1 = generate_dh_keypair(params)
    _, pub2 = generate_dh_keypair(params)
    assert pub1.public_numbers().y != pub2.public_numbers().y


# ---------------------------------------------------------------------------
# DH key exchange
# ---------------------------------------------------------------------------


def test_shared_secret_agreement():
    """Alice and Bob must derive the same shared secret."""
    params = generate_dh_params()
    alice_priv, alice_pub = generate_dh_keypair(params)
    bob_priv, bob_pub = generate_dh_keypair(params)

    alice_secret = perform_key_exchange(alice_priv, bob_pub)
    bob_secret = perform_key_exchange(bob_priv, alice_pub)

    assert alice_secret == bob_secret


def test_shared_secret_is_nonempty():
    params = generate_dh_params()
    alice_priv, _ = generate_dh_keypair(params)
    _, bob_pub = generate_dh_keypair(params)
    secret = perform_key_exchange(alice_priv, bob_pub)
    assert len(secret) > 0


def test_different_keypairs_produce_different_secrets():
    params = generate_dh_params()
    alice_priv, _ = generate_dh_keypair(params)
    _, bob_pub1 = generate_dh_keypair(params)
    _, bob_pub2 = generate_dh_keypair(params)
    s1 = perform_key_exchange(alice_priv, bob_pub1)
    s2 = perform_key_exchange(alice_priv, bob_pub2)
    assert s1 != s2


# ---------------------------------------------------------------------------
# HKDF key derivation
# ---------------------------------------------------------------------------


def test_derive_key_produces_correct_length():
    key = derive_key_hkdf(b"\x42" * 32, salt=b"\x00" * 16, info=b"test", length=32)
    assert len(key) == 32


def test_derive_key_different_lengths():
    secret = b"\x42" * 32
    salt = b"\x00" * 16
    key16 = derive_key_hkdf(secret, salt=salt, info=b"k", length=16)
    key32 = derive_key_hkdf(secret, salt=salt, info=b"k", length=32)
    assert len(key16) == 16
    assert len(key32) == 32
    # HKDF is a streaming PRF: the 16-byte output is a prefix of the 32-byte
    # output when inputs are identical. Use distinct info labels to get
    # independent keys (tested in test_derive_key_different_info_labels_*).
    assert key16 == key32[:16]


def test_derive_key_is_deterministic():
    secret = b"\x42" * 32
    salt = b"\x01" * 16
    k1 = derive_key_hkdf(secret, salt=salt, info=b"test")
    k2 = derive_key_hkdf(secret, salt=salt, info=b"test")
    assert k1 == k2


def test_derive_key_different_info_labels_produce_independent_keys():
    """Encryption and MAC keys must be independent even from the same secret."""
    secret = b"\x42" * 32
    salt = b"\x00" * 16
    enc_key = derive_key_hkdf(secret, salt=salt, info=b"handshake encryption key")
    mac_key = derive_key_hkdf(secret, salt=salt, info=b"handshake mac key")
    assert enc_key != mac_key


def test_derive_key_different_salts_produce_different_keys():
    secret = b"\x42" * 32
    k1 = derive_key_hkdf(secret, salt=b"\x00" * 16, info=b"k")
    k2 = derive_key_hkdf(secret, salt=b"\xFF" * 16, info=b"k")
    assert k1 != k2


# ---------------------------------------------------------------------------
# AES-GCM encryption / decryption
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_roundtrip():
    key = b"\xab" * 32
    plaintext = b"Hello, World!"
    nonce, ct = encrypt_aes_gcm(key, plaintext)
    assert decrypt_aes_gcm(key, nonce, ct) == plaintext


def test_encrypt_produces_unique_nonces():
    key = b"\xab" * 32
    nonce1, _ = encrypt_aes_gcm(key, b"same")
    nonce2, _ = encrypt_aes_gcm(key, b"same")
    assert nonce1 != nonce2  # Random nonce → almost certainly different


def test_nonce_is_12_bytes():
    key = b"\xab" * 32
    nonce, _ = encrypt_aes_gcm(key, b"data")
    assert len(nonce) == 12


def test_ciphertext_is_longer_than_plaintext():
    """Ciphertext should include plaintext + 16-byte GCM tag."""
    key = b"\xab" * 32
    plaintext = b"Hello"
    _, ct = encrypt_aes_gcm(key, plaintext)
    assert len(ct) == len(plaintext) + 16


def test_decrypt_wrong_key_raises():
    from cryptography.exceptions import InvalidTag

    key = b"\xab" * 32
    wrong_key = b"\xcd" * 32
    nonce, ct = encrypt_aes_gcm(key, b"Secret")
    with pytest.raises(InvalidTag):
        decrypt_aes_gcm(wrong_key, nonce, ct)


def test_decrypt_tampered_ciphertext_raises():
    from cryptography.exceptions import InvalidTag

    key = b"\xab" * 32
    nonce, ct = encrypt_aes_gcm(key, b"Secret message")
    tampered = bytes([ct[0] ^ 0xFF]) + ct[1:]
    with pytest.raises(InvalidTag):
        decrypt_aes_gcm(key, nonce, tampered)


def test_decrypt_wrong_nonce_raises():
    from cryptography.exceptions import InvalidTag
    import os

    key = b"\xab" * 32
    nonce, ct = encrypt_aes_gcm(key, b"Secret")
    wrong_nonce = os.urandom(12)
    with pytest.raises(InvalidTag):
        decrypt_aes_gcm(key, wrong_nonce, ct)


def test_encrypt_with_aad_roundtrip():
    key = b"\xab" * 32
    plaintext = b"Secret"
    aad = b"session=abc123"
    nonce, ct = encrypt_aes_gcm(key, plaintext, aad=aad)
    assert decrypt_aes_gcm(key, nonce, ct, aad=aad) == plaintext


def test_decrypt_wrong_aad_raises():
    from cryptography.exceptions import InvalidTag

    key = b"\xab" * 32
    nonce, ct = encrypt_aes_gcm(key, b"Secret", aad=b"real-aad")
    with pytest.raises(InvalidTag):
        decrypt_aes_gcm(key, nonce, ct, aad=b"fake-aad")


# ---------------------------------------------------------------------------
# HMAC sign / verify
# ---------------------------------------------------------------------------


def test_hmac_signature_is_32_bytes():
    sig = sign_hmac(b"\xaa" * 32, b"data")
    assert len(sig) == 32


def test_hmac_verify_valid_signature():
    key = b"\xaa" * 32
    data = b"important data"
    sig = sign_hmac(key, data)
    assert verify_hmac(key, data, sig) is True


def test_hmac_verify_tampered_data():
    key = b"\xaa" * 32
    sig = sign_hmac(key, b"original data")
    assert verify_hmac(key, b"tampered data!", sig) is False


def test_hmac_verify_wrong_key():
    key = b"\xaa" * 32
    wrong_key = b"\xbb" * 32
    sig = sign_hmac(key, b"data")
    assert verify_hmac(wrong_key, b"data", sig) is False


def test_hmac_verify_truncated_signature():
    key = b"\xaa" * 32
    data = b"data"
    sig = sign_hmac(key, data)
    assert verify_hmac(key, data, sig[:16]) is False


def test_hmac_is_deterministic():
    key = b"\xaa" * 32
    data = b"same data"
    assert sign_hmac(key, data) == sign_hmac(key, data)
