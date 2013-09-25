twitter-repeater is a bot that automatically retweets any tweets in
which its name is "mentioned" in. In order for a tweet to be retweeted,
the bot account must be following the original user who tweeted it, that
user must not be on the ignore list, and the tweet must pass some basic
quality tests.

The idea was originally inspired by the @SanMo bot and was created so I
could use something similar for New London, CT (@NLCT)

It runs well on Linux but it should run just as well on Mac OSX or
Windows.

I use the following user Cron job to run the bot every 5 minutes.

```
*/5     *       *       *       *       $HOME/twitter-repeater/repeater.py
```

## Configuration
http://dev.twitter.com/apps

```
TW_USERNAME=
TW_CONSUMER_KEY=
TW_CONSUMER_SECRET=
TW_ACCESS_TOKEN=
TW_ACCESS_TOKEN_SECRET=
DEBUG=
```

