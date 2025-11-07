import os
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# -----------------------------------------------------------
# 1️⃣ APP CONFIGURATION
# -----------------------------------------------------------
st.set_page_config(page_title="Fish Pond Water Quality Monitor", layout="wide")
st.title("🐟 Fish Pond Water Quality Monitoring System")

st.sidebar.header("📍 Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Farmer Input", "Evaluation"])

# -----------------------------------------------------------
# 2️⃣ LOAD DATASET (robust)
# -----------------------------------------------------------
@st.cache_data
def load_data():
    """Try several candidate locations for the dataset.
    If none are found, show a warning and return an empty DataFrame
    with the columns the dashboard expects to avoid crashing.
    """
    candidates = [
        "water.csv",
        os.path.join("data", "water.csv"),
        os.path.join(os.path.dirname(__file__), "data", "water.csv"),
        os.path.join(os.path.dirname(__file__), "water.csv"),
    ]

    for p in candidates:
        if p and os.path.exists(p):
            try:
                df = pd.read_csv(p)
                return df
            except Exception as e:
                st.error(f"Found dataset at {p} but failed to read it: {e}")
                return pd.DataFrame()

    # No dataset found — inform the user and return an empty DataFrame with expected columns
    st.warning(
        "Dataset file not found. Place 'water_potability.csv' in the project root or 'data/water.csv'. "
        "Dashboard will show an empty dataset until a file is added."
    )
    columns = ["ph", "Temperature", "Dissolved_Oxygen", "Ammonia"]
    return pd.DataFrame(columns=columns)


df = load_data()

# Map friendly display names to DataFrame column names (datasets often use different keys)
DISPLAY_TO_DF = {
    "pH": "ph",
    "Temperature": "Temperature",
    "Dissolved Oxygen": "Dissolved_Oxygen",
    "Ammonia": "Ammonia",
}

# -----------------------------------------------------------
# 3️⃣ DASHBOARD SECTION
# -----------------------------------------------------------
if page == "Dashboard":
    st.subheader("📊 Pond Water Quality Dashboard")
    st.write("This dashboard visualizes water quality parameters affecting fish health.")

    st.write("### Dataset Summary")
    st.dataframe(df.describe())

    # Parameter selection for visualization
    parameter = st.selectbox(
        "Select parameter to visualize",
        list(DISPLAY_TO_DF.keys())
    )

    col1, col2 = st.columns(2)

    with col1:
        # Histogram
        # Histogram (only plot if there is data)
        df_col = DISPLAY_TO_DF.get(parameter, parameter)
        if df_col not in df.columns or df[df_col].dropna().empty:
            st.info(f"No data available yet for {parameter} — add readings to see the distribution.")
        else:
            fig, ax = plt.subplots()
            ax.hist(df[df_col].dropna(), bins=20, color="skyblue", edgecolor="black")
            ax.set_title(f"{parameter} Distribution")
            ax.set_xlabel(parameter)
            ax.set_ylabel("Frequency")
            st.pyplot(fig)

    with col2:
        # Box plot for the same parameter (only plot if there is data)
        df_col = DISPLAY_TO_DF.get(parameter, parameter)
        if df_col not in df.columns or df[df_col].dropna().empty:
            st.info(f"No data available yet for {parameter} — add readings to see the box plot.")
        else:
            fig_box = px.box(df, y=df_col, title=f"{parameter} Variation (Box Plot)", color_discrete_sequence=["teal"])
            st.plotly_chart(fig_box, use_container_width=True)

    st.success("✅ Dashboard loaded successfully!")

