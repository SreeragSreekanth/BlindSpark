const chatBox = document.getElementById('chat-box');
const form = document.getElementById('chat-form');
const input = document.getElementById('msg-input');
const popup = document.getElementById('delete-popup');

let currentMsgId = null;
let pressTimer;
let lastMessageCount = 0;

// Scroll to bottom
function scrollToBottom() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Scroll only if user is near bottom
function scrollToBottomIfNearBottom() {
  const threshold = 50;
  const isNearBottom =
    chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight < threshold;
  if (isNearBottom) scrollToBottom();
}

// Fetch messages
function fetchMessages() {
  fetch(CHAT_FETCH_URL)
    .then(res => res.json())
    .then(data => {
      const oldMessageCount = lastMessageCount;

      chatBox.innerHTML = data.html;
      attachDeleteListeners();
      lastMessageCount = data.messages_count;

      if (oldMessageCount === 0) scrollToBottom();
      else if (lastMessageCount > oldMessageCount) scrollToBottom();
    });
}

// Delete message
function deleteMessage() {
  if (!currentMsgId || !confirm("Delete this message?")) return;

  fetch(`/chat/message/${currentMsgId}/delete/`, {
    method: "POST",
    headers: { "X-CSRFToken": CSRF_TOKEN }
  }).then(() => {
    fetchMessages();
    popup.style.display = "none";
    currentMsgId = null;
  });
}

// Right-click delete
document.addEventListener("contextmenu", function (e) {
  const bubble = e.target.closest(".msg-bubble.me");
  if (bubble) {
    e.preventDefault();
    currentMsgId = bubble.dataset.msgId;

    popup.style.display = "block";
    popup.style.left = e.pageX + "px";
    popup.style.top = e.pageY + "px";
  }
});

// Hide popup when clicking outside
document.addEventListener("click", (e) => {
  if (!e.target.closest("#delete-popup")) {
    popup.style.display = "none";
  }
});

// Mobile long-press delete
function attachDeleteListeners() {
  document.querySelectorAll(".msg-bubble.me").forEach(bubble => {
    const start = () => {
      pressTimer = setTimeout(() => {
        currentMsgId = bubble.dataset.msgId;
        deleteMessage();
      }, 800);
    };

    const cancel = () => clearTimeout(pressTimer);

    bubble.ontouchstart = start;
    bubble.ontouchend = cancel;
    bubble.ontouchmove = cancel;
  });
}

// Send message
form.addEventListener("submit", (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  const formData = new FormData();
  formData.append("text", text);
  formData.append("csrfmiddlewaretoken", CSRF_TOKEN);

  fetch(CHAT_SEND_URL, {
    method: "POST",
    body: formData
  }).then(() => {
    input.value = "";
    fetchMessages();
  });
});

// Reveal buttons
document.getElementById("request-btn")?.addEventListener("click", () => {
  fetch(REQUEST_REVEAL_URL, {
    method: "POST",
    headers: { "X-CSRFToken": CSRF_TOKEN }
  })
    .then(r => r.json())
    .then(d => {
      if (d.requested) {
        document.getElementById("reveal-controls").innerHTML =
          '<button class="btn btn-warning btn-sm" disabled>Requested</button>';
      }
    });
});

document.getElementById("accept-btn")?.addEventListener("click", () => {
  fetch(ACCEPT_REVEAL_URL, {
    method: "POST",
    headers: { "X-CSRFToken": CSRF_TOKEN }
  })
    .then(r => r.json())
    .then(d => {
      if (d.accepted) {
        document.getElementById("profile-photo").classList.remove("blur-photo");
        document.getElementById("reveal-controls").innerHTML =
          '<span class="text-success small">Unblurred</span>';
      }
    });
});

// Init
fetchMessages();
setInterval(fetchMessages, 2000);
