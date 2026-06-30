from flask import Flask, render_template, request, redirect
from database import conectar
from dashboard_api import dashboard_api

app = Flask(__name__)
app.register_blueprint(dashboard_api)


# =====================================================
# FUNCION PARA REDIRECCIONAR CON MENSAJE
# =====================================================

def volver(ruta, mensaje):
    return redirect(f"{ruta}?mensaje={mensaje}")


# =====================================================
# CLIENTES
# =====================================================

@app.route('/')
def inicio():
    cedula = request.args.get('cedula')
    mensaje = request.args.get('mensaje')

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if cedula:
        cursor.execute(
            "SELECT * FROM clientes WHERE cedula = %s",
            (cedula,)
        )
    else:
        cursor.execute("SELECT * FROM clientes")

    clientes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('clientes.html', clientes=clientes, mensaje=mensaje)


# =====================================================
# AGREGAR CLIENTE
# =====================================================

@app.route('/agregar_cliente', methods=['POST'])
def agregar_cliente():
    datos = request.form

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        sql = """
        INSERT INTO clientes
        (cedula, nombres, apellidos, fecha_nacimiento, direccion, telefono, correo)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        valores = (
            datos['cedula'],
            datos['nombres'],
            datos['apellidos'],
            datos['fecha_nacimiento'],
            datos['direccion'],
            datos['telefono'],
            datos['correo']
        )

        cursor.execute(sql, valores)
        conexion.commit()
        mensaje = "Cliente registrado correctamente"

    except Exception:
        mensaje = "Error: no se permite registrar clientes con la misma cedula"

    cursor.close()
    conexion.close()

    return volver('/', mensaje)


# =====================================================
# ELIMINAR CLIENTE
# =====================================================

@app.route('/eliminar/<int:id>')
def eliminar(id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id,))
        conexion.commit()
        mensaje = "Cliente eliminado correctamente"
    except Exception:
        mensaje = "No se puede eliminar el cliente porque tiene cuentas o prestamos registrados"

    cursor.close()
    conexion.close()

    return volver('/', mensaje)


# =====================================================
# EDITAR CLIENTE
# =====================================================

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':
        datos = request.form

        try:
            sql = """
            UPDATE clientes
            SET cedula=%s, nombres=%s, apellidos=%s, fecha_nacimiento=%s,
                direccion=%s, telefono=%s, correo=%s
            WHERE id_cliente=%s
            """

            valores = (
                datos['cedula'],
                datos['nombres'],
                datos['apellidos'],
                datos['fecha_nacimiento'],
                datos['direccion'],
                datos['telefono'],
                datos['correo'],
                id
            )

            cursor.execute(sql, valores)
            conexion.commit()
            mensaje = "Cliente actualizado correctamente"
        except Exception:
            mensaje = "Error: cedula duplicada"

        cursor.close()
        conexion.close()
        return volver('/', mensaje)

    cursor.execute("SELECT * FROM clientes WHERE id_cliente=%s", (id,))
    cliente = cursor.fetchone()

    cursor.close()
    conexion.close()

    return render_template('editar.html', cliente=cliente)


# =====================================================
# CUENTAS
# =====================================================

@app.route('/cuentas')
def cuentas():
    numero = request.args.get('numero_cuenta')
    mensaje = request.args.get('mensaje')

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if numero:
        cursor.execute("""
            SELECT c.*, cl.nombres, cl.apellidos
            FROM cuentas c
            INNER JOIN clientes cl ON c.id_cliente = cl.id_cliente
            WHERE c.numero_cuenta=%s
        """, (numero,))
    else:
        cursor.execute("""
            SELECT c.*, cl.nombres, cl.apellidos
            FROM cuentas c
            INNER JOIN clientes cl ON c.id_cliente = cl.id_cliente
        """)

    cuentas = cursor.fetchall()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('cuentas.html', cuentas=cuentas, clientes=clientes, mensaje=mensaje)


# =====================================================
# AGREGAR CUENTA
# =====================================================

@app.route('/agregar_cuenta', methods=['POST'])
def agregar_cuenta():
    datos = request.form
    saldo = float(datos['saldo_inicial'])

    if saldo < 0:
        return volver('/cuentas', 'Error: el saldo inicial no puede ser negativo')

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        sql = """
        INSERT INTO cuentas
        (numero_cuenta, tipo_cuenta, fecha_apertura, saldo_inicial, estado, id_cliente)
        VALUES (%s,%s,%s,%s,%s,%s)
        """

        valores = (
            datos['numero_cuenta'],
            datos['tipo_cuenta'],
            datos['fecha_apertura'],
            datos['saldo_inicial'],
            datos['estado'],
            datos['id_cliente']
        )

        cursor.execute(sql, valores)
        conexion.commit()
        mensaje = "Cuenta creada correctamente"
    except Exception:
        mensaje = "Error: no se permiten cuentas duplicadas"

    cursor.close()
    conexion.close()

    return volver('/cuentas', mensaje)


# =====================================================
# EDITAR CUENTA
# =====================================================

@app.route('/editar_cuenta/<int:id>', methods=['GET', 'POST'])
def editar_cuenta(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':
        datos = request.form
        saldo = float(datos['saldo_inicial'])

        if saldo < 0:
            cursor.close()
            conexion.close()
            return volver('/cuentas', 'Error: el saldo no puede ser negativo')

        try:
            sql = """
            UPDATE cuentas
            SET numero_cuenta=%s, tipo_cuenta=%s, fecha_apertura=%s,
                saldo_inicial=%s, estado=%s
            WHERE id_cuenta=%s
            """

            valores = (
                datos['numero_cuenta'],
                datos['tipo_cuenta'],
                datos['fecha_apertura'],
                datos['saldo_inicial'],
                datos['estado'],
                id
            )

            cursor.execute(sql, valores)
            conexion.commit()
            mensaje = "Cuenta actualizada correctamente"
        except Exception:
            mensaje = "Error: numero de cuenta duplicado"

        cursor.close()
        conexion.close()
        return volver('/cuentas', mensaje)

    cursor.execute("SELECT * FROM cuentas WHERE id_cuenta=%s", (id,))
    cuenta = cursor.fetchone()

    cursor.close()
    conexion.close()

    return render_template('editar_cuenta.html', cuenta=cuenta)


# =====================================================
# CERRAR CUENTA
# =====================================================

@app.route('/cerrar_cuenta/<int:id>')
def cerrar_cuenta(id):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("UPDATE cuentas SET estado='Cerrada' WHERE id_cuenta=%s", (id,))
    conexion.commit()

    cursor.close()
    conexion.close()

    return volver('/cuentas', 'Cuenta cerrada correctamente')


# =====================================================
# TRANSACCIONES
# =====================================================

@app.route('/transacciones')
def transacciones():
    mensaje = request.args.get('mensaje')

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.*, cl.nombres, cl.apellidos
        FROM cuentas c
        INNER JOIN clientes cl ON c.id_cliente = cl.id_cliente
        WHERE c.estado='Activa'
    """)
    cuentas = cursor.fetchall()

    cursor.execute("""
        SELECT t.*, c.numero_cuenta
        FROM transacciones t
        INNER JOIN cuentas c ON t.id_cuenta = c.id_cuenta
        ORDER BY t.id_transaccion DESC
    """)
    transacciones = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('transacciones.html', cuentas=cuentas, transacciones=transacciones, mensaje=mensaje)


