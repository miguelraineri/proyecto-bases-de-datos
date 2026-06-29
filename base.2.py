import streamlit as st
import psycopg2
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
from decimal import Decimal


# CONEXIONES

SUPABASE_URL = "postgresql://postgres.ufhulczizgqjkuepuiwp:fhjdshfjshdfg@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
MONGO_URL = "mongodb+srv://migueraineri_db_user:3g6LXc76QjjP3FwX@cluster0.0eyuz0j.mongodb.net/"


def conectar_sql():
    return psycopg2.connect(SUPABASE_URL)


def conectar_mongo():
    cliente = MongoClient(MONGO_URL)
    return cliente["respaldo_logistica"]


# Funciones basicas

def convertir(valor):
    if isinstance(valor, Decimal):
        return float(valor)

    if isinstance(valor, datetime):
        return valor.isoformat()

    if isinstance(valor, dict):
        return {k: convertir(v) for k, v in valor.items()}

    if isinstance(valor, list):
        return [convertir(v) for v in valor]

    return valor


def guardar_mongo(coleccion_nombre, documento):
    try:
        db = conectar_mongo()
        coleccion = db[coleccion_nombre]

        documento["fecha_registro_mongo"] = datetime.now().isoformat()

        coleccion.insert_one(convertir(documento))

    except Exception as error:
        st.warning("No se pudo guardar el registro en MongoDB.")
        st.warning(error)


def select_sql(query, datos=()):
    conexion = conectar_sql()
    cursor = conexion.cursor()

    cursor.execute(query, datos)

    resultado = cursor.fetchall()
    columnas = [desc[0] for desc in cursor.description]

    cursor.close()
    conexion.close()

    return pd.DataFrame(resultado, columns=columnas)


def mostrar_tabla(df):
    if len(df) == 0:
        st.info("No hay datos para mostrar.")
    else:
        st.dataframe(df, use_container_width=True)


# Crear empresa

