import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Monitor DP - Zona Centro", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS (DISEÑO PROFESIONAL EXECUTIVE)
# ---------------------------------------------------------
st.markdown('''
<style>
    /* Fondo general */
    .main {
        background-color: #f8fafc;
    }
    
    /* Banner de encabezado estilo dashboard corporativo */
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 1.8rem 2rem;
        border-radius: 16px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        margin-bottom: 1.5rem;
        border-left: 6px solid #0284c7;
    }
    .header-banner h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
        margin: 0 !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .header-banner p {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0 !important;
    }

    /* Contenedor de Filtros */
    .filter-card {
        background-color: #ffffff;
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
    }

    /* Tarjetas de Métricas Ejecutivas */
    .metric-card {
        background-color: #ffffff;
        padding: 1.25rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 900;
        line-height: 1;
    }

    /* Colores y bordes de tarjetas */
    .card-vencido { border-left: 5px solid #dc2626; }
    .card-vencido .metric-title { color: #dc2626; }
    .card-vencido .metric-value { color: #991b1b; }

    .card-limite { border-left: 5px solid #d97706; }
    .card-limite .metric-title { color: #d97706; }
    .card-limite .metric-value { color: #92400e; }

    .card-tiempo { border-left: 5px solid #16a34a; }
    .card-tiempo .metric-title { color: #16a34a; }
    .card-tiempo .metric-value { color: #166534; }

    .card-afectados { border-left: 5px solid #0284c7; }
    .card-afectados .metric-title { color: #0284c7; }
    .card-afectados .metric-value { color: #075985; }

    /* Ajustes generales de tablas */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
</style>
''', unsafe_allow_html=True)

# ---------------------------------------------------------
# ENCABEZADO
# ---------------------------------------------------------
st.markdown('''
<div class="header-banner">
    <h1>⚡ Monitor de Daños Pendientes (DP) - Zona Centro</h1>
    <p>Gestión operativa de tiempos de atención y control de SLA &nbsp;|&nbsp; <b>SLA Urbano:</b> ≤ 1 día &nbsp;•&nbsp; <b>SLA Rural:</b> ≤ 3 días</p>
</div>
''', unsafe_allow_html=True)

# 1. Archivo por defecto o carga opcional
archivo_por_defecto = "Base_DP.xlsx"
archivo_subido = st.file_uploader("📂 Actualizar reporte del día (Opcional - Excel WFM)", type=["xlsx", "xls"])

# 2. Selección de fuente de datos
if archivo_subido is not None:
    archivo_a_usar = archivo_subido
elif os.path.exists(archivo_por_defecto):
    archivo_a_usar = archivo_por_defecto
    st.success(f"✅ Datos cargados automáticamente desde el repositorio base (`{archivo_por_defecto}`).")
else:
    archivo_a_usar = None
    st.info("👋 Por favor carga el archivo de Excel para iniciar el monitoreo.")