@app.route('/deposito', methods=['POST'])
def deposito():
    datos = request.form
    id_cuenta = datos['id_cuenta']
    monto = float(datos['monto'])
    fecha = datos['fecha']

    if monto <= 0:
        return volver('/transacciones', 'Error: no se permiten depositos negativos o en cero')

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "UPDATE cuentas SET saldo_inicial = saldo_inicial + %s WHERE id_cuenta=%s AND estado='Activa'",
        (monto, id_cuenta)
    )

    cursor.execute("""
        INSERT INTO transacciones (id_cuenta, tipo, monto, fecha, descripcion)
        VALUES (%s, 'Deposito', %s, %s, 'Deposito realizado')
    """, (id_cuenta, monto, fecha))

    conexion.commit()

    cursor.close()
    conexion.close()

    return volver('/transacciones', 'Deposito registrado correctamente')


@app.route('/retiro', methods=['POST'])
def retiro():
    datos = request.form
    id_cuenta = datos['id_cuenta']
    monto = float(datos['monto'])
    fecha = datos['fecha']

    if monto <= 0:
        return volver('/transacciones', 'Error: no se permiten retiros negativos o en cero')

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT saldo_inicial FROM cuentas WHERE id_cuenta=%s AND estado='Activa'", (id_cuenta,))
    cuenta = cursor.fetchone()

    if cuenta is None:
        cursor.close()
        conexion.close()
        return volver('/transacciones', 'Error: cuenta no encontrada o cerrada')

    if float(cuenta['saldo_inicial']) < monto:
        cursor.close()
        conexion.close()
        return volver('/transacciones', 'Error: saldo insuficiente')

    cursor.execute(
        "UPDATE cuentas SET saldo_inicial = saldo_inicial - %s WHERE id_cuenta=%s",
        (monto, id_cuenta)
    )

    cursor.execute("""
        INSERT INTO transacciones (id_cuenta, tipo, monto, fecha, descripcion)
        VALUES (%s, 'Retiro', %s, %s, 'Retiro realizado')
    """, (id_cuenta, monto, fecha))

    conexion.commit()

    cursor.close()
    conexion.close()

    return volver('/transacciones', 'Retiro registrado correctamente')


