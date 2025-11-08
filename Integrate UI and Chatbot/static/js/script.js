import {sendQueryToGemini} from './gemini.js'

const foodData = [
    {
        name: "Phở Bò Gánh",
        location: "123 Đường ABC, Hà Nội",
        description: "Phở truyền thống Việt Nam, nước dùng đậm đà.",
        image: "images/pho_bo.jpg"
    },
    {
        name: "Bún Chả Hương Liên",
        location: "24 Lê Văn Hưu, Hà Nội",
        description: "Bún chả thơm ngon với chả nướng và nước chấm đậm vị.",
        image: "images/bun.jpg"
    },
    {
        name: "Cơm Tấm Sài Gòn",
        location: "56 Nguyễn Trãi, TP.HCM",
        description: "Cơm tấm với sườn nướng và trứng ốp la hấp dẫn.",
        image: "images/com_tam.jpg"
    },
    {
        name: "Bánh Mì Phượng",
        location: "2B Phan Chu Trinh, Đà Nẵng",
        description: "Bánh mì giòn tan, pate thơm ngon và thịt nướng đậm vị.",
        image: "images/banh_mi_thit.jpg"
    },
    {
        name: "Chè Hẻm",
        location: "37 Lê Thánh Tôn, TP.HCM",
        description: "Các loại chè truyền thống, ngọt dịu và thanh mát.",
        image: "images/che.jpg"
    }
];


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
    botMessageDiv.classList.add('message', 'bot-message', 'd-flex', 'align-items-start');
    botMessageDiv.innerHTML = `
        <img src="/static/images/jane.jpg" class="bot-avatar" alt="Bot Avatar">
        <p>${geminiText}</p>
    `;
    chatWindow.appendChild(botMessageDiv);

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

});


const themeToggleBtn = document.getElementById("themeToggleBtn");
const body = document.body;

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

const track = document.getElementById('food-track');

function renderFoodCards(container, data) {
    data.forEach(food => {
        const card = document.createElement('div');
        card.classList.add('card-food');
        card.innerHTML = `
            <img src="/static/${food.image}" alt="${food.name}">
            <div class="food-info">
                <h5 class="food-name">${food.name}</h5>
                <p class="food-location">Địa chỉ: ${food.location}</p>
                <p class="food-description">${food.description}</p>
            </div>
            <button class="location-btn">
                <i class="fa-solid fa-location-dot"></i>
            </button>
        `;
        container.appendChild(card);
    });
}

renderFoodCards(track, foodData);
renderFoodCards(track, foodData); 

