from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import User, db
from services.github_service import GitHubService
from services.jira_service import JiraService

def register_routes(app):
    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        return redirect(url_for('dashboard'))

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username']).first()
            if user:
                flash('Username already exists')
                return redirect(url_for('signup'))

            user = User(username=request.form['username'], email=request.form['email'])
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('index'))

        return render_template('signup.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username']).first()
            if user is None or not user.check_password(request.form['password']):
                flash('Invalid username or password')
                return redirect(url_for('login'))

            login_user(user)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)

        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        github_service = GitHubService(current_user.github_token)
        jira_service = JiraService(current_user.jira_token)

        github_metrics = github_service.get_four_keys_metrics()
        jira_metrics = jira_service.get_metrics()

        return render_template('dashboard.html', 
                             github_metrics=github_metrics,
                             jira_metrics=jira_metrics)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))