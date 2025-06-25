import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI

#load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

#import cmdstanpy
#cmdstanpy.install_cmdstan()


# Definir las fechas globalmente
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)

# Añadir imagen
image_url = "https://www.inabaweb.com/wp-content/uploads/2023/06/eToro.png"
st.image(image_url, caption="Imagen de la URL", use_container_width=True)

# Descargar datos
@st.cache_data
def cargar_datos():
    symbols = {
    "Apple": "AAPL", "Microsoft": "MSFT", "Amazon": "AMZN", "Alphabet (Google)": "GOOGL", "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B", "Johnson & Johnson": "JNJ", "Exxon Mobil": "XOM", "JPMorgan Chase": "JPM", "Visa": "V",
    "Nestlé": "NESN.SW", "Roche": "ROG.SW", "Samsung Electronics": "005930.KS", "Toyota": "7203.T", "Sony": "6758.T",
    "Alibaba": "BABA", "Tencent": "0700.HK", "HSBC": "HSBA.L", "BP": "BP.L", "Shell": "SHEL.L",
    "Unilever": "ULVR.L", "LVMH": "MC.PA", "TotalEnergies": "TTE.PA", "Siemens": "SIE.DE", "Volkswagen": "VOW3.DE",
    "SAP": "SAP.DE", "Banco Santander": "SAN.MC", "BBVA": "BBVA.MC", "Petrobras": "PBR", "Vale": "VALE",
    "ICICI Bank": "IBN", "Reliance Industries": "RELIANCE.BO", "Infosys": "INFY", "Ping An Insurance": "2318.HK",
    "China Mobile": "0941.HK", "Rio Tinto": "RIO.L", "BHP Group": "BHP.AX", "Commonwealth Bank": "CBA.AX",
    "CSL Limited": "CSL.AX", "Novo Nordisk": "NOVO-B.CO", "AstraZeneca": "AZN.L", "Adidas": "ADS.DE",
    "Heineken": "HEIA.AS", "Philips": "PHIA.AS", "Enel": "ENEL.MI", "Ferrari": "RACE", "Saudi Aramco": "2222.SR",
    "Tencent Music": "TME", "Meta Platforms (Facebook)": "META", "Procter & Gamble": "PG", "Coca-Cola": "KO",
    "PepsiCo": "PEP", "McDonald's": "MCD", "Walmart": "WMT", "Costco": "COST", "Intel": "INTC",
    "AMD": "AMD", "NVIDIA": "NVDA", "Qualcomm": "QCOM", "Broadcom": "AVGO", "Texas Instruments": "TXN",
    "IBM": "IBM", "Oracle": "ORCL", "Salesforce": "CRM", "Adobe": "ADBE", "Netflix": "NFLX",
    "AT&T": "T", "Verizon": "VZ", "T-Mobile": "TMUS", "Pfizer": "PFE", "Moderna": "MRNA",
    "Merck": "MRK", "Bristol-Myers Squibb": "BMY", "Amgen": "AMGN", "Gilead Sciences": "GILD", "Eli Lilly": "LLY",
    "Chevron": "CVX", "ConocoPhillips": "COP", "Schlumberger": "SLB", "Halliburton": "HAL", "Marathon Oil": "MRO",
    "Lockheed Martin": "LMT", "Northrop Grumman": "NOC", "Raytheon Technologies": "RTX", "Boeing": "BA",
    "General Electric": "GE", "Honeywell": "HON", "3M": "MMM", "Caterpillar": "CAT", "Deere & Company": "DE",
    "Starbucks": "SBUX", "Nike": "NKE", "Lululemon": "LULU", "Estee Lauder": "EL", "Domino's Pizza": "DPZ",
    "Booking Holdings": "BKNG", "American Express": "AXP", "Mastercard": "MA", "PayPal": "PYPL"
        # Puedes agregar más compañías aquí para tu MVP
    }
    data = pd.DataFrame()
    for company, symbol in symbols.items():
        df = yf.download(symbol, start=start_date, end=end_date)['Close']
        if not df.empty:
            data[company] = df
        else:
            print(f"No se pudieron descargar los datos para {company} ({symbol}).")
    return data.dropna()

