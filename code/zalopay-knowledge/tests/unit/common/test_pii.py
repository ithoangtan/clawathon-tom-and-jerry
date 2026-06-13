from __future__ import annotations

import pytest

from app.common.pii import mask_pii


class TestMaskPii:
    def test_empty_string_unchanged(self) -> None:
        assert mask_pii("") == ""

    def test_none_like_falsy_returns_as_is(self) -> None:
        # mask_pii expects str; empty is the guard case
        assert mask_pii("") == ""

    def test_masks_email(self) -> None:
        text = "Contact alice@example.com for details."
        assert mask_pii(text) == "Contact [email] for details."

    def test_masks_multiple_emails(self) -> None:
        text = "alice@corp.io and bob@test.org"
        result = mask_pii(text)
        assert "[email]" in result
        assert "alice@corp.io" not in result
        assert "bob@test.org" not in result

    def test_masks_vietnamese_phone_with_leading_zero(self) -> None:
        text = "Call 0912345678 today"
        assert mask_pii(text) == "Call [phone] today"

    def test_masks_vietnamese_phone_with_country_code(self) -> None:
        text = "Call +84912345678 today"
        result = mask_pii(text)
        assert "[phone]" in result
        assert "912345678" not in result

    def test_masks_card_number_with_spaces(self) -> None:
        text = "Card 4111 1111 1111 1111 expires soon"
        result = mask_pii(text)
        assert "[card]" in result
        assert "4111" not in result

    def test_masks_card_number_with_dashes(self) -> None:
        text = "4111-1111-1111-1111"
        assert mask_pii(text) == "[card]"

    def test_applies_all_patterns_in_order(self) -> None:
        text = "Email user@example.com phone 0901234567 card 4111 1111 1111 1111"
        result = mask_pii(text)
        assert "[email]" in result
        assert "[phone]" in result
        assert "[card]" in result
        assert "user@example.com" not in result

    @pytest.mark.parametrize(
        "text,expected_fragment",
        [
            ("no pii here", "no pii here"),
            ("ID: ABC-12345", "ID: ABC-12345"),
        ],
    )
    def test_leaves_non_pii_unchanged(self, text: str, expected_fragment: str) -> None:
        assert expected_fragment in mask_pii(text)
