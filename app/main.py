from flask import Flask, jsonify, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import logging
from g4f.client import Client

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

logging.basicConfig(level=logging.INFO)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('signup'))
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        url = request.form["user_input"]
        try:
            response = requests.get(f'https://{url}')
            if response.status_code == 200:
                file_path = os.path.join('app', 'templates', 'parsed_data.txt')
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(response.text)
                print(f'HTML-код страницы успешно сохранен в файл {file_path}')
                
                with open('Requierments.txt', 'r', encoding='utf-8') as file1:
                    content1 = file1.read()

                with open('app/templates/parsed_data.txt', 'r', encoding='utf-8') as file2:
                    content2 = file2.read()

                if not content1.strip() or not content2.strip():
                    flash("Один из текстов пуст, проверьте файлы.")
                    return redirect(url_for('dashboard'))

                prompt = f"""
                Оцени сайт по этим критериям, учитывай, что все они будут считаться за максимальный балл 10 из 10, по мере не соблюдения условий отнимай баллы и говори в каких местах будет лучше его подправить.
                {content1}
                Вот информация, полученная с сайта:
                {content2}
                Пожалуйста, сравни их и укажи, какие требования выполнены, а какие нет, с пояснениями. Объясни, что лучше улучшить и почему.
                """

                client = Client()
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                )
                result = response.choices[0].message.content
                return render_template('comparison_result.html', result=result) 

            else:
                flash(f'Ошибка при запросе: {response.status_code}')
        except Exception as e:
            logging.error(f"Ошибка при запросе: {e}")
            flash('Ошибка при запросе, проверьте URL.')

    return render_template('dashboard.html')

@app.route('/compare', methods=['POST'])
@login_required
def compare_files():
    try:
        with open('Requierments.txt', 'r', encoding='utf-8') as file1:
            content1 = file1.read()

        with open('app/templates/parsed_data.txt', 'r', encoding='utf-8') as file2:
            content2 = file2.read()

        if not content1.strip() or not content2.strip():
            flash("Один из текстов пуст, проверьте файлы.")
            return redirect(url_for('dashboard'))

        prompt = f"""
        Оцени сайт по этим критериям, учитывай, что все они будут считаться за максимальный балл 10 из 10, по мере не соблюдения условий отнимай баллы и говори в каких местах будет лучше его подправить.
        {content1}
        Вот информация, полученная с сайта:
        {content2}
        Пожалуйста, сравни их и укажи, какие требования выполнены, а какие нет, с пояснениями. Объясни, что лучше улучшить и почему.
        """

        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.choices[0].message.content
        return render_template('comparison_result.html', result=result)  # Создайте шаблон для отображения результата

    except Exception as e:
        logging.error(f"Ошибка при сравнении: {e}")
        flash('Ошибка при сравнении файлов.')
        return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    return f'Привет, {current_user.username}!'

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
