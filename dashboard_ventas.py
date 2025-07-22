import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Dashboard Estratégico de Ventas",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Estilo para las métricas estándar de Streamlit */
    .stMetric {
        border-radius: 10px;
        background-color: #f0f2f6;
        padding: 15px;
    }
    .stMetric-value {
        font-size: 2em;
    }
    /* Estilos para nuestras tarjetas de KPI personalizadas */
    .custom-metric {
        border-radius: 10px;
        background-color: #f0f2f6;
        padding: 15px;
        text-align: left;
        height: 100%;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        margin-bottom: 8px;
    }
    .metric-value-main {
        font-size: 2em;
        font-weight: 600;
        line-height: 1.2;
    }
    .metric-value-comp {
        font-size: 0.9rem;
        color: #888;
        margin-bottom: 8px;
    }
    .metric-delta {
        font-size: 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --- FUNCIONES AUXILIARES ---
@st.cache_data
def load_data(path):
    """Carga y preprocesa los datos desde un archivo Excel de forma robusta."""
    if not os.path.exists(path):
        st.error(f"Error: No se encontró el archivo en la ruta: {path}")
        return None
    try:
        df = pd.read_excel(path, sheet_name="Ventas", engine='openpyxl')
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
        
        dias_map = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        meses_map = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }
        
        df['año'] = df['fecha'].dt.year
        df['mes_num'] = df['fecha'].dt.month
        df['dia_semana'] = df['fecha'].dt.day_name().map(dias_map)
        df['mes_nombre'] = df['mes_num'].map(meses_map)
        df['mes_año'] = df['fecha'].dt.to_period('M').astype(str)
        
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")
        return None

def create_heatmap(df, title):
    """Crea una figura de mapa de calor de Plotly."""
    if df.empty:
        st.info(f"No hay datos para generar el mapa de calor: {title}")
        return None
    
    dias_ordenados = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    heatmap_data = df.pivot_table(
        values='ventas', index='tienda', columns='dia_semana', aggfunc='mean'
    ).reindex(columns=dias_ordenados)
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Día de la Semana", y="Tienda", color="Venta Promedio"),
        x=dias_ordenados, y=heatmap_data.index,
        text_auto=".2s", aspect="auto", color_continuous_scale="Viridis",
        title=title
    )
    fig.update_xaxes(side="top")
    return fig

def create_stats_barchart(df, title):
    """Crea un gráfico de barras para media y mediana por tienda."""
    if df.empty:
        st.info(f"No hay datos para generar el gráfico de estadísticas: {title}")
        return None
        
    # Excluir días con cero ventas para un cálculo justo
    df_operating_days = df[df['ventas'] > 0]
    
    stats = df_operating_days.groupby('tienda')['ventas'].agg(['mean', 'median']).reset_index()
    stats = stats.melt(id_vars='tienda', value_vars=['mean', 'median'], var_name='Métrica', value_name='Valor')
    
    # --- MEJORA 1: Traducir los nombres de las métricas ---
    stats['Métrica'] = stats['Métrica'].map({'mean': 'Media', 'median': 'Mediana'})
    
    fig = px.bar(
        stats,
        y='tienda',
        x='Valor',
        color='Métrica',
        barmode='group',
        orientation='h',
        title=title,
        labels={'Valor': 'Venta Diaria ($)', 'tienda': 'Tienda', 'Métrica': 'Métrica'},
        template='plotly_white',
        color_discrete_map={'Media': '#636EFA', 'Mediana': '#FFA15A'},
        text='Valor' # Especificar la columna para el texto
    )
    # --- MEJORA 2: Mostrar y formatear el valor en las barras ---
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        uniformtext_minsize=8, 
        uniformtext_mode='hide'
    )
    return fig


# --- CARGA DE DATOS ---
file_path = "C:/Users/aleja/OneDrive/Documentos/Jugando y Educando/App Visualizacion/MVP/Ventas.xlsx"
df_original = load_data(file_path)

if df_original is None:
    st.stop()

# --- BARRA LATERAL CON FILTROS ---
st.sidebar.title("🚀 Filtros Globales")
st.sidebar.markdown("Ajusta los filtros para explorar el dashboard.")

