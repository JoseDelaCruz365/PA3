import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
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
# URL DIRECTA DE TU CSV EN GITHUB
# ================================
URL_CSV_GITHUB = "https://raw.githubusercontent.com/JoseDelaCruz365/PA3/main/scopus_export%20(2).csv"

# ================================
# FUNCIONES DE PROCESAMIENTO
# ================================

@st.cache_data
def cargar_datos_desde_github(url):
    try:
        df = pd.read_csv(url)
        st.success(f"✅ Archivo cargado exitosamente desde GitHub: {len(df)} registros")
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar desde GitHub: {e}")
        return None

@st.cache_data
def limpiar_datos(df):
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
            if autor and autor != "Autor Desconocido" and autor != "Unknown Author":
                autor_limpio = autor.replace('"', '').strip()
                if len(autor_limpio) > 28:
                    autor_limpio = autor_limpio[:25] + "..."
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
        'mental', 'students', 'university', 'clinical', 'treatment',
        'well', 'being', 'also', 'may', 'will', 'can', 'used', 'using'
    }
    palabras_filtradas = [p for p in palabras if p not in stop_words and len(p) >= 4]
    contador = Counter(palabras_filtradas)
    return pd.DataFrame(contador.most_common(top_n), columns=['Palabra', 'Frecuencia'])

# ================================
# CARGA DE DATOS
# ================================
st.title("🧠 Inteligencia Artificial y la Prevención de Salud Mental Juvenil")
st.caption("Análisis Bibliométrico | Datos cargados directamente desde GitHub")

df_raw = cargar_datos_desde_github(URL_CSV_GITHUB)

if df_raw is None:
    st.stop()

df_raw = limpiar_datos(df_raw)

min_year = int(df_raw['Year'].min()) if not pd.isna(df_raw['Year'].min()) else 2019
max_year = int(df_raw['Year'].max()) if not pd.isna(df_raw['Year'].max()) else 2026

# ================================
# SIDEBAR
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
        """)
    
    st.divider()
    
    st.markdown("## 🎚️ Filtro Temporal")
    rango_anios = st.slider(
        "Rango de años",
        min_value=min_year,
        max_value=max_year,
        value=(max(2019, min_year), max_year),
        step=1
    )
    st.caption(f"📅 Mostrando: {rango_anios[0]} - {rango_anios[1]}")

# Aplicar filtro
df = df_raw[(df_raw['Year'] >= rango_anios[0]) & (df_raw['Year'] <= rango_anios[1])]

# ================================
# BLOQUE 1: DOS GRÁFICOS LADO A LADO
# ================================
st.markdown("## 📊 Bloque 1: Evolución Temporal e Investigadores de Mayor Impacto")

col1, col2 = st.columns(2)

# GRÁFICO 1: Publicaciones por año
with col1:
    st.markdown("### 📅 Cronología de Publicaciones Científicas")
    
    publicaciones_por_anio = df['Year'].value_counts().sort_index()
    
    if not publicaciones_por_anio.empty:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        
        años = publicaciones_por_anio.index.astype(int)
        valores = publicaciones_por_anio.values
        
        # Barras en azul profesional
        barras = ax1.bar(años, valores, color='#1f77b4', edgecolor='white', linewidth=1)
        
        ax1.set_xlabel("Año", fontsize=10)
        ax1.set_ylabel("Número de publicaciones", fontsize=10)
        ax1.tick_params(axis='x', labelsize=9)
        ax1.tick_params(axis='y', labelsize=9)
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        ax1.set_axisbelow(True)
        
        # Valor encima de cada barra
        for barra, valor in zip(barras, valores):
            ax1.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.3,
                     str(valor), ha='center', va='bottom', fontsize=8)
        
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig1)
    else:
        st.warning("No hay datos")

# GRÁFICO 2: Top autores
with col2:
    st.markdown("### 🏆 Top 10 Investigadores con Mayor Nivel de Citación")
    
    df_top_autores = extraer_top_autores(df, top_n=10)
    
    if not df_top_autores.empty:
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        
        y_pos = range(len(df_top_autores))
        ax2.barh(y_pos, df_top_autores['Total Citas'], color='#42929d', height=0.7)
        
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(df_top_autores['Autor'], fontsize=8)
        ax2.invert_yaxis()
        ax2.set_xlabel("Total de citas", fontsize=10)
        ax2.tick_params(axis='x', labelsize=9)
        ax2.grid(axis='x', linestyle='--', alpha=0.3)
        
        for i, (_, row) in enumerate(df_top_autores.iterrows()):
            ax2.text(row['Total Citas'] + 0.5, i, str(int(row['Total Citas'])), 
                     va='center', fontsize=8)
        
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.warning("No hay datos")

st.divider()

# ================================
# BLOQUE 2: TABLA + GRÁFICO DE PALABRAS
# ================================
st.markdown("## 🔍 Bloque 2: Análisis de Palabras Clave y Tendencias en Abstracts")

col3, col4 = st.columns(2)

# Tabla de palabras frecuentes
with col3:
    st.markdown("### 📋 Matriz Numérica de Conceptos Frecuentes")
    
    if df['Abstract'].str.len().sum() > 0:
        df_palabras = extraer_palabras_frecuentes(df, top_n=10)
        
        if not df_palabras.empty:
            st.dataframe(df_palabras, use_container_width=True, hide_index=True)
        else:
            st.warning("No se pudieron extraer palabras")
    else:
        st.warning("No hay abstracts disponibles")

# Gráfico de frecuencia de palabras
with col4:
    st.markdown("### 📊 Frecuencia de Enfoques de IA y Métodos de Prevención")
    
    if 'df_palabras' in locals() and not df_palabras.empty:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        
        barras = ax3.bar(df_palabras['Palabra'], df_palabras['Frecuencia'], 
                         color='#2ca02c', edgecolor='white', linewidth=1)
        
        ax3.set_xlabel("Palabra", fontsize=10)
        ax3.set_ylabel("Frecuencia", fontsize=10)
        ax3.tick_params(axis='x', rotation=45, labelsize=8)
        ax3.tick_params(axis='y', labelsize=9)
        ax3.grid(axis='y', linestyle='--', alpha=0.3)
        ax3.set_axisbelow(True)
        
        for barra, (_, row) in zip(barras, df_palabras.iterrows()):
            ax3.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.3,
                     str(row['Frecuencia']), ha='center', va='bottom', fontsize=8)
        
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig3)
    else:
        st.warning("No hay datos para graficar")

st.divider()

# ================================
# BLOQUE 3: VISTA PREVIA DE DATOS
# ================================
st.markdown("## 📋 Bloque 3: Explorador e Integridad de Datos (Vista Previa df.head)")
st.dataframe(df[['Authors', 'Title', 'Year', 'Cited by', 'Source title']].head(10), use_container_width=True)
st.caption(f"📌 Mostrando primeros 10 registros de {len(df)} totales | Fuente: Scopus")

st.divider()
st.caption("📌 Dashboard desarrollado con Streamlit | Datos cargados desde GitHub | Grupo 05")
