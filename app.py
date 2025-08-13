import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

app = Flask(__name__)

# Конфигурация базы данных из переменной окружения
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')  # для отладки локально
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель таблицы
class MissingItem(db.Model):
    __tablename__ = 'missing_item'  # явно зафиксируем имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.String(10), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('floor', 'position', 'zone', name='uix_floor_pos_zone'),
        db.Index('ix_floor_zone', 'floor', 'zone'),
    )

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

# Health-check endpoint для пингера. Для того что бы держать приложение горячим. Использую пингер cron-job.org
@app.route('/health')
def health():
    return 'ok', 200

# Сохранение отправленной формы
@app.route('/submit', methods=['POST'])
def submit():
    floor = request.form.get('floor')
    if not floor:
        return redirect('/')

    # Списки из формы (могут быть с пустыми значениями)
    pantry_positions = [p.strip() for p in request.form.getlist('position_pantry') if p.strip()]
    service_positions = [p.strip() for p in request.form.getlist('position_service') if p.strip()]

    # Уже существующие позиции для этого этажа (чтобы не плодить дубли)
    existing = MissingItem.query.filter_by(floor=floor).all()
    existing_set = {(row.position, row.zone) for row in existing}

    # Добавляем только те, которых ещё нет
    for pos in pantry_positions:
        if (pos, 'Pantry') not in existing_set:
            db.session.add(MissingItem(floor=floor, position=pos, zone='Pantry'))

    for pos in service_positions:
        if (pos, 'Service Area') not in existing_set:
            db.session.add(MissingItem(floor=floor, position=pos, zone='Service Area'))

    db.session.commit()
    return redirect('/')

# Страхуется от добликатов на уровне БД (UPSERT-вставка, сделаем универсально: Postgres на Render + SQLite локально)
def _is_postgres():
    return db.engine.url.drivername.startswith('postgresql')

def upsert_missing(floor, position, zone):
    if _is_postgres():
        stmt = pg_insert(MissingItem).values(floor=floor, position=position, zone=zone)
        stmt = stmt.on_conflict_do_nothing(index_elements=['floor', 'position', 'zone'])
    else:
        stmt = sqlite_insert(MissingItem).values(floor=floor, position=position, zone=zone)
        stmt = stmt.on_conflict_do_nothing(index_elements=['floor', 'position', 'zone'])
    db.session.execute(stmt)

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




