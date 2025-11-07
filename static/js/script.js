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

    function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        // Display user message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('message', 'user-message');
        const userMessageP = document.createElement('p');
        userMessageP.textContent = messageText;
        userMessageDiv.appendChild(userMessageP);
        chatWindow.appendChild(userMessageDiv);

        // Clear input
        userInput.value = '';
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Simulate bot response
        setTimeout(function() {
            const botMessageDiv = document.createElement('div');
            botMessageDiv.classList.add('message', 'bot-message');
            const botMessageP = document.createElement('p');
            botMessageP.textContent = 'Cảm ơn câu hỏi của bạn! Đây là câu trả lời mẫu từ chatbot. Chức năng này đang được phát triển.';
            botMessageDiv.appendChild(botMessageP);
            chatWindow.appendChild(botMessageDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }, 1000);
    }
});