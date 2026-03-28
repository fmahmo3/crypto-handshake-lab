"""Tests for the Handshake orchestrator."""
import pytest

from crypto_engine.handshake import DEFAULT_MESSAGE, Handshake, HandshakeComplete


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def test_initial_state():
    h = Handshake()
    assert h.current_step == 0
    assert h.steps == []
    assert h.tamper_mode is False
    assert not h.is_complete()


def test_advance_increments_step():
    h = Handshake()
    h.advance()
    assert h.current_step == 1
    assert len(h.steps) == 1


def test_run_all_executes_all_steps():
    h = Handshake()
    steps = h.run_all()
    assert len(steps) == Handshake.TOTAL_STEPS
    assert h.current_step == Handshake.TOTAL_STEPS
    assert h.is_complete()


def test_advance_beyond_complete_raises():
    h = Handshake()
    h.run_all()
    with pytest.raises(HandshakeComplete):
        h.advance()


def test_get_step_returns_correct_step():
    h = Handshake()
    h.advance()
    h.advance()
    step2 = h.get_step(2)
    assert step2["step"] == 2
    assert step2["name"] == "Alice Generates Key Pair"


def test_get_step_unexecuted_raises():
    h = Handshake()
    with pytest.raises(IndexError):
        h.get_step(1)


def test_get_step_out_of_range_raises():
    h = Handshake()
    h.run_all()
    with pytest.raises(IndexError):
        h.get_step(10)


# ---------------------------------------------------------------------------
# Step structure / schema
# ---------------------------------------------------------------------------


def test_each_step_has_required_keys():
    h = Handshake()
    for _ in range(h.TOTAL_STEPS):
        step = h.advance()
        assert "step" in step, f"Missing 'step' key: {step}"
        assert "name" in step, f"Missing 'name' key: {step}"
        assert "description" in step, f"Missing 'description' key: {step}"
        assert "party" in step, f"Missing 'party' key: {step}"
        assert "values" in step, f"Missing 'values' key: {step}"


def test_step_numbers_are_sequential():
    h = Handshake()
    for expected in range(1, h.TOTAL_STEPS + 1):
        step = h.advance()
        assert step["step"] == expected


def test_party_field_values():
    """Each step should declare which party performs the action."""
    expected_parties = {
        1: "shared",
        2: "alice",
        3: "bob",
        4: "shared",
        5: "shared",
        6: "shared",
        7: "alice",
        8: "alice",
        9: "bob",
    }
    h = Handshake()
    for n in range(1, h.TOTAL_STEPS + 1):
        step = h.advance()
        assert step["party"] == expected_parties[n], (
            f"Step {n}: expected party={expected_parties[n]!r}, got {step['party']!r}"
        )


# ---------------------------------------------------------------------------
# Step-specific value checks
# ---------------------------------------------------------------------------


def test_step1_contains_p_g_and_group_name():
    h = Handshake()
    step = h.advance()
    v = step["values"]
    assert "p" in v and v["p"].startswith("0x")
    assert "g" in v and v["g"] == "0x2"
    assert v["p_bits"] == 2048
    assert "RFC 3526" in v["group"]


def test_step2_alice_has_private_and_public_key():
    h = Handshake()
    h.advance()  # step 1
    step = h.advance()  # step 2
    v = step["values"]
    assert "alice_private_key" in v and v["alice_private_key"].startswith("0x")
    assert "alice_public_key" in v and v["alice_public_key"].startswith("0x")


def test_step3_bob_has_private_and_public_key():
    h = Handshake()
    for _ in range(3):
        step = h.advance()
    v = step["values"]
    assert "bob_private_key" in v and v["bob_private_key"].startswith("0x")
    assert "bob_public_key" in v and v["bob_public_key"].startswith("0x")


def test_step5_shared_secrets_match():
    h = Handshake()
    for _ in range(5):
        h.advance()
    step5 = h.get_step(5)
    v = step5["values"]
    assert v["secrets_match"] is True
    assert v["alice_computed_secret"] == v["bob_computed_secret"]


