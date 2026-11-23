#!/usr/bin/env python3
"""Review posts from an authorized Instagram account and add verified events."""

import getpass
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ACCOUNT = "lujan.creative"
API = "https://graph.instagram.com/v27.0"
OUTPUT = Path(__file__).resolve().with_name("instagram-events.js")
PREFIX = "window.SIGNAL_INSTAGRAM_EVENTS = "
SUFFIX = ";\n"


class ReviewError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_get(path, fields, token):
    query = urlencode({"fields": fields, "access_token": token})
    request = Request(f"{API}/{path}?{query}", headers={"Accept": "application/json"})
    try:
        with build_opener(NoRedirect).open(request, timeout=20) as response:
            data = json.load(response)
    except HTTPError as exc:
        try:
            error = json.load(exc).get("error", {})
            code = error.get("code")
            code = str(code) if isinstance(code, int) else "unknown"
        except (ValueError, AttributeError):
            code = "unknown"
        raise ReviewError(f"Meta API request failed (HTTP {exc.code}, Meta code {code}). Check token, app permissions, and account access.") from None
    except (URLError, TimeoutError, OSError):
        raise ReviewError("Could not reach the Meta API. Check your network connection and try again.") from None
    except ValueError:
        raise ReviewError("Meta returned an invalid response.") from None
    if not isinstance(data, dict):
        raise ReviewError("Meta returned an unexpected response.")
    return data


def get_posts(token):
    account = api_get("me", "user_id,username", token)
    username, account_id = account.get("username"), account.get("user_id")
    if not isinstance(username, str) or username.casefold() != ACCOUNT:
        raise ReviewError(f"The token must belong to @{ACCOUNT}. No posts were imported.")
    if not isinstance(account_id, (str, int)) or not str(account_id).isdigit():
        raise ReviewError("Meta did not return a valid Instagram account ID.")
    result = api_get(f"{account_id}/media", "id,permalink,timestamp,media_type", token)
    posts = result.get("data")
    if not isinstance(posts, list):
        raise ReviewError("Meta did not return a valid media list.")
    paging = result.get("paging")
    if paging is not None and not isinstance(paging, dict):
        raise ReviewError("Meta returned invalid pagination information.")
    return posts, bool(paging and paging.get("next"))


def valid_post(post):
    if not isinstance(post, dict):
        return False
    media_id, url = post.get("id"), post.get("permalink")
    if not isinstance(media_id, str) or not media_id.isdigit() or not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url)
        return parts.scheme == "https" and parts.hostname in ("instagram.com", "www.instagram.com") and not parts.username and not parts.password and parts.port in (None, 443)
    except ValueError:
        return False


def load_events(path=OUTPUT):
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReviewError(f"Cannot read the reviewed events file: {exc.strerror}") from None
    if not content.startswith(PREFIX) or not content.endswith(SUFFIX):
        raise ReviewError("The reviewed events file has an unexpected format; no changes were made.")
    try:
        events = json.loads(content[len(PREFIX):-len(SUFFIX)])
    except json.JSONDecodeError:
        raise ReviewError("The reviewed events file is invalid; no changes were made.") from None
    if not isinstance(events, list) or not all(isinstance(item, dict) for item in events):
        raise ReviewError("The reviewed events file is invalid; no changes were made.")
    return events


def save_events(events, path=OUTPUT):
    content = PREFIX + json.dumps(events, ensure_ascii=True, indent=2) + SUFFIX
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_name = file.name
            file.write(content)
        os.replace(temp_name, path)
    except OSError as exc:
        raise ReviewError(f"Could not save reviewed events: {exc.strerror}") from None
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def prompt_required(label):
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Please enter a value.")


def prompt_date(label, earliest=None):
    while True:
        value = prompt_required(f"{label} (YYYY-MM-DD)")
        try:
            parsed = date.fromisoformat(value)
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError
            if earliest and parsed < earliest:
                print("End date must be on or after the start date.")
                continue
            return parsed
        except ValueError:
            print("Enter a valid date in YYYY-MM-DD format.")


def review_post(post):
    print(f"\nPost: {post['permalink']}")
    print(f"Published: {post.get('timestamp', 'unknown')} (this is not the event date)")
    while True:
        answer = input("Open the link to review it. Add an event from this post? [y/n/q]: ").strip().lower()
        if answer in ("y", "n", "q"):
            break
        print("Enter y, n, or q.")
    if answer != "y":
        return answer, None
    title = prompt_required("Event title")
    venue = prompt_required("Venue")
    location = prompt_required("Location")
    start = prompt_date("Start date")
    end = prompt_date("End date", start)
    details = prompt_required("Details (include event time and time zone if known)")
    return answer, {
        "sourceId": post["id"],
        "title": title,
        "venue": venue,
        "location": location,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "details": details,
        "url": post["permalink"],
    }


def main():
    print(f"Review recent posts from @{ACCOUNT}. Your token will not be displayed or saved.")
    token = getpass.getpass("Instagram user access token: ").strip()
    if not token:
        raise ReviewError("No token supplied.")
    events = load_events()
    posts, has_more = get_posts(token)
    print(f"Found {len(posts)} posts on the first page.")
    if has_more:
        print("More posts exist; this tool currently reviews the first page only.")
    known_ids = {event.get("sourceId") for event in events}
    for post in posts:
        if not valid_post(post):
            print("Skipped a post with a missing or invalid ID or Instagram link.")
            continue
        if post["id"] in known_ids:
            continue
        answer, event = review_post(post)
        if answer == "q":
            break
        if event:
            events.append(event)
            save_events(events)
            known_ids.add(event["sourceId"])
            print("Saved. Reload the website to see this reviewed event.")
    print("Review complete.")


if __name__ == "__main__":
    try:
        main()
    except (ReviewError, EOFError, KeyboardInterrupt) as exc:
        message = str(exc) if isinstance(exc, ReviewError) else "Review stopped."
        print(message, file=sys.stderr)
        sys.exit(1)
