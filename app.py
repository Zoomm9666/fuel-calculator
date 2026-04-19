import streamlit as st
import pandas as pd
import json
import requests
import re
from utils import calculate_distance, get_intermediate_point

# --- ОБЯЗАТЕЛЬНО В САМОМ ВЕРХУ ---
CHECKWX_API_KEY = "8dcbfc4fe37e443c8ea59b14d550f5c0"
# Определяем иконку ветра (Компас)

def get_wind_icon(deg):
    try:
        deg = int(deg)
        if 337 <= deg or deg < 23: return "↑"
        if 23 <= deg < 68: return "↗"
        if 68 <= deg < 113: return "→"
        if 113 <= deg < 158: return "↘"
        if 158 <= deg < 203: return "↓"
        if 203 <= deg < 248: return "↙"
        if 248 <= deg < 293: return "←"
        if 293 <= deg < 337: return "↖"
    except: return "🧭"
    return "🧭"

# Цвет категории полетов
def get_cat_color(cat):
    return {"VFR": "#28a745", "MVFR": "#007bff", "IFR": "#dc3545", "LIFR": "#6f42c1"}.get(cat, "#808080")

# Твой метод извлечения давления через регулярные выражения
def extract_pressure(raw):
    if not isinstance(raw, str): return "N/A"
    m_q = re.search(r"\bQ(\d{4})\b", raw)
    if m_q: return f"Q{m_q.group(1)}"
    m_a = re.search(r"\bA(\d{4})\b", raw)
    if m_a: return f"A{m_a.group(1)}"
    return "N/A"

# Функция запроса ветра
def get_wind_aloft(lat, lon, flight_level):
    """Получает ветер на заданном эшелоне для конкретной точки"""
    # AWC API требует эшелон в сотнях футов (как и наш FL)
    url = f"https://aviationweather.gov"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Нам нужно найти ближайший ветер в текстовом блоке
            # Для начала сделаем упрощенный парсинг или возьмем среднее значение 
            # (AWC отдает сетку данных, которую нужно фильтровать по координатам)
            
            # ВРЕМЕННАЯ ЛОГИКА (Заглушка для теста):
            # В реальности тут будет сложный парсинг сетки GFS. 
            # Для v1.0 возьмем встречный ветер 20 узлов, если летим на Запад, 
            # и попутный, если на Восток.
            return -20 if lon < 40 else 20 
    except:
        return 0
    return 0


# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="FUEL CALCULATOR", layout="wide", initial_sidebar_state="expanded")

# Инициализация переменных сессии (память приложения)
if 'total_dist' not in st.session_state:
    st.session_state['total_dist'] = 0
if 'points' not in st.session_state:
    st.session_state['points'] = []

if 'weather_view' not in st.session_state:
    st.session_state['weather_view'] = {'dep': None, 'dest': None, 'altn': None}

if 'route_calculated' not in st.session_state:
    st.session_state['route_calculated'] = False

