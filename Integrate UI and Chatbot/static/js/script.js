import {sendQueryToGemini} from './gemini.js'

document.addEventListener('DOMContentLoaded', function () {
    // --- Logic for Food Modal on Homepage ---
    var foodModal = document.getElementById('foodModal');
    if (foodModal) {
        foodModal.addEventListener('show.bs.modal', function (event) {
            // Button that triggered the modal
            var card = event.relatedTarget;

            // Extract info from data-* attributes
            var name = card.getAttribute('data-name');
            var description = card.getAttribute('data-description');
            var location = card.getAttribute('data-location');
            var price = card.getAttribute('data-price');
            var image = card.getAttribute('data-image');

            // Update the modal's content
            var modalTitle = foodModal.querySelector('.modal-title');
            var modalImage = foodModal.querySelector('#modalFoodImage');
            var modalDescription = foodModal.querySelector('#modalFoodDescription');
            var modalLocation = foodModal.querySelector('#modalFoodLocation');
            var modalPrice = foodModal.querySelector('#modalFoodPrice');

            modalTitle.textContent = name;
            modalImage.src = image;
            modalDescription.textContent = description;
            modalLocation.textContent = location;
            modalPrice.textContent = price;
        });
    }

    // --- Simple Chatbot UI Logic ---
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const userInput = document.getElementById('userInput');
    const chatWindow = document.getElementById('chat-window');

    if (sendMessageBtn && userInput && chatWindow) {
        sendMessageBtn.addEventListener('click', function () {
            sendMessage();
        });

        userInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    async function sendMessage() {
    const messageText = userInput.value.trim();
    if (messageText === '') return;
    
    // Display user message
    const userMessageDiv = document.createElement('div');
    userMessageDiv.classList.add('message', 'user-message');
    userMessageDiv.innerHTML = `<p>${messageText}</p>`;
    chatWindow.appendChild(userMessageDiv);
    userInput.value = '';
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Create loading bubble
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'bot-message', 'loading-message');
    loadingDiv.innerHTML = `<p></p>`;
    chatWindow.appendChild(loadingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Call Gemini API
    const geminiText = await sendQueryToGemini(messageText);

    // Remove loading bubble
    loadingDiv.remove();

    // Display bot response
    const botMessageDiv = document.createElement('div');
    botMessageDiv.classList.add('message', 'bot-message');
    botMessageDiv.innerHTML = `<p>${geminiText}</p>`;
    chatWindow.appendChild(botMessageDiv);

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

});


const themeToggleBtn = document.getElementById("themeToggleBtn");
const body = document.body;

// Load trạng thái đã lưu
if (localStorage.getItem("theme") === "dark") {
    body.classList.add("dark");
    themeToggleBtn.textContent = "🌞 Sáng";
}

themeToggleBtn.addEventListener("click", () => {
    body.classList.toggle("dark");
    let isDark = body.classList.contains("dark");

    themeToggleBtn.textContent = isDark ? "🌞 Sáng" : "🌙 Tối";
    localStorage.setItem("theme", isDark ? "dark" : "light");
});
