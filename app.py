import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Monitor DP - Zona Centro", layout="wide")
st.title("⚡ Monitor de Daños Pendientes (DP) - Zona Centro")
st.markdown("Visualización de tiempos de atención (SLA: Urbano = 1 día | Rural = 3 días)")

# Carga del archivo Excel
archivo_subido = st.file_uploader("Carga el archivo 'Navegador de incidentes'", type=["xlsx", "xls"])

if archivo_subido is not None:
    try:
        # Leer el Excel saltando las filas de filtro superior
        df = pd.read_excel(archivo_subido, sheet_name=0, header=5)
        
        # Parseo de fechas y cálculo de días
        df['Fecha_Calculo'] = pd.to_datetime(df['Fecha de creación'])
        hoy = pd.Timestamp.now().normalize()
        df['Días Sin Servicio'] = (hoy - df['Fecha_Calculo']).dt.days
        
        # Clasificación Urbano/Rural basándonos en la dirección
        def clasificar_sector(direccion):
            if pd.isna(direccion): return 'URBANO'
            dir_upper = str(direccion).upper()
            rurales = ['VDA', 'VEREDA', 'FCA', 'FINCA', 'CORREGIMIENTO']
            return 'RURAL' if any(kw in dir_upper for kw in rurales) else 'URBANO'
            
        df['Tipo de Sector'] = df['Dirección del dispositivo'].apply(clasificar_sector)
        
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
        
        # Paleta de colores visual para rápida identificación
        colores = {'A Tiempo': '#00B050', 'Al Límite': '#FFC000', 'Vencido': '#C00000'}
        
        # Tarjetas de métricas gerenciales
        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 Vencidos", len(df[df['Estado SLA'] == 'Vencido']))
        col2.metric("🟡 Al Límite", len(df[df['Estado SLA'] == 'Al Límite']))
        col3.metric("🟢 A Tiempo", len(df[df['Estado SLA'] == 'A Tiempo']))
        
        st.markdown("---")
        
        # Gráficas de gestión
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribución General")
            conteo = df['Estado SLA'].value_counts().reset_index()
            fig1 = px.pie(conteo, names='Estado SLA', values='count', color='Estado SLA', color_discrete_map=colores)
            st.plotly_chart(fig1, use_container_width=True)
            
        with c2:
            st.subheader("Top DP Críticos con más días")
            vencidos = df.sort_values('Días Sin Servicio', ascending=False).head(10)
            # Se usa la Identificación (INC) para el eje Y y se añade Subestación en el tooltip
            fig2 = px.bar(vencidos, x='Días Sin Servicio', y='Identificación', 
                          hover_data=['Subestación', 'Dirección del dispositivo', 'Tipo de Sector'],
                          orientation='h', color='Estado SLA', color_discrete_map=colores)
            st.plotly_chart(fig2, use_container_width=True)
            
        # Tabla de datos actualizada con INC y Subestación
        st.subheader("Detalle Operativo")
        columnas = ['Identificación', 'Subestación', 'Instrucción', 'Dirección del dispositivo', 'Tipo de Sector', 'Días Sin Servicio', 'Estado SLA', 'Cuadrillas']
        
        def resaltar_filas(val):
            color = '#ffcccc' if val == 'Vencido' else '#ffffcc' if val == 'Al Límite' else '#ccffcc'
            return f'background-color: {color}'
            
        st.dataframe(df[columnas].style.map(resaltar_filas, subset=['Estado SLA']))
        
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}. Asegúrate de cargar el formato correcto.")