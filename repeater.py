#!/usr/bin/env python

"""Retweets direct replies"""

import settings

# Load ignore and filtered word lists
IGNORE_LIST = [line.lower().strip() for line in open(settings.ignore_list)]
FILTER_WORDS = [line.lower().strip() for line in open(settings.filtered_word_list)]

from sys import exit
from urllib2 import HTTPError
import tweepy

def debug_print(text):
    """Print text if debugging mode is on"""
    if settings.debug:
        print text


def save_id(statefile,id):
    """Save last status ID to a file"""
    last_id = get_last_id(statefile)

    if last_id < id:
        debug_print('Saving new ID %d to %s' % (id,statefile))
        f = open(statefile,'w')
        f.write(str(id)) # no trailing newline
        f.close()
    else:
        debug_print('Received smaller ID, not saving. Old: %d, New: %s' % (
            last_id, id))


def get_last_id(statefile):
    """Retrieve last status ID from a file"""

    debug_print('Getting last ID from %s' % (statefile,))
    try:
        f = open(statefile,'r')
        id = int(f.read())
        f.close()
    except IOError:
        debug_print('IOError raised, returning zero (0)')
        return 0
    debug_print('Got %d' % (id,))
    return id


def careful_retweet(api,reply):
    """Perform retweets while avoiding loops and spam"""

    debug_print('Preparing to retweet #%d' % (reply.id,))
    normalized_tweet = reply.text.lower().strip()

    # Don't try to retweet our own tweets
    if reply.user.screen_name.lower() == settings.username.lower():
        return

    # Don't retweet if the tweet is from an ignored user
    if reply.user.screen_name.lower() in IGNORE_LIST:
        return

    # Don't retweet if the tweet contains a filtered word
    for word in normalized_tweet.split():
        if word.lower().strip() in FILTER_WORDS:
            return

    # HACK: Don't retweet if tweet contains more usernames than words (roughly)
    username_count = normalized_tweet.count('@')
    if username_count >= len(normalized_tweet.split()) - username_count:
        return

    # Try to break retweet loops by counting the occurences tweeting user's name
    if normalized_tweet.split().count('@'+ reply.user.screen_name.lower()) > 0:
        return

    debug_print('Retweeting #%d' % (reply.id,))
    return api.retweet(id=reply.id)


def main():
    auth = tweepy.BasicAuthHandler(username=settings.username,
        password=settings.password)
    api = tweepy.API(auth_handler=auth, secure=True, retry_count=3)

    last_id = get_last_id(settings.lastid)

    debug_print('Loading friends list')
    friends = api.friends_ids()
    debug_print('Friend list loaded, size: %d' % len(friends))

    try:
        debug_print('Retrieving mentions')
        replies = api.mentions()
    except Exception, e:    # quit on error here
        print e
        exit(1)

    # want these in ascending order, api orders them descending
    replies.reverse()

    for reply in replies:
        # ignore tweet if it's id is lower than our last tweeted id
        if reply.id > last_id and reply.user.id in friends:
            try:
                careful_retweet(api,reply)
            except HTTPError, e:
                print e.code()
                print e.read()
            except Exception, e:
                print 'e: %s' % e
                print repr(e)
            else:
                save_id(settings.lastid,reply.id)

    debug_print('Exiting cleanly')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        quit()

