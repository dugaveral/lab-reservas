import os
import psycopg2
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, Response, session
from datetime import datetime, timedelta
import random
import string
import sendgrid
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "laboratorio-reservas-pades"
DB_URL = os.environ.get("DATABASE_URL")

EQUIPOS_LISTA = [
  "Agitador De Cabezal",
  "Agitador De Cabezal De Dispersión (Azul)",
  "Agitador De Cabezal De Dispersión (Azul) 2",
  "Agitador De Cabezal De Dispersión (Gris)",
  "Agitador De Cabezal De Dispersión (Gris) 2",
  "Agitador De Cabezal De Dispersión (Gris) 3",
  "Agitador Magnético Con Calentamiento",
  "Agitador Magnético",
  "Agitador Magnético 2",
  "Agitador Vortex",
  "Analizador De Tamaño De Partícula",
  "Analizador Elemental",
  "Autoclave",
  "Balanza 6Kg",
  "Balanza 6Kg 2",
  "Balanza De Humedad",
  "Balanza De Humedad 2",
  "Balanza De Humedad 3",
  "Balanza De Humedad 4",
  "Balanza Digital Capacidad 6 Kg Bacsa",
  "Balanza Gramera",
  "Balanzas Analítica",
  "Balanzas Analítica 2",
  "Balanzas Analítica 3",
  "Baño De Calentamiento Con Agitación",
  "Baño De María",
  "Baño Termostatado",
  "Baño Termostatado 12L",
  "Baño Termostatado 12L 2",
  "Baño Termostatado 12L 3",
  "Baño Termostatado 8L",
  "Baño Termostatado 8L 2",
  "Baño Termostatado Con Recirculación 24L",
  "Baño Ultrasónico",
  "Banda Trasportadora",
  "Batidora De 4.3 Litros",
  "Batidora De 4.3 Litros 2",
  "Batidora Marca",
  "Biorreactor De Lecho Fijo En Acero Inoxidable Tipo 304",
  "Bloque Digestor",
  "Bomba Calorimétrica",
  "Bomba De Vacío",
  "Bomba De Vacío 2",
  "Bomba De Vacío 3",
  "Bomba Del HPLC",
  "Bomba Isocratica / Cuaternaria",
  "Bomba Para Caldera",
  "Bomba Para Caldera 2",
  "Cámara De Estabilización",
  "Cámara De Fermentación",
  "Cámara De Fermentación 2",
  "Carretilla Para Afrecho En Acero Inoxidable Con Ruedas",
  "Centrifuga",
  "Centrifuga 2",
  "Centrifuga 3",
  "Shaker Con Agitación Orbital",
  "Colorímetro",
  "Colorímetro 2",
  "Compresor Elite",
  "Compresor Medic Air De 108 Litros",
  "Computador De Mesa Del Farinografo",
  "Congelador Horizontal",
  "Cromatógrafo De Gases Acoplado A Masas",
  "Cromatógrafo De Gases Con Detector FID",
  "Cúter",
  "CPU Del Computador Del HPLC",
  "Detector Del HPLC",
  "Destilador De Agua",
  "Destilador De Agua 2",
  "Desengrasador 6 Puestos",
  "Desgasificador HPLC",
  "Deshumidificador",
  "Determinador De Actividad De Agua",
  "Determinador De Fibra",
  "Determinador De Fibra Tecnal",
  "Determinador De Grasa",
  "Determinador De Nitrógeno",
  "Embutidora Manual",
  "Empacadora Al Vacío",
  "Empacadora De Sólidos Semi Manual Con Sistema De Sellado Horizontal",
  "Empacadora Selladora",
  "Enfriador De Agua",
  "Equipo De Electrocoagulación",
  "Equipo De Ultrasonido",
  "Equipo Soxhlet De 6 Puestos",
  "Equipo Soxhlet De 6 Puestos 2",
  "Equipo Termoquímico Multipropósito",
  "Espectrofotómetro UV",
  "Espectrofotómetro UV Visible",
  "Espectrofotómetro UV Visible 2",
  "Estufa De Secado",
  "Extractor De Fibra",
  "Extrusora Marca Equipos Y Montajes",
  "Extrusora Para Pastas",
  "Farinografo",
  "Flexi Chill Set Line",
  "Floculador De 4 Puestos",
  "Floculador Portable",
  "Hidrociclón Acero Inoxidable Tipo 304 Con Bomba",
  "Homogeneizador",
  "Homogeneizador 2",
  "Homogeneizador En Acero Inoxidable Aisi 304/Ha304-50150",
  "Horno 1",
  "Horno 2",
  "Horno 3",
  "Horno 4",
  "Horno 5",
  "Horno 6",
  "Horno 7",
  "Horno De Materia Volátil",
  "Mufla 1",
  "Mufla 2",
  "Impresora Del HPLC",
  "Incubadora Being",
  "Incubadora Being 2",
  "Licuadora",
  "Licuadora Osterizer",
  "Licuadora Osterizer 2",
  "Lavadora Peladora De Yuca",
  "Lavadora-Peladora De Vegetales",
  "Maquina Para Helado Suave Tres Boquillas Mh Twist 20 L",
  "Maquina Peletizadora Tempo Kl160",
  "Marmita Multipropósito Volcable Para Vapor",
  "Mouse Del HPLC",
  "Mezclador De Sólidos",
  "Micro Balanza",
  "Microscopio De Luz Polarizada",
  "Molino De Martillo Con Ciclón, Sistema De Carga Por Tornillo Alimentador Y Turbina",
  "Molino Multiusos",
  "Molino Multiusos 2",
  "Molino Para Carnes",
  "Molino Para Materiales Amiláceos",
  "Molino Tipo Willey",
  "Molino Tornillo Sin Fin",
  "Monitor",
  "Monitor Del HPLC",
  "Nevera",
  "Nevera 2",
  "Oxímetro",
  "Peletizadora (Negra)",
  "Peletizadora/Naranja",
  "Ph-Metro",
  "Ph-Metro 2",
  "Ph-Metro 3",
  "Picador/Triturador",
  "Picadora De Materiales En Acero Inoxidable",
  "Pipeteador Recargable",
  "Pirolizador",
  "Plancha De Calentamiento Con Agitación",
  "Plancha De Calentamiento Con Agitación 2",
  "Plancha De Calentamiento Con Agitación 3",
  "Plancha De Calentamiento Con Agitación 4",
  "Plancha De Calentamiento Con Agitación 5",
  "Plancha De Calentamiento Con Agitación 6",
  "Plancha De Calentamiento Con Agitación 7",
  "Plancha De Calentamiento Con Agitación 8",
  "Plancha De Calentamiento Con Agitación 9",
  "Plancha De Calentamiento Con Agitación 10",
  "Plancha De Calentamiento Con Agitación 11",
  "Purificador De Agua",
  "Rallador De Yuca Con Motor",
  "Rack De Batería",
  "Reactor",
  "Reactor Con Agitación",
  "Reactor Multiproposito",
  "Pirólisis",
  "Refractómetro Digital",
  "Refractómetro Digital 2",
  "Regulador De Voltaje",
  "Regulador Eléctrico Con Elevador",
  "Reómetro Modular",
  "Sistema Canopy",
  "Sistema De Biogás Doméstico",
  "Sistema De Calentamiento De Agua Con Control Pid Y Bomba",
  "Sistema De Sensores Respirométricos 6 Mixi",
  "Sistema De Sensores Respirométricos 6 Mixi 2",
  "Sistema De Recuperación De Almidón Y Mucílagos De Ñame",
  "Sistema FTIR",
  "Tanque De Afrecho Cónico Construido En Acero Inoxidable",
  "Tanque De Alimentación Para Recirculación Y Almacenamiento De Almidón Con Sistema De Agitación",
  "Tanque De Mezclado De Soluciones De Glucosa En Acero Inoxidable",
  "Tanque Recolector De La Picadora En Acero Inoxidable",
  "Tanque Recolector De Lavadora En Acero Inoxidable",
  "Tanque Sedimentos En Tres Compartimentos En Acero Inoxidable",
  "Termo Reactor",
  "Texturómetro",
  "Unidad De DSC Set Line",
  "Unidad De Extrusión De Almidones Kecon",
  "Unidad De Fermentación - Módulo 1",
  "Unidad De Fermentación - Módulo 2",
  "Unidad De Secado Tipo Spray Vibrasec Sas",
  "Unidad Extrusión De Bioplásticos Bausano",
  "Unidad Neutralizadora Scrubber",
  "Unidad UPS",
  "Ups Del HPLC",
  "Base Del HPLC",
  "Compartimiento De Columna Del HPLC",
  "CPU Del Computador Del HPLC",
  "Detector Del HPLC",
  "Impresora Del HPLC",
  "Monitor Del HPLC",
  "Mouse Del HPLC",
  "Teclado",
  "Zaranda",
  "Zaranda 2"
]


