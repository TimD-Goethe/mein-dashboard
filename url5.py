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
df = pd.read_csv("summary_with_meta.csv")

# aus "trbceconomicsectorname" wird "sector"
df.rename(columns={"trbceconomicsectorname": "sector"}, inplace=True)

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

# 5.1 Prüfen, ob für die gewählte Firma ein rating_tercile vorliegt
company_row   = df.loc[df["name"] == company]
rating_exists = pd.notna(company_row["rating_tercile"].iat[0])

# 5.2 Optionen-Liste zusammenbauen
peer_group_opts = [
    "All CSRD First Wave",
    "Country Peers",
    "Sector Peers",
    "Size Peers",
]
if rating_exists:
    peer_group_opts.append("Rating Peers")

# 5.3 Radio-Widget mit nur gültigen Optionen
benchmark_type = st.sidebar.radio(
    "Select Your Peer Group:",
    peer_group_opts,
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
    country         = df.loc[df["name"] == company, "country"].iat[0]
    benchmark_df    = df[df["country"] == country]
    benchmark_label = f"Country Peers: {country}"
elif benchmark_type == "Sector Peers":
    sector          = df.loc[df["name"] == company, "sector"].iat[0]
    benchmark_df    = df[df["sector"] == sector]
    benchmark_label = f"Sector Peers: {sector}"
elif benchmark_type == "Size Peers":
    terc            = df.loc[df["name"] == company, "market_cap_tercile"].iat[0]
    lbl             = "Small" if terc == 1 else "Mid" if terc == 2 else "Large"
    benchmark_df    = df[df["market_cap_tercile"] == terc]
    benchmark_label = f"Market Cap Group: {lbl}"

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
# 1. Header + Untertitel + Radio-Buttons in einem columns-Aufruf
header_col, nav_col = st.columns([3, 1], gap="large")

with header_col:
    st.header("CSRD Dashboard")
    st.markdown(
        """
        <p style="
            font-size: 16px;
            color: #555;
            margin-top: -8px;
            margin-bottom: 1rem;
        ">
          Please select a peer group and variable of interest to benchmark your company’s
          CSRD reporting. All analyses are based on companies’ 2024 sustainability reports.
        </p>
        """,
        unsafe_allow_html=True,
    )

with nav_col:
    analysis_mode = st.radio(
        "",
        ["Textual Analysis"],
        horizontal=True,
        key="analysis_mode",
    )

# 2. Voll-breiter, farbiger Strich
color = "#e63946" if analysis_mode == "Textual Analysis" else "#457b9d"
st.markdown(
    f"""
    <div style="
      width: 100%;
      height: 4px;
      background-color: {color};
      margin: 0 0 1rem 0;
      padding: 0;
    "></div>
    """,
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

            # vorher sicherstellen, dass mean_pages definiert ist
            mean_pages = benchmark_df["pagespdf"].mean()

            if plot_type == "Strip Plot":
                plot_df = benchmark_df.copy()
                # Company ergänzen, falls sie nicht zu den ausgewählten Peers gehört
                if company not in plot_df["name"].values:
                    focal_row = df[df["name"] == company]
                    plot_df = pd.concat([plot_df, focal_row], ignore_index=True)
            
                # Highlight-Label zuweisen
                plot_df["highlight_label"] = np.where(
                    plot_df["name"] == company, company, "Peers"
                )

                # 1) Jitter hinzufügen
                plot_df["jitter"] = 0.1 * np.random.randn(len(plot_df))

                # 2) Scatter-Plot
                fig = px.scatter(
                    plot_df.assign(y=plot_df["jitter"]),
                    x="pagespdf",
                    y="y",
                    hover_name="name",
                    hover_data={
                        "pagespdf": True,        # zeige die Seitenzahl
                        "highlight_label": False,# verberge „Peers“ vs. Firmenname
                        "y": False               # verberge den Jitter-Wert
                    },
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"pagespdf": "Pages", "highlight_label": ""}
                )

                # → hier die y-Achse komplett ausblenden und Range setzen:
                fig.update_yaxes(
                    showticklabels=False,   # keine Achsenbeschriftungen
                    title_text="",          # keine Achsentitel
                    range=[-0.5, 0.5],      # nur von -0.5 bis +0.5
                    showgrid=False,         # (optional) keine horizontalen Linien
                    zeroline=False          # (optional) keine Null-Linie
                )
                
                # 3) Peer Average als durchgezogene blaue Linie
                fig.add_trace(go.Scatter(
                    x=[mean_pages, mean_pages],
                    y=[-0.5, +0.5],
                    mode="lines",
                    line=dict(color="#1f77b4", width=2, dash="solid"),
                    name="Peer Average"
                ))

                # 4) Focal Company als rote, gestrichelte Linie
                fig.add_trace(go.Scatter(
                    x=[focal_pages, focal_pages],
                    y=[-0.5, +0.5],
                    mode="lines",
                    line=dict(color="red", width=2, dash="dash"),
                    name=company
                ))

                # 5) Y-Achse einschränken, damit die Linien nicht zu lang sind
                fig.update_yaxes(range=[-1, 1])

                # 6) Plot ausgeben
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="pagespdf", nbins=20,
                    labels={"pagespdf": "Pages"}
                )
                # Linien bleiben hier als VLines
                fig.add_vline(
                    x=mean_pages,
                    line_color="#1f77b4",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="Peer Average",
                    annotation_position="top right"
                )
                fig.add_vline(
                    x=focal_pages,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=company,
                    annotation_position="top left"
                )
                fig.update_layout(xaxis_title="Pages", yaxis_title="Number of Companies")
                st.plotly_chart(fig, use_container_width=True)

            else:  # Bar Chart
                # 1) Peer Average vs. Focal Company
                avg_pages = benchmark_df["pagespdf"].mean()
                comp_df = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "Pages": [avg_pages, focal_pages]
                })
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="Pages",
                    text="Pages",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Pages": "Pages", "Group": ""}
                )
                fig_avg.update_traces(
                    texttemplate="%{text:.0f}",
                    textposition="outside",
                    width=0.5
                )
                fig_avg.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis=dict(range=[0, comp_df["Pages"].max() * 1.2])
                )
                st.plotly_chart(fig_avg, use_container_width=True)
            
                # 2) Detail-Bar-Chart aller Peer-Unternehmen
                peers_df = plot_df.sort_values("pagespdf", ascending=False)
                fig2 = px.bar(
                    peers_df,
                    x="name",
                    y="pagespdf",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"pagespdf": "Pages", "name": "Company", "highlight_label": ""},
                    category_orders={"name": peers_df["name"].tolist()}
                )
                fig2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig2, use_container_width=True)


            # Fußnote
            st.caption("Number of pages of companies’ sustainability reports.")

        
        elif view == "Number of Words":
            st.subheader(f"Number of Words ({benchmark_label})")

            # 1) Peer-Average berechnen
            mean_words = benchmark_df["words"].mean()

            if plot_type == "Strip Plot":
                plot_df = benchmark_df.copy()
                # Company ergänzen, falls sie nicht zu den ausgewählten Peers gehört
                if company not in plot_df["name"].values:
                    focal_row = df[df["name"] == company]
                    plot_df = pd.concat([plot_df, focal_row], ignore_index=True)
            
                # Highlight-Label zuweisen
                plot_df["highlight_label"] = np.where(
                    plot_df["name"] == company, company, "Peers"
                )
                # Jitter zur Visualisierung
                plot_df["jitter_w"] = 0.1 * np.random.randn(len(plot_df))

                # Scatter-Plot
                fig = px.scatter(
                    plot_df.assign(y=plot_df["jitter_w"]),
                    x="words",
                    y="y",
                    hover_name="name",
                    hover_data={
                        "words": True,           # Zeige die Wortzahl
                        "highlight_label": False,# Verberge das Label
                        "y": False               # Verberge den Jitter-Wert
                    },
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"words": "Words", "highlight_label": ""}
                )


                # → hier die y-Achse komplett ausblenden und Range setzen:
                fig.update_yaxes(
                    showticklabels=False,   # keine Achsenbeschriftungen
                    title_text="",          # keine Achsentitel
                    range=[-0.5, 0.5],      # nur von -0.5 bis +0.5
                    showgrid=False,         # (optional) keine horizontalen Linien
                    zeroline=False          # (optional) keine Null-Linie
                )

                
                # Peer Average als durchgezogene blaue Linie
                fig.add_trace(go.Scatter(
                    x=[mean_words, mean_words],
                    y=[-0.5, +0.5],
                    mode="lines",
                    line=dict(color="#1f77b4", width=2, dash="solid"),
                    name="Peer Average"
                ))

                # Focal Company als rote, gestrichelte Linie
                fig.add_trace(go.Scatter(
                    x=[focal_words, focal_words],
                    y=[-0.5, +0.5],
                    mode="lines",
                    line=dict(color="red", width=2, dash="dash"),
                    name=company
                ))

                # Y-Achse einschränken
                fig.update_yaxes(range=[-1, 1])

                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="words", nbins=20,
                    labels={"words": "Words"}
                )
                # Peer Average als vertikale Linie mit Beschriftung
                fig.add_vline(
                    x=mean_words,
                    line_color="#1f77b4",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="Peer Average",
                    annotation_position="top right"
                )
                # Focal Company
                fig.add_vline(
                    x=focal_words,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=company,
                    annotation_position="top left"
                )
                fig.update_layout(xaxis_title="Words", yaxis_title="Number of Companies")
                st.plotly_chart(fig, use_container_width=True)

            else:  # Bar Chart
                # 1) Peer Average vs. Focal Company
                avg_words = benchmark_df["words"].mean()
                comp_df2 = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "Words": [avg_words, focal_words]
                })
                fig_avg2 = px.bar(
                    comp_df2,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""}
                )
                fig_avg2.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                fig_avg2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis=dict(range=[0, comp_df2["Words"].max() * 1.2])
                )
                st.plotly_chart(fig_avg2, use_container_width=True)
            
                # 2) Alle einzelnen Peer-Unternehmen
                peers_df = plot_df.sort_values("words", ascending=False)
                fig2w = px.bar(
                    peers_df,
                    x="name",
                    y="words",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"words": "Words", "name": "Company", "highlight_label": ""},
                    category_orders={"name": peers_df["name"].tolist()},
                )
                fig2w.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig2w, use_container_width=True)

            # Fußnote
            st.caption("Number of words in companies’ sustainability statements.")

        else:
            st.subheader("Peer Company List")

            st.caption("Companies included in this list, based on your peer group selection.")
            
            # 1) DataFrame ohne echten Index
            df_display = (
                benchmark_df
                [["name","country","sector","pagespdf","words"]]
                .sort_values(by="pagespdf")
                .reset_index(drop=True)
            )

            md = df_display.to_markdown(index=False)
            st.markdown(md, unsafe_allow_html=True)
