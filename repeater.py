#!/usr/bin/env python

"""
twitter-repeater is a bot that automatically retweets any tweets in which its name
is "mentioned" in. In order for a tweet to be retweeted, the bot account must be
following the original user who tweeted it, that user must not be on the ignore
list, and the tweet must pass some basic quality tests.

Please see the README at https://github.com/chooper/twitter-repeater/ for more info
"""

# imports
import os
from sys import exit
import tweepy

# import exceptions
from urllib2 import HTTPError

def debug_print(text):
    """Print text if debugging mode is on"""
    if os.environ.get('DEBUG'):
        print text


def careful_retweet(api,reply):
    """Perform retweets while avoiding loops and spam"""

    username = os.environ.get('TW_USERNAME')

    debug_print('Preparing to retweet #%d' % (reply.id,))
    normalized_tweet = reply.text.lower().strip()

    # Don't try to retweet our own tweets
    if reply.user.screen_name.lower() == username.lower():
        debug_print("Not retweeting: Own tweet")
        return

    # HACK: Don't retweet if tweet contains more usernames than words (roughly)
    username_count = normalized_tweet.count('@')
    if username_count >= len(normalized_tweet.split()) - username_count:
        debug_print("Not retweeting: Failed @ test")
        return

    debug_print('Retweeting #%d' % (reply.id,))
    return api.retweet(id=reply.id)


def validate_env():
    keys = [
        'TW_USERNAME',
        'TW_CONSUMER_KEY',
        'TW_CONSUMER_SECRET',
        'TW_ACCESS_TOKEN',
        'TW_ACCESS_TOKEN_SECRET',
        ]

    for key in keys:
        v = os.environ.get(key)
        if not v:
            raise ValueError("Missing ENV var: {0}".format(key))


def main():
    validate_env()

    consumer_key      = os.environ.get('TW_CONSUMER_KEY')
    consumer_secret   = os.environ.get('TW_CONSUMER_SECRET')
    access_key        = os.environ.get('TW_ACCESS_TOKEN')
    access_secret     = os.environ.get('TW_ACCESS_TOKEN_SECRET')

    auth = tweepy.OAuthHandler(consumer_key=consumer_key,
        consumer_secret=consumer_secret)
    auth.set_access_token(access_key, access_secret)

    api = tweepy.API(auth_handler=auth, secure=True, retry_count=3)

    debug_print('Loading friends list')
    friends = api.friends_ids()
    debug_print('Friend list loaded, size: %d' % len(friends))

    try:
        debug_print('Retrieving mentions')
        replies = api.mentions_timeline()
    except Exception, e:    # quit on error here
        print e
        exit(1)

    # want these in ascending order, api orders them descending
    replies.reverse()

    for reply in replies:
        # ignore twet if we've already tweeted it
        if reply.retweeted:
            continue

        # ignore tweet if it's not from someone we follow
        if reply.user.id not in friends:
            continue

        try:
            careful_retweet(api,reply)
        except HTTPError, e:
            print e.code()
            print e.read()
        except Exception, e:
            print 'e: %s' % e
            print repr(e)

    debug_print('Exiting cleanly')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        quit()

