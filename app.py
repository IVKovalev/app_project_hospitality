import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Конфигурация базы данных из переменной окружения
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')  # для отладки локально
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель таблицы
class MissingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.String(10), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(50), nullable=False)

# Загрузка списка позиций из Excel (items.xlsx)
def load_items():
    df = pd.read_excel('items.xlsx')  # можно заменить на .csv при необходимости
    pantry_items = df[df['Zone'] == 'Pantry']['Item'].tolist()
    service_items = df[df['Zone'] == 'Service Area']['Item'].tolist()
    return pantry_items, service_items

# Главная страница с формой
@app.route('/')
def index():
    floors = [2, 3, 6, 7, 8, 9]
    pantry_items, service_items = load_items()
    return render_template(
        'form.html',
        floors=floors,
        pantry_items=pantry_items,
        service_items=service_items
    )

# Сохранение отправленной формы
@app.route('/submit', methods=['POST'])
def submit():
    floor = request.form.get('floor')
    pantry_positions = request.form.getlist('position_pantry')
    service_positions = request.form.getlist('position_service')

    # Удалим все записи для этого этажа
    MissingItem.query.filter_by(floor=floor).delete()

    # Добавим новые записи
    for pos in pantry_positions:
        if pos.strip():
            db.session.add(MissingItem(floor=floor, position=pos.strip(), zone='Pantry'))

    for pos in service_positions:
        if pos.strip():
            db.session.add(MissingItem(floor=floor, position=pos.strip(), zone='Service Area'))

    db.session.commit()
    return redirect('/')

# Отчёт
@app.route('/report')
def report():
    rows = MissingItem.query.all()
    # Преобразуем в список кортежей для шаблона
    formatted = [(r.floor, r.position, r.zone) for r in rows]
    return render_template('report.html', rows=formatted)

# Удаление выполненных позиций
@app.route('/report/save', methods=['POST'])
def save_report_changes():
    to_remove = json.loads(request.form['to_remove'])

    for entry in to_remove:
        floor, position, zone = entry.split('|||')
        MissingItem.query.filter_by(floor=floor, position=position, zone=zone).delete()

    db.session.commit()
    return redirect('/report')

# Создание таблиц при первом запуске (или вручную в консоли)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