compare_mode = st.sidebar.checkbox("Comparar dos períodos", value=False)

st.sidebar.header("Período Principal")
min_date = df_original['fecha'].min().to_pydatetime()
max_date = df_original['fecha'].max().to_pydatetime()
start_date_1, end_date_1 = st.sidebar.date_input(
    "Selecciona el rango de fechas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="periodo1"
)

df_periodo_1 = df_original[
    (df_original['fecha'].between(pd.to_datetime(start_date_1), pd.to_datetime(end_date_1)))
]

df_periodo_2 = pd.DataFrame()
if compare_mode:
    st.sidebar.header("Período de Comparación")
    start_date_2, end_date_2 = st.sidebar.date_input(
        "Selecciona el rango de fechas a comparar:",
        value=(start_date_1 - pd.DateOffset(years=1), end_date_1 - pd.DateOffset(years=1)),
        min_value=min_date,
        max_value=max_date,
        key="periodo2"
    )
    df_periodo_2 = df_original[
        (df_original['fecha'].between(pd.to_datetime(start_date_2), pd.to_datetime(end_date_2)))
    ]

st.sidebar.header("Filtro de Tiendas")
all_stores = sorted(df_original['tienda'].unique())
selected_stores = st.sidebar.multiselect(
    "Selecciona las tiendas:", options=all_stores, default=all_stores
)

df_periodo_1 = df_periodo_1[df_periodo_1['tienda'].isin(selected_stores)]
if not df_periodo_2.empty:
    df_periodo_2 = df_periodo_2[df_periodo_2['tienda'].isin(selected_stores)]

if df_periodo_1.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados en el período principal.")
    st.stop()

# --- PANTALLA PRINCIPAL ---
st.title("🚀 Dashboard Estratégico de Ventas")

tab1, tab2, tab3 = st.tabs(["📊 Resumen Gerencial", "📈 Análisis Comparativo", "📋 Explorador de Datos"])

