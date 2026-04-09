(function () {
  if (document.getElementById("foundry-extension-anchor")) {
    return;
  }

  const anchor = document.createElement("div");
  anchor.id = "foundry-extension-anchor";
  anchor.style.position = "fixed";
  anchor.style.right = "12px";
  anchor.style.bottom = "12px";
  anchor.style.zIndex = "2147483000";
  anchor.style.padding = "8px 10px";
  anchor.style.borderRadius = "8px";
  anchor.style.background = "#1b2b55";
  anchor.style.color = "#fff";
  anchor.style.fontFamily = "Segoe UI, sans-serif";
  anchor.style.fontSize = "12px";
  anchor.style.boxShadow = "0 2px 8px rgba(0,0,0,0.2)";
  anchor.textContent = "Foundry extension active";
  document.body.appendChild(anchor);

  chrome.runtime.sendMessage({ type: "foundry.ping" }, () => {});
})();
