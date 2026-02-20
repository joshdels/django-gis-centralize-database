function initializeSpatialSelector() {
  const raw = document.getElementById("geojson-data");
  const keySelector = document.getElementById("key-selector");

  if (!raw || !keySelector) return;

  try {
    let geojson = JSON.parse(raw.textContent);
    if (typeof geojson === "string") geojson = JSON.parse(geojson);

    const features = geojson.features || [];
    if (features.length === 0) return;

    let sampleProps = features[0].properties;
    let propertyList = [];

    if (Array.isArray(sampleProps)) {
      sampleProps = sampleProps[0] || {};
      propertyList = features[0].properties;
    } else if (sampleProps.features && Array.isArray(sampleProps.features)) {
      sampleProps = sampleProps.features[0] || {};
      propertyList = features.flatMap((f) => f.properties.features);
    } else {
      propertyList = features.map((f) => f.properties);
    }

    const keys = Object.keys(sampleProps).sort((a, b) =>
      a.toLowerCase().localeCompare(b.toLowerCase()),
    );

    keySelector.innerHTML =
      "<option disabled selected>Pick an attribute</option>";

    keys.forEach((key) => {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = key;
      keySelector.appendChild(opt);
    });

    keySelector.addEventListener("change", (e) => {
      const selectedKey = e.target.value;
      const event = new CustomEvent("attributeSelected", {
        detail: {
          selectedKey: selectedKey,
          data: propertyList,
        },
      });
      document.dispatchEvent(event);
    });
  } catch (e) {
    console.error("GeoJSON processing error:", e);
  }
}

document.addEventListener("DOMContentLoaded", initializeSpatialSelector);