if archivo_a_usar is not None:
    try:
        # LECTURA INTELIGENTE DE ENCABEZADOS DE WFM
        if hasattr(archivo_a_usar, 'seek'):
            archivo_a_usar.seek(0)
            
        df_temp = pd.read_excel(archivo_a_usar, header=None, nrows=15)
        header_idx = 5
        for i in range(len(df_temp)):
            fila = df_temp.iloc[i].astype(str).str.lower().tolist()
            if any('identificaci' in c for c in fila) and any('instrucci' in c for c in fila):
                header_idx = i
                break
        
        if hasattr(archivo_a_usar, 'seek'):
            archivo_a_usar.seek(0)
            
        df = pd.read_excel(archivo_a_usar, header=header_idx)
        
        # PARSEO DE FECHAS Y DÍAS SIN SERVICIO
        df['Fecha_Calculo'] = pd.to_datetime(df['Fecha de creación'], errors='coerce')
        hoy = pd.Timestamp.now().normalize()
        df['Días Sin Servicio'] = (hoy - df['Fecha_Calculo']).dt.days.fillna(0).astype(int)
        
        # CLASIFICACIÓN SECTOR URBANO / RURAL
        def clasificar_sector(direccion):
            if pd.isna(direccion): return 'URBANO'
            dir_upper = str(direccion).upper()
            rurales = ['VDA', 'VEREDA', 'FCA', 'FINCA', 'CORREGIMIENTO']
            return 'RURAL' if any(kw in dir_upper for kw in rurales) else 'URBANO'
            
        df['Tipo de Sector'] = df['Dirección del dispositivo'].apply(clasificar_sector) if 'Dirección del dispositivo' in df.columns else 'URBANO'
        
        # DETERMINAR COLUMNA DE CLIENTES SIN SERVICIO (AFECTADOS)
        if 'Afectados' in df.columns:
            df['Clientes Sin Servicio'] = pd.to_numeric(df['Afectados'], errors='coerce').fillna(0).astype(int)
        elif 'Clientes no restaurados' in df.columns:
            df['Clientes Sin Servicio'] = pd.to_numeric(df['Clientes no restaurados'], errors='coerce').fillna(0).astype(int)
        else:
            df['Clientes Sin Servicio'] = 0

        # EVALUACIÓN DE ANS (SLA)
        def estado_sla(row):
            limite = 3 if row['Tipo de Sector'] == 'RURAL' else 1
            if row['Días Sin Servicio'] > limite:
                return 'Vencido'
            elif row['Días Sin Servicio'] == limite:
                return 'Al Límite'
            else:
                return 'A Tiempo'
                
        df['Estado SLA'] = df.apply(estado_sla, axis=1)
        
        # ---------------------------------------------------------
        # FILTRO MULTISELECCIÓN PROFESIONAL POR SUBESTACIÓN
        # ---------------------------------------------------------
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        subestaciones_disponibles = sorted(df['Subestación'].dropna().astype(str).unique()) if 'Subestación' in df.columns else []
        
        f1, f2 = st.columns([3.5, 1])
        with f1:
            subestaciones_seleccionadas = st.multiselect(
                "📍 Filtrar por Subestación (Selecciona una o varias):",
                options=subestaciones_disponibles,
                default=subestaciones_disponibles,
                help="Puedes borrar o añadir subestaciones para actualizar el tablero de control."
            )
        with f2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Ver Todas", use_container_width=True):
                subestaciones_seleccionadas = subestaciones_disponibles
        st.markdown('</div>', unsafe_allow_html=True)

        # Aplicar filtro
        if subestaciones_seleccionadas:
            df_filtrado = df[df['Subestación'].astype(str).isin(subestaciones_seleccionadas)]
        else:
            st.warning("⚠️ Por favor selecciona al menos una subestación para visualizar los datos.")
            st.stop()

        # ---------------------------------------------------------
        # TARJETAS DE MÉTRICAS OPERATIVAS (SLA + CLIENTES AFECTADOS)
        # ---------------------------------------------------------
        vencidos_cnt = len(df_filtrado[df_filtrado['Estado SLA'] == 'Vencido'])
        limite_cnt = len(df_filtrado[df_filtrado['Estado SLA'] == 'Al Límite'])
        tiempo_cnt = len(df_filtrado[df_filtrado['Estado SLA'] == 'A Tiempo'])
        total_afectados = df_filtrado['Clientes Sin Servicio'].sum()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'''
            <div class="metric-card card-vencido">
                <div class="metric-title">🔴 Vencidos SLA</div>
                <div class="metric-value">{vencidos_cnt}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with m2:
            st.markdown(f'''
            <div class="metric-card card-limite">
                <div class="metric-title">🟡 Al Límite SLA</div>
                <div class="metric-value">{limite_cnt}</div>
            </div>
            ''', unsafe_allow_html=True)

        with m3:
            st.markdown(f'''
            <div class="metric-card card-tiempo">
                <div class="metric-title">🟢 A Tiempo SLA</div>
                <div class="metric-value">{tiempo_cnt}</div>
            </div>
            ''', unsafe_allow_html=True)

        with m4:
            st.markdown(f'''
            <div class="metric-card card-afectados">
                <div class="metric-title">👥 Clientes Sin Servicio</div>
                <div class="metric-value">{total_afectados:,}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # PALETA DE COLORES OFICIAL
        colores = {'A Tiempo': '#00B050', 'Al Límite': '#FFC000', 'Vencido': '#C00000'}

        # ---------------------------------------------------------
        # GRÁFICAS DE GESTIÓN
        # ---------------------------------------------------------
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 Distribución General SLA")
            conteo = df_filtrado['Estado SLA'].value_counts().reset_index()
            conteo.columns = ['Estado SLA', 'Cantidad']
            fig1 = px.pie(
                conteo, names='Estado SLA', values='Cantidad', 
                color='Estado SLA', color_discrete_map=colores,
                hole=0.45
            )
            fig1.update_traces(textposition='inside', textinfo='percent+label+value')
            fig1.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True, height=340)
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            st.subheader("🚨 Top 10 DP Críticos (Más Días Sin Servicio)")
            df_vencidos = df_filtrado.sort_values('Días Sin Servicio', ascending=False).head(10)
            if not df_vencidos.empty:
                fig2 = px.bar(
                    df_vencidos, x='Días Sin Servicio', y='Identificación',
                    hover_data=['Subestación', 'Clientes Sin Servicio', 'Dirección del dispositivo', 'Tipo de Sector'],
                    orientation='h', color='Estado SLA', color_discrete_map=colores,
                    text='Días Sin Servicio'
                )
                fig2.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=340,
                    xaxis_title="Días Transcurridos",
                    yaxis_title="ID Incidente"
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("✨ No hay incidentes registrados para las subestaciones seleccionadas.")

        # ---------------------------------------------------------
        # TABLA DE DETALLE OPERATIVO PARA DESPACHO CON CLIENTES
        # ---------------------------------------------------------
        st.subheader("📋 Detalle Operativo para Despacho")
        st.caption(f"Mostrando {len(df_filtrado)} registros ordenados por criticidad")

        # Columnas seleccionadas incluyendo Clientes Sin Servicio
        columnas_mostrar = [
            'Identificación', 'Subestación', 'Instrucción', 
            'Dirección del dispositivo', 'Tipo de Sector', 
            'Clientes Sin Servicio', 'Días Sin Servicio', 
            'Estado SLA', 'Cuadrillas'
        ]
        
        cols_presentes = [c for c in columnas_mostrar if c in df_filtrado.columns]

        # Función de resaltado visual por estado SLA
        def resaltar_filas(val):
            if val == 'Vencido': return 'background-color: #ffcccc; color: #7f1d1d; font-weight: bold;'
            if val == 'Al Límite': return 'background-color: #ffffcc; color: #78350f; font-weight: bold;'
            if val == 'A Tiempo': return 'background-color: #ccffcc; color: #14532d; font-weight: bold;'
            return ''

        # Ordenar por prioridad (Vencidos primero, luego más días, luego más clientes afectados)
        orden_sla = {'Vencido': 1, 'Al Límite': 2, 'A Tiempo': 3}
        df_ordenado = df_filtrado.copy()
        df_ordenado['prioridad_sort'] = df_ordenado['Estado SLA'].map(orden_sla)
        df_ordenado = df_ordenado.sort_values(
            by=['prioridad_sort', 'Días Sin Servicio', 'Clientes Sin Servicio'], 
            ascending=[True, False, False]
        ).drop(columns=['prioridad_sort'])

        # Renderizado compatible con Pandas
        try:
            st.dataframe(
                df_ordenado[cols_presentes].style.map(resaltar_filas, subset=['Estado SLA']),
                use_container_width=True,
                height=450
            )
        except AttributeError:
            st.dataframe(
                df_ordenado[cols_presentes].style.applymap(resaltar_filas, subset=['Estado SLA']),
                use_container_width=True,
                height=450
            )

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}. Asegúrate de que sea el reporte oficial de WFM.")
