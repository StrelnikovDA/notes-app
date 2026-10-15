import os
import time
import psutil
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Путь к файлу для сохранения заметок (чтобы данные сохранялись при перезапуске)
DATA_FILE = '/data/notes.txt'

# Переменные для метрики "посещения в час"
visit_counts = []


def get_hourly_visits():
    current_time = time.time()
    # Удаляем посещения, которые были больше часа назад (3600 секунд)
    global visit_counts
    visit_counts = [t for t in visit_counts if current_time - t < 3600]
    return len(visit_counts)


# HTML-шаблон прямо в коде
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Менеджер заметок</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f9; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        textarea { width: 100%; padding: 8px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #007BFF; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .metrics { background: #e2e8f0; padding: 15px; border-radius: 8px; font-family: monospace; }
    </style>
</head>
<body>
    <h1>📝 Мои заметки (CI/CD Demo)</h1>

    <div class="card">
        <h3>Добавить новую заметку</h3>
        <form method="POST" action="/add">
            <textarea name="note" rows="3" placeholder="Введите текст заметки..." required></textarea><br>
            <button type="submit">Сохранить</button>
        </form>
    </div>

    <div class="card">
        <h3>Список заметок:</h3>
        {% if notes %}
            <ul>
                {% for note in notes %}
                    <li>{{ note }}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>Заметок пока нет.</p>
        {% endif %}
    </div>

    <div class="metrics">
        <h3>📊 Метрики приложения:</h3>
        <p><b>Посещений за последний час:</b> {{ visits }}</p>
        <p><b>Использование CPU:</b> {{ cpu_usage }}%</p>
        <p><b>Использование RAM:</b> {{ ram_usage }}% (Свободно: {{ ram_free }} MB)</p>
        <p><a href="/health" target="_blank">Health Check (/health)</a></p>
    </div>
</body>
</html>
'''


@app.before_request
def track_visits():
    # Не считаем запросы к health check за посещения пользователей
    if request.path not in ['/health']:
        visit_counts.append(time.time())


@app.route('/')
def index():
    notes = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            notes = [line.strip() for line in f.readlines()]

    # Собираем метрики ресурсов
    cpu_usage = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()

    return render_template_string(
        TEMPLATE,
        notes=notes,
        visits=get_hourly_visits(),
        cpu_usage=cpu_usage,
        ram_usage=ram.percent,
        ram_free=round(ram.available / (1024 * 1024), 2)
    )


@app.route('/add', methods=['POST'])
def add_note():
    note = request.form.get('note')
    if note:
        # Создаем папку для заметок, если ее нет
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'a', encoding='utf-8') as f:
            f.write(note + '\n')
    return redirect(url_for('index'))


@app.route('/health')
def health():
    return {"status": "UP", "message": "Application is running smoothly"}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)