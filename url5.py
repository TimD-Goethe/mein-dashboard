import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import unquote, quote

#-------------------------------------------------------------------------
# 1. Page config
#-------------------------------------------------------------------------
st.set_page_config(page_title="CSRD Dashboard", layout="wide")

# 1a. Globales CSS – direkt nach set_page_config, vor allen st.columns(...)
st.markdown(
    """
    <style>
      /* 1) Toolbar (Hamburger/Share/…) ausblenden */
      [data-testid="stToolbar"] {
        display: none !important;
      }

      /* 2) Hintergrund-Gradient über die gesamte App */
      html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(
          180deg,
          #E3DFFF 0%,
          #E3DFFF 60%,
          #FFFFFF 100%
        ) !important;
      }

      /* 3) Sidebars einfärben + Schatten (erste und letzte Column) */
      section[data-testid="column"]:first-of-type,
      section[data-testid="column"]:last-of-type {
        background-color: #F3E8FF !important;
        box-shadow:       2px 2px 8px rgba(0,0,0,0.1) !important;
        border-radius:    0.5rem;
        padding:          1rem;
      }

      /* 4) Mittlere Column transparent + alle Schatten killen */
      section[data-testid="column"]:nth-of-type(2) {
        background-color: transparent !important;
        box-shadow:       none        !important;
      }
      section[data-testid="column"]:nth-of-type(2) * {
        box-shadow: none               !important;
        background: transparent        !important;
      }

      /* 5) In der mittleren Column: die Standard-.block-container-Abstände auf 0 */
      [data-testid="stAppViewContainer"]
        > div[class*="block-container"]
        > section[data-testid="column"]:nth-of-type(2)
        > div[class*="block-container"] {
        padding-left:  0 !important;
        padding-right: 0 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

#-------------------------------------------------------------------------------------
# 2. Daten laden
#--------------------------------------------------------------------------------------
df = pd.read_csv("summary_with_meta_with_mcap_and_cat.csv")

#--------------------------------------------------------------------------------------
# 3. URL-Param & Default
#--------------------------------------------------------------------------------------
company_list    = df["company"].dropna().unique().tolist()
mapping_ci      = {n.strip().casefold(): n for n in company_list}
raw             = st.query_params.get("company", [""])[0] or ""
raw             = unquote(raw)
default_company = mapping_ci.get(raw.strip().casefold(), company_list[0])

#-----------------------------------------------------------------------------------------
# 4. Layout: drei Columns
#------------------------------------------------------------------------------------------
left, main, right = st.columns([2, 5, 2])

# 4a. Linke Sidebar: Company + Top-Level Radio + Unter-Radio
with left:
    # Company dropdown
    default_idx = company_list.index(default_company) if default_company in company_list else 0
    company = st.selectbox(
        "Select a company:",
        options=company_list,
        index=default_idx,
        key="company_selector",
    )

    # Top-Level Radio: steuert die beiden Hauptblöcke
    mode = st.radio(
        "Choose benchmark mode:",
        ["Benchmark Group", "Cross Country / Cross Industry"],
        key="mode_selector",
    )

    # Unter-Radio je nach gewähltem mode
    if mode == "Benchmark Group":
        st.subheader("Benchmark Group")
        benchmark_type = st.radio(
            "Select a peer group:",
            [
              "Sector Peers",
              "Country Peers",
              "Market Cap Peers",
              "All CSRD First Wave",
              "Choose specific peers"
            ],
            key="benchmark_type"
        )
        if benchmark_type == "Choose specific peers":
            peer_selection = st.multiselect(
                "Or choose specific peer companies:",
                options=company_list,
                default=[]
            )
        else:
            peer_selection = []

    else:
        st.subheader("Cross Country / Cross Industry Benchmarking")
        benchmark_type = st.radio(
            "Select a cross-benchmark type:",
            ["Between Country Comparison", "Between Industry Comparison"],
            key="cross_type"
        )
        peer_selection = []

# 4b. Rechte Spalte: View & Chart Type
with right:
    st.header("What do you want to benchmark?")

    # ─── CSS für die Separatoren ───
    st.markdown(
        """
        <style>
          /* Separator-Labels: grau + kein Mausklick */
          div[data-testid="stRadio"] > label:nth-of-type(3),
          div[data-testid="stRadio"] > label:nth-of-type(5),
          div[data-testid="stRadio"] > label:nth-of-type(9) {
            color: #888 !important;
            pointer-events: none !important;
          }

          /* Deren Radio-Inputs komplett ausblenden */
          div[data-testid="stRadio"] > label:nth-of-type(3) input,
          div[data-testid="stRadio"] > label:nth-of-type(5) input,
          div[data-testid="stRadio"] > label:nth-of-type(9) input {
            display: none !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # ─────────────────────────────────

    # Liste aller Einträge (inkl. Trennlinien)
    view_options = [
        "pages","words","sep1","esrs","sep2",
        "numbers","tables","images","sep3",
        "lang_std","lang_cplx","tone",
    ]
    # Lesbare Texte
    view_labels = {
        "pages":"Number of Pages",
        "words":"Number of Words",
        "sep1":"––––––––––––––––",
        "esrs":"Words per ESRS standard",
        "sep2":"––––––––––––––––",
        "numbers":"Numbers",
        "tables":"Tables",
        "images":"Images",
        "sep3":"––––––––––––––––",
        "lang_std":"Standardized Language",
        "lang_cplx":"Complex Language",
        "tone":"Tone",
    }

    view = st.radio(
        "Select Your View:",
        view_options,
        format_func=lambda k: view_labels[k],
        key="view_selector",
    )

    # Fallback, falls doch jemand eine Sep-Zeile anklickt (eigentlich ausgeblendet)
    if view.startswith("sep"):
        st.warning("Bitte wähle eine echte Option, keine Trennlinie.")
        st.stop()

    st.header("Chart Type")
    plot_type = st.radio(
        "",
        ["Bar Chart", "Histogram"],
        key="plot_type",
    )

# --------------------------------------------------------------------
# 6. Build `benchmark_df`
# --------------------------------------------------------------------
if benchmark_type == "Sector Peers":
    sector          = df.loc[df["company"] == company, "SASB_industry"].iat[0]
    benchmark_df    = df[df["SASB_industry"] == sector]
    benchmark_label = f"Sector Peers: {sector}"

elif benchmark_type == "Country Peers":
    country         = df.loc[df["company"] == company, "country"].iat[0]
    benchmark_df    = df[df["country"] == country]
    benchmark_label = f"Country Peers: {country}"

elif benchmark_type == "Market Cap Peers":
    terc            = df.loc[df["company"] == company, "Market_Cap_Cat"].iat[0]
    lbl             = (
        "Very Small" if terc == 1 else
        "Small"      if terc == 2 else
        "Medium"     if terc == 3 else
        "Large"      if terc == 4 else
        "Huge"
    )
    benchmark_df    = df[df["Market_Cap_Cat"] == terc]
    benchmark_label = f"Market Cap Peers: {lbl}"

elif benchmark_type == "All CSRD First Wave":
    benchmark_df    = df.copy()
    benchmark_label = "All CSRD First Wave"

elif benchmark_type == "Choose specific peers":
    sel = set(peer_selection) | {company} if peer_selection else {company}
    benchmark_df    = df[df["company"].isin(sel)]
    benchmark_label = f"Selected Peers ({len(benchmark_df)} firms)"

elif benchmark_type == "Between Country Comparison":
    focal_country   = df.loc[df["company"] == company, "country"].iat[0]
    country_df      = df[df["country"] == focal_country]
    rest_df         = df[df["country"] != focal_country]
    benchmark_df    = pd.concat([
                        country_df.assign(_group=focal_country),
                        rest_df.assign(_group="Others")
                     ], ignore_index=True)
    benchmark_label = f"{focal_country} vs Others"

elif benchmark_type == "Between Industry Comparison":
    focal_ind        = df.loc[df["company"] == company, "SASB_industry"].iat[0]
    industry_df      = df[df["SASB_industry"] == focal_ind]
    rest_ind_df      = df[df["SASB_industry"] != focal_ind]
    benchmark_df     = pd.concat([
                        industry_df.assign(_group=focal_ind),
                        rest_ind_df.assign(_group="Others")
                     ], ignore_index=True)
    benchmark_label  = f"{focal_ind} vs Others"

# focal values
focal_pages = df.loc[df["company"] == company, "Sustainability_Page_Count"].iat[0]
focal_words = df.loc[df["company"] == company, "words"].iat[0]

# --------------------------------------------------------------------
# 8. Main-Bereich: Header + Trennstrich + erste Content-Spalte
# --------------------------------------------------------------------
with main:
    header_col, _ = st.columns([3, 1], gap="large")
    with header_col:
        st.header("CSRD Dashboard")
        st.markdown(
            """
            <p style="
              font-size:16px;
              color:#555;
              margin-top:-8px;
              margin-bottom:1rem;
            ">
              Please select a peer group and variable of interest to benchmark your company’s 
              CSRD reporting. All analyses are based on companies’ 2024 sustainability reports.
            </p>
            """,
            unsafe_allow_html=True,
        )
    color = "#b34747"
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

    # ----------------------------------------------------------------
    # 9. Content Rendering: zwei Unterspalten in Main
    # ----------------------------------------------------------------
    col_content, col_view = st.columns([5, 1])

    with col_content:
        plot_df = benchmark_df.copy()
        plot_df["highlight_label"] = np.where(
            plot_df["company"] == company, company, "Peers"
        )

        if view == "Number of Pages":
            st.subheader(f"Number of Pages ({benchmark_label})")
    
            # vorher sicherstellen, dass mean_pages definiert ist
            mean_pages = benchmark_df["Sustainability_Page_Count"].mean()
            focal_pages = df.loc[df["company"] == company, "Sustainability_Page_Count"].iat[0]
    
    
    
            if benchmark_type == "Between Country Comparison" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder‐Durchschnitt vorbereiten (egal ob vorher schon definiert)
                country_avg = (
                    df
                    .groupby("country")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Pages")
                )
                
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                overall_avg = country_avg["Pages"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Pages"].iat[0]
                
                # 2) Einfaches Histogramm aller Länder‐Durchschnitte in dunkelblau
                fig = px.histogram(
                    country_avg,
                    x="Pages",
                    nbins=20,  # nach Belieben anpassen
                    opacity=0.8,
                    labels={"Pages": "Pages"},
                )
                
                # 4) Alle Balken in Dunkelblau (#1f77b4)
                fig.update_traces(marker_color="#1f77b4")
                
                # 4) V-Line für All Countries Avg (schwarz gestrichelt)
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_size=14,
                )
                
                # 5) V-Line für Austria Avg (rot gestrichelt), ohne extra Balken
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=14,
                )
                
                # 6) Legende ausblenden und Achsentitel
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Pages",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
            
            elif plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="Sustainability_Page_Count", nbins=20,
                    labels={"Sustainability_Page_Count": "Pages", "_group" : "Group"}
                )
    
                # 4) Alle Balken in Dunkelblau (#1f77b4)
                fig.update_traces(marker_color="#1f77b4")
    
                # Linien bleiben hier als VLines
                fig.add_vline(
                    x=mean_pages,
                    line_dash="dash",
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig.add_vline(
                    x=focal_pages,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig.update_layout(xaxis_title="Pages", yaxis_title="Number of Companies")
                st.plotly_chart(fig, use_container_width=True)
    
            elif benchmark_type == "Between Country Comparison" and plot_type == "Bar Chart":
                # 1) Bestimme das Land des gewählten Unternehmens
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Berechne das Länderdurchschnitt
                country_avg = (
                    df
                    .groupby("country")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Pages")
                )
            
                # 3) Sortiere von groß nach klein
                country_avg = country_avg.sort_values("Pages", ascending=False)
            
                # 4) Kürze die Ländernamen auf max. 15 Zeichen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 5) Behalte die Trunkierung auch in der Sortierreihenfolge
                y_order = country_avg["country_short"].tolist()
            
                # 6) Markiere Dein Land
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],  # markiere die gekürzte Variante
                    "Other Countries"
                )
            
                # 7) Baue das horizontale Balkendiagramm
                fig_ctry = px.bar(
                    country_avg,
                    x="Pages",
                    y="country_short",           # ← hier die gekürzten Labels
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country_short": y_order},
                    labels={"Pages":"Pages","country_short":""},
                )
            
                # 8) Peer‐Average‐Linie
                overall_avg = df["Sustainability_Page_Count"].mean()
                fig_ctry.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                
            
                # 9) Werte außen anzeigen
                fig_ctry.update_traces(
                    texttemplate="%{x:.0f}",
                    textposition="outside",
                    cliponaxis=False
                )
            
                # 10) Legende & Achsentitel
                fig_ctry.update_layout(
                    showlegend=False,
                    xaxis_title="Pages",
                )
            
                st.plotly_chart(fig_ctry, use_container_width=True)
                            
    
            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart aller Peer-Unternehmen, horizontale Balken
                #    nach Wert absteigend sortieren
                peers_df = plot_df.sort_values("Sustainability_Page_Count", ascending=False)
                
                mean_pages = benchmark_df["Sustainability_Page_Count"].mean()
                
                # 2) Wir drehen die Firmenliste, damit die größte ganz oben landet
                #    aber diesmal mit dem gekürzten Namen
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
                
                # 3) Erstelle das horizontale Balkendiagramm anhand der Kurz-Namen
                fig2 = px.bar(
                    peers_df,
                    x="Sustainability_Page_Count",
                    y="company_short",               # hier die gekürzte Spalte
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "Sustainability_Page_Count": "Pages",
                        "company_short": "Company",  # Achsenbeschriftung anpassen
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                )
                
                # 4) V-Line für Peer Average
                fig2.add_vline(
                    x=mean_pages,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                
                # 5) Layout anpassen, damit die Kurz-Namen korrekt oben stehen
                fig2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={
                        "categoryorder": "array",
                        "categoryarray": y_order_short,
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
    
            if benchmark_type == "Between Country Comparison" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder‐Durchschnitt der Wortanzahlen berechnen
                country_avg_words = (
                    df
                    .groupby("country")["words"]
                    .mean()
                    .reset_index(name="Words")
                )
            
                # 3) Gesamt‐ und Focal‐Durchschnitt
                overall_avg_words = country_avg_words["Words"].mean()
                focal_avg_words   = country_avg_words.loc[
                    country_avg_words["country"] == focal_country, "Words"
                ].iat[0]
            
                # 4) Histogramm aller Länder‐Durchschnitte in Dunkelblau
                fig = px.histogram(
                    country_avg_words,
                    x="Words",
                    nbins=20,
                    opacity=0.8,
                    labels={"Words": "Words"},
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 5) V-Line für All Countries Avg (schwarz, gestrichelt)
                fig.add_vline(
                    x=overall_avg_words,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_size=14,
                )
            
                # 6) V-Line für Focal Country Avg (rot, gestrichelt)
                fig.add_vline(
                    x=focal_avg_words,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=14,
                )
            
                # 7) Layout‐Feinschliff
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
            
                st.plotly_chart(fig, use_container_width=True)
    
    
            
            elif benchmark_type == "Between Country Comparison" and plot_type == "Bar Chart":
                # 1) Bestimme das Land des gewählten Unternehmens
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Berechne den Durchschnitt der Wörter pro Land
                country_avg_words = (
                    df
                    .groupby("country")["words"]
                    .mean()
                    .reset_index(name="Words")
                )
            
                # 3) Sortiere so, dass das kleinste Mittel unten und das größte ganz oben erscheint
                country_avg_words = country_avg_words.sort_values("Words", ascending=False)
                y_order = country_avg_words["country"].tolist()

                 # 4) Kürze die Ländernamen auf max. 15 Zeichen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Füge eine Markierungsspalte hinzu (Focal Country vs. Others)
                country_avg_words["highlight"] = np.where(
                    country_avg_words["country"] == focal_country,
                    "Focal Country",
                    "Other Countries"
                )
            
                # 5) Erstelle das horizontale Balkendiagramm
                fig_ctry = px.bar(
                    country_avg_words,
                    x="Words",
                    y="country",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        "Focal Country": "red",
                        "Other Countries": "#1f77b4"
                    },
                    labels={"Words": "Words", "country": ""},
                    category_orders={"country": y_order},
                )
            
                # 6) Gesamt- und Focal-Durchschnitt berechnen
                overall_avg_words = country_avg_words["Words"].mean()
                focal_avg_words   = country_avg_words.loc[
                    country_avg_words["country"] == focal_country, "Words"
                ].iat[0]
            
                # 7) Schwarze Peer-Average-Linie (alle Länder)
                fig_ctry.add_vline(
                    x=overall_avg_words,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                     
                # 9) Layout-Anpassungen: Legende aus, Werte außen anzeigen
                fig_ctry.update_traces(
                    texttemplate="%{x:.0f}",
                    textposition="outside",
                    cliponaxis=False
                )
                fig_ctry.update_layout(
                    showlegend=False,
                    xaxis_title="Words",
                )
            
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # 10) Kompakter Vergleich: Focal vs. Durchschnitt aller anderen Länder
                other_mean_words = country_avg_words.loc[
                    country_avg_words["country"] != focal_country, "Words"
                ].mean()
            
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other Countries"],
                    "Words": [focal_avg_words, other_mean_words]
                })
            
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={
                        focal_country:   "red",
                        "Other Countries": "#1f77b4"
                    },
                    labels={"Words": "Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=False,
                    yaxis_title="Words"
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_cmp, use_container_width=True)
    
    
            elif plot_type == "Histogram":
                fig = px.histogram(
                    plot_df, x="words", nbins=20,
                    labels={"words": "Words"}
                )
    
                # 4) Alle Balken in Dunkelblau (#1f77b4)
                fig.update_traces(marker_color="#1f77b4")
    
                # Linien bleiben hier als VLines
                fig.add_vline(
                    x=mean_words,
                    line_dash="dash",
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig.add_vline(
                    x=focal_words,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig.update_layout(xaxis_title="Words", yaxis_title="Number of Companies")
                st.plotly_chart(fig, use_container_width=True)
    
            
            elif plot_type == "Bar Chart":
                # 1) Peer-DF sortieren, Mean berechnen
                peers_df  = plot_df.sort_values("words", ascending=False)
                mean_words = benchmark_df["words"].mean()
            
                # 2) Kurzspalte anlegen
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
            
                # 3) categoryarray aus Kurzspalte (umgekehrt für horizontales Bar-Chart)
                y_order_short = peers_df["company_short"].tolist()[::-1]
            
                # 4) Chart mit company_short
                fig2w = px.bar(
                    peers_df,
                    x="words",
                    y="company_short",                  # ← hier die Kurzspalte verwenden
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "words":           "Words",
                        "company_short":   "Company",   # die Achsenbeschriftung umbiegen
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                    hover_data=["company"]               # optional: vollständiger Name im Tooltip
                )
            
                # 5) Peer-Average-Linie
                fig2w.add_vline(
                    x=mean_words,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 6) Layout anpassen
                fig2w.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={
                        "categoryorder": "array",
                        "categoryarray":  y_order_short
                    },
                    xaxis_title="Words"
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
    
    
        elif view == "Sentiment":
            
            if benchmark_type == "Between Country Comparison" and plot_type == "Bar Chart":
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 1) Länder-Durchschnitte berechnen
                country_avg = (
                    df
                    .groupby("country")[["words_pos", "words_neg"]]
                    .mean()
                    .reset_index()
                )
            
                # 2) Für positive Wörter: sortieren & highlight-Spalte
                pos_ctry = country_avg.sort_values("words_pos", ascending=False)
                pos_ctry["highlight"] = np.where(
                    pos_ctry["country"] == focal_country,
                    focal_country,
                    "Other Countries"
                )
                y_order_pos = pos_ctry["country"].tolist()

                 # 4) Kürze die Ländernamen auf max. 15 Zeichen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 3) Bar Chart positive Wörter pro Land
                fig_pos = px.bar(
                    pos_ctry,
                    x="words_pos",
                    y="country",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country:   "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country": y_order_pos},
                    labels={"words_pos": "# Positive Words", "country": ""}
                )
                # Peer-Average (aller Länder) als schwarze Linie
                overall_pos = country_avg["words_pos"].mean()
                fig_pos.add_vline(
                    x=overall_pos,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig_pos.update_layout(showlegend=False, xaxis_title="# Positive Words")
                st.subheader("Positive Words by Country")
                st.plotly_chart(fig_pos, use_container_width=True)
            
            
                # 4) Dasselbe für negative Wörter
                neg_ctry = country_avg.sort_values("words_neg", ascending=False)
                neg_ctry["highlight"] = np.where(
                    neg_ctry["country"] == focal_country,
                    focal_country,
                    "Other Countries"
                )
                y_order_neg = neg_ctry["country"].tolist()

                 # 4) Kürze die Ländernamen auf max. 15 Zeichen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                fig_neg = px.bar(
                    neg_ctry,
                    x="words_neg",
                    y="country",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country:   "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country": y_order_neg},
                    labels={"words_neg": "# Negative Words", "country": ""}
                )
                overall_neg = country_avg["words_neg"].mean()
                fig_neg.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig_neg.update_layout(showlegend=False, xaxis_title="# Negative Words")
                st.subheader("Negative Words by Country")
                st.plotly_chart(fig_neg, use_container_width=True)
            
            
                # 5) Kompaktvergleich: focal country vs alle anderen
                focal_pos = country_avg.loc[country_avg["country"] == focal_country, "words_pos"].iat[0]
                focal_neg = country_avg.loc[country_avg["country"] == focal_country, "words_neg"].iat[0]
                other_pos = country_avg.loc[country_avg["country"] != focal_country, "words_pos"].mean()
                other_neg = country_avg.loc[country_avg["country"] != focal_country, "words_neg"].mean()
            
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other Countries"],
                    "Positive": [focal_pos, other_pos],
                    "Negative": [focal_neg, other_neg]
                })
            
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y=["Positive", "Negative"],
                    barmode="group",
                    color_discrete_sequence=["#E10600", "#1f77b4"],
                    labels={"value": "Count", "variable": "Sentiment", "Group": ""}
                )
                # focal country links anzeigen
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=True,
                    legend_title_text=""
                )
                fig_cmp.update_traces(texttemplate="%{y:.0f}", textposition="outside")
                st.subheader("Peer vs. Country Sentiment")
                st.plotly_chart(fig_cmp, use_container_width=True)
    
    
            elif benchmark_type == "Between Country Comparison" and plot_type == "Histogram":
                # 1) Fokus-Land
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder-Durchschnitte vorbereiten
                country_avg = (
                    df
                    .groupby("country")[["words_pos", "words_neg"]]
                    .mean()
                    .reset_index()
                )
                # Gesamt-Mittelwerte
                overall_pos = country_avg["words_pos"].mean()
                overall_neg = country_avg["words_neg"].mean()
                # Fokus-Land-Mittelwerte
                focal_pos   = country_avg.loc[country_avg["country"] == focal_country, "words_pos"].iat[0]
                focal_neg   = country_avg.loc[country_avg["country"] == focal_country, "words_neg"].iat[0]
            
                # 3) Histogramm für alle Länder-Durchschnitte (überlagert, dunkelblau)
                fig_hist = px.histogram(
                    country_avg,
                    x="words_pos",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_pos": "# Positive Words"},
                )
                fig_hist.update_traces(marker_color="#1f77b4")
                # Fokus-Land als rote Linie
                fig_hist.add_vline(
                    x=focal_pos,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg Pos</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                # Gesamt-Average
                fig_hist.add_vline(
                    x=overall_pos,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg Pos</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                fig_hist.update_layout(
                    showlegend=False,
                    xaxis_title="# Positive Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                st.subheader("Positive Words Distribution by Country")
                st.plotly_chart(fig_hist, use_container_width=True)
            
                # 4) Dasselbe noch für negative Wörter
                fig_hist2 = px.histogram(
                    country_avg,
                    x="words_neg",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_neg": "# Negative Words"},
                )
                fig_hist2.update_traces(marker_color="#1f77b4")
                fig_hist2.add_vline(
                    x=focal_neg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg Neg</b>",
                    annotation_position="bottom left",
                    annotation_font_size=14,
                )
                fig_hist2.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg Neg</b>",
                    annotation_position="top right",
                    annotation_font_size=14,
                )
                fig_hist2.update_layout(
                    showlegend=False,
                    xaxis_title="# Negative Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                st.subheader("Negative Words Distribution by Country")
                st.plotly_chart(fig_hist2, use_container_width=True)
            
            
            elif plot_type == "Bar Chart":
                # --- Positive Words -----------------------
                st.subheader("Positive Words")
            
                pos_df = benchmark_df.sort_values("words_pos", ascending=False)
            
                # Highlight-Spalte
                pos_df["highlight_label"] = np.where(
                    pos_df["company"] == company,
                    company,
                    "Peers"
                )
            
                # 1) Kurzspalte erstellen
                pos_df["company_short"] = pos_df["company"].str.slice(0, 15)
            
                # 2) Plot bauen gegen company_short
                fig_pos = px.bar(
                    pos_df,
                    x="words_pos",
                    y="company_short",                        # <<< hier die Kurzspalte
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={
                        "Peers": "#4C78A8",
                        company: "#E10600",
                    },
                    labels={
                        "words_pos":    "# Positive Words",
                        "company_short":"Company",
                        "highlight_label":""
                    },
                    category_orders={"company_short": pos_df["company_short"].tolist()},
                    hover_data=["company"]                     # <<< vollen Namen im Tooltip
                )
            
                # Peer-Average‐Linie
                mean_pos = pos_df["words_pos"].mean()
                fig_pos.add_vline(
                    x=mean_pos,
                    line_dash="dash",
                    line_color="#333333",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                st.plotly_chart(fig_pos, use_container_width=True)
            
                # --- Negative Words -----------------------
                st.subheader("Negative Words")
            
                neg_df = benchmark_df.sort_values("words_neg", ascending=False)
            
                # Highlight-Spalte
                neg_df["highlight_label"] = np.where(
                    neg_df["company"] == company,
                    company,
                    "Peers"
                )
            
                # 1) Kurzspalte erstellen
                neg_df["company_short"] = neg_df["company"].str.slice(0, 15)
            
                # 2) Plot bauen gegen company_short
                fig_neg = px.bar(
                    neg_df,
                    x="words_neg",
                    y="company_short",                        # <<< hier die Kurzspalte
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={
                        "Peers": "#4C78A8",
                        company: "#E10600",
                    },
                    labels={
                        "words_neg":    "# Negative Words",
                        "company_short":"Company",
                        "highlight_label":""
                    },
                    category_orders={"company_short": neg_df["company_short"].tolist()},
                    hover_data=["company"]                     # <<< vollen Namen im Tooltip
                )
            
                # Peer-Average‐Linie
                mean_neg = neg_df["words_neg"].mean()
                fig_neg.add_vline(
                    x=mean_neg,
                    line_dash="dash",
                    line_color="#333333",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                st.plotly_chart(fig_neg, use_container_width=True)
            
                mean_pos  = benchmark_df["words_pos"].mean()
                focal_pos = df.loc[df["company"] == company, "words_pos"].iat[0]
                mean_neg  = benchmark_df["words_neg"].mean()
                focal_neg = df.loc[df["company"] == company, "words_neg"].iat[0]
    
                
                st.subheader("Peer vs. Company Sentiment")
    
                
                # Vergleich positive vs. negative als grouped bar
                comp_df = pd.DataFrame({
                    "company": ["Peer Average", company],
                    "Positive": [mean_pos,  focal_pos],
                    "Negative": [mean_neg,  focal_neg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="company",
                    y=["Positive","Negative"],
                    barmode="group",
                    labels={"value":"Count","company":""},
                    category_orders={"company": [company, "Peer Average"]},
                )
                st.plotly_chart(fig_cmp, use_container_width=True)
    
            elif plot_type == "Histogram":
                
                mean_pos  = benchmark_df["words_pos"].mean()
                focal_pos = df.loc[df["company"] == company, "words_pos"].iat[0]
                mean_neg  = benchmark_df["words_neg"].mean()
                focal_neg = df.loc[df["company"] == company, "words_neg"].iat[0]
                                
                st.write("Histogram of positive words")
                fig_h1 = px.histogram(benchmark_df, x="words_pos", nbins=20,
                                     )
    
                # Peer Average als vertikale Linie mit Beschriftung
                fig_h1.add_vline(
                    x=mean_pos,
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                # Focal Company
                fig_h1.add_vline(
                    x=focal_pos,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig_h1.update_layout(xaxis_title="Number of positive Words", yaxis_title="Number of Companies")
                st.plotly_chart(fig_h1, use_container_width=True)
                
                st.write("Histogram of negative words")
                fig_h2 = px.histogram(benchmark_df, x="words_neg", nbins=20)
        
                # Peer Average als vertikale Linie mit Beschriftung
                fig_h2.add_vline(
                    x=mean_neg,
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                # Focal Company
                fig_h2.add_vline(
                    x=focal_neg,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig_h2.update_layout(xaxis_title="Number of negative Words", yaxis_title="Number of Companies")
                st.plotly_chart(fig_h2, use_container_width=True)
    
    
        elif view == "Language Complexity":
            st.subheader(f"Language Complexity ({benchmark_label})")
        
            # 1) Peer-Average und Focal-Wert holen
            mean_fog  = benchmark_df["fog"].mean()
            focal_fog = df.loc[df["company"] == company, "fog"].iat[0]
    
    
            if benchmark_type == "Between Country Comparison" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder-Durchschnitt für fog berechnen
                country_avg = (
                    df
                    .groupby("country")["fog"]           # statt Sustainability_Page_Count jetzt fog
                    .mean()
                    .reset_index(name="FogScore")
                )
            
                # 3) Gesamt-Durchschnitt und Focal-Land-Durchschnitt
                overall_avg = country_avg["FogScore"].mean()
                focal_avg   = country_avg.loc[
                    country_avg["country"] == focal_country, "FogScore"
                ].iat[0]
            
                # 4) Histogramm der Länder-Durchschnitte in Dunkelblau
                fig = px.histogram(
                    country_avg,
                    x="FogScore",
                    nbins=20,
                    opacity=0.8,
                    labels={"FogScore": "Language Complexity (Fog)"}
                )
                fig.update_traces(marker_color="#1f77b4")  # alle Balken dunkelblau
            
                # 5) VLine für All Countries Avg (schwarz gestrichelt)
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_size=14,
                )
            
                # 6) VLine für Focal Country Avg (rot gestrichelt)
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=14,
                )
            
                # 7) Layout-Feinschliff
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Language Complexity (Fog)",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
            
                st.plotly_chart(fig, use_container_width=True)
    
            elif benchmark_type == "Between Country Comparison" and plot_type == "Bar Chart":
                # 1) Bestimme das Land des gewählten Unternehmens
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Berechne den Durchschnitt des Fog-Scores pro Land
                country_avg = (
                    df
                    .groupby("country")["fog"]
                    .mean()
                    .reset_index(name="FogScore")
                )
            
                # 3) Sortiere so, dass das kleinste Mittel unten und das größte ganz oben erscheint
                country_avg = country_avg.sort_values("FogScore", ascending=False)
                y_order = country_avg["country"].tolist()

                 # 4) Kürze die Ländernamen auf max. 15 Zeichen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Markiere Dein Land zum Hervorheben
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    focal_country,
                    "Other Countries"
                )
            
                # 5) Erstelle das horizontale Balkendiagramm
                fig_ctry = px.bar(
                    country_avg,
                    x="FogScore",
                    y="country",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country": y_order},
                    labels={"FogScore": "Language Complexity (Fog)", "country": ""},
                )
            
                # 6) Peer Average über **alle** Länder als schwarze VLine
                overall_avg = country_avg["FogScore"].mean()
                fig_ctry.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 7) Werte als Beschriftung außen anzeigen
                fig_ctry.update_traces(
                    texttemplate="%{x:.1f}",   # hier 1 Nachkommastelle
                    textposition="outside",
                    cliponaxis=False
                )
            
                # 8) Legende ausblenden und Achsentitel setzen
                fig_ctry.update_layout(
                    showlegend=False,
                    xaxis_title="Fog Score",
                )
            
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # 9) Zweiter Chart: Focal vs. Durchschnitt aller anderen Länder
                other_mean = (
                    country_avg
                    .loc[country_avg["country"] != focal_country, "FogScore"]
                    .mean()
                )
                focal_mean = country_avg.loc[
                    country_avg["country"] == focal_country, "FogScore"
                ].iat[0]
            
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other Countries"],
                    "FogScore": [focal_mean, other_mean]
                })
            
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="FogScore",
                    text="FogScore",
                    color="Group",
                    color_discrete_map={
                        focal_country:   "red",
                        "Other Countries": "#1f77b4"
                    },
                    labels={"FogScore": "Fog Score", "Group": ""}
                )
                # Focal-Country links  
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=False,
                    yaxis_title="Fog Score"
                )
                fig_cmp.update_traces(texttemplate="%{text:.1f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_cmp, use_container_width=True)
            
            elif plot_type == "Histogram":
                fig_fog = px.histogram(
                    plot_df, x="fog", nbins=20,
                    labels={"fog": "Fog Index"}
                )
                # Peer Average
                fig_fog.add_vline(
                    x=mean_fog,
                    line_dash="dash", line_color="black", line_width=1, opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                # Focal Company
                fig_fog.add_vline(
                    x=focal_fog,
                    line_dash="dash", line_color="red", opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig_fog.update_layout(
                    xaxis_title="Fog Index",
                    yaxis_title="Number of Companies",
                )
                st.plotly_chart(fig_fog, use_container_width=True)
        
            elif plot_type == "Bar Chart":
                # 1) sortieren und Highlight-Spalte
                peers_fog = plot_df.sort_values("fog", ascending=False)
                peers_fog["highlight_label"] = np.where(
                    peers_fog["company"] == company, company, "Peers"
                )
            
                # 2) Kurzspalte anlegen (max. 15 Zeichen)
                peers_fog["company_short"] = peers_fog["company"].str.slice(0, 15)
            
                # 3) Reihenfolge für die Kurzspalte umdrehen
                y_order_short = peers_fog["company_short"].tolist()[::-1]
            
                # 4) Bar Chart gegen company_short zeichnen
                fig_fog_bar = px.bar(
                    peers_fog,
                    x="fog",
                    y="company_short",                   # <<< Kurzspalte verwenden
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "fog":           "Fog Index",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                    hover_data=["company"]               # <<< Voller Name im Tooltip
                )
            
                # 5) Peer‐Average Linie
                fig_fog_bar.add_vline(
                    x=mean_fog,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 6) Layout anpassen
                fig_fog_bar.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={
                        "categoryorder": "array",
                        "categoryarray": y_order_short
                    },
                )
            
                st.plotly_chart(fig_fog_bar, use_container_width=True)
            
                # --- Vergleichsbalken bleibt unverändert ---
                comp_fog = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "Fog":   [mean_fog,      focal_fog],
                })
                fig_fog_cmp = px.bar(
                    comp_fog,
                    x="Group",
                    y="Fog",
                    text="Fog",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Fog": "Fog Index", "Group": ""}
                )
                fig_fog_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_fog_cmp.update_traces(
                    texttemplate="%{text:.1f}",
                    textposition="outside",
                    width=0.5
                )
                st.plotly_chart(fig_fog_cmp, use_container_width=True)
            
                st.caption("Fog index (Gunning’s language complexity measure).")
        
        
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
