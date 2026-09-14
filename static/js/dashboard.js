let chartFinancial = null;
let chartRoiCtr = null;

document.addEventListener("DOMContentLoaded", () => {
    checkStatus();
    loadDomainFilter();
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
    const domain = document.getElementById("filter-domain").value;
    let query = `period=${period}&source=${source}&domain=${domain}`;

    if (period === "custom") {
        const sDate = document.getElementById("custom-start-date").value;
        const eDate = document.getElementById("custom-end-date").value;
        if (sDate) query += `&start_date=${sDate}`;
        if (eDate) query += `&end_date=${eDate}`;
    }

    return query;
}

async function loadDomainFilter() {
    try {
        const res = await fetch('/api/domain-mappings');
        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();
        
        const selectFilter = document.getElementById("filter-domain");
        const selectSpendDomain = document.getElementById("spend-domain");

        const currentVal = selectFilter.value;
        selectFilter.innerHTML = '<option value="All">Semua Domain</option>';
        if (selectSpendDomain) selectSpendDomain.innerHTML = '';

        data.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item.domain_name;
            opt.textContent = `${item.domain_name} (Ads ID: ${item.google_ads_customer_id})`;
            selectFilter.appendChild(opt);

            if (selectSpendDomain) {
                const optSpend = document.createElement("option");
                optSpend.value = item.domain_name;
                optSpend.textContent = `${item.domain_name} (MCC: ${item.mcc_id} | Ads: ${item.google_ads_customer_id})`;
                optSpend.dataset.customerId = item.google_ads_customer_id;
                optSpend.dataset.mccId = item.mcc_id;
                selectSpendDomain.appendChild(optSpend);
            }
        });

        if (currentVal && Array.from(selectFilter.options).some(o => o.value === currentVal)) {
            selectFilter.value = currentVal;
        }
    } catch (err) {
        console.error("Error loading domain filter:", err);
    }
}

async function checkStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.status === 401) { window.location.href = "/login"; return; }
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
        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();
        const s = data.summary;

        document.getElementById("card-spend").textContent = formatRupiah(s.total_spend);
        document.getElementById("card-earning").textContent = formatRupiah(s.total_earning);
        
        const profitEl = document.getElementById("card-profit");
        profitEl.textContent = formatRupiah(s.total_profit);
        profitEl.className = s.total_profit < 0 ? "text-2xl font-bold text-rose-400 mt-2" : "text-2xl font-bold text-cyan-400 mt-2";

        const roiEl = document.getElementById("card-roi");
        roiEl.textContent = `${s.total_roi}%`;
        roiEl.className = s.total_roi < 0 ? "text-2xl font-bold text-rose-400 mt-2" : "text-2xl font-bold text-indigo-400 mt-2";

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
        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();
        renderCharts(data);
    } catch (err) {
        console.error("Error fetching timeseries:", err);
    }
}

