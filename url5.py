import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import textwrap
from urllib.parse import unquote, quote

#-------------------------------------------------------------------------
# 1. Page config
#-------------------------------------------------------------------------
st.set_page_config(page_title="CSRD Benchmarking Dashboard", layout="wide")

st.markdown(
    """
    <style>
      /* 1) In der Sidebar alle Markdown-Container enger machen */
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        margin-block-start: 0.2rem !important;
        margin-block-end:   0.2rem !important;
        padding:            0 !important;
      }

      /* 2) Und für jede Radio-Gruppe (role="radiogroup") den Abstand verringern */
      [data-testid="stSidebar"] [role="radiogroup"] {
        margin-block-start: 0.2rem !important;
        margin-block-end:   0.2rem !important;
        padding:            0 !important;
      }

      /* 3) Überschriften (h3) in der Sidebar etwas knapper fassen */
      [data-testid="stSidebar"] h3 {
        margin: 0.3rem 0 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)
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
df = pd.read_csv("450_final_version.csv")

# direkt nach dem Einlesen
df['SASB industry'] = (
    df['SASB industry']
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
df['supersector'] = df['SASB industry'] \
    .map(supersector_map) \
    .fillna('Other')

def smart_layout(fig, num_items, *,
                 min_height=300,    # absolute Mindesthöhe
                 max_height=1200,   # absolute Maxhöhe
                 bar_height=40,     # Pixel pro Item
                 min_font=10,        # absolute Mindestschrift
                 max_font=16        # absolute Maxschrift
                ):
    """
    Passt Höhe und Schriften an, je nachdem wie viele Balken (num_items) wir haben.
    Bei horizontalen Bars wird die y-Achse automatisch inverted, 
    so dass der größte Wert oben steht.
    """
    # 1) Höhe: pro Item bar_height px plus etwas Padding
    height = min(max_height, max(min_height, num_items * bar_height + 150))
    
    # 2) Schriftgröße: bei wenig Items groß, bei vielen kleiner
    #    lineare Interpolation zwischen max_font (bei 1 Item) und min_font (bei 30+ Items)
    if num_items <= 1:
        font_size = max_font
    else:
        font_size = max(min_font,
                        max_font - (num_items-1) * (max_font-min_font) / 29
                       )
    font_size = round(font_size, 1)
    
    # 3) Grund-Layout
    fig.update_layout(
        height=height,
        font=dict(size=font_size),
        margin=dict(l=150, r=20, t=40, b=40),
        yaxis=dict(tickfont=dict(size=font_size)),
        xaxis=dict(tickfont=dict(size=font_size))
    )

    # 4) Wenn es mindestens einen horizontalen Bar-Trace gibt, y-Achse invertieren
    if any(getattr(trace, "orientation", None) == "h" for trace in fig.data):
        fig.update_yaxes(autorange="reversed")
    
    return fig

#--------------------------------------------------------------------------------------
# 3. URL-Param & Default
#--------------------------------------------------------------------------------------
company_list    = df["company"].dropna().unique().tolist()
mapping_ci      = {n.strip().casefold(): n for n in company_list}

# Get and decode the company from URL
raw = st.query_params.get("company", None)
if isinstance(raw, list):
    raw = raw[0] if raw else None

if raw:
    raw = unquote(raw).strip()
    # Try to find the company in our mapping
    if raw in company_list:
        default_company = raw
    # Then try case-insensitive match
    elif raw.casefold() in mapping_ci:
        default_company = mapping_ci[raw.casefold()]
    else:
        default_company = company_list[0]
else:
    default_company = company_list[0]

#-----------------------------------------------------------------------------------------
# 4. Layout: drei Columns
#------------------------------------------------------------------------------------------
left, main, right = st.columns([2, 5, 2])

# 4a. Linke Sidebar: Company + Peer-Group-/Cross-Comparison-Radio
with left:
    # 1) Große Überschrift für Company
    st.subheader("Select a company:")

    # 2) Dann das Selectbox selbst, ganz ohne Label-Text
    default_idx = company_list.index(default_company)
    company = st.selectbox(
        "",                    # <— kein Label hier
        options=company_list,
        index=default_idx,
        key="company_selector"
    )
    
    # Update URL when company changes
    if company != default_company:
        st.query_params["company"] = company
        
    selected = company

    # 3) Wahl des Benchmark-Modes
    st.subheader("Choose Benchmarking Mode")
    mode = st.radio(
        "", 
        [
            "Company vs. Peer Group",
            "Company Sector vs Other Sectors",
            "Company Country vs Other Countries"
        ],
        key="benchmark_mode"
    )
    
    # 4) Je nach Mode eine zweite Auswahl einblenden
    if mode == "Company vs. Peer Group":
        st.markdown("**Select your peer group:**")
        peer_group = st.radio(
            "",
            [
                "Sector Peers",
                "Country Peers",
                "Market Cap Peers",
                "Choose specific peers",
                "All CSRD First Wave"
            ],
            key="peer_group"
        )
    
        if peer_group == "Choose specific peers":
            peer_selection = st.multiselect(
                "Choose specific peer companies:",
                options=company_list,
                default=[]
            )
        else:
            peer_selection = []
    
    elif mode == "Company Sector vs Other Sectors":
        st.markdown("**Company Sector vs Other Sectors**")
        # hier könntest du z.B. einen simplen Radio mit nur einer Option anzeigen
        _ = st.radio("", ["Company Sector vs Other Sectors"], key="sector_mode")
    
    elif mode == "Company Country vs Other Countries":
        st.markdown("**Company Country vs Other Countries**")
        _ = st.radio("", ["Company Country vs Other Countries"], key="country_mode")


# 4b. Rechte Spalte: View & Chart Type
with right:
    st.header("What do you want to benchmark?")

    # Hier ganz bewusst *nur* die echten Auswahl-Strings
    view_options = [
        "Number of Pages",
        "Number of Words",
        "Number of Norm Pages",
        "ESRS Topic Shares",
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
        "Number of Norm Pages": "Number of Norm Pages converts each text's total word count into standardized 500-word pages. A value of 2.5 means the document contains the equivalent of 2½ standard pages.",
        "ESRS Topic Shares": "This method utilizes word2vec (Mikolov et al. 2013), an algorithm that learns the meaning of words in a text using a neural networks. We use the resulting textual embeddings to generate a dictionary of keywords for each ESRS. Based on general seed words (e.g., greenhouse gas emissions for E1 climate change), we pick the 500 most similar words based on the embeddings. The resulting list of keywords allows us to broadly capture ESG-related discussions in reporting even before ESRS-specific terminology has been introduced. The main measure shown in this presentation is the number of words from sentences that contain a keyword from one of the 11 ESRS standards.",
        "Numbers": "Count of Numbers per Norm Page. A norm page is a standardized 500-word page.",
        "Tables": "Count of tables per Norm Page. A norm page is a standardized 500-word page.",
        "Images": "Average image area per Norm Page. A norm page is a standardized 500-word page.",
        "Standardized Language": "Standardized language measures how often a company relies on recurring four-word sequences (so-called tetragrams) in its reporting." ,
        "Language Complexity": "Fog-Index, an aggregate measure of readability where higher values suggest more complex and technical language - which may be appropriate in professional sustainability disclosures.",
        "Sentiment": "Average number of positive and negative words per Norm Page. A norm page is a standardized 500-word page.",
        "Peer Company List": "List of companies included in the peer group based on your choice.",
    }

    # Und zeige diese Erklärung direkt unter dem Radio:
    if view in help_texts:
        st.info(help_texts[view])

    st.header("Chart Type")

    if view == "ESRS Topic Shares":
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
# 1) Bestimme benchmark_df & benchmark_label anhand des Modes und ggf. peer_group
if mode == "Company vs. Peer Group":
    # Unter-Mode: Sector / Country / Market Cap / All CSRD / Choose specific
    if peer_group == "Sector Peers":
        supersec      = df.loc[df["company"] == company, "supersector"].iat[0]
        benchmark_df  = df[df["supersector"] == supersec]
        benchmark_label = f"Sector Peers: {supersec}"

    elif peer_group == "Country Peers":
        country       = df.loc[df["company"] == company, "country"].iat[0]
        benchmark_df  = df[df["country"] == country]
        benchmark_label = f"Country Peers: {country}"

    elif peer_group == "Market Cap Peers":
        terc          = df.loc[df["company"] == company, "Market_Cap_Cat"].iat[0]
        lbl           = (
            "Small-Cap" if 1 <= terc <= 3 else
            "Mid-Cap"   if 4 <= terc <= 7 else
            "Large-Cap" if 8 <= terc <= 10 else
            "Unknown"
        )
        benchmark_df  = df[df["Market_Cap_Cat"] == terc]
        benchmark_label = f"Market Cap Peers: {lbl}"

    elif peer_group == "All CSRD First Wave":
        benchmark_df    = df.copy()
        benchmark_label = "All CSRD First Wave"

    elif peer_group == "Choose specific peers":
        sel = set(peer_selection) | {company} if peer_selection else {company}
        benchmark_df    = df[df["company"].isin(sel)]
        benchmark_label = f"Selected Peers ({len(benchmark_df)} firms)"

    else:
        # Fallback, falls peer_group mal None ist
        benchmark_df    = df.copy()
        benchmark_label = "All CSRD First Wave"

elif mode == "Company Country vs Other Countries":
    focal_country = df.loc[df["company"] == company, "country"].iat[0]
    country_df    = df[df["country"] == focal_country]
    others_df     = df[df["country"] != focal_country]
    benchmark_df  = pd.concat([
        country_df.assign(_group=focal_country),
        others_df.assign(_group="Others")
    ], ignore_index=True)
    benchmark_label = f"{focal_country} vs Others"

elif mode == "Company Sector vs Other Sectors":
    focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
    super_df    = df[df["supersector"] == focal_super]
    others_df   = df[df["supersector"] != focal_super]
    benchmark_df = pd.concat([
        super_df.assign(_group=focal_super),
        others_df.assign(_group="Other sectors")
    ], ignore_index=True)
    benchmark_label = f"{focal_super} vs Other sectors"

# 2) Focal‐Werte bleiben gleich
focal_pages = df.loc[df["company"] == company, "Sustainability_Page_Count"].iat[0]
focal_words = df.loc[df["company"] == company, "words"].iat[0]
# --------------------------------------------------------------------
# 8. Main-Bereich: Header + Trennstrich + erste Content-Spalte
# --------------------------------------------------------------------
with main:
    header_col, _ = st.columns([3, 1], gap="large")
    with header_col:
        st.header("CSRD Benchmarking Dashboard")
        st.markdown(
            """
            <p style="
              font-size:16px;
              color:#555;
              margin-top:-8px;
              margin-bottom:1rem;
            ">
              Please select a peer group and variable of interest to benchmark your company's 
              CSRD reporting. All analyses are based on companies' 2024 sustainability reports.
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
        
            # Mittelwert aller Peers und Wert Deiner Firma
            mean_pages  = benchmark_df["Sustainability_Page_Count"].mean()
            focal_pages = df.loc[df["company"] == company, "Sustainability_Page_Count"].iat[0]
        
            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["Sustainability_Page_Count"]
                        .mean()
                        .reset_index(name="Pages")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "Pages": [focal_pages]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="Pages", y="Group", orientation="h", text="Pages",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"Pages":"Pages","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig.update_layout(xaxis_title="Pages", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "Pages": [mean_pages]
                    })
                    fig = px.bar(
                        comp_df,
                        x="Pages",
                        y="Group",
                        orientation="h",
                        text="Pages",
                        labels={"Pages": "Pages", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
        
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # … dein bestehender Histogramm‐Code für Länder …
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                country_avg = (
                    df
                    .groupby("country")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Pages")
                )
                overall_avg = country_avg["Pages"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Pages"].iat[0]
                fig = px.histogram(
                    country_avg, x="Pages", nbins=20, opacity=0.8, labels={"Pages": "Pages"}
                )
                fig.update_traces(marker_color="#1f77b4")
                fig.add_vline(x=overall_avg, line_dash="dash", line_color="black", line_width=2,
                             annotation_text="<b>All Countries Avg</b>", annotation_position="top right")
                fig.add_vline(x=focal_avg,   line_dash="dash", line_color="red",   line_width=2,
                             annotation_text=f"<b>{focal_country} Avg</b>", annotation_position="bottom left")
                fig.update_layout(showlegend=False, xaxis_title="Pages", yaxis_title="Countries", bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
        
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # … dein bestehender Bar-Chart‐Code für Länder …
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                country_avg = (
                    df
                    .groupby("country")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Pages")
                    .sort_values("Pages", ascending=False)
                )
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
                fig_ctry = px.bar(
                    country_avg,
                    x="Pages", y="country_short", orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"Pages": "Pages", "country_short": ""}
                )
                overall_avg = df["Sustainability_Page_Count"].mean()
                fig_ctry.add_vline(x=overall_avg, line_dash="dash", line_color="black", line_width=2,
                                   annotation_text="<b>Peer Average</b>", annotation_position="bottom right")
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
                fig_ctry.update_yaxes(categoryorder="array", categoryarray=y_order)
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # optionaler Vergleich Focal vs. Other countries avg …
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "Pages": [
                        country_avg.loc[country_avg["country"] == focal_country, "Pages"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "Pages"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group", y="Pages", text="Pages",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"Pages": "Pages", "Group": ""}
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                fig_cmp.update_layout(xaxis={"categoryorder":"array","categoryarray":[focal_country,"Other countries average"]},
                                      showlegend=False)
                st.plotly_chart(fig_cmp, use_container_width=True)

            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Seitenzahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Sustainability_Page_Count")
                )
                # 2) Plot
                fig = px.histogram(
                    sector_avg,
                    x="Sustainability_Page_Count",
                    nbins=20,
                    opacity=0.8,
                    labels={"Sustainability_Page_Count": "Sustainability_Page_Count"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["Sustainability_Page_Count"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Sustainability_Page_Count"].iat[0]
        
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
                                  xaxis_title="Pages",
                                  yaxis_title="Sectors",
                                  bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)


            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap
            
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnittliche Sietnzahl pro Supersector, absteigend sortiert
                sector_avg = (
                    df
                    .groupby("supersector")["Sustainability_Page_Count"]
                    .mean()
                    .reset_index(name="Sustainability_Page_Count")
                    .sort_values("Sustainability_Page_Count", ascending=False)
                )
            
                # 3) Mehrzeilige Labels mit "\n" (wrap bei 20 Zeichen)
                sector_avg["sector_short"] = sector_avg["supersector"].apply(
                    lambda s: "<br>".join(textwrap.wrap(s, width=20))
                )
            
                # 4) Reihenfolge für category_orders: 
                #    wir kehren die absteigend sortierte Liste um → niedrigste zuerst
                y_order = sector_avg["sector_short"].tolist()[::-1]
            
                # 5) Highlight fürs eigene Supersector
                focal_label = "\n".join(textwrap.wrap(focal_super, width=20))
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
            
                # 6) Horizontalen Bar‐Chart bauen
                fig_s = px.bar(
                    sector_avg,
                    x="Sustainability_Page_Count",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_label: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},  # niedrig→hoch
                    labels={"sector_short": "", "Sustainability_Page_Count": "Pages"},
                    hover_data={"Sustainability_Page_Count": ":.0f"}
                )
            
                # 7) Linie für den Durchschnitt aller Sektoren
                avg_all = sector_avg["Sustainability_Page_Count"].mean()
                fig_s.add_vline(
                    x=avg_all,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 8) Einheitliches Styling & Höhe/Shriftgröße + automatische y-Reverse
                fig_s = smart_layout(fig_s, len(sector_avg))
                fig_s.update_layout(showlegend=False)
            
                # 9) Chart rendern
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Optional: Vergleichs‐Chart Supersector vs Rest —
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "Sustainability_Page_Count"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "Sustainability_Page_Count"].mean()
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "Sustainability_Page_Count": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Sustainability_Page_Count",
                    text="Sustainability_Page_Count",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"Sustainability_Page_Count": "Pages", "Group": ""}
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
                fig.update_layout(xaxis_title="Pages", yaxis_title="Companies")
                st.plotly_chart(fig, use_container_width=True)
                            
    
            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart aller Peer-Unternehmen, horizontale Balken nach Wert absteigend sortieren
                peers_df = plot_df.sort_values("Sustainability_Page_Count", ascending=False)
                mean_pages = benchmark_df["Sustainability_Page_Count"].mean()
            
                # 2) Kurz-Namen für die Y-Achse, damit sie nicht zu lang werden
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
            
                # 3) Horizontales Balkendiagramm erstellen
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
            
                # 4) Peer-Average-Linie hinzufügen
                fig2.add_vline(
                    x=mean_pages,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 5) Einheitliches Styling direkt hier anwenden
                fig2 = smart_layout(fig2, len(peers_df))
                fig2.update_layout(showlegend=False)
            
                # 6) Chart ausgeben
                st.plotly_chart(fig2, use_container_width=True)
            
                # — Vertikaler Vergleich Peer Average vs. Focal Company —
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
                # rote Firma links anzeigen
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_avg, use_container_width=True)
    
    
        
        elif view == "Number of Words":
            st.subheader(f"Number of Words ({benchmark_label})")
    
            # 1) Peer-Average berechnen
            mean_words = benchmark_df["words"].mean()

            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["words"]
                        .mean()
                        .reset_index(name="Words")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "Words": [focal_words]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="Words", y="Group", orientation="h", text="Words",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"Words":"Words","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig.update_layout(xaxis_title="Words", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "Words": [mean_words]
                    })
                    fig = px.bar(
                        comp_df,
                        x="Words",
                        y="Group",
                        orientation="h",
                        text="Words",
                        labels={"Words": "Words", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
    
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder‐Durchschnitt der Wortzahl vorbereiten
                country_avg = (
                    df
                    .groupby("country")["words"]
                    .mean()
                    .reset_index(name="Words")
                )
            
                overall_avg = country_avg["Words"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Words"].iat[0]
            
                # 3) Einfaches Histogramm aller Länder‐Durchschnitte in Dunkelblau
                fig = px.histogram(
                    country_avg,
                    x="Words",
                    nbins=20,
                    opacity=0.8,
                    labels={"Words": "Words"},
                )
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
            
                # 5) V-Line für focal Country Avg (rot gestrichelt)
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
            
                # 6) Legende ausblenden und Achsentitel anpassen
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Words",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
            
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Durchschnittliche Wortzahl pro Country und Sortierung (absteigend)
                country_avg = (
                    df
                    .groupby("country")["words"]
                    .mean()
                    .reset_index(name="Words")
                    .sort_values("Words", ascending=False)
                )
            
                # 3) Labels kürzen (max. 15 Zeichen)
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Reihenfolge (absteigend sortiert) ohne zusätzliches Umdrehen
                y_order = country_avg["country_short"].tolist()
            
                # 5) Highlight für Dein Land
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
            
                # 6) Bar-Chart erzeugen mit category_orders
                fig_ctry = px.bar(
                    country_avg,
                    x="Words",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country_short": y_order},
                    labels={"Words": "Words", "country_short": ""},
                )
            
                # 7) Peer-Average-Linie
                overall_avg = df["words"].mean()
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
            
                # 8) Dynamische Höhe & Schriftgröße
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
            
                # 9) Reihenfolge final festlegen
                fig_ctry.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Focal vs. Other Countries Avg —
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "Words": [
                        country_avg.loc[country_avg["country"] == focal_country, "Words"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "Words"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={
                        "categoryorder": "array",
                        "categoryarray": [focal_country, "Other countries average"]
                    },
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

             # Histogramm aller Supersector‐Durchschnitte
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Seitenzahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["words"]
                    .mean()
                    .reset_index(name="words")
                )
                # 2) Plot
                fig = px.histogram(
                    sector_avg,
                    x="words",
                    nbins=20,
                    opacity=0.8,
                    labels={"words": "words"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["words"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "words"].iat[0]
        
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
                                  xaxis_title="words",
                                  yaxis_title="Sectors",
                                  bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)


            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap
            
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnittliche Sietnzahl pro Supersector, absteigend sortiert
                sector_avg = (
                    df
                    .groupby("supersector")["words"]
                    .mean()
                    .reset_index(name="words")
                    .sort_values("words", ascending=False)
                )
            
                # 3) Mehrzeilige Labels mit "\n" (wrap bei 20 Zeichen)
                sector_avg["sector_short"] = sector_avg["supersector"].apply(
                    lambda s: "<br>".join(textwrap.wrap(s, width=20))
                )
            
                # 4) Reihenfolge für category_orders: 
                #    wir kehren die absteigend sortierte Liste um → niedrigste zuerst
                y_order = sector_avg["sector_short"].tolist()[::-1]
            
                # 5) Highlight fürs eigene Supersector
                focal_label = "\n".join(textwrap.wrap(focal_super, width=20))
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
            
                # 6) Horizontalen Bar‐Chart bauen
                fig_s = px.bar(
                    sector_avg,
                    x="words",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_label: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},  # niedrig→hoch
                    labels={"sector_short": "", "words": "Words"},
                    hover_data={"words": ":.0f"}
                )
            
                # 7) Linie für den Durchschnitt aller Sektoren
                avg_all = sector_avg["words"].mean()
                fig_s.add_vline(
                    x=avg_all,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 8) Einheitliches Styling & Höhe/Shriftgröße + automatische y-Reverse
                fig_s = smart_layout(fig_s, len(sector_avg))
                fig_s.update_layout(showlegend=False)
            
                # 9) Chart rendern
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Optional: Vergleichs‐Chart Supersector vs Rest —
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "words"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "words"].mean()
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "words": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="words",
                    text="words",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"words": "Words", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
    
    
            elif plot_type == "Histogram":
                # 1) Gesamt-Durchschnitt und Focal-Wert der Wortzahl berechnen
                mean_words  = benchmark_df["words"].mean()
                focal_words = df.loc[df["company"] == company, "words"].iat[0]
            
                # 2) Histogramm aller Peer-Unternehmen nach Wortzahl
                fig = px.histogram(
                    plot_df,
                    x="words",
                    nbins=20,
                    opacity=0.8,
                    labels={"words": "Words", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 3) Linien für Peer Average und Focal Company
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
            
                # 4) Achsentitel anpassen
                fig.update_layout(
                    xaxis_title="Words",
                    yaxis_title="Companies"
                )
            
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart: Peer-Unternehmen nach Wortzahl absteigend sortieren
                peers_df  = plot_df.sort_values("words", ascending=False)
                mean_words = benchmark_df["words"].mean()
                focal_words = df.loc[df["company"] == company, "words"].iat[0]
            
                # 2) Kurz-Namen für Y-Achse (max. 15 Zeichen)
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short             = peers_df["company_short"].tolist()[::-1]
            
                # 3) Horizontales Balkendiagramm erzeugen
                fig2 = px.bar(
                    peers_df,
                    x="words",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"words": "Words", "company_short": "Company", "highlight_label": ""},
                    category_orders={"company_short": y_order_short},
                )
            
                # 4) Peer-Average-Linie hinzufügen
                fig2.add_vline(
                    x=mean_words,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 5) Styling & automatische Höhen- und Reihenfolge-Logik
                fig2 = smart_layout(fig2, len(peers_df))
                fig2.update_layout(showlegend=False)
            
                # 6) Chart ausgeben
                st.plotly_chart(fig2, use_container_width=True)
            
                # — Vertikaler Vergleich Peer Average vs. Focal Company —
                comp_df = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "Words": [mean_words, focal_words]
                })
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="Words",
                    text="Words",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Words": "Words", "Group": ""}
                )
                # rote Firma links anzeigen
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_avg, use_container_width=True)


        elif view == "Number of Norm Pages":
            st.subheader(f"Number of Norm Pages ({benchmark_label})")
        
            # 0) Norm Pages berechnen (500 Wörter = 1 Norm-Page)
            df["norm_pages"]         = df["words"] / 500
            benchmark_df["norm_pages"] = benchmark_df["words"] / 500
            plot_df["norm_pages"]    = plot_df["words"] / 500

            focal_norm_pages = df.loc[df["company"] == company, "norm_pages"].iat[0]
        
            # 1) Peer-Average berechnen
            mean_norm_pages = benchmark_df["norm_pages"].mean()

            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["norm_pages"]
                        .mean()
                        .reset_index(name="Norm Pages")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "Norm Pages": [focal_norm_pages]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="Norm Pages", y="Group", orientation="h", text="Norm Pages",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"Norm Pages":"Norm Pages","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig.update_layout(xaxis_title="Pages", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "Norm Pages": [mean_norm_pages]
                    })
                    fig = px.bar(
                        comp_df,
                        x="Norm Pages",
                        y="Group",
                        orientation="h",
                        text="Pages",
                        labels={"Norm Pages": "Norm Pages", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
        
            # Company Country vs Other Countries
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1a) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 1b) Länder-Durchschnitt der Norm-Pages vorbereiten
                country_avg = (
                    df
                    .groupby("country")["norm_pages"]
                    .mean()
                    .reset_index(name="NormPages")
                )
                overall_avg = country_avg["NormPages"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "NormPages"].iat[0]
        
                # 1c) Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="NormPages",
                    nbins=20,
                    opacity=0.8,
                    labels={"NormPages": "Norm Pages"}
                )
                fig.update_traces(marker_color="#1f77b4")
                # 1d) V-Lines
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
                    xaxis_title="Norm Pages",
                    yaxis_title="Countries",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 2a) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2b) Durchschnitt pro Country und Sortierung
                country_avg = (
                    df
                    .groupby("country")["norm_pages"]
                    .mean()
                    .reset_index(name="NormPages")
                    .sort_values("NormPages", ascending=False)
                )
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                # 2c) Bar-Chart zeichnen
                fig_ctry = px.bar(
                    country_avg,
                    x="NormPages",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"NormPages": "Norm Pages", "country_short": ""}
                )
                overall_avg = mean_norm_pages
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
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
                fig_ctry.update_yaxes(categoryorder="array", categoryarray=y_order)
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # 2d) Optional: Vergleich Focal vs Other Countries Avg
                comp_df = pd.DataFrame({
                    "Group":   [focal_country, "Other countries average"],
                    "NormPages": [
                        country_avg.loc[country_avg["country"] == focal_country, "NormPages"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "NormPages"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="NormPages",
                    text="NormPages",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"NormPages": "Norm Pages", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other countries average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
        
            # Company Sector vs Other Sectors
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                sector_avg = (
                    df
                    .groupby("supersector")["norm_pages"]
                    .mean()
                    .reset_index(name="NormPages")
                )
                overall_avg = sector_avg["NormPages"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "NormPages"].iat[0]
        
                fig = px.histogram(
                    sector_avg,
                    x="NormPages",
                    nbins=20,
                    opacity=0.8,
                    labels={"NormPages": "Norm Pages"}
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
                    xaxis_title="Norm Pages",
                    yaxis_title="Sectors",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap
        
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                sector_avg = (
                    df
                    .groupby("supersector")["norm_pages"]
                    .mean()
                    .reset_index(name="NormPages")
                    .sort_values("NormPages", ascending=False)
                )
                sector_avg["sector_short"] = sector_avg["supersector"].apply(
                    lambda s: "<br>".join(textwrap.wrap(s, width=20))
                )
                y_order = sector_avg["sector_short"].tolist()[::-1]
                focal_label = "<br>".join(textwrap.wrap(focal_super, width=20))
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
        
                fig_s = px.bar(
                    sector_avg,
                    x="NormPages",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_label: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "NormPages": "Norm Pages"},
                    hover_data={"NormPages": ":.2f"}
                )
                avg_all = sector_avg["NormPages"].mean()
                fig_s.add_vline(
                    x=avg_all,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig_s = smart_layout(fig_s, len(sector_avg))
                fig_s.update_layout(showlegend=False)
                st.plotly_chart(fig_s, use_container_width=True)
        
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "NormPages"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "NormPages"].mean()
                comp_df = pd.DataFrame({
                    "Group":     [focal_super, "Other sectors avg"],
                    "NormPages": [focal_avg,    others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="NormPages",
                    text="NormPages",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"NormPages": "Norm Pages", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
        
            # Peers Gesamt-Histogramm
            elif plot_type == "Histogram":
                # Gesamt- und Focal-Norm-Pages berechnen
                mean_np  = benchmark_df["norm_pages"].mean()
                focal_np = df.loc[df["company"] == company, "norm_pages"].iat[0]
        
                fig = px.histogram(
                    plot_df,
                    x="norm_pages",
                    nbins=20,
                    opacity=0.8,
                    labels={"norm_pages": "Norm Pages", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
                fig.add_vline(
                    x=mean_np,
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
                    x=focal_np,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
                fig.update_layout(
                    xaxis_title="Norm Pages",
                    yaxis_title="Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
        
            # Peers Detail-Bar-Chart
            elif plot_type == "Bar Chart":
                peers_df    = plot_df.sort_values("norm_pages", ascending=False)
                mean_np     = benchmark_df["norm_pages"].mean()
                focal_np    = df.loc[df["company"] == company, "norm_pages"].iat[0]
        
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short            = peers_df["company_short"].tolist()[::-1]
        
                fig2 = px.bar(
                    peers_df,
                    x="norm_pages",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={"norm_pages": "Norm Pages", "company_short": "Company", "highlight_label": ""},
                    category_orders={"company_short": y_order_short}
                )
                fig2.add_vline(
                    x=mean_np,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig2 = smart_layout(fig2, len(peers_df))
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        
                comp_df = pd.DataFrame({
                    "Group":     ["Peer Average", company],
                    "NormPages": [mean_np, focal_np]
                })
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="NormPages",
                    text="NormPages",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"NormPages": "Norm Pages", "Group": ""}
                )
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_avg, use_container_width=True)


        elif view == "ESRS Topic Shares":
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

            legend_order = [
                'E1: Climate change',
                'E2: Pollution',
                'E3: Water',
                'E4: Biodiversity',
                'E5: Circular economy',
                'S1: Own workforce',
                'S2: Value chain workers',
                'S3: Affected communities',
                'S4: Consumers',
                'ESRS 2: Governance',
                'G1: Business conduct'
            ]
            
            # Farben für jedes Topic
            my_colors = {
                'E1: Climate change':        '#145214',
                'E2: Pollution':             '#2e7d32',
                'E3: Water':                 '#388e3c',
                'E4: Biodiversity':          '#81c784',
                'E5: Circular economy':      '#c8e6c9',
                'S1: Own workforce':         '#f57c00',
                'S2: Value chain workers':   '#ffb74d',
                'S3: Affected communities':  '#e65100',
                'S4: Consumers':             '#bf360c',
                'ESRS 2: Governance':        '#5A9BD5',
                'G1: Business conduct':      '#1F4E79'
            }
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
            plot_long['topic']       = plot_long['topic_internal'].str.replace('_pct','', regex=False)
            plot_long['topic_label'] = plot_long['topic'].map(topic_map)
        
            # — 3) Aggregation auf Firmen-Level —
            avg_df = (
                plot_long
                .groupby(['company','topic_label'])['pct']
                .mean()
                .reset_index()
            )
        
            # — 3b) Nur Firmen behalten, die irgendwo pct > 0 haben —
            companies_with_data = avg_df.loc[avg_df['pct'] > 0, 'company'].unique()
            avg_df = avg_df[avg_df['company'].isin(companies_with_data)].copy()
        
            
            if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                peer_companies = benchmark_df["company"].unique()
                if len(peer_companies) <= 1:
                    st.warning("Unfortunately, there are no data available for your company.")
                    # —— a) Cap-Labels definieren
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
            
                    # —— b) Alle rel_* → pct in df kopieren
                    for t in topic_map:
                        rc, pc = f"rel_{t}", f"{t}_pct"
                        if rc in df.columns:
                            df[pc] = df[rc]
                    pct_cols = [c for c in df.columns if c.endswith("_pct")]
            
                    # —— c) Langformat aus dem vollen df (nicht benchmark_df)
                    full_long = (
                        df
                        .assign(cap_group=df["Market_Cap_Cat"].apply(cap_label))
                        .melt(
                            id_vars=["company","cap_group"],
                            value_vars=pct_cols,
                            var_name="topic_internal",
                            value_name="pct"
                        )
                        .assign(
                            topic=lambda d: d["topic_internal"].str.replace("_pct","",regex=False),
                            topic_label=lambda d: d["topic"].map(topic_map)
                        )
                        .query("pct>0")
                    )
            
                    # —— d) Durchschnitt pro cap_group & topic_label (ohne Unknown)
                    cap_avg = (
                        full_long[full_long.cap_group != "Unknown"]
                        .groupby(["cap_group","topic_label"])["pct"]
                        .mean()
                        .reset_index()
                    )
            
                    # —— e) Werte der ausgewählten Firma extrahieren
                    sel_df = (
                        full_long[full_long.company == company]
                        .groupby("topic_label")["pct"]
                        .mean()
                        .reset_index()
                        .assign(cap_group=company)
                    )
            
                    # —— f) cap_avg + sel_df zusammenbringen
                    plot_df = pd.concat(
                        [
                            cap_avg.rename(columns={"cap_group":"Group"}),
                            sel_df.rename(columns={"cap_group":"Group"})
                        ],
                        ignore_index=True
                    )
            
                    # —— g) Eine gestapelte Bar für Small/Mid/Large und Deine Firma
                    fig = px.bar(
                        plot_df,
                        x="pct", y="Group",
                        orientation="h",
                        color="topic_label",
                        barmode="stack",
                        text=plot_df["pct"].apply(lambda v: f"{v*100:.0f}%" if v >= 0.05 else ""),
                        color_discrete_map=my_colors,
                        category_orders={
                            "Group":      ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "topic_label": legend_order
                        },
                        labels={"pct":"","Group":""}
                    )
                    # Werte-Labels nur bei ≥5 %, innen ausrichten
                    fig.update_traces(textposition="inside", insidetextanchor="middle")
                    fig.update_layout(
                        xaxis_tickformat=",.0%",
                        showlegend=True,
                        legend_title_text="ESRS Topic"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
                    # kein weiterer Code ausführen
                    st.stop()
        
            

            
            # — 5) Darstellung je nach Benchmark-Typ —
            elif mode == "Company Country vs Other Countries":
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
                    labels={'country_short':'','pct':''},
                    color_discrete_map=my_colors,
                    category_orders={'country_short':catA,'topic_label':legend_order}
                )
                figA.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                figA.update_layout(
                    barmode='stack',
                    xaxis_tickformat=',.0%',
                    legend=dict(title='ESRS Topic', itemsizing='constant')
                )
                st.plotly_chart(figA, use_container_width=True)
            
            
                # Chart B: Alle Länder (focal zuerst)
                orderB = [focal[:15]] + sorted(
                    set(country_topic['country'].str.slice(0,15)) - {focal[:15]}
                )
                country_topic['country_short'] = pd.Categorical(
                    country_topic['country'].str.slice(0,15),
                    categories=orderB, ordered=True
                )
            
                figB = px.bar(
                    country_topic,
                    x='pct', y='country_short', color='topic_label',
                    orientation='h',
                    text=country_topic['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'country_short':'','pct':''},
                    color_discrete_map=my_colors,
                    category_orders={'country_short':orderB,'topic_label':legend_order}
                )
            
                # 3) Namen IN die Bars platzieren und style
                figB.update_traces(
                    textposition='inside',      # oder 'auto' / 'outside'
                    insidetextanchor='start',   # linksbündig in jedem Segment
                    textfont=dict(size=12, color='white')
                )
            
                # 4) Höhe & Margin vergrößern
                figB.update_layout(
                    barmode='stack',
                    xaxis_tickformat=',.0%',
                    legend=dict(title='ESRS Topic', itemsizing='constant'),
                    height=1000,
                    margin=dict(l=150, r=20, t=20, b=20),
                    showlegend=False
                )
            
                # Hier Chart B korrekt rendern
                st.plotly_chart(figB, use_container_width=True)

            
            elif mode == "Company Sector vs Other Sectors":
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
            
                # Funktion zum Wrappen und Joinen mit <br>
                def wrap_label(s, width=20):
                    return "<br>".join(textwrap.wrap(s, width=width))
            
                # Chart A: Focal vs. All sectors
                combo = pd.concat([focal_df, total], ignore_index=True)
                combo['sector_wrapped'] = combo['supersector'].apply(lambda s: wrap_label(s))
                catA = [wrap_label(focal_s), wrap_label('All sectors')]
                combo['sector_wrapped'] = pd.Categorical(combo['sector_wrapped'],
                                                        categories=catA, ordered=True)
            
                figA = px.bar(
                    combo,
                    x='pct', y='sector_wrapped', color='topic_label',
                    orientation='h',
                    text=combo['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'sector_wrapped':'','pct':''},
                    color_discrete_map=my_colors,
                    category_orders={'sector_wrapped':catA,'topic_label':legend_order}
                )
                figA.update_traces(marker_line_color='black', marker_line_width=0.5, opacity=1)
                figA.update_layout(
                    barmode='stack',
                    xaxis_tickformat=',.0%',
                    legend=dict(title='ESRS Topic', itemsizing='constant')
                )
                st.plotly_chart(figA, use_container_width=True)
            
                # Chart B: Alle Supersektoren (focal zuerst)
                orderB_raw = [focal_s] + sorted(set(sector_topic['supersector']) - {focal_s})
                orderB = [wrap_label(s) for s in orderB_raw]
                sector_topic['sector_wrapped'] = sector_topic['supersector'].apply(lambda s: wrap_label(s))
                sector_topic['sector_wrapped'] = pd.Categorical(
                    sector_topic['sector_wrapped'],
                    categories=orderB, ordered=True
                )
            
                figB = px.bar(
                    sector_topic,
                    x='pct', y='sector_wrapped', color='topic_label',
                    orientation='h',
                    text=sector_topic['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                    labels={'sector_wrapped':'','pct':''},
                    color_discrete_map=my_colors,
                    category_orders={'sector_wrapped':orderB,'topic_label':legend_order}
                )
                # Namen IN die Bars platzieren
                figB.update_traces(
                    textposition='inside',
                    insidetextanchor='start',
                    textfont=dict(size=12, color='white')
                )
            
                # Höhe, Margin & Legende
                figB.update_layout(
                    barmode='stack',
                    xaxis_tickformat=',.0%',
                    height=1000,
                    margin=dict(l=150, r=20, t=20, b=20),
                    showlegend=False
                )
            
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


                
                if sel_df.empty:
                    st.warning("Unfortunately, there are no data available for your company.")
                
                    # — Chart A: Peer group average —
                    peer_avg = (
                        avg_df
                        .groupby('topic_label')['pct']
                        .mean()
                        .reset_index()
                        .assign(company_short="Peer group average")
                    )
                    fig_avg = px.bar(
                        peer_avg,
                        x='pct', y='company_short', color='topic_label',
                        orientation='h',
                        text=peer_avg['pct'].apply(lambda v: f"{v*100:.0f}%"),
                        labels={'company_short':'','pct':''},
                        color_discrete_map=my_colors,
                        category_orders={
                            'topic_label': legend_order,
                            'company_short': ["Peer group average"]
                        }
                    )
                    fig_avg.update_layout(
                        barmode='stack',
                        xaxis_tickformat=',.0%',
                        showlegend=True
                    )
                    st.plotly_chart(fig_avg, use_container_width=True)
                
                    # — Chart B: Werte aller Peer-Unternehmen —
                    df_peers = avg_df.copy()
                    df_peers['company_short'] = df_peers['company'].str.slice(0,15)
                    # nach Alphabet sortieren (oder nach Deinem Bedarf)
                    peer_order = sorted(df_peers['company_short'].unique())
                    df_peers['company_short'] = pd.Categorical(
                        df_peers['company_short'],
                        categories=peer_order,
                        ordered=True
                    )
                    fig_peers = px.bar(
                        df_peers,
                        x='pct', y='company_short', color='topic_label',
                        orientation='h',
                        text=df_peers['pct'].apply(lambda v: f"{v*100:.0f}%"
                                                   if v>=0.05 else ""),
                        labels={'company_short':'','pct':''},
                        color_discrete_map=my_colors,
                        category_orders={
                            'company_short': peer_order,
                            'topic_label': legend_order
                        }
                    )
                    fig_peers.update_traces(
                        textposition='inside',
                        insidetextanchor='start',
                        textfont=dict(size=12, color='white')
                    )
                    fig_peers.update_layout(
                        barmode='stack',
                        xaxis_tickformat=',.0%',
                        height=1000,
                        margin=dict(l=150, r=20, t=20, b=20),
                        showlegend=False
                    )
                    st.plotly_chart(fig_peers, use_container_width=True)
                
                else:
                    # === EXISTIERENDER CODE FÜR CHART A + CHART B ===
                
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
                        labels={'company_short':'','pct':''},
                        color_discrete_map=my_colors,
                        category_orders={
                            'company_short': [sel_short, 'Peer group average'[:15]],
                            'topic_label': legend_order
                        }
                    )
                    fig_benchmark.update_traces(
                        marker_line_color='black',
                        marker_line_width=0.5,
                        opacity=1
                    )
                    fig_benchmark.update_layout(
                        barmode='stack',
                        xaxis_tickformat=',.0%',
                        legend=dict(title='ESRS Topic', itemsizing='constant')
                    )
                    st.plotly_chart(fig_benchmark, use_container_width=True)
                
                    # Chart B: alle Firmen (selected ganz oben)
                    avg_df['company_short'] = avg_df['company'].str.slice(0,15)
                    sel_short = selected[:15]
                    others = sorted(set(avg_df['company_short']) - {sel_short})
                    avg_df['company_short'] = pd.Categorical(
                        avg_df['company_short'],
                        categories=[sel_short] + others,
                        ordered=True
                    )
                    fig_firmen = px.bar(
                        avg_df,
                        x='pct', y='company_short', color='topic_label',
                        orientation='h',
                        text=avg_df['pct'].apply(lambda v: f"{v*100:.0f}%" if v>=0.05 else ""),
                        labels={'company_short':'','pct':''},
                        color_discrete_map=my_colors,
                        category_orders={
                            'company_short': [sel_short] + others,
                            'topic_label': legend_order
                        }
                    )
                    fig_firmen.update_traces(
                        textposition='inside',
                        insidetextanchor='start',
                        textfont=dict(size=12, color='white')
                    )
                    fig_firmen.update_layout(
                        barmode='stack',
                        xaxis_tickformat=',.0%',
                        legend=dict(title='ESRS Topic', itemsizing='constant'),
                        height=1000,
                        margin=dict(l=150, r=20, t=20, b=20),
                        showlegend=False
                    )
                    st.plotly_chart(fig_firmen, use_container_width=True)
        
        elif view == "Numbers":
            st.subheader(f"Numbers per Norm Page ({benchmark_label})")
        
            # Peer- und Focal-Werte berechnen
            mean_nums   = benchmark_df["nums_500"].mean()
            focal_nums  = df.loc[df["company"] == company, "nums_500"].iat[0]

           
                 
            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["nums_500"]
                        .mean()
                        .reset_index(name="nums_500")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "nums_500": [focal_nums]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="nums_500", y="Group", orientation="h", text="nums_500",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"nums_500":"nums_500","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    fig.update_layout(xaxis_title="Numbers per Norm Page", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "nums_500": [mean_nums]
                    })
                    fig = px.bar(
                        comp_df,
                        x="nums_500",
                        y="Group",
                        orientation="h",
                        text="nums_500",
                        labels={"nums_500": "nums_500", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
        
            
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
        
                # 2) Länder‐Durchschnitt vorbereiten, Spalte in "Numbers" umbenennen
                country_avg = (
                    df
                    .groupby("country")["nums_500"]
                    .mean()
                    .reset_index(name="Numbers")
                )
        
                overall_avg = country_avg["Numbers"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Numbers"].iat[0]
        
                # 3) Histogramm aller Länder‐Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="Numbers",
                    nbins=20,
                    opacity=0.8,
                    labels={"Numbers": "Numbers", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 4) V-Lines für Länderavg
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
        
                # 5) Layout anpassen
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Numbers",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
    
    
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Durchschnitt pro Country und Sortierung (absteigend)
                country_avg = (
                    df
                    .groupby("country")["nums_500"]
                    .mean()
                    .reset_index(name="nums_500")
                    .sort_values("nums_500", ascending=False)
                )
            
                # 3) Labels kürzen (max. 15 Zeichen)
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Reihenfolge nach sort_values (absteigend), ohne zusätzliches Umkehren
                y_order = country_avg["country_short"].tolist()
            
                # 5) Highlight für Dein Land
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
            
                # 6) Bar-Chart erzeugen mit category_orders
                fig_ctry = px.bar(
                    country_avg,
                    x="nums_500",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country_short": y_order},
                    labels={"nums_500": "Numbers per Norm Page", "country_short": ""},
                )
            
                # 7) Linien & Styling
                overall_avg = df["nums_500"].mean()
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
            
                # 8) Dynamische Höhe & Schriftgröße
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
            
                # 9) Jetzt nochmal sicherstellen, dass Plotly die Reihenfolge aus y_order als Array nimmt
                fig_ctry.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Focal vs. Other Countries Average —
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "num_o_seit_500": [
                        country_avg.loc[country_avg["country"] == focal_country, "nums_500"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "nums_500"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="nums_500",
                    text="nums_500",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"nums_500": "Numbers per Norm Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={
                        "categoryorder": "array",
                        "categoryarray": [focal_country, "Other countries average"]
                    },
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Numbers pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["nums_500"]
                    .mean()
                    .reset_index(name="Numbers")
                )
                # 2) Histogramm
                fig2 = px.histogram(
                    sector_avg,
                    x="Numbers",
                    nbins=20,
                    opacity=0.8,
                    labels={"Numbers": "Numbers per Norm Page"}
                )
                fig2.update_traces(marker_color="#1f77b4")
            
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["Numbers"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Numbers"].iat[0]
            
                fig2.add_vline(
                    x=overall_avg, line_dash="dash", line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig2.add_vline(
                    x=focal_avg, line_dash="dash", line_color="red",
                    annotation_text=f"<b>{focal_super} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
            
                # 4) Layout anpassen
                fig2.update_layout(
                    showlegend=False,
                    xaxis_title="Numbers per Norm Page",
                    yaxis_title="Sectors",
                    bargap=0.1
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnitt pro Supersector und Sortierung (absteigend)
                super_avg = (
                    df
                    .groupby("supersector")["nums_500"]
                    .mean()
                    .reset_index(name="Numbers")
                    .sort_values("Numbers", ascending=False)
                )
            
                # 3) Labels umbrechen statt abschneiden
                def wrap_label(s, width=20):
                    return "<br>".join(textwrap.wrap(s, width=width))
            
                super_avg["super_short"] = super_avg["supersector"].apply(lambda s: wrap_label(s))
            
                # 4) Reihenfolge nach sort_values (absteigend)
                y_order = super_avg["super_short"].tolist()
            
                # 5) Highlight fürs eigene Supersector
                super_avg["highlight"] = np.where(
                    super_avg["supersector"] == focal_super,
                    wrap_label(focal_super),
                    "Other Sectors"
                )
            
                # 6) Bar-Chart erzeugen mit category_orders
                fig_s = px.bar(
                    super_avg,
                    x="Numbers",
                    y="super_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        wrap_label(focal_super): "red",
                        "Other Sectors": "#1f77b4"
                    },
                    category_orders={"super_short": y_order},
                    labels={"Numbers": "Numbers per Norm Page", "super_short": ""}
                )
            
                # 7) Linien & Styling
                overall_avg = super_avg["Numbers"].mean()
                fig_s.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
            
                # 8) Dynamische Höhe & Schriftgröße
                fig_s = smart_layout(fig_s, len(super_avg))
                fig_s.update_layout(showlegend=False)
            
                # 9) Reihenfolge final festlegen
                fig_s.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Focal vs. Other Countries Average —
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors average"],
                    "Numbers": [
                        super_avg.loc[super_avg["supersector"] == focal_super, "Numbers"].iat[0],
                        super_avg.loc[super_avg["supersector"] != focal_super, "Numbers"].mean()
                    ]
                })
                fig_s_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Numbers",
                    text="Numbers",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors average": "#1f77b4"},
                    labels={"Numbers": "Numbers per 500 words", "Group": ""}
                )
                fig_s_cmp.update_layout(
                    xaxis={
                        "categoryorder": "array",
                        "categoryarray": [focal_super, "Other sectors average"]
                    },
                    showlegend=False
                )
                fig_s_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_s_cmp, use_container_width=True)
            
            
            elif plot_type == "Histogram":
                # 1) Peer- und Focal-Werte berechnen
                mean_numbers  = benchmark_df["nums_500"].mean()
                focal_numbers = df.loc[df["company"] == company, "nums_500"].iat[0]
            
                # 2) Histogramm aller Peer-Unternehmen nach Numbers
                fig = px.histogram(
                    plot_df,
                    x="nums_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"nums_500": "Numbers per Norm Page", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 3) Linien für Peer Average und Focal Company
                fig.add_vline(
                    x=mean_numbers,
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
                    x=focal_numbers,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
            
                # 4) Achsentitel anpassen
                fig.update_layout(
                    xaxis_title="Numbers per Norm Page",
                    yaxis_title="Companies"
                )
            
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif plot_type == "Bar Chart":
                # 1) Sortieren nach Numbers
                peers_df     = plot_df.sort_values("nums_500", ascending=False)
                mean_numbers = benchmark_df["nums_500"].mean()
                focal_numbers = df.loc[df["company"] == company, "nums_500"].iat[0]
            
                # 2) Kurz-Namen für die Y-Achse
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short             = peers_df["company_short"].tolist()[::-1]
            
                # 3) Horizontalen Bar‐Chart erzeugen
                fig2 = px.bar(
                    peers_df,
                    x="nums_500",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "nums_500": "Numbers per Norm Page",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                )
            
                # 4) Peer-Average-Linie hinzufügen
                fig2.add_vline(
                    x=mean_numbers,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
            
                # 5) Styling & Automatische Höhe/Reihenfolge
                fig2 = smart_layout(fig2, len(peers_df))
                fig2.update_layout(showlegend=False)
            
                # 6) Chart ausgeben
                st.plotly_chart(fig2, use_container_width=True)
            
                # — Vertikaler Vergleich Peer Average vs. Focal Company —
                comp_df = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "nums_500": [mean_numbers, focal_numbers]
                })
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="nums_500",
                    text="nums_500",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"nums_500": "Numbers per Norm Page", "Group": ""}
                )
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_avg, use_container_width=True)

        elif view == "Tables":
            st.subheader(f"Tables per Norm Page ({benchmark_label})")
        
            # Peer- und Focal-Werte berechnen
            mean_tables = benchmark_df["tables_500"].mean()
            focal_tables = df.loc[df["company"] == company, "tables_500"].iat[0]

            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["tables_500"]
                        .mean()
                        .reset_index(name="Tables")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "Tables": [focal_tables]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="Tables", y="Group", orientation="h", text="Tables",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"Pages":"Pages","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    fig.update_layout(xaxis_title="Pages", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "Tables": [mean_tables]
                    })
                    fig = px.bar(
                        comp_df,
                        x="Tables",
                        y="Group",
                        orientation="h",
                        text="Tables",
                        labels={"Tables": "Tables", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
            
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder‐Durchschnitt vorbereiten, Spalte in "Tables" umbenennen
                country_avg = (
                    df
                    .groupby("country")["tables_500"]
                    .mean()
                    .reset_index(name="Tables")
                )
            
                overall_avg = country_avg["Tables"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "Tables"].iat[0]
            
                # 3) Histogramm aller Länder‐Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="Tables",
                    nbins=20,
                    opacity=0.8,
                    labels={"Tables": "Tables per Norm Page", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 4) V-Lines für Länderavg
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
            
                # 5) Layout anpassen
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Tables per Norm Page",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Durchschnitt pro Country und Sortierung (absteigend)
                country_avg = (
                    df
                    .groupby("country")["tables_500"]
                    .mean()
                    .reset_index(name="Tables")
                    .sort_values("Tables", ascending=False)
                )
            
                # 3) Labels kürzen (max. 15 Zeichen)
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Reihenfolge nach sort_values (absteigend)
                y_order = country_avg["country_short"].tolist()
            
                # 5) Highlight für Dein Land
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
            
                # 6) Bar-Chart erzeugen mit category_orders
                fig_ctry = px.bar(
                    country_avg,
                    x="Tables",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"Tables": "Tables per Norm Page", "country_short": ""},
                )
            
                # 7) Linien & Styling
                overall_avg = df["tables_500"].mean()
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
            
                # 8) Dynamische Höhe & Schriftgröße
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
            
                # 9) Reihenfolge final festlegen
                fig_ctry.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Focal vs. Other Countries Average —
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "Tables": [
                        country_avg.loc[country_avg["country"] == focal_country, "Tables"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "Tables"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Tables",
                    text="Tables",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"Tables": "Tables per Norm Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other countries average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Tabellen-Zahl pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["tables_500"]
                    .mean()
                    .reset_index(name="Tables")
                )
                # 2) Histogramm
                fig2 = px.histogram(
                    sector_avg,
                    x="Tables",
                    nbins=20,
                    opacity=0.8,
                    labels={"Tables": "Tables per Norm Page"}
                )
                fig2.update_traces(marker_color="#1f77b4")
            
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["Tables"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "Tables"].iat[0]
            
                fig2.add_vline(
                    x=overall_avg, line_dash="dash", line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black", annotation_font_size=16
                )
                fig2.add_vline(
                    x=focal_avg, line_dash="dash", line_color="red",
                    annotation_text=f"<b>{focal_super} Avg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red", annotation_font_size=16
                )
            
                # 4) Layout anpassen
                fig2.update_layout(
                    showlegend=False,
                    xaxis_title="Tables per Norm Page",
                    yaxis_title="Sectors",
                    bargap=0.1
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnittliche Tabellen-Zahl pro Supersector, absteigend sortiert
                super_avg = (
                    df
                    .groupby("supersector")["tables_500"]
                    .mean()
                    .reset_index(name="Tables")
                    .sort_values("Tables", ascending=False)
                )
            
                # Hilfsfunktion: wrappt lange Strings und verbindet mit <br>
                def wrap_label(s, width=20):
                    return "<br>".join(textwrap.wrap(s, width=width))
            
                # 3) Labels umbrechen statt abschneiden
                super_avg["super_short"] = super_avg["supersector"].apply(wrap_label)
            
                # 4) Reihenfolge nach sort_values (absteigend)
                y_order = super_avg["super_short"].tolist()
            
                # 5) Highlight fürs eigene Supersector, ebenfalls gewrappt
                wrapped_focal = wrap_label(focal_super)
                super_avg["highlight"] = np.where(
                    super_avg["super_short"] == wrapped_focal,
                    wrapped_focal,
                    "Other Sectors"
                )
            
                # 6) Horizontalen Bar‐Chart bauen
                fig_s = px.bar(
                    super_avg,
                    x="Tables",
                    y="super_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={wrapped_focal: "red", "Other Sectors": "#1f77b4"},
                    category_orders={"super_short": y_order},
                    labels={"Tables": "Tables per Norm Page", "super_short": ""}
                )
            
                # 7) Peer‐Average‐Linie
                overall_avg = super_avg["Tables"].mean()
                fig_s.add_vline(
                    x=overall_avg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
            
                # 8) Styling & automatische y-Invertierung
                fig_s = smart_layout(fig_s, len(super_avg))
                fig_s.update_layout(showlegend=False)
            
                # 9) Reihenfolge final festlegen
                fig_s.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Vertikaler Vergleich Supersector vs. Rest —
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors average"],
                    "Tables": [
                        super_avg.loc[super_avg["supersector"] == focal_super, "Tables"].iat[0],
                        super_avg.loc[super_avg["supersector"] != focal_super, "Tables"].mean()
                    ]
                })
                fig_s_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Tables",
                    text="Tables",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors average": "#1f77b4"},
                    labels={"Tables": "Tables per Norm Page", "Group": ""}
                )
                fig_s_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors average"]},
                    showlegend=False
                )
                fig_s_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_s_cmp, use_container_width=True)

            elif plot_type == "Histogram":
                # Einfaches Histogramm aller Unternehmen
                fig = px.histogram(
                    plot_df,
                    x="tables_500",
                    nbins=20,
                    labels={"tables_500": "Tables per Norm Page", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # Peer-Average
                mean_tables  = benchmark_df["tables_500"].mean()
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
                focal_tables = df.loc[df["company"] == company, "tables_500"].iat[0]
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
                    xaxis_title="Tables per Norm Page",
                    yaxis_title="Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif plot_type == "Bar Chart":
                # 1) Peer-Detail-Chart
                peers_df = plot_df.sort_values("tables_500", ascending=False)
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
            
                mean_tables  = benchmark_df["tables_500"].mean()
                focal_tables = df.loc[df["company"] == company, "tables_500"].iat[0]
            
                fig2 = px.bar(
                    peers_df,
                    x="tables_500",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "tables_500": "Tables per Norm Page",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
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
            
                # 5) Einheitliches Styling direkt hier anwenden
                fig2 = smart_layout(fig2, len(peers_df))
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
            
                # Vergleichs-Chart
                comp_df = pd.DataFrame({
                    "Group": [company, "Peer Average"],
                    "Tables": [focal_tables, mean_tables]
                })
            
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="Tables",
                    text="Tables",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"Tables": "Tables per Norm Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
            
                st.subheader("Peer vs. Company Tables per Norm Page")
                st.plotly_chart(fig_cmp, use_container_width=True)


        elif view == "Images":
            st.subheader(f"Image Size per Norm Page ({benchmark_label})")
        
            # Peer- und Focal-Werte berechnen
            mean_img = benchmark_df["imgsize"].mean()
            focal_img = df.loc[df["company"] == company, "imgsize"].iat[0]

            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["imgsize"]
                        .mean()
                        .reset_index(name="imgsize")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "Pages": [focal_pages]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="imgsize", y="Group", orientation="h", text="imgsize",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"imgsize":"imgsize","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
                    fig.update_layout(xaxis_title="Image per Page", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "imgsize": [mean_img]
                    })
                    fig = px.bar(
                        comp_df,
                        x="Pages",
                        y="Group",
                        orientation="h",
                        text="imgsize",
                        labels={"imgsize": "imgsize", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
        
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Länder-Durchschnitt vorbereiten, Spalte in "ImageArea" umbenennen
                country_avg = (
                    df
                    .groupby("country")["imgsize"]
                    .mean()
                    .reset_index(name="ImageArea")
                )
            
                overall_avg = country_avg["ImageArea"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "ImageArea"].iat[0]
            
                # 3) Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="ImageArea",
                    nbins=20,
                    opacity=0.8,
                    labels={"ImageArea": "Image per Page", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 4) V-Lines für Länderavg
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
                fig.add_vline(
                    x=focal_avg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
            
                # 5) Layout anpassen
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Image per Page",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Focal Country ermitteln
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
            
                # 2) Durchschnitt pro Country und Sortierung (absteigend)
                country_avg = (
                    df
                    .groupby("country")["imgsize"]
                    .mean()
                    .reset_index(name="ImageArea")
                    .sort_values("ImageArea", ascending=False)
                )
            
                # 3) Labels kürzen (max. 15 Zeichen)
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
            
                # 4) Reihenfolge nach sort_values (absteigend)
                y_order = country_avg["country_short"].tolist()
            
                # 5) Highlight für Dein Land
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
            
                # 6) Bar-Chart erzeugen mit category_orders
                fig_ctry = px.bar(
                    country_avg,
                    x="ImageArea",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={"country_short": y_order},
                    labels={"ImageArea": "Image per Page", "country_short": ""},
                )
            
                # 7) Linien & Styling
                overall_avg = df["imgsize"].mean()
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
            
                # 8) Dynamische Höhe & Schriftgröße
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
            
                # 9) Reihenfolge final festlegen
                fig_ctry.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_ctry, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Focal vs. Other Countries Average —
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "ImageArea": [
                        country_avg.loc[country_avg["country"] == focal_country, "ImageArea"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "ImageArea"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="ImageArea",
                    text="ImageArea",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries average": "#1f77b4"},
                    labels={"ImageArea": "Image per Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other countries average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.3f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            # 1) Histogramm aller Supersector-Durchschnitte
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Bildfläche pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["imgsize"]
                    .mean()
                    .reset_index(name="ImageArea")
                )
                # 2) Histogramm
                fig = px.histogram(
                    sector_avg,
                    x="ImageArea",
                    nbins=20,
                    opacity=0.8,
                    labels={"ImageArea": "Image per Page"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["ImageArea"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "ImageArea"].iat[0]
            
                fig.add_vline(
                    x=overall_avg, line_dash="dash", line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="top right",
                    annotation_font_color="black", annotation_font_size=16
                )
                fig.add_vline(
                    x=focal_avg, line_dash="dash", line_color="red",
                    annotation_text=f"<b>{focal_super} Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="red", annotation_font_size=16
                )
            
                # 4) Layout anpassen
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Image per Page",
                    yaxis_title="Sectors",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap
            
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnittliche Bildfläche pro Supersector, absteigend sortiert
                super_avg = (
                    df
                    .groupby("supersector")["imgsize"]
                    .mean()
                    .reset_index(name="ImageArea")
                    .sort_values("ImageArea", ascending=False)
                )
            
                # 3) Mehrzeilige Labels mit "\n" (wrap bei 20 Zeichen)
                super_avg["super_short"] = super_avg["supersector"].apply(
                    lambda s: "<br>".join(textwrap.wrap(s, width=20))
                )
            
                # 4) Reihenfolge nach sort_values (absteigend)
                y_order = super_avg["super_short"].tolist()
            
                # 5) Highlight fürs eigene Supersector
                focal_label = "\n".join(textwrap.wrap(focal_super, width=20))
                super_avg["highlight"] = np.where(
                    super_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
            
                # 6) Horizontalen Bar‐Chart bauen
                fig_s = px.bar(
                    super_avg,
                    x="ImageArea",
                    y="super_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_super: "red", "Other sectors": "#1f77b4"},
                    category_orders={"super_short": y_order},
                    labels={"super_short": "", "ImageArea": "Image per Page"},
                    hover_data={"ImageArea": ":.1f"}
                )
            
                # 7) Linie für den Durchschnitt aller Sektoren
                avg_all = super_avg["ImageArea"].mean()
                fig_s.add_vline(
                    x=avg_all,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
            
                # 8) Einheitliches Styling & Höhe/Schriftgröße + automatische y-Reverse
                fig_s = smart_layout(fig_s, len(super_avg))
                fig_s.update_layout(showlegend=False)
            
                # 9) Reihenfolge final festlegen
                fig_s.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
            
                # 10) Chart rendern
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Optional: Vergleichs‐Chart Supersector vs. Rest —
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors average"],
                    "ImageArea": [
                        super_avg.loc[super_avg["supersector"] == focal_super, "ImageArea"].iat[0],
                        super_avg.loc[super_avg["supersector"] != focal_super, "ImageArea"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="ImageArea",
                    text="ImageArea",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors average": "#1f77b4"},
                    labels={"ImageArea": "Image per Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors average"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.3f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)


            elif plot_type == "Histogram":
                # Peer- und Focal-Werte berechnen
                mean_images  = benchmark_df["imgsize"].mean()
                focal_images = df.loc[df["company"] == company, "imgsize"].iat[0]
            
                # Histogramm aller Peer-Unternehmen nach Bildfläche
                fig = px.histogram(
                    plot_df,
                    x="imgsize",
                    nbins=20,
                    labels={"imgsize": "Image per Page", "_group": "Group"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # Peer Average
                fig.add_vline(
                    x=mean_images,
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
                    x=focal_images,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom right",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
            
                fig.update_layout(
                    xaxis_title="Image per Page",
                    yaxis_title="Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif plot_type == "Bar Chart":
                # 1) Peer-Detail-Chart nach Bildfläche absteigend sortieren
                peers_df     = plot_df.sort_values("imgsize", ascending=False)
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short           = peers_df["company_short"].tolist()[::-1]
            
                mean_images  = benchmark_df["imgsize"].mean()
                focal_images = df.loc[df["company"] == company, "imgsize"].iat[0]
            
                fig2 = px.bar(
                    peers_df,
                    x="imgsize",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "imgsize": "Image per Page",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short}
                )
            
                # Peer Average Linie
                fig2.add_vline(
                    x=mean_images,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
            
                # Styling & automatische Höhe/Reihenfolge
                fig2 = smart_layout(fig2, len(peers_df))
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
            
                # Vertikaler Vergleich Peer vs. Focal Company
                comp_df = pd.DataFrame({
                    "Group": [company, "Peer Average"],
                    "ImageArea": [focal_images, mean_images]
                })
            
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="ImageArea",
                    text="ImageArea",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"ImageArea": "Image per Page", "Group": ""}
                )
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.3f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_avg, use_container_width=True)
        
    
        elif view == "Sentiment":
            
            if mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                focal_country = df.loc[df["company"] == company, "country"].iat[0]

                # 1) Länder-Durchschnitte berechnen
                country_avg = (
                    df
                    .groupby("country")[["words_pos_500", "words_neg_500"]]
                    .mean()
                    .reset_index()
                )

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
                    labels={"value": "", "variable": "Sentiment", "Group": ""}
                )
                # focal country links anzeigen
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other Countries"]},
                    showlegend=True,
                    legend_title_text=""
                )
                fig_cmp.update_traces(texttemplate="%{y:.2f}", textposition="outside")
                st.subheader("Pos./Neg. Words per Norm Page")
                st.plotly_chart(fig_cmp, use_container_width=True)
            
                            
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
                    labels={"words_pos_500": "Positive Words", "country": ""}
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

                # Texte in die Balken hinein platzieren
                fig_pos.update_traces(
                    textposition="inside",  # inside, outside etc.
                    insidetextanchor="middle",  # zentriert
                    textfont=dict(size=12, color="white")
                )
                
                # Layout anpassen (Höhe+Margin)
                fig_pos.update_layout(
                    showlegend=False,
                    xaxis_title="Positive Words",
                    height=600,
                    margin=dict(l=150, r=20, t=20, b=20)
                )
                
                st.subheader("Positive Words per Norm Page")
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
                    labels={"words_neg_500": "Negative Words", "country": ""}
                )
                overall_neg = country_avg["words_neg_500"].mean()
                fig_neg.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Countries Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Texte in die Balken hinein platzieren
                fig_neg.update_traces(
                    textposition="inside",  # inside, outside etc.
                    insidetextanchor="middle",  # zentriert
                    textfont=dict(size=12, color="white")
                )
                
                # Layout anpassen (Höhe+Margin)
                fig_neg.update_layout(
                    showlegend=False,
                    xaxis_title="Negative Words",
                    height=600,
                    margin=dict(l=150, r=20, t=20, b=20)
                )
                
                st.subheader("Negative Words per Norm Page")
                st.plotly_chart(fig_neg, use_container_width=True)
    
    
            elif mode == "Company Country vs Other Countries" and plot_type == "Histogram":
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
                    labels={"words_pos_500": "Positive Words"},
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
                    xaxis_title="Positive Words",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
                st.subheader("Positive Words per Norm Page")
                st.plotly_chart(fig_hist, use_container_width=True)
            
                # 4) Dasselbe noch für negative Wörter
                fig_hist2 = px.histogram(
                    country_avg,
                    x="words_neg_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_neg_500": "Negative Words"},
                )
                fig_hist2.update_traces(marker_color="#1f77b4")
                fig_hist2.add_vline(
                    x=focal_neg,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"<b>{focal_country} Avg Neg</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16,
                )
                fig_hist2.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    line_width=2,
                    annotation_text="<b>All Countries Avg Neg</b>",
                    annotation_position="top right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
                fig_hist2.update_layout(
                    showlegend=False,
                    xaxis_title="Negative Words",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
                st.subheader("Negative Words per Norm Page")
                st.plotly_chart(fig_hist2, use_container_width=True)

            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                # 1) Focal‐Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnitt pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")[["words_pos_500", "words_neg_500"]]
                    .mean()
                    .reset_index()
                )
            
                # Hilfsfunktion: wrappt lange Labels und trennt mit <br>
                def wrap_label(s, width=20):
                    return "<br>".join(textwrap.wrap(s, width=width))
            
                # 3) „Wrapped“ Sektor‐Bezeichnung anlegen
                wrapped_focal = wrap_label(focal_super)
                sector_avg["sector_wrapped"] = sector_avg["supersector"].apply(wrap_label)
            
                # 4a) Kompaktvergleich: focal vs. others
                focal_pos = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_pos_500"].iat[0]
                focal_neg = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_neg_500"].iat[0]
                other_pos = sector_avg.loc[sector_avg["supersector"] != focal_super, "words_pos_500"].mean()
                other_neg = sector_avg.loc[sector_avg["supersector"] != focal_super, "words_neg_500"].mean()
            
                comp_df = pd.DataFrame({
                    "Group":    [wrapped_focal, "Other Sectors"],
                    "Positive": [focal_pos,   other_pos],
                    "Negative": [focal_neg,   other_neg]
                })
            
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y=["Positive", "Negative"],
                    barmode="group",
                    color_discrete_sequence=["#E10600", "#1f77b4"],
                    labels={"value": "", "variable": "Sentiment", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [wrapped_focal, "Other Sectors"]},
                    showlegend=True,
                    legend_title_text=""
                )
                fig_cmp.update_traces(texttemplate="%{y:.2f}", textposition="outside")
                st.subheader("Pos./Neg. Words per Norm Page")
                st.plotly_chart(fig_cmp, use_container_width=True)
            
                # 4b) Positive Words per Sector
                pos_sec = sector_avg.sort_values("words_pos_500", ascending=False).copy()
                pos_sec["highlight"] = np.where(
                    pos_sec["supersector"] == focal_super,
                    wrapped_focal,
                    "Other Sectors"
                )
                y_order_pos = pos_sec["sector_wrapped"].tolist()
            
                fig_pos = px.bar(
                    pos_sec,
                    x="words_pos_500",
                    y="sector_wrapped",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={wrapped_focal: "red", "Other Sectors": "#1f77b4"},
                    category_orders={"sector_wrapped": y_order_pos},
                    labels={"words_pos_500": "Positive Words", "sector_wrapped": ""}
                )
                overall_pos = sector_avg["words_pos_500"].mean()
                fig_pos.add_vline(
                    x=overall_pos,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig_pos.update_traces(
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(size=12, color="white")
                )
                fig_pos.update_layout(
                    showlegend=False,
                    xaxis_title="Positive Words",
                    height=600,
                    margin=dict(l=150, r=20, t=20, b=20)
                )
                st.subheader("Positive Words per Norm Page")
                st.plotly_chart(fig_pos, use_container_width=True)
            
                # 4c) Negative Words per Sector
                neg_sec = sector_avg.sort_values("words_neg_500", ascending=False).copy()
                neg_sec["highlight"] = np.where(
                    neg_sec["supersector"] == focal_super,
                    wrapped_focal,
                    "Other Sectors"
                )
                y_order_neg = neg_sec["sector_wrapped"].tolist()
            
                fig_neg = px.bar(
                    neg_sec,
                    x="words_neg_500",
                    y="sector_wrapped",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={wrapped_focal: "red", "Other Sectors": "#1f77b4"},
                    category_orders={"sector_wrapped": y_order_neg},
                    labels={"words_neg_500": "Negative Words", "sector_wrapped": ""}
                )
                overall_neg = sector_avg["words_neg_500"].mean()
                fig_neg.add_vline(
                    x=overall_neg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                fig_neg.update_traces(
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(size=12, color="white")
                )
                fig_neg.update_layout(
                    showlegend=False,
                    xaxis_title="Negative Words",
                    height=600,
                    margin=dict(l=150, r=20, t=20, b=20)
                )
                st.subheader("Negative Words per Norm Page")
                st.plotly_chart(fig_neg, use_container_width=True)
            
            
            # Histogram: Verteilung der Supersector-Durchschnitte
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
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
                    labels={"words_pos_500": "Positive Words"}
                )
                fig_h1.update_traces(marker_color="#1f77b4")
                overall_pos = sector_avg["words_pos_500"].mean()
                focal_pos   = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_pos_500"].iat[0]
                fig_h1.add_vline(x=overall_pos, line_dash="dash", line_color="black",
                                 annotation_text="<b>All Sectors Avg</b>", annotation_position="top right", annotation_font_color="black", annotation_font_size=16)
                fig_h1.add_vline(x=focal_pos,   line_dash="dash", line_color="red",
                                 annotation_text=f"<b>{focal_super} Avg</b>", annotation_position="bottom left", annotation_font_color="red", annotation_font_size=16)
                fig_h1.update_layout(showlegend=False, xaxis_title="Positive Words", yaxis_title="Sectors")
                st.subheader("Pos. Words per Norm Page")
                st.plotly_chart(fig_h1, use_container_width=True)
            
                # Negative Words Distribution
                fig_h2 = px.histogram(
                    sector_avg,
                    x="words_neg_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"words_neg_500": "Negative Words"}
                )
                fig_h2.update_traces(marker_color="#1f77b4")
                overall_neg = sector_avg["words_neg_500"].mean()
                focal_neg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "words_neg_500"].iat[0]
                fig_h2.add_vline(x=overall_neg, line_dash="dash", line_color="black",
                                 annotation_text="<b>All Sectors Avg</b>", annotation_position="top right", annotation_font_color="black", annotation_font_size=16)
                fig_h2.add_vline(x=focal_neg,   line_dash="dash", line_color="red",
                                 annotation_text=f"<b>{focal_super} Avg</b>", annotation_position="bottom left", annotation_font_color="red", annotation_font_size=16)
                fig_h2.update_layout(showlegend=False, xaxis_title="Negative Words", yaxis_title="Sectors")
                st.subheader("Neg. Words per Norm Page")
                st.plotly_chart(fig_h2, use_container_width=True)
                      
            
            elif plot_type == "Bar Chart":
                # — 1) Peer vs. Company Sentiment (kompakter Vergleich) —
                st.subheader("Pos./Neg. Words per Norm Page")
            
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
                    labels={"value": "", "company": ""}
                )
                
                # Jetzt pro Trace (0 = Positive, 1 = Negative) die Farben für Peer vs. Company setzen
                # Trace 0 = "Positive": [Peer, Company]
                fig_cmp.data[0].marker.color = ["#E10600", "#E10600"]
                # Trace 1 = "Negative": [Peer, Company]
                fig_cmp.data[1].marker.color = ["#1f77b4", "#1f77b4"]
                fig_cmp.update_traces(texttemplate="%{y:.2f}", textposition="outside")
                st.plotly_chart(fig_cmp, use_container_width=True)
            
            
                # — 2) Positive Words by Company —
                pos_df = benchmark_df.sort_values("words_pos_500", ascending=False).copy()
                pos_df["highlight"] = np.where(pos_df["company"] == company, company, "Peers")
                pos_df["company_short"] = pos_df["company"].str.slice(0, 15)
                fig_pos = px.bar(
                    pos_df,
                    x="words_pos_500",
                    y="company_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={company: "#E10600", "Peers": "#1f77b4"},  # Focal=Rot, Peers=Hellblau
                    category_orders={"company_short": pos_df["company_short"].tolist()},
                    labels={"words_pos_500": "Positive Words", "company_short": ""}
                )
                fig_pos.add_vline(
                    x=mean_pos,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Texte in die Balken hinein platzieren
                fig_pos.update_traces(
                    textposition="inside",  # inside, outside etc.
                    insidetextanchor="middle",  # zentriert
                    textfont=dict(size=12, color="white")
                )
                
                # Layout anpassen (Höhe+Margin)
                fig_pos.update_layout(
                    showlegend=False,
                    xaxis_title="Positive Words",
                    height=600,
                    margin=dict(l=150, r=20, t=20, b=20)
                )
                
                st.subheader("Positive Words per Norm Page")
                st.plotly_chart(fig_pos, use_container_width=True)
            
            
                # — 3) Negative Words by Company —
                neg_df = benchmark_df.sort_values("words_neg_500", ascending=False).copy()
                neg_df["highlight"] = np.where(neg_df["company"] == company, company, "Peers")
                neg_df["company_short"] = neg_df["company"].str.slice(0, 15)
                fig_neg = px.bar(
                    neg_df,
                    x="words_neg_500",
                    y="company_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={company: "#E10600", "Peers": "#1f77b4"},  # Focal=Rot, Peers=Dunkelblau
                    category_orders={"company_short": neg_df["company_short"].tolist()},
                    labels={"words_neg_500": "Negative Words", "company_short": ""}
                )
                fig_neg.add_vline(
                    x=mean_neg,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
                # Texte in die Balken hinein platzieren
                fig_neg.update_traces(
                    textposition="inside",  # inside, outside etc.
                    insidetextanchor="middle",  # zentriert
                    textfont=dict(size=12, color="white")
                )
                
                # Layout anpassen (Höhe+Margin)
                fig_neg.update_layout(
                    showlegend=False,
                    xaxis_title="Negative Words",
                    height=600,
                    margin=dict(l=150, r=20, t=20, b=20)
                )
                
                st.subheader("Negative Words per Norm Page")
                st.plotly_chart(fig_neg, use_container_width=True)

    
            elif plot_type == "Histogram":
                
                mean_pos  = benchmark_df["words_pos_500"].mean()
                focal_pos = df.loc[df["company"] == company, "words_pos_500"].iat[0]
                mean_neg  = benchmark_df["words_neg_500"].mean()
                focal_neg = df.loc[df["company"] == company, "words_neg_500"].iat[0]
                                
                st.subheader("Pos. Words per Norm Page")
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
                fig_h1.update_layout(xaxis_title="Positive Words", yaxis_title="Companies")
                st.plotly_chart(fig_h1, use_container_width=True)
                
                st.subheader("Neg. Words per Norm Page")
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
                fig_h2.update_layout(xaxis_title="Negative Words", yaxis_title="Companies")
                st.plotly_chart(fig_h2, use_container_width=True)
    
        elif view == "Standardized Language":
            st.subheader(f"Standardized Language ({benchmark_label})")
            
            # Mittelwert und Focal-Wert ermitteln
            mean_boiler   = benchmark_df["boilergrams_500"].mean()
            focal_boiler  = df.loc[df["company"] == company, "boilergrams_500"].iat[0]

            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["boilergrams_500"]
                        .mean()
                        .reset_index(name="boilergrams_500")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "boilergrams_500": [focal_boiler]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="boilergrams_500", y="Group", orientation="h", text="boilergrams_500",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"boilergrams_500":"boilergrams_500","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    fig.update_layout(xaxis_title="Tetragrams per Norm Page", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "Pages": [mean_pages]
                    })
                    fig = px.bar(
                        comp_df,
                        x="Pages",
                        y="Group",
                        orientation="h",
                        text="boilergrams_500",
                        labels={"boilergrams_500": "boilergrams_500", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
        
            
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Länder-Durchschnitt vorbereiten
                country_avg = (
                    df
                    .groupby("country")["boilergrams_500"]
                    .mean()
                    .reset_index(name="StdLang")
                )
        
                overall_avg = country_avg["StdLang"].mean()
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                focal_avg = country_avg.loc[country_avg["country"] == focal_country, "StdLang"].iat[0]
        
                # 2) Histogramm
                fig = px.histogram(
                    country_avg,
                    x="StdLang",
                    nbins=20,
                    opacity=0.8,
                    labels={"StdLang": "Tetragrams per Norm Page"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) Vertical lines
                fig.add_vline(
                    x=overall_avg, line_dash="dash", line_color="black", line_width=2,
                    annotation_text="<b>All Countries Avg</b>", annotation_position="top right",
                    annotation_font_color="black", annotation_font_size=16
                )
                fig.add_vline(
                    x=focal_avg, line_dash="dash", line_color="red", line_width=2,
                    annotation_text=f"<b>{focal_country} Avg</b>", annotation_position="bottom left",
                    annotation_font_color="red", annotation_font_size=16
                )
        
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Tetragrams per Norm Page",
                    yaxis_title="Countries",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                focal_country = df.loc[df["company"] == company, "country"].iat[0]
                # 1) Länder-Durchschnitt sortieren
                country_avg = (
                    df
                    .groupby("country")["boilergrams_500"]
                    .mean()
                    .reset_index(name="StdLang")
                    .sort_values("StdLang", ascending=False)
                )
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                # 2) Bar Chart
                fig_ctry = px.bar(
                    country_avg,
                    x="StdLang",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_country: "red", "Other Countries": "#1f77b4"},
                    category_orders={"country_short": y_order},
                    labels={"country_short": "", "StdLang": "Tetragrams per Norm Page"}
                )
        
                # 3) Peer-Average-Linie
                overall_avg = df["boilergrams_500"].mean()
                fig_ctry.add_vline(
                    x=overall_avg, line_dash="dash", line_color="black", line_width=2,
                    annotation_text="<b>Peer Average</b>", annotation_position="bottom right",
                    annotation_font_color="black", annotation_font_size=16
                )
        
                # 4) Styling & Reihenfolge
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
                fig_ctry.update_yaxes(categoryorder="array", categoryarray=y_order)
        
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # — Vergleichs-Chart —
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries avg"],
                    "StdLang": [
                        country_avg.loc[country_avg["country"] == focal_country, "StdLang"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "StdLang"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="StdLang",
                    text="StdLang",
                    color="Group",
                    color_discrete_map={focal_country: "red", "Other countries avg": "#1f77b4"},
                    labels={"StdLang": "Tetragrams per Norm Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_country, "Other countries avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
            
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche Standardized Language pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["boilergrams_500"]
                    .mean()
                    .reset_index(name="StdLang")
                )
                # 2) Histogramm
                fig = px.histogram(
                    sector_avg,
                    x="StdLang",
                    nbins=20,
                    opacity=0.8,
                    labels={"StdLang": "Tetragrams per Norm Page"}
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["StdLang"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "StdLang"].iat[0]
        
                fig.add_vline(
                    x=overall_avg, line_dash="dash", line_color="black",
                    annotation_text="<b>All Sectors Avg</b>", annotation_position="top right",
                    annotation_font_color="black", annotation_font_size=16
                )
                fig.add_vline(
                    x=focal_avg, line_dash="dash", line_color="red",
                    annotation_text=f"<b>{focal_super} Avg</b>", annotation_position="bottom left",
                    annotation_font_color="red", annotation_font_size=16
                )
        
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Tetragrams per Norm Page",
                    yaxis_title="Sectors",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap
        
                # 1) Durchschnitt pro Supersector, absteigend sortiert
                sector_avg = (
                    df
                    .groupby("supersector")["boilergrams_500"]
                    .mean()
                    .reset_index(name="StdLang")
                    .sort_values("StdLang", ascending=False)
                )
        
                # 2) Labels umbrechen (max. 20 Zeichen)
                sector_avg["sector_short"] = sector_avg["supersector"].apply(
                    lambda s: "<br>".join(textwrap.wrap(s, width=20))
                )
        
                # 3) Reihenfolge umdrehen, damit stärkster Wert oben
                y_order = sector_avg["sector_short"].tolist()[::-1]
        
                # 4) Highlight fürs eigene Supersector
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_label = "<br>".join(textwrap.wrap(focal_super, width=20))
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
        
                # 5) Horizontalen Bar‐Chart bauen
                fig_s = px.bar(
                    sector_avg,
                    x="StdLang",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_label: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"sector_short": "", "StdLang": "Tetragrams per Norm Page"}
                )
        
                # 6) Linie für den Durchschnitt aller Sektoren
                avg_all = sector_avg["StdLang"].mean()
                fig_s.add_vline(
                    x=avg_all, line_dash="dash", line_color="black",
                    annotation_text="<b>All Sectors Avg</b>", annotation_position="bottom right",
                    annotation_font_color="black", annotation_font_size=16
                )
        
                # 7) Styling & automatische y-Achse invertieren
                fig_s = smart_layout(fig_s, len(sector_avg))
                fig_s.update_layout(showlegend=False)
        
                # 8) Chart rendern
                st.plotly_chart(fig_s, use_container_width=True)
        
                # — Optional: Vergleichs‐Chart Supersector vs. Rest —
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "StdLang"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "StdLang"].mean()
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "StdLang": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="StdLang",
                    text="StdLang",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"StdLang": "Tetragrams per Norm Page", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)

            elif plot_type == "Histogram":
                # Einfach alle Companies im Benchmark_df
                fig = px.histogram(
                    benchmark_df,
                    x="boilergrams_500",
                    nbins=20,
                    opacity=0.8,
                    labels={"boilergrams_500":"Standardized Language","":""}
                )
                fig.update_traces(marker_color="#1f77b4")
                # Peer-Average (schwarz) und Focal (rot)
                fig.add_vline(x=mean_boiler,  line_dash="dash", line_color="black",
                             annotation_text="<b>Peer Avg</b>", annotation_position="top right", annotation_font_color="black", annotation_font_size=16)
                fig.add_vline(x=focal_boiler, line_dash="dash", line_color="red",
                             annotation_text=f"<b>{company}</b>", annotation_position="bottom right",
                             annotation_font_color="red", annotation_font_size=16)
                fig.update_layout(showlegend=False, xaxis_title="Standardized Language", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
        
            # — **Alle Peers**: Bar Chart über boiler_500 —
            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart aller Peer-Unternehmen, horizontale Balken nach Wert absteigend sortieren
                peers_df = plot_df.sort_values("boilergrams_500", ascending=False)
                mean_boiler = benchmark_df["boilergrams_500"].mean()
            
                # 2) Kurz-Namen für die Y-Achse, damit sie nicht zu lang werden
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
            
                # 3) Horizontales Balkendiagramm erstellen
                fig2 = px.bar(
                    peers_df,
                    x="boilergrams_500",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "boiler_500": "Tetragrams per Norm Page",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                )

                fig2.update_layout(showlegend=False)
            
                # 4) Peer-Average-Linie hinzufügen
                fig2.add_vline(
                    x=mean_boiler,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 5) Einheitliches Styling direkt hier anwenden
                fig2 = smart_layout(fig2, len(peers_df))
            
                # 6) Chart ausgeben
                st.plotly_chart(fig2, use_container_width=True)
            
                # — Vertikaler Vergleich Peer Average vs. Focal Company —
                avg_boiler = mean_boiler
                comp_df = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "boilergrams_500": [avg_boiler, focal_boiler]
                })
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="boilergrams_500",
                    text="boilergrams_500",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"boilergrams_500": "Tetragrams per Norm Page", "Group": ""}
                )
                # rote Firma links anzeigen
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_avg, use_container_width=True)

        
        elif view == "Language Complexity":
            st.subheader(f"Language Complexity ({benchmark_label})")
        
            # 1) Peer-Average und Focal-Wert holen
            mean_fog  = benchmark_df["fog"].mean()
            focal_fog = df.loc[df["company"] == company, "fog"].iat[0]

            # --- 1) Fallback-Prüfung: gibt es überhaupt echte Peers? ---
            peer_companies = benchmark_df["company"].unique()
            if len(peer_companies) <= 1 and peer_group != "Choose specific peers":
                st.warning("Unfortunately, there are no data available for your company.")
        
                # --- 1a) Falls Market Cap Peers: Vergleich der drei Gruppen ---
                if mode == "Company vs. Peer Group" and peer_group == "Market Cap Peers":
                    # a) Label-Funktion
                    def cap_label(terc):
                        return ("Small-Cap" if 1 <= terc <= 3 else
                                "Mid-Cap"   if 4 <= terc <= 7 else
                                "Large-Cap" if 8 <= terc <= 10 else
                                "Unknown")
                
                    # b) Cap-Gruppe in df anlegen
                    df["cap_group"] = df["Market_Cap_Cat"].apply(cap_label)
                
                    # c) Durchschnitt pro cap_group berechnen
                    cap_avg = (
                        df
                        .groupby("cap_group")["fog"]
                        .mean()
                        .reset_index(name="fog")
                        .rename(columns={"cap_group": "Group"})
                    )
                
                    # d) Unknown rausfiltern
                    cap_avg = cap_avg[cap_avg["Group"] != "Unknown"]
                
                    # e) ausgewählte Firma anhängen
                    sel_row = pd.DataFrame({
                        "Group": [company],
                        "fog": [focal_fog]
                    })
                    plot_df = pd.concat([cap_avg, sel_row], ignore_index=True)
                
                    # f) Highlight-Spalte
                    plot_df["highlight"] = np.where(
                        plot_df["Group"] == company,
                        "Your Company",
                        "Market Cap Group"
                    )
                
                    # g) Plot
                    fig = px.bar(
                        plot_df,
                        x="fog", y="Group", orientation="h", text="fog",
                        color="highlight",
                        category_orders={
                            "Group":     ["Small-Cap", "Mid-Cap", "Large-Cap", company],
                            "highlight": ["Market Cap Group", "Your Company"]
                        },
                        color_discrete_map={
                            "Market Cap Group": "#1f77b4",
                            "Your Company":      "red"
                        },
                        labels={"Pages":"Pages","Group":""}
                    )
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    fig.update_layout(xaxis_title="Fog-Index Average", margin=dict(l=120), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        
                # --- 1b) Für alle anderen Peer-Gruppen: nur Peer Average anzeigen ---
                else:
                    comp_df = pd.DataFrame({
                        "Group": ["Peer Average"],
                        "Pages": [mean_pages]
                    })
                    fig = px.bar(
                        comp_df,
                        x="fog",
                        y="Group",
                        orientation="h",
                        text="Pages",
                        labels={"fog": "fog", "Group": ""}
                    )
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)
        
                # kein weiterer Code ausführen
                st.stop()
        
            # --- 2) Normal-Fall: Es gibt echte Peers, jetzt der volle bestehende Plot-Code ---
    
    
            if mode == "Company Country vs Other Countries" and plot_type == "Histogram":
                # 1) Länder-Durchschnitt der Fog-Avg vorbereiten
                country_avg = (
                    df
                    .groupby("country")["fog"]
                    .mean()
                    .reset_index(name="FogAvg")
                )
                overall_avg = country_avg["FogAvg"].mean()
                focal_avg   = country_avg.loc[country_avg["country"] == focal_country, "FogAvg"].iat[0]
        
                # 2) Histogramm aller Länder-Durchschnitte
                fig = px.histogram(
                    country_avg,
                    x="FogAvg",
                    nbins=20,
                    opacity=0.8,
                    labels={"FogAvg": "FOG Average"},
                )
                fig.update_traces(marker_color="#1f77b4")
        
                # 3) V-Lines für Gesamt- und Focal-Country Avg
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
        
                # 4) Layout-Anpassungen
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="FOG Average",
                    yaxis_title="Countries",
                    bargap=0.1,
                )
                st.plotly_chart(fig, use_container_width=True)
        
            elif mode == "Company Country vs Other Countries" and plot_type == "Bar Chart":
                # 1) Durchschnitt pro Country (fog_avg) und Sortierung
                country_avg = (
                    df
                    .groupby("country")["fog"]
                    .mean()
                    .reset_index(name="FogAvg")
                    .sort_values("FogAvg", ascending=False)
                )
                # 2) Label-Kürzung
                country_avg["country_short"] = country_avg["country"].str.slice(0, 15)
                y_order = country_avg["country_short"].tolist()
        
                # 3) Highlight für Focal Country
                country_avg["highlight"] = np.where(
                    country_avg["country"] == focal_country,
                    country_avg["country_short"],
                    "Other Countries"
                )
        
                # 4) Bar-Chart erstellen
                fig_ctry = px.bar(
                    country_avg,
                    x="FogAvg",
                    y="country_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={
                        focal_country: "red",
                        "Other Countries": "#1f77b4"
                    },
                    category_orders={
                        "country_short": y_order
                    },
                    labels={"FogAvg": "FOG Average", "country_short": ""}
                )
                # 5) Peer Average Linie
                overall_avg = df["fog"].mean()
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
                # 6) Layout & Reihenfolge
                fig_ctry = smart_layout(fig_ctry, len(country_avg))
                fig_ctry.update_layout(showlegend=False)
                fig_ctry.update_yaxes(
                    categoryorder="array",
                    categoryarray=y_order
                )
                st.plotly_chart(fig_ctry, use_container_width=True)
        
                # Optionaler Vergleich: Focal vs. Other Countries Avg
                comp_df = pd.DataFrame({
                    "Group": [focal_country, "Other countries average"],
                    "FogAvg": [
                        country_avg.loc[country_avg["country"] == focal_country, "FogAvg"].iat[0],
                        country_avg.loc[country_avg["country"] != focal_country, "FogAvg"].mean()
                    ]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="FogAvg",
                    text="FogAvg",
                    color="Group",
                    color_discrete_map={
                        focal_country: "red",
                        "Other countries average": "#1f77b4"
                    },
                    labels={"FogAvg": "FOG Average", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={
                        "categoryorder": "array",
                        "categoryarray": [focal_country, "Other countries average"]
                    },
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
            

            # —————————————————————————————————————————————————————————————————————————————————
            # Between Sector Comparison für Fog-Index
            # —————————————————————————————————————————————————————————————————————————————————
        
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Histogram":
                # 1) Durchschnittliche FOG-Werte pro Supersector
                sector_avg = (
                    df
                    .groupby("supersector")["fog"]
                    .mean()
                    .reset_index(name="FogAvg")
                )
                # 2) Plot
                fig = px.histogram(
                    sector_avg,
                    x="FogAvg",
                    nbins=20,
                    opacity=0.8,
                    labels={"FogAvg": "FOG Average"}
                )
                fig.update_traces(marker_color="#1f77b4")
            
                # 3) Linien für All vs. Focal Supersector
                overall_avg = sector_avg["FogAvg"].mean()
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
                focal_avg   = sector_avg.loc[sector_avg["supersector"] == focal_super, "FogAvg"].iat[0]
            
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
                    xaxis_title="FOG Average",
                    yaxis_title="Sectors",
                    bargap=0.1
                )
                st.plotly_chart(fig, use_container_width=True)
            
            
            elif mode == "Company Sector vs Other Sectors" and plot_type == "Bar Chart":
                import textwrap
            
                # 1) Focal Supersector ermitteln
                focal_super = df.loc[df["company"] == company, "supersector"].iat[0]
            
                # 2) Durchschnittliche FOG-Werte pro Supersector, absteigend sortiert
                sector_avg = (
                    df
                    .groupby("supersector")["fog"]
                    .mean()
                    .reset_index(name="FogAvg")
                    .sort_values("FogAvg", ascending=False)
                )
            
                # 3) Mehrzeilige Labels mit "<br>" (wrap bei 20 Zeichen)
                sector_avg["sector_short"] = sector_avg["supersector"].apply(
                    lambda s: "<br>".join(textwrap.wrap(s, width=20))
                )
            
                # 4) Reihenfolge für category_orders: niedrigste FOG-Werte zuerst
                y_order = sector_avg["sector_short"].tolist()[::-1]
            
                # 5) Highlight fürs eigene Supersector
                focal_label = "<br>".join(textwrap.wrap(focal_super, width=20))
                sector_avg["highlight"] = np.where(
                    sector_avg["supersector"] == focal_super,
                    focal_label,
                    "Other sectors"
                )
            
                # 6) Horizontaler Bar-Chart
                fig_s = px.bar(
                    sector_avg,
                    x="FogAvg",
                    y="sector_short",
                    orientation="h",
                    color="highlight",
                    color_discrete_map={focal_label: "red", "Other sectors": "#1f77b4"},
                    category_orders={"sector_short": y_order},
                    labels={"FogAvg": "FOG Average", "sector_short": ""},
                    hover_data={"FogAvg": ":.2f"}
                )
            
                # 7) Linie für den Durchschnitt aller Sektoren
                avg_all = sector_avg["FogAvg"].mean()
                fig_s.add_vline(
                    x=avg_all,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>All Sectors Avg</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16
                )
            
                # 8) Styling & Layout
                fig_s = smart_layout(fig_s, len(sector_avg))
                fig_s.update_layout(showlegend=False)
                st.plotly_chart(fig_s, use_container_width=True)
            
                # — Optional: Vergleichs-Chart Supersector vs Rest —
                focal_avg = sector_avg.loc[sector_avg["supersector"] == focal_super, "FogAvg"].iat[0]
                others_avg = sector_avg.loc[sector_avg["supersector"] != focal_super, "FogAvg"].mean()
                comp_df = pd.DataFrame({
                    "Group": [focal_super, "Other sectors avg"],
                    "FogAvg": [focal_avg, others_avg]
                })
                fig_cmp = px.bar(
                    comp_df,
                    x="Group",
                    y="FogAvg",
                    text="FogAvg",
                    color="Group",
                    color_discrete_map={focal_super: "red", "Other sectors avg": "#1f77b4"},
                    labels={"FogAvg": "FOG Average", "Group": ""}
                )
                fig_cmp.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [focal_super, "Other sectors avg"]},
                    showlegend=False
                )
                fig_cmp.update_traces(texttemplate="%{text:.2f}", textposition="outside", width=0.5)
                st.plotly_chart(fig_cmp, use_container_width=True)
                    
                    
            elif plot_type == "Histogram":
                # Histogramm der FOG-Werte aller Unternehmen
                fig = px.histogram(
                    plot_df,
                    x="fog",
                    nbins=20,
                    labels={
                        "fog": "FOG Average",
                        "_group": "Group"
                    }
                )
                # 4) Alle Balken in Dunkelblau
                fig.update_traces(marker_color="#1f77b4")
                # Vertikale Linien für Peer und Focal
                fig.add_vline(
                    x=mean_fog,
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
                    x=focal_fog,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.8,
                    annotation_text=f"<b>{company}</b>",
                    annotation_position="bottom left",
                    annotation_font_color="red",
                    annotation_font_size=16
                )
                fig.update_layout(
                    xaxis_title="FOG Average",
                    yaxis_title="Companies"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif plot_type == "Bar Chart":
                # 1) Detail-Bar-Chart aller Peer-Unternehmen, horizontale Balken nach Wert absteigend sortieren
                peers_df = plot_df.sort_values("fog", ascending=False)
                mean_fog = benchmark_df["fog"].mean()
            
                # 2) Kurz-Namen für die Y-Achse, damit sie nicht zu lang werden
                peers_df["company_short"] = peers_df["company"].str.slice(0, 15)
                y_order_short = peers_df["company_short"].tolist()[::-1]
            
                # 3) Horizontales Balkendiagramm erstellen
                fig2 = px.bar(
                    peers_df,
                    x="fog",
                    y="company_short",
                    orientation="h",
                    color="highlight_label",
                    color_discrete_map={company: "red", "Peers": "#1f77b4"},
                    labels={
                        "fog_avg": "FOG Average",
                        "company_short": "Company",
                        "highlight_label": ""
                    },
                    category_orders={"company_short": y_order_short},
                )

                fig2.update_layout(showlegend=False)
            
                # 4) Peer-Average-Linie hinzufügen
                fig2.add_vline(
                    x=mean_fog,
                    line_dash="dash",
                    line_color="black",
                    annotation_text="<b>Peer Average</b>",
                    annotation_position="bottom right",
                    annotation_font_color="black",
                    annotation_font_size=16,
                )
            
                # 5) Einheitliches Styling direkt hier anwenden
                fig2 = smart_layout(fig2, len(peers_df))
            
                # 6) Chart ausgeben
                st.plotly_chart(fig2, use_container_width=True)
            
                # — Vertikaler Vergleich Peer Average vs. Focal Company —
                avg_fog = mean_fog
                comp_df = pd.DataFrame({
                    "Group": ["Peer Average", company],
                    "fog": [avg_fog, focal_fog]
                })
                fig_avg = px.bar(
                    comp_df,
                    x="Group",
                    y="fog",
                    text="fog",
                    color="Group",
                    color_discrete_map={company: "red", "Peer Average": "#1f77b4"},
                    labels={"fog": "FOG Average", "Group": ""}
                )
                # rote Firma links anzeigen
                fig_avg.update_layout(
                    xaxis={"categoryorder": "array", "categoryarray": [company, "Peer Average"]},
                    showlegend=False
                )
                fig_avg.update_traces(texttemplate="%{text:.0f}", textposition="outside", width=0.5)
            
                st.plotly_chart(fig_avg, use_container_width=True)
        
        
        else:
            st.subheader("Peer Company List")
    
            st.caption("Companies included in this list, based on your peer group selection.")
            
            # 1) DataFrame ohne echten Index
            df_display = (
                benchmark_df
                [["company","country","SASB industry","Sustainability_Page_Count","words"]]
                .sort_values(by="Sustainability_Page_Count")
                .reset_index(drop=True)
            )
    
            md = df_display.to_markdown(index=False)
            st.markdown(md, unsafe_allow_html=True)
