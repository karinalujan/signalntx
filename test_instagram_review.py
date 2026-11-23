import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import instagram_review as review


class InstagramReviewTests(unittest.TestCase):
    def test_account_must_match_before_fetching_media(self):
        with patch.object(review, "api_get", return_value={"user_id": "123", "username": "different"}) as api:
            with self.assertRaisesRegex(review.ReviewError, "lujan.creative"):
                review.get_posts("fake-token")
            self.assertEqual(api.call_count, 1)

    def test_fetches_verified_account_posts_and_reports_more_pages(self):
        responses = [
            {"user_id": "123", "username": "Lujan.Creative"},
            {"data": [{"id": "456"}], "paging": {"next": "https://example.invalid"}},
        ]
        with patch.object(review, "api_get", side_effect=responses) as api:
            posts, more = review.get_posts("fake-token")
        self.assertEqual(posts, [{"id": "456"}])
        self.assertTrue(more)
        self.assertEqual(api.call_args_list[1].args[0], "123/media")

    def test_only_accepts_valid_instagram_post_links(self):
        self.assertTrue(review.valid_post({"id": "123", "permalink": "https://www.instagram.com/p/abc/"}))
        for url in ("https://instagram.com.evil.example/p/abc", "http://instagram.com/p/abc", "https://instagram.com:bad/p/abc"):
            self.assertFalse(review.valid_post({"id": "123", "permalink": url}))

    def test_reviewed_event_round_trip_and_reject_invalid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.js"
            original = [{"sourceId": "123", "title": "Art & technology"}]
            review.save_events(original, path)
            self.assertEqual(review.load_events(path), original)
            path.write_text("unexpected content", encoding="utf-8")
            with self.assertRaises(review.ReviewError):
                review.load_events(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "unexpected content")

    def test_event_dates_are_reviewed_and_validated(self):
        post = {"id": "123", "permalink": "https://www.instagram.com/p/abc/", "timestamp": "2026-01-01"}
        replies = ["y", "Exhibition", "Gallery", "Dallas", "bad", "2026-08-29", "2026-08-28", "2026-09-12", "8 PM Central"]
        with patch("builtins.input", side_effect=replies), patch("sys.stdout", new_callable=io.StringIO):
            answer, event = review.review_post(post)
        self.assertEqual(answer, "y")
        self.assertEqual((event["startDate"], event["endDate"]), ("2026-08-29", "2026-09-12"))
        self.assertEqual(event["sourceId"], "123")

    def test_api_errors_do_not_echo_response_or_token(self):
        error = HTTPError("https://example.invalid/?access_token=fake-token", 400, "error", {}, io.BytesIO(json.dumps({"error": {"code": 190, "message": "fake-token"}}).encode()))
        with patch.object(review, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaises(review.ReviewError) as raised:
                review.api_get("me", "username", "fake-token")
        self.assertIn("190", str(raised.exception))
        self.assertNotIn("fake-token", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