function renderCharts(data) {
    if (chartFinancial) chartFinancial.destroy();
    if (chartRoiCtr) chartRoiCtr.destroy();

    const ctx1 = document.getElementById("chart-financial").getContext("2d");
    chartFinancial = new Chart(ctx1, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "Earning (Rp)",
                    data: data.earnings,
                    borderColor: "#10b981",
                    backgroundColor: "rgba(16, 185, 129, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: "Spend (Rp)",
                    data: data.spends,
                    borderColor: "#f43f5e",
                    backgroundColor: "rgba(244, 63, 94, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: "Profit (Rp)",
                    data: data.profits,
                    borderColor: "#06b6d4",
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

    const ctx2 = document.getElementById("chart-roi-ctr").getContext("2d");
    chartRoiCtr = new Chart(ctx2, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "ROI (%)",
                    data: data.rois,
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99, 102, 241, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: "y-roi"
                },
                {
                    label: "CTR (%)",
                    data: data.ctrs,
                    borderColor: "#f59e0b",
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
        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();

        const tbody = document.getElementById("table-body");
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="12" class="py-6 text-center text-slate-400">Tidak ada data ditemukan untuk filter ini.</td></tr>`;
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
                <td class="py-3 px-4 font-semibold text-indigo-300">${item.domain}</td>
                <td class="py-3 px-4 font-mono text-xs text-slate-400">${item.mcc_id || '-'}</td>
                <td class="py-3 px-4 font-mono text-xs text-slate-400">${item.google_ads_customer_id}</td>
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
                <td class="py-3 px-4 text-right font-medium text-amber-400">${item.ctr}%</td>
                <td class="py-3 px-4 text-right font-medium text-purple-400">${item.fill_rate}%</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error fetching table details:", err);
    }
}

// Modal Manual Spend Functions
function openManualSpendModal() {
    document.getElementById("manual-spend-modal").classList.remove("hidden");
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("spend-date").value = today;

    const selectSpendDomain = document.getElementById("spend-domain");
    if (selectSpendDomain && selectSpendDomain.selectedOptions.length > 0) {
        const opt = selectSpendDomain.selectedOptions[0];
        if (opt.dataset.customerId) document.getElementById("spend-customer-id").value = opt.dataset.customerId;
        if (opt.dataset.mccId) document.getElementById("spend-mcc-id").value = opt.dataset.mccId;
    }
}

function closeManualSpendModal() {
    document.getElementById("manual-spend-modal").classList.add("hidden");
}

async function saveManualSpend(e) {
    e.preventDefault();
    const date = document.getElementById("spend-date").value;
    const domain = document.getElementById("spend-domain").value;
    const mccId = document.getElementById("spend-mcc-id").value.trim();
    const customerId = document.getElementById("spend-customer-id").value.trim();
    const spend = parseFloat(document.getElementById("spend-amount").value) || 0;
    const clicks = parseInt(document.getElementById("spend-clicks").value) || 0;
    const impressions = parseInt(document.getElementById("spend-impressions").value) || 0;

    try {
        const res = await fetch('/api/manual-spend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                domain: domain,
                mcc_id: mccId,
                google_ads_customer_id: customerId,
                spend: spend,
                clicks: clicks,
                impressions: impressions
            })
        });

        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();

        if (data.success) {
            alert(data.message);
            closeManualSpendModal();
            await loadDashboardData();
        } else {
            alert("Gagal menyimpan Spend: " + data.error);
        }
    } catch (err) {
        alert("Error menghubungi server untuk menyimpan Spend.");
    }
}

// Modal Mapping Functions
function openMappingModal() {
    document.getElementById("mapping-modal").classList.remove("hidden");
    fetchMappingList();
}

function closeMappingModal() {
    document.getElementById("mapping-modal").classList.add("hidden");
}

async function fetchMappingList() {
    try {
        const res = await fetch('/api/domain-mappings');
        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();
        const listDiv = document.getElementById("mapping-list");
        listDiv.innerHTML = "";

        if (data.length === 0) {
            listDiv.innerHTML = '<p class="text-slate-500">Belum ada mapping domain.</p>';
            return;
        }

        data.forEach(m => {
            const div = document.createElement("div");
            div.className = "bg-slate-900 border border-slate-700/80 p-2.5 rounded-xl flex justify-between items-center";
            div.innerHTML = `
                <div>
                    <span class="font-bold text-indigo-300 text-xs">${m.domain_name}</span>
                    <span class="text-slate-500 mx-1.5">•</span>
                    <span class="font-mono text-slate-400">MCC: ${m.mcc_id || '-'}</span>
                    <span class="text-slate-500 mx-1">•</span>
                    <span class="font-mono text-slate-400">Ads ID: ${m.google_ads_customer_id}</span>
                </div>
                <span class="text-[10px] text-slate-500">${m.campaign_name || ''}</span>
            `;
            listDiv.appendChild(div);
        });
    } catch (err) {
        console.error("Error fetching mapping list:", err);
    }
}

async function saveMapping(e) {
    e.preventDefault();
    const domainName = document.getElementById("map-domain-name").value.trim();
    const mccId = document.getElementById("map-mcc-id").value.trim();
    const customerId = document.getElementById("map-customer-id").value.trim();
    const campaignName = document.getElementById("map-campaign-name").value.trim();

    try {
        const res = await fetch('/api/domain-mappings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                domain_name: domainName,
                mcc_id: mccId,
                google_ads_customer_id: customerId,
                campaign_name: campaignName
            })
        });

        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();

        if (data.success) {
            alert(data.message);
            document.getElementById("form-mapping").reset();
            await loadDomainFilter();
            await fetchMappingList();
            await loadDashboardData();
        } else {
            alert("Gagal menyimpan: " + data.error);
        }
    } catch (err) {
        alert("Error menghubungi server untuk menyimpan mapping.");
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

        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();
        if (data.success) {
            await loadDashboardData();
        } else {
            alert("Sinkronisasi gagal: " + (data.error || "Gagal sinkronisasi."));
        }
    } catch (err) {
        console.error("Sync error:", err);
        window.location.href = "/login";
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
