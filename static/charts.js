document.addEventListener('DOMContentLoaded', () => {
    (async () => {
        try {
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js not loaded — skipping charts init');
                return;
            }

            if (Chart.register && Chart.registerables) Chart.register(...Chart.registerables);

            const canvas = document.getElementById('dailyVolumeChart');
            if (!canvas) {
                console.warn('Canvas #dailyVolumeChart not found — skipping daily volume chart');
            } else {
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
                        console.warn('Failed to fetch /daily_volume, using sample data', res.status);
                    }
                } catch (e) {
                    console.warn('Error fetching /daily_volume, using sample data', e);
                }

                const config = {
                    type: 'line',
                    data: { labels, datasets: [{ label: 'Daily Trade Volume', data: volumes, borderColor: 'rgba(75,192,192,1)', backgroundColor: 'rgba(75,192,192,0.2)', fill: true, tension: 0.3 }] },
                    options: { responsive: true, maintainAspectRatio: true, aspectRatio: 2, scales: { x: { title: { display: true, text: 'Date' } }, y: { title: { display: true, text: 'Quantity Sold' }, beginAtZero: true } } }
                };

                if (canvas._chartInstance) canvas._chartInstance.destroy();
                canvas._chartInstance = new Chart(ctx, config);
                console.log('Daily volume chart initialized');
            }
        } catch (err) {
            console.error('charts.js init error:', err);
        }
    })();
});

// Item price stats table renderer
document.addEventListener("DOMContentLoaded", async () => {
    const table = document.getElementById("item-stats-table");
    if (!table) return;

    const tbody = table.querySelector("tbody");
    tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;opacity:0.7;">Loading...</td></tr>`;

    try {
        const res = await fetch("/item_price_stats");
        if (!res.ok) throw new Error("Failed to fetch item stats: " + res.status);
        const data = await res.json();

        if (!Array.isArray(data) || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;opacity:0.7;">No data</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        const nf = new Intl.NumberFormat(undefined, {maximumFractionDigits:2, minimumFractionDigits:2});
        data.forEach(row => {
            const item = row["_id"] || row.itemName || "Unknown";
            const highest = row.highestPrice ?? row.highest ?? null;
            const lowest = row.lowestPrice ?? row.lowest ?? null;
            const avg = row.averagePrice ?? row.avg ?? null;
            const tx = row.totalTransactions ?? row.tx ?? 0;

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${item}</td>
                <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${highest !== null ? nf.format(Number(highest)) : "-"}</td>
                <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${lowest !== null ? nf.format(Number(lowest)) : "-"}</td>
                <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${avg !== null ? nf.format(Number(avg)) : "-"}</td>
                <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${tx}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="padding:12px; color:salmon;">Error loading data</td></tr>`;
        console.error("item stats error:", err);
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    // Register Chart.js if present
    if (typeof Chart !== 'undefined' && Chart.register && Chart.registerables) {
        Chart.register(...Chart.registerables);
    }

    // Daily volume chart
    try {
        const canvas = document.getElementById('dailyVolumeChart');
        if (canvas && typeof fetch === 'function' && typeof Chart !== 'undefined') {
            const res = await fetch('/daily_volume');
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data) && data.length) {
                    const labels = data.map(d => d.date);
                    const volumes = data.map(d => d.volume);
                    const ctx = canvas.getContext('2d');
                    if (canvas._chartInstance) canvas._chartInstance.destroy();
                    canvas._chartInstance = new Chart(ctx, {
                        type: 'line',
                        data: { labels, datasets: [{ label: 'Daily Trade Volume', data: volumes, borderColor: 'rgba(75,192,192,1)', backgroundColor: 'rgba(75,192,192,0.2)', fill: true, tension: 0.3 }] },
                        options: { responsive: true, maintainAspectRatio: true, aspectRatio: 2, scales: { x: { title: { display: true, text: 'Date' } }, y: { title: { display: true, text: 'Quantity Sold' }, beginAtZero: true } } }
                    });
                }
            } else {
                console.warn('/daily_volume returned', res.status);
            }
        }
    } catch (err) {
        console.error('daily volume init error:', err);
    }

    // Item price stats table renderer
    try {
        const table = document.getElementById('item-stats-table');
        if (table && typeof fetch === 'function') {
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;opacity:0.7;">Loading...</td></tr>`;

            const res = await fetch('/item_price_stats');
            if (!res.ok) {
                tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;color:salmon;">Server error: ${res.status}</td></tr>`;
            } else {
                const data = await res.json();
                if (!Array.isArray(data) || data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;opacity:0.7;">No data</td></tr>`;
                } else {
                    tbody.innerHTML = '';
                    const nf = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
                    data.forEach(row => {
                        const item = row._id ?? row.itemName ?? 'Unknown';
                        const highest = row.highestPrice ?? row.highest ?? null;
                        const lowest = row.lowestPrice ?? row.lowest ?? null;
                        const avg = row.averagePrice ?? row.avg ?? null;
                        const tx = row.totalTransactions ?? row.tx ?? 0;

                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${item}</td>
                            <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${highest !== null ? nf.format(Number(highest)) : '-'}</td>
                            <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${lowest !== null ? nf.format(Number(lowest)) : '-'}</td>
                            <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${avg !== null ? nf.format(Number(avg)) : '-'}</td>
                            <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.04)">${tx}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            }
        }
    } catch (err) {
        console.error('item stats init error:', err);
    }

    // Simple client-side sorting for item-stats table
    try {
        const table = document.getElementById('item-stats-table');
        if (table) {
            const headers = Array.from(table.querySelectorAll('th'));
            const tbody = table.querySelector('tbody');
            headers.forEach((header, index) => {
                let ascending = true;
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    rows.sort((a, b) => {
                        const aText = a.children[index].innerText.trim();
                        const bText = b.children[index].innerText.trim();
                        const aNum = parseFloat(aText.replace(/[^0-9.-]+/g, ''));
                        const bNum = parseFloat(bText.replace(/[^0-9.-]+/g, ''));
                        if (!isNaN(aNum) && !isNaN(bNum)) return ascending ? aNum - bNum : bNum - aNum;
                        return ascending ? aText.localeCompare(bText) : bText.localeCompare(aText);
                    });
                    rows.forEach(r => tbody.appendChild(r));
                    ascending = !ascending;
                });
            });
        }
    } catch (err) {
        console.error('table sort init error:', err);
    }
});
