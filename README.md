# Taller 2: Machine Learning I — Premier League 2025/26
**Integrantes:** Alejandro Pardo & Ailyn Gomez

Este repositorio contiene la solución completa para el Taller 2 de ML1. Hemos construido un pipeline de machine learning para predecir variables clave de la Premier League 2025-26, incluyendo goles esperados (xG), marcador final y resultado del partido (H/D/A).

---

## 📂 Estructura del Proyecto

El proyecto está organizado de manera modular para garantizar la reproducibilidad y escalabilidad:

### 1. `src/` (Source Code)
Contiene los scripts de Python que ejecutan la lógica del proyecto:
*   `process_data.py`: Descarga datos de la API y genera **Rolling Stats** (promedios móviles de los últimos 5 partidos). Esto es vital para capturar el "estado de forma" de los equipos.
*   `train_xg.py`: Entrena el modelo de **Expected Goals (xG)** usando coordenadas (X, Y) de más de 7,000 disparos.
*   `train_regression.py`: Implementa la **Regresión Lineal** para predecir goles (Home/Away) usando validación cruzada.
*   `train_classification.py`: Entrena el **Match Predictor** (Regresión Logística) para clasificar el resultado en Victoria Local, Empate o Victoria Visitante.
*   `export_dashboard_data.py`: Consolida todos los resultados y parámetros de los modelos en un archivo JSON para la web.

### 2. `models/`
Aquí se almacenan los modelos entrenados en formato binario (`.pkl`). Esto permite que el simulador web realice predicciones en milisegundos sin tener que re-entrenar los modelos.
*   `xg_model.pkl`
*   `regression_home.pkl` / `regression_away.pkl`
*   `match_predictor.pkl`

### 3. `data/`
*   `raw/`: Datos originales descargados de la API.
*   `processed/`: Versiones limpias de los datos, incluyendo la matriz de confusión y la importancia de las variables para el dashboard.

### 4. `dashboard/`
Contiene la aplicación web (SPA) construida con **HTML5, CSS3 y Vanilla JavaScript**.
*   `index.html`: Estructura y storytelling.
*   `style.css`: Diseño premium con modo oscuro y responsive.
*   `script.js`: Lógica del simulador 1 vs 1 que aplica las fórmulas matemáticas de nuestros modelos en el navegador.

---

## 🧠 Metodología y Modelos

### Ingeniería de Variables
No usamos los datos "crudos". Creamos variables de **diferencia de rendimiento** y promedios de los últimos 5 encuentros. Esto permite que el modelo entienda si un equipo viene en una racha ganadora o si su defensa ha estado floja recientemente.

### El Modelo de xG
Calculamos la probabilidad de gol de cada tiro basándonos en:
*   **Distancia:** Qué tan lejos está el jugador del arco.
*   **Ángulo:** Qué tan "cerrado" es el ángulo de disparo.
Logramos un AUC-ROC de **0.711**, lo que nos da una base sólida para entender la calidad ofensiva de los equipos.

### Predicción de Resultados
Nuestro modelo de clasificación alcanzó una precisión del **48.6% (CV)**. Aunque parece bajo, es muy competitivo, considerando que el *baseline* de las casas de apuestas (Bet365) es del **50.6%**. Esto demuestra que el fútbol es intrínsecamente impredecible y que nuestro modelo captura gran parte de la señal disponible.

---

## 🚀 Cómo Ejecutar el Proyecto

1.  **Entorno Virtual:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Entrenamiento:**
    Ejecutar los scripts en `src/` en orden: `process_data.py` -> `train_xg.py` -> `train_regression.py` -> `train_classification.py`.
3.  **Visualización:**
    Abrir `dashboard/index.html` en cualquier navegador moderno.

---
**Machine Learning I — 2026**
