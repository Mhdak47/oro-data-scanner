import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import os  # Ajoute cette ligne tout en haut avec les autres imports

# --- CONFIG TELEGRAM (Lecture automatique depuis les Secrets GitHub) ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Petit garde-fou au cas où (pour éviter une erreur si tu lances en local)
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠️ Variables d'environnement non trouvées. Utilisation des valeurs par défaut.")
    # Tu peux laisser tes anciens codes en backup ici si tu veux, mais normalement GitHub les remplace."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, json=payload)
    except:
        print("Erreur d'envoi Telegram")

def get_signals():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Scan des marchés...")
    
    # Récupération des données sur 7 jours en 1h
    end = datetime.now()
    start = end - timedelta(days=7)
    
    btc = yf.download('BTC-USD', interval='1h', start=start, end=end, progress=False)
    gold_etf = yf.download('GLD', interval='1h', start=start, end=end, progress=False)
    xauusd = yf.download('XAUUSD=X', interval='1h', start=start, end=end, progress=False)
    
    # --- 1. TRAITEMENT BTC (avec le ratio Or/ETF) ---
    df_btc = pd.DataFrame()
    df_btc['BTC'] = btc['Close']
    df_btc['Gold'] = gold_etf['Close']
    df_btc.dropna(inplace=True)
    
    if len(df_btc) >= 60:
        df_btc['Ratio'] = df_btc['BTC'] / df_btc['Gold']
        df_btc['Z_Score'] = (df_btc['Ratio'] - df_btc['Ratio'].rolling(60).mean()) / df_btc['Ratio'].rolling(60).std()
        df_btc['MA20'] = df_btc['BTC'].rolling(20).mean()
        
        # RSI maison pour BTC
        delta = df_btc['BTC'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_btc['RSI'] = 100 - (100 / (1 + rs))
        
        last_btc = df_btc.iloc[-1]
        signal_btc_achat = (last_btc['Z_Score'] < -0.6) and (last_btc['RSI'] < 40) and (last_btc['BTC'] > last_btc['MA20'])
        signal_btc_vente = (last_btc['Z_Score'] > 0.6) and (last_btc['RSI'] > 60) and (last_btc['BTC'] < last_btc['MA20'])
        btc_price = last_btc['BTC']
    else:
        signal_btc_achat = False
        signal_btc_vente = False
        btc_price = 0

    # --- 2. TRAITEMENT XAUUSD (Or spot, stratégie simple MA20 + RSI) ---
    df_xau = pd.DataFrame()
    df_xau['XAU'] = xauusd['Close']
    df_xau.dropna(inplace=True)
    
    if len(df_xau) >= 60:
        df_xau['MA20'] = df_xau['XAU'].rolling(20).mean()
        delta_xau = df_xau['XAU'].diff()
        gain_xau = (delta_xau.where(delta_xau > 0, 0)).rolling(window=14).mean()
        loss_xau = (-delta_xau.where(delta_xau < 0, 0)).rolling(window=14).mean()
        rs_xau = gain_xau / loss_xau
        df_xau['RSI'] = 100 - (100 / (1 + rs_xau))
        
        last_xau = df_xau.iloc[-1]
        signal_xau_achat = (last_xau['RSI'] < 40) and (last_xau['XAU'] > last_xau['MA20'])
        signal_xau_vente = (last_xau['RSI'] > 60) and (last_xau['XAU'] < last_xau['MA20'])
        xau_price = last_xau['XAU']
    else:
        signal_xau_achat = False
        signal_xau_vente = False
        xau_price = 0

    # --- 3. CONSTRUCTION DU MESSAGE TELEGRAM ---
    msg = f"<b>🤖 SCAN ORO & DATA - {datetime.now().strftime('%H:%M')}</b>\n"
    msg += f"---------------------------------\n"
    
    # SECTION BTC
    if signal_btc_achat:
        msg += f"🔥 <b>BTC : ALERTE ACHAT (LONG)</b> 🔥\n"
        msg += f"💰 Prix : {btc_price:,.0f} $\n"
        msg += f"🎯 SL : {btc_price * 0.985:,.0f} | TP : {btc_price * 1.03:,.0f}\n"
    elif signal_btc_vente:
        msg += f"⚠️ <b>BTC : ALERTE VENTE (SHORT)</b> ⚠️\n"
        msg += f"💰 Prix : {btc_price:,.0f} $\n"
        msg += f"🎯 SL : {btc_price * 1.015:,.0f} | TP : {btc_price * 0.97:,.0f}\n"
    else:
        msg += f"⚪ <b>BTC : PAS DE SIGNAL</b>\n"
    
    # SECTION XAUUSD
    msg += f"---------------------------------\n"
    if signal_xau_achat:
        msg += f"🔥 <b>XAUUSD : ALERTE ACHAT (LONG)</b> 🔥\n"
        msg += f"🥇 Prix : {xau_price:.2f} $\n"
        msg += f"🎯 SL : {xau_price * 0.985:.2f} | TP : {xau_price * 1.015:.2f}\n"
    elif signal_xau_vente:
        msg += f"⚠️ <b>XAUUSD : ALERTE VENTE (SHORT)</b> ⚠️\n"
        msg += f"🥇 Prix : {xau_price:.2f} $\n"
        msg += f"🎯 SL : {xau_price * 1.015:.2f} | TP : {xau_price * 0.985:.2f}\n"
    else:
        msg += f"⚪ <b>XAUUSD : PAS DE SIGNAL</b>\n"
    
    msg += f"---------------------------------\n"
    msg += f"🎧 <i>Jamal Flow - Patience et domination.</i>"
    
    # Envoi du message (même s'il n'y a pas de signal, ça te rassure que le bot tourne)
    send_telegram(msg)
    print("Message envoyé à Telegram.")

# --- POUR RENDER (EXÉCUTION UNIQUE, PAS DE BOUCLE) ---
if __name__ == "__main__":
    print("🚀 Lancement du Scanner Cron (Mode Render)")
    get_signals()
    print("✅ Scan terminé.")
