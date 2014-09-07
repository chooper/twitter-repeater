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
2. Click the Heroku button: [![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)
3. Fill in the fields after creating a new app on the [Twitter's Developer page](https://dev.twitter.com/apps)
4. Configure the scheduler to run the repeater every 10 minutes
    1. `heroku addons:open scheduler`
    2. Click *Add Job* and enter:
        * **Task**: `./repeater.py`
        * **Dyno size**: `1X`
        * **Frequency**: `Every 10 minutes`
    3. Click *Save*

You're all done!

## Traditional (Linux)

Sorry, but these steps are mostly untested and written from memory. Please send
me a pull request if you find a mistake.

1. Check the code out of git: `git clone git@github.com:chooper/twitter-repeater.git`
2. Go to [Twitter's Developer page](https://dev.twitter.com/apps) and create a new application
3. Configure your repeater app with the Oauth credentials twitter gave you
    1. `cp .env.sample .env` and fill in the environment variables
4. Install dependencies (consider a virtualenv): `pip install -r requirements.txt`
5. Test that it works: `source .env ; ./repeater.py`
6. Add a cronjob to run the bot:

  ```
  */10     *       *       *       *       /path/to/repeater/repeater.py
  ```

