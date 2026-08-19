import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database import init_db, load_properties, save_property, update_property, delete_property, duplicate_property

# --- Configuration de la page ---
st.set_page_config(
    page_title="Immocomp | Simulateur SCI à l'IS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de la base de données
init_db()

# --- CSS Personnalisé & Design System Moderne ---
st.markdown("""
<style>
    /* Typographie et police globale */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* En-tête principal */
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .main-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        color: #F8FAFC;
    }
    .main-header p {
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
        color: #94A3B8;
    }
    .header-badge {
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #60A5FA;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* Cartes KPI Custom */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1.8rem;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.07);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3B82F6, #6366F1);
    }
    .kpi-card.success::before {
        background: linear-gradient(90deg, #10B981, #059669);
    }
    .kpi-card.warning::before {
        background: linear-gradient(90deg, #F59E0B, #D97706);
    }
    .kpi-card.indigo::before {
        background: linear-gradient(90deg, #8B5CF6, #6366F1);
    }
    .kpi-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .kpi-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 0.4rem;
    }

    /* Style des onglets Streamlit */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 0 18px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        color: #475569;
        background-color: transparent;
        border: none !important;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
    }

    /* Bannière d'information */
    .info-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
        color: #334155;
    }
    .info-box strong {
        color: #0F172A;
    }

    /* Badges & Tags */
    .badge-primary {
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Formulaires et cartes d'action */
    .action-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


# --- MOTEUR DE CALCUL FINANCIER & FISCAL (SCI À L'IS) ---
def calculate_metrics_sci_is(df):
    if df.empty:
        return df, pd.DataFrame()

    df['cout_projet'] = df['prix_achat'] + df['frais_notaire'] + df['travaux'] + df['meubles']
    df['emprunt'] = df['cout_projet'] - df['apport']

    def calc_pmt(row):
        r = (row['taux_credit'] / 100) / 12
        n = row['duree_credit'] * 12
        p = row['emprunt']
        if r == 0:
            return p / n if n > 0 else 0
        return p * (r * (1 + r)**n) / ((1 + r)**n - 1)

    df['mensualite_credit'] = df.apply(calc_pmt, axis=1)

    cf_yearly_list = []

    def process_20y_sci(row):
        # 1. Amortissements Fiscaux conformes
        valeur_bati = row['prix_achat'] * (1 - row['part_terrain_pct'] / 100)
        amort_bati_annuel = valeur_bati / 30.0  # Bâti : 30 ans
        amort_travaux_annuel = row['travaux'] / 10.0 if row['travaux'] > 0 else 0  # Travaux : 10 ans
        amort_meubles_annuel = row['meubles'] / 5.0 if row['meubles'] > 0 else 0  # Meubles : 5 ans

        solde_capital = row['emprunt']
        taux_mensuel = (row['taux_credit'] / 100) / 12

        total_cf_apres_is = 0
        cumul_cf = 0
        deficit_reportable = 0.0

        for y in range(1, 21):
            interets_annee = 0
            capital_amorti_annee = 0
            for _ in range(12):
                if solde_capital > 0:
                    i_mois = solde_capital * taux_mensuel
                    c_mois = row['mensualite_credit'] - i_mois
                    interets_annee += i_mois
                    capital_amorti_annee += c_mois
                    solde_capital -= c_mois
                    if solde_capital < 0:
                        solde_capital = 0

            # Prise en compte de la vacance locative et indexation IRL
            mois_loues = 12 - (row['vacance_semaines'] / 4.33)
            loyer_annuel_brut = (row['loyer_mensuel'] * mois_loues) * ((1 + row['irl_annuel'] / 100) ** (y - 1))

            # Charges d'exploitation
            charges_exploit = row['charges_annuelles'] + row['taxe_fonciere'] + row['assurance_pno'] + row['frais_compta']
            
            # Amortissements fiscaux applicables cette année
            amort_actuel = amort_bati_annuel
            if y <= 10:
                amort_actuel += amort_travaux_annuel
            if y <= 5:
                amort_actuel += amort_meubles_annuel

            # Frais de notaire en charge déductible immédiate en Année 1
            frais_notaire_deduits = row['frais_notaire'] if y == 1 else 0.0

            # Résultat fiscal brut
            resultat_brut = loyer_annuel_brut - charges_exploit - interets_annee - amort_actuel - frais_notaire_deduits
            
            # Imputation du déficit reportable
            resultat_apres_deficit = resultat_brut - deficit_reportable

            if resultat_apres_deficit > 0:
                impot_is = resultat_apres_deficit * 0.15  # Taux réduit PME
                deficit_reportable = 0.0
            else:
                impot_is = 0.0
                deficit_reportable = abs(resultat_apres_deficit)

            # Cash-Flow Trésorerie Réelle
            cf_tresorerie_annee = loyer_annuel_brut - charges_exploit - (row['mensualite_credit'] * 12) - impot_is
            total_cf_apres_is += cf_tresorerie_annee
            cumul_cf += cf_tresorerie_annee

            cf_yearly_list.append({
                "Annee": y,
                "Bien_ID": row['id'],
                "Bien": f"{row['nom']} ({row['ville'] or 'N/C'})",
                "Loyer_Brut": loyer_annuel_brut,
                "Charges_Exploitation": charges_exploit,
                "Interets_Credit": interets_annee,
                "Capital_Amorti": capital_amorti_annee,
                "Amortissements_Fiscaux": amort_actuel,
                "Resultat_Fiscal_Brut": resultat_brut,
                "Deficit_Reporte": deficit_reportable,
                "Impot_IS_Paye": impot_is,
                "CashFlow_Net_IS": cf_tresorerie_annee,
                "Cumul_CashFlow_IS": cumul_cf,
                "Capital_Restant_Du": solde_capital
            })

        return total_cf_apres_is

    df['cf_20ans_apres_is'] = df.apply(process_20y_sci, axis=1)
    df_cf_details = pd.DataFrame(cf_yearly_list)

    # Calculs pour l'Année 1
    df['loyer_net_vacance_y1'] = df['loyer_mensuel'] * (12 - (df['vacance_semaines'] / 4.33))
    df['renta_brute'] = (df['loyer_net_vacance_y1'] / df['cout_projet']) * 100
    df['renta_nette'] = ((df['loyer_net_vacance_y1'] - df['charges_annuelles'] - df['taxe_fonciere'] - df['assurance_pno'] - df['frais_compta']) / df['cout_projet']) * 100
    
    # Cash-flow mensuel moyen Année 1 après IS
    df_y1 = df_cf_details[df_cf_details['Annee'] == 1].set_index("Bien_ID")
    df['cf_mensuel_y1_is'] = df.apply(lambda r: df_y1.loc[r['id'], "CashFlow_Net_IS"] / 12, axis=1)

    return df, df_cf_details

# Chargement des données
df_raw = load_properties()
df, df_cf_details = calculate_metrics_sci_is(df_raw)


# --- MENU LATÉRAL : AJOUT D'UN BIEN ---
with st.sidebar:
    st.markdown("### 🏢 **Immocomp**")
    st.caption("Simulateur d'investissement locatif en SCI à l'IS")
    st.markdown("---")
    
    st.markdown("#### ➕ Ajouter un Nouveau Studio")
    with st.form("form_add", clear_on_submit=True):
        nom = st.text_input("Nom du bien *", placeholder="ex: Studio Centre-Ville")
        ville = st.text_input("Ville", placeholder="ex: Lyon, Bordeaux...")
        
        st.markdown("**💶 Acquisition & Travaux**")
        c1, c2 = st.columns(2)
        with c1:
            prix_achat = st.number_input("Prix d'achat (€)", min_value=0.0, value=90000.0, step=5000.0)
            frais_notaire = st.number_input("Notaire (€)", min_value=0.0, value=7500.0, step=500.0, help="Déductibles en charge immédiate en A1")
        with c2:
            travaux = st.number_input("Travaux (€)", min_value=0.0, value=8000.0, step=1000.0, help="Amortis sur 10 ans")
            meubles = st.number_input("Mobilier (€)", min_value=0.0, value=3000.0, step=500.0, help="Amortis sur 5 ans")

        st.markdown("**📈 Revenus Locatifs**")
        c3, c4 = st.columns(2)
        with c3:
            loyer_mensuel = st.number_input("Loyer mensuel HC (€)", min_value=0.0, value=580.0, step=20.0)
        with c4:
            vacance_semaines = st.number_input("Vacance (sem/an)", min_value=0, max_value=26, value=2)

        st.markdown("**💳 Charges & Exploitation (€/an)**")
        c5, c6 = st.columns(2)
        with c5:
            charges = st.number_input("Copro non récup.", min_value=0.0, value=450.0, step=50.0)
            taxe_f = st.number_input("Taxe Foncière", min_value=0.0, value=500.0, step=50.0)
        with c6:
            assurance_pno = st.number_input("Assurance PNO", min_value=0.0, value=120.0, step=10.0)
            frais_compta = st.number_input("Comptabilité SCI", min_value=0.0, value=500.0, step=50.0)

        st.markdown("**🏦 Financement & Paramètres SCI**")
        c7, c8 = st.columns(2)
        with c7:
            apport = st.number_input("Apport (€)", min_value=0.0, value=10000.0, step=1000.0)
            taux = st.number_input("Taux Crédit (%)", min_value=0.0, value=3.6, step=0.1)
        with c8:
            duree = st.number_input("Durée (ans)", min_value=1, max_value=30, value=20)
            irl = st.number_input("Indexation IRL (%)", min_value=0.0, value=1.5, step=0.1)

        part_terrain = st.slider("Quote-part Terrain non amortissable (%)", min_value=0.0, max_value=50.0, value=15.0, step=1.0, help="Par défaut 15% pour le terrain")

        btn_add = st.form_submit_button("💾 Enregistrer le Studio", use_container_width=True, type="primary")
        if btn_add:
            if nom.strip():
                save_property({
                    "nom": nom.strip(), "ville": ville.strip(), "prix_achat": prix_achat, "frais_notaire": frais_notaire,
                    "travaux": travaux, "meubles": meubles, "loyer_mensuel": loyer_mensuel,
                    "charges_annuelles": charges, "taxe_fonciere": taxe_f, "assurance_pno": assurance_pno,
                    "frais_compta": frais_compta, "vacance_semaines": vacance_semaines, "apport": apport,
                    "taux_credit": taux, "duree_credit": duree, "irl_annuel": irl, "part_terrain_pct": part_terrain
                })
                st.success("Studio ajouté avec succès !")
                st.rerun()
            else:
                st.error("Le nom du bien est obligatoire.")

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.78rem; color: #64748B; line-height: 1.4;">
        💡 <strong>Règles SCI IS appliquées :</strong><br>
        • Amortissement Bâti : 30 ans<br>
        • Amortissement Travaux : 10 ans<br>
        • Amortissement Meubles : 5 ans<br>
        • Frais de notaire déduits en A1<br>
        • IS à 15% & Report illimité des déficits
    </div>
    """, unsafe_allow_html=True)


# --- EN-TÊTE PRINCIPAL DE L'APPLICATION ---
nb_studios = len(df) if not df.empty else 0
st.markdown(f"""
<div class="main-header">
    <div>
        <h1>🏢 Immocomp • Simulateur & Comparateur SCI à l'IS</h1>
        <p>Analyse financière, comptabilité analytique et projection de trésorerie sur 20 ans</p>
    </div>
    <div>
        <span class="header-badge">{nb_studios} bien{'s' if nb_studios > 1 else ''} sous étude</span>
    </div>
</div>
""", unsafe_allow_html=True)


# --- CONTENU PRINCIPAL ---
if df.empty:
    st.info("👋 **Bienvenue sur Immocomp !** Aucun studio n'est actuellement enregistré. Utilisez le formulaire dans le menu latéral à gauche pour ajouter votre premier projet d'investissement.")
else:
    # 1. Cartes KPI Modernes en haut de page
    best_renta_row = df.loc[df['renta_nette'].idxmax()]
    best_cf_row = df.loc[df['cf_mensuel_y1_is'].idxmax()]
    max_cumul_row = df.loc[df['cf_20ans_apres_is'].idxmax()]

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card success">
            <div class="kpi-title">🏆 Max Renta Nette (A1)</div>
            <div class="kpi-value">{df['renta_nette'].max():.2f} %</div>
            <div class="kpi-subtitle">Top : {best_renta_row['nom']} ({best_renta_row['ville'] or 'N/C'})</div>
        </div>
        <div class="kpi-card indigo">
            <div class="kpi-title">💶 Meilleur Cash-Flow Mensuel IS (A1)</div>
            <div class="kpi-value">{df['cf_mensuel_y1_is'].max():+.0f} €<span style="font-size: 1rem; font-weight: normal; color: #64748B;">/mois</span></div>
            <div class="kpi-subtitle">Top : {best_cf_row['nom']}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">📊 Renta Nette Moyenne</div>
            <div class="kpi-value">{df['renta_nette'].mean():.2f} %</div>
            <div class="kpi-subtitle">Sur {len(df)} bien{'s' if len(df) > 1 else ''} analysé{'s' if len(df) > 1 else ''}</div>
        </div>
        <div class="kpi-card warning">
            <div class="kpi-title">💰 Max Trésorerie Cumulée 20 Ans</div>
            <div class="kpi-value">{df['cf_20ans_apres_is'].max():,.0f} €</div>
            <div class="kpi-subtitle">Top : {max_cumul_row['nom']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Structure par Onglets Thématiques
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Synthèse & Comparatif",
        "📈 Projections & Trésorerie 20 Ans",
        "📑 Fiscalité IS & Amortissements",
        "⚙️ Gestion des Biens & Scénarios"
    ])

    # =========================================================================
    # ONGLET 1 : SYNTHÈSE & COMPARATIF
    # =========================================================================
    with tab1:
        st.markdown("#### ⚖️ Comparatif Visuel des Biens")
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            fig1 = px.bar(
                df, x="nom", y="renta_nette", color="renta_nette",
                color_continuous_scale="Blues",
                labels={"nom": "Studio", "renta_nette": "Rentabilité Nette (%)"},
                title="<b>Rentabilité Nette Année 1 (%)</b>",
                text_auto='.2f'
            )
            fig1.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=45, b=20),
                coloraxis_showscale=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
            )
            st.plotly_chart(fig1, use_container_width=True)

        with c_chart2:
            fig2 = px.bar(
                df, x="nom", y="cf_20ans_apres_is", color="cf_20ans_apres_is",
                color_continuous_scale="Tealgrn",
                labels={"nom": "Studio", "cf_20ans_apres_is": "Trésorerie Cumulée (€)"},
                title="<b>Trésorerie Réelle Cumulée à 20 Ans (€)</b>",
                text_auto=',.0f'
            )
            fig2.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=45, b=20),
                coloraxis_showscale=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Tableau Récapitulatif Détaillé")

        # Mise en forme du tableau synthétique
        st.dataframe(
            df[[
                "nom", "ville", "prix_achat", "cout_projet", "apport", 
                "loyer_mensuel", "mensualite_credit", "renta_brute", 
                "renta_nette", "cf_mensuel_y1_is", "cf_20ans_apres_is"
            ]],
            column_config={
                "nom": st.column_config.TextColumn("Studio", width="medium"),
                "ville": st.column_config.TextColumn("Ville"),
                "prix_achat": st.column_config.NumberColumn("Prix Achat", format="%.0f €"),
                "cout_projet": st.column_config.NumberColumn("Coût Total", format="%.0f €"),
                "apport": st.column_config.NumberColumn("Apport", format="%.0f €"),
                "loyer_mensuel": st.column_config.NumberColumn("Loyer HC", format="%.0f €/m"),
                "mensualite_credit": st.column_config.NumberColumn("Crédit/Mois", format="%.0f €"),
                "renta_brute": st.column_config.NumberColumn("Renta Brute", format="%.2f %%"),
                "renta_nette": st.column_config.NumberColumn("Renta Nette", format="%.2f %%"),
                "cf_mensuel_y1_is": st.column_config.NumberColumn("Cash-Flow A1 (IS)", format="%+.0f €/m"),
                "cf_20ans_apres_is": st.column_config.NumberColumn("Trésorerie 20 ans", format="%.0f €")
            },
            use_container_width=True,
            hide_index=True
        )

    # =========================================================================
    # ONGLET 2 : PROJECTIONS & TRÉSORERIE 20 ANS
    # =========================================================================
    with tab2:
        st.markdown("#### 📈 Évolution Pluriannuelle de la Trésorerie (20 Ans)")
        
        # Filtre interactif par bien
        biens_dispos = ["Tous les biens"] + df_cf_details["Bien"].unique().tolist()
        filtre_bien = st.selectbox("🎯 Filtrer les projections sur un bien spécifique :", options=biens_dispos)

        if filtre_bien == "Tous les biens":
            data_plot = df_cf_details
        else:
            data_plot = df_cf_details[df_cf_details["Bien"] == filtre_bien]

        c_line1, c_line2 = st.columns(2)
        with c_line1:
            fig_annuel = px.line(
                data_plot, x="Annee", y="CashFlow_Net_IS", color="Bien", markers=True,
                title="<b>Trésorerie Nette Annuelle après IS (€/an)</b>",
                labels={"Annee": "Année", "CashFlow_Net_IS": "Cash-Flow Net (€)"},
                height=480
            )
            fig_annuel.add_hline(y=0, line_dash="dash", line_color="#94A3B8", opacity=0.8)
            fig_annuel.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                xaxis=dict(dtick=2, gridcolor="#F1F5F9"),
                yaxis=dict(gridcolor="#F1F5F9")
            )
            st.plotly_chart(fig_annuel, use_container_width=True)

        with c_line2:
            fig_cumul = px.line(
                data_plot, x="Annee", y="Cumul_CashFlow_IS", color="Bien", markers=True,
                title="<b>Trésorerie Cumulée Conservée dans la SCI (€)</b>",
                labels={"Annee": "Année", "Cumul_CashFlow_IS": "Trésorerie Cumulée (€)"},
                height=480
            )
            fig_cumul.add_hline(y=0, line_dash="dash", line_color="#94A3B8", opacity=0.8)
            fig_cumul.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                xaxis=dict(dtick=2, gridcolor="#F1F5F9"),
                yaxis=dict(gridcolor="#F1F5F9")
            )
            st.plotly_chart(fig_cumul, use_container_width=True)

        st.markdown("""
        <div class="info-box">
            📌 <strong>Analyse de la courbe :</strong> La trésorerie annuelle progresse au fil des ans grâce à l'indexation annuelle des loyers (IRL) et à l'amortissement du crédit bancaire (diminution des intérêts déductibles). L'arrêt de l'amortissement des meubles à $N=5$ ans et des travaux à $N=10$ ans marque des paliers d'imposition IS progressifs.
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # ONGLET 3 : FISCALITÉ IS & AMORTISSEMENTS
    # =========================================================================
    with tab3:
        st.markdown("#### 📑 Compte de Résultat & Suivi des Déficits Fiscaux")
        
        st.markdown("""
        <div class="info-box">
            💡 <strong>Mécanisme Fiscal de la SCI à l'IS :</strong><br>
            • <strong>Amortissements décomposés :</strong> Bâti (30 ans), Travaux (10 ans), Mobilier (5 ans).<br>
            • <strong>Frais de notaire :</strong> Passés en charge déductible immédiate en Année 1.<br>
            • <strong>Report indéfini des déficits :</strong> Aucun impôt n'est dû tant que le déficit fiscal cumulé n'a pas été entièrement absorbé.<br>
            • <strong>Taux d'IS :</strong> 15% sur la tranche de bénéfice &lt; 42 500 €.
        </div>
        """, unsafe_allow_html=True)

        # Tableau détaillé annuel
        sel_bien_fiscal = st.selectbox(
            "Sélectionner un bien pour examiner sa liasse fiscale annuelle :",
            options=df_cf_details["Bien"].unique().tolist(),
            key="sel_bien_fiscal"
        )
        
        df_fiscal_view = df_cf_details[df_cf_details["Bien"] == sel_bien_fiscal][[
            "Annee", "Loyer_Brut", "Charges_Exploitation", "Interets_Credit",
            "Amortissements_Fiscaux", "Resultat_Fiscal_Brut", "Deficit_Reporte",
            "Impot_IS_Paye", "CashFlow_Net_IS", "Cumul_CashFlow_IS", "Capital_Restant_Du"
        ]]

        st.dataframe(
            df_fiscal_view,
            column_config={
                "Annee": st.column_config.NumberColumn("Année", format="A%d"),
                "Loyer_Brut": st.column_config.NumberColumn("Loyers Bruts", format="%.0f €"),
                "Charges_Exploitation": st.column_config.NumberColumn("Charges Déduct.", format="%.0f €"),
                "Interets_Credit": st.column_config.NumberColumn("Intérêts Emprunt", format="%.0f €"),
                "Amortissements_Fiscaux": st.column_config.NumberColumn("Amortissements", format="%.0f €"),
                "Resultat_Fiscal_Brut": st.column_config.NumberColumn("Résultat Fiscal", format="%+.0f €"),
                "Deficit_Reporte": st.column_config.NumberColumn("Déficit Reporté", format="%.0f €"),
                "Impot_IS_Paye": st.column_config.NumberColumn("Impôt IS (15%)", format="%.0f €"),
                "CashFlow_Net_IS": st.column_config.NumberColumn("Cash-Flow Net", format="%+.0f €"),
                "Cumul_CashFlow_IS": st.column_config.NumberColumn("Trésorerie Cumulée", format="%.0f €"),
                "Capital_Restant_Du": st.column_config.NumberColumn("Capital Restant Dû", format="%.0f €")
            },
            use_container_width=True,
            hide_index=True
        )

        # Bouton d'export CSV
        csv_data = df_cf_details.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Télécharger les Projections 20 Ans (CSV)",
            data=csv_data,
            file_name="immocomp_projections_sci_is.csv",
            mime="text/csv"
        )

    # =========================================================================
    # ONGLET 4 : GESTION DES BIENS & SCÉNARIOS
    # =========================================================================
    with tab4:
        st.markdown("#### ⚙️ Administration & Scénarios Comparatifs")
        options_dict = {f"{row['nom']} ({row['ville'] or 'N/C'})": int(row['id']) for _, row in df.iterrows()}
        
        col_edit, col_tools = st.columns([2, 1])

        with col_edit:
            st.markdown("##### ✏️ Modifier un Studio")
            sel_edit = st.selectbox("Choisir le studio à modifier :", options=list(options_dict.keys()), key="edit_sel")
            edit_id = options_dict[sel_edit]
            b = df[df['id'] == edit_id].iloc[0]
            
            with st.form("form_edit"):
                u_nom = st.text_input("Nom du studio", value=str(b['nom']))
                u_ville = st.text_input("Ville", value=str(b['ville'] if b['ville'] else ""))
                
                uc1, uc2 = st.columns(2)
                with uc1:
                    u_prix = st.number_input("Prix d'achat (€)", value=float(b['prix_achat']), step=2000.0)
                    u_notaire = st.number_input("Notaire (€)", value=float(b['frais_notaire']), step=500.0)
                    u_travaux = st.number_input("Travaux (€)", value=float(b['travaux']), step=1000.0)
                    u_meubles = st.number_input("Meubles (€)", value=float(b['meubles']), step=500.0)
                    u_loyer = st.number_input("Loyer Mensuel (€)", value=float(b['loyer_mensuel']), step=20.0)
                    u_vacance = st.number_input("Vacance (semaines/an)", value=int(b['vacance_semaines']))
                with uc2:
                    u_charges = st.number_input("Charges Copro (€/an)", value=float(b['charges_annuelles']), step=50.0)
                    u_tf = st.number_input("Taxe Foncière (€/an)", value=float(b['taxe_fonciere']), step=50.0)
                    u_pno = st.number_input("Assurance PNO (€/an)", value=float(b['assurance_pno']), step=10.0)
                    u_compta = st.number_input("Comptabilité (€/an)", value=float(b['frais_compta']), step=50.0)
                    u_apport = st.number_input("Apport (€)", value=float(b['apport']), step=1000.0)
                    u_taux = st.number_input("Taux Crédit (%)", value=float(b['taux_credit']), step=0.1)
                
                uc3, uc4 = st.columns(2)
                with uc3:
                    u_duree = st.number_input("Durée Crédit (ans)", value=int(b['duree_credit']))
                    u_irl = st.number_input("Indexation IRL (%)", value=float(b['irl_annuel']), step=0.1)
                with uc4:
                    u_terrain = st.number_input("Quote-part Terrain (%)", value=float(b['part_terrain_pct']), step=1.0)

                if st.form_submit_button("💾 Mettre à jour les données", use_container_width=True, type="primary"):
                    update_property(edit_id, {
                        "nom": u_nom, "ville": u_ville, "prix_achat": u_prix, "frais_notaire": u_notaire,
                        "travaux": u_travaux, "meubles": u_meubles, "loyer_mensuel": u_loyer,
                        "charges_annuelles": u_charges, "taxe_fonciere": u_tf, "assurance_pno": u_pno,
                        "frais_compta": u_compta, "vacance_semaines": u_vacance, "apport": u_apport,
                        "taux_credit": u_taux, "duree_credit": u_duree, "irl_annuel": u_irl, "part_terrain_pct": u_terrain
                    })
                    st.success("Modifications enregistrées !")
                    st.rerun()

        with col_tools:
            st.markdown("##### 📋 Cloner pour Scénario A/B")
            st.caption("Dupliquez un studio en un clic pour tester des variantes (ex: négociation prix, taux bancaire...).")
            sel_clone = st.selectbox("Studio à dupliquer :", options=list(options_dict.keys()), key="clone_sel")
            clone_name = st.text_input("Nom de la variante :", value=f"{sel_clone.split('(')[0].strip()} (Scénario 2)")
            if st.button("📋 Dupliquer le studio", use_container_width=True):
                duplicate_property(options_dict[sel_clone], new_name=clone_name)
                st.success("Studio dupliqué avec succès !")
                st.rerun()

            st.markdown("---")
            st.markdown("##### 🗑️ Supprimer un Studio")
            sel_del = st.selectbox("Studio à supprimer :", options=list(options_dict.keys()), key="del_sel")
            if st.button("🚨 Confirmer la suppression", type="secondary", use_container_width=True):
                delete_property(options_dict[sel_del])
                st.success("Studio supprimé.")
                st.rerun()