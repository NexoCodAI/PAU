import streamlit as st
import json
import datetime
import os
import time
import pytz

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================

st.set_page_config(
    page_title="PAU Tracker Elite", 
    page_icon="🎓", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Constantes del Sistema
FILE_NAME = "pau_ultimate_data.json"
MIN_MINUTES_PER_TASK = 40  # Mínimo tiempo productivo por tarea (Técnica Pomodoro)

# Estilos CSS Personalizados para modo Dark/Elite
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}
    div[data-testid="stMetricValue"] { font-size: 2.2rem; color: #ff4b4b; font-weight: 700;}
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; }
    .css-1d391kg { padding-top: 1rem; }
    div.stProgress > div > div > div > div { background-color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DATOS (SYLLABUS)
# ==========================================

# Datos extraídos del PDF y la Guía Maestra
DEFAULT_SYLLABUS = {
    "Matemáticas II": {
        "category": "science",
        "topics": ["Matrices", "Rango e Inversa", "Determinantes", "Sistemas (Rouché)", "Límites & Continuidad", "Derivadas", "Optimización", "Integrales Indef.", "Integrales Def.", "Geo: Rectas y Planos", "Geo: Métrico", "Probabilidad Total", "Binomial/Normal"]
    },
    "Física": {
        "category": "science",
        "topics": ["Campo Gravitatorio", "Campo Eléctrico", "Campo Magnético", "Inducción EM", "Ondas Mecánicas", "Ondas Sonoras", "Óptica Geométrica", "Física Relativista", "Física Cuántica", "Física Nuclear"]
    },
    "Química": {
        "category": "science",
        "topics": ["Estructura Atómica", "Sistema Periódico", "Enlace Químico", "Cinética Química", "Equilibrio Químico", "Ácido-Base", "Redox", "Química del Carbono"]
    },
    "Tecnología e Ing.": {
        "category": "science",
        "topics": ["Materiales", "Diagramas de Fase", "Máquinas Térmicas", "Motores", "Neumática e Hidráulica", "Sistemas Automáticos", "Electrónica Digital"]
    },
    "Historia de España": {
        "category": "memory",
        "topics": ["Raíces Hcas", "Crisis A.R. (1808-1833)", "Estado Liberal (1833-1874)", "Restauración (1875-1902)", "Alfonso XIII (1902-1931)", "II República", "Guerra Civil", "Franquismo", "Transición"]
    },
    "Hª Filosofía": {
        "category": "memory",
        "topics": ["Platón: Ideas", "Platón: Política", "Aristóteles", "Tomás de Aquino", "Descartes", "Hume", "Rousseau", "Kant: Conocimiento", "Kant: Ética", "Marx", "Nietzsche", "Ortega y Gasset"]
    },
    "Inglés": {
        "category": "skills",
        "topics": ["Tenses Mix", "Passive Voice", "Reported Speech", "Conditionals", "Modals", "Relative Clauses", "Writing: Opinion", "Writing: For/Against"]
    }
}

# ==========================================
# 3. GESTIÓN DE DATOS (JSON)
# ==========================================

def load_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return create_defaults()
    else:
        return create_defaults()

def create_defaults():
    new_data = {}
    for subject, info in DEFAULT_SYLLABUS.items():
        new_data[subject] = []
        for topic in info["topics"]:
            new_data[subject].append({
                "name": topic,
                "category": info["category"],
                "unlocked": False,       # True = Visto en clase
                "level": 0,              # 0-5
                "next_review": str(datetime.date.today()),
                "last_error": "",
                "extra_queue": False     # Urgencia manual
            })
    return new_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 4. FUNCIONES VISUALES (RELOJ)
# ==========================================

def show_modern_clock(target_hour_float):
    """
    Muestra una cuenta atrás JS visualmente atractiva hasta la hora decimal indicada.
    """
    if target_hour_float == 0:
        return # No mostrar reloj en tiempo libre

    # Convertir hora decimal (ej. 17.5) a horas y minutos (17:30)
    th = int(target_hour_float)
    tm = int((target_hour_float - th) * 60)

    # HTML y JS inyectado para el reloj
    clock_html = f"""
    <div class="clock-container">
        <div class="clock-label">TIEMPO RESTANTE DE BLOQUE</div>
        <div id="countdown" class="clock-time">--:--:--</div>
        <div class="clock-target">Objetivo: {th:02d}:{tm:02d}</div>
    </div>

    <script>
    (function() {{
        var targetHour = {th};
        var targetMin = {tm};
        
        function updateTimer() {{
            var now = new Date();
            var target = new Date();
            target.setHours(targetHour, targetMin, 0, 0);
            
            // Si la hora objetivo es mañana (ej. madrugada), ajustar fecha (opcional, aquí asumimos mismo día)
            
            var diff = target - now;
            
            if (diff <= 0) {{
                var el = document.getElementById("countdown");
                if(el) {{
                    el.innerHTML = "00:00:00";
                    el.style.color = "#555";
                }}
                return;
            }}
            
            var hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((diff % (1000 * 60)) / 1000);
            
            hours = (hours < 10) ? "0" + hours : hours;
            minutes = (minutes < 10) ? "0" + minutes : minutes;
            seconds = (seconds < 10) ? "0" + seconds : seconds;
            
            var el = document.getElementById("countdown");
            if(el) el.innerHTML = hours + ":" + minutes + ":" + seconds;
        }}
        
        setInterval(updateTimer, 1000);
        updateTimer();
    }})();
    </script>
    
    <style>
    .clock-container {{
        background-color: #0e1117;
        border: 1px solid #ff4b4b;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 0 10px rgba(255, 75, 75, 0.15);
    }}
    .clock-label {{
        color: #aaa;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }}
    .clock-time {{
        font-family: 'Courier New', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #ff4b4b;
        text-shadow: 0 0 8px rgba(255, 75, 75, 0.4);
    }}
    .clock-target {{
        color: #666;
        font-size: 0.85rem;
        margin-top: 5px;
    }}
    </style>
    """
    st.sidebar.markdown(clock_html, unsafe_allow_html=True)

# ==========================================
# 5. LÓGICA DE HORARIO (CORREGIDA & UPDATED)
# ==========================================

def get_current_block():
    """
    Define qué toca estudiar según el día y la hora.
    Basado estrictamente en las tablas del PDF.
    Devuelve: tipo, nombre, duración, hora_fin (decimal)
    """
    
    # --- CORRECCIÓN ZONA HORARIA ---
    madrid_tz = pytz.timezone('Europe/Madrid')
    now = datetime.datetime.now(madrid_tz) 
    # -------------------------------

    weekday = now.weekday() # 0=Lunes ... 6=Domingo
    hour = now.hour + now.minute / 60.0

    # MIÉRCOLES (2)
    if weekday in [2]:
        if 16.0 <= hour < 17.5: return "science", "🔄 Tareas diarias", 90, 17.5
        if 17.5 <= hour < 19.0: return "gym", "🏋️ Gimnasio / Reset", 90, 19.0
        if 19.0 <= hour < 20.5: return "science", "🧪 Bloque Ciencia", 90, 20.5
        if 20.5 <= hour < 21.0: return "break", "🚿 Ducha", 30, 21.0
        if 21.0 <= hour < 21.5: return "break", "🥗 Cena (Sin Pantallas)", 30, 21.5
        if 21.5 <= hour < 23.0: return "memory", "🧠 Bloque Memoria (Gold)", 90, 23.0
        if hour > 23.0: return "sleep", "😴 DORMIR (Sagrado)", 0, 0

    # LUNES (0), MARTES (1) Y JUEVES (3) 
    elif weekday in [0, 1, 3]:
        # ¡OJO! Aquí es donde estaba tu problema. Martes empieza 15:30.
        if 15.5 <= hour < 17.0: return "science", "🔄 Tareas diarias", 90, 17.0
        if 17.0 <= hour < 18.5: return "gym", "🏋️ Gimnasio / Reset", 90, 18.5
        if 18.5 <= hour < 20.0: return "science", "🧪 Bloque Ciencia", 90, 20.0
        if 20.0 <= hour < 20.5: return "mix", "Buffer / Inglés/ Tareas diarias", 30, 20.5
        if 20.5 <= hour < 21.0: return "break", "Ducha", 30, 21.0
        if 21.0 <= hour < 21.5: return "break", "🥗 Cena", 30, 21.5
        if 21.5 <= hour < 23.0: return "memory", "🧠 Bloque Memoria (Gold)", 90, 23.0
        if hour >= 23.0: return "sleep", "😴 DORMIR (Sagrado)", 0, 0

    # VIERNES (4) - Buffer y Repaso
    elif weekday == 4:
        if 16.0 <= hour < 20.0: return "mix", "🔄 Repaso Buffer/ Tareas / Inglés", 240, 20.0
    
    # SÁBADO (5) - Simulacro
    elif weekday == 5:
        if 9.5 <= hour < 13.5: return "simulacro", "📝 SIMULACRO REAL EXAMEN", 240, 13.5
        if hour >= 14.0: return "free", "🎉 Tarde Libre", 0, 0
    
    # DOMINGO (6) - Planificación
    elif weekday == 6:
        if 18.0 <= hour < 20.0: return "review", "📅 Planificación + Cuaderno Errores", 120, 20.0

    return "free", "⏳ Tiempo Libre / Buffer", 0, 0

# ==========================================
# 6. INTERFAZ Y LÓGICA PRINCIPAL
# ==========================================

# Cargar estado
if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
# Recuperamos los 4 valores (incluyendo la hora de fin para el reloj)
real_type, block_name, duration, end_hour = get_current_block()

# --- SIDEBAR ---
with st.sidebar:
    st.title("PAU TRACKER")
    
    # RELOJ MODERNO INTEGRADO
    show_modern_clock(end_hour)
    
    st.markdown("### Estado Actual")
    
    # Checkbox para saltarse el descanso si es necesario
    force_study = st.checkbox("🔥 MODO INTENSO (Ignorar Descansos)", value=False)
    
    # Muestra el bloque actual
    st.info(f"**{block_name}**")
    if duration > 0:
        st.metric("Tiempo Bloque", f"{duration} min")
    else:
        st.caption("Fuera de horario lectivo.")
        
    st.divider()
    
    # Estadísticas rápidas
    total_unlocked = sum(1 for s in data for t in data[s] if t["unlocked"])
    st.write(f"📈 Temas activos: **{total_unlocked}**")

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Agenda", "📚 Temario", "📓 Errores", "⚙️ Ajustes"])

# ==========================================
# TAB 1: AGENDA INTELIGENTE (TIME BOXING)
# ==========================================
with tab1:
    st.header(f"Plan de Acción: {block_name}")
    
    # Lógica de tipo de bloque
    if force_study and real_type in ["gym", "break", "free", "sleep"]:
        target_type = "mix" # Si forzamos estudio en descanso, mostramos mezcla
        st.warning("⚠️ Saltándose la recuperación. Úsalo con cuidado.")
    else:
        target_type = real_type

    # Si es hora de descanso/gym y NO estamos forzando estudio
    if target_type in ["gym", "break", "sleep", "free"]:
        st.success(f"🛑 **STOP.** Toca recuperar energía.")
        st.markdown(f"### Actividad: {block_name}")
        st.markdown("> *El descanso es parte del entrenamiento. Desconecta para rendir luego.*")
    
    elif target_type == "review":
        st.info("📅 **Domingo:** Revisa la pestaña '📓 Errores' y planifica la semana.")

    else:
        # 1. FILTRADO DE TAREAS
        tasks = []
        today_date = datetime.date.today()
        today_str = str(today_date)
        
        for subj, topic_list in data.items():
            for i, topic in enumerate(topic_list):
                # A. ¿Está activo y 'caducado' o marcado urgente?
                is_due = (topic["next_review"] <= today_str) or topic["extra_queue"]
                
                # B. ¿Encaja en el bloque actual? (Ciencia vs Memoria)
                match_category = False
                if target_type in ["simulacro", "mix"]: 
                    match_category = True
                elif target_type == "science" and (topic["category"] in ["science", "skills"]): 
                    match_category = True # Inglés se puede meter en huecos de ciencia
                elif target_type == "memory" and topic["category"] == "memory": 
                    match_category = True
                
                if topic["unlocked"] and is_due and match_category:
                    # Calcular días de retraso para priorizar
                    due_date = datetime.datetime.strptime(topic["next_review"], "%Y-%m-%d").date()
                    days_overdue = (today_date - due_date).days
                    
                    tasks.append({
                        "subj": subj, 
                        "topic": topic, 
                        "idx": i,
                        "days_overdue": days_overdue
                    })

        # 2. ORDENACIÓN INTELIGENTE
        # Prioridad: 1. Urgente Manual (Fuego) -> 2. Más retraso -> 3. Más difícil (Nivel bajo)
        tasks.sort(key=lambda x: (not x["topic"]["extra_queue"], -x["days_overdue"], x["topic"]["level"]))

        # 3. TIME BOXING (SOLUCIÓN A LAS 19 TAREAS)
        # Calculamos cuántas tareas caben REALMENTE en el tiempo disponible
        if duration > 0:
            max_tasks_fit = int(duration / MIN_MINUTES_PER_TASK) # Ej: 90 / 25 = 3 tareas
            if max_tasks_fit < 1: max_tasks_fit = 1
        else:
            max_tasks_fit = 5 # Default si no hay tiempo definido

        total_pending = len(tasks)
        selected_tasks = tasks[:max_tasks_fit] # CORTAMOS LA LISTA
        hidden_tasks = total_pending - len(selected_tasks)

        # 4. VISUALIZACIÓN
        if not selected_tasks:
            st.success("✅ **¡Todo limpio!** No tienes tareas pendientes para este bloque.")
            st.markdown("Aprovecha para adelantar materia nueva en la pestaña **Temario**.")
        else:
            # Calcular tiempo real por tarea seleccionada
            real_time_per_task = int(duration / len(selected_tasks)) if duration > 0 else 30
            
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Objetivo Hoy", f"{len(selected_tasks)} Tareas", help="Tareas seleccionadas por prioridad")
            c2.metric("Tiempo / Tarea", f"{real_time_per_task} min", help="Tiempo enfocado por tema")
            c3.metric("Backlog", f"+{hidden_tasks}", delta_color="off", help="Tareas pendientes ocultas por falta de tiempo")

            st.progress(0, text="Progreso de la sesión")
            st.divider()

            for t in selected_tasks:
                subj = t["subj"]
                idx = t["idx"]
                topic = t["topic"]
                
                # Renderizar Tarjeta
                with st.container(border=True):
                    col_det, col_acc = st.columns([0.7, 0.3])
                    
                    with col_det:
                        # Etiquetas
                        badges = []
                        if topic["extra_queue"]: badges.append("🔥 URGENTE")
                        if t["days_overdue"] > 5: badges.append("💀 RETRASADO")
                        if topic["level"] < 2: badges.append("🐸 DIFÍCIL") # Eat the frog
                        
                        st.caption(f"{' '.join(badges)} • {subj}")
                        st.subheader(topic["name"])
                        st.write(f"Dominio: {topic['level']}/5")
                        st.progress(topic['level']/5)
                        
                        if topic["last_error"]:
                            st.error(f"⚠️ Ojo al fallo anterior: {topic['last_error']}")

                    with col_acc:
                        st.write("**Evaluación**")
                        b1, b2, b3 = st.columns(3)
                        
                        # Botones de Algoritmo (Spaced Repetition)
                        if b1.button("✅", key=f"ok_{subj}_{idx}", help="Bien (+Nivel)"):
                            topic["level"] = min(topic["level"] + 1, 5)
                            days = (topic["level"] * 5) + 3 
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                            topic["extra_queue"] = False
                            save_data(st.session_state.data)
                            st.rerun()

                        if b2.button("🆗", key=f"mid_{subj}_{idx}", help="Normal (Repetir pronto)"):
                            days = 3
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                            topic["extra_queue"] = False
                            save_data(st.session_state.data)
                            st.rerun()
                        
                        if b3.button("❌", key=f"bad_{subj}_{idx}", help="Mal (Reiniciar)"):
                            st.session_state[f"fail_{subj}_{idx}"] = True
                            topic["level"] = 1
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=1))
                            save_data(st.session_state.data)
                            st.rerun()
                    
                    # Si falló, pedir detalle para el Cuaderno de Errores
                    if st.session_state.get(f"fail_{subj}_{idx}", False):
                        with st.form(key=f"frm_{subj}_{idx}"):
                            st.markdown("📉 **Registro de Fallo**")
                            err_txt = st.text_input("¿Qué falló exactamente? (Cálculo, concepto, olvido...)")
                            if st.form_submit_button("Guardar en Cuaderno de Errores"):
                                topic["last_error"] = err_txt
                                del st.session_state[f"fail_{subj}_{idx}"]
                                save_data(st.session_state.data)
                                st.success("Guardado.")
                                st.rerun()

