import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np
from collections import Counter

# ================================
# CONFIGURACIÓN DE LA PÁGINA
# ================================
st.set_page_config(
    page_title="Dashboard IA + Salud Mental Juvenil",
    page_icon="🧠",
    layout="wide"
)

# ================================
# ⚠️ URL DIRECTA DE TU CSV EN GITHUB (rama main - siempre actualizada)
# ================================
URL_CSV_GITHUB = "https://raw.githubusercontent.com/JoseDelaCruz365/PA3/main/scopus_export%20(2).csv"

# ================================
# FUNCIONES DE PROCESAMIENTO
# ================================

@st.cache_data
def cargar_datos_desde_github(url):
    """Carga el CSV directamente desde GitHub"""
    try:
        df = pd.read_csv(url)
        st.success(f"✅ Archivo cargado exitosamente desde GitHub: {len(df)} registros")
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar desde GitHub: {e}")
        st.info("Verifica que la URL sea correcta y el archivo exista en el repositorio")
        return None

@st.cache_data
def limpiar_datos(df):
    """Limpia y prepara el DataFrame"""
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Cited by'] = df['Cited by'].astype(str).str.replace(',', '').str.strip()
    df['Cited by'] = pd.to_numeric(df['Cited by'], errors='coerce').fillna(0)
    df['Abstract'] = df['Abstract'].fillna("")
    df['Authors'] = df['Authors'].fillna("Autor Desconocido")
    return df

