import os
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

from database import conectar


load_dotenv(Path(__file__).with_name(".env"), override=True)
dashboard_api = Blueprint("dashboard_api", __name__, url_prefix="/api/v1")
CEDULA_PATTERN = re.compile(r"^[0-9]{6,20}$")
INCOME_TYPES = {"Deposito", "Transferencia Entrada"}
DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY")


def json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def row_to_dict(row):
    return {key: json_value(value) for key, value in row.items()}


def signed_amount(transaction_type, amount):
    value = float(amount)
    return value if transaction_type in INCOME_TYPES else -value


def mask_account(number):
    number = str(number)
    return f"**** {number[-4:]}" if len(number) > 4 else number


@dashboard_api.before_request
def validate_api_key():
    if request.endpoint == "dashboard_api.health" or request.method == "OPTIONS":
        return None
    if not DASHBOARD_API_KEY:
        return jsonify({"error": "API no configurada", "code": "API_KEY_NOT_CONFIGURED"}), 503
    if request.headers.get("X-API-Key") != DASHBOARD_API_KEY:
        return jsonify({"error": "No autorizado", "code": "UNAUTHORIZED"}), 401


@dashboard_api.after_request
def add_cors_headers(response):
    allowed_origin = os.getenv("DASHBOARD_ORIGIN", "http://localhost:5173")
    origin = request.headers.get("Origin")
    if origin == allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@dashboard_api.route("/health", methods=["GET"])
def health():
    connection = conectar()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT CURRENT_TIMESTAMP AS database_time")
        result = cursor.fetchone()
        return jsonify(
            {
                "status": "ok",
                "bank": {"id": "bank-1", "name": "Banco 1"},
                "database": "connected",
                "database_time": json_value(result["database_time"]),
            }
        )
    finally:
        cursor.close()
        connection.close()


