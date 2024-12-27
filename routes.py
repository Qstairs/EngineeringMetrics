from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import User, db, DashboardPreference
from services.github_service import GitHubService
from services.jira_service import JiraService
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

            # Create default dashboard preferences
            preferences = DashboardPreference(user=user)

            try:
                db.session.add(user)
                db.session.add(preferences)
                db.session.commit()
                logger.info(f"Created new user: {user.username}")
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                db.session.rollback()
                flash('Error creating account')
                return redirect(url_for('signup'))

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
        try:
            github_service = GitHubService(current_user.github_token)
            jira_service = JiraService(current_user.jira_token)

            github_metrics = github_service.get_four_keys_metrics()
            jira_metrics = jira_service.get_metrics()

            # Get or create user preferences
            preferences = current_user.dashboard_preferences
            if not preferences:
                preferences = DashboardPreference(user=current_user)
                db.session.add(preferences)
                db.session.commit()

            # Convert preferences to dictionary for JSON serialization
            preferences_dict = preferences.to_dict()
            logger.debug(f"Dashboard preferences: {preferences_dict}")

            return render_template('dashboard.html',
                                github_metrics=github_metrics,
                                jira_metrics=jira_metrics,
                                preferences=preferences_dict)
        except Exception as e:
            logger.error(f"Error in dashboard route: {str(e)}")
            flash('Error loading dashboard')
            return redirect(url_for('index'))

    @app.route('/api/preferences', methods=['POST'])
    @login_required
    def update_preferences():
        try:
            data = request.get_json()
            preferences = current_user.dashboard_preferences

            preferences.layout = data.get('layout', preferences.layout)
            preferences.chart_type = data.get('chart_type', preferences.chart_type)
            preferences.theme = data.get('theme', preferences.theme)
            preferences.refresh_interval = data.get('refresh_interval', preferences.refresh_interval)
            preferences.metrics_order = json.dumps(data.get('metrics_order', json.loads(preferences.metrics_order)))

            db.session.commit()
            logger.info(f"Updated preferences for user {current_user.username}")
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/api/metrics/refresh')
    @login_required
    def refresh_metrics():
        try:
            github_service = GitHubService(current_user.github_token)
            jira_service = JiraService(current_user.jira_token)

            github_metrics = github_service.get_four_keys_metrics()
            jira_metrics = jira_service.get_metrics()

            return jsonify({
                'github_metrics': github_metrics,
                'jira_metrics': jira_metrics
            })
        except Exception as e:
            logger.error(f"Error refreshing metrics: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))