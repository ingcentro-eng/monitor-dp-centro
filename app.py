import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import io

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL Y ESTILO BI ENTERPRISE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Monitor DP - Zona Centro & Norte", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Estilos CSS de grado industrial (Tema Executive Dark Slate)
st.markdown('''
<style>
    /* Estructura Base */
    .main {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header Principal Ejecutivo */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
        padding: 1.6rem 2rem;
        border-radius: 16px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        margin-bottom: 1.5rem;
        border-left: 6px solid #0284c7;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .hero-title {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.75rem !important;
        margin: 0 !important;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #94a3b8 !important;
        font-size: 0.88rem !important;
        margin-top: 0.35rem !important;
        margin-bottom: 0 !important;
    }
    .status-pill {
        background: rgba(2, 132, 199, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #38bdf8;
        padding: 0.4rem 0.9rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Contenedor de Filtros */
    .filter-panel {
        background-color: #ffffff;
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
    }

    /* Tarjetas de Métricas */
    .kpi-card {
        background-color: #ffffff;
        padding: 1.2rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        text-align: center;
        transition: all 0.25s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.08);
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.4rem;
    }
    .kpi-val {
        font-size: 2.2rem;
        font-weight: 900;
        line-height: 1;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: #64748b;
        margin-top: 0.35rem;
        font-weight: 500;
    }

    /* Variantes de Color SLA */
    .kpi-vencido { border-left: 5px solid #dc2626; }
    .kpi-vencido .kpi-label { color: #dc2626; }
    .kpi-vencido .kpi-val { color: #991b1b; }

    .kpi-limite { border-left: 5px solid #d97706; }
    .kpi-limite .kpi-label { color: #d97706; }
    .kpi-limite .kpi-val { color: #92400e; }

    .kpi-tiempo { border-left: 5px solid #16a34a; }
    .kpi-tiempo .kpi-label { color: #16a34a; }
    .kpi-tiempo .kpi-val { color: #166534; }

    .kpi-clientes { border-left: 5px solid #0284c7; }
    .kpi-clientes .kpi-label { color: #0284c7; }
    .kpi-clientes .kpi-val { color: #075985; }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }
</style>
''', unsafe_allow_html=True)

