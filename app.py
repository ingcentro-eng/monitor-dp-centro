import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(page_title="Monitor DP - Zona Centro", layout="wide")
st.title("⚡ Monitor de Daños Pendientes (DP) - Zona Centro")
st.markdown("Visualización de tiempos de atención (SLA: Urbano = 1 día | Rural = 3 días)")

# 1. Definir el archivo por defecto que subiste a GitHub
archivo_por_defecto = "Base_DP.xlsx"

# 2. Dejar la opción de cargar uno nuevo de forma opcional
archivo_subido = st.file_uploader("Actualizar reporte del día (Opcional)", type=["xlsx", "xls"])

# 3. Lógica para decidir qué archivo usar
if archivo_subido is not None:
    archivo_a_usar = archivo_subido
elif os.path.exists(archivo_por_defecto):
    archivo_a_usar = archivo_por_defecto
    st.success(f"Datos cargados automáticamente desde: {archivo_por_defecto}")
else:
    archivo_a_usar = None
    st.warning("No se encontró el archivo base. Por favor carga el Excel manualmente.")

if archivo_a_usar is not None:
    try:
        # LECTURA INTELIGENTE DE ENCABEZADOS (Blindada contra valores float/NaN)
        if hasattr(archivo_a_usar, 'seek'):
            archivo_a_usar.seek(0)
            
        df_temp = pd.read_excel(archivo_a_usar, header=None, nrows=15)
        header_idx = 5
        for i in range(len(df_temp)):
            # Convertimos explícitamente cada celda a String puro
            fila = [str(c).lower() for c in df_temp.iloc[i].tolist()]
            if any('identificaci' in c for c in fila) and any('instrucci' in c for c in fila):
                header_idx = i
                break
        
        if hasattr(archivo_a_usar, 'seek'):
            archivo_a_usar.seek(0)
            
        df = pd.read_excel(archivo_a_usar, header=header_idx)
        df.columns = df.columns.astype(str).str.strip()
        
        # Parseo de fechas y cálculo de días
        if 'Fecha de creación' in df.columns:
            df['Fecha_Calculo'] = pd.to_datetime(df['Fecha de creación'], errors='coerce')
        else:
            fecha_col = [c for c in df.columns if 'fecha' in c.lower() and 'creaci' in c.lower()]
            df['Fecha_Calculo'] = pd.to_datetime(df[fecha_col[0]], errors='coerce') if fecha_col else pd.NaT

        hoy = pd.Timestamp.now().normalize()
        df['Días Sin Servicio'] = (hoy - df['Fecha_Calculo']).dt.days.fillna(0).astype(int)
        
        # Clasificación Urbano/Rural basándonos en la dirección
        def clasificar_sector(direccion):
            if pd.isna(direccion) or direccion is None:
                return 'URBANO'
            dir_upper = str(direccion).upper()
            rurales = ['VDA', 'VEREDA', 'FCA', 'FINCA', 'CORREGIMIENTO']
            return 'RURAL' if any(kw in dir_upper for kw in rurales) else 'URBANO'
            
        dir_col = [c for c in df.columns if 'direcci' in c.lower()]
        df['Tipo de Sector'] = df[dir_col[0]].apply(clasificar_sector) if dir_col else 'URBANO'
        
        # Mapeo seguro de la columna de clientes sin servicio (Afectados / Clientes no restaurados)
        afectados_col = None
        for col_candidate in ['Clientes no restaurados', 'Afectados', 'Clientes no restaurados.']:
            if col_candidate in df.columns:
                afectados_col = col_candidate
                break

        if afectados_col:
            df['Clientes Sin Servicio'] = pd.to_numeric(df[afectados_col], errors='coerce').fillna(0).astype(int)
        else:
            df['Clientes Sin Servicio'] = 0

        # Evaluación del ANS (SLA) para control de vencimientos
        def estado_sla(row):
            limite = 3 if row['Tipo de Sector'] == 'RURAL' else 1
            if row['Días Sin Servicio'] > limite:
                return 'Vencido'
            elif row['Días Sin Servicio'] == limite:
                return 'Al Límite'
            else:
                return 'A Tiempo'
                
        df['Estado SLA'] = df.apply(estado_sla, axis=1)

        # --- FILTRO MULTISELECCIÓN POR SUBESTACIÓN ---
        sub_col = [c for c in df.columns if 'subestaci' in c.lower()]
        if sub_col:
            df['Subestación_Clean'] = df[sub_col[0]].fillna('SIN SUBESTACION').astype(str)
            subestaciones_disponibles = sorted(df['Subestación_Clean'].unique())
        else:
            subestaciones_disponibles = []

        if subestaciones_disponibles:
            subestaciones_seleccionadas = st.multiselect(
                "📍 Filtrar por Subestación (puedes elegir una o varias):",
                options=subestaciones_disponibles,
                default=subestaciones_disponibles
            )
            if subestaciones_seleccionadas:
                df_filtrado = df[df['Subestación_Clean'].isin(subestaciones_seleccionadas)]
            else:
                st.warning("Por favor selecciona al menos una subestación.")
                st.stop()
        else:
            df_filtrado = df

        # Paleta de colores visual para rápida identificación
        colores = {'A Tiempo': '#00B050', 'Al Límite': '#FFC000', 'Vencido': '#C00000'}
        
        # Tarjetas de métricas operativas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔴 Vencidos", len(df_filtrado[df_filtrado['Estado SLA'] == 'Vencido']))
        col2.metric("🟡 Al Límite", len(df_filtrado[df_filtrado['Estado SLA'] == 'Al Límite']))
        col3.metric("🟢 A Tiempo", len(df_filtrado[df_filtrado['Estado SLA'] == 'A Tiempo']))
        col4.metric("👥 Clientes Sin Servicio", int(df_filtrado['Clientes Sin Servicio'].sum()))
        
        st.markdown("---")
        
        # Gráficas de gestión
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribución General")
            conteo = df_filtrado['Estado SLA'].value_counts().reset_index()
            conteo.columns = ['Estado SLA', 'count']
            fig1 = px.pie(conteo, names='Estado SLA', values='count', color='Estado SLA', color_discrete_map=colores)
            st.plotly_chart(fig1, use_container_width=True)
            
        with c2:
            st.subheader("Top DP Críticos con más días")
            vencidos = df_filtrado.sort_values('Días Sin Servicio', ascending=False).head(10)
            if not vencidos.empty:
                hover_cols = [c for c in ['Subestación', 'Clientes Sin Servicio', 'Dirección del dispositivo', 'Tipo de Sector'] if c in vencidos.columns]
                id_col = [c for c in vencidos.columns if 'identificaci' in c.lower()]
                y_col = id_col[0] if id_col else 'Identificación'
                
                fig2 = px.bar(vencidos, x='Días Sin Servicio', y=y_col, 
                              hover_data=hover_cols,
                              orientation='h', color='Estado SLA', color_discrete_map=colores)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay incidentes vencidos registrados.")
            
        # Tabla de datos con INC, Subestación y Clientes Sin Servicio
        st.subheader("Detalle Operativo para Despacho")
        columnas_deseadas = [
            'Identificación', 'Subestación', 'Instrucción', 
            'Dirección del dispositivo', 'Tipo de Sector', 
            'Clientes Sin Servicio', 'Días Sin Servicio', 
            'Estado SLA', 'Cuadrillas'
        ]
        
        cols_finales = [c for c in columnas_deseadas if c in df_filtrado.columns]

        def resaltar_filas(val):
            color = '#ffcccc' if val == 'Vencido' else '#ffffcc' if val == 'Al Límite' else '#ccffcc'
            return f'background-color: {color}'
            
        try:
            st.dataframe(df_filtrado[cols_finales].style.map(resaltar_filas, subset=['Estado SLA']))
        except AttributeError:
            st.dataframe(df_filtrado[cols_finales].style.applymap(resaltar_filas, subset=['Estado SLA']))
        
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}. Asegúrate de que el formato de WFM sea el correcto.")
