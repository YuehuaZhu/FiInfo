from fiinfo.sources.fixture import FixtureTweetSource
from fiinfo.sources.playwright_src import PlaywrightTweetSource


def test_fixture_returns_tweets_for_known_handle():
    src = FixtureTweetSource()
    tweets = src.fetch_recent("VitalikButerin", limit=5)
    assert len(tweets) >= 1
    assert tweets[0].text


def test_fixture_unknown_handle_returns_empty():
    assert FixtureTweetSource().fetch_recent("nobody", limit=5) == []


def test_playwright_no_cookie_returns_empty():
    src = PlaywrightTweetSource(auth_token="")
    assert src.fetch_recent("VitalikButerin", limit=3) == []
