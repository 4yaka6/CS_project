document.addEventListener('DOMContentLoaded', () => {
    const bestTimeDisplay = document.getElementById('best-time');
    const recordsList = document.getElementById('records-list');
    let scores = JSON.parse(localStorage.getItem('numberClickScores') || []);
    
    // Sort scores by time (ascending)
    scores.sort((a, b) => a.time - b.time);
    
    // Display best time
    if (scores.length > 0) {
        const bestScore = scores[0];
        bestTimeDisplay.textContent = formatTime(bestScore.time);
    }
    
    // Display all records
    scores.forEach(score => {
        const recordItem = document.createElement('div');
        recordItem.className = 'record-item';
        
        const date = new Date(score.date);
        const dateStr = date.toLocaleString();
        
        recordItem.innerHTML = `
            <span>${dateStr}</span>
            <span>${formatTime(score.time)}</span>
        `;
        
        recordsList.appendChild(recordItem);
    });
    
    // Create chart with last 10 scores
    createTimeChart(scores.slice(-10).reverse());
    
    function formatTime(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            return `${minutes}m ${remainingSeconds}s`;
        } else {
            return `${seconds}s`;
        }
    }
    
    function createTimeChart(recentScores) {
        const ctx = document.getElementById('time-chart').getContext('2d');
        
        const labels = recentScores.map((score, index) => {
            const date = new Date(score.date);
            return date.toLocaleDateString();
        });
        
        const data = recentScores.map(score => Math.floor(score.time / 1000));
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Completion Time (seconds)',
                    data: data,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Time (seconds)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }
});