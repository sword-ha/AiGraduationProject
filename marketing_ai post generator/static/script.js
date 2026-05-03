const chatbox = document.getElementById("chatbox");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", (e) => { if(e.key === "Enter") sendMessage(); });

async function sendMessage() {
    const message = input.value.trim();
    if(!message) return;

    chatbox.innerHTML += `<div class="user">You: ${message}</div>`;
    input.value = "";

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });

    const data = await res.json();
    chatbox.innerHTML += `<div class="bot">Bot: ${data.reply}</div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
}
