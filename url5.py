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
      /* 0) Selectbox volle Breite */
      .stSelectbox > div > div > div > div {
        width: 100% !important;
      }

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
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1) !important;
        border-radius: 0.5rem;
        padding: 1rem;
      }

      /* 4) Mittlere Column transparent + alle Schatten killen */
      section[data-testid="column"]:nth-of-type(2) {
        background-color: transparent !important;
        box-shadow: none !important;
      }
      section[data-testid="column"]:nth-of-type(2) * {
        background: transparent !important;
        box-shadow: none !important;
      }

      /* 5) In der mittleren Column: die Standard-.block-container-Abstände auf 0 */
      [data-testid="stAppViewContainer"]
        > div[class*="block-container"]
        > section[data-testid="column"]:nth-of-type(2)
        > div[class*="block-container"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)
#-------------------------------------------------------------------------------------
# 2. Daten laden
#--------------------------------------------------------------------------------------
df = pd.read_csv("summary_final_version.csv")

# direkt nach dem Einlesen
df['SASB_industry'] = (
    df['SASB_industry']
      .str.replace(r'\s+', ' ', regex=True)  # alle mehrfachen spaces → 1 space
      .str.strip()
)


# Zusammenfassen der SASB_industry Variable in die SASB Sectors

supersector_map = {
    # Consumer Goods
    **dict.fromkeys([
        'Apparel Accessories & Footwear',
        'Appliance Manufacturing',
        'Building Products & Furnishings',
        'E-Commerce',
        'Household & Personal Products',
        'Multiline and Specialty Retailers & Distributors',
        'Toys & Sporting Goods'
    ], 'Consumer Goods'),
    # Extractives & Minerals Processing
    **dict.fromkeys([
        'Coal Operations',
        'Construction Materials',
        'Iron & Steel Producers',
        'Metals & Mining',
        'Oil & Gas – Exploration & Production',
        'Oil & Gas – Midstream',
        'Oil & Gas – Refining & Marketing',
        'Oil & Gas – Services'
    ], 'Extractives & Minerals Processing'),
    # Financials
    **dict.fromkeys([
        'Asset Management & Custody Activities',
        'Commercial Banks',
        'Consumer Finance',
        'Insurance',
        'Investment Banking & Brokerage',
        'Mortgage Finance',
        'Security & Commodity Exchange'
    ], 'Financials'),
    # Food & Beverage
    **dict.fromkeys([
        'Agricultural Products',
        'Alcoholic Beverages',
        'Food Retailers & Distributors',
        'Meat Poultry & Dairy',
        'Non-Alcoholic Beverages',
        'Processed Foods',
        'Restaurants',
        'Tobacco'
    ], 'Food & Beverage'),
    # Health Care
    **dict.fromkeys([
        'Biotechnology & Pharmaceuticals',
        'Drug Retailers',
        'Health Care Delivery',
        'Health Care Distributors',
        'Managed Care',
        'Medical Equipment & Supplies'
    ], 'Health Care'),
    # Infrastructure
    **dict.fromkeys([
        'Electric Utilities & Power Generators',
        'Engineering & Construction Services',
        'Gas Utilities & Distributors',
        'Home Builders',
        'Real Estate',
        'Real Estate Services',
        'Waste Management',
        'Water Utilities & Services'
    ], 'Infrastructure'),
    # Renewable Resources & Alternative Energy
    **dict.fromkeys([
        'Biofuels',
        'Forestry Management',
        'Fuel Cells & Industrial Batteries',
        'Pulp & Paper Products',
        'Solar Technology & Project Developers',
        'Wind Technology & Project Developers'
    ], 'Renewable Resources & Alternative Energy'),
    # Resource Transformation
    **dict.fromkeys([
        'Aerospace & Defence',
        'Chemicals',
        'Containers & Packaging',
        'Electrical & Electronic Equipment',
        'Industrial Machinery & Goods'
    ], 'Resource Transformation'),
    # Services
    **dict.fromkeys([
        'Advertising & Marketing',
        'Casinos & Gaming',
        'Education',
        'Hotels & Lodging',
        'Leisure Facilities',
        'Media & Entertainment',
        'Professional & Commercial Services'
    ], 'Services'),
    # Technology & Communications
    **dict.fromkeys([
        'Electronic Manufacturing Services & Original Design Manufacturing',
        'Hardware',
        'Internet Media & Services',
        'Semiconductors',
        'Software & IT Services',
        'Telecommunication Services'
    ], 'Technology & Communications'),
    # Transportation
    **dict.fromkeys([
        'Air Freight & Logistics',
        'Airlines',
        'Auto Parts',
        'Automobiles',
        'Car Rental & Leasing',
        'Cruise Lines',
        'Marine Transportation',
        'Rail Transportation',
        'Road Transportation'
    ], 'Transportation'),
}

# 5. Mapping anwenden
df['supersector'] = df['SASB_industry'] \
    .map(supersector_map) \
    .fillna('Other')

def smart_layout(fig, num_items, *,
                 min_height=300,    # absolute Mindesthöhe
                 max_height=1200,   # absolute Maxhöhe
                 bar_height=40,     # Pixel pro Item
                 min_font=8,        # absolute Mindestschrift
                 max_font=16        # absolute Maxschrift
                ):
    """
    Passt Höhe und Schriften an, je nachdem wie viele Balken (num_items) wir haben.
    """
    # 1) Höhe: pro Item bar_height px plus etwas Padding
    height = min(max_height, max(min_height, num_items * bar_height + 150))
    
    # 2) Schriftgröße: bei wenig Items groß, bei vielen kleiner
    #    lineare Interpolation zwischen max_font (bei 1 Item) und min_font (bei 30+ Items)
    if num_items <= 1:
        font_size = max_font
    else:
        # je mehr Items umso näher an min_font
        font_size = max(min_font,
                        max_font - (num_items-1) * (max_font-min_font) / 29
                       )
    font_size = round(font_size, 1)
    
    fig.update_layout(
        height=height,
        font=dict(size=font_size),
        margin=dict(l=150, r=20, t=40, b=40),
        yaxis=dict(tickfont=dict(size=font_size)),
        xaxis=dict(tickfont=dict(size=font_size))
    )
    return fig

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

# 4a. Linke Sidebar: Company + Peer-Group-/Cross-Comparison-Radio
with left:

    # 1) Große Überschrift für Company
    st.subheader("Select a company:")

    # 2) Dann das Selectbox selbst, ganz ohne Label-Text
    default_idx = company_list.index(default_company) if default_company in company_list else 0
    company = st.selectbox(
        "",                    # <— kein Label hier
        options=company_list,
        index=default_idx,
        key="company_selector"
    )
    selected = company

    # 3) Peer-Group Titel
    st.subheader("Company vs. Peer Group")

    # 4) Kombiniertes Radio-Widget
    options = [
        "Sector Peers",
        "Country Peers",
        "Market Cap Peers",
        "All CSRD First Wave",
        "Choose specific peers",
        "⭐ Company Sector vs Other Sectors",
        "🌍 Company Country vs Other Countries"
    ]
    raw_choice = st.radio("", options, key="benchmark_type")
    benchmark_type = raw_choice.replace("⭐ ", "").replace("🌍 ", "")

    # 4) Wenn „Choose specific peers“ gewählt, Multiselect anzeigen
    if benchmark_type == "Choose specific peers":
        peer_selection = st.multiselect(
            "Or choose specific peer companies:",
            options=company_list,
            default=[]
        )
    else:
        peer_selection = []

# 4b. Rechte Spalte: View & Chart Type
with right:
    st.header("What do you want to benchmark?")

    # Hier ganz bewusst *nur* die echten Auswahl-Strings
    view_options = [
        "Number of Pages",
        "Number of Words",
        "Words per ESRS standard",
        "Numbers",
        "Tables",
        "Images",
        "Standardized Language",
        "Language Complexity",
        "Sentiment",
        "Peer Company List",
    ]
    view = st.radio(
        "Select Your View:",
        view_options,
        key="view_selector"
    )

    help_texts = {
        "Number of Pages": "The total number of pages of the sustainability report.",
        "Number of Words": "The total number of words of the sustainability report.",
        "Words per ESRS standard": "This method utilizes word2vec (Mikolov et al. 2013), an algorithm that “learns” the meaning of words in a text using a neural networks. We use the resulting textual embeddings to generate a dictionary of keywords for each ESRS. Based on general “seed words” (e.g., greenhouse gas emissions for E1 climate change), we pick the 500 most similar words based on the embeddings. The resulting list of keywords allows us to broadly capture ESG-related discussions in reporting even before ESRS-specific terminology has been introduced. The main measure shown in this presentation is the number of words from sentences that contain a keyword from one of the 11 ESRS standards.",
        "Numbers": "Count of Numbers per 500 words",
        "Tables": "Count of tables per 500 words",
        "Images": "Average image area per 500 words",
        "Standardized Language": "Average count of frequently used tetragrams" ,
        "Language Complexity": "Fog-Index, an aggregate measure of readability where higher values suggest more complex and technical language - which may be appropriate in professional sustainability disclosures.",
        "Sentiment": "Average number of positive and negative words per 500 words",
        "Peer Company List": "List of companies included in the peer group based on your choice.",
    }

    # Und zeige diese Erklärung direkt unter dem Radio:
    if view in help_texts:
        st.info(help_texts[view])

    st.header("Chart Type")

    if view == "Words per ESRS standard":
        # bei ESRS only Bar Chart erlauben
        plot_type = st.radio(
            "",
            ["Bar Chart"], 
            key="plot_type"
        )
    else:
        # bei allen anderen Views beide Optionen
        plot_type = st.radio(
            "",
            ["Bar Chart", "Histogram"],
            key="plot_type"
        )

