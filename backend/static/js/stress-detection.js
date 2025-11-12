// Stress Detection JavaScript

let video;
let canvas;
let ctx;
let stream;
let isDetecting = false;

document.addEventListener('DOMContentLoaded', function() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    ctx = canvas.getContext('2d');
    
    const startBtn = document.getElementById('startBtn');
    const captureBtn = document.getElementById('captureBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    startBtn.addEventListener('click', startCamera);
    captureBtn.addEventListener('click', captureAndAnalyze);
    stopBtn.addEventListener('click', stopCamera);
    
    // Add animations
    document.querySelector('.detection-container').classList.add('fade-in');
});

async function startCamera() {
    try {
        const constraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        };
        
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        
        // Update button states
        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('captureBtn').style.display = 'inline-block';
        document.getElementById('stopBtn').style.display = 'inline-block';
        
        // Update results
        updateResults('📹 Camera is ready! Position your face in the guide and click "Analyze Stress"');
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        updateResults('❌ Unable to access camera. Please ensure you have granted camera permissions.', 'error');
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
    
    // Update button states
    document.getElementById('startBtn').style.display = 'inline-block';
    document.getElementById('captureBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'none';
    
    // Reset results
    updateResults('📱 Start the camera and click "Analyze Stress" to begin detection');
    isDetecting = false;
}

async function captureAndAnalyze() {
    if (isDetecting) return;
    
    isDetecting = true;
    const captureBtn = document.getElementById('captureBtn');
    const originalText = captureBtn.textContent;
    
    captureBtn.textContent = 'Analyzing...';
    captureBtn.disabled = true;
    
    updateResults('🧠 Analyzing facial expressions for stress indicators...');
    
    try {
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw video frame to canvas
        ctx.drawImage(video, 0, 0);
        
        // Convert canvas to base64
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        // Send to backend for analysis
        const response = await fetch('/api/detect-stress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayStressResult(data.stress_level, data.message);
        } else {
            updateResults(`❌ ${data.message || 'Analysis failed. Please try again.'}`, 'error');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        updateResults('❌ Connection error during analysis. Please check your internet connection.', 'error');
    } finally {
        captureBtn.textContent = originalText;
        captureBtn.disabled = false;
        isDetecting = false;
    }
}

function displayStressResult(stressLevel, message) {
    const stressCategory = getStressCategory(stressLevel);
    const color = getStressColor(stressLevel);
    
    const resultHTML = `
        <div class="stress-result">
            <div class="stress-meter stress-level-${stressCategory}" style="background: ${color}">
                <div class="stress-percentage">${stressLevel}%</div>
            </div>
            <div class="stress-message">
                <h4>Stress Level: ${getStressLabel(stressLevel)}</h4>
                <p>${message}</p>
            </div>
            <div class="result-actions">
                <button class="btn btn-primary" onclick="captureAndAnalyze()" ${isDetecting ? 'disabled' : ''}>
                    Analyze Again
                </button>
                <button class="btn btn-secondary" onclick="viewHistory()">
                    View History
                </button>
            </div>
            <div class="recommendations">
                ${getRecommendations(stressLevel)}
            </div>
        </div>
    `;
    
    document.getElementById('results').innerHTML = resultHTML;
    
    // Add animation
    document.querySelector('.stress-result').classList.add('fade-in');
    
    // Add pulse animation to high stress levels
    if (stressLevel > 70) {
        document.querySelector('.stress-meter').classList.add('pulse');
    }
}

function getStressCategory(level) {
    if (level < 30) return 0;      // Low
    else if (level < 50) return 1; // Mild
    else if (level < 70) return 2; // Moderate
    else return 3;                 // High
}

function getStressColor(level) {
    if (level < 30) return 'linear-gradient(135deg, #28a745, #20c997)';
    else if (level < 50) return 'linear-gradient(135deg, #ffc107, #fd7e14)';
    else if (level < 70) return 'linear-gradient(135deg, #fd7e14, #dc3545)';
    else return 'linear-gradient(135deg, #dc3545, #6f42c1)';
}

function getStressLabel(level) {
    if (level < 30) return 'Low Stress 😊';
    else if (level < 50) return 'Mild Stress 😐';
    else if (level < 70) return 'Moderate Stress 😰';
    else return 'High Stress 😟';
}

function getRecommendations(level) {
    const recommendations = {
        low: [
            '🎉 Great job managing your stress!',
            '✨ Keep up your current routine',
            '🌱 Consider sharing your strategies with others',
            '📚 Focus on your studies with confidence'
        ],
        mild: [
            '🫁 Practice deep breathing exercises',
            '⏰ Take regular 5-minute breaks',
            '💧 Stay hydrated throughout the day',
            '🎵 Listen to calming music while studying'
        ],
        moderate: [
            '🧘 Try meditation or mindfulness exercises',
            '🚶 Take a short walk to clear your mind',
            '👥 Talk to friends, family, or counselors',
            '📝 Break down tasks into smaller, manageable steps'
        ],
        high: [
            '🆘 Consider speaking with a counselor or therapist',
            '🛑 Take immediate breaks from stressful activities',
            '❤️ Practice self-care and prioritize your well-being',
            '📞 Reach out to mental health resources at your school'
        ]
    };
    
    let category;
    if (level < 30) category = 'low';
    else if (level < 50) category = 'mild';
    else if (level < 70) category = 'moderate';
    else category = 'high';
    
    return `
        <div class="recommendations-section">
            <h4>Recommendations:</h4>
            <ul class="recommendations-list">
                ${recommendations[category].map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
    `;
}

function updateResults(message, type = 'info') {
    const resultsDiv = document.getElementById('results');
    const className = type === 'error' ? 'error-message' : 'info-message';
    
    resultsDiv.innerHTML = `
        <div class="${className}">
            <div class="message-content">
                ${message}
            </div>
        </div>
    `;
}

function viewHistory() {
    window.location.href = '/dashboard';
}

// Add CSS for stress detection specific styles
const detectionStyles = `
    <style>
        .stress-result {
            text-align: center;
            padding: 1rem;
        }
        
        .stress-meter {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 1rem auto;
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            position: relative;
            overflow: hidden;
        }
        
        .stress-percentage {
            position: relative;
            z-index: 2;
        }
        
        .stress-message {
            margin: 1.5rem 0;
        }
        
        .stress-message h4 {
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 1.3rem;
        }
        
        .stress-message p {
            color: #666;
            font-size: 1.1rem;
            margin: 0;
        }
        
        .result-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin: 1.5rem 0;
            flex-wrap: wrap;
        }
        
        .recommendations-section {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            text-align: left;
        }
        
        .recommendations-section h4 {
            color: #333;
            margin-bottom: 1rem;
            text-align: center;
            font-size: 1.2rem;
        }
        
        .recommendations-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .recommendations-list li {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .recommendations-list li:hover {
            transform: translateX(5px);
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }
        
        .info-message,
        .error-message {
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
        }
        
        .info-message {
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
            color: #333;
            border: 2px solid #667eea;
        }
        
        .error-message {
            background: linear-gradient(135deg, #ffebee, #fce4ec);
            color: #721c24;
            border: 2px solid #dc3545;
        }
        
        .message-content {
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        @media (max-width: 600px) {
            .result-actions {
                flex-direction: column;
                align-items: center;
            }
            
            .result-actions .btn {
                width: 100%;
                max-width: 200px;
            }
        }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', detectionStyles);

// Error handling for camera access
window.addEventListener('error', function(e) {
    if (e.message.includes('camera') || e.message.includes('getUserMedia')) {
        updateResults('❌ Camera access error. Please refresh the page and allow camera permissions.', 'error');
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden && stream) {
        // Optionally pause or handle when page is not visible
    }
});