def crear_empresa():
    st.header("Crear empresa")

    nombre = st.text_input("Nombre empresa")
    rut = st.text_input("RUT")
    tipo_empresa = st.text_input("Tipo empresa", value="Cliente")

    if st.button("Guardar empresa"):
        if nombre == "" or rut == "":
            st.error("Debes completar nombre y RUT.")
            return

        conexion = conectar_sql()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                INSERT INTO "Empresa" (nombre, rut, tipo_empresa)
                VALUES (%s, %s, %s)
                RETURNING id_empresa;
            """, (nombre, rut, tipo_empresa))

            id_empresa = cursor.fetchone()[0]

            conexion.commit()
            cursor.close()
            conexion.close()

            guardar_mongo("empresas", {
                "id_empresa_sql": id_empresa,
                "nombre": nombre,
                "rut": rut,
                "tipo_empresa": tipo_empresa
            })

            st.success(f"Empresa guardada correctamente. ID: {id_empresa}")

        except Exception as error:
            conexion.rollback()
            cursor.close()
            conexion.close()

            st.error("Error al guardar empresa.")
            st.error(error)

    st.subheader("Empresas registradas")

    empresas = select_sql("""
        SELECT id_empresa, nombre, rut, tipo_empresa
        FROM "Empresa"
        ORDER BY id_empresa DESC;
    """)

    mostrar_tabla(empresas)


# crear envio y carga

def crear_envio():
    st.header("Crear envío con carga")

    empresas = select_sql("""
        SELECT id_empresa, nombre
        FROM "Empresa"
        ORDER BY id_empresa;
    """)

    rutas = select_sql("""
        SELECT id_ruta, nombre, distancia_km
        FROM "Ruta"
        ORDER BY id_ruta;
    """)

    medios = select_sql("""
        SELECT id_medio, tipo, patente
        FROM "Medio Transporte"
        ORDER BY id_medio;
    """)

    estados = select_sql("""
        SELECT id_estado, estado
        FROM "Estado Envio"
        ORDER BY id_estado;
    """)

    tipos_carga = select_sql("""
        SELECT id_tipo_carga, nombre
        FROM "Tipo Carga"
        ORDER BY id_tipo_carga;
    """)

    if len(empresas) < 2:
        st.warning("Debes tener al menos dos empresas.")
        return

    if len(rutas) == 0:
        st.warning("Debes tener al menos una ruta.")
        return

    if len(medios) == 0:
        st.warning("Debes tener al menos un medio de transporte.")
        return

    if len(estados) == 0:
        st.warning("Debes tener al menos un estado de envío.")
        return

    if len(tipos_carga) == 0:
        st.warning("Debes tener al menos un tipo de carga.")
        return

    st.subheader("Datos del envío")

    empresa_origen = st.selectbox(
        "Empresa origen",
        [f"{fila.id_empresa} - {fila.nombre}" for fila in empresas.itertuples()]
    )

    empresa_destino = st.selectbox(
        "Empresa destino",
        [f"{fila.id_empresa} - {fila.nombre}" for fila in empresas.itertuples()]
    )

    ruta = st.selectbox(
        "Ruta",
        [f"{fila.id_ruta} | {fila.nombre} | {fila.distancia_km} km" for fila in rutas.itertuples()]
    )

    medio = st.selectbox(
        "Medio de transporte",
        [f"{fila.id_medio} - {fila.tipo} - {fila.patente}" for fila in medios.itertuples()]
    )

    estado = st.selectbox(
        "Estado",
        [f"{fila.id_estado} - {fila.estado}" for fila in estados.itertuples()]
    )

    codigo = st.text_input(
        "Código envío",
        value=f"ENV-{datetime.now().strftime('%H%M%S')}"
    )

    prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
    valor_total = st.number_input("Valor declarado total", min_value=0.0, step=1000.0)

    st.subheader("Datos de la carga")

    tipo_carga = st.selectbox(
        "Tipo de carga",
        [f"{fila.id_tipo_carga} - {fila.nombre}" for fila in tipos_carga.itertuples()]
    )

    descripcion = st.text_input("Descripción producto")
    cantidad = st.number_input("Cantidad unidades", min_value=1, step=1)
    peso = st.number_input("Peso kg", min_value=0.0, step=1.0)
    volumen = st.number_input("Volumen", min_value=0.0, step=1.0)
    valor_carga = st.number_input("Valor carga", min_value=0.0, step=1000.0)

    id_origen = int(empresa_origen.split(" - ")[0])
    id_destino = int(empresa_destino.split(" - ")[0])

    id_ruta = int(ruta.split(" | ")[0])
    distancia_km = float(ruta.split(" | ")[2].replace(" km", ""))

    id_medio = int(medio.split(" - ")[0])
    id_estado = int(estado.split(" - ")[0])
    id_tipo_carga = int(tipo_carga.split(" - ")[0])

    toneladas_km = (peso / 1000) * distancia_km

    st.info(f"Toneladas-kilómetro estimadas: {round(toneladas_km, 2)}")

    if st.button("Guardar envío"):
        if id_origen == id_destino:
            st.error("La empresa origen y destino no pueden ser iguales.")
            return

        if descripcion == "":
            st.error("Debes escribir la descripción del producto.")
            return

        conexion = conectar_sql()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                INSERT INTO "Envio" (
                    codigo_envio,
                    fecha_creacion,
                    fecha_programada,
                    fecha_entrega_real,
                    prioridad,
                    valor_declarado_total,
                    id_empresa_origen,
                    id_empresa_destino,
                    id_estado,
                    id_ruta,
                    id_medio
                )
                VALUES (%s, NOW(), NOW(), NULL, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_envio;
            """, (
                codigo,
                prioridad,
                valor_total,
                id_origen,
                id_destino,
                id_estado,
                id_ruta,
                id_medio
            ))

            id_envio = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO "Carga" (
                    descripcion_producto,
                    cantidad_unidades,
                    peso,
                    volumen,
                    valor_declarado,
                    id_envio,
                    id_tipo_carga
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_carga;
            """, (
                descripcion,
                cantidad,
                peso,
                volumen,
                valor_carga,
                id_envio,
                id_tipo_carga
            ))

            id_carga = cursor.fetchone()[0]

            conexion.commit()
            cursor.close()
            conexion.close()

            guardar_mongo("envios", {
                "id_envio_sql": id_envio,
                "codigo_envio": codigo,
                "fecha_creacion": datetime.now().isoformat(),
                "prioridad": prioridad,
                "valor_declarado_total": valor_total,
                "id_empresa_origen": id_origen,
                "id_empresa_destino": id_destino,
                "id_estado": id_estado,
                "id_ruta": id_ruta,
                "id_medio": id_medio,

                "carga": {
                    "id_carga_sql": id_carga,
                    "descripcion_producto": descripcion,
                    "cantidad_unidades": cantidad,
                    "peso_kg": peso,
                    "volumen": volumen,
                    "valor_declarado": valor_carga,
                    "id_tipo_carga": id_tipo_carga
                },

                "indicador_ods_9_1_2": {
                    "distancia_km": distancia_km,
                    "toneladas_kilometro": toneladas_km
                }
            })

            st.success("Envío y carga guardados correctamente.")
            st.write("ID envío:", id_envio)
            st.write("ID carga:", id_carga)
            st.write("Toneladas-kilómetro:", round(toneladas_km, 2))

        except Exception as error:
            conexion.rollback()
            cursor.close()
            conexion.close()

            st.error("Error al guardar el envío.")
            st.error(error)


# Ver envios

def ver_envios():
    st.header("Ver envíos")


    medios = select_sql("""
        SELECT DISTINCT tipo
        FROM "Medio Transporte"
        ORDER BY tipo;
    """)

    opciones = ["Todos"] + list(medios["tipo"])

    filtro = st.selectbox("", opciones)

    if filtro == "Todos":
        condicion = ""
        datos = ()
    else:
        condicion = "WHERE mt.tipo = %s"
        datos = (filtro,)

    consulta = f"""
        SELECT 
            e.id_envio,
            e.codigo_envio,
            emp_o.nombre AS empresa_origen,
            emp_d.nombre AS empresa_destino,
            est.estado AS estado_envio,
            r.nombre AS ruta,
            r.distancia_km,
            mt.tipo AS medio_transporte,
            c.id_carga,
            c.descripcion_producto,
            c.cantidad_unidades,
            c.peso AS peso_kg,
            ROUND((c.peso / 1000.0) * r.distancia_km, 2) AS toneladas_kilometro
        FROM "Envio" e
        JOIN "Empresa" emp_o
            ON e.id_empresa_origen = emp_o.id_empresa
        JOIN "Empresa" emp_d
            ON e.id_empresa_destino = emp_d.id_empresa
        JOIN "Estado Envio" est
            ON e.id_estado = est.id_estado
        JOIN "Ruta" r
            ON e.id_ruta = r.id_ruta
        JOIN "Medio Transporte" mt
            ON e.id_medio = mt.id_medio
        JOIN "Carga" c
            ON e.id_envio = c.id_envio
        {condicion}
        ORDER BY e.id_envio DESC;
    """

    envios = select_sql(consulta, datos)

    mostrar_tabla(envios)


# configuracion y iniciación sitio 

st.set_page_config(
    page_title="proyecto",
    page_icon="",
    layout="wide"
)



menu = st.sidebar.radio(
    "Menú",
    [
        "Crear empresa",
        "Crear envío con carga",
        "Ver envíos"
    ]
)

try:
    if menu == "Crear empresa":
        crear_empresa()

    elif menu == "Crear envío con carga":
        crear_envio()

    elif menu == "Ver envíos":
        ver_envios()

except Exception as error:
    st.error("Ocurrió un error.")
    st.error(error)