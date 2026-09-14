let chartRevenueImp = null;
let chartCtrFill = null;

document.addEventListener("DOMContentLoaded", () => {
    checkStatus();
    loadDashboardData();
});

async function checkStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const badge = document.getElementById("mode-badge");
        const text = document.getElementById("mode-text");

        text.textContent = data.mode;
        if (data.mode.includes("Mock")) {
            badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-2";
        } else {
            badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-2";
        }
    } catch (err) {
        console.error("Gagal memeriksa status API:", err);
    }
}

async function loadDashboardData() {
    const days = document.getElementById("filter-days").value;
    const source = document.getElementById("filter-source").value;

    await Promise.all([
        fetchSummary(days, source),
        fetchTimeseries(days, source),
        fetchDailyDetails(days, source)
    ]);

    document.getElementById("last-updated-time").textContent = new Date().toLocaleTimeString("id-ID");
}

async function fetchSummary(days, source) {
    try {
        const res = await fetch(`/api/summary?days=${days}&source=${source}`);
        const data = await res.json();
        const s = data.summary;

        document.getElementById("card-revenue").textContent = `$${s.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
        document.getElementById("card-impressions").textContent = s.total_impressions.toLocaleString('id-ID');
        document.getElementById("card-fillrate").textContent = `${s.avg_fill_rate}%`;
        document.getElementById("card-ctr").textContent = `${s.avg_ctr}%`;
        document.getElementById("card-rpm").textContent = `$${s.avg_rpm.toFixed(2)}`;
    } catch (err) {
        console.error("Error fetching summary:", err);
    }
}

async function fetchTimeseries(days, source) {
    try {
        const res = await fetch(`/api/timeseries?days=${days}&source=${source}`);
        const data = await res.json();
        renderCharts(data);
    } catch (err) {
        console.error("Error fetching timeseries:", err);
    }
}

function renderCharts(data) {
    // Destroy previous charts if exist
    if (chartRevenueImp) chartRevenueImp.destroy();
    if (chartCtrFill) chartCtrFill.destroy();

    // Chart 1: Revenue & Impression
    const ctx1 = document.getElementById("chart-revenue-imp").getContext("2d");
    chartRevenueImp = new Chart(ctx1, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "Pendapatan ($)",
                    data: data.revenues,
                    borderColor: "#10b981", // Emerald 500
                    backgroundColor: "rgba(16, 185, 129, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: "y-rev"
                },
                {
                    label: "Impression",
                    data: data.impressions,
                    borderColor: "#3b82f6", // Blue 500
                    backgroundColor: "rgba(59, 130, 246, 0.05)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: "y-imp"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#94a3b8" } }
            },
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148, 163, 184, 0.1)" } },
                "y-rev": {
                    type: "linear",
                    position: "left",
                    ticks: { color: "#10b981", callback: v => "$" + v },
                    grid: { color: "rgba(148, 163, 184, 0.1)" }
                },
                "y-imp": {
                    type: "linear",
                    position: "right",
                    ticks: { color: "#3b82f6", callback: v => v.toLocaleString() },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });

    // Chart 2: Fill Rate & CTR
    const ctx2 = document.getElementById("chart-ctr-fill").getContext("2d");
    chartCtrFill = new Chart(ctx2, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "Fill Rate (%)",
                    data: data.fill_rates,
                    borderColor: "#a855f7", // Purple 500
                    backgroundColor: "rgba(168, 85, 247, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: "y-fill"
                },
                {
                    label: "CTR (%)",
                    data: data.ctrs,
                    borderColor: "#f59e0b", // Amber 500
                    backgroundColor: "rgba(245, 158, 11, 0.1)",
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                    yAxisID: "y-ctr"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#94a3b8" } }
            },
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148, 163, 184, 0.1)" } },
                "y-fill": {
                    type: "linear",
                    position: "left",
                    ticks: { color: "#a855f7", callback: v => v + "%" },
                    grid: { color: "rgba(148, 163, 184, 0.1)" }
                },
                "y-ctr": {
                    type: "linear",
                    position: "right",
                    ticks: { color: "#f59e0b", callback: v => v + "%" },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

async function fetchDailyDetails(days, source) {
    try {
        const res = await fetch(`/api/daily-details?days=${days}&source=${source}`);
        const data = await res.json();

        const tbody = document.getElementById("table-body");
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="py-6 text-center text-slate-400">Tidak ada data ditemukan untuk filter ini.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-700/30 transition border-b border-slate-700/40";

            const sourceBadgeClass = item.source === 'GAM' 
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' 
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';

            tr.innerHTML = `
                <td class="py-3 px-4 font-mono text-slate-200">${item.date}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded text-xs font-semibold border ${sourceBadgeClass}">
                        ${item.source}
                    </span>
                </td>
                <td class="py-3 px-4 text-right font-medium text-emerald-400">$${item.revenue.toFixed(2)}</td>
                <td class="py-3 px-4 text-right">${item.impressions.toLocaleString()}</td>
                <td class="py-3 px-4 text-right">${item.clicks.toLocaleString()}</td>
                <td class="py-3 px-4 text-right text-slate-400">${item.ad_requests.toLocaleString()}</td>
                <td class="py-3 px-4 text-right text-slate-400">${item.matched_requests.toLocaleString()}</td>
                <td class="py-3 px-4 text-right font-medium text-amber-400">${item.ctr}%</td>
                <td class="py-3 px-4 text-right font-medium text-purple-400">${item.fill_rate}%</td>
                <td class="py-3 px-4 text-right font-medium text-cyan-400">$${item.rpm.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error fetching table details:", err);
    }
}

async function syncData() {
    const icon = document.getElementById("sync-icon");
    icon.classList.add("fa-spin");

    try {
        const days = document.getElementById("filter-days").value;
        const res = await fetch("/api/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ days: parseInt(days) })
        });
        const data = await res.json();
        if (data.success) {
            await loadDashboardData();
        } else {
            alert("Sinkronisasi gagal: " + data.error);
        }
    } catch (err) {
        alert("Error menghubungi server untuk sinkronisasi.");
    } finally {
        icon.classList.remove("fa-spin");
    }
}

function filterTable() {
    const query = document.getElementById("search-table").value.toLowerCase();
    const rows = document.querySelectorAll("#table-body tr");

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
    });
}
