from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import SearchModule
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

import os

# Khởi tạo ứng dụng Flask
app = Flask(__name__)


# --- Cấu hình cho Database và Authentication ---
# Cần một SECRET_KEY để bảo vệ session của người dùng
app.config['SECRET_KEY'] = 'mot-chuoi-bi-mat-rat-kho-doan' 
# Thiết lập đường dẫn đến file database SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo các đối tượng
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Nếu người dùng chưa đăng nhập, chuyển đến route 'login'
login_manager.login_message_category = 'info' # Tùy chỉnh thông báo flash

# --- Định nghĩa các Model cho Database ---

# Model cho Người dùng (User)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    # Quan hệ một-nhiều: Một người dùng có thể có nhiều bài đăng
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}')"

# Model cho Bài đăng Nhật ký (Post)
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # Lưu khóa ngoại đến id của người dùng
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}')"

# Flask-Login cần hàm này để load người dùng từ session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dữ liệu mẫu về các món ăn
# Trong một dự án thực tế, dữ liệu này nên được lấy từ database
foods = {
    'pho': {
        'name': 'Phở Bò',
        'description': 'Phở là một món ăn truyền thống của Việt Nam, được xem là một trong những món ăn tiêu biểu cho ẩm thực Việt Nam. Thành phần chính của phở là bánh phở và nước dùng cùng với thịt bò hoặc gà cắt lát mỏng.',
        'location': 'Phở Thìn - 13 Lò Đúc, Hà Nội',
        'price': '50,000 - 70,000 VNĐ',
        'image': 'images/mainpage-display/pho.jpg'
    },
    'banh_mi': {
        'name': 'Bánh Mì',
        'description': 'Bánh mì Việt Nam là một loại bánh mì baguette được xẻ dọc, nhồi với thịt, πατέ, rau, và các loại nước sốt. Đây là một món ăn đường phố phổ biến và được yêu thích trên toàn thế giới.',
        'location': 'Bánh mì Phượng - 2B Phan Chu Trinh, Hội An',
        'price': '25,000 - 40,000 VNĐ',
        'image': 'images/mainpage-display/banh_mi.jpg'
    },
    'bun_cha': {
        'name': 'Bún Chả',
        'description': 'Bún chả là một món ăn của Hà Nội, bao gồm bún, chả thịt lợn nướng trên than hoa và bát nước mắm chua cay mặn ngọt. Món ăn này thường được ăn kèm với các loại rau sống.',
        'location': 'Bún chả Hương Liên - 24 Lê Văn Hưu, Hà Nội',
        'price': '40,000 - 60,000 VNĐ',
        'image': 'images/mainpage-display/bun_cha.jpg'
    }
}

# Route cho trang chủ
@app.route('/')
def index():
    """
    Hiển thị trang chủ với danh sách các món ăn nổi bật.
    """
    return render_template('index.html', foods=foods)

# Route cho trang bản đồ
@app.route('/map')
def map_page():
    """
    Hiển thị trang bản đồ.
    """
    return render_template('map.html')

# Route cho trang chatbot
@app.route('/chatbot')
def chatbot_page():
    """
    Hiển thị trang chatbot.
    """
    return render_template('chatbot.html')

# Route cho trang giới thiệu
@app.route('/about')
def about_page():
    """
    Hiển thị trang giới thiệu dự án.
    """
    return render_template('about.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Nhận tin nhắn từ JavaScript, gọi SearchModule, và trả về kết quả.
    """
    try:
        # 1. Nhận dữ liệu JSON từ request
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # 2. Gọi hàm logic từ SearchModule
        restaurant_list = SearchModule.restaurantSuggest(user_message)

        # 3. Định dạng kết quả trả về
        if not restaurant_list:
            response_text = "Xin lỗi, mình không tìm thấy nhà hàng nào phù hợp với yêu cầu của bạn. Bạn thử tìm ở khu vực khác xem?"
        else:
            # Biến danh sách nhà hàng thành một chuỗi văn bản đẹp
            response_text = "Mình tìm thấy vài gợi ý cho bạn nè:\n\n"
            print(restaurant_list)
            for r in restaurant_list:
                # Dùng **để in đậm (Markdown)
                response_text += f"{r['Name']}\n" 
                response_text += f"Địa chỉ: {r['Address']}\n"
                response_text += f"Giờ mở cửa: {r['OpeningTime']}\n"
                response_text += f"Ẩm thực: {r['Cuisine']}\n\n"

        # 4. Trả về kết quả dạng JSON
        # JavaScript của bạn sẽ nhận được {'reply': response_text}
        response = {"food_data": restaurant_list}
        print("JSON response:", response)  # Debug trước khi jsonify
        return jsonify(response)

    except Exception as e:
        print(f"Lỗi tại /api/chat: {e}")
        return jsonify({'error': str(e)}), 500
    
# --- Route MỚI cho Trang Tài Khoản ---
@app.route('/account')
@login_required # Yêu cầu người dùng phải đăng nhập để truy cập trang này
def account_page():
    """
    Hiển thị trang tài khoản với thông tin người dùng và nhật ký của họ.
    """
    # Lấy tất cả các bài đăng của người dùng hiện tại từ database
    user_posts = Post.query.filter_by(author=current_user).all()
    return render_template('account.html', user=current_user, posts=user_posts)

# --- Route MỚI để xử lý việc thêm bài đăng ---
@app.route('/add_post', methods=['POST'])
@login_required
def add_post():
    """
    Xử lý việc thêm một bài đăng nhật ký mới.
    """
    title = request.form.get('title')
    content = request.form.get('content')

    if title and content:
        new_post = Post(title=title, content=content, author=current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Bài viết của bạn đã được đăng!', 'success')
    else:
        flash('Tiêu đề và nội dung không được để trống.', 'danger')
        
    return redirect(url_for('account_page'))


# --- Routes MỚI cho Đăng ký, Đăng nhập, Đăng xuất ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Nếu đã đăng nhập, về trang chủ
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Kiểm tra xem username đã tồn tại chưa
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên người dùng này đã tồn tại. Vui lòng chọn tên khác.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Tài khoản của bạn đã được tạo! Bây giờ bạn có thể đăng nhập.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Nếu đã đăng nhập, về trang chủ
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            # Chuyển hướng đến trang mà người dùng định truy cập trước khi bị yêu cầu đăng nhập
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('account_page'))
        else:
            flash('Đăng nhập không thành công. Vui lòng kiểm tra lại tên người dùng và mật khẩu.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Chạy ứng dụng
if __name__ == '__main__':
    # Dòng code này sẽ tạo ra các bảng (như user, post) trong database
    # nếu chúng chưa tồn tại.
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=5000)