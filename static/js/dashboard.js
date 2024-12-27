document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initializeGitHubMetricsChart();
    initializeJiraMetricsChart();
});

function initializeGitHubMetricsChart() {
    const ctx = document.getElementById('githubMetricsChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Deployment Frequency', 'Lead Time', 'Change Failure Rate', 'Time to Restore'],
            datasets: [{
                label: 'GitHub Metrics',
                data: window.githubMetrics || [],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function initializeJiraMetricsChart() {
    const ctx = document.getElementById('jiraMetricsChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'Ticket Completion Rate',
                data: window.jiraMetrics || [],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
