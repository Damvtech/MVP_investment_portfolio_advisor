import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from scipy.optimize import minimize

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
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    data = pd.DataFrame()
    for company, symbol in symbols.items():
        df = yf.download(symbol, start=start_date, end=end_date)['Close']
        if not df.empty:
            data[company] = df
        #else:
        #    print(f"No se pudieron descargar los datos para {company} ({symbol}).")
    return data.dropna()

data = cargar_datos()

# Rendimientos diarios
daily_returns = data.pct_change().dropna()
mean_daily_returns = daily_returns.mean()
cov_matrix = daily_returns.cov()

# Preguntas
st.title("📊 Recomendador de Cartera de Inversión")
st.write("Responde estas preguntas para determinar la cartera más adecuada a tu apetito de riesgo actual:")

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

        # Mostrar resultados
        cartera = {data.columns[i]: round(pesos_optimos[i]*100,2) for i in range(len(data.columns)) if pesos_optimos[i] > 0.001}

        st.subheader("🎯 Composición óptima de tu cartera")
        for empresa, peso in cartera.items():
            st.write(f"- **{empresa}:** {peso}%")

        rent_anual = annualized_return(pesos_optimos)
        vol_anual = annualized_volatility(pesos_optimos)

        st.write(f"🔸 **Rentabilidad anualizada esperada:** {rent_anual:.2%}")
        st.write(f"🔸 **Volatilidad anualizada esperada:** {vol_anual:.2%}")

