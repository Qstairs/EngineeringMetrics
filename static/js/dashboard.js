document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    initializePreferences();
    setupDragAndDrop();
});

let charts = {};

function initializeCharts() {
    charts.github = createChart('githubMetricsChart', window.githubMetrics, userPreferences.chart_type);
    charts.jira = createChart('jiraMetricsChart', window.jiraMetrics, userPreferences.chart_type);
}

function createChart(canvasId, data, type = 'bar') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const chartConfig = getChartConfig(data, type);
    return new Chart(ctx, chartConfig);
}

function getChartConfig(data, type) {
    const isGithub = Object.keys(data).includes('deployment_frequency');
    return {
        type: type,
        data: {
            labels: isGithub 
                ? ['Deployment Frequency', 'Lead Time', 'Change Failure Rate', 'Time to Restore']
                : ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: isGithub ? 'GitHub Metrics' : 'Jira Metrics',
                data: isGithub 
                    ? [data.deployment_frequency.value, data.lead_time.value, 
                       data.change_failure_rate.value, data.time_to_restore.value]
                    : data || [],
                backgroundColor: isGithub 
                    ? 'rgba(54, 162, 235, 0.2)'
                    : 'rgba(75, 192, 192, 0.2)',
                borderColor: isGithub 
                    ? 'rgba(54, 162, 235, 1)'
                    : 'rgba(75, 192, 192, 1)',
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
    };
}

function initializePreferences() {
    // Layout preference
    document.getElementById('layoutPreference').addEventListener('change', function(e) {
        const container = document.getElementById('metricsContainer');
        container.className = `row ${e.target.value === 'list' ? 'list-layout' : ''}`;
        savePreferences();
    });

    // Chart type preference
    document.getElementById('chartType').addEventListener('change', function(e) {
        updateChartType(e.target.value);
        savePreferences();
    });

    // Theme preference
    document.getElementById('themePreference').addEventListener('change', function(e) {
        document.body.className = e.target.value === 'dark' ? 'dark-theme' : '';
        savePreferences();
    });

    // Refresh interval
    document.getElementById('refreshInterval').addEventListener('change', function(e) {
        setupRefreshInterval(parseInt(e.target.value));
        savePreferences();
    });

    // Initial setup
    setupRefreshInterval(userPreferences.refresh_interval);
    if (userPreferences.theme === 'dark') {
        document.body.className = 'dark-theme';
    }
}

function setupDragAndDrop() {
    const container = document.getElementById('metricsContainer');
    new Sortable(container, {
        animation: 150,
        onEnd: function() {
            savePreferences();
        }
    });
}

function updateChartType(type) {
    Object.entries(charts).forEach(([key, chart]) => {
        const data = chart.data;
        chart.destroy();
        charts[key] = createChart(`${key}MetricsChart`, window[`${key}Metrics`], type);
    });
}

function setupRefreshInterval(interval) {
    if (window.refreshTimer) {
        clearInterval(window.refreshTimer);
    }
    window.refreshTimer = setInterval(refreshData, interval * 1000);
}

async function refreshData() {
    try {
        const response = await fetch('/api/metrics/refresh');
        const data = await response.json();
        window.githubMetrics = data.github_metrics;
        window.jiraMetrics = data.jira_metrics;
        updateChartType(document.getElementById('chartType').value);
    } catch (error) {
        console.error('Failed to refresh metrics:', error);
    }
}

async function savePreferences() {
    const preferences = {
        layout: document.getElementById('layoutPreference').value,
        chart_type: document.getElementById('chartType').value,
        theme: document.getElementById('themePreference').value,
        refresh_interval: parseInt(document.getElementById('refreshInterval').value),
        metrics_order: Array.from(document.querySelectorAll('.metrics-card-wrapper'))
            .map(el => el.dataset.metricType)
    };

    try {
        await fetch('/api/preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(preferences)
        });
    } catch (error) {
        console.error('Failed to save preferences:', error);
    }
}