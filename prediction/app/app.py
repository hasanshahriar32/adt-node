import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
import os
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted

# Page configuration
st.set_page_config(
    page_title="🌾 Crop Yield Prediction Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E7D32;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Custom Model Definitions
# ==========================================

class CascadeRandomForest(ClassifierMixin, BaseEstimator):
    def __init__(self, n_layers=3, n_estimators_per_layer=50, max_depth=15, min_samples_split=5, random_state=42):
        self.n_layers = n_layers
        self.n_estimators_per_layer = n_estimators_per_layer
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.layers = []
        self.feature_importances_ = None
        self.classes_ = None
        self.n_classes_ = None
    
    def fit(self, X, y): pass
    
    def predict_proba(self, X):
        check_is_fitted(self)
        X = check_array(X)
        proba = np.zeros((X.shape[0], self.n_classes_))
        total_weight = sum([2.0 ** (len(self.layers) - i - 1) for i in range(len(self.layers))])
        for i, layer in enumerate(self.layers):
            layer_weight = (2.0 ** (len(self.layers) - i - 1)) / total_weight
            layer_proba = layer.predict_proba(X)
            layer_proba_aligned = np.zeros_like(proba)
            for cls_idx, cls in enumerate(self.classes_):
                if cls in layer.classes_:
                    class_idx_in_layer = np.where(layer.classes_ == cls)[0][0]
                    layer_proba_aligned[:, cls_idx] = layer_proba[:, class_idx_in_layer]
            proba += layer_weight * layer_proba_aligned
        proba_sum = proba.sum(axis=1, keepdims=True)
        proba_sum[proba_sum == 0] = 1
        return proba / proba_sum
    
    def predict(self, X):
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

class HierarchicalRandomForest(ClassifierMixin, BaseEstimator):
    def __init__(self, n_clusters=3, n_estimators_global=50, n_estimators_local=30, max_depth=12, random_state=42):
        self.n_clusters = n_clusters
        self.n_estimators_global = n_estimators_global
        self.n_estimators_local = n_estimators_local
        self.max_depth = max_depth
        self.random_state = random_state
        self.global_rf = None
        self.cluster_models = {}
        self.kmeans = None
        self.feature_importances_ = None
        self.classes_ = None
        self.n_classes_ = None
        
    def fit(self, X, y): pass
    
    def predict_proba(self, X):
        check_is_fitted(self)
        X = check_array(X)
        clusters = self.kmeans.predict(X)
        proba = np.zeros((X.shape[0], self.n_classes_))
        global_proba = self.global_rf.predict_proba(X)
        global_proba_aligned = np.zeros_like(proba)
        for cls_idx, cls in enumerate(self.classes_):
            if cls in self.global_rf.classes_:
                class_idx_in_global = np.where(self.global_rf.classes_ == cls)[0][0]
                global_proba_aligned[:, cls_idx] = global_proba[:, class_idx_in_global]
        proba = 0.25 * global_proba_aligned
        for cluster_id, cluster_model in self.cluster_models.items():
            cluster_mask = (clusters == cluster_id)
            if cluster_mask.sum() == 0: continue
            X_cluster = X[cluster_mask]
            cluster_proba = cluster_model.predict_proba(X_cluster)
            cluster_proba_aligned = np.zeros((len(X_cluster), self.n_classes_))
            for cls_idx, cls in enumerate(self.classes_):
                if cls in cluster_model.classes_:
                    class_idx_in_cluster = np.where(cluster_model.classes_ == cls)[0][0]
                    cluster_proba_aligned[:, cls_idx] = cluster_proba[:, class_idx_in_cluster]
            proba[cluster_mask] += 0.75 * cluster_proba_aligned
        proba_sum = proba.sum(axis=1, keepdims=True)
        proba_sum[proba_sum == 0] = 1
        return proba / proba_sum
    
    def predict(self, X):
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

# ==========================================
# Helper Functions
# ==========================================

@st.cache_resource
def load_models():
    """Load trained models and configurations"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "../output")
        
        models = {
            "Standard RF": joblib.load(os.path.join(model_dir, "standard_random_forest_model.joblib")),
            "Cascade RF": joblib.load(os.path.join(model_dir, "cascade_random_forest_model.joblib")),
            "Hierarchical RF": joblib.load(os.path.join(model_dir, "hierarchical_random_forest_model.joblib"))
        }
        config = joblib.load(os.path.join(model_dir, "model_config.joblib"))
        encoders = joblib.load(os.path.join(model_dir, "label_encoders.joblib"))
        scaler = joblib.load(os.path.join(model_dir, "scaler.joblib"))
        
        return models, config, encoders, scaler, None
    except Exception as e:
        return None, None, None, None, str(e)

def fetch_simulation_data(api_url):
    """Fetch data from simulation API"""
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API returned status code {response.status_code}"
    except requests.exceptions.Timeout:
        return None, "Request timeout - API not responding"
    except requests.exceptions.ConnectionError:
        return None, "Connection error - Is the simulation running?"
    except Exception as e:
        return None, f"Error: {str(e)}"

def prepare_features(telemetry_data, user_inputs, feature_columns):
    """Prepare feature vector from telemetry and user inputs"""
    feature_dict = {}
    
    # Map telemetry data
    if 'telemetry' in telemetry_data:
        feature_dict['Avg Temp'] = telemetry_data['telemetry'].get('temperature', 25)
        feature_dict['Avg Humidity'] = telemetry_data['telemetry'].get('humidity', 70)
        feature_dict['Soil Moisture'] = telemetry_data['telemetry'].get('soilMoisture', 35)
    
    # Add user inputs
    feature_dict.update(user_inputs)
    
    # Calculate derived features
    if 'Max Temp' in feature_dict and 'Min Temp' in feature_dict:
        feature_dict['Temp_Range'] = feature_dict['Max Temp'] - feature_dict['Min Temp']
    
    if 'Max Relative Humidity' in feature_dict and 'Min Relative Humidity' in feature_dict:
        feature_dict['Humidity_Range'] = feature_dict['Max Relative Humidity'] - feature_dict['Min Relative Humidity']
    
    if 'Avg Temp' in feature_dict and 'Avg Humidity' in feature_dict:
        feature_dict['Temp_Humidity_Index'] = feature_dict['Avg Temp'] * feature_dict['Avg Humidity'] / 100
    
    # Create DataFrame with correct column order
    df = pd.DataFrame([feature_dict])
    
    # Ensure all required columns exist
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[feature_columns]

def encode_and_scale(df, encoders, scaler, feature_columns):
    """Encode categorical variables and scale features"""
    df_processed = df.copy()
    
    # Encode categorical columns
    for col, encoder in encoders.items():
        if col in df_processed.columns:
            try:
                df_processed[col] = encoder.transform(df_processed[col].astype(str))
            except:
                df_processed[col] = 0
    
    # Scale features
    df_scaled = pd.DataFrame(
        scaler.transform(df_processed),
        columns=feature_columns
    )
    
    return df_scaled

# ==========================================
# Main Application
# ==========================================

def main():
    # Header
    st.markdown('<div class="main-header">🌾 Real-time Crop Yield Prediction Dashboard</div>', unsafe_allow_html=True)
    
    # Load models
    models, config, encoders, scaler, error = load_models()
    
    if error:
        st.error(f"❌ Error loading models: {error}")
        st.info("Please ensure the model files are present in the `prediction/output/` directory.")
        return
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Configuration")
    
    api_url = st.sidebar.text_input(
        "Simulation API Endpoint",
        value="https://adt-node.onrender.com/api/telemetry",
        help="Enter the URL of your Node-RED simulation API"
    )
    
    auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 60, 5)
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Configure farm parameters in the expandable section below the dashboard.")
    
    # Farm parameter inputs (outside the refresh loop to avoid duplicate keys)
    # Get options from encoders
    districts = list(encoders['District'].classes_) if 'District' in encoders else ['District_A']
    seasons = list(encoders['Season'].classes_) if 'Season' in encoders else ['Kharif', 'Rabi']
    
    with st.expander("⚙️ Configure Farm Parameters", expanded=False):
        st.subheader("Enter Farm Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Location & Season**")
            district = st.selectbox("District", districts, key="district_input")
            season = st.selectbox("Season", seasons, key="season_input")
            area = st.number_input("Area (Ha)", min_value=0.1, value=1.0, step=0.1, key="area_input")
            ap_ratio = st.number_input("AP Ratio", min_value=0.0, value=0.5, step=0.1, key="ap_ratio_input")
        
        with col2:
            st.markdown("**Environmental**")
            total_rainfall = st.number_input("Total Rainfall (mm)", min_value=0.0, value=800.0, step=10.0, key="rainfall_input")
            ph_level = st.number_input("pH Level", min_value=0.0, max_value=14.0, value=6.5, step=0.1, key="ph_input")
            max_temp = st.number_input("Max Temp (°C)", min_value=-10.0, max_value=50.0, value=35.0, step=0.5, key="max_temp_input")
            min_temp = st.number_input("Min Temp (°C)", min_value=-10.0, max_value=50.0, value=20.0, step=0.5, key="min_temp_input")
        
        with col3:
            st.markdown("**Production & Growth**")
            production = st.number_input("Production", min_value=0.0, value=1000.0, step=100.0, key="production_input")
            max_humidity = st.slider("Max Humidity (%)", 0, 100, 90, key="max_humidity_input")
            min_humidity = st.slider("Min Humidity (%)", 0, 100, 50, key="min_humidity_input")
        
        st.markdown("**Crop Growth Stages (days)**")
        gcol1, gcol2, gcol3 = st.columns(3)
        with gcol1:
            transplant = st.number_input("Transplant", min_value=0, value=30, step=1, key="transplant_input")
        with gcol2:
            growth = st.number_input("Growth", min_value=0, value=90, step=1, key="growth_input")
        with gcol3:
            harvest = st.number_input("Harvest", min_value=0, value=120, step=1, key="harvest_input")
    
    st.markdown("---")
    
    # Main content area
    if auto_refresh:
        # Create placeholder for dynamic content
        placeholder = st.empty()
        iteration = 0  # Counter for unique keys
        
        while True:
            iteration += 1
            with placeholder.container():
                # Fetch simulation data
                data, fetch_error = fetch_simulation_data(api_url)
                
                if fetch_error:
                    st.error(f"❌ {fetch_error}")
                    st.info("💡 Make sure your Node-RED simulation is running at the specified endpoint.")
                else:
                    # Display live telemetry
                    st.subheader("📡 Live Sensor Data")
                    
                    tel_cols = st.columns(4)
                    
                    if 'telemetry' in data:
                        tel = data['telemetry']
                        tel_cols[0].metric("🌡️ Temperature", f"{tel.get('temperature', 0):.1f} °C")
                        tel_cols[1].metric("💧 Humidity", f"{tel.get('humidity', 0):.1f} %")
                        tel_cols[2].metric("🌱 Soil Moisture", f"{tel.get('soilMoisture', 0):.1f} %")
                        tel_cols[3].metric("⏰ Last Update", datetime.now().strftime("%H:%M:%S"))
                    
                    st.markdown("---")
                    
                    # Prepare features
                    user_inputs = {
                        'Area': area,
                        'AP Ratio': ap_ratio,
                        'District': district,
                        'Season': season,
                        'Total Rainfall': total_rainfall,
                        'Production': production,
                        'Max Temp': max_temp,
                        'Min Temp': min_temp,
                        'Max Relative Humidity': max_humidity,
                        'Min Relative Humidity': min_humidity,
                        'pH Level': ph_level,
                        'Transplant': transplant,
                        'Growth': growth,
                        'Harvest': harvest
                    }
                    
                    try:
                        # Prepare and process features
                        features_df = prepare_features(data, user_inputs, config['feature_columns'])
                        features_scaled = encode_and_scale(features_df, encoders, scaler, config['feature_columns'])
                        
                        # Make predictions
                        st.subheader("🎯 Crop Yield Predictions")
                        
                        pred_cols = st.columns(len(models))
                        predictions = {}
                        
                        for idx, (model_name, model) in enumerate(models.items()):
                            with pred_cols[idx]:
                                prediction = model.predict(features_scaled)[0]
                                predictions[model_name] = prediction
                                
                                # Decode prediction if it's a class label
                                if 'Crop Name' in encoders:
                                    try:
                                        crop_name = encoders['Crop Name'].inverse_transform([prediction])[0]
                                        st.metric(model_name, crop_name)
                                    except:
                                        st.metric(model_name, f"Class {prediction}")
                                else:
                                    st.metric(model_name, f"{prediction:.2f}")
                        
                        st.markdown("---")
                        
                        # Visualization Section
                        st.subheader("📊 Analysis & Visualizations")
                        
                        viz_cols = st.columns(2)
                        
                        with viz_cols[0]:
                            # Prediction comparison chart
                            fig_pred = go.Figure(data=[
                                go.Bar(
                                    x=list(predictions.keys()),
                                    y=list(predictions.values()),
                                    marker_color=['#2E7D32', '#388E3C', '#43A047']
                                )
                            ])
                            fig_pred.update_layout(
                                title="Model Predictions Comparison",
                                xaxis_title="Model",
                                yaxis_title="Prediction",
                                height=400
                            )
                            st.plotly_chart(fig_pred, use_container_width=True, key=f"pred_chart_{iteration}")
                        
                        with viz_cols[1]:
                            # Environmental factors gauge
                            fig_env = go.Figure()
                            
                            fig_env.add_trace(go.Indicator(
                                mode="gauge+number",
                                value=tel.get('temperature', 0) if 'telemetry' in data else 0,
                                domain={'x': [0, 1], 'y': [0, 1]},
                                title={'text': "Temperature (°C)"},
                                gauge={
                                    'axis': {'range': [None, 50]},
                                    'bar': {'color': "#FF5722"},
                                    'steps': [
                                        {'range': [0, 20], 'color': "lightblue"},
                                        {'range': [20, 35], 'color': "lightgreen"},
                                        {'range': [35, 50], 'color': "lightyellow"}
                                    ]
                                }
                            ))
                            
                            fig_env.update_layout(height=400)
                            st.plotly_chart(fig_env, use_container_width=True, key=f"env_gauge_{iteration}")
                        
                        # Feature importance (if available)
                        if hasattr(models["Standard RF"], 'feature_importances_'):
                            st.subheader("🔍 Feature Importance")
                            
                            importances = models["Standard RF"].feature_importances_
                            feature_names = config['feature_columns']
                            
                            importance_df = pd.DataFrame({
                                'Feature': feature_names,
                                'Importance': importances
                            }).sort_values('Importance', ascending=False).head(10)
                            
                            fig_imp = px.bar(
                                importance_df,
                                x='Importance',
                                y='Feature',
                                orientation='h',
                                title="Top 10 Most Important Features"
                            )
                            fig_imp.update_traces(marker_color='#2E7D32')
                            st.plotly_chart(fig_imp, use_container_width=True, key=f"feature_imp_{iteration}")
                        
                        # Raw data expander
                        with st.expander("📋 View Raw Data"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.json(data)
                            with col2:
                                st.dataframe(features_df)
                    
                    except Exception as e:
                        st.error(f"❌ Prediction error: {str(e)}")
                        st.exception(e)
            
            # Wait before refresh
            time.sleep(refresh_interval)
    
    else:
        st.info("Enable 'Auto Refresh' in the sidebar to start real-time predictions.")

if __name__ == "__main__":
    main()