# ---------------------------------------------------------
# MAPEO MAESTRO DE CIRCUITOS Y ZONAS
# ---------------------------------------------------------
MAPEO_CIRCUITOS = {
    'IMA 1 13.2 KV': 'CENTRO',
    'CAJAMARCA 2 CT 3': 'CENTRO',
    'CTO RURAL 13.2 KV SUB ROVIRA 34.5 KV': 'CENTRO',
    'CAJAMARCA 2 CT 2': 'CENTRO',
    'VENADILLO 2 13.2 KV': 'NORTE',
    'PAYANDE 2 13.2 KV': 'CENTRO',
    'SAN JORGE 5 13.2 KV': 'CENTRO',
    'PAPAYO 7 13.2 KV': 'CENTRO',
    'CTO URBANO 13.2 KV SUB ROVIRA 34.5 KV': 'CENTRO',
    'PASTALES 13.2 KV': 'CENTRO',
    'LA VEGA 13.2 KV': 'CENTRO',
    'BRISAS 3 13.2 KV': 'CENTRO',
    'SAN JUAN 13.2 KV': 'CENTRO',
    'BRISAS 2 13.2 KV': 'CENTRO',
    'PAPAYO 9 13.2 KV': 'CENTRO',
    'IBAGUE 13.2 KV': 'CENTRO',
    'SAN JORGE 1 13.2 KV': 'CENTRO',
    'MARIQUITA 4 13.2 KV': 'NORTE',
    'ANZOATEGUI 13.2 KV': 'NORTE',
    'HONDA 2 13.2 KV': 'NORTE',
    'EL TABLAZO 13.2 KV': 'NORTE',
    'PALOCABILDO 3 13.2 KV': 'NORTE',
    'JUNIN 13.2 KV': 'NORTE',
    'HERVEO 2 13.2 KV': 'NORTE',
    'LIBANO 3 13.2 KV': 'NORTE',
    'SIMON BOLIVAR 1 13.2 KV': 'CENTRO',
    'LERIDA 3 13.2 KV': 'NORTE',
    'MARIQUITA 1 13.2 KV': 'NORTE',
    'LIBANO 5 13.2 KV': 'NORTE',
    'LIBANO 2 13.2 KV': 'NORTE',
    'FRESNO 2 13.2 KV': 'NORTE',
    'PAPAYO 2 13.2 KV': 'CENTRO',
    'PAPAYO 6 13.2 KV': 'CENTRO',
    'SAN JORGE 4 13.2 KV': 'CENTRO',
    'RURAL 13.2 KV': 'CENTRO',
    'PAPAYO 4 13.2 KV': 'CENTRO',
    'URBANO 13.2 KV': 'CENTRO',
    'ALVARADO 13.2 KV': 'CENTRO',
    'LERIDA 1 13.2 KV': 'NORTE',
    'SANTA ISABEL 13.2 KV': 'NORTE',
    'GUAYABAL 3 13.2 KV': 'NORTE',
    'EL SALTO CTO 1 13.2 kVNORTE': 'NORTE',
    'EL SALTO CTO 1 13.2 KV': 'NORTE',
    'PALOCABILDO 2 13.2 KV': 'NORTE',
    'LIBANO 4 13.2 KV': 'NORTE',
    'AMBALEMA 1 13.2 KV': 'NORTE',
    'MARIQUITA 3 13.2 KV': 'NORTE',
    'REFUGIO 2 13.2 KV': 'NORTE',
    'SAN JORGE 2 13.2 KV': 'CENTRO',
    'LIBANO 1 13.2 KV': 'NORTE',
    'VERDESOL 13.2 KV': 'CENTRO',
    'PIEDRAS 13.2 KV': 'CENTRO',
    'PICALEÑA 1 13.2 KV': 'CENTRO',
    'FRESNO 3 13.2 KV': 'NORTE',
    'SAN JORGE 6 13.2 KV': 'CENTRO',
    'SAN JORGE 3 13.2 KV': 'CENTRO',
    'PAPAYO 3 13.2 KV': 'CENTRO',
    'CAJAMARCA 2 13.2 KV': 'CENTRO',
    'SIMON BOLIVAR 2 13.2 KV': 'CENTRO',
    'PAYANDE 1 13.2 KV': 'CENTRO',
    'PAPAYO 8 13.2 KV': 'CENTRO',
    'PAPAYO 5 13.2 KV': 'CENTRO',
    'AMBALEMA 3 13.2 KV': 'NORTE',
    'TOPACIO 13.2 KV': 'CENTRO',
    'VERGEL 4 13.2 KV': 'CENTRO',
    'VERGEL 5 13.2 KV': 'CENTRO',
    'VERGEL 1 13.2 KV': 'CENTRO',
    'CALDAS VIEJO 13.2 KV': 'CENTRO',
    'ARBOLEDA 2 13.2 KV': 'CENTRO',
    'PICALEÑA 2 13.2 KV': 'CENTRO',
    'LA MIEL 3 13.2 KV': 'CENTRO',
    'ARBOLEDA 3 13.2 KV': 'CENTRO',
    'EL SALTO CTO 3 A 13,2 kVNORTE': 'NORTE',
    'EL SALTO CTO 3 A 13.2 KV': 'NORTE',
    'VERGEL 3 13.2 KV': 'CENTRO',
    'BRISAS 1 13.2 KV': 'CENTRO',
    'VERGEL 2 13.2 KV': 'CENTRO',
    'LERIDA 5 13.2 KV': 'NORTE',
    'PAPAYO 10 13.2 KV': 'CENTRO',
    'GUAYABAL 2 13.2 KV': 'NORTE',
    'EL SALTO CTO 2 13.2 kVNORTE': 'NORTE',
    'EL SALTO CTO 2 13.2 KV': 'NORTE',
    'ENEA 34.5 KV': 'NORTE',
    'LETRAS 1 13.2 KV': 'NORTE',
    'ENLACE CASA MONEDA 34.5 KV SUB MIROLINDO 230 KV': 'CENTRO',
    'VENTANA 34.5 KV': 'CENTRO',
    'MARIQUITA 2 13.2 KV': 'NORTE',
    'LERIDA 2 13.2 KV': 'NORTE',
    'ROVIRA 34.5 KV': 'CENTRO',
    'PAPAYO 11 13.2 KV': 'CENTRO',
    'PAPAYO 1 13.2 KV': 'CENTRO',
    'PALOCABILDO 1 13.2 KV': 'NORTE',
    'GUAYABAL 1 13.2 KV': 'NORTE',
    'RIO RECIO 1 34.5 KV': 'CENTRO',
    'RIO RECIO 34.5 KV': 'NORTE',
    'SALADO 34.5 KV': 'CENTRO',
    'RIO RECIO 2 34.5 KV': 'CENTRO',
    'CAJAMARCA 1 13.2 KV': 'CENTRO',
    'FATEXTOL 34.5 KV': 'CENTRO',
    'LA MIEL 1 13.2 KV': 'CENTRO',
    'AMBALEMA 2 13.2 KV': 'CENTRO',
    'BUENOS AIRES 13.2 KV': 'CENTRO',
    'VENADILLO 1 13.2 KV': 'NORTE',
    'PAPAYO 34.5 KV': 'CENTRO',
    'BRISAS 34.5 KV': 'NORTE',
    'HERVEO 1 13.2 KV': 'NORTE',
    'FRESNO 1 13.2 KV': 'NORTE',
    'SAN JORGE 34.5 KV': 'CENTRO',
    'CTO SAN JORGE 34.5 KV SUB BRISAS 115 KV': 'CENTRO',
    'VERGEL 1 34.5 KV': 'CENTRO',
    'MIROLINDO 1 34.5 KV': 'CENTRO',
    'HONDA 3 13.2 KV': 'NORTE',
    'LA MIEL 2 13.2 KV': 'CENTRO',
    'LERIDA 4 13.2 KV': 'NORTE',
    'ENLACE SAN FELIPE 34.5 KV SUB MARIQUITA 115': 'NORTE',
    'MIROLINDO 34.5 KV': 'CENTRO',
    'ALEGRIAS 34.5 KV': 'NORTE',
    'BOQUERON 1 13.2 KV': 'CENTRO',
    'ANGULO 1 13.2 KV': 'NORTE',
    'PUERTO VIEJO CTO 2 13.2 KV': 'NORTE',
    'REFUGIO 1 13.2 KV': 'NORTE',
    'KAPPA 34.5 KV': 'CENTRO',
    'GUAMO 34.5 KV': 'CENTRO',
    'FLANDES 1 34.5 KV': 'CENTRO',
    'ESPINAL 34.5 KV': 'CENTRO',
    'ESPINAL 2 34.5 KV': 'CENTRO',
    'AMBALEMA 34.5 KV': 'NORTE',
    'SALDAÑA 2 13.2 KV': 'CENTRO',
    'SAN ANTONIO 2 13.2 KV': 'CENTRO',
    'PARQUE 13.2 KV': 'CENTRO',
    'CASA MONEDA 34.5 KV': 'CENTRO',
    'PUERTO VIEJO AMBALEMA 34.5 KV': 'CENTRO',
    'SANTA ISABEL 34.5 KV': 'NORTE',
    'ECOPETROL 34.5 KV': 'NORTE',
    'FRESNO 4 13.2 KV': 'NORTE',
    'SAN FELIPE 34.5 KV': 'NORTE',
    'ARRIEROS CTO 3': 'NORTE',
    'FRESNO 34.5 KV': 'NORTE',
    'VERGEL 2 34.5 KV': 'CENTRO',
    'MARIQUITA 34.5 KV': 'NORTE',
    'GUAYABAL 34.5 KV': 'NORTE',
    'SALDANA 34.5 KV': 'CENTRO',
    'PURIFICACION 34.5 KV': 'CENTRO',
    'LERIDA 34.5 KV': 'NORTE',
    'LIBANO 34.5 KV': 'NORTE',
    'ARRIEROS CTO 2': 'NORTE',
    'ARRIEROS CTO 1': 'NORTE',
    'CTO CAJAMARCA 2': 'CENTRO',
    'PUERTO VIEJO CTO 3 13.2 KV': 'NORTE',
    'ARRIEROS LIBANO 34.5 kV': 'NORTE',
    'CAJAMARCA 2 - CAJAMARCA 34.5 kV': 'CENTRO',
    'CHAPETON 34.5 KV': 'CENTRO',
    'CTO GUALANDAY': 'CENTRO',
    'FIBRA TOLIMA 34.5 KV': 'CENTRO',
    'SALADO 1 - ALVARADO 34.5 KV': 'CENTRO',
    'SALADO 2 - ALVARADO 34.5 KV': 'CENTRO',
    'VENADILLO 1 34.5 kV': 'CENTRO',
    'VENADILLO 2 34.5 kV': 'CENTRO'
}