data = cargar_datos()

# Rendimientos diarios
daily_returns = data.pct_change().dropna()
mean_daily_returns = daily_returns.mean()
cov_matrix = daily_returns.cov()

# Preguntas
st.title("📊 Recomendador de Cartera de Inversión")
st.write("Responde estas preguntas para determinar la cartera más adecuada a tu apetito de riesgo actual:")
st.write("**Esta simulación se basa en datos históricos y no garantiza rentabilidades futuras. Invierte con responsabilidad.*") # Disclaimer

# Widget con clave única
q1 = st.radio("Nivel de seguridad deseado:",
              ["Máxima seguridad", "Alta seguridad", "Equilibrado", "Alta rentabilidad", "Máxima rentabilidad"],
              index=None, key='q1')

q2 = st.radio("Diversificación deseada:",
              ["Muy conservadora", "Conservadora", "Equilibrada", "Agresiva", "Muy agresiva"],
              index=None, key='q2')

q3 = st.radio("Expectativa de rentabilidad:",
              ["Muy baja", "Moderada-baja", "Media", "Alta", "Muy alta"],
              index=None, key='q3')

q4 = st.radio("Nivel máximo de pérdida aceptable:",
              ["0%", "Hasta 5%", "Hasta 10%", "Hasta 20%", "Más de 20%"],
              index=None, key='q4')

q5 = st.radio("Horizonte temporal de la inversión:",
              ["< 1 año", "1-3 años", "3-5 años", "5-10 años", ">10 años"],
              index=None, key='q5')