# --- УВЕЛИЧЕНИЕ ШРИФТА ВКЛАДОК (CSS) ---
st.markdown("""
    <style>
    /* Находим кнопки вкладок по их CSS-классу и увеличиваем шрифт */
    button[data-baseweb="tab"] {
        border-radius: 10px !important;
    }
    button[data-baseweb="tab"] p {
        font-size: 24px !important;  /* Размер шрифта */
        font-weight: bold !important; /* Жирность */
        color: #FFFFFF !important;    /* Цвет текста */
    }
    /* Эффект при наведении */
    button[data-baseweb="tab"]:hover {
        background-color: rgba(40, 167, 69, 0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- САМИ ВКЛАДКИ С ОБНОВЛЕННЫМИ ИКОНКАМИ ---
tab_route, tab_payload, tab_fuel = st.tabs([
    "🗺️ ROUTE & WX", 
    "⚖️ PAYLOAD", 
    "⛽ FUEL PLANNING"
])

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_aircraft_db():
    with open('aircraft_db.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_airports():
    # Загружаем базу аэропортов (убедитесь, что файл airports.csv в корне)
    df = pd.read_csv('airports.csv')
    return df[['ident', 'name', 'latitude_deg', 'longitude_deg', 'elevation_ft']]

aircraft_db = load_aircraft_db()
airports_df = load_airports()

# --- ФУНКЦИИ API ---

# --- ФУНКЦИИ API ---

def checkwx_request(url):
    headers = {"X-API-KEY": CHECKWX_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"{response.status_code}: {response.text}"
        data = response.json()
        if 'data' in data and data['data']:
            return data['data'][0], None
        return None, "No data returned"
    except Exception as e:
        return None, str(e)


def get_metar(icao):
    if not CHECKWX_API_KEY:
        return None, "API key is missing"
    
    url = f"https://api.checkwx.com/v2/metar/{icao.upper()}/decoded"
    return checkwx_request(url)


def get_taf(icao):
    """Получение прогноза TAF через CheckWX API v2"""
    if not CHECKWX_API_KEY:
        return None, "API key is missing"
    
    url = f"https://api.checkwx.com/v2/taf/{icao.upper()}/decoded"
    return checkwx_request(url)


def get_airport_data(icao):
    icao = icao.upper().strip()
    data = airports_df[airports_df['ident'] == icao]
    if not data.empty:
        return data.iloc[0]
    return None

# --- САЙДБАР (ВЫБОР ВС) ---
st.sidebar.title("AIRCRAFT CONFIG")
unit = st.sidebar.selectbox("UNITS / ЕДИНИЦЫ", ["KG", "LBS"])

brand = st.sidebar.selectbox("BRAND / БРЕНД", list(aircraft_db.keys()))
model_key = st.sidebar.selectbox("MODEL / МОДЕЛЬ", list(aircraft_db[brand].keys()))
selected_ac = aircraft_db[brand][model_key]

st.sidebar.divider()
st.sidebar.info(f"""
**Selected: {selected_ac['name']}**
* MZFW: {selected_ac['mzfw_kg']} kg
* MTOW: {selected_ac['mtow_kg']} kg
* Burn: {selected_ac['fuel_burn_kgph']} kg/h
""")

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
st.title("✈️ FUEL CALCULATOR")
st.caption(" Fuel Planning based on FAP-128")

#tab_route, tab_payload, tab_fuel = st.tabs(["📍 ROUTE", "📦 PAYLOAD", "⛽ FUEL"])

# --- ВКЛАДКА 1: МАРШРУТ ---
with tab_route:
    st.subheader("ROUTE & WEATHER / МАРШРУТ И ПОГОДА")
    
    # 1. Поля ввода ICAO
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        dep_icao = st.text_input("ORIGIN (ICAO) / ВЫЛЕТ", value="ULLI").upper().strip()
        st.caption("Аэропорт вылета")
    with col_i2:
        dest_icao = st.text_input("DESTINATION (ICAO) / ПРИЛЕТ", value="UUEE").upper().strip()
        st.caption("Аэропорт назначения")
    with col_i3:
        altn_icao = st.text_input("ALTERNATE (ICAO) / ЗАПАСНОЙ", value="UUDD").upper().strip()
        st.caption("Запасной аэродром")

    cruise_fl = st.number_input("CRUISE LEVEL (FL) / ЭШЕЛОН", value=350, step=10)
    st.caption("Планируемый эшелон полета")

    # 2. Логика обработки маршрута
    if st.button("GET ROUTE DATA / ПОЛУЧИТЬ ДАННЫЕ", use_container_width=True):
        dep_data = get_airport_data(dep_icao)
        dest_data = get_airport_data(dest_icao)
        altn_data = get_airport_data(altn_icao)

        if all(x is not None for x in [dep_data, dest_data, altn_data]):
            st.session_state['route_calculated'] = True
        else:
            st.session_state['route_calculated'] = False
            st.error("One or more ICAO codes were not found in the airport database.")

    if st.session_state['route_calculated']:
        dep_data = get_airport_data(dep_icao)
        dest_data = get_airport_data(dest_icao)
        altn_data = get_airport_data(altn_icao)

        # Если аэропорты найдены, продолжаем расчеты
        if all(x is not None for x in [dep_data, dest_data, altn_data]):
            
            # --- РАСЧЕТ ДИСТАНЦИЙ ---
            raw_dist = calculate_distance(
                dep_data['latitude_deg'], dep_data['longitude_deg'],
                dest_data['latitude_deg'], dest_data['longitude_deg']
            )
            dist_main_final = round(raw_dist * 1.07)
            st.session_state['total_dist'] = dist_main_final

            dist_altn_raw = calculate_distance(
                dest_data['latitude_deg'], dest_data['longitude_deg'],
                altn_data['latitude_deg'], altn_data['longitude_deg']
            )
            dist_altn_final = round(dist_altn_raw * 1.07)
            st.session_state['altn_dist'] = dist_altn_final

            points = []
            for f in [0.25, 0.5, 0.75]:
                p = get_intermediate_point(
                    dep_data['latitude_deg'], dep_data['longitude_deg'],
                    dest_data['latitude_deg'], dest_data['longitude_deg'], f
                )
                points.append(p)
            st.session_state['points'] = points

            st.divider()
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.success(f"**MAIN DISTANCE:** {dist_main_final} NM")
                st.caption("Расстояние основного маршрута (+7% Airway Factor)")
            with col_res2:
                st.warning(f"**ALTERNATE DISTANCE:** {dist_altn_final} NM")
                st.caption("Расстояние до запасного (+7% Airway Factor)")

            p1, p2, p3 = points
            st.info(f"""
            **Wind Checkpoints (LAT/LON):**
            * 25%: {p1[0]:.2f}, {p1[1]:.2f} | 50%: {p2[0]:.2f}, {p2[1]:.2f} | 75%: {p3[0]:.2f}, {p3[1]:.2f}
            """)
            # Расчет среднего ветра по 3 точкам
            total_wind_comp = 0
            for p in points:
                # p[1] — это долгота (longitude) точки
                total_wind_comp += get_wind_aloft(p[0], p[1], cruise_fl)
            
            avg_wind = round(total_wind_comp / 3)
            st.session_state['avg_wind'] = avg_wind

            # Вывод результата на экран
            st.info(f"💨 **AVERAGE WIND COMPONENT:** {avg_wind} KT")
            st.caption("Средняя составляющая ветра (Tailwind > 0, Headwind < 0)")
        else:
            st.error("One or more ICAO codes were not found in the airport database.")

        st.divider()
        st.write("**AIRPORT WEATHER / ПОГОДА В АЭРОПОРТАХ**")
        
        mw1, mw2, mw3 = st.columns(3)

        # Вспомогательная функция для отрисовки колонки погоды
        def render_weather_col(col, icao, label_en, label_ru, state_key):
            with col:
                st.markdown(f"### {icao}")
                st.caption(f"{label_en} / {label_ru}")
                
                # Кнопки METAR/TAF
                b_c1, b_c2 = st.columns(2)
                if b_c1.button("⛅ METAR", key=f"btn_m_{state_key}_{icao}", use_container_width=True):
                    st.session_state['weather_view'][state_key] = 'metar'
                if b_c2.button("📄 TAF", key=f"btn_t_{state_key}_{icao}", use_container_width=True):
                    st.session_state['weather_view'][state_key] = 'taf'

                # Логика показа данных
                view = st.session_state['weather_view'][state_key]
                
                if view == 'metar':
                    with st.spinner(f"Loading {icao} METAR..."):
                        m_data, error = get_metar(icao)
                        if error:
                            st.error(f"METAR error: {error}")
                        elif m_data:
                            raw = m_data.get('raw_text', '')
                            cat = m_data.get('flight_category', 'VFR')
                            color = get_cat_color(cat)
                            st.markdown(f"<span style='color:{color}; font-weight:bold;'>● {cat}</span>", unsafe_allow_html=True)
                            st.code(raw, language="text")
                            
                            # Расшифровка
                            wind_deg = m_data.get('wind', {}).get('degrees', 0)
                            icon = get_wind_icon(wind_deg)
                            pressure = extract_pressure(raw)
                            st.write(f"{icon} Wind: {wind_deg}° / {m_data.get('wind', {}).get('speed_mps', 0)} m/s")
                            st.write(f"🌡 Temp: {m_data.get('temperature', {}).get('celsius')}°C | ⏱ {pressure}")
                        else:
                            st.error("No METAR found")
                            
                elif view == 'taf':
                    with st.spinner(f"Loading {icao} TAF..."):
                        t_data, error = get_taf(icao) # Убедитесь, что функция get_taf определена в API
                        if error:
                            st.error(f"TAF error: {error}")
                        elif t_data:
                            st.code(t_data.get('raw_text'), language="text")
                        else:
                            st.error("No TAF found")

        # Отрисовка трех колонок
        if dep_icao: render_weather_col(mw1, dep_icao, "DEPARTURE", "ВЫЛЕТ", "dep")
        if dest_icao: render_weather_col(mw2, dest_icao, "ARRIVAL", "ПРИЛЕТ", "dest")
        if altn_icao: render_weather_col(mw3, altn_icao, "ALTERNATE", "ЗАПАСНОЙ", "altn")


# --- ВКЛАДКА 2 (ЗАГОТОВКА) ---
# --- ВКЛАДКА 2: ЗАГРУЗКА ---
with tab_payload:
    st.subheader("PAYLOAD & WEIGHTS / ЗАГРУЗКА")
    
        # 1. ПАССАЖИРЫ
    st.write("**PASSENGERS / ПАССАЖИРЫ**")
    col_pax1, col_pax2, col_pax3 = st.columns(3)
    
    with col_pax1:
        # Динамический дефолт: если в самолете меньше 150 мест, ставим максимум самолета
        default_adults = min(150, selected_ac['max_pax'])
        pax_adult = st.number_input(
            "ADULTS / ВЗРОСЛЫЕ (84 kg)", 
            min_value=0, 
            max_value=selected_ac['max_pax'], 
            value=default_adults
        )
        st.caption("Взрослые")

    with col_pax2:
        # Ограничиваем детей остатком свободных мест
        remaining_seats = selected_ac['max_pax'] - pax_adult
        default_children = min(10, remaining_seats)
        pax_child = st.number_input(
            "CHILDREN / ДЕТИ (35 kg)", 
            min_value=0, 
            max_value=max(0, remaining_seats), 
            value=default_children
        )
        st.caption("Дети (2-12 лет)")

    with col_pax3:
        pax_infant = st.number_input(
            "INFANTS / МЛАДЕНЦЫ (0 kg)", 
            min_value=0, 
            max_value=50, 
            value=2
        )
        st.caption("Младенцы (0-2 года)")

    st.divider()


    # 2. БАГАЖ (Шкала 5-10-15-20)
    st.write("**BAGGAGE PER PASSENGER / БАГАЖ НА ПАССАЖИРА (kg)**")
    bag_weight_per_pax = st.select_slider(
        "Select kg per bag / Выберите кг на сумку",
        options=[5, 10, 15, 20],
        value=10
    )
    total_baggage = (pax_adult + pax_child) * bag_weight_per_pax

    st.divider()

    # 3. ГРУЗ, ПОЧТА, LOOSE LOAD
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        extra_cargo = st.number_input("EXTRA CARGO / ГРУЗ (kg)", min_value=0, value=0)
    with col_c2:
        mail = st.number_input("MAIL / ПОЧТА (kg)", min_value=0, value=0)
    with col_c3:
        loose_load = st.number_input("LOOSE LOAD (kg)", min_value=0, value=0)

    # 4. ИТОГОВЫЙ РАСЧЕТ ВЕСА
    pax_total_weight = (pax_adult * 84) + (pax_child * 35)
    total_payload = pax_total_weight + total_baggage + extra_cargo + mail + loose_load
    current_zfw = selected_ac['oew_kg'] + total_payload
    
    # Валидация (Проверка на перегруз)
    zfw_limit = selected_ac['mzfw_kg']
    is_overweight = current_zfw > zfw_limit

    st.divider()
    
    # Вывод ZFW
    if is_overweight:
        st.error(f"⚠️ ZERO FUEL WEIGHT: {current_zfw:,} KG (LIMIT EXCEEDED by {current_zfw - zfw_limit:,} kg)")
    else:
        st.metric("ZERO FUEL WEIGHT (ZFW)", f"{current_zfw:,} KG", f"Limit: {zfw_limit:,} KG")
        st.success("ZFW is within structural limits / Вес в норме")

    # Сохраняем ZFW в сессию для вкладки FUEL
    st.session_state['current_zfw'] = current_zfw


# --- ВКЛАДКА 3 (ЗАГОТОВКА) ---
with tab_fuel:
    # --- 1. CSS ДЛЯ ЗЕЛЕНОЙ КНОПКИ CALCULATE ---
    st.markdown("""
        <style>
        /* Ищем кнопку CALCULATE по тексту и красим в зеленый */
        div.stButton > button:first-child {
            background-color: #28a745 !important;
            color: white !important;
            border: none !important;
            transition: 0.3s;
        }
        div.stButton > button:first-child:hover {
            background-color: #218838 !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("FUEL PLANNING / РАСЧЕТ ТОПЛИВА")
    
    # --- 2. ОКНА ВВОДА (Input Parameters) ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        apu_fuel = st.number_input("APU FUEL", value=selected_ac.get('apu_fuel_kg', 60))
        st.caption("ВСУ (кг)")
        taxi_fuel = st.number_input("TAXI FUEL", value=selected_ac.get('taxi_fuel_kg', 200))
        st.caption("РУЛЕНИЕ (кг)")
    with col_f2:
        final_res = st.number_input("FINAL RESERVE (30 min)", value=1200)
        st.caption("ФИНАЛЬНЫЙ РЕЗЕРВ (кг)")
        captain_extra = st.number_input("CAPTAIN EXTRA", value=800)
        st.caption("ЭКСТРА КВС (кг)")

    st.divider()

    # --- 3. ANTI-ICE С ЦВЕТОВОЙ ЛОГИКОЙ ---
    st.write("**ANTI-ICE SETTINGS / ПРОТИВООБЛЕДЕНЕНИЕ**")
    col_ai1, col_ai2 = st.columns(2)
    with col_ai1:
        eng_ai = st.checkbox("ENGINE ANTI-ICE")
        if eng_ai:
            st.markdown("<p style='color:#28a745; font-weight:bold; margin-top:-15px;'>● ON / ВКЛ</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#dc3545; font-weight:bold; margin-top:-15px;'>○ OFF / ВЫКЛ</p>", unsafe_allow_html=True)
    with col_ai2:
        wing_ai = st.checkbox("WING ANTI-ICE")
        if wing_ai:
            st.markdown("<p style='color:#28a745; font-weight:bold; margin-top:-15px;'>● ON / ВКЛ</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#dc3545; font-weight:bold; margin-top:-15px;'>○ OFF / ВЫКЛ</p>", unsafe_allow_html=True)

    st.divider()

    # --- 4. ПАНЕЛЬ КНОПОК (3 в ряд) ---
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    # Кнопка CALCULATE (Зеленая через CSS)
    calculate_clicked = btn_col1.button("CALCULATE", use_container_width=True)

    # Кнопка RESET
    if btn_col2.button("RESET", use_container_width=True):
        if 'results' in st.session_state:
            del st.session_state['results']
        st.rerun()

       # Логика расчета
    if calculate_clicked:
        dist = st.session_state.get('total_dist', 0)
        altn_dist = st.session_state.get('altn_dist', 0)
        avg_wind = st.session_state.get('avg_wind', 0)
        zfw = st.session_state.get('current_zfw', selected_ac['oew_kg'])
        
        if dist == 0:
            st.error("Calculate ROUTE first! / Сначала рассчитайте маршрут!")
        else:
            # 1. Корректировка часового расхода (Anti-Ice + Вес)
            base_ff = selected_ac['fuel_burn_kgph']
            if eng_ai: base_ff *= selected_ac['eng_ai_factor']
            if wing_ai: base_ff *= selected_ac['wing_ai_factor']
            
            # Поправка на вес: +0.5% на каждые 1000 кг выше веса пустого (DOW)
            weight_penalty = 1 + ((zfw - selected_ac['oew_kg']) / 1000) * 0.005
            current_ff = base_ff * weight_penalty
            
            # 2. Расчет времени полета с учетом ветра (Ground Speed)
            # Принимаем TAS за 440 узлов
            ground_speed = 440 + avg_wind 
            if ground_speed < 200: ground_speed = 200 # Защита от нереальных значений
            
            flight_time_hours = dist / ground_speed
            
            # 3. Расчет TRIP FUEL
            trip_fuel = round(flight_time_hours * current_ff)
            
            # 4. Расчет ALTERNATE FUEL (на основе дистанции до запасного)
            # Для запасного берем чуть меньшую скорость (400) из-за низкого эшелона
            altn_time = altn_dist / 400
            alternate_fuel = round(altn_time * current_ff) + 300 # +300 кг на набор/заход
            
            # 5. Резервы и Итог (Block Fuel)
            contingency = round(trip_fuel * 0.05) # АНЗ 5%
            
            block_fuel = apu_fuel + taxi_fuel + trip_fuel + contingency + alternate_fuel + final_res + captain_extra
            
            # 6. Проверка весов
            tow = zfw + block_fuel - taxi_fuel
            law = zfw + final_res + alternate_fuel + contingency
            
            # Сохраняем всё в сессию для вывода и Loadsheet
            st.session_state['results'] = {
                'block': block_fuel,
                'trip': trip_fuel,
                'cont': contingency,
                'alt': alternate_fuel,
                'final': final_res,
                'extra': captain_extra,
                'taxiapu': taxi_fuel + apu_fuel,
                'tow': tow,
                'law': law,
                'zfw': zfw,
                'payload': total_payload,
                'pax_total': pax_adult + pax_child + pax_infant,
                'avg_wind': avg_wind
            }

            # Сохраняем в сессию
            st.session_state['results'] = {
                'block': block_fuel, 'trip': trip_fuel, 'cont': contingency,
                'alt': alternate_fuel, 'final': final_res, 'extra': captain_extra,
                'taxiapu': taxi_fuel + apu_fuel,
                'tow': zfw + block_fuel - taxi_fuel,
                'law': zfw + final_res + alternate_fuel + contingency,
                'zfw': zfw, 'payload': total_payload, 'pax_total': pax_adult + pax_child + pax_infant
            }

    # --- 5. ВЫВОД РЕЗУЛЬТАТОВ И КНОПКА LOADSHEET ---
    if st.session_state.get('results'):
        res = st.session_state['results']
        
        # Текст для LOADSHEET
        ls_text = f"""-------------------------------------------
   EDNO 1  LOADSHEET  CHECKED  APPROVED
-------------------------------------------
AIRCRAFT: {selected_ac['name']}
FROM/TO:  {dep_icao}/{dest_icao}
-------------------------------------------
ZFW: {res['zfw']:,}  (MAX: {selected_ac['mzfw_kg']:,})
TOW: {round(res['tow']):,}  (MAX: {selected_ac['mtow_kg']:,})
LAW: {round(res['law']):,}  (MAX: {selected_ac['mlw_kg']:,})
-------------------------------------------
PAX TOTAL: {res['pax_total']}
PAYLOAD:   {res['payload']:,}
BLOCK FUEL: {res['block']:,}
-------------------------------------------"""

        # Кнопка LOADSHEET становится активной в 3-й колонке
        btn_col3.download_button("LOADSHEET", data=ls_text, file_name=f"LS_{dep_icao}_{dest_icao}.txt", use_container_width=True)

        st.success(f"### BLOCK FUEL: {res['block']:,} KG")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            fuel_df = pd.DataFrame({
                "Item": ["TRIP FUEL", "CONT (5%)", "ALTN", "FINAL RES", "EXTRA", "TAXI+APU"],
                "KG": [res['trip'], res['cont'], res['alt'], res['final'], res['extra'], res['taxiapu']]
            })
            st.table(fuel_df)
            
        with r_col2:
            st.metric("TAKEOFF WEIGHT (TOW)", f"{round(res['tow']):,} kg")
            st.metric("LANDING WEIGHT (LAW)", f"{round(res['law']):,} kg")
            if res['law'] > selected_ac['mlw_kg']:
                st.error(f"LAW EXCEEDS LIMIT: {selected_ac['mlw_kg']}")

        with st.expander("VIEW LOADSHEET"):
            st.code(ls_text, language="text")
    else:
        # Если расчета нет, LOADSHEET видна, но не активна
        btn_col3.button("LOADSHEET", use_container_width=True, disabled=True)

