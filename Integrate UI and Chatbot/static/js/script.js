// import {sendQueryToGemini} from './gemini.js'

const foodData = [
    {
        name: "Phở Bò Gánh",
        location: "123 Đường ABC, Hà Nội",
        description: "Phở truyền thống Việt Nam, nước dùng đậm đà.",
        image: "images/pho_bo.jpg",
        open: "Mo-Su 10:00-21:00",
        cuisine: "vietnamese"
    },
    {
        name: "Bún Chả Hương Liên",
        location: "24 Lê Văn Hưu, Hà Nội",
        description: "Bún chả thơm ngon với chả nướng và nước chấm đậm vị.",
        image: "images/bun.jpg",
        open: "Mo-Su 10:00-21:00",
        cuisine: "vietnamese"
    },
    {
        name: "Cơm Tấm Sài Gòn",
        location: "56 Nguyễn Trãi, TP.HCM",
        description: "Cơm tấm với sườn nướng và trứng ốp la hấp dẫn.",
        image: "images/com_tam.jpg",
        open: "Mo-Su 10:00-21:00",
        cuisine: "vietnamese"
    },
    {
        name: "Bánh Mì Phượng",
        location: "2B Phan Chu Trinh, Đà Nẵng",
        description: "Bánh mì giòn tan, pate thơm ngon và thịt nướng đậm vị.",
        image: "images/banh_mi_thit.jpg",
        open: "Mo-Su 10:00-21:00",
        cuisine: "vietnamese"
    },
    {
        name: "Chè Hẻm",
        location: "37 Lê Thánh Tôn, TP.HCM",
        description: "Các loại chè truyền thống, ngọt dịu và thanh mát.",
        image: "images/che.jpg",
        open: "Mo-Su 10:00-21:00",
        cuisine: "vietnamese"
    }
];


