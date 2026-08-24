import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt  
import seaborn as sns
import numpy as np

engine = create_engine("mysql+pymysql://root:root@localhost")

with engine.connect() as conn: 
    conn.execute(text("CREATE DATABASE IF NOT EXISTS weather_db"))

engine = create_engine("mysql+pymysql://root:root@localhost/weather_db")
df = pd.read_csv('D:/Meteo/data/global_weather_100_cities_2014_2024.csv')

df.to_sql("weather_global", con=engine, index=False, if_exists='replace')

query = """
SELECT 
    city, 
    YEAR(date) AS year, 
    MONTH(date) AS month, 
    AVG(avg_temperature_c) AS temp, 
    AVG(avg_humidity_pct) AS hum_pct, 
    AVG(rainfall_mm) AS rainfall,  
    AVG(max_wind_speed_kmh) AS wind
FROM weather_global
GROUP BY city, year, month
"""

df_agg = pd.read_sql(query, engine)

import os 
os.makedirs('reports', exist_ok=True)

cities = df_agg['city'].unique()

for city_name in cities:
    try:
        city_data = df_agg[df_agg["city"] == city_name]

        pivot_temp = city_data.pivot(index = 'month', columns = 'year', values = 'temp')
        pivot_hum = city_data.pivot(index = 'month', columns = 'year', values = 'hum_pct')
        pivot_rain = city_data.pivot(index='month', columns='year', values='rainfall')
        pivot_wind = city_data.pivot(index='month', columns='year', values='wind')

        def calc_deviation(pivot_df):
            monthly_avg = pivot_df.mean(axis = 1)
            deviation = pivot_df.sub(monthly_avg, axis = 0)
            return deviation

        dev_temp = calc_deviation(pivot_temp)
        dev_hum = calc_deviation(pivot_hum)
        dev_rain = calc_deviation(pivot_rain)
        dev_wind = calc_deviation(pivot_wind)

        dev_avg = pd.DataFrame({
            'month': dev_temp.index,
            'temp_dev': dev_temp.mean(axis=1).round(2),
            'hum_dev': dev_hum.mean(axis=1).round(2),
            'rain_dev': dev_rain.mean(axis=1).round(2),
            'wind_dev': dev_wind.mean(axis=1).round(2)
        })
        dev_avg.to_csv(f'reports/{city_name}_deviation.csv', index = False)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        metrics = [
            (dev_temp, 'Температура (°C)', 'coolwarm', 'Отклонение температуры от нормы'),
            (dev_hum, 'Влажность (%)', 'coolwarm', 'Отклонение влажности от нормы'),
            (dev_rain, 'Осадки (мм)', 'coolwarm', 'Отклонение осадков от нормы'),
            (dev_wind, 'Ветер (км/ч)', 'coolwarm', 'Отклонение ветра от нормы')
        ]
        
        for ax, (data, title, cmap, cbar_label) in zip(axes.flatten(), metrics):
            # 
            sns.heatmap(
                data, 
                annot=True,         
                fmt=".1f",          
                cmap=cmap, 
                center=0,      
                ax=ax,
                cbar_kws={'label': cbar_label},
                linewidths=0.5,     
                linecolor='white'
            )
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel("Год", fontsize=12)
            ax.set_ylabel("Месяц", fontsize=12)
            
            month_names = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                          'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
            ax.set_yticklabels(month_names, rotation=0)

        plt.suptitle(f"{city_name})",
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"reports/{city_name}_weather_deviations.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"{city_name} - отчет создан")
        
    except Exception as e:
        print(f"Ошибка для города {city_name}: {str(e)}")