@app.route('/transferencia', methods=['POST'])
def transferencia():
    datos = request.form
    cuenta_origen = datos['cuenta_origen']
    cuenta_destino = datos['cuenta_destino']
    monto = float(datos['monto'])
    fecha = datos['fecha']

    if cuenta_origen == cuenta_destino:
        return volver('/transacciones', 'Error: la cuenta origen y destino no pueden ser iguales')

    if monto <= 0:
        return volver('/transacciones', 'Error: no se permiten transferencias negativas o en cero')

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT saldo_inicial FROM cuentas WHERE id_cuenta=%s AND estado='Activa'", (cuenta_origen,))
    origen = cursor.fetchone()

    cursor.execute("SELECT saldo_inicial FROM cuentas WHERE id_cuenta=%s AND estado='Activa'", (cuenta_destino,))
    destino = cursor.fetchone()

    if origen is None or destino is None:
        cursor.close()
        conexion.close()
        return volver('/transacciones', 'Error: una de las cuentas no existe o esta cerrada')

    if float(origen['saldo_inicial']) < monto:
        cursor.close()
        conexion.close()
        return volver('/transacciones', 'Error: saldo insuficiente para transferir')

    cursor.execute("UPDATE cuentas SET saldo_inicial = saldo_inicial - %s WHERE id_cuenta=%s", (monto, cuenta_origen))
    cursor.execute("UPDATE cuentas SET saldo_inicial = saldo_inicial + %s WHERE id_cuenta=%s", (monto, cuenta_destino))

    cursor.execute("""
        INSERT INTO transacciones (id_cuenta, tipo, monto, fecha, descripcion, id_cuenta_destino)
        VALUES (%s, 'Transferencia Salida', %s, %s, 'Transferencia enviada', %s)
    """, (cuenta_origen, monto, fecha, cuenta_destino))

    cursor.execute("""
        INSERT INTO transacciones (id_cuenta, tipo, monto, fecha, descripcion, id_cuenta_destino)
        VALUES (%s, 'Transferencia Entrada', %s, %s, 'Transferencia recibida', %s)
    """, (cuenta_destino, monto, fecha, cuenta_origen))

    conexion.commit()

    cursor.close()
    conexion.close()

    return volver('/transacciones', 'Transferencia registrada correctamente')


# =====================================================
# PRESTAMOS
# =====================================================

@app.route('/prestamos')
def prestamos():
    mensaje = request.args.get('mensaje')

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.execute("""
        SELECT p.*, cl.nombres, cl.apellidos, cl.cedula
        FROM prestamos p
        INNER JOIN clientes cl ON p.id_cliente = cl.id_cliente
        ORDER BY p.id_prestamo DESC
    """)
    prestamos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('prestamos.html', clientes=clientes, prestamos=prestamos, mensaje=mensaje)


@app.route('/agregar_prestamo', methods=['POST'])
def agregar_prestamo():
    datos = request.form
    monto = float(datos['monto'])
    interes = float(datos['interes'])
    plazo = int(datos['plazo'])

    if monto <= 0 or interes < 0 or plazo <= 0:
        return volver('/prestamos', 'Error: revise monto, interes y plazo')

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO prestamos (id_cliente, monto, interes, plazo, estado)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        datos['id_cliente'],
        datos['monto'],
        datos['interes'],
        datos['plazo'],
        datos['estado']
    ))

    conexion.commit()

    cursor.close()
    conexion.close()

    return volver('/prestamos', 'Prestamo registrado correctamente')


@app.route('/estado_prestamo/<int:id>/<estado>')
def estado_prestamo(id, estado):
    if estado not in ['Pendiente', 'Aprobado', 'Rechazado']:
        return volver('/prestamos', 'Estado no valido')

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("UPDATE prestamos SET estado=%s WHERE id_prestamo=%s", (estado, id))
    conexion.commit()

    cursor.close()
    conexion.close()

    return volver('/prestamos', 'Estado del prestamo actualizado')


# =====================================================
# REPORTES
# =====================================================

@app.route('/reportes')
def reportes():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM clientes")
    clientes_registrados = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM cuentas WHERE estado='Activa'")
    cuentas_activas = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(monto),0) AS total FROM transacciones WHERE tipo='Deposito'")
    total_depositos = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(monto),0) AS total FROM transacciones WHERE tipo='Retiro'")
    total_retiros = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(monto),0) AS total FROM prestamos")
    total_prestamos = cursor.fetchone()['total']

    cursor.execute("""
        SELECT cl.nombres, cl.apellidos, c.numero_cuenta, c.saldo_inicial
        FROM cuentas c
        INNER JOIN clientes cl ON c.id_cliente = cl.id_cliente
        ORDER BY c.saldo_inicial DESC
        LIMIT 5
    """)
    mayores_saldos = cursor.fetchall()

    cursor.execute("""
        SELECT t.*, c.numero_cuenta
        FROM transacciones t
        INNER JOIN cuentas c ON t.id_cuenta = c.id_cuenta
        ORDER BY t.id_transaccion DESC
    """)
    movimientos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'reportes.html',
        clientes_registrados=clientes_registrados,
        cuentas_activas=cuentas_activas,
        total_depositos=total_depositos,
        total_retiros=total_retiros,
        total_prestamos=total_prestamos,
        mayores_saldos=mayores_saldos,
        movimientos=movimientos
    )


# =====================================================
# INICIAR APP
# =====================================================

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(__import__("os").getenv("PORT", "5001")),
        debug=__import__("os").getenv("FLASK_DEBUG", "false").lower() == "true",
    )
