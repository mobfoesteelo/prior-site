"""Diagnostic — does OAuth 2.0 user context unlock read endpoints?

Tests both auth methods against the same read endpoints.
"""
import os, tweepy

print("\n=== OAuth 1.0a User Context (current write auth) ===")
c1 = tweepy.Client(
    consumer_key        = os.environ["X_API_KEY"],
    consumer_secret     = os.environ["X_API_SECRET"],
    access_token        = os.environ["X_ACCESS_TOKEN"],
    access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
)

print("\n=== OAuth 2.0 User Context (just provided) ===")
c2 = tweepy.Client(os.environ["X_OAUTH2_ACCESS_TOKEN"])

tests = [
    ("get_me",                lambda c: c.get_me()),
    ("get_users_mentions",    lambda c: c.get_users_mentions(id="2047071438956331008", max_results=5)),
    ("search_recent_tweets",  lambda c: c.search_recent_tweets(query="from:elonmusk", max_results=10)),
    ("get_users_tweets",      lambda c: c.get_users_tweets(id="2047071438956331008", max_results=5)),
]

for label, c in [("OAuth 1.0a", c1), ("OAuth 2.0 ", c2)]:
    print(f"\n{label}:")
    for name, fn in tests:
        try:
            r = fn(c)
            if r and r.data:
                n = len(r.data) if isinstance(r.data, list) else 'object'
                print(f"  OK    {name}: 200 ({n})")
            else:
                print(f"  OK    {name}: 200 (empty)")
        except tweepy.errors.Unauthorized:
            print(f"  FAIL  {name}: 401 Unauthorized")
        except tweepy.errors.Forbidden as e:
            print(f"  FAIL  {name}: 403 Forbidden -- {str(e)[:140]}")
        except tweepy.errors.TooManyRequests:
            print(f"  RATE  {name}: 429")
        except Exception as e:
            print(f"  FAIL  {name}: {type(e).__name__} -- {str(e)[:140]}")
