document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('grid');
    const currentNumDisplay = document.getElementById('current-num');
    const timerDisplay = document.getElementById('time');
    const restartBtn = document.getElementById('restart-btn');
    const recordBtn = document.getElementById('record-btn');
    const resultModal = document.getElementById('result-modal');
    const finalTimeDisplay = document.getElementById('final-time');
    const closeModal = document.getElementById('close-modal');

    let currentNumber = 0;
    let startTime = null;
    let timerInterval = null;
    let gameCompleted = false;

    // Initialize the game
    function initGame() {
        grid.innerHTML = '';
        currentNumber = 0;
        currentNumDisplay.textContent = '00';
        gameCompleted = false;
        
        // Generate random numbers for the grid
        const numbers = [];
        for (let i = 0; i < 100; i++) {
            numbers.push(i.toString().padStart(2, '0'));
        }
        
        // Shuffle the numbers
        for (let i = numbers.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
        }
        
        // Create grid cells
        numbers.forEach(num => {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.textContent = num;
            cell.dataset.number = num;
            cell.addEventListener('click', handleCellClick);
            grid.appendChild(cell);
        });
        
        // Start timer
        startTimer();
    }
    
    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        startTime = Date.now();
        timerInterval = setInterval(updateTimer, 100);
    }
    
    function updateTimer() {
        const elapsed = Date.now() - startTime;
        const seconds = Math.floor(elapsed / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            timerDisplay.textContent = `${minutes}m ${remainingSeconds}s`;
        } else {
            timerDisplay.textContent = `${seconds}s`;
        }
    }
    
    function handleCellClick(e) {
        if (gameCompleted) return;
        
        const cell = e.target;
        const cellNumber = cell.dataset.number;
        const expectedNumber = currentNumber.toString().padStart(2, '0');
        
        if (cellNumber === expectedNumber) {
            cell.classList.add('clicked');
            currentNumber++;
            currentNumDisplay.textContent = expectedNumber;
            
            // Check if game is completed
            if (currentNumber === 100) {
                gameCompleted = true;
                clearInterval(timerInterval);
                const elapsed = Date.now() - startTime;
                showResult(elapsed);
                saveScore(elapsed);
            }
        }
    }
    
    function showResult(elapsed) {
        const seconds = Math.floor(elapsed / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        let timeString;
        if (minutes > 0) {
            timeString = `${minutes}m ${remainingSeconds}s`;
        } else {
            timeString = `${seconds}s`;
        }
        
        finalTimeDisplay.textContent = timeString;
        resultModal.style.display = 'flex';
    }
    
    function saveScore(elapsed) {
        let scores = JSON.parse(localStorage.getItem('numberClickScores') || '[]');
        const now = new Date();
        
        scores.push({
            date: now.toISOString(),
            time: elapsed
        });
        
        // Keep only the last 100 records
        if (scores.length > 100) {
            scores = scores.slice(scores.length - 100);
        }
        
        localStorage.setItem('numberClickScores', JSON.stringify(scores));
    }
    
    // Event listeners
    restartBtn.addEventListener('click', initGame);
    recordBtn.addEventListener('click', () => {
        window.location.href = 'record.html';
    });
    closeModal.addEventListener('click', () => {
        resultModal.style.display = 'none';
    });
    
    // Start the game
    initGame();
});