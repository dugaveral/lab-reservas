import os
import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Ruta absoluta para evitar errores en entornos como Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "reservas.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            usuario TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM reservas ORDER BY fecha, hora')
    reservas = c.fetchall()
    conn.close()
    return render_template('index.html', reservas=reservas)

@app.route('/reservar', methods=['GET', 'POST'])
def reservar():
    if request.method == 'POST':
        equipo = request.form['equipo']
        fecha = request.form['fecha']
        hora = request.form['hora']
        usuario = request.form['usuario']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM reservas WHERE equipo=? AND fecha=? AND hora=?',
                  (equipo, fecha, hora))
        solape = c.fetchone()
        if solape:
            conn.close()
            return "⚠️ Ya existe una reserva para ese equipo en ese horario.", 400

        c.execute('INSERT INTO reservas (equipo, fecha, hora, usuario) VALUES (?, ?, ?, ?)',
                  (equipo, fecha, hora, usuario))
        conn.commit()
        conn.close()
        return redirect('/')
    
    return render_template('reservar.html')

# Crear la base de datos al arrancar la app
with app.app_context():
    init_db()
