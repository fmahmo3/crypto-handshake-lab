"""Orchestrates the full DH + AES-GCM + HMAC handshake, step by step.

Each call to ``advance()`` executes one step and appends a rich dict to
``self.steps``.  The frontend can page through steps one at a time or call
``run_all()`` for the complete transcript in one shot.

Step map
--------
1  DH Parameter Generation
2  Alice Key Generation
3  Bob Key Generation
4  Public Key Exchange
5  Shared Secret Derivation
6  Key Derivation (HKDF)
7  Message Encryption (AES-GCM)
8  HMAC-SHA256 Signing
9  Verification & Decryption
"""
from __future__ import annotations

import os
from typing import Any

from cryptography.exceptions import InvalidTag

from .parties import Party
from .primitives import (
    derive_key_hkdf,
    decrypt_aes_gcm,
    encrypt_aes_gcm,
    generate_dh_params,
    sign_hmac,
    verify_hmac,
)

DEFAULT_MESSAGE = "Hello, Bob! This is Alice's secret message."
TOTAL_STEPS = 9


class HandshakeComplete(Exception):
    """Raised when ``advance()`` is called on an already-finished handshake."""


def _hex(b: bytes) -> str:
    return "0x" + b.hex()


class Handshake:
    """Step-by-step DH key exchange, AES-GCM encryption, and HMAC verification.

    Usage::

        h = Handshake()
        while not h.is_complete():
            step = h.advance()
            print(step["name"], step["values"])

    Or all at once::

        steps = Handshake().run_all()

    Tamper mode::

        h = Handshake()
        h.enable_tamper()   # flip bits in ciphertext before step 9
        steps = h.run_all() # final step shows verification failure
    """

    TOTAL_STEPS: int = TOTAL_STEPS

    def __init__(self, plaintext: str = DEFAULT_MESSAGE) -> None:
        self.plaintext = plaintext
        self.tamper_mode: bool = False
        self.steps: list[dict[str, Any]] = []
        self.current_step: int = 0

        # Internal state populated as steps execute
        self._params = None
        self._alice: Party = Party(name="Alice")
        self._bob: Party = Party(name="Bob")
        self._salt: bytes | None = None
        self._encryption_key: bytes | None = None
        self._mac_key: bytes | None = None
        self._nonce: bytes | None = None
        self._ciphertext_with_tag: bytes | None = None
        self._hmac_sig: bytes | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enable_tamper(self) -> None:
        """Enable tamper mode.

        When step 9 runs, the first byte of the ciphertext is XOR-flipped
        before HMAC verification, causing the integrity check to fail and
        decryption to be aborted.
        """
        self.tamper_mode = True

    def is_complete(self) -> bool:
        """Return True after all nine steps have been executed."""
        return self.current_step >= self.TOTAL_STEPS

    def advance(self) -> dict[str, Any]:
        """Execute the next step and return its recorded data dict.

        Raises ``HandshakeComplete`` if all steps are already done.
        """
        if self.is_complete():
            raise HandshakeComplete("All steps already complete.")
        self.current_step += 1
        step_data = self._execute_step(self.current_step)
        self.steps.append(step_data)
        return step_data

    def get_step(self, step_number: int) -> dict[str, Any]:
        """Return a previously executed step by 1-based *step_number*.

        Raises ``IndexError`` if the step has not been executed yet.
        """
        if step_number < 1 or step_number > len(self.steps):
            raise IndexError(
                f"Step {step_number} has not been executed yet "
                f"(current_step={self.current_step})."
            )
        return self.steps[step_number - 1]

    def run_all(self) -> list[dict[str, Any]]:
        """Execute all remaining steps and return the full step list."""
        while not self.is_complete():
            self.advance()
        return self.steps

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    def _execute_step(self, step: int) -> dict[str, Any]:
        dispatch = {
            1: self._step1_dh_params,
            2: self._step2_alice_keygen,
            3: self._step3_bob_keygen,
            4: self._step4_key_exchange,
            5: self._step5_shared_secret,
            6: self._step6_key_derivation,
            7: self._step7_encrypt,
            8: self._step8_hmac_sign,
            9: self._step9_verify_decrypt,
        }
        return dispatch[step]()

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    def _step1_dh_params(self) -> dict[str, Any]:
        self._params = generate_dh_params()
        pn = self._params.parameter_numbers()
        return {
            "step": 1,
            "name": "DH Parameter Generation",
            "description": (
                "Establish the public Diffie-Hellman parameters: a large prime p and "
                "generator g. These are shared openly and form the mathematical basis "
                "of the key exchange. We use RFC 3526 Group 14 — a 2048-bit MODP group "
                "providing approximately 112 bits of equivalent security strength."
            ),
            "party": "shared",
            "values": {
                "p": hex(pn.p),
                "p_bits": pn.p.bit_length(),
                "g": hex(pn.g),
                "group": "RFC 3526 Group 14 (2048-bit MODP)",
            },
        }

    def _step2_alice_keygen(self) -> dict[str, Any]:
        self._alice.generate_keys(self._params)
        return {
            "step": 2,
            "name": "Alice Generates Key Pair",
            "description": (
                "Alice picks a random private exponent a and computes her public key "
                "A = g^a mod p. The private key a is never transmitted. "
                "A is published to Bob over the (untrusted) channel."
            ),
            "party": "alice",
            "values": {
                "alice_private_key": hex(self._alice.private_key_int),
                "alice_public_key": hex(self._alice.public_key_int),
                "formula": "A = g^a mod p",
            },
        }

    def _step3_bob_keygen(self) -> dict[str, Any]:
        self._bob.generate_keys(self._params)
        return {
            "step": 3,
            "name": "Bob Generates Key Pair",
            "description": (
                "Bob independently picks a random private exponent b and computes his "
                "public key B = g^b mod p. The private key b is never transmitted. "
                "B is published to Alice over the (untrusted) channel."
            ),
            "party": "bob",
            "values": {
                "bob_private_key": hex(self._bob.private_key_int),
                "bob_public_key": hex(self._bob.public_key_int),
                "formula": "B = g^b mod p",
            },
        }

    def _step4_key_exchange(self) -> dict[str, Any]:
        return {
            "step": 4,
            "name": "Public Key Exchange",
            "description": (
                "Alice sends A to Bob; Bob sends B to Alice — both over the insecure "
                "channel. A passive eavesdropper can observe A and B in the clear. "
                "However, computing g^(ab) mod p from just A, B, p, and g requires "
                "solving the discrete logarithm problem, which is computationally "
                "infeasible for a 2048-bit group."
            ),
            "party": "shared",
            "values": {
                "alice_public_key_sent": hex(self._alice.public_key_int),
                "bob_public_key_sent": hex(self._bob.public_key_int),
                "note": (
                    "Both keys are visible on the wire. "
                    "The shared secret is never transmitted."
                ),
            },
        }

    def _step5_shared_secret(self) -> dict[str, Any]:
        self._alice.compute_shared_secret(self._bob.public_key)
        self._bob.compute_shared_secret(self._alice.public_key)

        alice_secret_hex = _hex(self._alice.shared_secret)
        bob_secret_hex = _hex(self._bob.shared_secret)
        secrets_match = self._alice.shared_secret == self._bob.shared_secret

        return {
            "step": 5,
            "name": "Shared Secret Derivation",
            "description": (
                "Alice computes S = B^a mod p; Bob computes S = A^b mod p. "
                "Both arrive at the same value S = g^(ab) mod p — the shared secret — "
                "without ever transmitting it. This equality is the core insight of "
                "Diffie-Hellman."
            ),
            "party": "shared",
            "values": {
                "alice_computed_secret": alice_secret_hex,
                "bob_computed_secret": bob_secret_hex,
                "secrets_match": secrets_match,
                "formula": "S = B^a mod p  =  A^b mod p  =  g^(ab) mod p",
            },
        }

    def _step6_key_derivation(self) -> dict[str, Any]:
        self._salt = os.urandom(16)
        self._encryption_key = derive_key_hkdf(
            self._alice.shared_secret,
            salt=self._salt,
            info=b"handshake encryption key",
            length=32,
        )
        self._mac_key = derive_key_hkdf(
            self._alice.shared_secret,
            salt=self._salt,
            info=b"handshake mac key",
            length=32,
        )
        return {
            "step": 6,
            "name": "Key Derivation (HKDF)",
            "description": (
                "The raw DH output has mathematical structure that makes it unsuitable "
                "for direct use as an encryption key. HKDF-SHA256 extracts entropy from "
                "the shared secret and expands it into two independent 256-bit keys: "
                "one for AES-256-GCM encryption and one for HMAC-SHA256 signing. "
                "Different 'info' labels guarantee the two keys are cryptographically "
                "independent even though they share the same source secret."
            ),
            "party": "shared",
            "values": {
                "shared_secret": _hex(self._alice.shared_secret),
                "salt": _hex(self._salt),
                "encryption_key": _hex(self._encryption_key),
                "mac_key": _hex(self._mac_key),
                "encryption_info_label": "handshake encryption key",
                "mac_info_label": "handshake mac key",
                "algorithm": "HKDF-SHA256",
                "key_length_bits": 256,
            },
        }

    def _step7_encrypt(self) -> dict[str, Any]:
        plaintext_bytes = self.plaintext.encode()
        self._nonce, self._ciphertext_with_tag = encrypt_aes_gcm(
            self._encryption_key,
            plaintext_bytes,
        )
        ciphertext = self._ciphertext_with_tag[:-16]
        tag = self._ciphertext_with_tag[-16:]
        return {
            "step": 7,
            "name": "Message Encryption (AES-GCM)",
            "description": (
                "Alice encrypts her plaintext message using AES-256-GCM with a randomly "
                "generated 96-bit nonce. AES-GCM is an authenticated encryption scheme: "
                "it produces both the ciphertext and a 128-bit authentication tag. "
                "The tag will detect any modification to the ciphertext during transit."
            ),
            "party": "alice",
            "values": {
                "plaintext": self.plaintext,
                "nonce": _hex(self._nonce),
                "ciphertext": _hex(ciphertext),
                "auth_tag": _hex(tag),
                "algorithm": "AES-256-GCM",
                "nonce_bits": 96,
                "tag_bits": 128,
            },
        }

    def _step8_hmac_sign(self) -> dict[str, Any]:
        ciphertext = self._ciphertext_with_tag[:-16]
        self._hmac_sig = sign_hmac(self._mac_key, ciphertext)
        return {
            "step": 8,
            "name": "HMAC-SHA256 Signing",
            "description": (
                "Alice computes HMAC-SHA256 over the ciphertext using the derived MAC key. "
                "This binds the message to the shared secret: only someone who completed "
                "the same key exchange can produce or verify this signature. "
                "Bob will verify the HMAC before attempting decryption (MAC-then-Encrypt)."
            ),
            "party": "alice",
            "values": {
                "ciphertext": _hex(ciphertext),
                "mac_key_preview": _hex(self._mac_key[:8]) + "...",
                "hmac_signature": _hex(self._hmac_sig),
                "algorithm": "HMAC-SHA256",
                "signature_bits": 256,
            },
        }

    def _step9_verify_decrypt(self) -> dict[str, Any]:
        ciphertext = self._ciphertext_with_tag[:-16]
        tag = self._ciphertext_with_tag[-16:]

        tampered = self.tamper_mode
        if tampered:
            # Flip the first byte of the ciphertext — simulates an in-transit
            # bit-flip attack. The HMAC was computed over the original bytes,
            # so the signature will no longer match.
            tampered_ct = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]
            verify_target = tampered_ct
            decrypt_blob = tampered_ct + tag
            tampered_ciphertext_hex = _hex(tampered_ct)
        else:
            verify_target = ciphertext
            decrypt_blob = self._ciphertext_with_tag
            tampered_ciphertext_hex = None

        hmac_valid = verify_hmac(self._mac_key, verify_target, self._hmac_sig)

        decrypted_message: str | None = None
        error: str | None = None

        if hmac_valid:
            try:
                plaintext_bytes = decrypt_aes_gcm(
                    self._encryption_key,
                    self._nonce,
                    decrypt_blob,
                )
                decrypted_message = plaintext_bytes.decode()
            except InvalidTag:
                error = "AES-GCM authentication tag invalid — decryption failed."
        else:
            error = "HMAC verification failed — message integrity compromised."

        return {
            "step": 9,
            "name": "Verification & Decryption",
            "description": (
                "Bob first verifies the HMAC signature to confirm the message has not "
                "been tampered with. Only if verification passes does he attempt AES-GCM "
                "decryption. In tamper mode, the first byte of the ciphertext was flipped "
                "before verification, so the HMAC check fails and decryption is aborted "
                "— demonstrating how authenticated encryption detects in-transit attacks."
            ),
            "party": "bob",
            "tampered": tampered,
            "values": {
                "tamper_mode": tampered,
                "tampered_ciphertext": tampered_ciphertext_hex,
                "original_hmac_signature": _hex(self._hmac_sig),
                "hmac_verified": hmac_valid,
                "decrypted_message": decrypted_message,
                "error": error,
                "handshake_success": hmac_valid and error is None,
            },
        }
