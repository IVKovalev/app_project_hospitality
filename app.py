from flask import Flask, render_template, request, redirect
import os
import csv
import json
import pandas as pd

app = Flask(__name__)

DATA_FILE = 'data.csv'

def read_data():
    try:
        with open(DATA_FILE, newline='') as f:
            return list(csv.reader(f))
    except FileNotFoundError:
        return []

def write_data(rows):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def update_floor_data(floor, pantry_positions, service_positions):
    rows = read_data()
    rows = [row for row in rows if row[0] != floor]

    for pos in pantry_positions:
        if pos.strip():
            rows.append([floor, pos.strip(), 'Pantry'])

    for pos in service_positions:
        if pos.strip():
            rows.append([floor, pos.strip(), 'Service Area'])

    write_data(rows)

def load_items():
    df = pd.read_excel('items.xlsx')  # или .csv
    pantry_items = df[df['Zone'] == 'Pantry']['Item'].tolist()
    service_items = df[df['Zone'] == 'Service Area']['Item'].tolist()
    return pantry_items, service_items

@app.route('/')
def index():
    floors = [2, 3, 6, 7, 8, 9]
    pantry_items, service_items = load_items()  # читаем из Excel
    return render_template(
        'form.html',
        floors=floors,
        pantry_items=pantry_items,
        service_items=service_items
    )

@app.route('/submit', methods=['POST'])
def submit():
    floor = request.form.get('floor')
    pantry_positions = request.form.getlist('position_pantry')
    service_positions = request.form.getlist('position_service')
    update_floor_data(floor, pantry_positions, service_positions)
    return redirect('/')

@app.route('/report')
def report():
    rows = read_data()
    return render_template('report.html', rows=rows)

@app.route('/report/save', methods=['POST'])
def save_report_changes():
    to_remove = json.loads(request.form['to_remove'])
    rows = read_data()

    updated = [
        row for row in rows
        if f"{row[0]}|||{row[1]}|||{row[2]}" not in to_remove
    ]

    write_data(updated)
    return redirect('/report')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
