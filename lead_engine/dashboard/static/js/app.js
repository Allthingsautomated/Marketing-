// Global toast notification
function showToast(message, duration = 3000) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => toast.classList.add("hidden"), duration);
}

// Auto-refresh leads page every 30s if a search was recently started
if (window.location.pathname === "/leads") {
  const urlParams = new URLSearchParams(window.location.search);
  if (document.referrer.includes("/search")) {
    let countdown = 30;
    const interval = setInterval(() => {
      countdown--;
      if (countdown <= 0) {
        clearInterval(interval);
        window.location.reload();
      }
    }, 1000);
  }
}

// Confirm before marking as lost
document.querySelectorAll(".status-select").forEach(sel => {
  sel.addEventListener("change", function(e) {
    if (e.target.value === "lost") {
      if (!confirm("Mark this lead as lost? This will trigger AI learning.")) {
        e.target.value = e.target.dataset.prev || "new";
        return;
      }
    }
    e.target.dataset.prev = e.target.value;
  });
  sel.dataset.prev = sel.value;
});
