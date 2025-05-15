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
company_list = df["company"].dropna().unique().tolist()
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

# 5.2 Optionen-Liste zusammenbauen
peer_group_opts = [
    "Sector Peers",
    "All CSRD First Wave",
    "Country Peers",
    "Size Peers",
]

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
if benchmark_type == "Sector Peers":
    sector          = df.loc[df["company"] == company, "SASB_industry"].iat[0]
    benchmark_df    = df[df["SASB_industry"] == sector]
    benchmark_label = f"Sector Peers: {sector}"
elif benchmark_type == "All CSRD First Wave":
    benchmark_df    = df.copy()
    benchmark_label = "All CSRD First Wave"
elif benchmark_type == "Country Peers":
    country         = df.loc[df["company"] == company, "country"].iat[0]
    benchmark_df    = df[df["country"] == country]
    benchmark_label = f"Country Peers: {country}"
elif benchmark_type == "Size Peers":
    terc            = df.loc[df["name"] == company, "market_cap_tercile"].iat[0]
    lbl             = "Small" if terc == 1 else "Mid" if terc == 2 else "Large"
    benchmark_df    = df[df["market_cap_tercile"] == terc]
    benchmark_label = f"Market Cap Group: {lbl}"
if peer_selection:
    benchmark_df    = df[df["company"].isin(peer_selection)]
    benchmark_label = f"Selected Peers ({len(benchmark_df)} firms)"

# Focal-Werte
focal_pages = df.loc[df["company"] == company, "Sustainability_Page_Count"].iat[0]
focal_words = df.loc[df["company"] == company, "words"].iat[0]

# --------------------------------------------------------------------
# 7. Sidebar: Chart Type
# --------------------------------------------------------------------
st.sidebar.header("Chart Type")
plot_type = st.sidebar.radio(
    "Select plot type:",
    ["Bar Chart", "Histogram"],
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
            plot_df["company"] == company, company, "Peers"
        )

        if view == "Number of Pages":
            st.subheader(f"Number of Pages ({benchmark_label})")

            # vorher sicherstellen, dass mean_pages definiert ist
            mean_pages = benchmark_df["Sustainability_Page_Count"].mean()

            if plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="Sustainability_Page_Count", nbins=20,
                    labels={"Sustainability_Page_Count": "Pages"}
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

            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart aller Peer-Unternehmen, horizontale Balken
                # nach Wert absteigend sortieren
                peers_df = plot_df.sort_values("Sustainability_Page_Count", ascending=False)

                
                mean_pages = benchmark_df["Sustainability_Page_Count"].mean()

                 # Wir drehen die Firmenliste, damit die größte ganz oben landet
                y_order = peers_df["company"].tolist()[::-1]
                
                fig2 = px.bar(
                    peers_df,
                    x="Sustainability_Page_Count",
                    y="company",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "Sustainability_Page_Count": "Pages",
                        "company": "Company",
                        "highlight_label": ""
                    },
                    # hier verwenden wir die umgedrehte Liste
                    category_orders={"company": y_order}
                )
                
                fig2.add_vline(
                    x=mean_pages,
                    line_dash="dash",
                    line_color="#1f77b4",
                    annotation_text="Peer Average",
                    annotation_position="top left"
                )
                
                fig2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={
                        "categoryorder": "array",
                        # auch hier die umgedrehte Liste, damit "Imerys" ganz oben steht
                        "categoryarray": y_order
                    }
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
                # 2) Peer Average vs. Focal Company, jetzt als vertikale Balken mit rotem Balken links
                avg_pages = mean_pages
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
                # rote Firma links (als erste Kategorie) anzeigen
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_avg, use_container_width=True)

            # Fußnote
            st.caption("Number of pages of companies’ sustainability reports.")

        
        elif view == "Number of Words":
            st.subheader(f"Number of Words ({benchmark_label})")

            # 1) Peer-Average berechnen
            mean_words = benchmark_df["words"].mean()

            if plot_type == "Histogram":
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

            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart aller Peer-Unternehmen als horizontale Balken (Words)
                peers_df = plot_df.sort_values("words", ascending=False)
                mean_words = benchmark_df["words"].mean()
            
                # categoryarray umdrehen, damit die höchste ganz oben ist
                y_order = peers_df["company"].tolist()[::-1]
            
                fig2w = px.bar(
                    peers_df,
                    x="words",
                    y="company",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"words": "Words", "company": "Company", "highlight_label": ""},
                    category_orders={"company": y_order},
                )
                # vertikale Peer-Average-Linie
                fig2w.add_vline(
                    x=mean_words,
                    line_dash="dash",
                    line_color="#1f77b4",
                    annotation_text="Peer Average",
                    annotation_position="top left",
                )
                # eindeutige Element-ID verhindern Kollision
                fig2w.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={"categoryorder": "array", "categoryarray": y_order},
                    xaxis_title="Words",
                )
                st.plotly_chart(fig2w, use_container_width=True, key="words_detail")
            
                # 2) Peer Average vs. Focal Company als vertikale Balken (roter Balken links)
                comp_df2 = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "Words": [mean_words, focal_words],
                })
                fig_avg2 = px.bar(
                    comp_df2,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""},
                )
                # sortiere x-Achse so, dass red Company links steht
                fig_avg2.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False,
                    yaxis_title="Words",
                )
                fig_avg2.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_avg2, use_container_width=True, key="words_comparison")
            
                st.caption("Number of words in companies’ sustainability statements.")
        else:
            st.subheader("Peer Company List")

            st.caption("Companies included in this list, based on your peer group selection.")
            
            # 1) DataFrame ohne echten Index
            df_display = (
                benchmark_df
                [["company","country","SASB_industry","Sustainability_Page_Count","words"]]
                .sort_values(by="Sustainability_Page_Count")
                .reset_index(drop=True)
            )

            md = df_display.to_markdown(index=False)
            st.markdown(md, unsafe_allow_html=True)
