import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import unquote, quote  # zum Percent-Decoding und URL-Encoding

# --------------------------------------------------------------------
# Helper: Erzeuge company-spezifische URL
# --------------------------------------------------------------------
def make_company_url(company_name: str) -> str:
    base_url = "https://mein-dashboard-fphsbzmbpbzpscuephvjfu.streamlit.app/"
    return f"{base_url}?company={quote(company_name)}"

# --------------------------------------------------------------------
# 1. Page config und CSS-Tweak
# --------------------------------------------------------------------
st.set_page_config(page_title="CSRD Dashboard", layout="wide")
st.markdown(
    """
    <style>
      .block-container {
        padding-top: 2.5rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------
# 2. Daten laden
# --------------------------------------------------------------------
df = pd.read_csv("report_data.csv")

# --------------------------------------------------------------------
# 3. URL-Param lesen, decodieren & auf Default-Firma mappen
# --------------------------------------------------------------------
# 3.1 Liste aller Firmennamen und case-insensitive Mapping
company_list = df["name"].dropna().unique().tolist()
mapping_ci   = {name.strip().casefold(): name for name in company_list}

# 3.2 Query-Param auslesen und percent-decodieren
raw = st.query_params.get("company", [""])[0] or ""
raw = unquote(raw)

# 3.3 Normalisieren
key = raw.strip().casefold()

# 3.4 Lookup oder Fallback
default_company = mapping_ci.get(key, company_list[0])

# --------------------------------------------------------------------
# 4. Sidebar: Focal Company Selection
# --------------------------------------------------------------------
st.sidebar.header("Company Selection")
default_idx = company_list.index(default_company) if default_company in company_list else 0
company = st.sidebar.selectbox(
    "Select a company:",
    options=company_list,
    index=default_idx,
    key="company",
)

# --------------------------------------------------------------------
# 5. Sidebar: Benchmark Group Selection
# --------------------------------------------------------------------
st.sidebar.header("Benchmark Group")
benchmark_type = st.sidebar.radio(
    "Select Your Peer Group:",
    [
        "All CSRD First Wave",
        "Country Peers",
        "Sector Peers",
        "Size Peers",
        "Rating Peers",
    ],
    key="benchmark_type",
)

peer_selection = st.sidebar.multiselect(
    "Or choose specific peer companies:",
    options=company_list,
    default=[],
)

# --------------------------------------------------------------------
# 6. Build benchmark_df
# --------------------------------------------------------------------
if peer_selection:
    benchmark_df    = df[df["name"].isin(peer_selection)]
    benchmark_label = f"Selected Peers ({len(benchmark_df)} firms)"
elif benchmark_type == "All CSRD First Wave":
    benchmark_df    = df.copy()
    benchmark_label = "All CSRD First Wave"
elif benchmark_type == "Country Peers":
    country         = df.loc[df["name"] == focal_company, "country"].iat[0]
    benchmark_df    = df[df["country"] == country]
    benchmark_label = f"Country Peers: {country}"
elif benchmark_type == "Sector Peers":
    sector          = df.loc[df["name"] == focal_company, "trbceconomicsectorname"].iat[0]
    benchmark_df    = df[df["trbceconomicsectorname"] == sector]
    benchmark_label = f"Sector Peers: {sector}"
elif benchmark_type == "Market Cap Peers":
    terc            = df.loc[df["name"] == focal_company, "market_cap_tercile"].iat[0]
    lbl             = "Small" if terc == 1 else "Mid" if terc == 2 else "Large"
    benchmark_df    = df[df["market_cap_tercile"] == terc]
    benchmark_label = f"Market Cap Group: {lbl}"
else:  # Rating Peers
    terc            = df.loc[df["name"] == focal_company, "rating_tercile"].iat[0]
    lbl             = "Low" if terc == 1 else "Mid" if terc == 2 else "High"
    benchmark_df    = df[df["rating_tercile"] == terc]
    benchmark_label = f"ESG Rating Group: {lbl}"

# Focal-Werte
focal_pages = df.loc[df["name"] == company, "pagespdf"].iat[0]
focal_words = df.loc[df["name"] == company, "words"].iat[0]

# --------------------------------------------------------------------
# 7. Sidebar: Chart Type
# --------------------------------------------------------------------
st.sidebar.header("Chart Type")
plot_type = st.sidebar.radio(
    "Select plot type:",
    ["Strip Plot", "Bar Chart", "Histogram"],
    key="plot_type",
)

# --------------------------------------------------------------------
# 8. Header & Analysis mode
# --------------------------------------------------------------------
header_col, nav_col = st.columns([3, 1], gap="large")
with header_col:
    st.header("CSRD Benchmarking Report")
with nav_col:
    analysis_mode = st.radio(
        "",
        ["Textual Analysis", "Materiality Analysis"],
        horizontal=True,
        key="analysis_mode",
    )
    color = "#e63946" if analysis_mode == "Textual Analysis" else "#457b9d"
    st.markdown(
        f"<div style='height:3px; background:{color}; margin-top:0.25rem'></div>",
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------
# 9. Content Rendering
# --------------------------------------------------------------------
if analysis_mode == "Textual Analysis":
    col_content, col_view = st.columns([3, 1])
    with col_view:
        view = st.selectbox(
            "Analysis:", 
            ["Number of Pages", "Number of Words", "Peer Company List"],
            key="view_selector"
        )
    with col_content:
        plot_df = benchmark_df.copy()
        plot_df["highlight_label"] = np.where(
            plot_df["name"] == company, company, "Peers"
        )

        if view == "Number of Pages":
            st.subheader(f"Number of Pages ({benchmark_label})")
            if plot_type == "Strip Plot":
                plot_df["jitter"] = 0.1 * np.random.randn(len(plot_df))
                fig = px.scatter(
                    plot_df.assign(y=plot_df["jitter"]),
                        x="pagespdf",
                        y="y",
                        hover_name="name",
                        hover_data={
                            "pagespdf": True,        # zeige die Seitenzahl
                            "highlight_label": False, # verberge „Peers“ vs. Firmenname
                            "y": False               # verberge den Jitter-Wert
                        },
                        color="highlight_label",
                        color_discrete_map={company: "red", "Peers": "#1f77b4"},
                        labels={"pagespdf": "Pages", "highlight_label": ""}
                    )
                fig.add_vline(
                    x=benchmark_df["pagespdf"].mean(),
                    line_color="#1f77b4", line_width=1, opacity=0.6
                )
                fig.add_vline(
                    x=focal_pages, line_dash="dash", line_color="red", opacity=0.8
                )
                fig.update_layout(yaxis=dict(visible=False), xaxis_title="Pages")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="pagespdf", nbins=20,
                    labels={"pagespdf": "Pages"}
                )
                fig.add_vline(
                    x=benchmark_df["pagespdf"].mean(),
                    line_color="#1f77b4", line_width=1, opacity=0.6
                )
                fig.add_vline(
                    x=focal_pages, line_dash="dash", line_color="red", opacity=0.8
                )
                fig.update_layout(xaxis_title="Pages", yaxis_title="Number of Companies")
                st.plotly_chart(fig, use_container_width=True)

            else:  # Bar Chart
                avg_pages = benchmark_df["pagespdf"].mean()
                comp_df = pd.DataFrame({
                    "Group": ["Peer Group Average", focal_company],
                    "Pages": [avg_pages, focal_pages]
                })
                fig_avg = px.bar(
                    comp_df, x="Group", y="Pages", text="Pages",
                    color="Group",
                    color_discrete_map={focal_company: "red", "Benchmark Average": "#1f77b4"},
                    labels={"Pages": "Pages", "Group": ""}
                )
                fig_avg.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                fig_avg.update_layout(showlegend=False, yaxis=dict(range=[0, comp_df["Pages"].max() * 1.2]))
                st.plotly_chart(fig_avg, use_container_width=True)

                peers_df = plot_df.sort_values("pagespdf", ascending=False)
                fig2 = px.bar(
                    peers_df, x="name", y="pagespdf",
                    color="highlight_label",
                    color_discrete_map={focal_company: "red", "Peers": "#1f77b4"},
                    labels={"pagespdf": "Pages", "name": "Company", "highlight_label": ""},
                    category_orders={"name": peers_df["name"].tolist()}
                )
                fig2.update_layout(showlegend=True, legend_title_text="", xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)

        elif view == "Number of Words":
            st.subheader(f"Number of Words ({benchmark_label})")
            if plot_type == "Strip Plot":
                plot_df["jitter_w"] = 0.1 * np.random.randn(len(plot_df))

                # Hier beginnt der Aufruf von px.scatter – alle Argumente auf einer Ebene:
                fig = px.scatter(
                    plot_df.assign(y=plot_df["jitter_w"]),
                    x="words",
                    y="y",
                    hover_name="name",
                    hover_data={
                        "words": True,           # zeige nur die Wortzahl
                        "highlight_label": False,# verberge „Peers“ vs. Firmenname
                        "y": False               # verberge den Jitter-Wert
                    },
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"words": "Words", "highlight_label": ""}
                )  # <- schließende Klammer muss auf gleicher Einrückung stehen wie 'fig ='
        
                fig.add_vline(
                    x=benchmark_df["words"].mean(), line_color="#1f77b4", line_width=1, opacity=0.6
                )
                fig.add_vline(
                    x=focal_words, line_dash="dash", line_color="red", opacity=0.8
                )
                fig.update_layout(yaxis=dict(visible=False), xaxis_title="Words")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="words", nbins=20, labels={"words": "Words"}
                )
                fig.add_vline(
                    x=benchmark_df["words"].mean(), line_color="#1f77b4", line_width=1, opacity=0.6
                )
                fig.add_vline(
                    x=focal_words, line_dash="dash", line_color="red", opacity=0.8
                )
                fig.update_layout(xaxis_title="Words", yaxis_title="Number of Companies")
                st.plotly_chart(fig, use_container_width=True)

            else:  # Bar Chart
                avg_words = benchmark_df["words"].mean()
                comp_df2 = pd.DataFrame({
                    "Group": ["Peer Group Average", focal_company],
                    "Words": [avg_words, focal_words]
                })
                fig_avg2 = px.bar(
                    comp_df2, x="Group", y="Words", text="Words",
                    color="Group",
                    color_discrete_map={focal_company: "red", "Peer Group Average": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""}
                )
                fig_avg2.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                fig_avg2.update_layout(showlegend=False, yaxis=dict(range=[0, comp_df2["Words"].max() * 1.2]))
                st.plotly_chart(fig_avg2, use_container_width=True)

                peers_df2 = plot_df.sort_values("words", ascending=False)
                fig2w = px.bar(
                    peers_df2, x="name", y="words",
                    color="highlight_label",
                    color_discrete_map={focal_company: "red", "Peers": "#1f77b4"},
                    labels={"words": "Words", "name": "Company", "highlight_label": ""},
                    category_orders={"name": peers_df2["name"].tolist()}
                )
                fig2w.update_layout(showlegend=True, legend_title_text="", xaxis_tickangle=-45)
                st.plotly_chart(fig2w, use_container_width=True)

        else:
            st.subheader("Peer Company List")
            df_display = (
                benchmark_df[
                    ["name", "country", "trbceconomicsectorname", "pagespdf", "words"]
                ]
                .sort_values(by="pagespdf")
                .reset_index()          # ← Index ausblenden, nicht verwerfen
           	)
            st.write(df_display.to_dict(orient="records"))

else:
    st.subheader("Materiality Analysis")
    st.info("This section is under construction.")