def extraer_top_autores(df, top_n=10):
    citas_por_autor = {}
    for _, row in df.iterrows():
        citas = row['Cited by']
        autores_str = str(row['Authors'])
        if ';' in autores_str:
            autores = [a.strip() for a in autores_str.split(';')]
        elif ',' in autores_str and '.,' not in autores_str:
            autores = [a.strip() for a in autores_str.split(',')]
        else:
            autores = [autores_str.strip()]
        for autor in autores:
            if autor and autor != "Autor Desconocido":
                autor_limpio = autor.replace('"', '').strip()
                if len(autor_limpio) > 30:
                    autor_limpio = autor_limpio[:27] + "..."
                citas_por_autor[autor_limpio] = citas_por_autor.get(autor_limpio, 0) + citas
    if citas_por_autor:
        top_autores = sorted(citas_por_autor.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return pd.DataFrame(top_autores, columns=['Autor', 'Total Citas'])
    return pd.DataFrame(columns=['Autor', 'Total Citas'])

def extraer_palabras_frecuentes(df, top_n=10):
    texto_completo = " ".join(df['Abstract'].dropna().astype(str).str.lower())
    palabras = re.findall(r'\b[a-z]{4,}\b', texto_completo)
    stop_words = {
        'this', 'that', 'these', 'those', 'with', 'from', 'have', 'will',
        'were', 'been', 'also', 'can', 'may', 'used', 'using', 'study',
        'research', 'paper', 'article', 'results', 'analysis', 'data',
        'based', 'method', 'methods', 'approach', 'proposed', 'model',
        'system', 'systems', 'work', 'present', 'discuss', 'show',
        'demonstrate', 'provide', 'identify', 'evaluate', 'evaluation',
        'performance', 'different', 'compared', 'comparison', 'health',
        'mental', 'students', 'university', 'clinical', 'treatment'
    }
    palabras_filtradas = [p for p in palabras if p not in stop_words and len(p) >= 4]
    contador = Counter(palabras_filtradas)
    return pd.DataFrame(contador.most_common(top_n), columns=['Palabra', 'Frecuencia'])

# ================================
# CARGA DE DATOS DESDE GITHUB
# ================================
st.title("🧠 Inteligencia Artificial y la Prevención de Salud Mental Juvenil")
st.caption("Análisis Bibliométrico | Datos cargados directamente desde GitHub")

# Cargar datos
df_raw = cargar_datos_desde_github(URL_CSV_GITHUB)

if df_raw is None:
    st.stop()

# Limpiar datos
df_raw = limpiar_datos(df_raw)

# Determinar rangos
min_year = int(df_raw['Year'].min()) if not pd.isna(df_raw['Year'].min()) else 2019
max_year = int(df_raw['Year'].max()) if not pd.isna(df_raw['Year'].max()) else 2026

# ================================
# SIDEBAR - INFORMACIÓN Y FILTROS
# ================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=70)
    st.markdown("## 📊 Sobre el Dashboard")
    
    with st.expander("🎯 Pregunta de Investigación", expanded=True):
        st.markdown("""
        > ¿Cómo contribuye la investigación académica en inteligencia artificial a la **prevención de trastornos de salud mental en jóvenes** desde 2019 a la actualidad?
        """)
    
    with st.expander("📈 Métricas Analizadas", expanded=True):
        st.markdown("""
        - 🔬 **Volumen de publicaciones** por año
        - 🏆 **Autores más citados** en el campo
        - 🔍 **Palabras clave** en abstracts
        - 📊 **Tendencias de investigación** en IA aplicada
        """)
    
    with st.expander("📚 Fuente y Periodo", expanded=True):
        st.markdown(f"""
        - **Base de datos:** Scopus  
        - **Rango:** {min_year} - {max_year}  
        - **Keywords:** Artificial Intelligence, Mental Health, Prevention, Youth
        - **Repositorio:** [GitHub - JoseDelaCruz365/PA3](https://github.com/JoseDelaCruz365/PA3)
        """)
    
    st.divider()
    
    # Filtro de años
    st.markdown("## 🎚️ Filtro Temporal")
    rango_anios = st.slider(
        "Rango de años",
        min_value=min_year,
        max_value=max_year,
        value=(max(2019, min_year), max_year),
        step=1
    )
    st.caption(f"📅 Mostrando: {rango_anios[0]} - {rango_anios[1]}")
    
    # Mostrar información del archivo
    st.divider()
    st.caption(f"📁 Archivo: `scopus_export (2).csv`")
    st.caption(f"✅ Cargado desde GitHub")

# Aplicar filtro de años
df = df_raw[(df_raw['Year'] >= rango_anios[0]) & (df_raw['Year'] <= rango_anios[1])]

# ================================
# RECOMENDACIONES (inspirado en el dashboard de referencia)
# ================================
st.markdown("## 📋 Recomendaciones basadas en la literatura")

col_rec1, col_rec2, col_rec3 = st.columns(3)

with col_rec1:
    st.markdown("### 🎓 Para estudiantes")
    st.markdown("""
    - Utilizar aplicaciones de IA (chatbots) como apoyo emocional
    - Participar en programas de prevención digital
    - Reconocer señales de alerta temprana
    """)

with col_rec2:
    st.markdown("### 🔬 Para investigadores")
    st.markdown("""
    - Desarrollar modelos predictivos validados
    - Incluir datos demográficos diversos
    - Reportar métricas de rendimiento completas
    - Priorizar la ética y privacidad de datos
    """)

with col_rec3:
    st.markdown("### 🏥 Para profesionales de salud mental")
    st.markdown("""
    - Incorporar herramientas de IA como apoyo diagnóstico
    - Mantener actualización en tecnologías digitales
    - Validar hallazgos con enfoque clínico
    - Capacitarse en telepsicología
    """)

st.divider()

# ================================
# KPI MÉTRICAS
# ================================
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.metric("🔬 Volumen de artículos", f"{len(df)} docs")
with col_k2:
    st.metric("💬 Citas totales", f"{int(df['Cited by'].sum()):,}")
with col_k3:
    st.metric("📈 Impacto promedio", f"{round(df['Cited by'].mean(), 2)}")
with col_k4:
    st.metric("📅 Rango seleccionado", f"{rango_anios[0]} - {rango_anios[1]}")

st.divider()

# ================================
# TABLA DE DATOS (df.head)
# ================================
st.markdown("## 📄 Vista previa de datos (Scopus)")
st.dataframe(
    df[['Authors', 'Title', 'Year', 'Cited by', 'Source title', 'Document Type']].head(10),
    use_container_width=True
)
st.caption(f"📌 Mostrando primeros 10 registros de {len(df)} totales | Fuente: Scopus")

st.divider()

# ================================
# GRÁFICO 1: Publicaciones por año (MODERNO)
# ================================
st.markdown("## 📅 Evolución de publicaciones por año")

publicaciones_por_anio = df['Year'].value_counts().sort_index()

if not publicaciones_por_anio.empty:
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    
    # Colores degradados
    años = publicaciones_por_anio.index.astype(str)
    valores = publicaciones_por_anio.values
    
    # Paleta moderna: azul turquesa a morado suave
    colores = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd', 
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    barras = ax1.bar(años, valores, color=colores[:len(años)], edgecolor='white', linewidth=1.5)
    
    # Estilo profesional
    ax1.set_xlabel("Año", fontsize=12, fontweight='semibold', color='#34495e')
    ax1.set_ylabel("Número de publicaciones", fontsize=12, fontweight='semibold', color='#34495e')
    ax1.set_title("📈 Crecimiento de la investigación en IA para prevención de salud mental juvenil", 
                  fontsize=14, fontweight='bold', pad=20, color='#2c3e50')
    ax1.tick_params(axis='x', rotation=45, labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)
    
    # Cuadrícula suave
    ax1.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax1.set_axisbelow(True)
    
    # Añadir valores encima de barras
    for barra, valor in zip(barras, valores):
        ax1.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.5,
                 str(valor), ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2c3e50')
    
    # Fondo y bordes
    ax1.set_facecolor('#f8f9fa')
    fig1.patch.set_facecolor('white')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig1)
