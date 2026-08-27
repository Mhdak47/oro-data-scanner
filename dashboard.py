import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Oro & Data - QG AK47",
    page_icon="👾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSO (Noir & Or - Street Luxe / AK47) ---
st.markdown("""
    <style>
        .main { background-color: #0a0a0a; }
        .stApp { background-color: #0a0a0a; }
        h1, h2, h3, h4, h5, h6 { color: #D4AF37 !important; font-family: 'Arial Black', sans-serif; }
        .css-1d391kg { background-color: #0a0a0a; }
        .stMetric { background-color: #1a1a1a; border-radius: 10px; padding: 10px; border: 1px solid #D4AF37; }
        .block-container { padding-top: 2rem; }
        .stTextInput > div > div > input { background-color: #1a1a1a; color: white; border: 1px solid #D4AF37; }
        .stSelectbox > div > div > select { background-color: #1a1a1a; color: white; border: 1px solid #D4AF37; }
        hr { border-color: #D4AF37; opacity: 0.3; }
        .header-tag { color: #888; font-size: 14px; letter-spacing: 2px; }
        .gold-text { color: #D4AF37; font-weight: bold; }
        .ak-quote { color: #aaa; font-style: italic; border-left: 3px solid #D4AF37; padding-left: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- TITRE ---
st.markdown("<h1 style='text-align: center;'>👾 ORO & DATA - QG AK47</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Le QG du Stratège Marocain - Précision & Domination 🇲🇦</p>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR (Paramètres) ---
with st.sidebar:
    st.image("https://via.placeholder.com/150/0a0a0a/D4AF37?text=AK47+FLOW", width=150) 
    st.markdown("### 🎯 Paramètres du Stratège")
    days = st.slider("Période d'analyse (jours)", 7, 60, 30)
    threshold = st.slider("Seuil Z-Score (agressivité)", 0.3, 1.0, 0.6)
    st.markdown("---")
    st.markdown("<p class='ak-quote'>'La domination ne s'obtient pas par la force, mais par la lecture du jeu.' - Stratège AK47</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("⚡ Dernier scan: " + datetime.now().strftime("%H:%M:%S"))

# --- 1. RECUPERATION DES DONNEES ---
@st.cache_data(ttl=300)  # Cache de 5 minutes
def load_data(days):
    end = datetime.now()
    start = end - timedelta(days=days)
    
    btc = yf.download('BTC-USD', start=start, end=end, progress=False)
    gold = yf.download('GLD', start=start, end=end, progress=False)
    xau = yf.download('XAUUSD=X', start=start, end=end, progress=False)
    dxy = yf.download('DX-Y.NYB', start=start, end=end, progress=False)
    
    df = pd.DataFrame()
    df['BTC'] = btc['Close']
    df['GLD'] = gold['Close']
    df['XAU'] = xau['Close']
    df['DXY'] = dxy['Close']
    df.dropna(inplace=True)
    
    if len(df) < 20:
        return None
    
    df['MA20_BTC'] = df['BTC'].rolling(20).mean()
    df['Ratio_BTC_GLD'] = df['BTC'] / df['GLD']
    df['Z_Score'] = (df['Ratio_BTC_GLD'] - df['Ratio_BTC_GLD'].rolling(60).mean()) / df['Ratio_BTC_GLD'].rolling(60).std()
    
    delta = df['BTC'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_BTC'] = 100 - (100 / (1 + rs))
    
    delta_x = df['XAU'].diff()
    gain_x = (delta_x.where(delta_x > 0, 0)).rolling(window=14).mean()
    loss_x = (-delta_x.where(delta_x < 0, 0)).rolling(window=14).mean()
    rs_x = gain_x / loss_x
    df['RSI_XAU'] = 100 - (100 / (1 + rs_x))
    df['MA20_XAU'] = df['XAU'].rolling(20).mean()
    
    df['Corr_BTC_GLD'] = df['BTC'].rolling(30).corr(df['GLD'])
    df['Corr_BTC_DXY'] = df['BTC'].rolling(30).corr(df['DXY'])
    
    return df

df = load_data(days)

if df is None or df.empty:
    st.error("⚠️ Erreur de chargement des données. Vérifie ta connexion ou réessaie plus tard.")
    st.stop()

last = df.iloc[-1]

# --- 2. SECTION METRIQUES (TOP ROW) ---
st.markdown("### 📡 Situation des Marchés")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("💰 BTC/USD", f"${last['BTC']:,.0f}", delta=f"{((last['BTC']/df.iloc[-2]['BTC']-1)*100):.2f}%")
with col2:
    st.metric("🥇 XAU/USD", f"${last['XAU']:.2f}", delta=f"{((last['XAU']/df.iloc[-2]['XAU']-1)*100):.2f}%")
with col3:
    color_zs = "normal"
    if last['Z_Score'] > threshold: color_zs = "inverse"
    elif last['Z_Score'] < -threshold: color_zs = "normal"
    st.metric("🎯 Z-Score (BTC/Or)", f"{last['Z_Score']:.2f}", delta=f"Seuil: ±{threshold}", delta_color=color_zs)
with col4:
    st.metric("📈 RSI BTC", f"{last['RSI_BTC']:.1f}", delta="Survente < 40" if last['RSI_BTC'] < 40 else "Surachat > 60" if last['RSI_BTC'] > 60 else "Neutre")
with col5:
    corr_val = last['Corr_BTC_GLD']
    st.metric("🔗 Corr BTC/Or", f"{corr_val:.2f}", delta="Refuge" if corr_val > 0.3 else "Risqué" if corr_val < -0.3 else "Décorrélé")

st.divider()

# --- 3. SIGNAL DU MOMENT (L'ALERTE CHAUDE) ---
st.markdown("### 🚨 Alerte Stratégique du Moment")
cond1 = last['Z_Score'] < -threshold
cond2 = last['RSI_BTC'] < 40
cond3 = last['BTC'] > last['MA20_BTC']

signal_buy = cond1 and cond2 and cond3
signal_sell = (last['Z_Score'] > threshold) and (last['RSI_BTC'] > 60) and (last['BTC'] < last['MA20_BTC'])

col_alert, col_advice = st.columns([2, 1])
with col_alert:
    if signal_buy:
        st.success(f"🔥 **ALERTE ACHAT (LONG)** - BTC sous-évalué. Prix: ${last['BTC']:,.0f} | SL: ${last['BTC']*0.985:,.0f} | TP: ${last['BTC']*1.03:,.0f}")
    elif signal_sell:
        st.error(f"⚠️ **ALERTE VENTE (SHORT)** - BTC sur-évalué. Prix: ${last['BTC']:,.0f} | SL: ${last['BTC']*1.015:,.0f} | TP: ${last['BTC']*0.97:,.0f}")
    else:
        st.info("⚪ **PAS DE SIGNAL FORT** - Le marché est en phase d'attente. Patience, stratège.")
with col_advice:
    st.markdown(f"<p style='text-align: right; color: #D4AF37;'>🎧 <i>Mode AK47 activé</i></p>", unsafe_allow_html=True)

st.divider()

# --- 4. GRAPHIQUES DYNAMIQUES (PLOTLY) ---
st.markdown("### 📊 Analyse Technique Avancée")

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=('BTC/USD - Prix & MA20', 'BTC - RSI (Zone de guerre)',
                    'XAU/USD - Or Spot', 'Z-Score du Ratio BTC/Or',
                    'Corrélations (BTC/Or & BTC/DXY)', 'Volume (indicatif)'),
    vertical_spacing=0.12,
    horizontal_spacing=0.1
)

# Graph 1: BTC + MA20
fig.add_trace(go.Scatter(x=df.index, y=df['BTC'], name='BTC', line=dict(color='#D4AF37', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MA20_BTC'], name='MA20', line=dict(color='cyan', width=1, dash='dash')), row=1, col=1)

# Graph 2: RSI BTC
fig.add_trace(go.Scatter(x=df.index, y=df['RSI_BTC'], name='RSI', line=dict(color='orange', width=2)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

# Graph 3: XAU
fig.add_trace(go.Scatter(x=df.index, y=df['XAU'], name='XAUUSD', line=dict(color='gold', width=2)), row=1, col=2)
fig.add_trace(go.Scatter(x=df.index, y=df['MA20_XAU'], name='MA20_XAU', line=dict(color='white', width=1, dash='dash')), row=1, col=2)

# Graph 4: Z-Score
fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], name='Z-Score', line=dict(color='cyan', width=2)), row=2, col=2)
fig.add_hline(y=threshold, line_dash="dash", line_color="red", row=2, col=2)
fig.add_hline(y=-threshold, line_dash="dash", line_color="green", row=2, col=2)
fig.add_hrect(y0=-threshold, y1=threshold, line_width=0, fillcolor="gray", opacity=0.15, row=2, col=2)

# Graph 5: Correlations
fig.add_trace(go.Scatter(x=df.index, y=df['Corr_BTC_GLD'], name='Corr BTC/Or', line=dict(color='#D4AF37', width=2)), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['Corr_BTC_DXY'], name='Corr BTC/DXY', line=dict(color='red', width=2)), row=3, col=1)
fig.add_hline(y=0, line_dash="dash", line_color="white", row=3, col=1)

# Graph 6: Volume placeholder
fig.add_trace(go.Bar(x=df.index, y=df['BTC'], name='Volume estimé', marker_color='#D4AF37', opacity=0.3), row=3, col=2)

# Mise à jour du layout global (Dark Theme)
fig.update_layout(
    template='plotly_dark',
    height=1000,
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    paper_bgcolor='#0a0a0a',
    plot_bgcolor='#0a0a0a',
    font=dict(color='white'),
    hovermode='x unified'
)

fig.update_xaxes(gridcolor='#333333', color='white')
fig.update_yaxes(gridcolor='#333333', color='white')

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 5. HISTORIQUE DES ALERTES & TRADE JOURNAL ---
st.markdown("### 📓 Carnet de Bord du Stratège")

col_journal, col_actions = st.columns([3, 1])

with col_journal:
    data_history = {
        'Date': ['2026-08-27 12:00', '2026-08-27 06:00', '2026-08-26 22:00'],
        'Actif': ['BTC', 'XAUUSD', 'BTC'],
        'Signal': ['ACHAT (LONG)', 'NEUTRE', 'VENTE (SHORT)'],
        'Prix': ['$61,234', '$2,512.30', '$60,100'],
        'Résultat': ['En cours', '-', 'N/A']
    }
    df_history = pd.DataFrame(data_history)
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    st.caption("📌 L'historique réel des alertes Telegram s'affichera ici automatiquement (à connecter plus tard).")

with col_actions:
    st.markdown("#### 🎯 Action Rapide")
    trade_result = st.selectbox("Résultat du dernier trade", ["✅ Gagnant", "❌ Perdant", "⏳ En cours"])
    if st.button("📝 Enregistrer dans le journal"):
        st.success("Journal mis à jour ! (Feature en construction pour lien avec bot)")

# --- 6. FOOTER ---
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f2:
    st.markdown("<p style='text-align: center; color: #555;'>👾 Oro & Data - Puissance AK47 & Data 🇲🇦</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #333; font-size: 12px;'>Le QG du Stratège Marocain - 2026</p>", unsafe_allow_html=True)