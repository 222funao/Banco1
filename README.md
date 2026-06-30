# Banco 1

Aplicacion Flask del primer banco, conectada a PostgreSQL en Neon y preparada
para entregar la informacion financiera que consume el dashboard.

## Configuracion

1. Crea un entorno virtual de Python.
2. Instala las dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copia `.env.example` como `.env` y configura `DATABASE_URL`.
4. Ejecuta `banco_completo.sql` una vez en Neon para crear las tablas.
5. Inicia el banco:

   ```powershell
   python app.py
   ```

La aplicacion se publica por defecto en `http://localhost:5001`.

## API para el dashboard

### Estado del banco

```http
GET /api/v1/health
```

### Informacion financiera de un cliente

```http
POST /api/v1/dashboard
Content-Type: application/json

{
  "cedula": "0102030405",
  "transaction_limit": 20
}
```

La respuesta incluye:

- Datos del banco y del cliente.
- Balance, ingresos, gastos y ahorro neto del mes.
- Cuentas activas e inactivas con numeros enmascarados.
- Actividad diaria de los ultimos siete dias.
- Movimientos recientes con monto y direccion.

El emparejamiento se realiza exclusivamente mediante la columna unica
`clientes.cedula`. Para proteger los datos, la cedula se envia en el cuerpo de
una solicitud `POST` y no en la URL.

## Seguridad de integracion

- `.env` esta excluido de Git.
- `DASHBOARD_ORIGIN` limita el origen web autorizado.
- Si se define `DASHBOARD_API_KEY`, el dashboard debe enviar ese valor en el
  encabezado `X-API-Key`.
- En produccion se recomienda activar `DASHBOARD_API_KEY` y rotar la clave de
  Neon que haya sido compartida fuera del entorno privado.
