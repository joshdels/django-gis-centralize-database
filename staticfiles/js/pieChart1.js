let pieChart1Instance = null;

function renderPieChart(selectedKey, data) {
  const canvas = document.getElementById("pieChart1");
  const placeholder = document.getElementById("chart-placeholder");

  if (!canvas) return;

  if (placeholder) {
    placeholder.style.display = "none";
  }

  const counts = {};
  data.forEach((item) => {
    const val = item[selectedKey] || "N/A";
    counts[val] = (counts[val] || 0) + 1;
  });

  // const formattedTitle = selectedKey.replace(/_/g, " ").toUpperCase();

  if (pieChart1Instance) pieChart1Instance.destroy();

  pieChart1Instance = new Chart(canvas.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: Object.keys(counts),
      datasets: [
        {
          data: Object.values(counts),
          backgroundColor: [
            "#419400", // green
            "#E1E6D9", // light beige
            "#343300", // dark brown
            "#FF6384", // pink
            "#36A2EB", // blue
            "#FFCE56", // yellow
            "#FFA500", // orange
            "#800080", // purple
            "#008080", // teal
            "#A52A2A", // brown
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "50%",
      plugins: {
        title: {
          display: true,
          text: selectedKey,
          font: { size: 16, weight: "900" },
        },
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.parsed;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1) + "%";
              return `${value} (${percentage})`;
            },
          },
        },
      },
    },
  });
}

document.addEventListener("attributeSelected", (e) => {
  renderPieChart(e.detail.selectedKey, e.detail.data);
});

document.addEventListener("DOMContentLoaded", () => {
  if (window.spatialDataStore && window.spatialDataStore.selectedKey) {
    renderPieChart(
      window.spatialDataStore.selectedKey,
      window.spatialDataStore.data,
    );
  }
});