document.addEventListener('DOMContentLoaded', function () {
    // Initialize AOS for scroll animations
    if (window.AOS) {
        AOS.init({
            duration: 700,
            easing: 'ease-out-cubic',
            once: true,
            offset: 80
        });
    }

    // Smooth scroll for hero CTA
    document.querySelectorAll('.hero-cta').forEach(a => {
        a.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // --- Logic for Food Modal on Homepage (improved) ---
    var foodModal = document.getElementById('foodModal');
    if (foodModal) {
        foodModal.addEventListener('show.bs.modal', function (event) {
           var card = event.relatedTarget;
            if (!card) return;

            var name = card.getAttribute('data-name') || 'Không tên';
            var description = card.getAttribute('data-description') || 'Không có mô tả';
            var location = card.getAttribute('data-location') || '-';
            var price = card.getAttribute('data-price') || '-';
            var image = card.getAttribute('data-image') || '/static/images/placeholder-food.jpg';

            var modalTitle = foodModal.querySelector('.modal-title');
            var modalImage = foodModal.querySelector('#modalFoodImage');
            var modalDescription = foodModal.querySelector('#modalFoodDescription');
            var modalLocation = foodModal.querySelector('#modalFoodLocation');
            var modalPrice = foodModal.querySelector('#modalFoodPrice');
            var openMapBtn = foodModal.querySelector('#openMapBtn');

            modalTitle.textContent = name;
            modalImage.src = image;
            modalDescription.textContent = description;
            modalLocation.textContent = location;
            modalPrice.textContent = price;

            // openMapBtn can link to map page with query params (simple)
            openMapBtn.href = `/map?name=${encodeURIComponent(name)}&location=${encodeURIComponent(location)}`;
        });
    }
    // --- Filter & Search (client-side simple) ---
    const areaSelect = document.getElementById('areaSelect');
    const searchInput = document.getElementById('searchInput');
    const clearFilters = document.getElementById('clearFilters');
    const foodsGrid = document.getElementById('foodsGrid');
    const foodItems = Array.from(document.querySelectorAll('.food-item'));

    function applyFilters() {
        const area = (areaSelect?.value || 'all').toLowerCase();
        const q = (searchInput?.value || '').trim().toLowerCase();

        foodItems.forEach(item => {
            const itemArea = (item.getAttribute('data-area') || '').toLowerCase();
            const name = (item.getAttribute('data-name') || '').toLowerCase();
            const matchArea = (area === 'all') || itemArea.includes(area);
            const matchQuery = q === '' || name.includes(q);
            item.style.display = (matchArea && matchQuery) ? '' : 'none';
        });

        // refresh AOS (if used)
        if (window.AOS) AOS.refresh();
    }

    if (areaSelect) areaSelect.addEventListener('change', applyFilters);
    if (searchInput) searchInput.addEventListener('input', () => {
        // debounce quick
        clearTimeout(window.__searchDeb);
        window.__searchDeb = setTimeout(applyFilters, 200);
    });
    if (clearFilters) clearFilters.addEventListener('click', () => {
        if (areaSelect) areaSelect.value = 'all';
        if (searchInput) searchInput.value = '';
        applyFilters();
    });

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
    // 3. GỌI API BACKEND (thay vì gọi gemini.js)
    let botText = ""; // Biến để lưu tin nhắn trả lời
    try {
        // Gửi yêu cầu POST đến endpoint /api/chat của Flask
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // Gửi tin nhắn dưới dạng JSON
            body: JSON.stringify({ message: messageText }) 
        });

        if (!response.ok) {
            // Xử lý lỗi nếu server trả về 4xx, 5xx
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Nhận dữ liệu JSON trả về
        const data = await response.json();
        
        // Lấy nội dung trả lời từ key 'reply' (đã định nghĩa trong app.py)
        botText = data.reply; 

        // RẤT QUAN TRỌNG: Thay thế ký tự xuống dòng (\n) bằng thẻ <br>
        // để chúng hiển thị đúng trong HTML
        botText = botText.replace(/\n/g, '<br>');

    } catch (err) {
        console.error("Lỗi khi gọi API:", err);
        botText = "Xin lỗi, hệ thống đang gặp sự cố. Bạn vui lòng thử lại sau.";
    }

    // Remove loading bubble
    loadingDiv.remove();

    // Display bot response
    const botMessageDiv = document.createElement('div');
    botMessageDiv.classList.add('message', 'bot-message', 'd-flex', 'align-items-start');
    botMessageDiv.innerHTML = `
        <img src="/static/images/jane.jpg" class="bot-avatar" alt="Bot Avatar">
        <p>${botText}</p>
    `;
    chatWindow.appendChild(botMessageDiv);

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

    // --- Theme toggle (dark mode) ---
    const themeToggleBtn = document.getElementById("themeToggleBtn");
        const body = document.body;
        // === Theme initialization ===
    const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark") {
        body.classList.add("dark");
        if (themeToggleBtn) themeToggleBtn.textContent = "🌙 Tối";
    } else {
        body.classList.remove("dark");
        if (themeToggleBtn) themeToggleBtn.textContent = "🌞 Sáng";
    }


    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const isDark = body.classList.toggle("dark");
            themeToggleBtn.textContent = isDark ? "🌙 Tối" : "🌞 Sáng";
            localStorage.setItem("theme", isDark ? "dark" : "light");
            if (window.AOS) setTimeout(() => AOS.refresh(), 350);
        });
    }

    document.querySelectorAll('.location-dot').forEach(btn => {
        btn.addEventListener('click', function(e) {

            const lat = parseFloat(this.getAttribute('data-lat'));
            const lng = parseFloat(this.getAttribute('data-lng'));

            const modalEl = document.getElementById('mapModal');
            const mapModal = new bootstrap.Modal(modalEl);
            mapModal.show();

            modalEl.addEventListener('shown.bs.modal', function () {
                if (!window.map) {
                    window.map = L.map('mapContainer').setView([lat, lng], 16);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(window.map);
                    window.marker = L.marker([lat, lng]).addTo(window.map);
                } else {
                    window.map.setView([lat, lng], 16);
                    window.marker.setLatLng([lat, lng]);
                    window.map.invalidateSize();
                }
            }, { once: true });
        });
    });

    
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
                <p class="food-open-time">Giờ mở cửa: ${food.open}</p>
                <p class="cuisine">Ẩm thực: ${food.cuisine}</p>
            </div>
            <button class="location-btn location-dot"
                    title="Xem trên bản đồ" 
                    data-lat="10.780615" 
                    data-lng="106.695574"
                    data-name="${food.name}"
                    data-description="${food.description}"
                    data-location="${food.location}"
                    data-image="/static/${food.image}">
                <i class="fa-solid fa-location-dot"></i>
            </button>
        `;
        container.appendChild(card);
    });

    // --- Gắn listener sau khi tạo card ---
    container.querySelectorAll('.location-dot').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const lat = parseFloat(this.getAttribute('data-lat'));
            const lng = parseFloat(this.getAttribute('data-lng'));
            const modalEl = document.getElementById('mapModal');
            const mapModal = new bootstrap.Modal(modalEl);

            // Update modal nội dung
            const foodModal = modalEl;
            const modalTitle = foodModal.querySelector('.modal-title');
            const modalImage = foodModal.querySelector('#modalFoodImage');
            const modalDescription = foodModal.querySelector('#modalFoodDescription');
            const modalLocation = foodModal.querySelector('#modalFoodLocation');

            modalTitle.textContent = this.dataset.name;
            modalImage.src = this.dataset.image;
            modalDescription.textContent = this.dataset.description;
            modalLocation.textContent = this.dataset.location;

            mapModal.show();

            modalEl.addEventListener('shown.bs.modal', function () {
                if (!window.map) {
                    window.map = L.map('mapContainer').setView([lat, lng], 16);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(window.map);
                    window.marker = L.marker([lat, lng]).addTo(window.map);
                } else {
                    window.map.setView([lat, lng], 16);
                    window.marker.setLatLng([lat, lng]);
                    window.map.invalidateSize();
                }
            }, { once: true });
        });
    });
}
renderFoodCards(track, foodData);
renderFoodCards(track, foodData);

const pauseBtn = document.querySelector('.pause');
const restartBtn = document.querySelector('.restart');

pauseBtn.addEventListener('click', () => {
    // Kiểm tra animation đang paused hay chưa
    const isPaused = track.classList.toggle('paused'); // toggle trả về true nếu vừa add class

    // Thay đổi icon
    if (isPaused) {
        // Nếu paused → hiển thị icon play
        pauseBtn.innerHTML = '<i class="fa-regular fa-square-caret-right"></i>';
    } else {
        // Nếu đang chạy → hiển thị icon pause
        pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
    }
});

const fastBtn = document.querySelector('.fast');

let isFast = false; // trạng thái fast forward

fastBtn.addEventListener('click', () => {
    isFast = !isFast; // toggle trạng thái

    if (isFast) {
        // tua nhanh 1.5x → giảm duration xuống 2/3
        track.style.animationDuration = '5s'; // ví dụ gốc 10s / 1.5
        fastBtn.style.backgroundColor = 'rgba(255, 165, 0, 0.7)'; // highlight nút (tuỳ chọn)
    } else {
        // trở về tốc độ bình thường
        track.style.animationDuration = '20s'; 
        fastBtn.style.backgroundColor = ''; // reset
    }
});