import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from database import init_db, load_properties, save_property, delete_property

# Configuration de la page
st.set_page_config(page_title="Comparateur Immobilier Pro", layout="wide")
init_db()

st.title("🏠 Real Estate Analyzer & Comparateur 20 Ans")

# --- CALCULS FINANCIERS ---
def calculate_metrics(df):
    if df.empty:
        return df
    
    # Coût total
    df['cout_total'] = df['prix_achat'] + df['frais_notaire'] + df['travaux']
    df['emprunt'] = df['cout_total'] - df['apport']
    
    # Mensualité crédit
    def pmt(row):
        r = (row['taux_credit'] / 100) / 12
        n = row['duree_credit'] * 12
        p = row['emprunt']
        if r == 0:
            return p / n
        return p * (r * (1 + r)**n) / ((1 + r)**n - 1)
        
    df['mensualite'] = df.apply(pmt, axis=1)
    
    # Rentabilités Y1
    df['renta_brute'] = (df['loyer_mensuel'] * 12) / df['cout_total'] * 100
    df['renta_nette'] = ((df['loyer_mensuel'] * 12) - df['charges_annuelles'] - df['taxe_fonciere']) / df['cout_total'] * 100
    df['cash_flow_mois'] = df['loyer_mensuel'] - df['mensualite'] - (df['charges_annuelles'] / 12) - (df['taxe_fonciere'] / 12)
    
    # Projection 20 Ans avec IRL
    def cf_cumule_20ans(row):
        total_cf = 0
        for y in range(1, 21):
            loyer_y = (row['loyer_mensuel'] * 12) * ((1 + row['irl_annuel'] / 100) ** (y - 1))
            cf_y = loyer_y - (row['mensualite'] * 12) - row['charges_annuelles'] - row['taxe_fonciere']
            total_cf += cf_y
        return total_cf

    df['cf_cumule_20ans'] = df.apply(cf_cumule_20ans, axis=1)
    return df

df_raw = load_properties()
df = calculate_metrics(df_raw)

# --- MENU LATÉRAL (FORMULAIRE DE SAISIE) ---
st.sidebar.header("➕ Ajouter un Bien")
with st.sidebar.form("property_form", clear_on_submit=True):
    nom = st.text_input("Nom du bien (ex: T2 Hypercentre)")
    ville = st.text_input("Ville")
    
    col1, col2 = st.columns(2)
    with col1:
        prix_achat = st.number_input("Prix d'achat (€)", min_value=0.0, value=120000.0, step=5000.0)
        frais_notaire = st.number_input("Notaire (€)", min_value=0.0, value=9000.0, step=500.0)
        travaux = st.number_input("Travaux (€)", min_value=0.0, value=10000.0, step=1000.0)
        loyer_mensuel = st.number_input("Loyer Mensuel (€)", min_value=0.0, value=700.0, step=50.0)
    
    with col2:
        charges = st.number_input("Charges / An (€)", min_value=0.0, value=800.0, step=100.0)
        taxe_f = st.number_input("Taxe Foncière / An (€)", min_value=0.0, value=650.0, step=50.0)
        apport = st.number_input("Apport (€)", min_value=0.0, value=15000.0, step=1000.0)
        taux = st.number_input("Taux Crédit (%)", min_value=0.0, value=3.5, step=0.1)
    
    duree = st.number_input("Durée Emprunt (ans)", min_value=1, max_value=30, value=20)
    irl = st.number_input("Indexation IRL / An (%)", min_value=0.0, max_value=10.0, value=1.5, step=0.1)
    
    submitted = st.form_submit_button("Sauvegarder le Bien")
    if submitted and nom:
        new_data = {
            "nom": nom, "ville": ville, "prix_achat": prix_achat, "frais_notaire": frais_notaire,
            "travaux": travaux, "loyer_mensuel": loyer_mensuel, "charges_annuelles": charges,
            "taxe_fonciere": taxe_f, "apport": apport, "taux_credit": taux,
            "duree_credit": duree, "irl_annuel": irl
        }
        save_property(new_data)
        st.success("Bien enregistré avec succès !")
        st.rerun()

# --- TABLEAU DE BORD (DASHBOARD) ---
if not df.empty:
    # 1. Cartes KPIs
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Meilleure Renta Nette", f"{df['renta_nette'].max():.2f} %")
    col_kpi2.metric("Max Cash-Flow / Mois", f"{df['cash_flow_mois'].max():.0f} €")
    col_kpi3.metric("Renta Nette Moyenne", f"{df['renta_nette'].mean():.2f} %")
    col_kpi4.metric("Max CF Cumulé 20 Ans", f"{df['cf_cumule_20ans'].max():,.0f} €".replace(",", " "))

    st.markdown("---")

    # 2. Graphiques
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig1 = px.bar(df, x="nom", y="renta_nette", color="renta_nette", 
                      title="Rentabilité Nette par Bien (%)", labels={"nom": "Bien", "renta_nette": "Renta Nette (%)"})
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        fig2 = px.bar(df, x="nom", y="cf_cumule_20ans", color="cf_cumule_20ans",
                      title="Cash-Flow Cumulé sur 20 Ans avec IRL (€)", labels={"nom": "Bien", "cf_cumule_20ans": "CF 20 Ans (€)"})
        st.plotly_chart(fig2, use_container_width=True)

    # 3. Tableau complet des biens
    st.subheader("📊 Classement et Détails des Biens")
    st.dataframe(
        df[["id", "nom", "ville", "prix_achat", "cout_total", "loyer_mensuel", "renta_brute", "renta_nette", "cash_flow_mois", "cf_cumule_20ans"]],
        column_config={
            "id": st.column_config.NumberColumn("ID", format="%d"),
            "prix_achat": st.column_config.NumberColumn("Prix Achat", format="%.0f €"),
            "cout_total": st.column_config.NumberColumn("Coût Total", format="%.0f €"),
            "loyer_mensuel": st.column_config.NumberColumn("Loyer/Mois", format="%.0f €"),
            "renta_brute": st.column_config.NumberColumn("Renta Brute", format="%.2f %%"),
            "renta_nette": st.column_config.NumberColumn("Renta Nette", format="%.2f %%"),
            "cash_flow_mois": st.column_config.NumberColumn("CF/Mois Y1", format="%.0f €"),
            "cf_cumule_20ans": st.column_config.NumberColumn("CF 20 Ans", format="%.0f €")
        },
        use_container_width=True
    )

    # --- SECTION SUPPRESSION (CORRIGÉE) ---
    with st.expander("🗑️ Supprimer un bien"):
        # Création d'un dictionnaire lisible { "ID - Nom du bien": ID }
        options_dict = {f"ID {row['id']} - {row['nom']} ({row['ville']})": int(row['id']) for _, row in df.iterrows()}
        selected_label = st.selectbox("Choisir le bien à supprimer", options=list(options_dict.keys()))
        
        if st.button("Confirmer la suppression", type="primary"):
            id_to_del = options_dict[selected_label]
            delete_property(id_to_del)
            st.success(f"Bien supprimé avec succès.")
            st.rerun()
else:
    st.info("Aucun bien enregistré pour le moment. Utilisez le panneau latéral pour en ajouter.")