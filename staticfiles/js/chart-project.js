let chartInstance = null;

function renderChart(xKey, yKey, data, chartType = "doughnut") {
    const canvas = document.getElementById("pieChart");
    const placeholder = document.getElementById("chart-placeholder");
    if (!canvas) return;
    if (placeholder) placeholder.style.display = "none";

    let labels = [];
    let values = [];

    if (chartType === "bar" && xKey && yKey) {
        // Bar chart: X from data panel, Y numeric
        data.forEach(item => {
            const xVal = item[xKey] ?? "N/A";
            const yVal = parseFloat(item[yKey]);
            labels.push(xVal);
            values.push(isNaN(yVal) ? 0 : yVal);
        });
    } else {
        // Pie/Doughnut aggregate counts
        const counts = {};
        data.forEach(item => {
            const val = item[xKey] ?? "N/A";
            counts[val] = (counts[val] || 0) + 1;
        });
        labels = Object.keys(counts);
        values = Object.values(counts);
    }

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(canvas.getContext("2d"), {
        type: chartType === "bar" ? "bar" : "doughnut",
        data: {
            labels,
            datasets: [{
                label: chartType === "bar" ? yKey : xKey,
                data: values,
                backgroundColor: chartType === "bar" ? "#36A2EB" : [
                    "#419400","#E1E6D9","#343300","#FF6384","#36A2EB",
                    "#FFCE56","#FFA500","#800080","#008080","#A52A2A"
                ],
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: chartType === "doughnut" ? "50%" : undefined,
            plugins: {
                title: {
                    display: true,
                    text: chartType === "bar" ? `${yKey} vs ${xKey}` : xKey,
                    font: { size: 16, weight: "900" },
                },
                legend: { position: chartType === "doughnut" ? "bottom" : "top" },
            },
            scales: chartType === "bar" ? {
                y: { beginAtZero: true, title: { display: true, text: yKey } },
                x: { title: { display: true, text: xKey } }
            } : {},
        },
    });
}

document.addEventListener("DOMContentLoaded", function() {
    const raw = document.getElementById("geojson-data");
    if (!raw) return;

    let geojson = JSON.parse(raw.textContent);
    if (typeof geojson === "string") geojson = JSON.parse(geojson);
    const features = geojson.features || [];
    if (!features.length) return;
    const propertyList = features.map(f => f.properties);

    const keySelector = document.getElementById("key-selector"); // X-axis
    const chartTypeSelector = document.getElementById("chart-type-selector");
    const ySelector = document.getElementById("y-axis-selector"); // numeric only

    // Populate Y-axis options dynamically (numeric only, sorted alphabetically)
    const numericKeys = Object.keys(features[0].properties)
        .filter(k => !isNaN(parseFloat(features[0].properties[k])))
        .sort();

    numericKeys.forEach(k => {
        const opt = document.createElement("option");
        opt.value = k;
        opt.textContent = k;
        ySelector.appendChild(opt);
    });

    // Restore localStorage
    keySelector.value = localStorage.getItem("selectedKey") || keySelector.value;
    chartTypeSelector.value = localStorage.getItem("selectedChartType") || "doughnut";
    ySelector.value = localStorage.getItem("selectedY") || ySelector.value;

    function updateChart() {
        const xKey = keySelector.value;
        const yKey = ySelector.value;
        const chartType = chartTypeSelector.value;

        localStorage.setItem("selectedKey", xKey);
        localStorage.setItem("selectedChartType", chartType);
        localStorage.setItem("selectedY", yKey);

        // Show Y-axis only for bar chart
        ySelector.style.display = chartType === "bar" ? "inline-block" : "none";

        if (!xKey) return;
        if (chartType === "bar" && !yKey) return;
        renderChart(xKey, yKey, propertyList, chartType);
    }

    keySelector.addEventListener("change", updateChart);
    chartTypeSelector.addEventListener("change", updateChart);
    ySelector.addEventListener("change", updateChart);

    updateChart(); // initial render
});