@dashboard_api.route("/dashboard", methods=["POST", "OPTIONS"])
def customer_dashboard():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    cedula = str(payload.get("cedula", "")).strip()
    transaction_limit = payload.get("transaction_limit", 20)

    if not CEDULA_PATTERN.fullmatch(cedula):
        return (
            jsonify(
                {
                    "error": "La cedula debe contener entre 6 y 20 digitos",
                    "code": "INVALID_CEDULA",
                }
            ),
            400,
        )

    try:
        transaction_limit = max(1, min(int(transaction_limit), 100))
    except (TypeError, ValueError):
        return jsonify({"error": "transaction_limit no es valido", "code": "INVALID_LIMIT"}), 400

    connection = conectar()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id_cliente, cedula, nombres, apellidos, correo, telefono
            FROM clientes
            WHERE cedula = %s
            """,
            (cedula,),
        )
        customer = cursor.fetchone()

        if customer is None:
            return (
                jsonify(
                    {
                        "error": "No existe un cliente de Banco 1 con esa cedula",
                        "code": "CUSTOMER_NOT_FOUND",
                    }
                ),
                404,
            )

        customer_id = customer["id_cliente"]

        cursor.execute(
            """
            SELECT
                c.id_cuenta,
                c.numero_cuenta,
                c.tipo_cuenta,
                c.fecha_apertura,
                c.saldo_inicial AS balance,
                c.estado,
                COALESCE(SUM(
                    CASE
                        WHEN t.tipo IN ('Deposito', 'Transferencia Entrada') THEN t.monto
                        ELSE -t.monto
                    END
                ) FILTER (
                    WHERE t.fecha >= DATE_TRUNC('month', CURRENT_DATE)
                ), 0) AS month_change
            FROM cuentas c
            LEFT JOIN transacciones t ON t.id_cuenta = c.id_cuenta
            WHERE c.id_cliente = %s
            GROUP BY c.id_cuenta
            ORDER BY c.fecha_apertura DESC, c.id_cuenta DESC
            """,
            (customer_id,),
        )
        account_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                COALESCE((
                    SELECT SUM(c.saldo_inicial)
                    FROM cuentas c
                    WHERE c.id_cliente = %s AND c.estado = 'Activa'
                ), 0) AS balance,
                COALESCE((
                    SELECT SUM(t.monto)
                    FROM transacciones t
                    INNER JOIN cuentas c ON c.id_cuenta = t.id_cuenta
                    WHERE c.id_cliente = %s
                      AND t.tipo IN ('Deposito', 'Transferencia Entrada')
                      AND t.fecha >= DATE_TRUNC('month', CURRENT_DATE)
                ), 0) AS income,
                COALESCE((
                    SELECT SUM(t.monto)
                    FROM transacciones t
                    INNER JOIN cuentas c ON c.id_cuenta = t.id_cuenta
                    WHERE c.id_cliente = %s
                      AND t.tipo IN ('Retiro', 'Transferencia Salida')
                      AND t.fecha >= DATE_TRUNC('month', CURRENT_DATE)
                ), 0) AS expenses
            """,
            (customer_id, customer_id, customer_id),
        )
        summary_row = cursor.fetchone()

        cursor.execute(
            """
            WITH days AS (
                SELECT GENERATE_SERIES(
                    CURRENT_DATE - INTERVAL '6 days',
                    CURRENT_DATE,
                    INTERVAL '1 day'
                )::date AS activity_date
            )
            SELECT
                d.activity_date,
                COALESCE(SUM(
                    CASE
                        WHEN t.tipo IN ('Deposito', 'Transferencia Entrada') THEN t.monto
                        ELSE -t.monto
                    END
                ), 0) AS net_amount,
                COUNT(t.id_transaccion) AS transaction_count
            FROM days d
            LEFT JOIN transacciones t
                ON t.fecha = d.activity_date
                AND t.id_cuenta IN (
                    SELECT id_cuenta FROM cuentas WHERE id_cliente = %s
                )
            GROUP BY d.activity_date
            ORDER BY d.activity_date
            """,
            (customer_id,),
        )
        activity = [row_to_dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT
                t.id_transaccion,
                t.tipo,
                t.monto,
                t.fecha,
                t.descripcion,
                c.id_cuenta,
                c.numero_cuenta
            FROM transacciones t
            INNER JOIN cuentas c ON c.id_cuenta = t.id_cuenta
            WHERE c.id_cliente = %s
            ORDER BY t.fecha DESC, t.id_transaccion DESC
            LIMIT %s
            """,
            (customer_id, transaction_limit),
        )
        transaction_rows = cursor.fetchall()

        accounts = []
        for row in account_rows:
            account = row_to_dict(row)
            account["masked_number"] = mask_account(account["numero_cuenta"])
            accounts.append(account)

        transactions = []
        for row in transaction_rows:
            transaction = row_to_dict(row)
            transaction["direction"] = (
                "income" if transaction["tipo"] in INCOME_TYPES else "expense"
            )
            transaction["signed_amount"] = signed_amount(
                transaction["tipo"], transaction["monto"]
            )
            transaction["masked_account"] = mask_account(transaction["numero_cuenta"])
            transactions.append(transaction)

        balance = float(summary_row["balance"])
        income = float(summary_row["income"])
        expenses = float(summary_row["expenses"])

        return jsonify(
            {
                "bank": {
                    "id": "bank-1",
                    "name": os.getenv("BANK_NAME", "Banco 1"),
                    "status": "connected",
                },
                "customer": row_to_dict(customer),
                "summary": {
                    "currency": os.getenv("BANK_CURRENCY", "USD"),
                    "balance": balance,
                    "income_this_month": income,
                    "expenses_this_month": expenses,
                    "net_savings_this_month": income - expenses,
                    "active_accounts": sum(
                        1 for account in accounts if account["estado"] == "Activa"
                    ),
                },
                "accounts": accounts,
                "daily_activity": activity,
                "recent_transactions": transactions,
                "generated_at": datetime.now().astimezone().isoformat(),
            }
        )
    finally:
        cursor.close()
        connection.close()
