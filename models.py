from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    github_token = db.Column(db.String(256))
    jira_token = db.Column(db.String(256))
    metrics = db.relationship('Metric', backref='user', lazy='dynamic')
    dashboard_preferences = db.relationship('DashboardPreference', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), nullable=False)

class DashboardPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    layout = db.Column(db.String(20), default='grid')  # grid or list
    metrics_order = db.Column(db.String(500), default='["github","jira"]')  # JSON string of ordered metrics
    refresh_interval = db.Column(db.Integer, default=300)  # in seconds
    chart_type = db.Column(db.String(20), default='bar')  # bar or line
    theme = db.Column(db.String(20), default='light')  # light or dark

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))