import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter

# ================================
# CONFIGURACIÓN DE LA PÁGINA
# ================================
st.set_page_config(
    page_title="Dashboard Bibliométrico Scopus",
    page_icon="📊",
    layout="wide"
)

# ================================
# FUNCIONES DE PROCESAMIENTO
# ================================

@st.cache_data
def cargar_datos(archivo):
    """Carga y limpia el CSV exportado desde Scopus"""
    df = pd.read_csv(archivo)
    
    # Limpiar columna de años
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    
    # Limpiar columna de citas (eliminar comas, espacios, etc.)
    df['Cited by'] = df['Cited by'].astype(str).str.replace(',', '').str.strip()
    df['Cited by'] = pd.to_numeric(df['Cited by'], errors='coerce').fillna(0)
    
    # Limpiar abstracts
    df['Abstract'] = df['Abstract'].fillna("")
    
    # Limpiar autores
    df['Authors'] = df['Authors'].fillna("Autor Desconocido")
    
    return df


def extraer_top_autores(df, top_n=10):
    """
    Extrae el top N de autores más citados.
    Considera múltiples autores por artículo (separados por ; o ,)
    """
    citas_por_autor = {}
    
    for _, row in df.iterrows():
        citas = row['Cited by']
        autores_str = str(row['Authors'])
        
        # Separar autores (punto y coma o coma)
        if ';' in autores_str:
            autores = [a.strip() for a in autores_str.split(';')]
        elif ',' in autores_str and '.,' not in autores_str:
            autores = [a.strip() for a in autores_str.split(',')]
        else:
            autores = [autores_str.strip()]
        
        # Acumular citas por autor
        for autor in autores:
            if autor and autor != "Autor Desconocido":
                # Limpiar nombre para mostrar
                autor_limpio = autor.replace('"', '').strip()
                if len(autor_limpio) > 30:
                    autor_limpio = autor_limpio[:27] + "..."
                citas_por_autor[autor_limpio] = citas_por_autor.get(autor_limpio, 0) + citas
    
    # Ordenar y tomar top N
    if citas_por_autor:
        top_autores = sorted(citas_por_autor.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return pd.DataFrame(top_autores, columns=['Autor', 'Total Citas'])
    else:
        return pd.DataFrame(columns=['Autor', 'Total Citas'])


def extraer_palabras_frecuentes(df, top_n=10):
    """
    Extrae las palabras más frecuentes de los abstracts,
    omitiendo stop-words comunes en inglés técnico.
    """
    # Unir todos los abstracts en un solo texto
    texto_completo = " ".join(df['Abstract'].dropna().astype(str).str.lower())
    
    # Extraer palabras (solo letras, mínimo 4 caracteres)
    palabras = re.findall(r'\b[a-z]{4,}\b', texto_completo)
    
    # Stop-words en inglés (técnico y común)
    stop_words = {
        'this', 'that', 'these', 'those', 'with', 'from', 'have', 'will',
        'were', 'been', 'also', 'can', 'may', 'used', 'using', 'study',
        'research', 'paper', 'article', 'results', 'analysis', 'data',
        'based', 'method', 'methods', 'approach', 'proposed', 'model',
        'system', 'systems', 'work', 'present', 'discuss', 'show',
        'demonstrate', 'provide', 'identify', 'evaluate', 'evaluation',
        'performance', 'different', 'compared', 'comparison', 'well',
        'would', 'could', 'should', 'within', 'without', 'among',
        'between', 'through', 'during', 'after', 'before', 'under',
        'over', 'into', 'such', 'more', 'most', 'some', 'very', 'just',
        'but', 'not', 'are', 'was', 'has', 'were', 'being', 'been',
        'their', 'they', 'them', 'there', 'these', 'those', 'then',
        'than', 'then', 'because', 'therefore', 'however', 'although'
    }
    
    # Filtrar stop-words y palabras demasiado cortas
    palabras_filtradas = [p for p in palabras if p not in stop_words and len(p) >= 4]
    
    # Contar frecuencias
    contador = Counter(palabras_filtradas)
    
    # Tomar top N
    top_palabras = contador.most_common(top_n)
    
    return pd.DataFrame(top_palabras, columns=['Palabra', 'Frecuencia'])


# ================================
# INTERFAZ DE USUARIO
# ================================

st.title("📊 Dashboard Bibliométrico para Exportación de Scopus")
st.markdown("---")

# --- SIDEBAR: Carga de archivo y filtros ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    
    # Widget para cargar CSV
    archivo_subido = st.file_uploader(
        "Subir archivo CSV exportado desde Scopus",
        type=["csv"],
        help="El archivo debe ser la exportación estándar de Scopus en formato CSV"
    )
    
    st.divider()
    
    # Verificar si hay datos cargados
    if archivo_subido is not None:
        try:
            df_raw = cargar_datos(archivo_subido)
            st.success(f"✅ {len(df_raw)} registros cargados correctamente")
            
            # Determinar rango de años disponible
            min_year = int(df_raw['Year'].min()) if not pd.isna(df_raw['Year'].min()) else 2000
            max_year = int(df_raw['Year'].max()) if not pd.isna(df_raw['Year'].max()) else 2025
            
            # Slider para filtrar por rango de años
            st.subheader("🎚️ Filtro Temporal")
            rango_anios = st.slider(
                "Seleccionar rango de años",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
                step=1
            )
            
            # Aplicar filtro de años
            df = df_raw[(df_raw['Year'] >= rango_anios[0]) & (df_raw['Year'] <= rango_anios[1])]
            
            st.caption(f"📅 Mostrando {len(df)} publicaciones entre {rango_anios[0]} y {rango_anios[1]}")
            
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()
    else:
        st.info("👈 Esperando archivo CSV...")
        st.stop()

# ================================
# CUERPO PRINCIPAL
# ================================

# --- Confirmación de carga correcta (df.head) ---
st.subheader("📋 Vista previa de los datos cargados")
st.caption("Primeras 5 filas del DataFrame (df.head)")
st.dataframe(df.head(), use_container_width=True)
st.success("✅ Datos cargados correctamente en memoria")

st.divider()

# --- SECCIÓN 1: Distribución de publicaciones por año ---
st.subheader("📅 Distribución de publicaciones por año")

# Agrupar por año
publicaciones_por_anio = df['Year'].value_counts().sort_index()

if not publicaciones_por_anio.empty:
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(publicaciones_por_anio.index.astype(str), publicaciones_por_anio.values, color='steelblue')
    ax1.set_xlabel("Año", fontsize=11)
    ax1.set_ylabel("Número de publicaciones", fontsize=11)
    ax1.set_title("Cantidad de artículos por año (Scopus)", fontsize=13)
    ax1.tick_params(axis='x', rotation=45)
    
    # Añadir valor encima de cada barra
    for i, (year, count) in enumerate(publicaciones_por_anio.items()):
        ax1.text(i, count + 0.5, str(count), ha='center', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig1)
else:
    st.warning("No hay datos suficientes para mostrar distribución por año")

st.divider()

# --- SECCIÓN 2: Top 10 autores más citados (gráfico horizontal) ---
st.subheader("🏆 Top 10 autores más citados")

df_top_autores = extraer_top_autores(df, top_n=10)

if not df_top_autores.empty:
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    # Gráfico de barras horizontal
    y_pos = range(len(df_top_autores))
    ax2.barh(y_pos, df_top_autores['Total Citas'], color='coral')
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_top_autores['Autor'])
    ax2.invert_yaxis()  # El más citado arriba
    ax2.set_xlabel("Total de citas", fontsize=11)
    ax2.set_title("Top 10 autores con mayor impacto (por número de citas)", fontsize=13)
    
    # Añadir valor al final de cada barra
    for i, (_, row) in enumerate(df_top_autores.iterrows()):
        ax2.text(row['Total Citas'] + 0.5, i, str(int(row['Total Citas'])), va='center', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig2)
