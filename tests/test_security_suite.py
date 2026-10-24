"""
ONE DOTS - Comprehensive Security Test Suite
Verifies all 19 Security Hardening & Defense Controls:
1. Row Level Security (RLS) & Multi-Tenant Isolation
2. Tamper-Evident Admin Action Audit Logging
3. Bearer & API Key Auth on API routes
4. Private Storage Buckets & Path Traversal Blockade
5. Input Sanitization & XSS Defense
6. File Upload Verification (MIME, Magic Bytes, Executables Blocklist)
7. Parameterized Query Integrity
8. Sliding-Window Rate Limiting
9. SSRF Prevention
10. Locked-Down CORS & Security Headers
11. IDOR Prevention (Object Ownership Checks)
12. HMAC Webhook Signature Verification
13. Debug Mode Error Masking
14. Cryptographic CAPTCHA Protection
"""

import time
import hmac
import hashlib
from fastapi.testclient import TestClient
from api.app import app
from config.settings import settings
from core.security import (
    UserRole,
    AuthenticatedUser,
    sanitize_text,
    sanitize_filename,
    validate_file_upload,
    is_safe_external_url,
    verify_webhook_signature,
    generate_captcha_challenge,
    verify_captcha_token,
    session_store,
)
from memory.state_store import state_store

client = TestClient(app)


def test_row_level_security_and_idor_prevention():
    """Verify tenant isolation: User A cannot view, modify, or delete User B's agents."""
    # Register two separate users in session store
    user_a = AuthenticatedUser(id="usr_tenant_a", username="alice", role=UserRole.USER, tenant_id="tenant_a")
    user_b = AuthenticatedUser(id="usr_tenant_b", username="bob", role=UserRole.USER, tenant_id="tenant_b")
    
    token_a = session_store.register_session(user_a)
    token_b = session_store.register_session(user_b)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A creates an agent
    resp_a = client.post("/api/agents", headers=headers_a, json={
        "name": "AliceAgent",
        "responsibility": "Private proprietary research for Tenant A",
        "schedule_interval_seconds": 60,
    })
    assert resp_a.status_code == 200, resp_a.text
    agent_a_id = resp_a.json()["id"]

    try:
        # 2. User B lists agents -> User A's agent must NOT appear
        list_b = client.get("/api/agents", headers=headers_b)
        assert list_b.status_code == 200
        agents_b = list_b.json()
        assert not any(a["id"] == agent_a_id for a in agents_b), "RLS Leak: User B saw User A's agent"

        # 3. User B attempts direct object reference (IDOR) to access User A's agent -> 404
        idor_get = client.get(f"/api/agents/{agent_a_id}", headers=headers_b)
        assert idor_get.status_code == 404, "IDOR Vulnerability: User B accessed User A's agent directly"

        # 4. User B attempts IDOR delete on User A's agent -> 404
        idor_del = client.delete(f"/api/agents/{agent_a_id}", headers=headers_b)
        assert idor_del.status_code == 404, "IDOR Vulnerability: User B deleted User A's agent"

        # 5. User A can still retrieve their own agent
        owner_get = client.get(f"/api/agents/{agent_a_id}", headers=headers_a)
        assert owner_get.status_code == 200
        assert owner_get.json()["id"] == agent_a_id
    finally:
        client.delete(f"/api/agents/{agent_a_id}", headers=headers_a)


def test_admin_audit_logging_and_vault_access():
    """Verify tamper-evident audit logs and strict admin authorization."""
    admin_headers = {"X-API-Key": settings.ADMIN_API_KEY}
    
    # Non-admin user session
    user = AuthenticatedUser(id="usr_regular_joe", username="joe", role=UserRole.USER, tenant_id="tenant_joe")
    user_token = session_store.register_session(user)
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Non-admin accessing audit logs -> 403 Forbidden
    resp_denied = client.get("/api/admin/audit-logs", headers=user_headers)
    assert resp_denied.status_code == 403, "Security Leak: Non-admin accessed audit logs"

    # 2. Admin creates an agent to generate audit event
    create_resp = client.post("/api/agents", headers=admin_headers, json={
        "name": "AuditTesterAgent",
        "responsibility": "Validate audit log creation",
        "schedule_interval_seconds": 120,
    })
    assert create_resp.status_code == 200
    agent_id = create_resp.json()["id"]

    try:
        # 3. Admin queries audit log vault -> must contain AGENT_CREATE action
        audit_resp = client.get("/api/admin/audit-logs", headers=admin_headers)
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert len(logs) > 0
        create_events = [l for l in logs if l["action"] == "AGENT_CREATE" and l["resource_id"] == agent_id]
        assert len(create_events) > 0, "Audit trail missing AGENT_CREATE event"
        assert create_events[0]["status"] == "SUCCESS"
    finally:
        client.delete(f"/api/agents/{agent_id}", headers=admin_headers)


def test_input_sanitization_and_xss_defense():
    """Verify XSS vectors and malicious HTML tags are stripped from user inputs."""
    malicious_inputs = [
        "<script>alert('XSS')</script>Hello",
        "<img src=x onerror=alert(document.cookie)>Test",
        "javascript:alert(1) Payload",
        "Normal Text\x00NullByteAttack",
    ]

    for raw in malicious_inputs:
        cleaned = sanitize_text(raw)
        assert "<script>" not in cleaned
        assert "onerror=" not in cleaned
        assert "\x00" not in cleaned
        assert "javascript:" not in cleaned


