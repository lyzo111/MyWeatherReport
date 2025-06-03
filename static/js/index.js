document.addEventListener('DOMContentLoaded', function () {
    const welcomeMessage = document.getElementById('welcome-message');

    const shouldFadeOut = !sessionStorage.getItem("welcomeFadeOutStarted");

    if (welcomeMessage) {
        if (shouldFadeOut) {
            setTimeout(() => {
                welcomeMessage.style.transition = "opacity 1s ease-out";
                welcomeMessage.style.opacity = "0";
                setTimeout(() => {
                    welcomeMessage.style.display = "none";
                    sessionStorage.setItem("welcomeFadeOutStarted", "true");
                }, 1000);
            }, 5000);
        } else {
            welcomeMessage.style.display = "none";
        }
    }

    const chartElement = document.getElementById('weatherChart');
    if (!chartElement) return;

    const ctx = chartElement.getContext('2d');

    const weatherByLocation = window.weatherByLocation || {};
    const labelsSet = new Set();

    const datasets = Object.entries(weatherByLocation).map(([location, data], index) => {
        data.labels.forEach(label => labelsSet.add(label));
        return {
            label: location,
            data: data.data,
            borderColor: ['red', 'blue', 'green', 'orange', 'purple'][index % 5],
            tension: 0.1,
            fill: false
        };
    });

    const labels = Array.from(labelsSet).sort();

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        }
    });
});
