from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
sess = Session(app)
# bs = Bootstrap(app)

from app import views, models