else:
    st.warning("No hay datos suficientes")

st.divider()

# ================================
# GRÁFICO 2: Top autores más citados (HORIZONTAL MODERNO)
# ================================
st.markdown("## 🏆 Top 10 autores más citados")

df_top_autores = extraer_top_autores(df, top_n=10)

if not df_top_autores.empty:
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    # Colores degradados (más citado = más intenso)
    colores_barra = plt.cm.viridis_r(np.linspace(0.2, 0.9, len(df_top_autores)))
    
    # Gráfico horizontal
    y_pos = range(len(df_top_autores))
    barras = ax2.barh(y_pos, df_top_autores['Total Citas'], color=colores_barra, edgecolor='white', linewidth=1)
    
    # Configuración
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_top_autores['Autor'], fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("Total de citas", fontsize=12, fontweight='semibold', color='#34495e')
    ax2.set_title("🏅 Investigadores con mayor impacto en IA y salud mental juvenil", 
                  fontsize=14, fontweight='bold', pad=20, color='#2c3e50')
    
    # Cuadrícula suave
    ax2.grid(axis='x', linestyle='--', alpha=0.3, color='gray')
    ax2.set_axisbelow(True)
    
    # Valores al final de cada barra
    for i, (_, row) in enumerate(df_top_autores.iterrows()):
        ax2.text(row['Total Citas'] + 0.5, i, str(int(row['Total Citas'])), 
                 va='center', fontsize=9, fontweight='bold', color='#2c3e50')
    
    # Fondo y bordes
    ax2.set_facecolor('#f8f9fa')
    fig2.patch.set_facecolor('white')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig2)
else:
    st.warning("No se encontraron autores con citas")

st.divider()

# ================================
# GRÁFICO 3: Palabras frecuentes en abstracts (MODERNO)
# ================================
st.markdown("## 🔍 Tendencias: Palabras clave en abstracts")

if df['Abstract'].str.len().sum() > 0:
    df_palabras = extraer_palabras_frecuentes(df, top_n=10)
    
    if not df_palabras.empty:
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        
        # Colores cálidos (naranja/rojo para destacar)
        colores = plt.cm.OrRd(np.linspace(0.3, 0.9, len(df_palabras)))
        
        barras = ax3.bar(df_palabras['Palabra'], df_palabras['Frecuencia'], 
                         color=colores, edgecolor='white', linewidth=1.5)
        
        ax3.set_xlabel("Palabra", fontsize=12, fontweight='semibold', color='#34495e')
        ax3.set_ylabel("Frecuencia", fontsize=12, fontweight='semibold', color='#34495e')
        ax3.set_title("🔤 Términos más repetidos en los resúmenes (sin stop-words)", 
                      fontsize=14, fontweight='bold', pad=20, color='#2c3e50')
        ax3.tick_params(axis='x', rotation=45, labelsize=10)
        ax3.tick_params(axis='y', labelsize=10)
        
        # Cuadrícula
        ax3.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
        ax3.set_axisbelow(True)
        
        # Valores encima de barras
        for barra, (_, row) in zip(barras, df_palabras.iterrows()):
            ax3.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.5,
                     str(row['Frecuencia']), ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Fondo y bordes
        ax3.set_facecolor('#f8f9fa')
        fig3.patch.set_facecolor('white')
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig3)
        
        with st.expander("📄 Ver tabla de frecuencias"):
            st.dataframe(df_palabras, use_container_width=True)
    else:
        st.warning("No se pudieron extraer palabras suficientes")
else:
    st.warning("No hay abstracts disponibles")
