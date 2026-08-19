# 🏢 Immocomp - Comparateur & Simulateur d'Investissement Immobilier en SCI à l'IS

**Immocomp** est une application web interactive d'aide à la décision financière pour investisseurs immobiliers. Elle permet de simuler, comparer et projeter la rentabilité et la trésorerie nette de biens immobiliers (notamment des studios / appartements locatifs) détenus au sein d'une **Société Civile Immobilière soumise à l'Impôt sur les Sociétés (SCI à l'IS)** sur un horizon de **20 ans**.

---

## 📑 Sommaire
1. [Vue d'ensemble & Problématique Métier](#-vue-densemble--problématique-métier)
2. [Modèle Financier & Logique Business](#-modèle-financier--logique-business)
   - [1. Coût global du projet & Financement](#1-coût-global-du-projet--financement)
   - [2. Revenus locatifs & Indexation (IRL)](#2-revenus-locatifs--indexation-irl)
   - [3. Charges d'exploitation](#3-charges-dexploitation)
   - [4. Amortissements fiscaux par composants (Règles SCI IS)](#4-amortissements-fiscaux-par-composants-règles-sci-is)
   - [5. Déductibilité des frais de notaire](#5-déductibilité-des-frais-de-notaire)
   - [6. Résultat fiscal, report de déficit & Impôt sur les Sociétés (IS)](#6-résultat-fiscal-report-de-déficit--impôt-sur-les-sociétés-is)
   - [7. Trésorerie réelle (Cash-Flow) de la SCI](#7-trésorerie-réelle-cash-flow-de-la-sci)
   - [8. Indicateurs de performance (KPIs)](#8-indicateurs-de-performance-kpis)
3. [Fonctionnalités de l'Application](#-fonctionnalités-de-lapplication)
4. [Architecture Technique & Stack](#-architecture-technique--stack)
5. [Structure de la Base de Données](#-structure-de-la-base-de-données)
6. [Installation & Lancement](#-installation--lancement)

---

## 🎯 Vue d'ensemble & Problématique Métier

Dans un investissement immobilier locatif en direct (nom propre), l'investisseur est imposé au barème progressif de l'impôt sur le revenu (IR) majoré des prélèvements sociaux (17,2%), ce qui peut rapidement dégrader la rentabilité nette.

Le choix de la **SCI à l'IS** permet :
- **D'amortir le bien** comptablement (réduction drastique de la base imposable).
- **De déduire l'ensemble des charges réelles** (frais de notaire, intérêts, travaux, mobilier, assurance, comptabilité).
- **De reporter indéfiniment les déficits fiscaux** sur les bénéfices futurs.
- **De bénéficier d'un taux réduit d'IS à 15%** (sur la tranche de bénéfice inférieure à 42 500 €).
- **D'accumuler et réinvestir la trésorerie brute** au sein de la société sans frottement fiscal personnel immédiat.

**Immocomp modélise précisément cette réalité comptable et fiscale française année par année sur 20 ans.**

---

## 📊 Modèle Financier & Logique Business

L'application implémente une chaîne complète de calculs financiers et fiscaux. Voici le détail des algorithmes utilisés :

### 1. Coût global du projet & Financement

Le montant total investi et l'emprunt bancaire nécessaire sont calculés comme suit :

$$\text{Coût Total Projet} = \text{Prix d'achat} + \text{Frais de notaire} + \text{Travaux} + \text{Meubles / Équipement}$$

$$\text{Montant Emprunté} = \text{Coût Total Projet} - \text{Apport}$$

#### Calcul de la mensualité de crédit (formule bancaire standard à taux fixe) :
Pour un emprunt de capital $P$, avec un taux d'intérêt annuel $T$ (soit un taux mensuel $r = \frac{T}{100 \times 12}$) sur une durée de $n = \text{Durée en années} \times 12$ mois :

$$M = P \times \frac{r \cdot (1 + r)^n}{(1 + r)^n - 1}$$

Chaque année, l'application décompose les 12 mensualités entre la part d'**intérêts déductibles** et le **remboursement du capital**, en mettant à jour le capital restant dû.

---

### 2. Revenus locatifs & Indexation (IRL)

Pour chaque année $y \in [1, 20]$ :
- **Vacance locative** : Prise en compte du nombre de semaines de vacance par an :
  $$\text{Mois loués par an} = 12 - \left(\frac{\text{Vacance (semaines)}}{4.33}\right)$$
- **Indexation annuelle des loyers (IRL)** :
  $$\text{Loyer Annuel Brut}_y = (\text{Loyer Mensuel Cible} \times \text{Mois loués}) \times \left(1 + \frac{\text{IRL}}{100}\right)^{y - 1}$$

---

### 3. Charges d'exploitation

Les charges réelles d'exploitation annuelles sont déductibles :
$$\text{Charges Exploitation} = \text{Charges Copropriété (non récupérables)} + \text{Taxe Foncière} + \text{Assurance PNO} + \text{Frais Comptabilité SCI}$$

---

### 4. Amortissements fiscaux par composants (Règles SCI IS)

Contrairement aux particuliers au régime micro-foncier ou réel foncier, la SCI à l'IS pratique l'**amortissement par composants** :

| Composant | Assiette de calcul | Durée d'amortissement | Amortissement annuel | Période d'application |
| :--- | :--- | :--- | :--- | :--- |
| **Terrain (non amortissable)** | % Part Terrain (défaut : 15%) appliqué au Prix d'Achat | $\infty$ | $0\ \text{€}$ | - |
| **Bâti / Structure** | $\text{Prix d'Achat} \times (1 - \text{Part Terrain})$ | **30 ans** | $\frac{\text{Valeur Bâti}}{30}$ | Années 1 à 20 |
| **Travaux / Rénovations** | Montant des travaux | **10 ans** | $\frac{\text{Travaux}}{10}$ | Années 1 à 10 ($0$ après) |
| **Mobilier / Équipements** | Montant des meubles | **5 ans** | $\frac{\text{Meubles}}{5}$ | Années 1 à 5 ($0$ après) |

$$\text{Amortissement Annuel}_y = \text{Amortissement Bâti} + \mathbb{I}_{\{y \le 10\}} \text{Amort. Travaux} + \mathbb{I}_{\{y \le 5\}} \text{Amort. Meubles}$$

---

### 5. Déductibilité des frais de notaire

L'application applique l'option fiscale courante à l'IS consistant à **déduire l'intégralité des frais de notaire en charge immédiate en Année 1** :
$$\text{Frais Notaire Déduits}_y = \begin{cases} \text{Frais de Notaire} & \text{si } y = 1 \\ 0 & \text{si } y > 1 \end{cases}$$

---

### 6. Résultat fiscal, report de déficit & Impôt sur les Sociétés (IS)

Pour chaque année $y$ :

1. **Résultat fiscal brut de l'exercice** :
   $$\text{Résultat Brut}_y = \text{Loyer Annuel Brut}_y - \text{Charges Exploitation} - \text{Intérêts Emprunt}_y - \text{Amortissements}_y - \text{Frais Notaire Déduits}_y$$

2. **Imputation du déficit fiscal antérieur reportable** :
   $$\text{Résultat Imposable}_y = \text{Résultat Brut}_y - \text{Déficit Reportable}_{y-1}$$

3. **Calcul de l'Impôt et mise à jour du déficit** :
   - Si $\text{Résultat Imposable}_y > 0$ :
     $$\text{Impôt IS}_y = \text{Résultat Imposable}_y \times 15\% \quad (\text{Taux réduit PME})$$
     $$\text{Déficit Reportable}_y = 0$$
   - Si $\text{Résultat Imposable}_y \le 0$ :
     $$\text{Impôt IS}_y = 0\ \text{€}$$
     $$\text{Déficit Reportable}_y = |\text{Résultat Imposable}_y| \quad (\text{Report indéfini dans le temps})$$

---

### 7. Trésorerie réelle (Cash-Flow) de la SCI

Le cash-flow net représente l'argent liquide réellement généré et conservé sur le compte bancaire de la SCI :

$$\text{Cash-Flow Net Annuel}_y = \text{Loyer Annuel Brut}_y - \text{Charges Exploitation} - (\text{Mensualité Crédit} \times 12) - \text{Impôt IS}_y$$

$$\text{Cash-Flow Cumulé}_y = \sum_{t=1}^{y} \text{Cash-Flow Net Annuel}_t$$

---

### 8. Indicateurs de performance (KPIs)

- **Rentabilité Brute (Année 1)** :
  $$\text{Renta Brute} = \frac{\text{Loyer Brut A1 (net de vacance)}}{\text{Coût Total Projet}} \times 100$$
- **Rentabilité Nette (Année 1)** :
  $$\text{Renta Nette} = \frac{\text{Loyer Brut A1} - \text{Charges d'exploitation}}{\text{Coût Total Projet}} \times 100$$
- **Cash-Flow Mensuel Moyen (Année 1)** :
  $$\text{CF Mensuel A1} = \frac{\text{Cash-Flow Net Annuel}_1}{12}$$
- **Cash-Flow Cumulé à 20 ans** :
  $$\text{CF Cumulé 20 ans} = \text{Cash-Flow Cumulé}_{20}$$

---

## 🖥️ Fonctionnalités de l'Application

1. **Tableau de Bord Exécutif & Métriques Clés** :
   - Cartes KPI récapitulatives : Meilleure rentabilité nette, meilleur cash-flow mensuel (A1), moyenne globale, et trésorerie cumulée maximale à 20 ans.
2. **Visualisations Comparatives Interactives (Plotly)** :
   - Histogramme comparatif des rentabilités nettes par studio.
   - Histogramme comparatif de la trésorerie cumulée à 20 ans.
   - Graphique linéaire d'évolution de la **trésorerie annuelle** après IS sur 20 ans pour chaque bien.
   - Graphique linéaire de la **trésorerie cumulée** sur 20 ans.
3. **Audit Fiscal Détaillé (Déficits & IS)** :
   - Tableau déroulant affichant pour chaque année : Cash-flow net, impôt IS payé, et solde du déficit fiscal reporté.
4. **Tableau Synthétique Global** :
   - Vue tabulaire complète des biens enregistrés avec mise en forme des montants monétaires et pourcentages.
5. **Gestion CRUD Complète (Création, Lecture, Modification, Suppression)** :
   - *Ajout* via un formulaire latéral ergonomique avec des valeurs par défaut réalistes.
   - *Modification* dynamique des paramètres de n'importe quel studio.
   - *Suppression* sécurisée avec confirmation.

---

## 🛠️ Architecture Technique & Stack

```
immocomp/
├── app.py              # Application Streamlit principale (UI, calculs financiers, graphiques Plotly)
├── database.py         # Couche d'accès aux données (SQLite local ou Turso Cloud, migrations)
├── requirements.txt    # Dépendances Python du projet
└── .streamlit/
    └── secrets.toml    # (Optionnel) Clés de connexion Turso Database en production
```

- **Langage** : Python 3.9+
- **Interface Utilisateur** : [Streamlit](https://streamlit.io/)
- **Calculs Numériques & Données** : [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **Visualisations Graphiques** : [Plotly Express](https://plotly.com/python/plotly-express/)
- **Base de Données Hybride** :
  - **Local** : SQLite (`database.db`) par défaut (sans configuration requise).
  - **Cloud / Production** : [Turso](https://turso.tech/) (`libsql-client`) via variables d'environnement ou `secrets.toml`.

---

## 🗄️ Structure de la Base de Données

La table `properties` stocke toutes les caractéristiques d'un projet immobilier :

| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER PK` | Identifiant unique auto-incrémenté |
| `nom` | `TEXT` | Nom descriptif du bien (ex: Studio Gare) |
| `ville` | `TEXT` | Ville de localisation |
| `prix_achat` | `REAL` | Prix d'achat du bien (€) |
| `frais_notaire` | `REAL` | Frais de notaire / acquisition (€) |
| `travaux` | `REAL` | Montant des travaux initiaux (€) |
| `meubles` | `REAL` | Montant du mobilier / électroménager (€) |
| `loyer_mensuel` | `REAL` | Loyer mensuel hors charges (€) |
| `charges_annuelles` | `REAL` | Charges de copropriété annuelles non récupérables (€) |
| `taxe_fonciere` | `REAL` | Taxe foncière annuelle (€) |
| `assurance_pno` | `REAL` | Assurance PNO annuelle (€) |
| `frais_compta` | `REAL` | Honoraires comptables annuels de la SCI (€) |
| `vacance_semaines`| `INTEGER`| Semaines de vacance locative estimées par an |
| `apport` | `REAL` | Apport personnel en capital (€) |
| `taux_credit` | `REAL` | Taux d'intérêt annuel du crédit immobilier (%) |
| `duree_credit` | `INTEGER`| Durée de l'emprunt (années) |
| `irl_annuel` | `REAL` | Indexation prévisionnelle annuelle des loyers (%) |
| `part_terrain_pct`| `REAL` | Quote-part du terrain non amortissable (%) |

---

## 🚀 Installation & Lancement

### 1. Prérequis
- Python 3.9 ou version supérieure
- Gestionnaire de paquets `pip`

### 2. Cloner le projet et installer les dépendances
```bash
# Cloner le dépôt
git clone <url-du-depot>
cd immocomp

# (Recommandé) Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Lancer l'application
```bash
streamlit run app.py
```
L'application sera automatiquement accessible dans votre navigateur à l'adresse `http://localhost:8501`.

### 4. (Optionnel) Configuration Base de Données Cloud (Turso)
Pour utiliser une base de données cloud distribuée Turso, configurez les variables d'environnement ou ajoutez le fichier `.streamlit/secrets.toml` :

```toml
TURSO_DATABASE_URL = "libsql://votre-base-turso.turso.io"
TURSO_AUTH_TOKEN = "votre_token_secret"
```
Si ces variables ne sont pas renseignées, l'application utilise automatiquement le fichier SQLite local `database.db`.
