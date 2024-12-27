import requests
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, token):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}" if self.token else "",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_four_keys_metrics(self):
        if not self.token:
            logger.warning("No GitHub token provided")
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
            # Get all repositories for the authenticated user
            repos_response = requests.get(f"{self.base_url}/user/repos", headers=self.headers)
            repos_response.raise_for_status()
            repos = repos_response.json()

            total_deployments = 0
            for repo in repos:
                # Get deployments for each repository
                deployments_url = f"{self.base_url}/repos/{repo['full_name']}/deployments"
                deployments_response = requests.get(
                    deployments_url,
                    headers=self.headers,
                    params={
                        'since': start_date.isoformat(),
                        'until': end_date.isoformat()
                    }
                )
                if deployments_response.status_code == 200:
                    total_deployments += len(deployments_response.json())

            days = (end_date - start_date).days
            frequency = total_deployments / days if days > 0 else 0
            return {"value": round(frequency, 2), "unit": "per day"}
        except Exception as e:
            logger.error(f"Error calculating deployment frequency: {str(e)}")
            return {"value": 0, "unit": "per day"}

    def _get_lead_time(self, start_date, end_date):
        try:
            # Get merged pull requests
            pulls_url = f"{self.base_url}/search/issues"
            query = f"type:pr is:merged merged:{start_date.isoformat()}..{end_date.isoformat()}"
            pulls_response = requests.get(
                pulls_url,
                headers=self.headers,
                params={'q': query}
            )
            pulls_response.raise_for_status()
            pulls_data = pulls_response.json()

            if pulls_data['total_count'] == 0:
                return {"value": 0, "unit": "days"}

            total_lead_time = 0
            for pr in pulls_data['items']:
                created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                merged_at = datetime.strptime(pr['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                lead_time = (merged_at - created_at).total_seconds() / 86400  # Convert to days
                total_lead_time += lead_time

            average_lead_time = total_lead_time / pulls_data['total_count']
            return {"value": round(average_lead_time, 2), "unit": "days"}
        except Exception as e:
            logger.error(f"Error calculating lead time: {str(e)}")
            return {"value": 0, "unit": "days"}

    def _get_change_failure_rate(self, start_date, end_date):
        try:
            # Get all deployments and their statuses
            repos_response = requests.get(f"{self.base_url}/user/repos", headers=self.headers)
            repos_response.raise_for_status()
            repos = repos_response.json()

            total_deployments = 0
            failed_deployments = 0

            for repo in repos:
                deployments_url = f"{self.base_url}/repos/{repo['full_name']}/deployments"
                deployments_response = requests.get(
                    deployments_url,
                    headers=self.headers,
                    params={
                        'since': start_date.isoformat(),
                        'until': end_date.isoformat()
                    }
                )
                if deployments_response.status_code == 200:
                    deployments = deployments_response.json()
                    total_deployments += len(deployments)

                    for deployment in deployments:
                        status_url = deployment['statuses_url']
                        status_response = requests.get(status_url, headers=self.headers)
                        if status_response.status_code == 200:
                            statuses = status_response.json()
                            if any(s['state'] == 'failure' for s in statuses):
                                failed_deployments += 1

            failure_rate = (failed_deployments / total_deployments * 100) if total_deployments > 0 else 0
            return {"value": round(failure_rate, 2), "unit": "percent"}
        except Exception as e:
            logger.error(f"Error calculating change failure rate: {str(e)}")
            return {"value": 0, "unit": "percent"}

    def _get_time_to_restore(self, start_date, end_date):
        try:
            # Get issues labeled as incidents/failures that were closed in the time period
            issues_url = f"{self.base_url}/search/issues"
            query = f"label:incident closed:{start_date.isoformat()}..{end_date.isoformat()}"
            issues_response = requests.get(
                issues_url,
                headers=self.headers,
                params={'q': query}
            )
            issues_response.raise_for_status()
            issues_data = issues_response.json()

            if issues_data['total_count'] == 0:
                return {"value": 0, "unit": "hours"}

            total_restore_time = 0
            for issue in issues_data['items']:
                created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                closed_at = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                restore_time = (closed_at - created_at).total_seconds() / 3600  # Convert to hours
                total_restore_time += restore_time

            average_restore_time = total_restore_time / issues_data['total_count']
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