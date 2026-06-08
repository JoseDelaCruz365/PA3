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
# GRÁFICO 1: Publicaciones por año
# ================================
st.markdown("## 📅 Evolución de publicaciones por año")

publicaciones_por_anio = df['Year'].value_counts().sort_index()

if not publicaciones_por_anio.empty:
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(publicaciones_por_anio.index.astype(str), publicaciones_por_anio.values, color='#1f77b4')
    ax1.set_xlabel("Año", fontsize=11)
    ax1.set_ylabel("Número de publicaciones", fontsize=11)
    ax1.set_title("Crecimiento de la investigación en IA para prevención de salud mental juvenil", fontsize=13)
    ax1.tick_params(axis='x', rotation=45)
    
    for i, (year, count) in enumerate(publicaciones_por_anio.items()):
        ax1.text(i, count + 0.5, str(count), ha='center', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig1)
else:
    st.warning("No hay datos suficientes")

st.divider()

# ================================
# GRÁFICO 2: Top autores más citados (horizontal)
# ================================
st.markdown("## 🏆 Top 10 autores más citados")

df_top_autores = extraer_top_autores(df, top_n=10)

if not df_top_autores.empty:
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    y_pos = range(len(df_top_autores))
    ax2.barh(y_pos, df_top_autores['Total Citas'], color='#42929d')
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_top_autores['Autor'])
    ax2.invert_yaxis()
    ax2.set_xlabel("Total de citas", fontsize=11)
    ax2.set_title("Investigadores con mayor impacto en IA y salud mental juvenil", fontsize=13)
    
    for i, (_, row) in enumerate(df_top_autores.iterrows()):
        ax2.text(row['Total Citas'] + 0.5, i, str(int(row['Total Citas'])), va='center', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig2)
else:
    st.warning("No se encontraron autores con citas")

st.divider()

# ================================
# GRÁFICO 3: Palabras frecuentes en abstracts
# ================================
st.markdown("## 🔍 Tendencias: Palabras clave en abstracts")

if df['Abstract'].str.len().sum() > 0:
    df_palabras = extraer_palabras_frecuentes(df, top_n=10)
    
    if not df_palabras.empty:
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        ax3.bar(df_palabras['Palabra'], df_palabras['Frecuencia'], color='#2ca02c')
        ax3.set_xlabel("Palabra", fontsize=11)
        ax3.set_ylabel("Frecuencia", fontsize=11)
        ax3.set_title("Términos más repetidos en los resúmenes (sin stop-words)", fontsize=13)
        ax3.tick_params(axis='x', rotation=45)
        
        for i, (_, row) in enumerate(df_palabras.iterrows()):
            ax3.text(i, row['Frecuencia'] + 0.5, str(row['Frecuencia']), ha='center', fontsize=9)
        
        plt.tight_layout()
        st.pyplot(fig3)
        
        with st.expander("📄 Ver tabla de frecuencias"):
            st.dataframe(df_palabras, use_container_width=True)
    else:
        st.warning("No se pudieron extraer palabras suficientes")
else:
    st.warning("No hay abstracts disponibles")

st.divider()
st.caption("📌 Dashboard desarrollado con Streamlit | Datos cargados desde GitHub | Grupo 05")