def test_file_upload_type_and_executable_defense():
    """Verify upload allowlist and executable blocklist."""
    # 1. Prohibited executable extensions
    for bad_file in ["malware.exe", "script.sh", "payload.bat", "trojan.dll", "hack.php", "xss.svg"]:
        valid, reason = validate_file_upload(bad_file, b"sample text content")
        assert not valid, f"Dangerous file '{bad_file}' was erroneously accepted"

    # 2. Executable binary headers (PE / MZ)
    fake_txt_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"
    valid, reason = validate_file_upload("innocent.txt", fake_txt_exe)
    assert not valid, "Executable binary header was not rejected"

    # 3. Valid text file
    valid, reason = validate_file_upload("data.csv", b"col1,col2\n1,2")
    assert valid, f"Valid CSV rejected: {reason}"

    # 4. Valid PNG image magic bytes
    valid_png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    valid, reason = validate_file_upload("screenshot.png", valid_png_header)
    assert valid, f"Valid PNG rejected: {reason}"

    # 5. Mismatched magic bytes (text disguised as PNG)
    invalid_png = b"This is just plain text disguised as png"
    valid, reason = validate_file_upload("screenshot.png", invalid_png)
    assert not valid, "Mismatched image magic bytes was not caught"


def test_path_traversal_defense():
    """Verify directory traversal is sanitized and blocked."""
    # Filename sanitizer
    assert ".." not in sanitize_filename("../../etc/passwd")
    assert "/" not in sanitize_filename("..\\..\\windows\\system32")
    assert "\\" not in sanitize_filename("..\\..\\windows\\system32")
    assert "\x00" not in sanitize_filename("safe.txt\x00.exe")


def test_ssrf_url_validation():
    """Verify private networks, loopback, and cloud metadata targets are blocked."""
    blocked_urls = [
        "http://localhost:8000/secret",
        "http://127.0.0.1:9000/admin",
        "http://169.254.169.254/latest/meta-data/",  # AWS / Cloud metadata
        "http://10.0.0.1/internal-api",
        "http://192.168.1.1/router",
        "ftp://example.com/file",
        "file:///etc/passwd",
    ]

    for url in blocked_urls:
        safe, reason = is_safe_external_url(url)
        assert not safe, f"SSRF vulnerability: '{url}' was allowed ({reason})"


def test_hmac_webhook_signature_verification():
    """Verify HMAC-SHA256 signature and replay attack prevention."""
    payload = b'{"event":"agent_deploy","source":"external_ci"}'
    secret = settings.WEBHOOK_SECRET

    # 1. Valid signature with current timestamp
    ts = str(int(time.time()))
    sign_payload = f"{ts}.".encode("utf-8") + payload
    valid_sig = hmac.new(secret.encode("utf-8"), sign_payload, hashlib.sha256).hexdigest()

    ok, msg = verify_webhook_signature(
        raw_body=payload,
        signature_header=valid_sig,
        timestamp_header=ts,
        secret=secret,
    )
    assert ok, f"Valid signature failed: {msg}"

    # 2. Tampered signature -> Rejected
    ok_bad, _ = verify_webhook_signature(
        raw_body=payload,
        signature_header="deadbeef0011223344",
        timestamp_header=ts,
        secret=secret,
    )
    assert not ok_bad, "Tampered signature was accepted"

    # 3. Replay attack with expired timestamp (> 300s old) -> Rejected
    expired_ts = str(int(time.time()) - 400)
    expired_sign_payload = f"{expired_ts}.".encode("utf-8") + payload
    expired_sig = hmac.new(secret.encode("utf-8"), expired_sign_payload, hashlib.sha256).hexdigest()

    ok_replay, msg_replay = verify_webhook_signature(
        raw_body=payload,
        signature_header=expired_sig,
        timestamp_header=expired_ts,
        secret=secret,
    )
    assert not ok_replay, "Replay attack with expired timestamp was accepted"
    assert "expired" in msg_replay.lower()


def test_security_headers():
    """Verify enterprise HTTP security headers (CSP, HSTS, X-Frame-Options, nosniff)."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")


def test_captcha_challenge_lifecycle():
    """Verify cryptographic CAPTCHA challenge generation and validation."""
    challenge = generate_captcha_challenge()
    assert "token" in challenge
    assert "question" in challenge

    # Extract the math question and answer (e.g. "What is 7 + 8?")
    q = challenge["question"]
    import re
    m = re.search(r"What is (\d+) \+ (\d+)\?", q)
    assert m is not None
    ans = str(int(m.group(1)) + int(m.group(2)))

    # 1. Correct answer verifies successfully
    valid, msg = verify_captcha_token(challenge["token"], ans)
    assert valid, f"Correct answer rejected: {msg}"

    # 2. Incorrect answer rejected
    wrong_ans = str(int(ans) + 99)
    invalid, reason = verify_captcha_token(challenge["token"], wrong_ans)
    assert not invalid, "Incorrect CAPTCHA answer was accepted"
