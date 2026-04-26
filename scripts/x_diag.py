"""Quick test: does app-only bearer token unlock the read endpoints we need?

If yes, we use it for replies.py (no rotation, no refresh, never expires).
"""
import os, tweepy

print("\n=== App-only Bearer Token (no rotation, never expires) ===")
c = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])

tests = [
    ("search_recent_tweets · @-mention",
        lambda: c.search_recent_tweets(query="@mobfoesteelo OR @prior_agent",
                                        max_results=10,
                                        tweet_fields=["created_at","author_id","conversation_id"],
                                        expansions=["author_id"],
                                        user_fields=["username","public_metrics","created_at"])),
    ("search_recent_tweets · plain query",
        lambda: c.search_recent_tweets(query="from:elonmusk",
                                        max_results=10)),
    ("get_users_mentions",
        lambda: c.get_users_mentions(id="2047071438956331008", max_results=5)),
]

for name, fn in tests:
    try:
        r = fn()
        if r and r.data:
            n = len(r.data) if isinstance(r.data, list) else 'object'
            print(f"  OK    {name}: 200 ({n})")
        else:
            print(f"  OK    {name}: 200 (empty)")
    except tweepy.errors.Unauthorized:
        print(f"  FAIL  {name}: 401 Unauthorized")
    except tweepy.errors.Forbidden as e:
        print(f"  FAIL  {name}: 403 Forbidden -- {str(e)[:140]}")
    except Exception as e:
        print(f"  FAIL  {name}: {type(e).__name__} -- {str(e)[:140]}")
