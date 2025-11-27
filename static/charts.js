document.addEventListener('DOMContentLoaded', async () => {
    // Register Chart.js if present
    if (typeof Chart !== 'undefined' && Chart.register && Chart.registerables) {
        Chart.register(...Chart.registerables);
    }

    // Daily Volume Chart
    try {
        const canvas = document.getElementById('dailyVolumeChart');
        if (canvas) {
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
                            maintainAspectRatio: true,
                            aspectRatio: 2,
                            scales: { 
                                x: { title: { display: true, text: 'Date' } },
                                y: { title: { display: true, text: 'Quantity Sold' }, beginAtZero: true }
                            }
                        }
                    });
                }
            }
        }
    } catch (err) {
        console.error('Daily volume chart error:', err);
    }

    // Item Price Stats Table
    try {
        const table = document.getElementById('item-stats-table');
        if (table) {
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;opacity:0.7;">Loading...</td></tr>`;
            const res = await fetch('/item_price_stats');
            if (!res.ok) {
                tbody.innerHTML = `<tr><td colspan="5" style="padding:12px;color:salmon;">Server error: ${res.status}</td></tr>`;
            } else {
                const data = await res.json();
                if (!Array.isArray(data) || !data.length) {
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
        console.error('Item stats table error:', err);
    }

    // Simple Table Sorting
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
        console.error('Table sorting error:', err);
    }

    // Demand Stability Chart
    try {
        const select = document.getElementById('stability-item-select');
        const canvas = document.getElementById('stabilityChart');
        if (!select || !canvas) return;

        // Populate items
        const resItems = await fetch('/item_price_stats');
        if (resItems.ok) {
            const items = await resItems.json();
            select.innerHTML = items.map(i => {
                const name = i._id ?? i.itemName ?? '';
                return `<option value="${encodeURIComponent(name)}">${name}</option>`;
            }).join('');
        } else {
            select.innerHTML = '<option value="">(no items)</option>';
            return;
        }

        // Fetch max for scaling
        const resMax = await fetch('/demand_stability_max');
        const maxStability = resMax.ok ? Number((await resMax.json()).max || 1) : 1;

        let stabilityChart = null;
        async function renderStability(item) {
            if (!item) return;
            try {
                const q = `?item=${encodeURIComponent(item)}`;
                const r = await fetch('/demand_stability' + q);
                if (!r.ok) throw new Error('failed to load stability');
                const payload = await r.json();
                const value = Number(payload.score || 0);

                // Min-max log scaling
                const scaled = Math.log(value + 1) / Math.log(maxStability + 1);

                const ctx = canvas.getContext('2d');
                if (stabilityChart) stabilityChart.destroy();
                stabilityChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: [payload.item || item],
                        datasets: [{
                            label: 'Demand Stability (normalized)',
                            data: [scaled],
                            backgroundColor: ['#FF5E00'],
                            borderColor: ['#FF5E00'],
                            borderWidth: 0.5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 2,
                        scales: {
                            x: { display: true },
                            y: {
                                min: 0,
                                max: 17,
                                title: { display: true, text: 'Normalized Score' }
                            }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            } catch (err) {
                console.error('Stability render error', err);
            }
        }

        // Initial render
        const first = select.options[0]?.value ? decodeURIComponent(select.options[0].value) : select.options[0]?.text;
        if (first) renderStability(first);

        select.addEventListener('change', () => {
            const v = select.value ? decodeURIComponent(select.value) : select.options[select.selectedIndex].text;
            renderStability(v);
        });
    } catch (err) {
        console.error('Stability chart init error:', err);
    }

    // Price Volatility Chart
    (async function initPriceVolatilityWidget() {
        const select = document.getElementById('price-volatility-select');
        const canvas = document.getElementById('priceVolatilityChart');
        if (!select || !canvas) return;

        try {
            const resItems = await fetch('/item_price_stats');
            const items = resItems.ok ? await resItems.json() : [];
            select.innerHTML = items.map(i => {
                const name = i._id ?? i.itemName ?? '';
                return `<option value="${encodeURIComponent(name)}">${name}</option>`;
            }).join('');
        } catch (e) {
            select.innerHTML = '<option value="">(no items)</option>';
            return;
        }

        const resMax = await fetch('/price_volatility_max');
        const maxPVI = resMax.ok ? Number((await resMax.json()).max || 1) : 1;

        let pvChart = null;
        async function renderPriceVol(item) {
            if (!item) return;
            try {
                const q = `?item=${encodeURIComponent(item)}`;
                const r = await fetch('/price_volatility' + q);
                if (!r.ok) throw new Error('failed to load PVI');
                const payload = await r.json();
                const value = payload.pvi == null ? 0 : Number(payload.pvi);

                const scaled = Math.log(value + 1) / Math.log(maxPVI + 1);

                const ctx = canvas.getContext('2d');
                if (pvChart) pvChart.destroy();
                pvChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: [payload.item || item],
                        datasets: [{
                            label: 'Price Volatility Index (normalized)',
                            data: [scaled],
                            backgroundColor: ['rgba(54,162,235,0.9)'],
                            borderColor: ['rgba(54,162,235,1)'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 2,
                        scales: {
                            x: { display: true },
                            y: {
                                min: 0,
                                max: 17,
                                title: { display: true, text: 'Normalized PVI' }
                            }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            } catch (err) {
                console.error('Price Volatility render error', err);
            }
        }

        // Initial render
        const first = select.options[0]?.value ? decodeURIComponent(select.options[0].value) : select.options[0]?.text;
        if (first) renderPriceVol(first);

        select.addEventListener('change', () => {
            const v = select.value ? decodeURIComponent(select.value) : select.options[select.selectedIndex].text;
            renderPriceVol(v);
        });
    })();
});