def test_step6_keys_are_32_bytes_hex():
    h = Handshake()
    for _ in range(6):
        h.advance()
    v = h.get_step(6)["values"]
    # 32 bytes → 64 hex chars + "0x" prefix = 66 chars
    assert len(v["encryption_key"]) == 66
    assert len(v["mac_key"]) == 66
    assert v["encryption_key"] != v["mac_key"]


def test_step7_ciphertext_differs_from_plaintext():
    h = Handshake()
    for _ in range(7):
        h.advance()
    v = h.get_step(7)["values"]
    assert v["plaintext"] == DEFAULT_MESSAGE
    assert v["ciphertext"] != v["plaintext"]
    assert v["nonce"].startswith("0x")
    assert v["auth_tag"].startswith("0x")


def test_step8_hmac_is_32_bytes_hex():
    h = Handshake()
    for _ in range(8):
        h.advance()
    v = h.get_step(8)["values"]
    assert len(v["hmac_signature"]) == 66  # 0x + 64 hex chars


# ---------------------------------------------------------------------------
# Normal handshake success
# ---------------------------------------------------------------------------


def test_normal_handshake_succeeds():
    h = Handshake()
    steps = h.run_all()
    final = steps[-1]
    assert final["values"]["handshake_success"] is True
    assert final["values"]["decrypted_message"] == DEFAULT_MESSAGE
    assert final["values"]["error"] is None
    assert final["values"]["hmac_verified"] is True
    assert final["tampered"] is False


def test_custom_plaintext_survives_roundtrip():
    msg = "Top secret: the launch code is 0000."
    h = Handshake(plaintext=msg)
    steps = h.run_all()
    assert steps[-1]["values"]["decrypted_message"] == msg


# ---------------------------------------------------------------------------
# Tamper mode
# ---------------------------------------------------------------------------


def test_enable_tamper_sets_flag():
    h = Handshake()
    h.enable_tamper()
    assert h.tamper_mode is True


def test_tamper_mode_causes_hmac_failure():
    h = Handshake()
    h.enable_tamper()
    h.run_all()
    final = h.get_step(9)
    assert final["values"]["hmac_verified"] is False
    assert final["values"]["handshake_success"] is False


def test_tamper_mode_prevents_decryption():
    h = Handshake()
    h.enable_tamper()
    h.run_all()
    final = h.get_step(9)
    assert final["values"]["decrypted_message"] is None
    assert final["values"]["error"] is not None


def test_tamper_mode_sets_tampered_flag():
    h = Handshake()
    h.enable_tamper()
    h.run_all()
    assert h.get_step(9)["tampered"] is True


def test_tamper_mode_shows_modified_ciphertext():
    h = Handshake()
    h.enable_tamper()
    h.run_all()
    v9 = h.get_step(9)["values"]
    assert v9["tampered_ciphertext"] is not None
    # Original ciphertext from step 7 should differ from tampered ciphertext
    v7 = h.get_step(7)["values"]
    assert v9["tampered_ciphertext"] != v7["ciphertext"]


def test_normal_mode_has_no_tampered_ciphertext():
    h = Handshake()
    h.run_all()
    v9 = h.get_step(9)["values"]
    assert v9["tampered_ciphertext"] is None


# ---------------------------------------------------------------------------
# Partial advance then run_all
# ---------------------------------------------------------------------------


def test_partial_advance_then_run_all():
    h = Handshake()
    h.advance()  # step 1
    h.advance()  # step 2
    h.run_all()  # steps 3–9
    assert h.current_step == h.TOTAL_STEPS
    assert len(h.steps) == h.TOTAL_STEPS


def test_enable_tamper_between_steps():
    """Tamper mode can be enabled after some steps have already run."""
    h = Handshake()
    for _ in range(8):
        h.advance()
    h.enable_tamper()
    h.advance()  # step 9
    assert h.get_step(9)["values"]["handshake_success"] is False
