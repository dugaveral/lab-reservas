import os
import psycopg2
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'clave-super-secreta')

# Datos de conexión desde variables de entorno
DB_URL = os.environ.get('DATABASE_URL')

def conectar_db():
    return psycopg2.connect(DB_URL)

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def enviar_correo(destinatario, codigo):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        message = Mail(
            from_email='pades.reservas.laboratorios@gmail.com',
            to_emails=destinatario,
            subject='Tu código de reserva de laboratorio',
            html_content=f'<strong>Tu código secreto para eliminar la reserva es:</strong> {codigo}'
        )
        sg.send(message)
    except Exception as e:
        import traceback
        print("Error al enviar correo:")
        traceback.print_exc()

def crear_tabla_si_no_existe():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id SERIAL PRIMARY KEY,
            equipo TEXT NOT NULL,
            inicio TIMESTAMP NOT NULL,
            fin TIMESTAMP NOT NULL,
            usuario TEXT NOT NULL,
            codigo TEXT
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM reservas ORDER BY inicio')
    reservas = cur.fetchall()
    conn.close()
    return render_template('index.html', reservas=reservas, usuario=None, fecha=None, equipo=None)

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

        inicio_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        fin_dt = inicio_dt + timedelta(hours=duracion_horas)

        conn = conectar_db()
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM reservas
            WHERE equipo = %s
            AND (
                inicio < %s
                AND fin > %s
            )
        ''', (equipo, fin_dt, inicio_dt))
        solape = cur.fetchone()
        if solape:
            conn.close()
            return render_template("error.html", mensaje="⚠️ Ya existe una reserva para ese equipo durante este periodo.")

        cur.execute('''
            INSERT INTO reservas (equipo, inicio, fin, usuario, codigo)
            VALUES (%s, %s, %s, %s, %s)
        ''', (equipo, inicio_dt, fin_dt, usuario, codigo))
        conn.commit()
        conn.close()

        enviar_correo(correo, codigo)

        session['codigo_reserva'] = codigo
        return redirect(url_for('mostrar_codigo'))

    conn = conectar_db()
    cur = conn.cursor()
    cur.execute('SELECT equipo, inicio, fin, usuario FROM reservas ORDER BY equipo, inicio')
    reservas = cur.fetchall()
    conn.close()
    return render_template('reservar.html', reservas=reservas)

@app.route('/codigo')
def mostrar_codigo():
    codigo = session.get('codigo_reserva', None)
    if not codigo:
        return redirect('/')
    return render_template('codigo.html', codigo=codigo)

@app.route('/eliminar/<int:reserva_id>', methods=['POST'])
def eliminar_reserva(reserva_id):
    codigo_ingresado = request.form['codigo'].strip().upper()

    conn = conectar_db()
    cur = conn.cursor()
    cur.execute('SELECT codigo FROM reservas WHERE id = %s', (reserva_id,))
    resultado = cur.fetchone()

    if not resultado:
        conn.close()
        return render_template("error.html", mensaje="❌ Reserva no encontrada.")

    codigo_real = resultado[0].strip().upper()

    if codigo_ingresado == codigo_real:
        cur.execute('DELETE FROM reservas WHERE id = %s', (reserva_id,))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        conn.close()
        return render_template("error.html", mensaje="❌ Código incorrecto. No puedes eliminar esta reserva.")

# Ejecuta solo una vez al iniciar la app para crear la tabla si no existe
with app.app_context():
    crear_tabla_si_no_existe()
