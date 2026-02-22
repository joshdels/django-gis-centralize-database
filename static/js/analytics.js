document.addEventListener("DOMContentLoaded", function () {
  const layerSelector = document.getElementById("layer-selector");
  if (!layerSelector) return;

  const STORAGE_KEY = "selectedSpatialLayer";

  const savedLayer = localStorage.getItem(STORAGE_KEY);
  const currentURL = new URL(window.location.href);
  const urlLayer = currentURL.searchParams.get("file_id");

  if (!urlLayer && savedLayer) {
    window.location.href = "?file_id=" + savedLayer;
    return;
  }

  if (urlLayer) {
    localStorage.setItem(STORAGE_KEY, urlLayer);
    layerSelector.value = urlLayer;
  }

  layerSelector.addEventListener("change", function (e) {
    const selectedLayer = e.target.value;

    localStorage.setItem(STORAGE_KEY, selectedLayer);
    window.location.href = "?file_id=" + selectedLayer;
  });
});