def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def enviar_correo(destinatario, codigo):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    message = Mail(
        from_email='pades.reservas.laboratorios@gmail.com',
        to_emails=destinatario,
        subject='Código secreto para eliminar tu reserva',
        html_content=f'<p>Tu código para eliminar la reserva es:</p><h2>{codigo}</h2>'
    )
    sg.send(message)

def get_db_connection():
    return psycopg2.connect(DB_URL)

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, equipo, inicio, fin, usuario FROM reservas ORDER BY inicio')
    reservas = cur.fetchall()
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
        observaciones = request.form.get('observaciones', '')
        codigo = generar_codigo()

        inicio_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        fin_dt = inicio_dt + timedelta(hours=duracion_horas)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM reservas
            WHERE equipo = %s
            AND (%s < fin AND %s > inicio)
        """, (equipo, fin_dt, inicio_dt))
        conflicto = cur.fetchone()
        if conflicto:
            conn.close()
            return render_template("error.html", mensaje="⚠️ Ya existe una reserva para ese equipo en ese periodo.")

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

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT equipo, inicio, fin, usuario FROM reservas ORDER BY equipo, inicio")
    registros = cur.fetchall()
    conn.close()

    reservas_por_equipo = {}
    for equipo, inicio, fin, usuario in registros:
        reservas_por_equipo.setdefault(equipo, []).append((inicio, fin, usuario))

    return render_template('reservar.html', equipos=EQUIPOS_LISTA, reservas_por_equipo=reservas_por_equipo)

@app.route('/eliminar/<int:reserva_id>', methods=['POST'])
def eliminar_reserva(reserva_id):
    codigo = request.form['codigo'].strip().upper()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT codigo FROM reservas WHERE id = %s', (reserva_id,))
    resultado = cur.fetchone()

    if resultado and resultado[0].strip().upper() == codigo:
        cur.execute('DELETE FROM reservas WHERE id = %s', (reserva_id,))
        conn.commit()
        mensaje = "✅ Reserva eliminada exitosamente."
    else:
        mensaje = "❌ Código incorrecto. No puedes eliminar esta reserva."

    conn.close()
    return render_template("error.html", mensaje=mensaje)

@app.route('/reservas')
def ver_reservas():
    filtro_equipo = request.args.get('equipo')
    filtro_usuario = request.args.get('usuario')
    filtro_fecha = request.args.get('fecha')

    query = """
        SELECT id, equipo,
               TO_CHAR(inicio, 'YYYY-MM-DD HH24:MI'),
               TO_CHAR(fin, 'YYYY-MM-DD HH24:MI'),
               usuario
        FROM reservas
        WHERE TRUE
    """
    params = []

    if filtro_equipo:
        query += " AND equipo ILIKE %s"
        params.append(f"%{filtro_equipo}%")
    if filtro_usuario:
        query += " AND usuario ILIKE %s"
        params.append(f"%{filtro_usuario}%")
    if filtro_fecha:
        query += " AND CAST(inicio AS DATE) = %s"
        params.append(filtro_fecha)

    query += " ORDER BY inicio"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    reservas = cur.fetchall()
    conn.close()

    return render_template("ver_reservas.html", reservas=reservas)

@app.route('/descargar', methods=['GET', 'POST'])
def descargar():
    if request.method == 'POST':
        password = request.form.get('password')
        if not password or password.strip() != "P4D3SADMIN#*":
            return render_template("error.html", mensaje="❌ Contraseña incorrecta para descargar.")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, equipo, inicio, fin, usuario, observaciones FROM reservas ORDER BY inicio")
        rows = cur.fetchall()
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Equipo', 'Inicio', 'Fin', 'Usuario', 'Observaciones'])
        for row in rows:
            writer.writerow(row)

        output.seek(0)
        return Response(
            output,
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment; filename=reservas.csv"}
        )

    return render_template("descargar.html")

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password.strip() == "P4D3SADMIN#*":
            session['admin'] = True  # ⚠️ Activa sesión admin
            return redirect('/admin')
        else:
            return render_template("error.html", mensaje="❌ Contraseña incorrecta.")
    return render_template("admin_login.html")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if not password or password.strip() != "P4D3SADMIN#*":
            return render_template("error.html", mensaje="❌ Contraseña incorrecta.")
        session['admin'] = True  # activa modo admin
        return redirect('/admin')

    if not session.get('admin'):
        return render_template("admin_login.html")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, equipo, inicio, fin, usuario FROM reservas ORDER BY inicio")
    reservas = cur.fetchall()
    conn.close()
    return render_template("ver_reservas.html", reservas=reservas, admin=True)

@app.route('/admin/eliminar/<int:reserva_id>', methods=['POST'])
def admin_eliminar_reserva(reserva_id):
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM reservas WHERE id = %s', (reserva_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/reservas')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)