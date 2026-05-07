"""Tests for pipeline.telegram — Telegram Bot API helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, mock_open

import pytest

from pipeline.telegram import (
    add_reaction, require_pt_channel_id, send_photo, send_text,
)


class TestSendText:
    """send_text: send a text message to TG."""

    @patch("pipeline.telegram.requests.post")
    def test_basic_send(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 42}
        }
        result = send_text(
            chat_id="-100123",
            caption="Hello world",
            bot_token="test-token",
        )
        assert result == 42
        mock_post.assert_called_once()

    @patch("pipeline.telegram.requests.post")
    def test_with_preview_url(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 43}
        }
        result = send_text(
            chat_id="-100123",
            caption="Check this",
            preview_url="https://example.com/article",
            bot_token="test-token",
        )
        assert result == 43
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        # Text should have invisible link prepended
        assert "\u00a0" in payload["text"]
        assert "example.com" in payload["text"]

    @patch("pipeline.telegram.requests.post")
    def test_silent_mode(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 44}
        }
        send_text(
            chat_id="-100123",
            caption="Quiet",
            silent=True,
            bot_token="test-token",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["disable_notification"] is True

    @patch("pipeline.telegram.requests.post")
    def test_with_button(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 45}
        }
        send_text(
            chat_id="-100123",
            caption="Read more",
            button_url="https://example.com",
            button_text="Open",
            bot_token="test-token",
        )
        payload = mock_post.call_args[1]["json"]
        assert "reply_markup" in payload
        assert payload["reply_markup"]["inline_keyboard"][0][0]["text"] == "Open"
        assert payload["reply_markup"]["inline_keyboard"][0][0]["url"] == "https://example.com"

    @patch("pipeline.telegram.requests.post")
    def test_api_error_returns_none(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": False, "description": "Bad Request"
        }
        result = send_text(
            chat_id="-100123",
            caption="Test",
            bot_token="test-token",
        )
        assert result is None

    @patch("pipeline.telegram.requests.post")
    def test_exception_returns_none(self, mock_post):
        mock_post.side_effect = Exception("Network error")
        result = send_text(
            chat_id="-100123",
            caption="Test",
            bot_token="test-token",
        )
        assert result is None

    @patch("pipeline.telegram.requests.post")
    def test_parse_mode_html(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 46}
        }
        send_text(
            chat_id="-100123",
            caption="<b>Bold</b>",
            bot_token="test-token",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["parse_mode"] == "HTML"

    @patch("pipeline.telegram.requests.post")
    def test_link_preview_options(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 47}
        }
        send_text(
            chat_id="-100123",
            caption="Test",
            preview_url="https://example.com",
            bot_token="test-token",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["link_preview_options"]["prefer_large_media"] is True
        assert payload["link_preview_options"]["show_above_text"] is True
        assert payload["link_preview_options"]["url"] == "https://example.com"

    @patch("pipeline.telegram.requests.post")
    def test_no_preview_url_no_url_in_opts(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 48}
        }
        send_text(
            chat_id="-100123",
            caption="No preview",
            bot_token="test-token",
        )
        payload = mock_post.call_args[1]["json"]
        assert "url" not in payload["link_preview_options"]

    @patch("pipeline.telegram.requests.post")
    def test_chat_id_converted_to_int(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 49}
        }
        send_text(
            chat_id="-100123456",
            caption="Test",
            bot_token="test-token",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["chat_id"] == -100123456


class TestSendPhoto:
    """send_photo: send a photo with caption to TG."""

    @patch("pipeline.telegram.requests.post")
    @patch("builtins.open", mock_open(read_data=b"fake image data"))
    def test_basic_send_photo(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 50}
        }
        result = send_photo(
            chat_id="-100123",
            image_path="/tmp/test.jpg",
            caption="Photo caption",
            bot_token="test-token",
        )
        assert result == 50

    @patch("pipeline.telegram.requests.post")
    @patch("builtins.open", mock_open(read_data=b"fake image data"))
    def test_silent_photo(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 51}
        }
        send_photo(
            chat_id="-100123",
            image_path="/tmp/test.jpg",
            caption="Quiet photo",
            bot_token="test-token",
            silent=True,
        )
        call_args = mock_post.call_args
        assert call_args[1]["data"]["disable_notification"] == "true"

    @patch("pipeline.telegram.requests.post")
    @patch("builtins.open", mock_open(read_data=b"fake image data"))
    def test_photo_api_error(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": False, "description": "Photo too large"
        }
        result = send_photo(
            chat_id="-100123",
            image_path="/tmp/test.jpg",
            caption="Big photo",
            bot_token="test-token",
        )
        assert result is None

    @patch("pipeline.telegram.requests.post")
    def test_photo_exception(self, mock_post):
        mock_post.side_effect = Exception("Upload failed")
        result = send_photo(
            chat_id="-100123",
            image_path="/tmp/test.jpg",
            caption="Error",
            bot_token="test-token",
        )
        assert result is None

    @patch("pipeline.telegram.requests.post")
    @patch("builtins.open", mock_open(read_data=b"fake"))
    def test_photo_html_parse_mode(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 52}
        }
        send_photo(
            chat_id="-100123",
            image_path="/tmp/test.jpg",
            caption="<b>Bold</b>",
            bot_token="test-token",
        )
        call_args = mock_post.call_args
        assert call_args[1]["data"]["parse_mode"] == "HTML"


class TestAddReaction:
    """add_reaction: add emoji reaction to a message."""

    @patch("pipeline.telegram.requests.post")
    def test_basic_reaction(self, mock_post):
        add_reaction(
            chat_id="-100123",
            msg_id=42,
            emoji="\U0001f525",
            bot_token="test-token",
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["chat_id"] == -100123
        assert payload["message_id"] == 42
        assert payload["reaction"][0]["emoji"] == "\U0001f525"

    @patch("pipeline.telegram.requests.post")
    def test_reaction_exception_swallowed(self, mock_post):
        """Reaction failures should not raise exceptions."""
        mock_post.side_effect = Exception("API error")
        # Should not raise
        add_reaction(
            chat_id="-100123",
            msg_id=42,
            emoji="\U0001f525",
            bot_token="test-token",
        )


# ---- pt-translation-b1: PT channel guard ----

class TestRequirePtChannelId:
    """require_pt_channel_id: clear-fail when the env var is missing."""

    def test_returns_id_when_set(self, monkeypatch):
        import pipeline.telegram as tg
        monkeypatch.setattr(tg, "TG_CHANNEL_PT_ID", "-1003999999999")
        assert tg.require_pt_channel_id() == "-1003999999999"

    def test_raises_with_actionable_message_when_empty(self, monkeypatch):
        import pipeline.telegram as tg
        monkeypatch.setattr(tg, "TG_CHANNEL_PT_ID", "")
        with pytest.raises(RuntimeError) as exc_info:
            tg.require_pt_channel_id()
        msg = str(exc_info.value)
        assert "TG_CHANNEL_PT_ID" in msg
        assert "@pashtelka_pt" in msg
        assert "@nero_open_bot" in msg
        assert "~/workspace/.env" in msg

