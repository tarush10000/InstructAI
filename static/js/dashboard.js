// Mock data - in a real app, this would come from an API/database
const dashboardData = {
    dailyHours: [3, 2.5, 4, 3.5, 5, 2, 1.5],
    quizPerformance: {
      correct: 75,
      incorrect: 10,
      notAttempted: 15
    },
    completionRate: {
      completed: 75,
      pending: 20,
      skipped: 5
    },
    streak: 19,
    leaderboard: [
      { position: 2, name: "Obi Wan", score: 7009 },
      { position: 3, name: "Darth Wader", score: 6968 },
      { position: 4, name: "Anakin", score: 6904 },
      { position: 5, name: "Yoda", score: 6787 }
    ]
  };
  
  // Initialize charts when DOM is loaded
  document.addEventListener('DOMContentLoaded', function() {
    // Set streak count
    document.getElementById('streakCount').innerHTML = `${dashboardData.streak} <span>days</span>`;
    
    // Populate leaderboard
    const leaderboardBody = document.querySelector('#leaderboardTable tbody');
    dashboardData.leaderboard.forEach(user => {
      const row = document.createElement('tr');
      if (user.name === "Darth Wader") row.classList.add('highlighted');
      row.innerHTML = `
        <td>${user.position}</td>
        <td>${user.name}</td>
        <td>${user.score}</td>
      `;
      leaderboardBody.appendChild(row);
    });
  
    // Daily Hours Chart (Line Chart)
    const hoursCtx = document.getElementById('hoursChart').getContext('2d');
    new Chart(hoursCtx, {
      type: 'line',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
          label: 'Hours Studied',
          data: dashboardData.dailyHours,
          borderColor: '#7987ff',
          backgroundColor: 'rgba(121, 135, 255, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.parsed.y} hours`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 6,
            ticks: {
              callback: function(value) {
                return value + 'h';
              }
            }
          }
        }
      }
    });
  
    // Quiz Performance Chart (Doughnut)
    const quizCtx = document.getElementById('quizChart').getContext('2d');
    new Chart(quizCtx, {
      type: 'doughnut',
      data: {
        labels: ['Correct', 'Incorrect', 'Not attempted'],
        datasets: [{
          data: [
            dashboardData.quizPerformance.correct,
            dashboardData.quizPerformance.incorrect,
            dashboardData.quizPerformance.notAttempted
          ],
          backgroundColor: [
            '#7987ff',
            '#ffa5cb',
            '#e697ff'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.label}: ${context.raw}%`;
              }
            }
          }
        }
      }
    });
  
    // Completion Rate Chart (Doughnut)
    const completionCtx = document.getElementById('completionChart').getContext('2d');
    new Chart(completionCtx, {
      type: 'doughnut',
      data: {
        labels: ['Completed', 'Pending', 'Skipped'],
        datasets: [{
          data: [
            dashboardData.completionRate.completed,
            dashboardData.completionRate.pending,
            dashboardData.completionRate.skipped
          ],
          backgroundColor: [
            '#7987ff',
            '#ffa5cb',
            '#e697ff'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.label}: ${context.raw}%`;
              }
            }
          }
        }
      }
    });
  });