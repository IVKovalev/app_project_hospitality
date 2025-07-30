from flask import Flask, render_template, request, redirect
import csv

app = Flask(__name__)

def update_floor_data(floor, pantry_positions, service_positions):
    rows = []
    try:
        with open('data.csv', newline='') as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        rows = []

    # Удаляем записи для текущего этажа
    rows = [row for row in rows if row[0] != floor]

    # Добавляем кладовку
    for pos in pantry_positions:
        if pos.strip():
            rows.append([floor, pos.strip(), 'Pantry'])

    # Добавляем сервисную зону
    for pos in service_positions:
        if pos.strip():
            rows.append([floor, pos.strip(), 'Service Area'])

    with open('data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

@app.route('/')
def index():
    floors = [2, 3, 6, 7, 8, 9]
    return render_template('form.html', floors=floors)

@app.route('/submit', methods=['POST'])
def submit():
    floor = request.form.get('floor')
    pantry_positions = request.form.getlist('position_pantry')
    service_positions = request.form.getlist('position_service')
    update_floor_data(floor, pantry_positions, service_positions)
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
    app.run(debug=True)