# ---------------------------------------------------------
# ENCABEZADO PRINCIPAL
# ---------------------------------------------------------
st.markdown('''
<div class="hero-banner">
    <div>
        <h1 class="hero-title">⚡ Monitor de Daños Pendientes (DP) — Control Operativo</h1>
        <p class="hero-subtitle">Plataforma de Control y ANS de Mantenimiento &nbsp;|&nbsp; <b>SLA Urbano:</b> ≤ 1 día &nbsp;•&nbsp; <b>SLA Rural:</b> ≤ 3 días</p>
    </div>
    <div style="margin-top: 10px;">
        <span class="status-pill">● MONITOREO ACTIVO</span>
    </div>
</div>
''', unsafe_allow_html=True)

# ---------------------------------------------------------
# CARGA Y FUENTE DE DATOS
# ---------------------------------------------------------
archivo_por_defecto = "Navegador de incidentes_01_10_2026 06_15_57.320.xlsx"
if not os.path.exists(archivo_por_defecto):
    archivo_por_defecto = "Base_DP.xlsx"

# Configuración en Barra Lateral
with st.sidebar:
    st.image("https://img.icons8.com/color/96/electricity.png", width=60)
    st.title("Centro de Control")
    st.markdown("---")
    archivo_subido = st.file_uploader("📂 Cargar reporte del día (Excel)", type=["xlsx", "xls"])
    st.markdown("---")
    st.caption("<b>Parámetros de Control:</b><br>• Sector Urbano: Límite 1 día<br>• Sector Rural: Límite 3 días", unsafe_allow_html=True)

