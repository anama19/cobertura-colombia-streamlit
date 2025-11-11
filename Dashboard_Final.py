import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ----------- Configuración inicial ---------------- 
st.set_page_config(
    page_title="Cobertura Móvil Colombia 2017 - 2024",
    layout="wide",
    page_icon="📶"
)

st.title("📶📱 Cobertura Móvil Colombia 2017 - 2024")

# ----------- Carga de datos ----------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("cobertura_colombia_2017_2024_con_coords.csv", sep=",", quotechar='"', engine="python", encoding="utf-8")
    df.columns = df.columns.str.strip()
    return df

df = cargar_datos()

# --------------- Estructura del dashboard ------------------
st.sidebar.title("Menú de navegación")
pagina = st.sidebar.selectbox("Ir a:", ["Proveedores", "Cobertura", "Variables Socioeconómicas"])

st.sidebar.header("🔍 Filtros")

filtros = {
    "DEPARTAMENTO": st.sidebar.multiselect("Departamento", sorted(df["DEPARTAMENTO"].unique())),
    "MUNICIPIO": st.sidebar.multiselect("Municipio", sorted(df["MUNICIPIO"].unique())),
    "CENTRO_POBLADO": st.sidebar.multiselect("Centro poblado", sorted(df["CENTRO_POBLADO"].unique()))
}

df_filtrado = df.copy()
for col, valores in filtros.items():
    if valores:
        df_filtrado = df_filtrado[df_filtrado[col].isin(valores)]

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Promedio tasa pobreza", round(df_filtrado["TASA_POBREZA"].mean(), 2))
with col2:
    st.metric("Promedio tasa desempleo", round(df_filtrado["TASA_DESEMPLEO"].mean(), 2))
with col3:
    st.metric("Promedio tasa electrificación", round(df_filtrado["TASA_ELECTRIFICACION"].mean(), 2))
with col4:
    promedio_ingreso = df_filtrado["INGRESO_PROMEDIO_HOGAR"].mean()
    st.metric("Promedio ingreso hogar", f"${promedio_ingreso:,.2f}")

st.markdown("---")
st.title(f"{pagina}")

# ------------------------------------------
# 📊 Página 1: Proveedores (paleta azul)
# ------------------------------------------
if pagina == "Proveedores":
    st.subheader("🏢 Distribución por proveedor")

    df_proveedor = df_filtrado['NOMBRE_PROVEEDOR_COMERCIAL'].value_counts().reset_index()
    df_proveedor.columns = ['Proveedor', 'Cantidad']

    fig1 = px.bar(
        df_proveedor,
        x='Proveedor',
        y='Cantidad',
        color='Proveedor',
        color_discrete_sequence=px.colors.sequential.Blues_r,
        labels={'Proveedor': 'Proveedor', 'Cantidad': 'Número de personas'},
        title="Distribución de Proveedores"
    )
    fig1.update_layout(plot_bgcolor="#F5F7FA", title_font=dict(size=20, color="#003366"))
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("---")

    df_cobertura_prov = (
    df_filtrado.groupby("NOMBRE_PROVEEDOR_COMERCIAL")[["COBERTURA_2G", "COBERTURA_3G", "COBERTURA_4G", "COBERTURA_5G"]]
    .apply(lambda x: (x == "SÍ").mean() * 100)
    .reset_index()
    )

    df_cobertura_melt = df_cobertura_prov.melt(
        id_vars="NOMBRE_PROVEEDOR_COMERCIAL",
        var_name="Tipo de Red",
        value_name="Porcentaje de Cobertura"
    )
    df_cobertura_melt["Porcentaje de Cobertura"] = df_cobertura_melt["Porcentaje de Cobertura"].round(2)

    fig_cobertura_prov = px.bar(
        df_cobertura_melt,
        x="NOMBRE_PROVEEDOR_COMERCIAL",
        y="Porcentaje de Cobertura",
        color="Tipo de Red",
        barmode="group",
        color_discrete_sequence=px.colors.sequential.Blues_r,
        title="Cobertura Promedio por Proveedor y Tipo de Red (%)",
        labels={
        "NOMBRE_PROVEEDOR_COMERCIAL": "Proveedor",
        "Porcentaje de Cobertura": "Porcentaje (%)",
        "Tipo de Red": "Tecnología"
        }
    )
    st.plotly_chart(fig_cobertura_prov, use_container_width=True)