# -----------------------------------------------------------
# 4️⃣ FARMER INPUT SECTION
# -----------------------------------------------------------
elif page == "Farmer Input":
    st.subheader("🧑‍🌾 Enter Pond Water Details")

    with st.form("farmer_form"):
        temp = st.number_input("🌡 Temperature (°C)", min_value=0.0, max_value=50.0, step=0.1)
        do = st.number_input("💧 Dissolved Oxygen (mg/L)", min_value=0.0, max_value=15.0, step=0.1)
        ammonia = st.number_input("🧪 Ammonia (mg/L)", min_value=0.0, max_value=5.0, step=0.01)
        ph = st.number_input("⚗️ pH Level", min_value=0.0, max_value=14.0, step=0.1)

        submitted = st.form_submit_button("Analyze Pond Water")

    if submitted:
        # Use display-friendly keys that match evaluation safe_ranges (e.g. 'Dissolved Oxygen')
        st.session_state["inputs"] = {"Temperature": temp, "Dissolved Oxygen": do, "Ammonia": ammonia, "pH": ph}
        st.success("✅ Data submitted successfully! Go to 'Evaluation' to see results.")
        st.balloons()

# -----------------------------------------------------------
# 5️⃣ AUTOMATIC WATER QUALITY EVALUATION
# -----------------------------------------------------------
elif page == "Evaluation":
    st.subheader("🤖 Automatic Water Quality Evaluation")

    if "inputs" not in st.session_state:
        st.warning("Please enter data in the 'Farmer Input' section first.")
    else:
        data = st.session_state["inputs"]

        st.write("### Entered Data")
        st.write(pd.DataFrame([data]))

        # Safe range definitions
        safe_ranges = {
            "Temperature": (25, 30),
            "Dissolved Oxygen": (5, 10),
            "pH": (6.5, 8.5),
            "Ammonia": (0, 0.05)
        }

        # Check function
        def check_status(param, value):
            low, high = safe_ranges[param]
            if param == "Ammonia":
                if value <= high:
                    return "Safe"
                elif value <= 0.1:
                    return "Risky"
                else:
                    return "Unsafe"
            elif value < low:
                return "Low"
            elif value > high:
                return "High"
            else:
                return "Safe"

        status = {param: check_status(param, val) for param, val in data.items()}

        # Convert to DataFrame for visualization
        df_eval = pd.DataFrame({
            "Parameter": list(data.keys()),
            "Value": list(data.values()),
            "Status": list(status.values())
        })

        # ------------------------------
        # PIE CHART (SAFE vs UNSAFE)
        # ------------------------------
        st.subheader("📈 Interactive Water Quality Dashboard")

        status_counts = df_eval["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig_pie = px.pie(
            status_counts,
            names="Status",
            values="Count",
            title="Pond Condition Status",
            color="Status",
            color_discrete_map={
                "Safe": "green",
                "Low": "orange",
                "High": "red",
                "Risky": "orange",
                "Unsafe": "red"
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # ------------------------------
        # BAR CHART (VALUES vs IDEAL RANGE)
        # ------------------------------
        ideal_min = [safe_ranges[p][0] for p in df_eval["Parameter"]]
        ideal_max = [safe_ranges[p][1] for p in df_eval["Parameter"]]

        df_eval["Ideal Min"] = ideal_min
        df_eval["Ideal Max"] = ideal_max

        fig_bar = px.bar(
            df_eval,
            x="Parameter",
            y="Value",
            color="Status",
            text_auto=True,
            title="Parameter Comparison with Ideal Range",
            color_discrete_map={
                "Safe": "green",
                "Low": "orange",
                "High": "red",
                "Risky": "orange",
                "Unsafe": "red"
            }
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ------------------------------
        # RECOMMENDATIONS SECTION
        # ------------------------------
        st.subheader("🧠 Recommendations & Analysis")

        for param, s in status.items():
            val = data[param]
            if s == "Safe":
                st.success(f"✅ {param} = {val} → Within safe range.")
            elif s in ["Low", "Risky"]:
                st.warning(f"⚠ {param} = {val} → Slightly out of range. Check soon.")
            else:
                st.error(f"❌ {param} = {val} → Unsafe! Immediate action needed.")

        # Final verdict
        if all(s == "Safe" for s in status.values()):
            st.success("🌿 Excellent! Water is healthy for fish.")
        else:
            st.error("🚨 Water is not suitable. Please follow the recommendations above.")
