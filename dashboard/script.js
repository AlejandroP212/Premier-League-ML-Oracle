let dashboardData = null;

async function init() {
    try {
        const response = await fetch('data/data.json');
        dashboardData = await response.json();
        
        setupSelectors();
        renderCharts();
        setupEventListeners();
        
        // Initial animation
        document.querySelectorAll('.card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function setupSelectors() {
    const hSelect = document.getElementById('home-team-select');
    const aSelect = document.getElementById('away-team-select');
    
    dashboardData.teams.sort().forEach(team => {
        hSelect.add(new Option(team, team));
        aSelect.add(new Option(team, team));
    });
    
    hSelect.value = 'Liverpool';
    aSelect.value = 'Man City';
}

function renderCharts() {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    // 1. Importance Chart
    const importanceCtx = document.getElementById('importanceChart').getContext('2d');
    const impData = dashboardData.metrics.regression_importance;
    
    new Chart(importanceCtx, {
        type: 'bar',
        data: {
            labels: impData.map(d => d.Feature.replace(/_/g, ' ')),
            datasets: [{
                label: 'Peso en el Modelo (Coef)',
                data: impData.map(d => d.Coef_Home),
                backgroundColor: 'rgba(56, 189, 248, 0.6)',
                borderColor: '#38bdf8',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });

    // 2. xG Sample Chart
    const xgCtx = document.getElementById('xgChart').getContext('2d');
    const shots = dashboardData.shots_sample;
    
    new Chart(xgCtx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'No Gol',
                    data: shots.filter(s => !s.goal).map(s => ({ x: s.dist, y: s.angle })),
                    backgroundColor: 'rgba(148, 163, 184, 0.2)',
                    pointRadius: 4
                },
                {
                    label: 'Gol',
                    data: shots.filter(s => s.goal).map(s => ({ x: s.dist, y: s.angle })),
                    backgroundColor: '#4ade80',
                    pointRadius: 6,
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Distancia (unidades)' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { title: { display: true, text: 'Ángulo (rad)' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function setupEventListeners() {
    document.getElementById('simulate-btn').addEventListener('click', simulateMatch);
}

function simulateMatch() {
    const hTeam = document.getElementById('home-team-select').value;
    const aTeam = document.getElementById('away-team-select').value;
    
    if (hTeam === aTeam) {
        alert('Selecciona dos equipos diferentes');
        return;
    }
    
    const hStats = dashboardData.team_stats[hTeam];
    const aStats = dashboardData.team_stats[aTeam];
    
    // Feature vector construction (matches training logic)
    const features = [
        hStats.goals, aStats.goals,
        hStats.shots, aStats.shots,
        hStats.sot, aStats.sot,
        hStats.goals - aStats.goals,
        hStats.shots - aStats.shots,
        hStats.sot - aStats.sot,
        2.0, 3.4, 3.5 // Baseline odds
    ];
    
    // Regression Goals Prediction
    const reg = dashboardData.models.regression;
    let hGoals = reg.home_intercept;
    let aGoals = reg.away_intercept;
    
    for (let i = 0; i < features.length; i++) {
        hGoals += features[i] * reg.home_coef[i];
        aGoals += features[i] * reg.away_coef[i];
    }
    
    // Classification Probabilities
    const clf = dashboardData.models.classification;
    const scores = [];
    for (let c = 0; c < clf.classes.length; c++) {
        let score = clf.intercept[c];
        for (let i = 0; i < features.length; i++) {
            score += features[i] * clf.coef[c][i];
        }
        scores.push(Math.exp(score));
    }
    const sum = scores.reduce((a, b) => a + b, 0);
    const rawProbs = scores.map(s => (s / sum) * 100);
    
    // Map probabilities back to H, D, A (classes are usually alphabetical: A, D, H)
    const probs = {};
    clf.classes.forEach((className, i) => {
        probs[className] = rawProbs[i];
    });

    // UI Updates with animation
    const resultsDiv = document.getElementById('results');
    resultsDiv.classList.remove('hidden');
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Animate numbers
    animateNumber('res-home-goals', Math.max(0, hGoals), 1);
    animateNumber('res-away-goals', Math.max(0, aGoals), 1);
    
    animateNumber('prob-h-text', probs.H, 0, '%');
    animateNumber('prob-d-text', probs.D, 0, '%');
    animateNumber('prob-a-text', probs.A, 0, '%');

    // Update bars
    document.getElementById('prob-h-bar').style.width = `${probs.H}%`;
    document.getElementById('prob-d-bar').style.width = `${probs.D}%`;
    document.getElementById('prob-a-bar').style.width = `${probs.A}%`;
    
    document.getElementById('res-home-name').innerText = hTeam.toUpperCase();
    document.getElementById('res-away-name').innerText = aTeam.toUpperCase();
}

function animateNumber(id, endValue, decimals = 0, suffix = '') {
    const obj = document.getElementById(id);
    let startValue = 0;
    const duration = 1000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = progress * (endValue - startValue) + startValue;
        obj.innerText = current.toFixed(decimals) + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

init();
