import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt  
import seaborn as sns

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
        city_data = df_agg[df_agg["city"] == city_name].pivot(
        index='month', 
        columns='year', 
        values=['temp', 'hum_pct', 'rainfall', 'wind'])

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        metrics = ['temp', 'hum_pct', 'rainfall', 'wind']
        titles = ['Температура (°C)', 'Влажность (%)', 'Осадки (мм)', 'Ветер (км/ч)']
        cmaps = ['coolwarm', 'Blues', 'Blues', 'YlOrRd']

        for ax, metric, title, cmap in zip(axes.flatten(), metrics, titles, cmaps):
            data = city_data[metric]
            sns.heatmap(data, annot=True, cmap=cmap, fmt=".1f", ax=ax)
            ax.set_title(title)
            ax.set_xlabel("Год")
            ax.set_ylabel("Месяц")

        plt.suptitle(f"{city_name} — погода по месяцам и годам", fontsize=18)
        plt.tight_layout()
        plt.savefig(f"reports/{city_name}_weather.png")
        plt.close()
    except Exception as e:
        print('Ошибка!')
