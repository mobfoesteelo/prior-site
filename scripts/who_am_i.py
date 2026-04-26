"""Quick self-test: confirm bot's handle + recent mentions."""
import os, tweepy, sys

bt = os.environ["X_BEARER_TOKEN"]
c = tweepy.Client(bearer_token=bt)

# Resolve handle
try:
    me = c.get_user(id="2047071438956331008", user_fields=["created_at","public_metrics"])
    if me and me.data:
        u = me.data
        print(f"BOT HANDLE: @{u.username}")
        print(f"  display name: {u.name}")
        print(f"  followers: {getattr(u.public_metrics, 'followers_count', '?') if u.public_metrics else '?'}")
        print(f"  following: {getattr(u.public_metrics, 'following_count', '?') if u.public_metrics else '?'}")
        print(f"  tweets: {getattr(u.public_metrics, 'tweet_count', '?') if u.public_metrics else '?'}")
        print(f"  created: {u.created_at}")
except Exception as e:
    print(f"FAIL get_user: {e}")

# Search for any tweets mentioning the handle (last 7 days)
try:
    if me and me.data:
        q = f"@{me.data.username}"
        print(f"\nSearching: {q}")
        r = c.search_recent_tweets(query=q, max_results=10, tweet_fields=["created_at","author_id"])
        if r and r.data:
            print(f"  found {len(r.data)} mentions in last 7d:")
            for t in r.data[:5]:
                print(f"    [{t.created_at}] author {t.author_id}: {t.text[:120]}")
        else:
            print("  no mentions found")
except Exception as e:
    print(f"FAIL search: {e}")
