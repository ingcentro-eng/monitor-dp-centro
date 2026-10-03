import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Monitor DP - Zona Centro", layout="wide")
st.title("⚡ Monitor de Daños Pendientes (DP) - Zona Centro")
st.markdown("Visualización de tiempos de atención (SLA: Urbano = 1 día | Rural = 3 días)")

# Cargar el reporte de WFM
archivo_subido = st.file_uploader("📂 Cargar reporte del día (Excel de WFM)", type=["xlsx", "xls"])

if archivo_subido is not None:
    try:
        # 1. LECTURA INTELIGENTE DE ENCABEZADOS (Soluciona el error de lectura)
        # Leemos las primeras 15 filas para encontrar automáticamente dónde empiezan los datos
        df_temp = pd.read_excel(archivo_subido, header=None, nrows=15)
        header_idx = -1
        
        for i in range(len(df_temp)):
            fila_texto = " ".join(df_temp.iloc[i].astype(str).str.lower().tolist())
            # Si la fila contiene la palabra clave, esa es nuestra cabecera
            if 'identificación' in fila_texto or 'instrucción' in fila_texto:
                header_idx = i
                break
        
        if header_idx == -1:
            st.error("❌ No se detectaron los encabezados en el archivo. Verifica que sea el reporte de WFM.")
        else:
            # Volvemos a leer el Excel desde la fila exacta que encontramos
            archivo_subido.seek(0)
            df = pd.read_excel(archivo_subido, header=header_idx)
            
            if 'Fecha de creación' not in df.columns:
                st.error("❌ Error: No se encontró la columna 'Fecha de creación'.")
            else:
                # 2. PARSEO DE FECHAS Y DÍAS SIN SERVICIO
                df['Fecha_Calculo'] = pd.to_datetime(df['Fecha de creación'], errors='coerce')
                hoy = pd.Timestamp.now().normalize() # Trae la fecha de hoy a las 00:00:00
                df['Días Sin Servicio'] = (hoy - df['Fecha_Calculo']).dt.days.fillna(0).astype(int)
                
                # 3. CLASIFICACIÓN SECTOR URBANO / RURAL
                def clasificar_sector(direccion):
                    if pd.isna(direccion): return 'URBANO'
                    dir_upper = str(direccion).upper()
                    rurales = ['VDA', 'VEREDA', 'FCA', 'FINCA', 'CORREGIMIENTO']
                    return 'RURAL' if any(kw in dir_upper for kw in rurales) else 'URBANO'
                
                if 'Dirección del dispositivo' in df.columns:
                    df['Tipo de Sector'] = df['Dirección del dispositivo'].apply(clasificar_sector)
                else:
                    df['Tipo de Sector'] = 'URBANO'
                    
                # 4. EVALUACIÓN DE ANS (SLA)
                def estado_sla(row):
                    # Límite: 3 días rural, 1 día urbano
                    limite = 3 if row['Tipo de Sector'] == 'RURAL' else 1
                    
                    if row['Días Sin Servicio'] > limite:
                        return 'Vencido'
                    elif row['Días Sin Servicio'] == limite:
                        return 'Al Límite'
                    else:
                        return 'A Tiempo'
                        
                df['Estado SLA'] = df.apply(estado_sla, axis=1)
                
                # 5. PALETA DE COLORES (Semáforo visual)
                colores = {'A Tiempo': '#00B050', 'Al Límite': '#FFC000', 'Vencido': '#C00000'}
                
                # 6. MÉTRICAS OPERATIVAS
                vencidos = len(df[df['Estado SLA'] == 'Vencido'])
                limite = len(df[df['Estado SLA'] == 'Al Límite'])
                a_tiempo = len(df[df['Estado SLA'] == 'A Tiempo'])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("🔴 Vencidos", vencidos)
                col2.metric("🟡 Al Límite", limite)
                col3.metric("🟢 A Tiempo", a_tiempo)
                
                st.markdown("---")
                
                # 7. GRÁFICAS DE GESTIÓN
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Distribución General SLA")
                    conteo = df['Estado SLA'].value_counts().reset_index()
                    conteo.columns = ['Estado SLA', 'Cantidad']
                    fig1 = px.pie(conteo, names='Estado SLA', values='Cantidad', 
                                  color='Estado SLA', color_discrete_map=colores)
                    st.plotly_chart(fig1, use_container_width=True)
                    
                with c2:
                    st.subheader("Top 10 DP Críticos (Más Días)")
                    df_vencidos = df.sort_values('Días Sin Servicio', ascending=False).head(10)
                    if not df_vencidos.empty:
                        fig2 = px.bar(df_vencidos, x='Días Sin Servicio', y='Identificación',
                                      hover_data=['Subestación', 'Dirección del dispositivo', 'Tipo de Sector'],
                                      orientation='h', color='Estado SLA', color_discrete_map=colores)
                        # Ordenar las barras de mayor a menor visualmente
                        fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("¡Excelente! No hay incidentes cargados.")
                        
                # 8. TABLA DE DETALLES CON COLORES
                st.subheader(f"Detalle Operativo para Despacho ({len(df)} Registros)")
                cols_deseadas = ['Identificación', 'Subestación', 'Instrucción', 'Dirección del dispositivo', 'Tipo de Sector', 'Días Sin Servicio', 'Estado SLA', 'Cuadrillas']
                # Filtramos para mostrar solo las columnas que sí existen en el archivo
                cols_finales = [c for c in cols_deseadas if c in df.columns]
                
                def color_celdas(val):
                    if val == 'Vencido': return 'background-color: #ffcccc; color: black;'
                    if val == 'Al Límite': return 'background-color: #ffffcc; color: black;'
                    if val == 'A Tiempo': return 'background-color: #ccffcc; color: black;'
                    return ''
                
                # Aplicar estilos compatibles con la nube de Streamlit
                try:
                    st.dataframe(df[cols_finales].style.map(color_celdas, subset=['Estado SLA']))
                except AttributeError:
                    # Soporte para versiones anteriores de Pandas
                    st.dataframe(df[cols_finales].style.applymap(color_celdas, subset=['Estado SLA']))
                    
    except Exception as e:
        st.error(f"❌ Ocurrió un error procesando el archivo: {e}")
else:
    st.info("👆 Por favor, carga tu reporte de Excel arriba para iniciar el análisis.")
