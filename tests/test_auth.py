"""Tests for Telegram initData HMAC-SHA256 authentication."""

import hashlib
import hmac
import json
import time
from urllib.parse import quote, urlencode

import pytest


def _build_init_data(
    bot_token: str = "test-token",  # noqa: S107
    user_id: int = 123456,
    username: str = "testuser",
    auth_date: int | None = None,
) -> str:
    """Build a valid Telegram initData string for testing.

    Creates properly signed initData using the same HMAC-SHA256
    algorithm that Telegram uses.
    """
    if auth_date is None:
        auth_date = int(time.time())

    user_data = json.dumps(
        {"id": user_id, "username": username, "first_name": "Test"},
        ensure_ascii=False,
    )

    params = {
        "auth_date": str(auth_date),
        "user": user_data,
        "query_id": "test-query-id",
    }

    # Build data-check-string (sorted keys, joined by \n)
    data_check_string = "\n".join(f"{k}={params[k]}" for k in sorted(params))

    # HMAC-SHA256: secret = HMAC("WebAppData", bot_token)
    secret = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # hash = HMAC(secret, data_check_string)
    computed_hash = hmac.new(
        secret,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    params["hash"] = computed_hash
    return urlencode(params, quote_via=quote)


@pytest.fixture(autouse=True)
def _patch_bot_token(monkeypatch):
    """Patch settings.TELEGRAM_BOT_TOKEN for auth tests.

    Pydantic Settings is cached at import time and monkeypatch on
    os.environ alone won't update it.
    """
    from animantis.config.settings import settings

    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token")


@pytest.mark.api
class TestValidateInitData:
    """Test validate_init_data function directly."""

    def test_valid_init_data(self):
        """Valid initData passes HMAC verification."""
        from animantis.api.auth import validate_init_data

        init_data = _build_init_data()
        result = validate_init_data(init_data)
        assert result["id"] == 123456
        assert result["username"] == "testuser"

    def test_empty_init_data_raises(self):
        """Empty string raises ValueError."""
        from animantis.api.auth import validate_init_data

        with pytest.raises(ValueError, match="Empty"):
            validate_init_data("")

    def test_missing_hash_raises(self):
        """initData without hash raises ValueError."""
        from animantis.api.auth import validate_init_data

        with pytest.raises(ValueError, match="Missing hash"):
            validate_init_data("auth_date=123&user=%7B%22id%22%3A1%7D")

    def test_expired_init_data_raises(self):
        """initData older than 1 hour raises ValueError."""
        from animantis.api.auth import validate_init_data

        old_time = int(time.time()) - 7200  # 2 hours ago
        init_data = _build_init_data(auth_date=old_time)

        with pytest.raises(ValueError, match="expired"):
            validate_init_data(init_data)

    def test_tampered_data_raises(self):
        """Modified initData fails HMAC verification."""
        from animantis.api.auth import validate_init_data

        init_data = _build_init_data()
        # Tamper with auth_date
        tampered = init_data.replace("auth_date=", "auth_date=9")

        with pytest.raises(ValueError, match="Invalid initData signature"):
            validate_init_data(tampered)

    def test_wrong_token_raises(self):
        """initData signed with different token fails."""
        from animantis.api.auth import validate_init_data

        init_data = _build_init_data(bot_token="wrong-token")  # noqa: S106

        with pytest.raises(ValueError, match="Invalid initData signature"):
            validate_init_data(init_data)

    def test_missing_user_raises(self):
        """initData without user field raises ValueError."""
        from animantis.api.auth import validate_init_data

        auth_date = str(int(time.time()))
        params = {"auth_date": auth_date, "query_id": "test"}

        data_check_string = "\n".join(f"{k}={params[k]}" for k in sorted(params))
        secret = hmac.new(
            b"WebAppData",
            b"test-token",
            hashlib.sha256,
        ).digest()
        h = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
        params["hash"] = h

        init_data = urlencode(params, quote_via=quote)
        with pytest.raises(ValueError, match="Missing user"):
            validate_init_data(init_data)
