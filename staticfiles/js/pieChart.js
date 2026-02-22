let pieChart1Instance = null;

function renderPieChart(selectedKey, data) {
  const canvas = document.getElementById("pieChart");
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

  if (pieChart1Instance) pieChart1Instance.destroy();

  pieChart1Instance = new Chart(canvas.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: Object.keys(counts),
      datasets: [
        {
          data: Object.values(counts),
          backgroundColor: [
            "#419400",
            "#E1E6D9",
            "#343300",
            "#FF6384",
            "#36A2EB",
            "#FFCE56",
            "#FFA500",
            "#800080",
            "#008080",
            "#A52A2A",
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
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const raw = document.getElementById("geojson-data");
  const keySelector = document.getElementById("key-selector");

  if (!raw) return;

  let geojson = JSON.parse(raw.textContent);
  if (typeof geojson === "string") geojson = JSON.parse(geojson);

  const features = geojson.features || [];
  if (features.length === 0) return;
  const propertyList = features.map((f) => f.properties);

  if (keySelector) {
    keySelector.addEventListener("change", function (e) {
      const selectedKey = e.target.value;
      localStorage.setItem("selectedAttribute", selectedKey);
      renderPieChart(selectedKey, propertyList);
    });
  }

  const savedKey = localStorage.getItem("selectedAttribute");
  if (savedKey) {
    renderPieChart(savedKey, propertyList);
  }
});