else:
    st.warning("No se encontraron autores con citas en el rango seleccionado")

st.divider()

# --- SECCIÓN 3: Palabras más frecuentes en abstracts ---
st.subheader("🔤 Top 10 palabras más frecuentes en los abstracts")

if df['Abstract'].str.len().sum() > 0:
    df_palabras = extraer_palabras_frecuentes(df, top_n=10)
    
    if not df_palabras.empty:
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        
        # Gráfico de barras vertical
        ax3.bar(df_palabras['Palabra'], df_palabras['Frecuencia'], color='seagreen')
        ax3.set_xlabel("Palabra", fontsize=11)
        ax3.set_ylabel("Frecuencia", fontsize=11)
        ax3.set_title("Términos más repetidos en los resúmenes (sin stop-words)", fontsize=13)
        ax3.tick_params(axis='x', rotation=45)
        
        # Añadir valor encima de cada barra
        for i, (_, row) in enumerate(df_palabras.iterrows()):
            ax3.text(i, row['Frecuencia'] + 0.5, str(row['Frecuencia']), ha='center', fontsize=9)
        
        plt.tight_layout()
        st.pyplot(fig3)
        
        # Mostrar también como tabla para referencia
        with st.expander("📄 Ver tabla de frecuencias"):
            st.dataframe(df_palabras, use_container_width=True)
    else:
        st.warning("No se pudieron extraer palabras suficientes de los abstracts")
else:
    st.warning("No hay abstracts disponibles en el dataset")

st.divider()
st.caption("📌 Dashboard desarrollado con Streamlit · Datos exportados desde Scopus")