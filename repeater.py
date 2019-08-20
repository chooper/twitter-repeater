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
import backoff

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


def fav_tweet(api,reply):
    """Attempt to fav a tweet and return True if successful"""

    # sometimes this raises TweepError even if reply.favorited
    # was False
    try:
        api.create_favorite(id=reply.id)
    except tweepy.TweepError, e:
        log(at='fav_error', tweet=reply.id, klass='TweepError', msg="'{0}'".format(str(e)))
        return False

    log(at='favorite', tweet=reply.id)
    return True


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


@backoff.on_exception(backoff.expo, tweepy.TweepError, max_tries=8)
def fetch_friends(api):
    """Fetch friend list from twitter"""
    with measure(at='fetch_friends'):
        friends = api.friends_ids()
    return friends


@backoff.on_exception(backoff.expo, tweepy.TweepError, max_tries=8)
def fetch_mentions(api):
    """Fetch mentions from twitter"""
    with measure(at='fetch_mentions'):
        replies = api.mentions_timeline()
    return replies


def main():
    log(at='main')
    main_start = time.time()

    validate_env()

    owner_username    = os.environ.get('TW_OWNER_USERNAME')
    username          = os.environ.get('TW_USERNAME')
    consumer_key      = os.environ.get('TW_CONSUMER_KEY')
    consumer_secret   = os.environ.get('TW_CONSUMER_SECRET')
    access_key        = os.environ.get('TW_ACCESS_TOKEN')
    access_secret     = os.environ.get('TW_ACCESS_TOKEN_SECRET')

    auth = tweepy.OAuthHandler(consumer_key=consumer_key,
        consumer_secret=consumer_secret, secure=True)
    auth.set_access_token(access_key, access_secret)

    api = tweepy.API(auth_handler=auth, secure=True, retry_count=3)
    friends = fetch_friends(api)
    replies = fetch_mentions(api)

    log(at='fetched_from_api', friends=len(friends), mentions=len(replies))

    for reply in reversed(replies):
        # ignore tweet if it's not from someone we follow and send notification
        if reply.user.id not in friends:
            if not reply.favorited: # TODO: log "seen" status
                prev_seen = "false"
                status = fav_tweet(api, reply)
            else:
                prev_seen = "true"

            log(at='ignore', tweet=reply.id, reason='not_followed', prev_seen=prev_seen)
            continue

        try:
            filter_or_retweet(api,reply)
        except HTTPError, e:
            log(at='rt_error', klass='HTTPError', code=e.code(), body_size=len(e.read()))
            debug_print(e.code())
            debug_print(e.read())
        except Exception, e:
            log(at='rt_error', klass='Exception', msg="'{0}'".format(str(e)))
            debug_print('e: %s' % e)
            raise

    log(at='finish', status='ok', duration=time.time() - main_start)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log(at='keyboard_interrupt')
        quit()
    except:
        raise