# --------------------------------------------------------------------
# 6. Build `benchmark_df`
# --------------------------------------------------------------------
if benchmark_type == "Sector Peers":
    supersec      = df.loc[df["company"] == company, "supersector"].iat[0]
    benchmark_df  = df[df["supersector"] == supersec]
    benchmark_label = f"Sector Peers: {supersec}"

elif benchmark_type == "Country Peers":
    country       = df.loc[df["company"] == company, "country"].iat[0]
    benchmark_df  = df[df["country"] == country]
    benchmark_label = f"Country Peers: {country}"

elif benchmark_type == "Market Cap Peers":
    terc          = df.loc[df["company"] == company, "Market_Cap_Cat"].iat[0]
    lbl           = (
        "Very Small" if terc == 1 else
        "Small"      if terc == 2 else
        "Medium"     if terc == 3 else
        "Large"      if terc == 4 else
        "Huge"
    )
    benchmark_df  = df[df["Market_Cap_Cat"] == terc]
    benchmark_label = f"Market Cap Peers: {lbl}"

elif benchmark_type == "All CSRD First Wave":
    benchmark_df    = df.copy()
    benchmark_label = "All CSRD First Wave"

elif benchmark_type == "Choose specific peers":
    sel = set(peer_selection) | {company} if peer_selection else {company}
    benchmark_df    = df[df["company"].isin(sel)]
    benchmark_label = f"Selected Peers ({len(benchmark_df)} firms)"

elif benchmark_type == "Company Country vs Other Countries":
    focal_country = df.loc[df["company"] == company, "country"].iat[0]
    country_df    = df[df["country"] == focal_country]
    others_df     = df[df["country"] != focal_country]
    benchmark_df  = pd.concat([
        country_df.assign(_group=focal_country),
        others_df.assign(_group="Others")
    ], ignore_index=True)
    benchmark_label = f"{focal_country} vs Others"

elif benchmark_type == "Company Sector vs Other Sectors":
    focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
    super_df    = df[df["supersector"] == focal_super]
    others_df   = df[df["supersector"] != focal_super]
    benchmark_df = pd.concat([
        super_df.assign(_group=focal_super),
        others_df.assign(_group="Other sectors")
    ], ignore_index=True)
    benchmark_label = f"{focal_super} vs Other sectors"

