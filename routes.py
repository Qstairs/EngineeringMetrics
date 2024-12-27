import logging
from datetime import datetime
import json
import markdown
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, current_app as app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import User, DashboardPreference
from services.github_service import GitHubService
from services.jira_service import JiraService

logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            user = User.query.filter_by(username=request.form.get('username')).first()
            if user and user.check_password(request.form.get('password')):
                login_user(user)
                return redirect(url_for('dashboard'))
            flash('Invalid username or password')
        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return render_template('signup.html')

            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return render_template('signup.html')

            user = User(username=username, email=email)
            user.set_password(password)

            # Create default dashboard preferences
            preferences = DashboardPreference(user=user)

            db.session.add(user)
            db.session.add(preferences)
            db.session.commit()

            login_user(user)
            return redirect(url_for('dashboard'))

        return render_template('signup.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Initialize services with user tokens
        github_service = GitHubService(current_user.github_token)
        jira_service = JiraService(current_user.jira_token)

        # Get metrics
        github_metrics = github_service.get_four_keys_metrics()
        jira_metrics = jira_service.get_metrics()

        # Get user preferences
        preferences = current_user.dashboard_preferences
        if not preferences:
            preferences = DashboardPreference(user=current_user)
            db.session.add(preferences)
            db.session.commit()

        return render_template('dashboard.html',
                             github_metrics=github_metrics,
                             jira_metrics=jira_metrics,
                             preferences=preferences.to_dict())

    @app.route('/api/metrics/refresh')
    @login_required
    def refresh_metrics():
        github_service = GitHubService(current_user.github_token)
        jira_service = JiraService(current_user.jira_token)

        return jsonify({
            'github_metrics': github_service.get_four_keys_metrics(),
            'jira_metrics': jira_service.get_metrics()
        })

    @app.route('/api/preferences', methods=['POST'])
    @login_required
    def update_preferences():
        try:
            data = request.get_json()
            preferences = current_user.dashboard_preferences

            if not preferences:
                preferences = DashboardPreference(user=current_user)
                db.session.add(preferences)

            preferences.layout = data.get('layout', 'grid')
            preferences.chart_type = data.get('chart_type', 'bar')
            preferences.theme = data.get('theme', 'light')
            preferences.refresh_interval = data.get('refresh_interval', 300)
            preferences.metrics_order = json.dumps(data.get('metrics_order', ['github', 'jira']))

            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/readme_generator')
    @login_required
    def readme_generator():
        initial_content = """# プロジェクト名

## プロジェクトの概要

## 主な機能

## 技術スタック

## インストール方法

## 環境設定

## 使用方法

## 開発ガイドライン
"""
        return render_template('readme_generator.html', initial_content=initial_content)

    @app.route('/api/preview_markdown', methods=['POST'])
    @login_required
    def preview_markdown():
        try:
            content = request.get_json().get('content', '')
            html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
            return jsonify({'html': html})
        except Exception as e:
            logger.error(f"Error converting markdown: {str(e)}")
            return jsonify({'error': str(e)}), 500

    logger.info("All routes registered successfully")