# ------------------------------------------
# 🌐 Página 2: Cobertura (paleta verde)
# ------------------------------------------
elif pagina == "Cobertura":
    columnas_cobertura = ["COBERTURA_2G", "COBERTURA_3G", "COBERTURA_4G", "COBERTURA_5G"]

    df_melt = df_filtrado.melt(value_vars=columnas_cobertura, var_name="Tipo de red", value_name="Cobertura")
    df_resumen = df_melt.groupby(["Tipo de red", "Cobertura"]).size().reset_index(name="Cantidad")

    fig = px.bar(
        df_resumen,
        x="Tipo de red",
        y="Cantidad",
        color="Cobertura",
        barmode="group",
        color_discrete_map={"SÍ": "#007F5F", "NO": "#D62828"},
        title="Distribución de Cobertura por Tipo de Red"
    )
    fig.update_layout(plot_bgcolor="#F0F8F5", title_font=dict(size=20, color="#003D2E"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🌐 Resumen por municipio y conectividad")
    tabla_municipio = df_filtrado.groupby("MUNICIPIO").agg(
        COBERTURA_2G=("COBERTURA_2G", lambda x: x.mode().iloc[0]),
        COBERTURA_3G=("COBERTURA_3G", lambda x: x.mode().iloc[0]),
        COBERTURA_4G=("COBERTURA_4G", lambda x: x.mode().iloc[0]),
        COBERTURA_5G=("COBERTURA_5G", lambda x: x.mode().iloc[0])
    ).reset_index()

    tabla_municipio["NUM_COBERTURAS"] = tabla_municipio[
        ["COBERTURA_2G", "COBERTURA_3G", "COBERTURA_4G", "COBERTURA_5G"]
    ].apply(lambda x: (x == "SÍ").sum(), axis=1)

    def clasificar_conectividad(n):
        if n == 4: return "Alta (2G-5G)"
        elif n == 3: return "Media-Alta (sin 5G)"
        elif n == 2: return "Media"
        elif n == 1: return "Baja"
        else: return "Sin cobertura"

    tabla_municipio["NIVEL_CONECTIVIDAD"] = tabla_municipio["NUM_COBERTURAS"].apply(clasificar_conectividad)
    st.dataframe(tabla_municipio, use_container_width=True)

    df_pct = round(df.groupby("DEPARTAMENTO", as_index=False)["PCT_HOGARES_INTERNET"]
                   .mean().sort_values("PCT_HOGARES_INTERNET", ascending=False), 0)

    st.markdown("---")
    st.subheader("🗺️ Mapa Interactivo de Cobertura por Departamento")

    if "LATITUD" in df_filtrado.columns and "LONGITUD" in df_filtrado.columns:
        columnas_cobertura = ["COBERTURA_2G", "COBERTURA_3G", "COBERTURA_4G", "COBERTURA_5G"]
        df_filtrado[columnas_cobertura] = df_filtrado[columnas_cobertura].replace({"SÍ": 1, "NO": 0})

        df_depart = df_filtrado.groupby(["DEPARTAMENTO"], as_index=False).agg({
            "LATITUD": "mean",
            "LONGITUD": "mean",
            "PCT_HOGARES_INTERNET": "mean",
            "COBERTURA_2G": "mean",
            "COBERTURA_3G": "mean",
            "COBERTURA_4G": "mean",
            "COBERTURA_5G": "mean"
        })

        df_depart["NUM_COBERTURAS"] = (
            (df_depart["COBERTURA_2G"] > 0.5).astype(int) +
            (df_depart["COBERTURA_3G"] > 0.5).astype(int) +
            (df_depart["COBERTURA_4G"] > 0.5).astype(int) +
            (df_depart["COBERTURA_5G"] > 0.5).astype(int)
        )
        df_depart["NIVEL_CONECTIVIDAD"] = df_depart["NUM_COBERTURAS"].apply(clasificar_conectividad)

        variable_mapa = st.selectbox(
            "Selecciona la variable de cobertura para mostrar en el mapa:",
            ["NIVEL_CONECTIVIDAD", "PCT_HOGARES_INTERNET", "COBERTURA_2G", "COBERTURA_3G", "COBERTURA_4G", "COBERTURA_5G"],
            index=0
        )

        if variable_mapa == "NIVEL_CONECTIVIDAD":
            fig_mapa = px.scatter_mapbox(
                df_depart,
                lat="LATITUD",
                lon="LONGITUD",
                color="NIVEL_CONECTIVIDAD",
                size="NUM_COBERTURAS",
                hover_name="DEPARTAMENTO",
                color_discrete_map={
                    "Alta (2G-5G)": "#006D2C",
                    "Media-Alta (sin 5G)": "#31A354",
                    "Media": "#A1D99B",
                    "Baja": "#FDD49E",
                    "Sin cobertura": "#E5E5E5"
                },
                size_max=30,
                zoom=4.3,
                mapbox_style="carto-positron",
                title="Nivel de Conectividad Promedio por Departamento"
            )
        else:
            fig_mapa = px.scatter_mapbox(
                df_depart,
                lat="LATITUD",
                lon="LONGITUD",
                color=variable_mapa,
                size=variable_mapa if df_depart[variable_mapa].dtype != 'O' else None,
                hover_name="DEPARTAMENTO",
                color_continuous_scale="YlGn",
                zoom=4.3,
                mapbox_style="carto-positron",
                title=f"Mapa de {variable_mapa} por Departamento"
            )

        fig_mapa.update_layout(autosize=True, height=750, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig_mapa, use_container_width=True)

# ------------------------------------------
# 📉 Página 3: Variables Socioeconómicas (paleta cálida)
# ------------------------------------------
elif pagina == "Variables Socioeconómicas":
    df_desempleo = round(df.groupby("DEPARTAMENTO", as_index=False)["TASA_DESEMPLEO"]
                         .mean().sort_values("TASA_DESEMPLEO", ascending=False), 2)
    fig_desempleo = px.bar(
        df_desempleo,
        x="DEPARTAMENTO",
        y="TASA_DESEMPLEO",
        color="TASA_DESEMPLEO",
        color_continuous_scale="Oranges",
        title="💼 Tasa Promedio de Desempleo por Departamento (%)",
    )
    st.plotly_chart(fig_desempleo, use_container_width=True)

    estrato_counts = df["ESTRATO_PROMEDIO"].value_counts().reset_index()
    estrato_counts.columns = ["Estrato Promedio", "Cantidad"]
    fig_estrato = px.pie(
        estrato_counts,
        names="Estrato Promedio",
        values="Cantidad",
        title="Distribución de Estrato Promedio",
        color_discrete_sequence=px.colors.sequential.Sunset
    )
    st.plotly_chart(fig_estrato, use_container_width=True)

    df_precip = round(df.groupby("DEPARTAMENTO", as_index=False)["PRECIPITACION_MEDIA"]
                      .mean().sort_values("PRECIPITACION_MEDIA", ascending=False), 0)
    fig_precip = px.bar(
        df_precip,
        x="DEPARTAMENTO",
        y="PRECIPITACION_MEDIA",
        color="PRECIPITACION_MEDIA",
        color_continuous_scale="Blues",
        title="🌧️ Promedio de Precipitación Media por Departamento (mm/año)",
    )
    st.plotly_chart(fig_precip, use_container_width=True)