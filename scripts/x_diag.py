"""Diagnostic — what X read endpoints work on this app's tokens."""
import os, tweepy

c = tweepy.Client(
    consumer_key        = os.environ["X_API_KEY"],
    consumer_secret     = os.environ["X_API_SECRET"],
    access_token        = os.environ["X_ACCESS_TOKEN"],
    access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
)

tests = [
    ("get_me",                lambda: c.get_me()),
    ("get_users_mentions",    lambda: c.get_users_mentions(id="2047071438956331008", max_results=5)),
    ("search_recent_tweets",  lambda: c.search_recent_tweets(query="from:elonmusk", max_results=10)),
    ("get_users_tweets",      lambda: c.get_users_tweets(id="2047071438956331008", max_results=5)),
]

for name, fn in tests:
    try:
        r = fn()
        if r and r.data:
            n = len(r.data) if isinstance(r.data, list) else 'object'
            print(f"  OK    {name}: 200 ({n} items)")
        else:
            print(f"  OK    {name}: 200 (no data)")
    except tweepy.errors.Unauthorized:
        print(f"  FAIL  {name}: 401 Unauthorized")
    except tweepy.errors.Forbidden as e:
        print(f"  FAIL  {name}: 403 Forbidden -- {str(e)[:120]}")
    except tweepy.errors.TooManyRequests:
        print(f"  RATE  {name}: 429")
    except Exception as e:
        print(f"  FAIL  {name}: {type(e).__name__} -- {str(e)[:120]}")