with tab1:
    st.header("Visión General del Negocio")
    
    total_sales_1 = df_periodo_1['ventas'].sum()
    avg_daily_sales_1 = df_periodo_1.groupby('fecha')['ventas'].sum().mean()

    if compare_mode and not df_periodo_2.empty:
        total_sales_2 = df_periodo_2['ventas'].sum()
        avg_daily_sales_2 = df_periodo_2.groupby('fecha')['ventas'].sum().mean()
        sales_var = ((total_sales_1 - total_sales_2) / total_sales_2) * 100 if total_sales_2 > 0 else float('inf')
        avg_sales_var = ((avg_daily_sales_1 - avg_daily_sales_2) / avg_daily_sales_2) * 100 if avg_daily_sales_2 > 0 else float('inf')

        st.subheader("Comparativa de KPIs")
        col1, col2 = st.columns(2)
        with col1:
            delta_color = "green" if sales_var >= 0 else "red"
            arrow = '▲' if sales_var >= 0 else '▼'
            html_kpi_1 = f"""
            <div class="custom-metric">
                <div class="metric-label">Ventas Totales</div>
                <div class="metric-value-main">${total_sales_1:,.0f}</div>
                <div class="metric-value-comp">vs. ${total_sales_2:,.0f} (comp.)</div>
                <div class="metric-delta" style="color:{delta_color};">
                    {arrow} {sales_var:.2f}%
                </div>
            </div>
            """
            st.markdown(html_kpi_1, unsafe_allow_html=True)
            
        with col2:
            delta_color = "green" if avg_sales_var >= 0 else "red"
            arrow = '▲' if avg_sales_var >= 0 else '▼'
            html_kpi_2 = f"""
            <div class="custom-metric">
                <div class="metric-label">Venta Diaria Promedio</div>
                <div class="metric-value-main">${avg_daily_sales_1:,.0f}</div>
                <div class="metric-value-comp">vs. ${avg_daily_sales_2:,.0f} (comp.)</div>
                <div class="metric-delta" style="color:{delta_color};">
                    {arrow} {avg_sales_var:.2f}%
                </div>
            </div>
            """
            st.markdown(html_kpi_2, unsafe_allow_html=True)

    else:
        st.subheader("KPIs del Período Principal")
        col1, col2 = st.columns(2)
        col1.metric("Ventas Totales", f"${total_sales_1:,.0f}")
        col2.metric("Venta Diaria Promedio", f"${avg_daily_sales_1:,.0f}")

    st.markdown("---")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Tendencia de Ventas Mensuales")
        
        if compare_mode and not df_periodo_2.empty:
            monthly_sales_1 = df_periodo_1.groupby(['mes_num', 'mes_nombre'])['ventas'].sum().reset_index()
            monthly_sales_1['Periodo'] = 'Principal'
            
            monthly_sales_2 = df_periodo_2.groupby(['mes_num', 'mes_nombre'])['ventas'].sum().reset_index()
            monthly_sales_2['Periodo'] = 'Comparación'
            
            plot_df = pd.concat([monthly_sales_1, monthly_sales_2])
            plot_df = plot_df.sort_values('mes_num')
            
            fig_line = px.line(
                plot_df, x='mes_nombre', y='ventas', color='Periodo',
                title="Comparación de Ventas Mensuales", labels={'ventas': 'Ventas ($)', 'mes_nombre': 'Mes'},
                markers=True, template='plotly_white',
                color_discrete_map={'Principal': '#1f77b4', 'Comparación': '#ff7f0e'}
            )
        else:
            plot_df = df_periodo_1.groupby('mes_año')['ventas'].sum().reset_index()
            fig_line = px.line(
                plot_df, x='mes_año', y='ventas',
                title="Evolución Mensual de Ventas", labels={'ventas': 'Ventas ($)', 'mes_año': 'Mes'},
                markers=True, template='plotly_white'
            )

        fig_line.update_layout(xaxis_title=None, yaxis_title="Ventas ($)", legend_title="Período")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_b:
        st.subheader("Composición de Ventas por Tienda (Principal)")
        store_sales = df_periodo_1.groupby('tienda')['ventas'].sum().reset_index()
        fig_donut = px.pie(
            store_sales, names='tienda', values='ventas',
            title="Distribución de Ventas", hole=0.4, template='plotly_white'
        )
        fig_donut.update_traces(textinfo='percent+label', textposition='inside')
        st.plotly_chart(fig_donut, use_container_width=True)

with tab2:
    st.header("Análisis de Rendimiento por Tienda")
    st.subheader("Mapa de Calor: Venta Promedio por Día de la Semana")

    if compare_mode and not df_periodo_2.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig1 = create_heatmap(df_periodo_1, "Período Principal")
            if fig1: st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = create_heatmap(df_periodo_2, "Período de Comparación")
            if fig2: st.plotly_chart(fig2, use_container_width=True)
    else:
        fig = create_heatmap(df_periodo_1, "Rendimiento en el Período Seleccionado")
        if fig: st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    st.subheader("Rendimiento Típico por Tienda (Media y Mediana)")
    st.info("💡 El cálculo de la media y la mediana excluye los días con ventas iguales a cero para una comparación más justa del rendimiento en días operativos.")

    if compare_mode and not df_periodo_2.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_stats1 = create_stats_barchart(df_periodo_1, "Período Principal")
            if fig_stats1: st.plotly_chart(fig_stats1, use_container_width=True)
        with col2:
            fig_stats2 = create_stats_barchart(df_periodo_2, "Período de Comparación")
            if fig_stats2: st.plotly_chart(fig_stats2, use_container_width=True)
    else:
        fig_stats = create_stats_barchart(df_periodo_1, "Rendimiento en el Período Seleccionado")
        if fig_stats: st.plotly_chart(fig_stats, use_container_width=True)


with tab3:
    st.header("Explorador de Datos Detallados")
    st.markdown("Datos del **período principal**. Puedes ordenar y buscar.")
    
    df_display = df_periodo_1[['fecha', 'tienda', 'ventas', 'dia_semana']].copy()
    df_display['ventas'] = df_display['ventas'].apply(lambda x: f"${x:,.0f}")
    df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_display.sort_values(by="fecha", ascending=False), 
        use_container_width=True, hide_index=True
    )
