#!/usr/bin/env python

"""
twitter-repeater is a bot that automatically retweets any tweets in which its name
is "mentioned" in. In order for a tweet to be retweeted, the bot account must be
following the original user who tweeted it, that user must not be on the ignore
list, and the tweet must pass some basic quality tests.

Please see the README at https://github.com/chooper/twitter-repeater/ for more info
"""

# imports
import os, time, json
from sys import exit
from urlparse import urlparse
from contextlib import contextmanager
import tweepy
import redis

# import exceptions
from urllib2 import HTTPError

def log(**kwargs):
    print ' '.join( "{0}={1}".format(k,v) for k,v in sorted(kwargs.items()) )


@contextmanager
def measure(**kwargs):
    start = time.time()
    status = {'status': 'starting'}
    log(**dict(kwargs.items() + status.items()))
    try:
        yield
    except Exception, e:
        status = {'status': 'err', 'exception': "'{0}'".format(e)}
        log(**dict(kwargs.items() + status.items()))
        raise
    else:
        status = {'status': 'ok', 'duration': time.time() - start}
        log(**dict(kwargs.items() + status.items()))


def debug_print(text):
    """Print text if debugging mode is on"""
    if os.environ.get('DEBUG'):
        print text


def bus_emit(username,tweet):
    """Sends a tweet to a redis Pub/Sub channel"""
    redis_url = os.environ.get('REDIS_URL', os.environ.get('REDISTOGO_URL'))

    if not redis_url:
        log(at='bus_emit', status='skipped', reason='no_redis_url')
        return

    r = redis.from_url(redis_url)

    publish_key = 'repeater:{0}'.format(username.lower())
    serialized_tweet = json.dumps(tweet)
    debug_print(serialized_tweet)
    r.publish(publish_key, serialized_tweet)
    r.close()
    log(at='bus_emit', status='ok')


def filter_or_retweet(api,reply):
    """Perform retweets while avoiding loops and spam"""

    username = os.environ.get('TW_USERNAME')
    normalized_tweet = reply.text.lower().strip()

    # ignore tweet if we've already tweeted it
    if reply.retweeted:
        log(at='filter', reason='already_retweeted', tweet=reply.id)
        return

    # Don't try to retweet our own tweets
    if reply.user.screen_name.lower() == username.lower():
        log(at='filter', reason='is_my_tweet', tweet=reply.id)
        return

    # HACK: Don't retweet if tweet contains more usernames than words (roughly)
    username_count = normalized_tweet.count('@')
    if username_count >= len(normalized_tweet.split()) - username_count:
        log(at='filter', reason='too_many_usernames', tweet=reply.id)
        return

    log(at='retweet', tweet=reply.id)
    return api.retweet(id=reply.id)


def validate_env():
    keys = [
        'TW_USERNAME',
        'TW_CONSUMER_KEY',
        'TW_CONSUMER_SECRET',
        'TW_ACCESS_TOKEN',
        'TW_ACCESS_TOKEN_SECRET',
        ]

    # Check for missing env vars
    for key in keys:
        v = os.environ.get(key)
        if not v:
            log(at='validate_env', status='missing', var=key)
            raise ValueError("Missing ENV var: {0}".format(key))

    # Log success
    log(at='validate_env', status='ok')


def main():
    log(at='main')
    main_start = time.time()

    validate_env()

    username          = os.environ.get('TW_USERNAME')
    consumer_key      = os.environ.get('TW_CONSUMER_KEY')
    consumer_secret   = os.environ.get('TW_CONSUMER_SECRET')
    access_key        = os.environ.get('TW_ACCESS_TOKEN')
    access_secret     = os.environ.get('TW_ACCESS_TOKEN_SECRET')
    redis_url         = os.environ.get('REDIS_URL')

    auth = tweepy.OAuthHandler(consumer_key=consumer_key,
        consumer_secret=consumer_secret)
    auth.set_access_token(access_key, access_secret)

    api = tweepy.API(auth_handler=auth, secure=True, retry_count=3)

    with measure(at='fetch_friends'):
        friends = api.friends_ids()

    with measure(at='fetch_mentions'):
        replies = api.mentions_timeline()

    log(at='fetched_from_api', friends=len(friends), mentions=len(replies))

    for reply in reversed(replies):
        # ignore tweet if it's not from someone we follow and send notification
        # TODO: dedup on subsequent runs?
        if reply.user.id not in friends:
            log(at='ignore', tweet=reply.id, reason='not_followed')
            tweet_dict = dict(id=reply.id, user=reply.user.screen_name, text=reply.text)
            bus_emit(username, tweet_dict)
            continue

        try:
            filter_or_retweet(api,reply)
        except HTTPError, e:
            log(at='rt_error', klass='HTTPError', code=e.code(), body_size=len(e.read()))
            debug_log(e.code())
            debug_log(e.read())
        except Exception, e:
            log(at='rt_error', klass='Exception', msg="'{0}'".format(str(e)))
            debug_log('e: %s' % e)
            raise

    log(at='finish', status='ok', duration=time.time() - main_start)

if __name__ == '__main__':
    # set up raven/sentry
    raven_url = os.environ.get('RAVEN_URL')
    if raven_url:
        import raven
        raven_client = raven.Client(raven_url)
    else:
        raven_client = None

    try:
        main()
    except KeyboardInterrupt:
        log(at='keyboard_interrupt')
        quit()
    except:
        if raven_client:
            raven_client.captureException()
        raise

