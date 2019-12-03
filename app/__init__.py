from flask import Flask
from config import DevelopmentConfig, ProductionConfig
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db = SQLAlchemy(app)
bs = Bootstrap(app)

from app import views, models
