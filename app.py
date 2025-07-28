import os
from flask import Flask, render_template, request, redirect
import csv

app = Flask(__name__)

def update_floor_data(floor, new_positions):
    rows = []
    try:
        with open('data.csv', newline='') as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        rows = []
    # Оставляем все записи, кроме тех, что с текущим этажом
    rows = [row for row in rows if row[0] != floor]
    # Добавляем новые записи
    for pos in new_positions:
        if pos.strip():
            rows.append([floor, pos.strip()])
    # Перезаписываем файл
    with open('data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    floor = request.form['floor']
    positions = request.form.getlist('position')
    update_floor_data(floor, positions)
    # Перенаправляем обратно на форму после сохранения
    return redirect('/')

@app.route('/report')
def report():
    rows = []
    try:
        with open('data.csv', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
    except FileNotFoundError:
        rows = []
    return render_template('report.html', rows=rows)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
