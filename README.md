A Canadian computer programming competition. Uses Heroku.

To run it on your local machine, first install dependencies like so:

1. Use your OS package manager to get ruby, gem, python2, and virtualenv2
2. cd into jhkg
3. Create a Python 2 virtualenv using `virtualenv venv`
4. Activate your virtualenv using `source venv/bin/activate`
5. Install the required python packages using `pip install -r requirements.txt`
6. Install foreman using `gem install foreman`

Then run the app with `foreman start`.
