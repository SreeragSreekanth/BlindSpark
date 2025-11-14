// --- Force reload when coming back from chatroom ---
window.addEventListener("pageshow", function (event) {
    const navType = performance.getEntriesByType("navigation")[0]?.type;
    if (event.persisted || navType === "back_forward") {
        window.location.reload();
    }
});

// --- Auto-refresh chat list every 5 seconds ---
setInterval(() => {
    fetch(window.location.href, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
    .then(res => res.text())
    .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        const newList = doc.querySelector(".list-group");
        const oldList = document.querySelector(".list-group");

        if (newList && oldList) {
            oldList.innerHTML = newList.innerHTML;
        }
    })
    .catch(err => console.error("Chat list refresh failed:", err));
}, 5000);

// --- FIXED SEARCH FILTER ---
document.getElementById('search-input').addEventListener('input', function() {
    const query = this.value.toLowerCase();

    document.querySelectorAll('.chat-item').forEach(item => {
        const username = item.dataset.name;
        item.style.display = username.includes(query) ? '' : 'none';
    });
});
