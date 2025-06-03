document.addEventListener('DOMContentLoaded', function () {
    // Welcome message handling - only show after actual login
    const welcomeMessage = document.getElementById('welcome-message');
    if (welcomeMessage) {
        // Welcome message will be handled by inline script in template
        // This ensures it only shows when show_welcome is true from server
    }

    // Chart handling
    const chartElement = document.getElementById('weatherChart');
    if (chartElement && window.weatherByLocation) {
        initializeChart();
    }

    // Live data auto-refresh
    startLiveDataRefresh();

    // Filter form enhancements
    enhanceFilterForm();
});

function initializeChart() {
    const ctx = document.getElementById('weatherChart').getContext('2d');
    const weatherByLocation = window.weatherByLocation || {};

    const datasets = Object.entries(weatherByLocation).map(([location, data], index) => {
        const colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7',
            '#fd79a8', '#a29bfe', '#6c5ce7', '#fd63a8', '#fab1a0'
        ];

        // Create data points for Chart.js
        const chartData = data.labels.map((label, i) => ({
            x: label,
            y: data.data[i]
        }));

        return {
            label: location + ' (Temperature)',
            data: chartData,
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length] + '33',
            tension: 0.4,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 6
        };
    });

    if (datasets.length === 0) {
        // Hide chart if no data
        document.getElementById('weatherChart').style.display = 'none';
        return;
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    type: 'category',
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Temperature Over Time by Location',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Time: ' + context[0].label;
                        },
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '°C';
                        }
                    }
                }
            }
        }
    });
}

function startLiveDataRefresh() {
    // Auto-refresh live data every 30 seconds
    setInterval(function() {
        fetch('/api/live-data')
            .then(response => response.json())
            .then(data => {
                updateLiveDataDisplay(data);
            })
            .catch(error => {
                console.log('Error fetching live data:', error);
            });
    }, 30000);
}

function updateLiveDataDisplay(liveData) {
    // Find the live data table
    const liveDataSection = document.querySelector('.data-section');
    if (!liveDataSection) return;

    const table = liveDataSection.querySelector('.csv-preview');
    const noDataMessage = liveDataSection.querySelector('.no-data-message');

    if (liveData && liveData.length > 0) {
        if (noDataMessage) {
            noDataMessage.style.display = 'none';
        }

        if (table) {
            // Update table with latest data (last 10 entries)
            const tbody = table.querySelector('tbody') || table;
            const rows = tbody.querySelectorAll('tr:not(:first-child)');

            // Remove old data rows
            rows.forEach(row => row.remove());

            // Add new data rows
            const latestData = liveData.slice(-10);
            latestData.forEach(data => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${data.timestamp}</td>
                    <td>${parseFloat(data.temperature).toFixed(1)}</td>
                    <td>${parseFloat(data.humidity).toFixed(1)}</td>
                    <td>${parseFloat(data.air_pressure).toFixed(1)}</td>
                    <td>${data.location}</td>
                `;
                tbody.appendChild(row);
            });
        }
    } else {
        if (table) {
            table.style.display = 'none';
        }
        if (noDataMessage) {
            noDataMessage.style.display = 'block';
        }
    }
}

function enhanceFilterForm() {
    // Add form validation and UX improvements
    const filterForm = document.querySelector('.filter-section form');
    if (!filterForm) return;

    // Add input validation for number fields
    const numberInputs = filterForm.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (isNaN(value)) return;

            // Validate temperature ranges
            if (this.name.includes('temp')) {
                if (value < -50 || value > 60) {
                    this.setCustomValidity('Temperature should be between -50°C and 60°C');
                } else {
                    this.setCustomValidity('');
                }
            }

            // Validate humidity ranges
            if (this.name.includes('humidity')) {
                if (value < 0 || value > 100) {
                    this.setCustomValidity('Humidity should be between 0% and 100%');
                } else {
                    this.setCustomValidity('');
                }
            }

            // Validate pressure ranges
            if (this.name.includes('pressure')) {
                if (value < 800 || value > 1200) {
                    this.setCustomValidity('Pressure should be between 800 hPa and 1200 hPa');
                } else {
                    this.setCustomValidity('');
                }
            }
        });
    });

    // Add date validation
    const dateFromInput = filterForm.querySelector('input[name="date_from"]');
    const dateToInput = filterForm.querySelector('input[name="date_to"]');

    if (dateFromInput && dateToInput) {
        function validateDates() {
            const dateFrom = new Date(dateFromInput.value);
            const dateTo = new Date(dateToInput.value);

            if (dateFromInput.value && dateToInput.value) {
                if (dateFrom > dateTo) {
                    dateToInput.setCustomValidity('End date must be after start date');
                } else {
                    dateToInput.setCustomValidity('');
                }
            }
        }

        dateFromInput.addEventListener('change', validateDates);
        dateToInput.addEventListener('change', validateDates);
    }

    // Add range validation for min/max pairs
    const rangeGroups = [
        ['temp_min', 'temp_max'],
        ['humidity_min', 'humidity_max'],
        ['pressure_min', 'pressure_max']
    ];

    rangeGroups.forEach(([minName, maxName]) => {
        const minInput = filterForm.querySelector(`input[name="${minName}"]`);
        const maxInput = filterForm.querySelector(`input[name="${maxName}"]`);

        if (minInput && maxInput) {
            function validateRange() {
                const minVal = parseFloat(minInput.value);
                const maxVal = parseFloat(maxInput.value);

                if (!isNaN(minVal) && !isNaN(maxVal)) {
                    if (minVal > maxVal) {
                        maxInput.setCustomValidity('Maximum value must be greater than minimum value');
                    } else {
                        maxInput.setCustomValidity('');
                    }
                }
            }

            minInput.addEventListener('input', validateRange);
            maxInput.addEventListener('input', validateRange);
        }
    });
}

// Utility function to format timestamps
function formatTimestamp(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('de-DE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        return timestamp;
    }
}

// Export functions for potential external use
window.WeatherStationApp = {
    updateLiveDataDisplay,
    formatTimestamp,
    initializeChart
};