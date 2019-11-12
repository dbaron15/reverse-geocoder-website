from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from flask_security import Security


app = Flask(__name__)
app.config.from_object(Config)
# login = LoginManager(app)
db = SQLAlchemy(app)
# bs = Bootstrap(app)
# admin = Admin(app, name='revgeocoder')

from app import views, models