# Botón para generar cartera (para evitar auto-ejecución)
if st.button("Generar cartera óptima"):

    # Verificar si todas las preguntas han sido respondidas
    if None in [q1, q2, q3, q4, q5]:
        st.warning("Por favor, responde todas las preguntas antes de continuar.")
    else:
        # Calcular puntuación
        preguntas = [q1, q2, q3, q4, q5]
        puntuaciones = [ ["Máxima seguridad", "Alta seguridad", "Equilibrado", "Alta rentabilidad", "Máxima rentabilidad"].index(q1)+1,
                         ["Muy conservadora", "Conservadora", "Equilibrada", "Agresiva", "Muy agresiva"].index(q2)+1,
                         ["Muy baja", "Moderada-baja", "Media", "Alta", "Muy alta"].index(q3)+1,
                         ["0%", "Hasta 5%", "Hasta 10%", "Hasta 20%", "Más de 20%"].index(q4)+1,
                         ["< 1 año", "1-3 años", "3-5 años", "5-10 años", ">10 años"].index(q5)+1 ]
        
        total = sum(puntuaciones)

        # Categorizar usuario
        if total <= 8:
            perfil = "Riesgo mínimo"
        elif total <= 12:
            perfil = "Riesgo bajo"
        elif total <= 17:
            perfil = "Riesgo medio"
        elif total <= 21:
            perfil = "Riesgo alto"
        else:
            perfil = "Rentabilidad máxima"

        st.subheader(f"Tu perfil actual: {perfil}")

        # Funciones objetivo
        def annualized_return(w):
            return np.sum(mean_daily_returns * w) * 252

        def annualized_volatility(w):
            return np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))) * np.sqrt(252)

        objetivos = {
            "Riesgo mínimo": lambda w: annualized_volatility(w),
            "Riesgo bajo": lambda w: 0.75*annualized_volatility(w)-0.25*annualized_return(w),
            "Riesgo medio": lambda w: 0.50*annualized_volatility(w)-0.50*annualized_return(w),
            "Riesgo alto": lambda w: 0.25*annualized_volatility(w)-0.75*annualized_return(w),
            "Rentabilidad máxima": lambda w: -annualized_return(w)
        }

        # Optimizar cartera
        def optimizar(objetivo):
            num_activos = len(mean_daily_returns)
            w0 = np.ones(num_activos) / num_activos
            bounds = [(0,1) for _ in range(num_activos)]
            constraints = {'type':'eq', 'fun': lambda w: np.sum(w)-1}
            result = minimize(objetivo, w0, bounds=bounds, constraints=constraints)
            return result.x

        # Cartera óptima
        pesos_optimos = optimizar(objetivos[perfil])

        # Mostrar resultados ordenados
        cartera = {data.columns[i]: round(pesos_optimos[i]*100, 2) for i in range(len(data.columns)) if pesos_optimos[i] > 0.001}

        # Ordenar la cartera por porcentaje de mayor a menor
        cartera_ordenada = dict(sorted(cartera.items(), key=lambda item: item[1], reverse=True))

        st.subheader("🎯 Composición óptima de tu cartera (ordenada de mayor a menor)")
        for empresa, peso in cartera_ordenada.items():
            st.write(f"- **{empresa}:** {peso}%")

        # Convertir divisa a EUR si es necesario

        # Mapeo de divisas por activo (según Yahoo Finance)
        divisas = {
            "AAPL": "USD", "MSFT": "USD", "AMZN": "USD", "GOOGL": "USD", "TSLA": "USD",
            "BRK-B": "USD", "JNJ": "USD", "XOM": "USD", "JPM": "USD", "V": "USD",
            "NESN.SW": "CHF", "ROG.SW": "CHF", "005930.KS": "KRW", "7203.T": "JPY", "6758.T": "JPY",
            "BABA": "HKD", "0700.HK": "HKD", "HSBA.L": "GBP", "BP.L": "GBP", "SHEL.L": "GBP",
            "ULVR.L": "GBP", "MC.PA": "EUR", "TTE.PA": "EUR", "SIE.DE": "EUR", "VOW3.DE": "EUR",
            "SAP.DE": "EUR", "SAN.MC": "EUR", "BBVA.MC": "EUR", "PBR": "BRL", "VALE": "BRL",
            "IBN": "INR", "RELIANCE.BO": "INR", "INFY": "INR", "2318.HK": "HKD",
            "0941.HK": "HKD", "RIO.L": "GBP", "BHP.AX": "AUD", "CBA.AX": "AUD",
            "CSL.AX": "AUD", "NOVO-B.CO": "DKK", "AZN.L": "GBP", "ADS.DE": "EUR",
            "HEIA.AS": "EUR", "PHIA.AS": "EUR", "ENEL.MI": "EUR", "RACE": "EUR", "2222.SR": "SAR",
            "TME": "USD", "META": "USD", "PG": "USD", "KO": "USD",
            "PEP": "USD", "MCD": "USD", "WMT": "USD", "COST": "USD", "INTC": "USD",
            "AMD": "USD", "NVDA": "USD", "QCOM": "USD", "AVGO": "USD", "TXN": "USD",
            "IBM": "USD", "ORCL": "USD", "CRM": "USD", "ADBE": "USD", "NFLX": "USD",
            "T": "USD", "VZ": "USD", "TMUS": "USD", "PFE": "USD", "MRNA": "USD",
            "MRK": "USD", "BMY": "USD", "AMGN": "USD", "GILD": "USD", "LLY": "USD",
            "CVX": "USD", "COP": "USD", "SLB": "USD", "HAL": "USD", "MRO": "USD",
            "LMT": "USD", "NOC": "USD", "RTX": "USD", "BA": "USD",
            "GE": "USD", "HON": "USD", "MMM": "USD", "CAT": "USD", "DE": "USD",
            "SBUX": "USD", "NKE": "USD", "LULU": "USD", "EL": "USD", "DPZ": "USD",
            "BKNG": "USD", "AXP": "USD", "MA": "USD", "PYPL": "USD"
        }

        # Descargar tipos de cambio necesarios
        st.write("🔄 **Descargando tipos de cambio para convertir a EUR...**")
        tipos_cambio = {}
        for divisa in set(divisas.values()):
            if divisa != "EUR":  # No necesitamos convertir EUR a EUR
                ticker = f"EUR{divisa}=X" if divisa != "USD" else "EURUSD=X"
                tipos_cambio[divisa] = yf.download(ticker, start=start_date, end=end_date)['Close'].fillna(method='ffill')

        # Convertir cada activo a EUR según su divisa
        st.write("💱 **Convirtiendo valores de los activos a EUR...**")
        data_eur = data.copy()
        for column in data.columns:
            divisa = divisas.get(column, "USD")  # Asumir USD por defecto si no se especifica
            if divisa != "EUR":  # Solo convertir si no está ya en EUR
                ticker = f"EUR{divisa}=X" if divisa != "USD" else "EURUSD=X"
                # Alinear los índices de los datos y los tipos de cambio
                tipo_cambio_alineado = tipos_cambio[divisa].reindex(data.index).fillna(method='ffill')
                # Convertir el precio del activo a EUR
                data_eur[column] = data[column] / tipo_cambio_alineado[ticker]

        # Continuar con el cálculo de la cartera
        st.write("📊 **Calculando el valor diario de la cartera propuesta...**")

        # Escalamos la cartera como si hubieras invertido 1.000 €
        inversion_inicial = 1000
        cartera_retornos = (data_eur * pesos_optimos).sum(axis=1)
        cartera_valores = cartera_retornos / cartera_retornos.iloc[0] * inversion_inicial

        # Graficar la cartera durante los últimos 5 años
        st.subheader("📈 **Evolución de la cartera propuesta en los últimos 5 años:**")
        plt.figure(figsize=(10, 6))
        plt.plot(cartera_valores, label="Cartera propuesta")
        plt.title("Evolución de la cartera propuesta (últimos 5 años)")
        plt.xlabel("Fecha")
        plt.ylabel("Valor de la cartera (EUR)")
        plt.legend()
        st.pyplot(plt)

        # Calcular estadísticas de la cartera
        rolling_max = cartera_valores.cummax()
        drawdowns = (cartera_valores - rolling_max) / rolling_max

        if not drawdowns.isnull().all():
            max_drawdown = drawdowns.min()
            drawdown_start = drawdowns.idxmin()

            try:
                recovery_series = cartera_valores.loc[cartera_valores.index >= drawdown_start]
                drawdown_end = recovery_series[recovery_series >= recovery_series.iloc[0]].index[0]
            except IndexError:
                drawdown_end = cartera_valores.index[-1]
        else:
            max_drawdown = 0.0
            drawdown_start = cartera_valores.index[0]
            drawdown_end = cartera_valores.index[-1]

        valor_final = cartera_valores.iloc[-1]
        ganancia_pct = (valor_final - inversion_inicial) / inversion_inicial * 100
    
        # Crear función para enviar promp a ChatGPT
        def generar_mensaje_inversion(perfil, valor_final, ganancia_pct, drawdown_pct, drawdown_inicio, drawdown_fin):
            prompt = f"""
        Eres un asesor financiero que explica de forma clara y cercana los resultados de una inversión simulada.

        Perfil del inversor: {perfil}.
        Inversión inicial: 1.000€.
        Valor actual después de 5 años: {valor_final:.2f}€.
        Rentabilidad acumulada: {ganancia_pct:.2f}%.

        El peor momento de esta cartera fue entre {drawdown_inicio} y {drawdown_fin}, con una caída del {drawdown_pct:.2f}% desde su máximo anterior.

        Redacta una frase breve y empática que combine estos datos y le recuerde al usuario que mantener la calma es clave, adaptándola a su perfil de riesgo.
        """
            client = OpenAI(
                api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )

            mensaje = response.choices[0].message.content.strip()

            return mensaje

        with st.spinner("Generando análisis personalizado con IA..."):
            try:
                mensaje = generar_mensaje_inversion(
                    perfil=perfil,  # ej. "Riesgo medio"
                    valor_final=valor_final,  # float, ej. 2217.71
                    ganancia_pct=ganancia_pct,  # float, ej. 121.77
                    drawdown_pct=max_drawdown * 100,  # float
                    drawdown_inicio=drawdown_start.strftime('%B %Y'),  # ej. "diciembre 2023"
                    drawdown_fin=drawdown_end.strftime('%B %Y')  # ej. "abril 2025"
                )
                st.markdown("### 🧠 Reflexión sobre tu inversión 👇🏼")
                st.success(mensaje)
            except Exception as e:
                st.error(f"Ocurrió un error al generar el mensaje: {e}")


