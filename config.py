import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # In the previous line we used or to have a default value beside the os.environ
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = 'FLASKY'
    FLASKY_MAIL_SENDER = 'FLASKY SUPPORT <mail.protocol.sender@gmail.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    PATH_PROFILE_IMAGES = os.path.join(basedir, 'app', 'static', 'profile_images')
    MAX_CONTENT_LENGTH = 256 * 1024  # Maximum upload size
    PATH_STATIC = os.path.join(basedir , 'app' , 'static')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQL_DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or \
                              "C:/Users/HP 450 G2/PycharmProjects/flasky_project/app/database/database.db"


class TestingConfig(Config):
    TESTING = True
    SQL_DATABASE_URL = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'


class ProductionConfig(Config):
    SQL_DATABASE_URL = os.environ.get('DATABASE_URL')
    # pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