if archivo_subido is not None:
    archivo_a_usar = archivo_subido
elif os.path.exists(archivo_por_defecto):
    archivo_a_usar = archivo_por_defecto
    st.success(f"✅ Repositorio base activo (`{archivo_por_defecto}`).")
else:
    archivo_a_usar = None
    st.info("👋 Para iniciar, carga un archivo Excel de WFM en la barra lateral.")

if archivo_a_usar is not None:
    try:
        # LECTURA DE ENCABEZADOS Y DATOS (CONVERSIÓN SEGURA A TEXTO)
        if hasattr(archivo_a_usar, 'seek'):
            archivo_a_usar.seek(0)
            
        df_temp = pd.read_excel(archivo_a_usar, header=None, nrows=15)
        header_idx = 5
        for i in range(len(df_temp)):
            fila = [str(c).lower() for c in df_temp.iloc[i].tolist()]
            if any('identificaci' in c for c in fila) and any('instrucci' in c for c in fila):
                header_idx = i
                break
        
        if hasattr(archivo_a_usar, 'seek'):
            archivo_a_usar.seek(0)
            
        df = pd.read_excel(archivo_a_usar, header=header_idx)
        
        # 1. LIMPIAR Y DEDUPLICAR COLUMNAS DESDE LA CARGA INICIAL
        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.duplicated()].copy()
        
        # PARSEO DE FECHAS Y DÍAS SIN SERVICIO
        if 'Fecha de creación' in df.columns:
            df['Fecha_Calculo'] = pd.to_datetime(df['Fecha de creación'], errors='coerce')
        else:
            fecha_col = [c for c in df.columns if 'fecha' in c.lower() and 'creaci' in c.lower()]
            df['Fecha_Calculo'] = pd.to_datetime(df[fecha_col[0]], errors='coerce') if fecha_col else pd.NaT

        hoy = pd.Timestamp.now().normalize()
        df['Días Sin Servicio'] = (hoy - df['Fecha_Calculo']).dt.days.fillna(0).astype(int)
        
        # CLASIFICACIÓN SECTOR URBANO / RURAL
        def clasificar_sector(direccion):
            if pd.isna(direccion) or direccion is None:
                return 'URBANO'
            dir_upper = str(direccion).upper()
            rurales = ['VDA', 'VEREDA', 'FCA', 'FINCA', 'CORREGIMIENTO']
            return 'RURAL' if any(kw in dir_upper for kw in rurales) else 'URBANO'
            
        dir_col = [c for c in df.columns if 'direcci' in c.lower()]
        df['Tipo de Sector'] = df[dir_col[0]].apply(clasificar_sector) if dir_col else 'URBANO'
        
        # --- SELECCIÓN DE LA COLUMNA AFECTADOS PARA CLIENTES SIN SERVICIO ---
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
        # ASIGNACIÓN DE ZONA SEGÚN CIRCUITO
        # ---------------------------------------------------------
        def obtener_circuito(row):
            if 'Circuito normal' in row and pd.notna(row['Circuito normal']) and str(row['Circuito normal']).strip() != '':
                return str(row['Circuito normal']).strip()
            elif 'Circuito actual' in row and pd.notna(row['Circuito actual']) and str(row['Circuito actual']).strip() != '':
                return str(row['Circuito actual']).strip()
            return 'SIN CIRCUITO'

        df['Circuito_Nombre'] = df.apply(obtener_circuito, axis=1)

        def asignar_zona(circuito):
            if circuito in MAPEO_CIRCUITOS:
                return MAPEO_CIRCUITOS[circuito]
            
            # Intento de emparejamiento parcial por nombre
            circ_upper = circuito.upper()
            for key, val in MAPEO_CIRCUITOS.items():
                if key in circ_upper or circ_upper in key:
                    return val
            
            return '⚠️ ZONA NO ENCONTRADA (REVISIÓN MANUAL)'

        df['Zona'] = df['Circuito_Nombre'].apply(asignar_zona)

        # HOMOGENEIZACIÓN DE LA COLUMNA SUBESTACIÓN
        sub_col = [c for c in df.columns if 'subestaci' in c.lower()]
        if sub_col and sub_col[0] != 'Subestación':
            df['Subestación'] = df[sub_col[0]].fillna('SIN SUBESTACIÓN').astype(str)
        elif 'Subestación' in df.columns:
            df['Subestación'] = df['Subestación'].fillna('SIN SUBESTACIÓN').astype(str)
        else:
            df['Subestación'] = 'SIN SUBESTACIÓN'
            
        subestaciones_disponibles = sorted(df['Subestación'].unique())
        zonas_disponibles = sorted(df['Zona'].unique())

        # ---------------------------------------------------------
        # PANEL DE FILTROS AVANZADOS MULTINIVEL
        # ---------------------------------------------------------
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)

        f1, f2, f3, f4, f5 = st.columns([1.8, 2.2, 1.3, 1.3, 0.9])
        
        with f1:
            zonas_seleccionadas = st.multiselect(
                "🗺️ Zona:",
                options=zonas_disponibles,
                default=zonas_disponibles
            )
        with f2:
            subestaciones_seleccionadas = st.multiselect(
                "📍 Subestación:",
                options=subestaciones_disponibles,
                default=subestaciones_disponibles
            )
        with f3:
            sectores_seleccionados = st.multiselect(
                "🏠 Sector:",
                options=['URBANO', 'RURAL'],
                default=['URBANO', 'RURAL']
            )
        with f4:
            sla_seleccionados = st.multiselect(
                "🚨 Estado SLA:",
                options=['Vencido', 'Al Límite', 'A Tiempo'],
                default=['Vencido', 'Al Límite', 'A Tiempo']
            )
        with f5:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Restablecer", use_container_width=True):
                zonas_seleccionadas = zonas_disponibles
                subestaciones_seleccionadas = subestaciones_disponibles
                sectores_seleccionados = ['URBANO', 'RURAL']
                sla_seleccionados = ['Vencido', 'Al Límite', 'A Tiempo']
        st.markdown('</div>', unsafe_allow_html=True)

        # APLICACIÓN DE FILTROS COMBINADOS Y REAJUSTE DE ÍNDICE
        df_filtrado = df[
            (df['Zona'].isin(zonas_seleccionadas)) &
            (df['Subestación'].isin(subestaciones_seleccionadas)) &
            (df['Tipo de Sector'].isin(sectores_seleccionados)) &
            (df['Estado SLA'].isin(sla_seleccionados))
        ].copy().reset_index(drop=True)

        # NOTIFICACIÓN SI HAY CIRCUITO NO ENCONTRADO
        desconocidos = df_filtrado[df_filtrado['Zona'] == '⚠️ ZONA NO ENCONTRADA (REVISIÓN MANUAL)']
        if not desconocidos.empty:
            circs_unk = desconocidos['Circuito_Nombre'].unique()
            st.warning(f"⚠️ **Atención:** Se detectaron **{len(desconocidos)}** incidentes con circuitos no mapeados ({', '.join(circs_unk)}). Revisa el archivo cargado para verificar manualmente.")

        if df_filtrado.empty:
            st.warning("⚠️ No existen registros que coincidan con la combinación de filtros seleccionada.")
            st.stop()

        # PALETA OFICIAL
        colores = {'A Tiempo': '#00B050', 'Al Límite': '#FFC000', 'Vencido': '#C00000'}

        # ---------------------------------------------------------
        # PESTAÑAS OPERATIVAS (TAB STRUCTURE)
        # ---------------------------------------------------------
        tab1, tab2, tab3 = st.tabs(["🚨 Control de Despacho & SLA", "📊 Análisis por Subestación y Zona", "📥 Exportación de Planilla"])

        # =========================================================
        # TAB 1: DESPACHO Y SLA (VISTA PRINCIPAL)
        # =========================================================
        with tab1:
            # MÉTRICAS EJECUTIVAS
            vencidos_cnt = int((df_filtrado['Estado SLA'] == 'Vencido').sum())
            limite_cnt = int((df_filtrado['Estado SLA'] == 'Al Límite').sum())
            tiempo_cnt = int((df_filtrado['Estado SLA'] == 'A Tiempo').sum())
            total_cnt = len(df_filtrado)
            total_afectados = int(df_filtrado['Clientes Sin Servicio'].sum())

            pct_vencidos = round((vencidos_cnt / total_cnt) * 100, 1) if total_cnt > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'''
                <div class="kpi-card kpi-vencido">
                    <div class="kpi-label">🔴 Vencidos SLA</div>
                    <div class="kpi-val">{vencidos_cnt}</div>
                    <div class="kpi-sub">{pct_vencidos}% del total acumulado</div>
                </div>
                ''', unsafe_allow_html=True)

            with m2:
                st.markdown(f'''
                <div class="kpi-card kpi-limite">
                    <div class="kpi-label">🟡 Al Límite SLA</div>
                    <div class="kpi-val">{limite_cnt}</div>
                    <div class="kpi-sub">Atención prioritaria hoy</div>
                </div>
                ''', unsafe_allow_html=True)

            with m3:
                st.markdown(f'''
                <div class="kpi-card kpi-tiempo">
                    <div class="kpi-label">🟢 A Tiempo SLA</div>
                    <div class="kpi-val">{tiempo_cnt}</div>
                    <div class="kpi-sub">Dentro de ventana ANS</div>
                </div>
                ''', unsafe_allow_html=True)

            with m4:
                st.markdown(f'''
                <div class="kpi-card kpi-clientes">
                    <div class="kpi-label">👥 Clientes Sin Servicio</div>
                    <div class="kpi-val">{total_afectados:,}</div>
                    <div class="kpi-sub">Afectación en tiempo real</div>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # GRÁFICAS DE GESTIÓN
            c1, c2 = st.columns([2, 3])
            with c1:
                st.subheader("📊 Distribución de Estado SLA")
                conteo = df_filtrado['Estado SLA'].value_counts().reset_index()
                conteo.columns = ['Estado SLA', 'count']
                
                fig1 = px.pie(
                    conteo, names='Estado SLA', values='count', 
                    color='Estado SLA', color_discrete_map=colores,
                    hole=0.55
                )
                fig1.update_traces(
                    textposition='inside', 
                    textinfo='percent+value',
                    marker=dict(line=dict(color='#ffffff', width=2))
                )
                fig1.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), 
                    showlegend=True, 
                    height=320,
                    annotations=[dict(text=f'<b>{total_cnt}</b><br>DP Total', x=0.5, y=0.5, font_size=16, showarrow=False)]
                )
                st.plotly_chart(fig1, use_container_width=True)

            with c2:
                st.subheader("🚨 Top 10 DP Críticos (Más Días Sin Servicio)")
                vencidos = df_filtrado.sort_values(by=['Días Sin Servicio', 'Clientes Sin Servicio'], ascending=[False, False]).head(10).reset_index(drop=True)
                if not vencidos.empty:
                    hover_cols = [c for c in ['Zona', 'Subestación', 'Clientes Sin Servicio', 'Dirección del dispositivo', 'Tipo de Sector', 'Cuadrillas'] if c in vencidos.columns]
                    id_col = [c for c in vencidos.columns if 'identificaci' in c.lower()]
                    y_col = id_col[0] if id_col else 'Identificación'

                    fig2 = px.bar(
                        vencidos, x='Días Sin Servicio', y=y_col, 
                        hover_data=hover_cols,
                        orientation='h', color='Estado SLA', color_discrete_map=colores,
                        text='Días Sin Servicio'
                    )
                    fig2.update_traces(textposition='outside')
                    fig2.update_layout(
                        yaxis={'categoryorder': 'total ascending', 'title': 'ID Incidente'},
                        xaxis={'title': 'Días Sin Servicio'},
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=320
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("✨ No hay incidentes en el corte actual.")

            # TABLA DE DETALLE OPERATIVO
            st.subheader("📋 Detalle Operativo para Despacho")
            st.caption("Ordenado automáticamente por criticidad: Vencidos ➔ Días Transcurridos ➔ Clientes Afectados")

            columnas_deseadas = [
                'Identificación', 'Zona', 'Subestación', 'Circuito_Nombre', 'Instrucción', 
                'Dirección del dispositivo', 'Tipo de Sector', 
                'Clientes Sin Servicio', 'Días Sin Servicio', 
                'Estado SLA', 'Cuadrillas'
            ]
            
            cols_finales = list(dict.fromkeys([c for c in columnas_deseadas if c in df_filtrado.columns]))

            def resaltar_filas(val):
                if val == 'Vencido': return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
                if val == 'Al Límite': return 'background-color: #fef3c7; color: #92400e; font-weight: bold;'
                if val == 'A Tiempo': return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
                return ''

            # Orden de prioridad
            orden_map = {'Vencido': 1, 'Al Límite': 2, 'A Tiempo': 3}
            df_display = df_filtrado.copy()
            df_display['prioridad'] = df_display['Estado SLA'].map(orden_map)
            df_display = df_display.sort_values(
                by=['prioridad', 'Días Sin Servicio', 'Clientes Sin Servicio'], 
                ascending=[True, False, False]
            ).drop(columns=['prioridad'])

            df_display_clean = df_display[cols_finales].reset_index(drop=True)

            try:
                st.dataframe(
                    df_display_clean.style.map(resaltar_filas, subset=['Estado SLA']),
                    use_container_width=True,
                    height=420
                )
            except AttributeError:
                st.dataframe(
                    df_display_clean.style.applymap(resaltar_filas, subset=['Estado SLA']),
                    use_container_width=True,
                    height=420
                )

        # =========================================================
        # TAB 2: ANÁLISIS POR SUBESTACIÓN Y ZONA
        # =========================================================
        with tab2:
            st.subheader("📊 Matriz de Cumplimiento por Subestación y Zona")
            
            resumen_sub = df_filtrado.groupby(['Zona', 'Subestación'], as_index=False).agg(
                Total_DP=('Identificación', 'count'),
                Vencidos=('Estado SLA', lambda x: (x == 'Vencido').sum()),
                Al_Limite=('Estado SLA', lambda x: (x == 'Al Límite').sum()),
                A_Tiempo=('Estado SLA', lambda x: (x == 'A Tiempo').sum()),
                Clientes_Afectados=('Clientes Sin Servicio', 'sum')
            )

            resumen_sub['% Cumplimiento SLA'] = ((resumen_sub['A_Tiempo'] / resumen_sub['Total_DP']) * 100).round(1)

            s1, s2 = st.columns([3, 2])
            with s1:
                fig_sub = px.bar(
                    resumen_sub, x='Subestación', y=['Vencidos', 'Al_Limite', 'A_Tiempo'],
                    title="Comparativo de Estado SLA por Subestación",
                    color_discrete_sequence=['#C00000', '#FFC000', '#00B050'],
                    barmode='stack', hover_data=['Zona']
                )
                fig_sub.update_layout(height=380, xaxis_title="Subestación", yaxis_title="Cantidad de DP")
                st.plotly_chart(fig_sub, use_container_width=True)

            with s2:
                st.markdown("##### Resumen Agregado")
                st.dataframe(
                    resumen_sub[['Zona', 'Subestación', 'Total_DP', 'Vencidos', '% Cumplimiento SLA', 'Clientes_Afectados']].sort_values(by=['Zona', 'Vencidos'], ascending=[True, False]).reset_index(drop=True),
                    use_container_width=True,
                    height=340
                )

        # =========================================================
        # TAB 3: EXPORTACIÓN DE DATOS
        # =========================================================
        with tab3:
            st.subheader("📥 Exportar Planilla de Despacho")
            st.markdown("Descarga la lista con el filtro actual aplicado para enviar a los líderes de cuadrilla o imprimir.")

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_display_clean.to_excel(writer, index=False, sheet_name='Reporte_DP_Centro_Norte')
            
            st.download_button(
                label="📥 Descargar Planilla en Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"Planilla_Despacho_DP_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False
            )

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}. Asegúrate de que sea el archivo exportado de WFM.")
