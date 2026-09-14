let chartFinancial = null;
let chartRoiCtr = null;

document.addEventListener("DOMContentLoaded", () => {
    checkStatus();
    loadDashboardData();
});

function formatRupiah(num) {
    if (num === null || num === undefined) return "Rp 0";
    const rounded = Math.round(num);
    return "Rp " + rounded.toLocaleString("id-ID");
}

function handlePeriodChange() {
    const period = document.getElementById("filter-period").value;
    const customContainer = document.getElementById("custom-date-container");

    if (period === "custom") {
        customContainer.classList.remove("hidden");
        const today = new Date().toISOString().split('T')[0];
        if (!document.getElementById("custom-end-date").value) {
            document.getElementById("custom-end-date").value = today;
        }
        if (!document.getElementById("custom-start-date").value) {
            const d = new Date();
            d.setDate(d.getDate() - 30);
            document.getElementById("custom-start-date").value = d.toISOString().split('T')[0];
        }
    } else {
        customContainer.classList.add("hidden");
    }

    loadDashboardData();
}

function buildQueryParams() {
    const period = document.getElementById("filter-period").value;
    const source = document.getElementById("filter-source").value;
    let query = `period=${period}&source=${source}`;

    if (period === "custom") {
        const sDate = document.getElementById("custom-start-date").value;
        const eDate = document.getElementById("custom-end-date").value;
        if (sDate) query += `&start_date=${sDate}`;
        if (eDate) query += `&end_date=${eDate}`;
    }

    return query;
}

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
    const query = buildQueryParams();

    await Promise.all([
        fetchSummary(query),
        fetchTimeseries(query),
        fetchDailyDetails(query)
    ]);

    document.getElementById("last-updated-time").textContent = new Date().toLocaleTimeString("id-ID");
}

async function fetchSummary(query) {
    try {
        const res = await fetch(`/api/summary?${query}`);
        const data = await res.json();
        const s = data.summary;

        document.getElementById("card-spend").textContent = formatRupiah(s.total_spend);
        document.getElementById("card-earning").textContent = formatRupiah(s.total_earning);
        
        const profitEl = document.getElementById("card-profit");
        profitEl.textContent = formatRupiah(s.total_profit);
        if (s.total_profit < 0) {
            profitEl.className = "text-2xl font-bold text-rose-400 mt-2";
        } else {
            profitEl.className = "text-2xl font-bold text-cyan-400 mt-2";
        }

        const roiEl = document.getElementById("card-roi");
        roiEl.textContent = `${s.total_roi}%`;
        if (s.total_roi < 0) {
            roiEl.className = "text-2xl font-bold text-rose-400 mt-2";
        } else {
            roiEl.className = "text-2xl font-bold text-indigo-400 mt-2";
        }

        document.getElementById("card-impressions").textContent = s.total_impressions.toLocaleString('id-ID');
        document.getElementById("card-ctr").textContent = `${s.avg_ctr}%`;
        document.getElementById("card-rpm").textContent = formatRupiah(s.avg_rpm);
    } catch (err) {
        console.error("Error fetching summary:", err);
    }
}

async function fetchTimeseries(query) {
    try {
        const res = await fetch(`/api/timeseries?${query}`);
        const data = await res.json();
        renderCharts(data);
    } catch (err) {
        console.error("Error fetching timeseries:", err);
    }
}

function renderCharts(data) {
    if (chartFinancial) chartFinancial.destroy();
    if (chartRoiCtr) chartRoiCtr.destroy();

    // Chart 1: Earning, Spend, Profit dalam Rupiah
    const ctx1 = document.getElementById("chart-financial").getContext("2d");
    chartFinancial = new Chart(ctx1, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "Earning (Rp)",
                    data: data.earnings,
                    borderColor: "#10b981", // Emerald 500
                    backgroundColor: "rgba(16, 185, 129, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: "Spend (Rp)",
                    data: data.spends,
                    borderColor: "#f43f5e", // Rose 500
                    backgroundColor: "rgba(244, 63, 94, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: "Profit (Rp)",
                    data: data.profits,
                    borderColor: "#06b6d4", // Cyan 500
                    backgroundColor: "rgba(6, 182, 212, 0.05)",
                    borderWidth: 2,
                    borderDash: [4, 4],
                    fill: false,
                    tension: 0.3
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
                y: { 
                    ticks: { 
                        color: "#94a3b8", 
                        callback: v => "Rp " + (v / 1000).toLocaleString('id-ID') + "k" 
                    }, 
                    grid: { color: "rgba(148, 163, 184, 0.1)" } 
                }
            }
        }
    });

    // Chart 2: ROI (%) & CTR (%)
    const ctx2 = document.getElementById("chart-roi-ctr").getContext("2d");
    chartRoiCtr = new Chart(ctx2, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "ROI (%)",
                    data: data.rois,
                    borderColor: "#6366f1", // Indigo 500
                    backgroundColor: "rgba(99, 102, 241, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: "y-roi"
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
                "y-roi": {
                    type: "linear",
                    position: "left",
                    ticks: { color: "#6366f1", callback: v => v + "%" },
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

async function fetchDailyDetails(query) {
    try {
        const res = await fetch(`/api/daily-details?${query}`);
        const data = await res.json();

        const tbody = document.getElementById("table-body");
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" class="py-6 text-center text-slate-400">Tidak ada data ditemukan untuk filter ini.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-700/30 transition border-b border-slate-700/40";

            const sourceBadgeClass = item.source === 'GAM' 
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' 
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';

            const profitClass = item.profit < 0 ? "text-rose-400 font-bold" : "text-cyan-400 font-bold";
            const roiClass = item.roi < 0 ? "text-rose-400 font-bold" : "text-indigo-400 font-bold";

            tr.innerHTML = `
                <td class="py-3 px-4 font-mono text-slate-200">${item.date}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded text-xs font-semibold border ${sourceBadgeClass}">
                        ${item.source}
                    </span>
                </td>
                <td class="py-3 px-4 text-right font-medium text-rose-400">${formatRupiah(item.spend)}</td>
                <td class="py-3 px-4 text-right font-medium text-emerald-400">${formatRupiah(item.earning)}</td>
                <td class="py-3 px-4 text-right ${profitClass}">${formatRupiah(item.profit)}</td>
                <td class="py-3 px-4 text-right ${roiClass}">${item.roi}%</td>
                <td class="py-3 px-4 text-right">${item.impressions.toLocaleString('id-ID')}</td>
                <td class="py-3 px-4 text-right">${item.clicks.toLocaleString('id-ID')}</td>
                <td class="py-3 px-4 text-right font-medium text-amber-400">${item.ctr}%</td>
                <td class="py-3 px-4 text-right font-medium text-purple-400">${item.fill_rate}%</td>
                <td class="py-3 px-4 text-right font-medium text-cyan-400">${formatRupiah(item.rpm)}</td>
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
        const period = document.getElementById("filter-period").value;
        const days = (period === "today" || period === "yesterday") ? 7 : (parseInt(period) || 30);
        const res = await fetch("/api/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ days: days })
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
