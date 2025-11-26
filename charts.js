document.addEventListener('DOMContentLoaded', () => {
    (async () => {
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart.js not loaded');

            if (Chart.register && Chart.registerables) Chart.register(...Chart.registerables);

            const canvas = document.getElementById('dailyVolumeChart');
            if (!canvas) throw new Error('Canvas #dailyVolumeChart not found');
            const ctx = canvas.getContext('2d');

            // fetch data (falls back to sample data on failure)
            let labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
            let volumes = [12,19,7,14,9,11,6];
            try {
                const res = await fetch('/daily_volume');
                if (res.ok) {
                    const data = await res.json();
                    if (Array.isArray(data) && data.length) {
                        labels = data.map(d => d.date);
                        volumes = data.map(d => d.volume);
                    }
                } else {
                    console.warn('Failed to fetch /daily_volume, using sample data');
                }
            } catch (e) {
                console.warn('Error fetching /daily_volume, using sample data', e);
            }

            const config = {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Daily Trade Volume',
                        data: volumes,
                        borderColor: 'rgba(75,192,192,1)',
                        backgroundColor: 'rgba(75,192,192,0.2)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    // keep this true (or set a fixed aspectRatio) to avoid layout feedback loops
                    maintainAspectRatio: true,
                    aspectRatio: 2, // adjust to control chart height
                    scales: {
                        x: { title: { display: true, text: 'Date' } },
                        y: { title: { display: true, text: 'Quantity Sold' }, beginAtZero: true }
                    }
                }
            };

            // reuse/destroy any previous instance
            if (canvas._chartInstance) canvas._chartInstance.destroy();
            canvas._chartInstance = new Chart(ctx, config);
            console.log('Chart initialized');
        } catch (err) {
            console.error('charts.js init error:', err);
        }
    })();
});