# focal values (bleiben unverändert)
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
    
    
    
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
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
                    annotation_font_color="black",
                    annotation_font_size=16,
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
                    annotation_font_size=16,
                )
                
                # 6) Legende ausblenden und Achsentitel
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Pages",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Durchschnitt pro Country und Sortierung (absteigend)
                country_avg = (
                    df
                    .groupby("country")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Pages")
                    .sort_values("Pages", ascending=False)
                )
            
                # 3) Labels kürzen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Reihenfolge umdrehen, damit in Plotly die größte Bar oben landet
                y_order = country_avg["country_short"].tolist()[::-1]
            
                # 5) Highlight für Dein Land
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
            
                # 6) Bar-Chart erzeugen
                fig_ctry = px.bar(
                    country_avg,
                    x="Pages",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country_short": y_order},
                    labels={"Pages": "Pages", "country_short": ""},
                )
            
                # 7) Peer-Average-Linie
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
            
                # 8) Einheitliches Styling anwenden (dicke Bars, Außen-Labels, dynamische Höhe)
                fig_ctry = style_bar_chart(fig_ctry, country_avg, y_order)
                # 9) Legende ausblenden, wenn gewünscht
                fig_ctry.update_layout(showlegend=False)
            
                # 10) Chart rendern
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Focal vs. Other Countries Avg —
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "Pages": [
                        country_avg.loc[country_avg["country"] == focal_country, "Pages"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "Pages"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Pages",
                    text="Pages",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"Pages": "Pages", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other countries average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Wortzahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["words"]
                    .mean()
                    .reset_index(name="Words")
                )
                # 2) Plot
                fig = px.histogram(
                    sector_avg,
                    x="Words",
                    nbins=20,
                    opacity=0.8,
                    labels={"Words": "Words"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["Words"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Words"].iat[0]
        
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black",
                              annotation_text="<b>All Sectors Avg</b>",
                              annotation_position="top right",
                              annotation_font_color= "black",
                              annotation_font_size=16)
                fig.add_vline(x=focal_avg, line_dash="dash", line_color="red",
                              annotation_text=f"<b>{focal_super} Avg</b>",
                              annotation_position="bottom left",
                              annotation_font_color="red",
                              annotation_font_size=16)
        
                fig.update_layout(showlegend=False,
                                  xaxis_title="Words",
                                  yaxis_title="Number of Sectors",
                                  bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)


            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap  # für automatischen Zeilenumbruch
            
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnittliche Wortzahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["words"]
                    .mean()
                    .reset_index(name="Words")
                    .sort_values("Words", ascending=False)
                )
            
                # 3) Mehrzeilige Labels mit wrap (width gibt Max-Zeichen pro Zeile an)
                sector_avg["sector_short"] = sector_avg["supersector"].apply(
                    lambda s: "\n".join(textwrap.wrap(s, width=20))
                )
            
                # 4) Reihenfolge umdrehen, damit die größte Bar oben sitzt
                y_order_short = sector_avg["sector_short"].tolist()[::-1]
            
                # 5) Highlight fürs eigene Supersector (umgebrochener Label)
                focal_label = "\n".join(textwrap.wrap(focal_super, width=20))
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
            
                # 6) Horizontalen Bar‐Chart bauen
                fig_s = px.bar(
                    sector_avg,
                    x="Words",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_label: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order_short},
                    labels={"sector_short": "", "Words": "Words"},
                )
            
                # 7) Linie für den Durchschnitt aller Sektoren
                avg_all = sector_avg["Words"].mean()
                fig_s.add_vline(
                    x=avg_all,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 8) Einheitliches Styling (Balkenstärke, Außen‐Labels, dynamische Höhe)
                fig_s = style_bar_chart(fig_s, sector_avg, y_order_short)
                fig_s.update_layout(showlegend=False)
            
                # 9) Chart ausgeben
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Optional: Vergleichs‐Chart Supersector vs Rest —
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "Words"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "Words"].mean()
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "Words": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            
            
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
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "Sustainability_Page_Count": "Pages",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                )
        
                # c) Peer-Average-Linie
                fig2.add_vline(
                    x=mean_pages,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
        
                # d) Einheitliches Styling via Hilfsfunktion
                fig2 = style_bar_chart(fig2, peers_df, y_order_short)
        
                # e) Chart ausgeben
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
    
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
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
                    annotation_font_color="black",
                    annotation_font_size=16,
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
                    annotation_font_size=16,
                )
            
                # 7) Layout‐Feinschliff
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
            
                st.plotly_chart(fig, use_container_width=True)
    
    
            
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
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
                country_avg_words["country_short"] = country_avg_words["country"].str.slice(0, 15)
            
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


             # Histogramm aller Supersector‐Durchschnitte
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Wortzahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["words"]
                    .mean()
                    .reset_index(name="Words")
                )
                # 2) Plot
                fig = px.histogram(
                    sector_avg,
                    x="Words",
                    nbins=20,
                    opacity=0.8,
                    labels={"Words": "Words"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["Words"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Words"].iat[0]
        
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black",
                              annotation_text="<b>All Sectors Avg</b>",
                              annotation_position="top right",
                              annotation_font_color= "black",
                              annotation_font_size=16)
                fig.add_vline(x=focal_avg, line_dash="dash", line_color="red",
                              annotation_text=f"<b>{focal_super} Avg</b>",
                              annotation_position="bottom left",
                              annotation_font_color="red",
                              annotation_font_size=16)
        
                fig.update_layout(showlegend=False,
                                  xaxis_title="Words",
                                  yaxis_title="Number of Sectors",
                                  bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
        
        
            # Bar-Chart aller Supersektoren
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                # 1) Durchschnittliche Wortzahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["words"]
                    .mean()
                    .reset_index(name="Words")
                ).sort_values("Words", ascending=False)
        
                # 2) Kurzlabel auf 15 Zeichen
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0,15)
                y_order = sector_avg["sector_short"].tolist()
        
                # 3) Highlight focal Supersector
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    sector_avg["sector_short"],
                    "Other sectors"
                )
        
                # 4) Plot
                fig_s = px.bar(
                    sector_avg,
                    x="Words",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "Words": "Words"}
                )
                fig_s.add_vline(x=sector_avg["Words"].mean(), line_dash="dash",
                                line_color="black",
                                annotation_text="<b>All Sectors Avg</b>",
                                annotation_position="bottom right",
                                annotation_font_color="black",
                                annotation_font_size=16
                               )
                fig_s.update_traces(texttemplate="%{x:.0f}", textposition="outside", cliponaxis=False)
                fig_s.update_layout(showlegend=False, xaxis_title="Words")
                st.plotly_chart(fig_s, use_container_width=True)
        
                # 5) Kompakter Vergleich: focal vs. average of others
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "Words"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "Words"].mean()
        
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "Words": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
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



        elif view == "Words per ESRS standard":
            st.subheader(f"Words per ESRS standard ({benchmark_label})")
        
            # — 1) Topics-Mapping & pct-Spalten —
            topic_map = {
                'affected':       'S3: Affected communities',
                'biodiversity':   'E4: Biodiversity',
                'climate':        'E1: Climate change',
                'conduct':        'G1: Business conduct',
                'consumers':      'S4: Consumers',
                'governance':     'ESRS 2: Governance',
                'ownworkforce':   'S1: Own workforce',
                'pollution':      'E2: Pollution',
                'waste':          'E5: Circular economy',
                'water':          'E3: Water',
                'workersvalchain':'S2: Value chain workers'
            }
            # Für jede rel_<topic> eine neue Spalte <topic>_pct anlegen
            for t, lbl in topic_map.items():
                rc, pc = f'rel_{t}', f'{t}_pct'
                if rc in benchmark_df.columns:
                    benchmark_df[pc] = benchmark_df[rc]
            pct_cols = [c for c in benchmark_df.columns if c.endswith('_pct')]
        
            # — 2) Wide → Long & Mapping —
            plot_long = (
                benchmark_df[['company'] + pct_cols]
                .melt(
                    id_vars=['company'],
                    value_vars=pct_cols,
                    var_name='topic_internal',
                    value_name='pct'
                )
            )
            plot_long['topic'] = plot_long['topic_internal'].str.replace('_pct','', regex=False)
            plot_long['topic_label'] = plot_long['topic'].map(topic_map)
        
            # — 3) Aggregation auf Firmen-Level —
            avg_df = (
                plot_long
                .groupby(['company','topic_label'])['pct']
                .mean()
                .reset_index()
            )
        
            # — 4) Legenden-Reihenfolge & Farben —
            legend_order = [
                'E1: Climate change','E2: Pollution','E3: Water','E4: Biodiversity',
                'E5: Circular economy','S1: Own workforce','S2: Value chain workers',
                'S3: Affected communities','S4: Consumers','ESRS 2: Governance',
                'G1: Business conduct'
            ]
            my_colors = {
                'E1: Climate change':'#145214','E2: Pollution':'#2e7d32','E3: Water':'#388e3c',
                'E4: Biodiversity':'#81c784','E5: Circular economy':'#c8e6c9',
                'S1: Own workforce':'#f57c00','S2: Value chain workers':'#ffb74d',
                'S3: Affected communities':'#e65100','S4: Consumers':'#bf360c',
                'ESRS 2: Governance':'#5A9BD5','G1: Business conduct':'#1F4E79'
            }
        
            # — 5) Darstellung je nach Benchmark-Typ —
            if benchmark_type == "Company Country vs Other Countries":
                # a) country ins Long-DF einfügen
                plot_long = plot_long.merge(
                    benchmark_df[['company','country']],
                    on='company',
                    how='left'
                )
        
                # b) Durchschnitt pro Land & Topic
                country_topic = (
                    plot_long
                    .groupby(['country','topic_label'])['pct']
                    .mean()
                    .reset_index()
                )
                # Gesamt-Durchschnitt
                total = (
                    country_topic
                    .groupby('topic_label')['pct']
                    .mean()
                    .reset_index()
                    .assign(country='All countries')
                )
                # Focal Country
                focal = df.loc[df['company']==company, 'country'].iat[0]
                focal_df = country_topic[country_topic['country']==focal].copy()
        
                # Chart A: Focal vs. All countries
                combo = pd.concat([focal_df, total], ignore_index=True)
                combo['country_short'] = combo['country'].str.slice(0,15)
                catA = [focal[:15], 'All countries']
                combo['country_short'] = pd.Categorical(combo['country_short'],
                                                       categories=catA, ordered=True)
        
                figA = px.bar(
                    combo,
                    x='pct', y='country_short', color='topic_label',
                    orientation='h',
                    text=combo['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'country_short':'','pct':'Share'},
                    color_discrete_map=my_colors,
                    category_orders={'country_short':catA,'topic_label':legend_order}
                )
                figA.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                figA.update_layout(barmode='stack', xaxis_tickformat=',.0%',
                                   legend=dict(title='ESRS Topic', itemsizing='constant'))
                st.plotly_chart(figA, use_container_width=True)
        
                # Chart B: Alle Länder (focal zuerst)
                orderB = [focal[:15]] + sorted(set(country_topic['country'].str.slice(0,15)) - {focal[:15]})
                country_topic['country_short'] = pd.Categorical(
                    country_topic['country'].str.slice(0,15),
                    categories=orderB, ordered=True
                )
                figB = px.bar(
                    country_topic,
                    x='pct', y='country_short', color='topic_label',
                    orientation='h',
                    text=country_topic['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'country_short':'','pct':'Share'},
                    color_discrete_map=my_colors,
                    category_orders={'country_short':orderB,'topic_label':legend_order}
                )
                figB.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                figB.update_layout(barmode='stack', xaxis_tickformat=',.0%',
                                   legend=dict(title='ESRS Topic', itemsizing='constant'))
                st.plotly_chart(figB, use_container_width=True)
        
            elif benchmark_type == "Company Sector vs Other Sectors":
                sector_topic = (
                    plot_long
                    .merge(df[['company','supersector']], on='company')
                    .groupby(['supersector','topic_label'])['pct']
                    .mean()
                    .reset_index()
                )
                total = sector_topic.groupby('topic_label')['pct'].mean().reset_index()
                total['supersector'] = 'All sectors'
                focal_s = df.loc[df['company']==company,'supersector'].iat[0]
                focal_df = sector_topic[sector_topic['supersector']==focal_s].copy()
        
                # Chart A: Focal vs. All sectors
                combo = pd.concat([focal_df, total], ignore_index=True)
                combo['sector_short'] = combo['supersector'].str.slice(0,15)
                catA = [focal_s[:15], 'All sectors']
                combo['sector_short'] = pd.Categorical(combo['sector_short'],
                                                      categories=catA, ordered=True)
        
                figA = px.bar(
                    combo,
                    x='pct', y='sector_short', color='topic_label',
                    orientation='h',
                    text=combo['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'sector_short':'','pct':'Share'},
                    color_discrete_map=my_colors,
                    category_orders={'sector_short':catA,'topic_label':legend_order}
                )
                figA.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                figA.update_layout(barmode='stack', xaxis_tickformat=',.0%',
                                   legend=dict(title='ESRS Topic', itemsizing='constant'))
                st.plotly_chart(figA, use_container_width=True)
        
                # Chart B: Alle Supersektoren (focal zuerst)
                orderB = [focal_s[:15]] + sorted(set(sector_topic['supersector'].str.slice(0,15)) - {focal_s[:15]})
                sector_topic['sector_short'] = pd.Categorical(
                    sector_topic['supersector'].str.slice(0,15),
                    categories=orderB, ordered=True
                )
                figB = px.bar(
                    sector_topic,
                    x='pct', y='sector_short', color='topic_label',
                    orientation='h',
                    text=sector_topic['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'sector_short':'','pct':'Share'},
                    color_discrete_map=my_colors,
                    category_orders={'sector_short':orderB,'topic_label':legend_order}
                )
                figB.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                figB.update_layout(barmode='stack', xaxis_tickformat=',.0%',
                                   legend=dict(title='ESRS Topic', itemsizing='constant'))
                st.plotly_chart(figB, use_container_width=True)
        
            else:
                # Chart A: Peer group average vs. selected company
                peer_avg = (
                    avg_df[avg_df['company'] != selected]
                    .groupby('topic_label')['pct']
                    .mean()
                    .reset_index()
                )
                peer_avg['company'] = 'Peer group average'
                sel_df = avg_df[avg_df['company'] == selected].copy()
        
                combo = pd.concat([sel_df, peer_avg], ignore_index=True)
                combo['company_short'] = combo['company'].str.slice(0,15)
                sel_short = selected[:15]
                combo['company_short'] = pd.Categorical(
                    combo['company_short'],
                    categories=[sel_short, 'Peer group average'[:15]],
                    ordered=True
                )
        
                fig_benchmark = px.bar(
                    combo,
                    x='pct', y='company_short', color='topic_label',
                    orientation='h',
                    text=combo['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'company_short':'','pct':'Share'},
                    color_discrete_map=my_colors,
                    category_orders={
                        'company_short': [sel_short, 'Peer group average'[:15]],
                        'topic_label': legend_order
                    }
                )
                fig_benchmark.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                fig_benchmark.update_layout(barmode='stack', xaxis_tickformat=',.0%',
                                            legend=dict(title='ESRS Topic', itemsizing='constant'))
                st.plotly_chart(fig_benchmark, use_container_width=True)
        
                # Chart B: alle Firmen (selected ganz oben)
                avg_df['company_short'] = avg_df['company'].str.slice(0,15)
                sel_short = selected[:15]
                others = sorted(set(avg_df['company_short']) - {sel_short})
                avg_df['company_short'] = pd.Categorical(
                    avg_df['company_short'], categories=[sel_short] + others, ordered=True
                )
                fig_firmen = px.bar(
                    avg_df,
                    x='pct', y='company_short', color='topic_label',
                    orientation='h',
                    text=avg_df['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'company_short':'','pct':'Share'},
                    color_discrete_map=my_colors,
                    category_orders={
                        'company_short': [sel_short] + others,
                        'topic_label': legend_order
                    }
                )
                fig_firmen.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                fig_firmen.update_layout(barmode='stack', xaxis_tickformat=',.0%',
                                         legend=dict(title='ESRS Topic', itemsizing='constant'))
                st.plotly_chart(fig_firmen, use_container_width=True)

        elif view == "Numbers":
            st.subheader(f"Numbers per 500 Words ({benchmark_label})")
        
            # Peer- und Focal-Werte berechnen
            mean_nums   = benchmark_df["num_o_seit_500"].mean()
            focal_nums  = df.loc[df["company"] == company, "num_o_seit_500"].iat[0]
        
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder-Durchschnitt vorbereiten
                country_avg = (
                    df
                    .groupby("country")["num_o_seit_500"]
                    .mean()
                    .reset_index(name="Nums_per_500")
                )
        
                overall_avg = country_avg["Nums_per_500"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Nums_per_500"].iat[0]
        
                # 3) Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="Nums_per_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"Nums_per_500": "Numbers per 500 Words"},
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 4) V-Line Overall Avg
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                # 5) V-Line Focal Country
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
        
                # 6) Layout
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Numbers per 500 Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder-Durchschnitt (Nums_per_500)
                country_avg = (
                    df
                    .groupby("country")["num_o_seit_500"]
                    .mean()
                    .reset_index(name="Nums_per_500")
                    .sort_values("Nums_per_500", ascending=False)
                )
        
                # 3) Kürze Ländernamen für die Y-Achse
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
        
                # 4) Highlight-Spalte für Focal Country
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                # 5) Erstes horizontales Balkendiagramm: alle Länder
                fig_ctry = px.bar(
                    country_avg,
                    x="Nums_per_500",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"Nums_per_500": "Numbers per 500 Words", "country_short": ""}
                )
                # Peer-Average als Linie
                overall_avg = country_avg["Nums_per_500"].mean()
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
                # Werte außen anzeigen
                fig_ctry.update_traces(texttemplate="%{x:.1f}", textposition="outside", cliponaxis=False)
                fig_ctry.update_layout(showlegend=False, xaxis_title="Numbers per 500 Words")
        
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # -------------------------------------------------------
                # 6) Kompaktvergleich: Focal Country vs. Other Countries
                # -------------------------------------------------------
                focal_avg = (
                    country_avg
                    .loc[country_avg["country"] == focal_country, "Nums_per_500"]
                    .iat[0]
                )
                other_avg = (
                    country_avg
                    .loc[country_avg["country"] != focal_country, "Nums_per_500"]
                    .mean()
                )
        
                comp_df = pd.DataFrame({
                    "Group":         [focal_country, "Other Countries"],
                    "Nums_per_500":  [focal_avg,      other_avg]
                })
        
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Nums_per_500",
                    text="Nums_per_500",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    labels={"Nums_per_500": "Numbers per 500 Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.1f}", textposition="outside", width=0.5)
        
                st.subheader(f"{focal_country} vs. Other Countries")
                st.plotly_chart(fig_cmp, use_container_width=True)

            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                sector_avg = (
                    df
                    .groupby("supersector")["num_o_seit_500"]
                    .mean()
                    .reset_index(name="Nums per 500")
                )
                fig = px.histogram(
                    sector_avg,
                    x="Nums per 500",
                    nbins=20,
                    opacity=0.8,
                    labels={"Nums per 500": "Count of Numbers per 500 words"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # Linien (All vs Focal)
                overall_avg = sector_avg["Nums per 500"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Nums per 500"].iat[0]
        
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black",
                              annotation_text="<b>All Sectors Avg</b>", 
                              annotation_position="top right",
                              annotation_font_color="black",
                              annotation_font_size=16
                             )
                fig.add_vline(x=focal_avg,   line_dash="dash", line_color="red",
                              annotation_text=f"<b>{focal_super} Avg</b>", 
                              annotation_position="bottom left",
                              annotation_font_color = "red",
                              annotation_font_size=16
                             )
        
                fig.update_layout(showlegend=False,
                                  xaxis_title="Count of Numbers per 500 words",
                                  yaxis_title="Number of Sectors")
                st.plotly_chart(fig, use_container_width=True)
        
            # Bar-Chart aller Supersektoren
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                sector_avg = (
                    df
                    .groupby("supersector")["num_o_seit_500"]
                    .mean()
                    .reset_index(name="Nums per 500")
                ).sort_values("Nums per 500", ascending=False)
        
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0,15)
                y_order = sector_avg["sector_short"].tolist()
        
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    sector_avg["sector_short"],
                    "Other sectors"
                )
        
                fig_s = px.bar(
                    sector_avg,
                    x="Nums per 500",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "Nums per 500": "Count of Numbers per 500 words"}
                )
                fig_s.add_vline(x=sector_avg["Nums per 500"].mean(),
                                line_dash="dash", line_color="black",
                                annotation_text="<b>All Sectors Avg</b>",
                                annotation_position="bottom right",
                                annotation_font_color="black",
                                annotation_font_size=16
                               )
                fig_s.update_traces(texttemplate="%{x:.0f}", textposition="outside", cliponaxis=False)
                fig_s.update_layout(showlegend=False, xaxis_title="Count of Numbers per 500 words")
                st.plotly_chart(fig_s, use_container_width=True)
        
                # Kompakter Vergleich: focal vs. average of others
                focal_avg  = sector_avg.loc[sector_avg["supersector"] == focal_super, "Nums per 500"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "Nums per 500"].mean()
        
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "Nums":  [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Nums",
                    text="Nums",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"Nums": "Count of Numbers per 500 words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            

            elif plot_type == "Histogram":
                # nimm benchmark_df statt plot_df, da es dort sicher nums_500 gibt
                fig = px.histogram(
                    benchmark_df,
                    x="num_o_seit_500",
                    nbins=20,
                    labels={"num_o_seit_500": "Numbers per 500 Words"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # Peer Average
                fig.add_vline(
                    x=mean_nums,
                    line_dash="dash",
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Focal Company
                fig.add_vline(
                    x=focal_nums,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
            
                fig.update_layout(
                    xaxis_title="Numbers per 500 Words",
                    yaxis_title="Number of Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif plot_type == "Bar Chart":
                # 1) Peer-Detail-Chart
                peers_df = plot_df.sort_values("num_o_seit_500", ascending=False)
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
        
                fig2 = px.bar(
                    peers_df,
                    x="num_o_seit_500",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"num_o_seit_500": "Numbers per 500 Words", "company_short": "Company", "highlight_label": ""},
                    category_orders={"company_short": y_order_short}
                )
                fig2.add_vline(
                    x=mean_nums,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={"categoryorder": "array", "categoryarray": y_order_short}
                )
                st.plotly_chart(fig2, use_container_width=True)
        
                comp_df = pd.DataFrame({
                    "Group":       [company, "Peer Average"],
                    "Nums_per_500":[focal_nums, mean_nums]
                })
        
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Nums_per_500",
                    text="Nums_per_500",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Nums_per_500": "Numbers per 500 Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.1f}", textposition="outside", width=0.5)
        
                st.subheader("Peer vs. Company Numbers per 500 Words")
                st.plotly_chart(fig_cmp, use_container_width=True)
        
            # Fußnote
            st.caption("Number of numeric values per 500 words in companies’ sustainability reports.")

        elif view == "Tables":
            st.subheader(f"Tables per 500 Words ({benchmark_label})")
        
            # Peer- und Focal-Werte berechnen
            mean_tables = benchmark_df["tables_500"].mean()
            focal_tables = df.loc[df["company"] == company, "tables_500"].iat[0]
        
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder-Durchschnitt vorbereiten
                country_avg = (
                    df
                    .groupby("country")["tables_500"]
                    .mean()
                    .reset_index(name="Tables_per_500")
                )
        
                overall_avg = country_avg["Tables_per_500"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Tables_per_500"].iat[0]
        
                # 3) Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="Tables_per_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"Tables_per_500": "Tables per 500 Words"},
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 4) V-Line Overall Avg
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                # 5) V-Line Focal Country
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
        
                # 6) Layout
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Tables per 500 Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
        
                    
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder-Durchschnitt (Tables_per_500)
                country_avg = (
                    df
                    .groupby("country")["tables_500"]
                    .mean()
                    .reset_index(name="Tables_per_500")
                    .sort_values("Tables_per_500", ascending=False)
                )
        
                # 3) Kürze Ländernamen für die Y-Achse
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
        
                # 4) Highlight-Spalte für Focal Country
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                # 5) Erstes horizontales Balkendiagramm: alle Länder
                fig_ctry = px.bar(
                    country_avg,
                    x="Tables_per_500",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"Tables_per_500": "Tables per 500 Words", "country_short": ""}
                )
                # Peer-Average als Linie
                overall_avg = country_avg["Tables_per_500"].mean()
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
                # Werte außen anzeigen
                fig_ctry.update_traces(texttemplate="%{x:.1f}", textposition="outside", cliponaxis=False)
                fig_ctry.update_layout(showlegend=False, xaxis_title="Tables per 500 Words")
        
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # -------------------------------------------------------
                # 6) Kompaktvergleich: Focal Country vs. Other Countries
                #    (zwei Balken nebeneinander)
                # -------------------------------------------------------
        
                # focal_avg aus country_avg holen
                focal_avg = (
                    country_avg
                    .loc[country_avg["country"] == focal_country, "Tables_per_500"]
                    .iat[0]
                )
                # other_avg über alle Länder außer Focal Country
                other_avg = (
                    country_avg
                    .loc[country_avg["country"] != focal_country, "Tables_per_500"]
                    .mean()
                )
        
                comp_df = pd.DataFrame({
                    "Group":           [focal_country, "Other Countries"],
                    "Tables_per_500":  [focal_avg,      other_avg]
                })
        
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Tables_per_500",
                    text="Tables_per_500",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    labels={"Tables_per_500": "Tables per 500 Words", "Group": ""}
                )
                # Focal Country links, Other Countries rechts
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.1f}", textposition="outside", width=0.5)
        
                st.subheader(f"{focal_country} vs. Other Countries")
                st.plotly_chart(fig_cmp, use_container_width=True)


            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                sector_avg = (
                    df
                    .groupby("supersector")["tables_500"]
                    .mean()
                    .reset_index(name="Tables per 500")
                )
                fig = px.histogram(
                    sector_avg,
                    x="Tables per 500",
                    nbins=20,
                    opacity=0.8,
                    labels={"Tables per 500": "Count of Tables per 500 words"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # Linien für All vs. Focal Supersector
                overall_avg = sector_avg["Tables per 500"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Tables per 500"].iat[0]
        
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black",
                              annotation_text="<b>All Sectors Avg</b>",
                              annotation_position="top right",
                              annotation_font_color="black",
                              annotation_font_size=16
                             )
                fig.add_vline(x=focal_avg,   line_dash="dash", line_color="red",
                              annotation_text=f"<b>{focal_super} Avg</b>",
                              annotation_position="bottom left",
                              annotation_font_color="red",
                              annotation_font_size=16
                             )
        
                fig.update_layout(showlegend=False,
                                  xaxis_title="Count of Tables per 500 words",
                                  yaxis_title="Number of Sectors",
                                  bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
        
        
            # 2) Bar-Chart aller Supersektoren
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                sector_avg = (
                    df
                    .groupby("supersector")["tables_500"]
                    .mean()
                    .reset_index(name="Tables per 500")
                ).sort_values("Tables per 500", ascending=False)
        
                # auf 15 Zeichen kürzen
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0,15)
                y_order = sector_avg["sector_short"].tolist()
        
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    sector_avg["sector_short"],
                    "Other sectors"
                )
        
                fig_s = px.bar(
                    sector_avg,
                    x="Tables per 500",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "Tables per 500": "Count of Tables per 500 words"}
                )
                fig_s.add_vline(x=sector_avg["Tables per 500"].mean(),
                                line_dash="dash", line_color="black",
                                annotation_text="<b>All Sectors Avg</b>",
                                annotation_position="bottom right",
                                annotation_font_color="black",
                                annotation_font_size=16
                               )
                fig_s.update_traces(texttemplate="%{x:.0f}", textposition="outside", cliponaxis=False)
                fig_s.update_layout(showlegend=False, xaxis_title="Count of Tables per 500 words")
                st.plotly_chart(fig_s, use_container_width=True)
        
                # 3) Kompakter Vergleich: focal vs. avg of others
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Tables per 500"].iat[0]
                others_avg  = sector_avg.loc[sector_avg["supersector"] != focal_super, "Tables per 500"].mean()
        
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "Tables": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Tables",
                    text="Tables",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"Tables": "Count of Tables per 500 words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)


            elif plot_type == "Histogram":
                # Einfaches Histogramm aller Unternehmen
                fig = px.histogram(
                    plot_df,
                    x="tables_500",
                    nbins=20,
                    labels={"tables_500": "Tables per 500 Words", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
                # Peer-Average
                fig.add_vline(
                    x=mean_tables,
                    line_dash="dash",
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Focal Company
                fig.add_vline(
                    x=focal_tables,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig.update_layout(
                    xaxis_title="Tables per 500 Words",
                    yaxis_title="Number of Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif plot_type == "Bar Chart":
                # 1) Peer-Detail-Chart
                peers_df = plot_df.sort_values("tables_500", ascending=False)
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
                fig2 = px.bar(
                    peers_df,
                    x="tables_500",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"tables_500": "Tables per 500 Words", "company_short": "Company", "highlight_label": ""},
                    category_orders={"company_short": y_order_short}
                )
                # Peer-Average-Linie
                fig2.add_vline(
                    x=mean_tables,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={"categoryorder": "array", "categoryarray": y_order_short}
                )
                st.plotly_chart(fig2, use_container_width=True)

                comp_df = pd.DataFrame({
                    "Group": [company, "Peer Average"],
                    "Tables_per_500": [focal_tables, mean_tables]
                })
                
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Tables_per_500",
                    text="Tables_per_500",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Tables_per_500": "Tables per 500 Words", "Group": ""}
                )
                
                # Sorge dafür, dass Dein Unternehmen links steht:
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                
                # Werte außen anzeigen
                fig_cmp.update_traces(texttemplate="%{text:.1f}", textposition="outside", width=0.5)
                
                st.subheader("Peer vs. Company Tables per 500 Words")
                st.plotly_chart(fig_cmp, use_container_width=True)
                
        
            # Fußnote
            st.caption("Number of tables per 500 words in companies’ sustainability reports.")


        elif view == "Images":
            st.subheader(f"Image Size per 500 Words ({benchmark_label})")
        
            # Peer- und Focal-Werte berechnen
            mean_img = benchmark_df["imgsize_pages"].mean()
            focal_img = df.loc[df["company"] == company, "imgsize_pages"].iat[0]
        
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder-Durchschnitt vorbereiten
                country_avg = (
                    df
                    .groupby("country")["imgsize_pages"]
                    .mean()
                    .reset_index(name="ImgSize_per_Page")
                )
        
                overall_avg = country_avg["ImgSize_per_Page"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "ImgSize_per_Page"].iat[0]
        
                # 3) Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="ImgSize_per_Page",
                    nbins=20,
                    opacity=0.8,
                    labels={"ImgSize_per_Page": "Image Size per Page"},
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 4) V-Line Overall Avg
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                # 5) V-Line Focal Country
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
        
                # 6) Layout
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Image Size per Page",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
        
                    
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder-Durchschnitt (ImgSize_per_Page)
                country_avg = (
                    df
                    .groupby("country")["imgsize_pages"]
                    .mean()
                    .reset_index(name="ImgSize_per_Page")
                    .sort_values("ImgSize_per_Page", ascending=False)
                )
        
                # 3) Kürze Ländernamen für Y-Achse
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
        
                # 4) Highlight-Spalte
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                # 5) Erstes horizontales Balkendiagramm: alle Länder
                fig_ctry = px.bar(
                    country_avg,
                    x="ImgSize_per_500",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"ImgSize_per_Page": "Image Size per Page", "country_short": ""}
                )
                # Peer-Average als Linie
                overall_avg = country_avg["ImgSize_per_Page"].mean()
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
                # Werte außen anzeigen
                fig_ctry.update_traces(texttemplate="%{x:.2f}", textposition="outside", cliponaxis=False)
                fig_ctry.update_layout(showlegend=False, xaxis_title="Image Size per Page")
        
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # -------------------------------------------------------
                # 6) Kompaktvergleich: Focal Country vs. Other Countries
                # -------------------------------------------------------
                focal_avg = (
                    country_avg
                    .loc[country_avg["country"] == focal_country, "ImgSize_per_Page"]
                    .iat[0]
                )
                other_avg = (
                    country_avg
                    .loc[country_avg["country"] != focal_country, "ImgSize_per_Page"]
                    .mean()
                )
        
                comp_df = pd.DataFrame({
                    "Group":            [focal_country, "Other Countries"],
                    "ImgSize_per_Page":  [focal_avg,      other_avg]
                })
        
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="ImgSize_per_Page",
                    text="ImgSize_per_Page",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    labels={"ImgSize_per_Page": "Image Size per Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
        
                st.subheader(f"{focal_country} vs. Other Countries")
                st.plotly_chart(fig_cmp, use_container_width=True)


            # 1) Histogramm aller Supersector-Durchschnitte
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                sector_avg = (
                    df
                    .groupby("supersector")["imgsize_pages"]
                    .mean()
                    .reset_index(name="ImgArea per Page")
                )
                fig = px.histogram(
                    sector_avg,
                    x="ImgArea per Page",
                    nbins=20,
                    opacity=0.8,
                    labels={"ImgArea per Page": "Average image area per Page"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # Linien für All vs. Focal Supersector
                overall_avg = sector_avg["ImgArea per Page"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "ImgArea per Page"].iat[0]
        
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black",
                              annotation_text="<b>All Sectors Avg</b>", 
                              annotation_position="top right",
                              annotation_font_color="black",
                              annotation_font_size=16
                             )
                fig.add_vline(x=focal_avg,   line_dash="dash", line_color="red",
                              annotation_text=f"<b>{focal_super} Avg</b>", 
                              annotation_position="bottom left",
                              annotation_font_color="black",
                              annotation_font_size=16
                             )
        
                fig.update_layout(showlegend=False,
                                  xaxis_title="Average image area per Pages",
                                  yaxis_title="Number of Sectors",
                                  bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
        
        
            # 2) Bar-Chart aller Supersektoren
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                sector_avg = (
                    df
                    .groupby("supersector")["imgsize_pages"]
                    .mean()
                    .reset_index(name="ImgArea per Page")
                ).sort_values("ImgArea per Page", ascending=False)
        
                # auf 15 Zeichen kürzen
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0,15)
                y_order = sector_avg["sector_short"].tolist()
        
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    sector_avg["sector_short"],
                    "Other sectors"
                )
        
                fig_s = px.bar(
                    sector_avg,
                    x="ImgArea per Page",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "ImgArea per Page": "Average image area per Page"}
                )
                fig_s.add_vline(x=sector_avg["ImgArea per Page"].mean(),
                                line_dash="dash", line_color="black",
                                annotation_text="<b>All Sectors Avg</b>",
                                annotation_position="bottom right",
                                annotation_font_color="black",
                                annotation_font_size=16
                               )
                fig_s.update_traces(texttemplate="%{x:.0f}", textposition="outside", cliponaxis=False)
                fig_s.update_layout(showlegend=False, xaxis_title="Average image area per Page")
                st.plotly_chart(fig_s, use_container_width=True)
        
                # 3) Kompakter Vergleich: focal vs. avg of others
                focal_avg  = sector_avg.loc[sector_avg["supersector"] == focal_super, "ImgArea per Page"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "ImgArea per Page"].mean()
        
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "ImgArea": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="ImgArea",
                    text="ImgArea",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"ImgArea": "Average image area per 500 words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)


            elif plot_type == "Histogram":
                # Benchmark_df verwenden, um sicher imgsize_500 zu haben
                fig = px.histogram(
                    benchmark_df,
                    x="imgsize_pages",
                    nbins=20,
                    labels={"imgsize_500": "Image Size per Page"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # Peer Average
                fig.add_vline(
                    x=mean_img,
                    line_dash="dash",
                    line_color="black",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Focal Company
                fig.add_vline(
                    x=focal_img,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
        
                fig.update_layout(
                    xaxis_title="Image Size per Page",
                    yaxis_title="Number of Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif plot_type == "Bar Chart":
                # 1) Peer-Detail-Chart
                peers_df = plot_df.sort_values("imgsize_pages", ascending=False)
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
        
                fig2 = px.bar(
                    peers_df,
                    x="imgsize_pages",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"imgsize_pages": "Image Size per Page", "company_short": "Company", "highlight_label": ""},
                    category_orders={"company_short": y_order_short}
                )
                fig2.add_vline(
                    x=mean_img,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig2.update_layout(
                    showlegend=True,
                    legend_title_text="",
                    yaxis={"categoryorder": "array", "categoryarray": y_order_short}
                )
                st.plotly_chart(fig2, use_container_width=True)
        
                comp_df = pd.DataFrame({
                    "Group":            [company, "Peer Average"],
                    "ImgSize_per_Page":  [focal_img, mean_img]
                })
        
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="ImgSize_per_Page",
                    text="ImgSize_per_Page",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"ImgSize_per_Page": "Image Size per Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
        
                st.subheader("Peer vs. Company Image Size per Page")
                st.plotly_chart(fig_cmp, use_container_width=True)
        
            # Fußnote
            st.caption("Total image file size (in KB) per page of companies’ sustainability reports.")
        
    
        elif view == "Sentiment":
            
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                focal_country = df.loc[df["company"] == company, "country"].iat[0]

                # 5) Kompaktvergleich: focal country vs alle anderen
                focal_pos = country_avg.loc[country_avg["country"] == focal_country, "words_pos_500"].iat[0]
                focal_neg = country_avg.loc[country_avg["country"] == focal_country, "words_neg_500"].iat[0]
                other_pos = country_avg.loc[country_avg["country"] != focal_country, "words_pos_500"].mean()
                other_neg = country_avg.loc[country_avg["country"] != focal_country, "words_neg_500"].mean()
            
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
            
                # 1) Länder-Durchschnitte berechnen
                country_avg = (
                    df
                    .groupby("country")[["words_pos_500", "words_neg_500"]]
                    .mean()
                    .reset_index()
                )
            
                # 2) Für positive Wörter: sortieren & highlight-Spalte
                pos_ctry = country_avg.sort_values("words_pos_500", ascending=False)
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
                    x="words_pos_500",
                    y="country",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country:   "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country": y_order_pos},
                    labels={"words_pos_500": "# Positive Words", "country": ""}
                )
                # Peer-Average (aller Länder) als schwarze Linie
                overall_pos = country_avg["words_pos_500"].mean()
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
                neg_ctry = country_avg.sort_values("words_neg_500", ascending=False)
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
                    x="words_neg_500",
                    y="country",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country:   "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country": y_order_neg},
                    labels={"words_neg_500": "# Negative Words", "country": ""}
                )
                overall_neg = country_avg["words_neg_500"].mean()
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
    
    
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Fokus-Land
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder-Durchschnitte vorbereiten
                country_avg = (
                    df
                    .groupby("country")[["words_pos_500", "words_neg_500"]]
                    .mean()
                    .reset_index()
                )
                # Gesamt-Mittelwerte
                overall_pos = country_avg["words_pos_500"].mean()
                overall_neg = country_avg["words_neg_500"].mean()
                # Fokus-Land-Mittelwerte
                focal_pos   = country_avg.loc[country_avg["country"] == focal_country, "words_pos_500"].iat[0]
                focal_neg   = country_avg.loc[country_avg["country"] == focal_country, "words_neg_500"].iat[0]
            
                # 3) Histogramm für alle Länder-Durchschnitte (überlagert, dunkelblau)
                fig_hist = px.histogram(
                    country_avg,
                    x="words_pos_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_pos_500": "# Positive Words"},
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
                    x="words_neg_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_neg_500": "# Negative Words"},
                )
                fig_hist2.update_traces(marker_color="#1f77b4")
                fig_hist2.add_vline(
                    x=focal_neg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg Neg</b>",
                    annotation_position="bottom left",
                    annotation_font_size=16,
                )
                fig_hist2.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg Neg</b>",
                    annotation_position="top right",
                    annotation_font_size=16,
                )
                fig_hist2.update_layout(
                    showlegend=False,
                    xaxis_title="# Negative Words",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
                st.subheader("Negative Words Distribution by Country")
                st.plotly_chart(fig_hist2, use_container_width=True)

            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                # Focal-Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]

                # 4) Kompaktvergleich: focal_super vs. alle anderen
                focal_pos = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_pos_500"].iat[0]
                focal_neg = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_neg_500"].iat[0]
                other_pos = sector_avg.loc[sector_avg["supersector"] != focal_super, "words_pos_500"].mean()
                other_neg = sector_avg.loc[sector_avg["supersector"] != focal_super, "words_neg_500"].mean()
            
                comp_df = pd.DataFrame({
                    "Group":    [focal_super, "Other Sectors"],
                    "Positive": [focal_pos,   other_pos],
                    "Negative": [focal_neg,   other_neg]
                })
            
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y=["Positive", "Negative"],
                    barmode="group",
                    color_discrete_sequence=["#E10600", "#1f77b4"],
                    labels={"value": "Count", "variable": "Sentiment", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other Sectors"]},
                    showlegend=True, legend_title_text=""
                )
                fig_cmp.update_traces(texttemplate="%{y:.0f}", textposition="outside")
                st.subheader("Peer vs. Sector Sentiment")
                st.plotly_chart(fig_cmp, use_container_width=True)
            
                # 1) Durchschnitt pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")[["words_pos_500", "words_neg_500"]]
                    .mean()
                    .reset_index()
                )
            
                # gekürzte Sektor-Namen
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0, 15)
            
                # 2a) Reihenfolge für positive Wörter
                pos_sec = sector_avg.sort_values("words_pos_500", ascending=False)
                pos_sec["highlight"] = np.where(
                    pos_sec["supersector"] == focal_super,
                    focal_super,
                    "Other Sectors"
                )
                # korrekte Kurz-Orderliste
                y_order_pos_short = pos_sec["sector_short"].tolist()
            
                # 3a) Bar Chart positive Wörter
                fig_pos = px.bar(
                    pos_sec,
                    x="words_pos_500",
                    y="sector_short",                        # Kurzspalte verwenden
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other Sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order_pos_short},
                    labels={
                        "words_pos_500": "# Positive Words",
                        "sector_short": ""
                    }
                )
                # Linie Peer-Average
                overall_pos = sector_avg["words_pos_500"].mean()
                fig_pos.add_vline(
                    x=overall_pos,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_size=16
                )
                fig_pos.update_layout(showlegend=False, xaxis_title="# Positive Words")
                st.subheader("Positive Words by Sector")
                st.plotly_chart(fig_pos, use_container_width=True)
            
            
                # 2b) Reihenfolge für negative Wörter
                neg_sec = sector_avg.sort_values("words_neg_500", ascending=False)
                neg_sec["highlight"] = np.where(
                    neg_sec["supersector"] == focal_super,
                    focal_super,
                    "Other Sectors"
                )
                # korrekte Kurz-Orderliste
                y_order_neg_short = neg_sec["sector_short"].tolist()
            
                # 3b) Bar Chart negative Wörter
                fig_neg = px.bar(
                    neg_sec,
                    x="words_neg_500",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other Sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order_neg_short},
                    labels={
                        "words_neg_500": "# Negative Words",
                        "sector_short": ""
                    }
                )
                overall_neg = sector_avg["words_neg_500"].mean()
                fig_neg.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_size=16
                )
                fig_neg.update_layout(showlegend=False, xaxis_title="# Negative Words")
                st.subheader("Negative Words by Sector")
                st.plotly_chart(fig_neg, use_container_width=True)
            
            
            # Histogram: Verteilung der Supersector-Durchschnitte
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                sector_avg = (
                    df
                    .groupby("supersector")[["words_pos_500", "words_neg_500"]]
                    .mean()
                    .reset_index()
                )

                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0, 15)
                
                # Positive Words Distribution
                fig_h1 = px.histogram(
                    sector_avg,
                    x="words_pos_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_pos_500": "# Positive Words"}
                )
                fig_h1.update_traces(marker_color="#1f77b4")
                overall_pos = sector_avg["words_pos_500"].mean()
                focal_pos   = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_pos_500"].iat[0]
                fig_h1.add_vline(x=overall_pos, line_dash="dash", line_color="black",
                                 annotation_text="<b>All Sectors Avg</b>", annotation_position="top right")
                fig_h1.add_vline(x=focal_pos,   line_dash="dash", line_color="red",
                                 annotation_text=f"<b>{focal_super} Avg</b>", annotation_position="bottom left")
                fig_h1.update_layout(showlegend=False, xaxis_title="# Positive Words", yaxis_title="Number of Sectors")
                st.subheader("Positive Words Distribution by Sector")
                st.plotly_chart(fig_h1, use_container_width=True)
            
                # Negative Words Distribution
                fig_h2 = px.histogram(
                    sector_avg,
                    x="words_neg_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_neg_500": "# Negative Words"}
                )
                fig_h2.update_traces(marker_color="#1f77b4")
                overall_neg = sector_avg["words_neg_500"].mean()
                focal_neg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_neg_500"].iat[0]
                fig_h2.add_vline(x=overall_neg, line_dash="dash", line_color="black",
                                 annotation_text="<b>All Sectors Avg</b>", annotation_position="top right")
                fig_h2.add_vline(x=focal_neg,   line_dash="dash", line_color="red",
                                 annotation_text=f"<b>{focal_super} Avg</b>", annotation_position="bottom left")
                fig_h2.update_layout(showlegend=False, xaxis_title="# Negative Words", yaxis_title="Number of Sectors")
                st.subheader("Negative Words Distribution by Sector")
                st.plotly_chart(fig_h2, use_container_width=True)
                      
            
            elif plot_type == "Bar Chart":
                # — 1) Peer vs. Company Sentiment (kompakter Vergleich) —
                st.subheader("Peer vs. Company Sentiment")
            
                # erst die Kennzahlen berechnen
                mean_pos  = benchmark_df["words_pos_500"].mean()
                focal_pos = df.loc[df["company"] == company, "words_pos_500"].iat[0]
                mean_neg  = benchmark_df["words_neg_500"].mean()
                focal_neg = df.loc[df["company"] == company, "words_neg_500"].iat[0]
            
                # dann das Vergleichs-DataFrame anlegen
                comp_df = pd.DataFrame({
                    "company": ["Peer Average", company],
                    "Positive": [mean_pos,  focal_pos],
                    "Negative": [mean_neg,  focal_neg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="company",
                    y=["Positive", "Negative"],
                    barmode="group",
                    # wir lassen color_discrete_sequence hier stehen, wird aber gleich überschrieben
                    color_discrete_sequence=["#FF7F7F", "#E10600"],
                    category_orders={"company": [company, "Peer Average"]},
                    labels={"value": "Count", "company": ""}
                )
                
                # Jetzt pro Trace (0 = Positive, 1 = Negative) die Farben für Peer vs. Company setzen
                # Trace 0 = "Positive": [Peer, Company]
                fig_cmp.data[0].marker.color = ["#ADD8E6", "#FF7F7F"]
                # Trace 1 = "Negative": [Peer, Company]
                fig_cmp.data[1].marker.color = ["#00008B", "#E10600"]
                fig_cmp.update_traces(texttemplate="%{y:.0f}", textposition="outside")
                st.plotly_chart(fig_cmp, use_container_width=True)
            
            
                # — 2) Positive Words by Company —
                st.subheader("Positive Words by Company")
                pos_df = benchmark_df.sort_values("words_pos_500", ascending=False).copy()
                pos_df["highlight"] = np.where(pos_df["company"] == company, company, "Peers")
                pos_df["company_short"] = pos_df["company"].str.slice(0, 15)
                fig_pos = px.bar(
                    pos_df,
                    x="words_pos_500",
                    y="company_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={company: "#E10600", "Peers": "#ADD8E6"},  # Focal=Rot, Peers=Hellblau
                    category_orders={"company_short": pos_df["company_short"].tolist()},
                    labels={"words_pos_500": "# Positive Words", "company_short": ""}
                )
                fig_pos.add_vline(
                    x=mean_pos,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right"
                )
                st.plotly_chart(fig_pos, use_container_width=True)
            
            
                # — 3) Negative Words by Company —
                st.subheader("Negative Words by Company")
                neg_df = benchmark_df.sort_values("words_neg_500", ascending=False).copy()
                neg_df["highlight"] = np.where(neg_df["company"] == company, company, "Peers")
                neg_df["company_short"] = neg_df["company"].str.slice(0, 15)
                fig_neg = px.bar(
                    neg_df,
                    x="words_neg_500",
                    y="company_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={company: "#E10600", "Peers": "#00008B"},  # Focal=Rot, Peers=Dunkelblau
                    category_orders={"company_short": neg_df["company_short"].tolist()},
                    labels={"words_neg_500": "# Negative Words", "company_short": ""}
                )
                fig_neg.add_vline(
                    x=mean_neg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right"
                )
                st.plotly_chart(fig_neg, use_container_width=True)

    
            elif plot_type == "Histogram":
                
                mean_pos  = benchmark_df["words_pos_500"].mean()
                focal_pos = df.loc[df["company"] == company, "words_pos_500"].iat[0]
                mean_neg  = benchmark_df["words_neg_500"].mean()
                focal_neg = df.loc[df["company"] == company, "words_neg_500"].iat[0]
                                
                st.write("Histogram of positive words")
                fig_h1 = px.histogram(benchmark_df, x="words_pos_500", nbins=20,
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
                fig_h2 = px.histogram(benchmark_df, x="words_neg_500", nbins=20)
        
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
    
        elif view == "Standardized Language":
            st.subheader(f"Standardized Language ({benchmark_label})")
            
            # Mittelwert und Focal-Wert ermitteln
            mean_boiler   = benchmark_df["boiler_500"].mean()
            focal_boiler  = df.loc[df["company"] == company, "boiler_500"].iat[0]
        
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Länder-Durchschnitt vorbereiten
                country_avg = (
                    df
                    .groupby("country")["boiler_500"]
                    .mean()
                    .reset_index(name="StdLang")
                )
                overall_avg = country_avg["StdLang"].mean()
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                focal_avg = country_avg.loc[country_avg["country"] == focal_country, "StdLang"].iat[0]
        
                # Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="StdLang",
                    nbins=20,
                    opacity=0.8,
                    labels={"StdLang": "Standardized Language"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # Peer-Average-Linie (schwarz gestrichelt)
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Focal Country Linie (rot gestrichelt)
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
        
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Standardized Language",
                    yaxis_title="Number of Countries",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
        
        
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # Länder-Durchschnitt berechnen
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                country_avg = (
                    df
                    .groupby("country")["boiler_500"]
                    .mean()
                    .reset_index(name="StdLang")
                    .sort_values("StdLang", ascending=False)
                )
                # Länder-Namen kürzen
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
                # Highlight
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                fig_ctry = px.bar(
                    country_avg,
                    x="StdLang",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"StdLang": "Standardized Language", "country_short": ""}
                )
                # Peer-Average-Linie
                overall_avg = df["boiler_500"].mean()
                fig_ctry.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_size=16
                )
        
                fig_ctry.update_traces(
                    texttemplate="%{x:.2f}",
                    textposition="outside",
                    cliponaxis=False
                )
                fig_ctry.update_layout(
                    showlegend=False,
                    xaxis_title="Standardized Language"
                )
                st.plotly_chart(fig_ctry, use_container_width=True)
        
        
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                sector_avg = (
                    df
                    .groupby("supersector")["boiler_500"]
                    .mean()
                    .reset_index(name="StdLang")
                )
                overall_avg = sector_avg["StdLang"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "StdLang"].iat[0]
        
                fig = px.histogram(
                    sector_avg,
                    x="StdLang",
                    nbins=20,
                    opacity=0.8,
                    labels={"StdLang": "Standardized Language"}
                )
                fig.update_traces(marker_color="#1f77b4")
                fig.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"<b>{focal_super} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Standardized Language",
                    yaxis_title="Number of Sectors"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                sector_avg = (
                    df
                    .groupby("supersector")["boiler_500"]
                    .mean()
                    .reset_index(name="StdLang")
                    .sort_values("StdLang", ascending=False)
                )
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0, 15)
                y_order = sector_avg["sector_short"].tolist()
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    sector_avg["sector_short"],
                    "Other sectors"
                )
        
                fig_s = px.bar(
                    sector_avg,
                    x="StdLang",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"StdLang": "Standardized Language", "sector_short": ""}
                )
                fig_s.add_vline(
                    x=sector_avg["StdLang"].mean(),
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_size=16
                )
                fig_s.update_traces(
                    texttemplate="%{x:.2f}",
                    textposition="outside",
                    cliponaxis=False
                )
                fig_s.update_layout(showlegend=False, xaxis_title="Standardized Language")
                st.plotly_chart(fig_s, use_container_width=True)

            elif plot_type == "Histogram":
                # Einfach alle Companies im Benchmark_df
                fig = px.histogram(
                    benchmark_df,
                    x="boiler_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"boiler_500":"Standardized Language","count":"Number of Companies"}
                )
                fig.update_traces(marker_color="#1f77b4")
                # Peer-Average (schwarz) und Focal (rot)
                fig.add_vline(x=mean_boiler,  line_dash="dash", line_color="black",
                             annotation_text="<b>Peer Avg</b>", annotation_position="top right")
                fig.add_vline(x=focal_boiler, line_dash="dash", line_color="red",
                             annotation_text=f"<b>{company}</b>", annotation_position="bottom left",
                             annotation_font_color="red")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
            # — **Alle Peers**: Bar Chart über boiler_500 —
            elif plot_type == "Bar Chart":
                peers_df = benchmark_df.sort_values("boiler_500", ascending=False).copy()
                peers_df["company_short"] = peers_df["company"].str.slice(0,15)
                order_short = peers_df["company_short"].tolist()
                peers_df["highlight"] = np.where(
                    peers_df["company"] == company,
                    peers_df["company_short"],
                    "Peers"
                )
        
                fig2 = px.bar(
                    peers_df,
                    x="boiler_500",
                    y="company_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    category_orders={"company_short": order_short},
                    labels={"boiler_500":"Standardized Language","company_short":""}
                )
                # Peer-Average Linie
                fig2.add_vline(x=mean_boiler,
                               line_dash="dash", line_color="black",
                               annotation_text="<b>Peer Avg</b>",
                               annotation_position="bottom right")
                fig2.update_traces(texttemplate="%{x:.2f}", textposition="outside", cliponaxis=False)
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        
            # Fußnote
            st.caption("Standardized Language (boilergrams per 500 words)")

        
        elif view == "Language Complexity":
            st.subheader(f"Language Complexity ({benchmark_label})")
        
            # 1) Peer-Average und Focal-Wert holen
            mean_fog  = benchmark_df["fog_avg"].mean()
            focal_fog = df.loc[df["company"] == company, "fog_avg"].iat[0]
    
    
            if benchmark_type == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder-Durchschnitt für fog berechnen
                country_avg = (
                    df
                    .groupby("country")["fog_avg"]           # statt Sustainability_Page_Count jetzt fog
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
                    annotation_font_color="black",
                    annotation_font_size=16,
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
                    annotation_font_size=16,
                )
            
                # 7) Layout-Feinschliff
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Language Complexity (Fog)",
                    yaxis_title="Number of Countries",
                    bargap=0.1,
                )
            
                st.plotly_chart(fig, use_container_width=True)
    
            elif benchmark_type == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Bestimme das Land des gewählten Unternehmens
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Berechne den Durchschnitt des Fog-Scores pro Land
                country_avg = (
                    df
                    .groupby("country")["fog_avg"]
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

            

            # —————————————————————————————————————————————————————————————————————————————————
            # Between Sector Comparison für Fog-Index
            # —————————————————————————————————————————————————————————————————————————————————
        
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                sector_avg = (
                    df
                    .groupby("supersector")["fog_avg"]
                    .mean()
                    .reset_index(name="Fog-Index")
                )
                fig = px.histogram(
                    sector_avg,
                    x="Fog-Index",
                    nbins=20,
                    opacity=0.8,
                    labels={"Fog-Index": "Fog-Index"}
                )
                fig.update_traces(marker_color="#1f77b4")
                overall_avg = sector_avg["Fog-Index"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg_sec = sector_avg.loc[sector_avg["supersector"] == focal_super, "Fog-Index"].iat[0]
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black",
                              annotation_text="<b>All Sectors Avg</b>", 
                              annotation_position="top right",
                              annotation_font_color="black",
                              annotation_font_size=16
                             )
                fig.add_vline(x=focal_avg_sec, line_dash="dash", line_color="red",
                              annotation_text=f"<b>{focal_super} Avg</b>",
                              annotation_position="bottom left",
                              annotation_font_color="red",
                              annotation_font_size=16
                             )
                fig.update_layout(showlegend=False, xaxis_title="Fog-Index", yaxis_title="Number of Sectors")
                st.plotly_chart(fig, use_container_width=True)
        
            elif benchmark_type == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                sector_avg = (
                    df
                    .groupby("supersector")["fog_avg"]
                    .mean()
                    .reset_index(name="Fog-Index")
                ).sort_values("Fog-Index", ascending=False)
                sector_avg["sector_short"] = sector_avg["supersector"].str.slice(0,15)
                y_order = sector_avg["sector_short"].tolist()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    sector_avg["sector_short"],
                    "Other sectors"
                )
                fig_s = px.bar(
                    sector_avg,
                    x="Fog-Index",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "Fog-Index": "Fog-Index"}
                )
                fig_s.add_vline(x=sector_avg["Fog-Index"].mean(), line_dash="dash",
                                line_color="black", annotation_text="<b>All Sectors Avg</b>",
                                annotation_position="bottom right",
                                annotation_font_color="black",
                                anotation_font_size=16
                               )
                fig_s.update_traces(texttemplate="%{x:.1f}", textposition="outside", cliponaxis=False)
                fig_s.update_layout(showlegend=False, xaxis_title="Fog-Index")
                st.plotly_chart(fig_s, use_container_width=True)
        
                # Kompakter Vergleich: Focal Supersector vs. andere Sektoren avg
                focal_avg_sec = sector_avg.loc[sector_avg["supersector"] == focal_super, "Fog-Index"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "Fog-Index"].mean()
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "Fog-Index": [focal_avg_sec, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Fog-Index",
                    text="Fog-Index",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"Fog-Index": "Fog-Index", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.1f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
                    
                    
            elif plot_type == "Histogram":
                fig_fog = px.histogram(
                    plot_df, x="fog_avg", nbins=20,
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
                peers_fog = plot_df.sort_values("fog_avg", ascending=False)
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
                    x="fog_avg",
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
