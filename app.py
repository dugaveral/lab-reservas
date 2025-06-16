from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

with app.app_context():
    init_db()

def init_db():
    conn = sqlite3.connect('reservas.db')
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
    conn = sqlite3.connect('reservas.db')
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

        conn = sqlite3.connect('reservas.db')
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)