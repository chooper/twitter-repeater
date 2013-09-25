twitter-repeater is a bot that automatically retweets any tweets in
which its name is "mentioned" in. In order for a tweet to be retweeted,
the bot account must be following the original user who tweeted it and the
tweet must pass some basic quality tests.

The idea was originally inspired by the @SanMo bot and was created so I
could use something similar for New London, CT (@NLCT)

It runs well on Linux but it should run just as well on Mac OSX or
Windows.

# Installation

## Heroku

1. Check the code out of git: `git clone git@github.com:chooper/twitter-repeater.git`
2. Create a [Heroku](http://www.heroku.com) app: `heroku create`
3. Go to [Twitter's Developer page](https://dev.twitter.com/apps) and create a new application
4. Configure your Heroku app with the Oauth credentials twitter gave you
   ```
   heroku config:set TW_USERNAME=<twitter username> \
     TW_CONSUMER_KEY=... \
     TW_CONSUMER_SECRET=... \
     TW_ACCESS_TOKEN=... \
     TW_ACCESS_TOKEN_SECRET=... \
     DEBUG=true
   ```
5. Push your application: `git push heroku master`
6. Test that your repeater works: `heroku run ./repeater.py`
7. Add the scheduler addon: `heroku addons:add scheduler:standard`
8. Configure the scheduler to run the repeater every 10 minutes
    1. `heroku addons:open scheduler`
    2. Click *Add Job* and enter:
        * **Task**: `./repeater.py`
        * **Dyno size**: `1X`
        * **Frequency**: `Every 10 minutes`
    3. Click *Save*

That should be it! It seems like alot of steps but after this you're all done!

## Traditional (Linux)

Sorry, but these steps are mostly untested and written from memory. Please send
me a pull request if you find a mistake.

1. Check the code out of git: `git clone git@github.com:chooper/twitter-repeater.git`
2. Go to [Twitter's Developer page](https://dev.twitter.com/apps) and create a new application
3. Configure your repeater app with the Oauth credentials twitter gave you
    1. `cp .env.sample .env` and fill in the environment variables
4. Install dependencies: `pip install -r requirements.txt` (consider using a virtualenv)
5. Test that it works: `source .env ; ./repeater.py`
6 Add a cronjob to run the bot:
  ```
  */10     *       *       *       *       /path/to/repeater/repeater.py
  ```

