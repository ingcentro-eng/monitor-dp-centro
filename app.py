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
    page_title="Monitor DP - Control Operativo & SLA", 
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
# --------------------------------
