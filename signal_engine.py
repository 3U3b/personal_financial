# -*- coding: utf-8 -*-
# signal_engine.py

# 動能狀態判斷
def calculate_momentum(price_change_ratio):
    if price_change_ratio >= 0.02:
        momentum = "價格動能明顯增強"
    elif price_change_ratio >= 0.005:
        momentum = "價格小幅走強"
    elif price_change_ratio <= -0.02:
        momentum = "價格動能明顯轉弱"
    elif price_change_ratio <= -0.005:
        momentum = "價格小幅走弱"
    else:
        momentum = "價格平穩盤整"
        
    return momentum
    
def calculate_volume_signal(imbalance_ratio):

    text = (
        "🚀 強烈買盤拉抬" if imbalance_ratio > 0.15 
        else "📈 買盤略大於賣盤" if imbalance_ratio > 0.02 
        else "📉 賣壓湧現" if imbalance_ratio < -0.05 
        else "⚪ 買賣力道均衡"
    )
    return text