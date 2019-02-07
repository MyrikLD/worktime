import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '9vm+b4leaqg3ym^%^7725&#r_11&rdq*7jnj^m^yj@apcwu3t0'

DEBUG = False

INSTALLED_APPS = ['worktimer']
#TIME_ZONE = 'Europe/Minsk'
#USE_TZ = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.db'),
    }
}
