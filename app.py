import os
import psycopg2
import random
import string
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")
DATABASE_URL = os.environ.get("DATABASE_URL")

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def enviar_correo(destinatario, codigo):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    message = Mail(
        from_email='pades.reservas.laboratorios@gmail.com',
        to_emails=destinatario,
        subject='Código de eliminación de tu reserva',
        html_content=f'<strong>Tu código secreto para eliminar la reserva es:</strong> {codigo}'
    )
    sg.send(message)

@app.route('/')
def index():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, equipo, inicio, fin, usuario FROM reservas ORDER BY inicio")
    reservas = cur.fetchall()
    conn.close()
    return render_template('index.html', reservas=reservas)

@app.route('/reservar', methods=['GET', 'POST'])
def reservar():
    if request.method == 'POST':
        equipo = request.form['equipo']
        fecha = request.form['fecha']
        hora = request.form['hora']
        duracion = int(request.form['duracion'])
        usuario = request.form['usuario']
        correo = request.form['correo']
        observaciones = request.form.get('observaciones', '')
        codigo = generar_codigo()

        inicio_str = f"{fecha} {hora}"
        inicio_dt = datetime.strptime(inicio_str, "%Y-%m-%d %H:%M")
        fin_dt = inicio_dt + timedelta(hours=duracion)

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM reservas
            WHERE equipo = %s AND (%s < fin AND %s > inicio)
        """, (equipo, fin_dt, inicio_dt))
        conflicto = cur.fetchone()

        if conflicto:
            conn.close()
            return render_template("error.html", mensaje="⚠️ Ya existe una reserva para ese equipo durante este periodo.")

        cur.execute("""
            INSERT INTO reservas (equipo, inicio, fin, usuario, codigo, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (equipo, inicio_dt, fin_dt, usuario, codigo, observaciones))
        conn.commit()
        conn.close()

        try:
            enviar_correo(correo, codigo)
        except Exception as e:
            print("Error al enviar correo:", e)

        return render_template("codigo.html", codigo=codigo)

    # Si GET, mostrar reservas agrupadas por equipo
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT equipo, inicio, fin FROM reservas ORDER BY equipo, inicio")
    reservas_existentes = cur.fetchall()
    conn.close()

    reservas_por_equipo = {}
    for equipo, inicio, fin in reservas_existentes:
        if equipo not in reservas_por_equipo:
            reservas_por_equipo[equipo] = []
        reservas_por_equipo[equipo].append((inicio, fin))

    return render_template('reservar.html', reservas_por_equipo=reservas_por_equipo)

@app.route('/eliminar/<int:reserva_id>', methods=['POST'])
def eliminar_reserva(reserva_id):
    codigo_ingresado = request.form['codigo'].strip().upper()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT codigo FROM reservas WHERE id = %s", (reserva_id,))
    resultado = cur.fetchone()

    if not resultado:
        conn.close()
        return render_template("error.html", mensaje="❌ Reserva no encontrada.")

    codigo_real = resultado[0].strip().upper()

    if codigo_ingresado == codigo_real:
        cur.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        conn.close()
        return render_template("error.html", mensaje="❌ Código incorrecto. No puedes eliminar esta reserva.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