# ==========================================
# TAB 2: GESTIÓN DE TEMARIO
# ==========================================
with tab2:
    st.header("📚 Temario (Syllabus)")
    st.info("Marca las casillas ✅ cuando des un tema en clase para activarlo en el algoritmo.")
    
    col_search, _ = st.columns([0.8, 0.2])
    query = col_search.text_input("🔍 Buscar tema...")

    for subj in data:
        with st.expander(f"**{subj}**"):
            # Input añadir tema manual
            c_input, c_btn = st.columns([0.8, 0.2])
            new_top = c_input.text_input(f"Añadir tema a {subj}", key=f"new_{subj}")
            if c_btn.button("➕", key=f"add_{subj}") and new_top:
                data[subj].append({
                    "name": new_top, "category": data[subj][0]["category"], 
                    "unlocked": True, "level": 0, "next_review": str(datetime.date.today()), 
                    "last_error": "", "extra_queue": True
                })
                save_data(data)
                st.rerun()
            
            st.divider()
            
            # Lista de temas
            for i, topic in enumerate(data[subj]):
                if query.lower() in topic["name"].lower():
                    cols = st.columns([0.1, 0.6, 0.2, 0.1])
                    
                    # Checkbox desbloqueo
                    act = cols[0].checkbox("", value=topic["unlocked"], key=f"chk_{subj}_{i}")
                    if act != topic["unlocked"]:
                        topic["unlocked"] = act
                        if act: topic["next_review"] = str(datetime.date.today())
                        save_data(data)
                        st.rerun()
                    
                    cols[1].write(topic["name"])
                    cols[2].caption(f"Nv. {topic['level']}")
                    
                    # Toggle Fuego (Urgencia)
                    urg = cols[3].toggle("🔥", value=topic["extra_queue"], key=f"urg_{subj}_{i}")
                    if urg != topic["extra_queue"]:
                        topic["extra_queue"] = urg
                        save_data(data)
                        st.rerun()

