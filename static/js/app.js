// Drag & drop upload zone
document.querySelectorAll(".dropzone").forEach(zone => {
  const input = zone.querySelector("input[type=file]"), label = zone.querySelector(".dz-label");
  zone.addEventListener("click", () => input.click());
  ["dragover", "dragenter"].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.add("drag"); }));
  ["dragleave", "drop"].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.remove("drag"); }));
  zone.addEventListener("drop", ev => { input.files = ev.dataTransfer.files; input.dispatchEvent(new Event("change")); });
  input.addEventListener("click", ev => ev.stopPropagation());
  input.addEventListener("change", () => { if (input.files[0]) label.textContent = input.files[0].name; });
});
// Busy state on forms that run NLP (can take a few seconds)
document.querySelectorAll("form[data-busy]").forEach(f => f.addEventListener("submit", () => {
  const b = f.querySelector("button[type=submit]");
  if (b && f.checkValidity()) { b.disabled = true; b.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + (f.dataset.busy || "Working…"); }
}));
window.makeChart = (id, cfg) => { const el = document.getElementById(id); if (el && window.Chart) return new Chart(el, cfg); };
