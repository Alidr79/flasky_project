from flask import Flask, render_template
from flask_mail import Mail
from flask_moment import Moment
from config import config  # --> the second config is the dict that we have defined
from flask_login import LoginManager

import datetime

mail = Mail()
moment = Moment()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Please login to your account'


def time_from(timestamp):
    input_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    delta = (now - input_time).total_seconds()

    _delay_string = None
    if delta < 60:
        _delay_string = "less than a minute ago"
    elif int(delta / 60) < 60:
        _delay_string = "{} minute/minutes ago".format(int(delta / 60))
    elif int(delta / (60 * 60)) < 24:
        _delay_string = "{} hour/hours ago".format(int(delta / (60 * 60)))
    elif int(delta / (60 * 60 * 24)) < 50:
        _delay_string = "{} days ago".format(int(delta / (60 * 60 * 24)))
    else:
        _delay_string = "long time ago"

    return _delay_string


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)

    # custom functions
    app.jinja_env.globals.update(time_from=time_from)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app
