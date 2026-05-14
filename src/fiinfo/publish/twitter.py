from fiinfo.publish.base import Publisher


class TwitterPublisher(Publisher):
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_secret: str,
    ):
        if not all([consumer_key, consumer_secret, access_token, access_secret]):
            raise RuntimeError("Twitter write credentials missing — use DryRunPublisher instead")
        import tweepy

        self.client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )

    def publish_threads(self, threads: list[list[str]]) -> list[str]:
        ids: list[str] = []
        for thread in threads:
            prev = None
            for tweet in thread:
                resp = self.client.create_tweet(text=tweet[:280], in_reply_to_tweet_id=prev)
                prev = resp.data["id"]
            ids.append(str(prev))
        return ids
