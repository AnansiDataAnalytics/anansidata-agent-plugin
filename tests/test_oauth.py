from types import SimpleNamespace

from anansi_mcp.oauth import AnansiOAuthProvider, _consent_html


def test_consent_html_escapes_attacker_controlled_client_name():
    page = _consent_html("rid123", "http://127.0.0.1:8000", "<script>alert(1)</script>", "evil.example")
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "evil.example" in page


def test_authz_cookie_binds_authorization_to_browser():
    provider = AnansiOAuthProvider("http://127.0.0.1:8000", "test-secret")
    request = SimpleNamespace(cookies={"anansi_mcp_authz": provider.sign_authz("abc")})
    assert provider.verify_authz(request, "abc") is True
    assert provider.verify_authz(request, "other") is False
    assert provider.verify_authz(SimpleNamespace(cookies={}), "abc") is False
