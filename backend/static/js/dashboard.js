// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadRecentLogs();
    loadStressHistory();
    
    // Add animations
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});

async function loadRecentLogs() {
    const recentLogsContainer = document.getElementById('recentLogs');
    
    try {
        const response = await fetch('/api/stress-logs');
        const data = await response.json();
        
        if (data.success && data.logs && data.logs.length > 0) {
            const recentLogs = data.logs.slice(0, 3); // Show only 3 most recent
            
            recentLogsContainer.innerHTML = recentLogs.map(log => `
                <div class="log-entry">
                    <div class="log-info">
                        <h4>Stress Level: ${log.stress_level}%</h4>
                        <p>${formatDate(log.timestamp)}</p>
                    </div>
                    <div class="log-stress">
                        <span class="stress-badge ${getStressBadgeClass(log.stress_level)}">
                            ${getStressLabel(log.stress_level)}
                        </span>
                    </div>
                </div>
            `).join('');
        } else {
            recentLogsContainer.innerHTML = `
                <div class="no-results">
                    📊 No stress detection sessions yet.<br>
                    <a href="/stress-detection" class="btn btn-primary" style="margin-top: 1rem;">Start Your First Session</a>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recent logs:', error);
        recentLogsContainer.innerHTML = `
            <div class="no-results">
                ❌ Error loading recent activity
            </div>
        `;
    }
}

async function loadStressHistory() {
    const stressHistoryContainer = document.getElementById('stressHistory');
    
    try {
        const response = await fetch('/api/stress-logs');
        const data = await response.json();
        
        if (data.success && data.logs && data.logs.length > 0) {
            // Create a simple chart-like visualization
            const chartData = processStressData(data.logs);
            
            stressHistoryContainer.innerHTML = `
                <div class="stress-chart">
                    <div class="chart-header">
                        <h4>Your Stress Pattern (Last 10 Sessions)</h4>
                    </div>
                    <div class="chart-bars">
                        ${chartData.map((item, index) => `
                            <div class="chart-bar">
                                <div class="bar ${getStressBadgeClass(item.level)}" 
                                     style="height: ${item.level}%"
                                     title="${item.level}% - ${formatDate(item.date)}">
                                </div>
                                <div class="bar-label">${index + 1}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="chart-stats">
                        <div class="stat">
                            <strong>Average:</strong> ${calculateAverage(data.logs)}%
                        </div>
                        <div class="stat">
                            <strong>Trend:</strong> ${getTrend(chartData)}
                        </div>
                        <div class="stat">
                            <strong>Total Sessions:</strong> ${data.logs.length}
                        </div>
                    </div>
                </div>
                
                <div class="all-logs">
                    <h4>All Sessions</h4>
                    <div class="logs-container">
                        ${data.logs.map(log => `
                            <div class="log-entry">
                                <div class="log-info">
                                    <h4>Session: ${log.stress_level}% Stress</h4>
                                    <p>${formatDate(log.timestamp)}</p>
                                </div>
                                <div class="log-stress">
                                    <span class="stress-badge ${getStressBadgeClass(log.stress_level)}">
                                        ${getStressLabel(log.stress_level)}
                                    </span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            stressHistoryContainer.innerHTML = `
                <div class="no-results">
                    📈 No stress history available yet.<br>
                    Start using the stress detection feature to see your progress over time.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading stress history:', error);
        stressHistoryContainer.innerHTML = `
            <div class="no-results">
                ❌ Error loading stress history
            </div>
        `;
    }
}

function processStressData(logs) {
    // Get last 10 sessions for chart
    return logs.slice(0, 10).reverse().map(log => ({
        level: log.stress_level,
        date: log.timestamp
    }));
}

function calculateAverage(logs) {
    if (logs.length === 0) return 0;
    const sum = logs.reduce((acc, log) => acc + log.stress_level, 0);
    return Math.round(sum / logs.length);
}

function getTrend(chartData) {
    if (chartData.length < 2) return 'Insufficient data';
    
    const recent = chartData.slice(-3);
    const older = chartData.slice(0, -3);
    
    if (older.length === 0) return 'New user';
    
    const recentAvg = recent.reduce((acc, item) => acc + item.level, 0) / recent.length;
    const olderAvg = older.reduce((acc, item) => acc + item.level, 0) / older.length;
    
    const diff = recentAvg - olderAvg;
    
    if (Math.abs(diff) < 5) return 'Stable 📊';
    else if (diff > 0) return 'Increasing ⬆️';
    else return 'Decreasing ⬇️';
}

function getStressBadgeClass(level) {
    if (level < 30) return 'stress-level-0';
    else if (level < 50) return 'stress-level-1';
    else if (level < 70) return 'stress-level-2';
    else return 'stress-level-3';
}

function getStressLabel(level) {
    if (level < 30) return 'Low';
    else if (level < 50) return 'Mild';
    else if (level < 70) return 'Moderate';
    else return 'High';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Add CSS for chart visualization
const chartStyles = `
    <style>
        .stress-chart {
            margin-bottom: 2rem;
        }
        
        .chart-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        .chart-header h4 {
            color: #333;
            font-weight: 600;
        }
        
        .chart-bars {
            display: flex;
            align-items: end;
            justify-content: center;
            gap: 8px;
            height: 200px;
            margin-bottom: 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .chart-bar {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            max-width: 40px;
        }
        
        .bar {
            width: 100%;
            min-height: 10px;
            border-radius: 4px 4px 0 0;
            transition: all 0.3s ease;
            cursor: pointer;
            margin-bottom: 8px;
        }
        
        .bar:hover {
            opacity: 0.8;
            transform: scaleY(1.1);
        }
        
        .bar-label {
            font-size: 0.8rem;
            color: #666;
            font-weight: 500;
        }
        
        .chart-stats {
            display: flex;
            justify-content: space-around;
            gap: 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        
        .chart-stats .stat {
            text-align: center;
            flex: 1;
        }
        
        .chart-stats strong {
            display: block;
            color: #333;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }
        
        .all-logs h4 {
            color: #333;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        .logs-container {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 8px;
        }
        
        .logs-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .logs-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 6px;
        }
        
        .logs-container::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 6px;
        }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', chartStyles);