# ==========================================
# TAB 3: CUADERNO DE ERRORES
# ==========================================
with tab3:
    st.header("📓 Cuaderno de Errores")
    st.markdown("Los domingos, repasa esta lista. Si entiendes el error y sabes solucionarlo, bórralo.")
    
    has_errors = False
    for subj, topic_list in data.items():
        err_topics = [t for t in topic_list if t["last_error"]]
        if err_topics:
            has_errors = True
            st.subheader(subj)
            for t in err_topics:
                with st.container(border=True):
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        st.markdown(f"**{t['name']}**")
                        st.error(f"❌ {t['last_error']}")
                    with c2:
                        if st.button("🗑️", key=f"del_err_{t['name']}", help="Borrar error (Superado)"):
                            t["last_error"] = ""
                            save_data(data)
                            st.rerun()
    
    if not has_errors:
        st.success("¡Cuaderno limpio! Buen trabajo.")

# ==========================================
# TAB 4: CONFIGURACIÓN
# ==========================================
with tab4:
    st.header("⚙️ Configuración")
    
    with st.expander("Gestionar Asignaturas"):
        n_subj = st.text_input("Nueva Asignatura")
        n_cat = st.selectbox("Categoría", ["science", "memory", "skills"])
        if st.button("Crear Asignatura"):
            if n_subj and n_subj not in data:
                data[n_subj] = [{"name": "Tema 1", "category": n_cat, "unlocked": True, "level": 0, "next_review": str(datetime.date.today()), "last_error": "", "extra_queue": False}]
                save_data(data)
                st.rerun()
                
        st.divider()
        d_subj = st.selectbox("Borrar Asignatura", list(data.keys()))
        if st.button("🗑️ Eliminar Asignatura"):
            del data[d_subj]
            save_data(data)
            st.rerun()

    st.markdown("---")
    if st.button("☠️ RESET TOTAL (Borrar todos los datos)"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        st.session_state.clear()
        st.rerun()
