import requests
from datetime import datetime, timedelta
import logging
import os
from github import Github
from github.GithubException import GithubException

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, token=None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        if self.token:
            try:
                self.github = Github(self.token)
                self.headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                # Test connection
                self.github.get_user().login
                logger.info("Successfully authenticated with GitHub")
            except GithubException as e:
                logger.error(f"Failed to authenticate with GitHub: {str(e)}")
                self.github = None
                self.headers = {"Accept": "application/vnd.github.v3+json"}
        else:
            logger.warning("No GitHub token provided")
            self.github = None
            self.headers = {"Accept": "application/vnd.github.v3+json"}

    def get_four_keys_metrics(self):
        if not self.github:
            logger.warning("GitHub client not initialized, returning empty metrics")
            return self._get_empty_metrics()

        try:
            # Calculate metrics for the last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            metrics = {
                "deployment_frequency": self._get_deployment_frequency(start_date, end_date),
                "lead_time": self._get_lead_time(start_date, end_date),
                "change_failure_rate": self._get_change_failure_rate(start_date, end_date),
                "time_to_restore": self._get_time_to_restore(start_date, end_date)
            }
            logger.info(f"Successfully fetched GitHub metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error fetching GitHub metrics: {str(e)}")
            return self._get_empty_metrics()

    def _get_deployment_frequency(self, start_date, end_date):
        try:
            total_deployments = 0
            for repo in self.github.get_user().get_repos():
                try:
                    deployments = repo.get_deployments()
                    for deployment in deployments:
                        created_at = deployment.created_at
                        if start_date <= created_at <= end_date:
                            total_deployments += 1
                except GithubException as e:
                    logger.warning(f"Error fetching deployments for repo {repo.name}: {str(e)}")
                    continue

            days = (end_date - start_date).days
            frequency = total_deployments / days if days > 0 else 0
            return {"value": round(frequency, 2), "unit": "per day"}
        except Exception as e:
            logger.error(f"Error calculating deployment frequency: {str(e)}")
            return {"value": 0, "unit": "per day"}

    def _get_lead_time(self, start_date, end_date):
        try:
            total_lead_time = 0
            total_prs = 0

            for repo in self.github.get_user().get_repos():
                try:
                    pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')
                    for pr in pulls:
                        if pr.merged and start_date <= pr.merged_at <= end_date:
                            lead_time = (pr.merged_at - pr.created_at).total_seconds() / 86400  # Convert to days
                            total_lead_time += lead_time
                            total_prs += 1
                except GithubException as e:
                    logger.warning(f"Error fetching pull requests for repo {repo.name}: {str(e)}")
                    continue

            average_lead_time = total_lead_time / total_prs if total_prs > 0 else 0
            return {"value": round(average_lead_time, 2), "unit": "days"}
        except Exception as e:
            logger.error(f"Error calculating lead time: {str(e)}")
            return {"value": 0, "unit": "days"}

    def _get_change_failure_rate(self, start_date, end_date):
        try:
            total_deployments = 0
            failed_deployments = 0

            for repo in self.github.get_user().get_repos():
                try:
                    deployments = repo.get_deployments()
                    for deployment in deployments:
                        if start_date <= deployment.created_at <= end_date:
                            total_deployments += 1
                            statuses = deployment.get_statuses()
                            if any(status.state == 'failure' for status in statuses):
                                failed_deployments += 1
                except GithubException as e:
                    logger.warning(f"Error fetching deployment statuses for repo {repo.name}: {str(e)}")
                    continue

            failure_rate = (failed_deployments / total_deployments * 100) if total_deployments > 0 else 0
            return {"value": round(failure_rate, 2), "unit": "percent"}
        except Exception as e:
            logger.error(f"Error calculating change failure rate: {str(e)}")
            return {"value": 0, "unit": "percent"}

    def _get_time_to_restore(self, start_date, end_date):
        try:
            total_restore_time = 0
            total_incidents = 0

            for repo in self.github.get_user().get_repos():
                try:
                    issues = repo.get_issues(state='closed', labels=['incident'])
                    for issue in issues:
                        if start_date <= issue.closed_at <= end_date:
                            restore_time = (issue.closed_at - issue.created_at).total_seconds() / 3600  # Convert to hours
                            total_restore_time += restore_time
                            total_incidents += 1
                except GithubException as e:
                    logger.warning(f"Error fetching incidents for repo {repo.name}: {str(e)}")
                    continue

            average_restore_time = total_restore_time / total_incidents if total_incidents > 0 else 0
            return {"value": round(average_restore_time, 2), "unit": "hours"}
        except Exception as e:
            logger.error(f"Error calculating time to restore: {str(e)}")
            return {"value": 0, "unit": "hours"}

    def _get_empty_metrics(self):
        return {
            "deployment_frequency": {"value": 0, "unit": "per day"},
            "lead_time": {"value": 0, "unit": "days"},
            "change_failure_rate": {"value": 0, "unit": "percent"},
            "time_to_restore": {"value": 0, "unit": "hours"}
        }