import os
import sqlite3
import random
import string
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "reservas.db")

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def enviar_correo(destinatario, codigo):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    message = Mail(
        from_email='tu-correo-verificado@tudominio.com',  # reemplaza por tu correo verificado en SendGrid
        to_emails=destinatario,
        subject='Tu código de reserva de laboratorio',
        html_content=f'<strong>Tu código secreto para eliminar la reserva es:</strong> {codigo}'
    )
    sg.send(message)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL,
            usuario TEXT NOT NULL,
            codigo TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM reservas ORDER BY inicio')
    reservas = c.fetchall()
    conn.close()
    return render_template('index.html', reservas=reservas)

@app.route('/reservar', methods=['GET', 'POST'])
def reservar():
    if request.method == 'POST':
        equipo = request.form['equipo']
        fecha = request.form['fecha']
        hora = request.form['hora']
        duracion_horas = int(request.form['duracion'])
        usuario = request.form['usuario']
        correo = request.form['correo']
        codigo = generar_codigo()

        inicio_str = f"{fecha} {hora}"
        inicio_dt = datetime.strptime(inicio_str, "%Y-%m-%d %H:%M")
        fin_dt = inicio_dt + timedelta(hours=duracion_horas)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT * FROM reservas
            WHERE equipo = ?
            AND (? < fin AND ? > inicio)
        ''', (equipo, fin_dt.isoformat(), inicio_dt.isoformat()))
        solape = c.fetchone()
        if solape:
            conn.close()
            return render_template("error.html", mensaje="⚠️ Ya existe una reserva para ese equipo durante este periodo.")

        c.execute('INSERT INTO reservas (equipo, inicio, fin, usuario, codigo) VALUES (?, ?, ?, ?, ?)',
                  (equipo, inicio_dt.isoformat(), fin_dt.isoformat(), usuario, codigo))
        conn.commit()
        conn.close()

        try:
            enviar_correo(correo, codigo)
        except Exception as e:
            print("Error al enviar correo:", e)

        return render_template("codigo.html", codigo=codigo)

    return render_template('reservar.html')

@app.route('/eliminar/<int:reserva_id>', methods=['POST'])
def eliminar_reserva(reserva_id):
    codigo_ingresado = request.form['codigo'].strip().upper()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT codigo FROM reservas WHERE id = ?', (reserva_id,))
    resultado = c.fetchone()

    if not resultado:
        conn.close()
        return render_template("error.html", mensaje="❌ Reserva no encontrada.")

    codigo_real = resultado[0].strip().upper()

    if codigo_ingresado == codigo_real:
        c.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        conn.close()
        return render_template("error.html", mensaje="❌ Código incorrecto. No puedes eliminar esta reserva.")

with app.app_context():
    init_db()