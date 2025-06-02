document.addEventListener('DOMContentLoaded', function () {
  const welcomeMessage = document.getElementById('welcome-message');
  if (welcomeMessage) {
    setTimeout(() => {
      welcomeMessage.style.transition = "opacity 1s ease-out";
      welcomeMessage.style.opacity = "0";
      setTimeout(() => welcomeMessage.remove(), 1000);
    }, 10000);
  }

  const chartElement = document.getElementById('weatherChart');
  if (chartElement) {
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: window.weatherLabels || [],
        datasets: [{
          label: 'Temperature (°C)',
          data: window.weatherData || [],
          fill: false,
          borderColor: 'blue',
          tension: 0.1
        }]
      }
    });
  }
});
