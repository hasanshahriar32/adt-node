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
# Crop Image Mapping
# ==========================================

def get_crop_image_url(crop_name):
    """
    Generate image URL for crop using Bing's thumbnail service.
    This ensures a valid image is always returned based on the crop name.
    """
    # Mapping for better search terms to ensure accurate images
    search_term_map = {
        'karala': 'bitter gourd vegetable',
        'palong shak': 'spinach vegetable',
        'puishak': 'malabar spinach',
        'maize 1': 'maize corn cob',
        'betelnut': 'areca nut fruit',
        'jambura': 'pomelo fruit',
        'black berry': 'blackberry fruit',
        'ladies finger': 'okra vegetable',
        'brinjal': 'eggplant vegetable',
        'red amaranth': 'red amaranth plant',
        'data shak': 'amaranth greens',
        'kolmi shak': 'water spinach',
        'khesari': 'grass pea',
        'maskalai': 'black gram',
        'mug': 'mung bean',
        'arhar': 'pigeon pea',
        'felon': 'yardlong bean',
        'motor': 'pea plant',
        'sugarcane': 'sugarcane plant',
        'jute': 'jute plant',
        'cotton': 'cotton plant',
        'tobacco': 'tobacco plant',
        'tea': 'tea garden',
        'paddy': 'rice paddy',
        'boro rice': 'rice paddy',
        'aman rice': 'rice paddy',
        'aus rice': 'rice paddy',
        'wheat': 'wheat field',
        'mustard': 'mustard flower field',
        'sesame': 'sesame plant',
        'linseed': 'flax plant',
        'sunflower': 'sunflower field',
        'potato': 'potato plant',
        'sweet potato': 'sweet potato plant',
        'turmeric': 'turmeric plant',
        'ginger': 'ginger plant',
        'onion': 'onion bulb',
        'garlic': 'garlic bulb',
        'chili': 'green chili plant',
        'coriander': 'coriander plant',
        'mint': 'mint plant',
        'banana': 'banana tree',
        'mango': 'mango fruit',
        'jackfruit': 'jackfruit tree',
        'papaya': 'papaya fruit',
        'guava': 'guava fruit',
        'lemon': 'lemon fruit',
        'lime': 'lime fruit',
        'pomelo': 'pomelo fruit',
        'orange': 'orange fruit',
        'pineapple': 'pineapple plant',
        'watermelon': 'watermelon field',
        'melon': 'melon fruit',
        'litchi': 'lychee fruit',
        'coconut': 'coconut tree',
        'betel leaf': 'betel leaf plant',
        'rubber': 'rubber tree',
        'bamboo': 'bamboo forest'
    }
    
    # Normalize
    crop_lower = crop_name.lower().strip()
    
    # Get better search term if available, otherwise use the name itself
    query = search_term_map.get(crop_lower, crop_lower)
    
    # Add 'crop' context if not present to avoid generic results
    if 'plant' not in query and 'fruit' not in query and 'tree' not in query and 'field' not in query and 'vegetable' not in query:
        query += " crop"
        
    # URL encode the query
    query_encoded = query.replace(' ', '+')
    
    # Use Bing Thumbnail API (reliable, no key required for low volume)
    return f"https://tse2.mm.bing.net/th?q={query_encoded}&w=200&h=150&c=7&rs=1&p=0"

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
                        
                        # Make predictions with confidence scores
                        st.subheader("🎯 Crop Yield Predictions")
                        
                        pred_cols = st.columns(len(models))
                        predictions = {}
                        prediction_probas = {}
                        
                        for idx, (model_name, model) in enumerate(models.items()):
                            with pred_cols[idx]:
                                prediction = model.predict(features_scaled)[0]
                                proba = model.predict_proba(features_scaled)[0]
                                predictions[model_name] = prediction
                                prediction_probas[model_name] = proba
                                
                                # Decode prediction if it's a class label
                                if 'Crop Name' in encoders:
                                    try:
                                        crop_name = encoders['Crop Name'].inverse_transform([prediction])[0]
                                        confidence = proba[prediction] * 100
                                        
                                        # Show crop image
                                        img_url = get_crop_image_url(crop_name)
                                        st.image(img_url, use_column_width=True)
                                        
                                        st.metric(model_name, crop_name, f"{confidence:.1f}% confidence")
                                    except:
                                        st.metric(model_name, f"Class {prediction}")
                                else:
                                    st.metric(model_name, f"{prediction:.2f}")
                        
                        # Show top 5 predictions for each model with images
                        st.markdown("---")
                        st.subheader("🔝 Top 5 Crop Recommendations (by model)")
                        
                        top_pred_cols = st.columns(len(models))
                        
                        for idx, (model_name, proba) in enumerate(prediction_probas.items()):
                            with top_pred_cols[idx]:
                                st.markdown(f"**{model_name}**")
                                top_5_indices = np.argsort(proba)[-5:][::-1]
                                
                                if 'Crop Name' in encoders:
                                    for rank, class_idx in enumerate(top_5_indices, 1):
                                        try:
                                            crop_name = encoders['Crop Name'].inverse_transform([class_idx])[0]
                                            confidence = proba[class_idx] * 100
                                            
                                            # Create a container for each crop
                                            with st.container():
                                                col1, col2 = st.columns([1, 2])
                                                with col1:
                                                    # Show crop image
                                                    img_url = get_crop_image_url(crop_name)
                                                    st.image(img_url, width=80)
                                                with col2:
                                                    st.markdown(f"**{rank}. {crop_name}**")
                                                    st.progress(confidence / 100)
                                                    st.caption(f"{confidence:.1f}% confidence")
                                        except:
                                            st.write(f"{rank}. Class {class_idx}: {proba[class_idx]*100:.1f}%")
                        
                        st.markdown("---")
                        
                        # Visualization Section
                        st.subheader("📊 Analysis & Visualizations")
                        
                        viz_cols = st.columns(2)
                        
                        with viz_cols[0]:
                            # Confidence comparison across models
                            fig_conf = go.Figure()
                            
                            for model_name, proba in prediction_probas.items():
                                pred_idx = predictions[model_name]
                                confidence = proba[pred_idx] * 100
                                
                                fig_conf.add_trace(go.Bar(
                                    x=[model_name],
                                    y=[confidence],
                                    name=model_name,
                                    text=[f"{confidence:.1f}%"],
                                    textposition='auto',
                                ))
                            
                            fig_conf.update_layout(
                                title="Model Confidence Comparison",
                                xaxis_title="Model",
                                yaxis_title="Confidence (%)",
                                yaxis_range=[0, 100],
                                height=400,
                                showlegend=False
                            )
                            st.plotly_chart(fig_conf, use_container_width=True, key=f"conf_chart_{iteration}")
                        
                        with viz_cols[1]:
                            # Environmental factors gauge - Temperature
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
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': 40
                                    }
                                }
                            ))
                            
                            fig_env.update_layout(height=400)
                            st.plotly_chart(fig_env, use_container_width=True, key=f"env_gauge_{iteration}")
                        
                        # Additional environmental gauges
                        env_cols = st.columns(3)
                        
                        with env_cols[0]:
                            # Humidity gauge
                            fig_hum = go.Figure(go.Indicator(
                                mode="gauge+number+delta",
                                value=tel.get('humidity', 0) if 'telemetry' in data else 0,
                                delta={'reference': 60},
                                title={'text': "Humidity (%)"},
                                gauge={
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "#2196F3"},
                                    'steps': [
                                        {'range': [0, 40], 'color': "lightyellow"},
                                        {'range': [40, 70], 'color': "lightgreen"},
                                        {'range': [70, 100], 'color': "lightblue"}
                                    ]
                                }
                            ))
                            fig_hum.update_layout(height=300)
                            st.plotly_chart(fig_hum, use_container_width=True, key=f"hum_gauge_{iteration}")
                        
                        with env_cols[1]:
                            # Soil Moisture gauge
                            fig_soil = go.Figure(go.Indicator(
                                mode="gauge+number+delta",
                                value=tel.get('soilMoisture', 0) if 'telemetry' in data else 0,
                                delta={'reference': 50},
                                title={'text': "Soil Moisture (%)"},
                                gauge={
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "#8D6E63"},
                                    'steps': [
                                        {'range': [0, 30], 'color': "#FFCCBC"},
                                        {'range': [30, 60], 'color': "#A1887F"},
                                        {'range': [60, 100], 'color': "#6D4C41"}
                                    ]
                                }
                            ))
                            fig_soil.update_layout(height=300)
                            st.plotly_chart(fig_soil, use_container_width=True, key=f"soil_gauge_{iteration}")
                        
                        with env_cols[2]:
                            # Prediction agreement indicator
                            unique_preds = len(set(predictions.values()))
                            agreement = ((len(predictions) - unique_preds + 1) / len(predictions)) * 100
                            
                            fig_agree = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=agreement,
                                title={'text': "Model Agreement (%)"},
                                gauge={
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "#4CAF50"},
                                    'steps': [
                                        {'range': [0, 50], 'color': "#FFCDD2"},
                                        {'range': [50, 75], 'color': "#FFF9C4"},
                                        {'range': [75, 100], 'color': "#C8E6C9"}
                                    ]
                                }
                            ))
                            fig_agree.update_layout(height=300)
                            st.plotly_chart(fig_agree, use_container_width=True, key=f"agree_gauge_{iteration}")
                        
                        # Prediction probability distribution for primary model
                        st.markdown("---")
                        st.subheader("📈 Prediction Probability Distribution (Standard RF)")
                        
                        primary_model = "Standard RF"
                        if primary_model in prediction_probas:
                            proba = prediction_probas[primary_model]
                            top_10_indices = np.argsort(proba)[-10:][::-1]
                            
                            crop_names = []
                            confidences = []
                            
                            if 'Crop Name' in encoders:
                                for idx in top_10_indices:
                                    try:
                                        crop_name = encoders['Crop Name'].inverse_transform([idx])[0]
                                        crop_names.append(crop_name)
                                        confidences.append(proba[idx] * 100)
                                    except:
                                        crop_names.append(f"Class {idx}")
                                        confidences.append(proba[idx] * 100)
                            
                                fig_dist = go.Figure(data=[
                                    go.Bar(
                                        x=confidences,
                                        y=crop_names,
                                        orientation='h',
                                        marker=dict(
                                            color=confidences,
                                            colorscale='Greens',
                                            showscale=True,
                                            colorbar=dict(title="Confidence %")
                                        ),
                                        text=[f"{c:.1f}%" for c in confidences],
                                        textposition='auto'
                                    )
                                ])
                                
                                fig_dist.update_layout(
                                    title="Top 10 Crop Predictions by Confidence",
                                    xaxis_title="Confidence (%)",
                                    yaxis_title="Crop Name",
                                    height=400,
                                    yaxis={'categoryorder': 'total ascending'}
                                )
                                
                                st.plotly_chart(fig_dist, use_container_width=True, key=f"dist_chart_{iteration}")
                        
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
                        
                        # Model Performance Comparison
                        st.markdown("---")
                        st.subheader("📊 Model Performance Analysis")
                        
                        perf_tabs = st.tabs(["Comparison Table", "Confidence Analysis", "Feature Importance Comparison"])
                        
                        with perf_tabs[0]:
                            # Create performance comparison table
                            perf_data = []
                            for model_name, proba in prediction_probas.items():
                                pred_idx = predictions[model_name]
                                confidence = proba[pred_idx] * 100
                                
                                # Get top 5 predictions
                                top_5_indices = np.argsort(proba)[-5:][::-1]
                                top_5_conf = [proba[i] * 100 for i in top_5_indices]
                                avg_top5 = np.mean(top_5_conf)
                                
                                # Entropy (measure of uncertainty)
                                entropy = -np.sum(proba * np.log(proba + 1e-10))
                                
                                perf_data.append({
                                    'Model': model_name,
                                    'Predicted Crop': encoders['Crop Name'].inverse_transform([pred_idx])[0] if 'Crop Name' in encoders else f"Class {pred_idx}",
                                    'Confidence (%)': f"{confidence:.2f}",
                                    'Avg Top-5 Conf (%)': f"{avg_top5:.2f}",
                                    'Prediction Entropy': f"{entropy:.3f}",
                                    'Decision Certainty': "High" if confidence > 80 else "Medium" if confidence > 50 else "Low"
                                })
                            
                            perf_df = pd.DataFrame(perf_data)
                            st.dataframe(perf_df, use_container_width=True, hide_index=True)
                            
                            st.info("**Interpretation:**\n"
                                   "- **Confidence**: How certain the model is about its top prediction\n"
                                   "- **Avg Top-5 Conf**: Average confidence across top 5 predictions (higher = more decisive)\n"
                                   "- **Entropy**: Lower values indicate more certainty (less spread in probabilities)\n"
                                   "- **Decision Certainty**: Overall assessment of prediction reliability")
                        
                        with perf_tabs[1]:
                            # Confidence distribution comparison
                            st.markdown("**Probability Distribution Comparison Across Models**")
                            
                            # Get top 10 crops from primary model
                            primary_proba = prediction_probas["Standard RF"]
                            top_10_indices = np.argsort(primary_proba)[-10:][::-1]
                            
                            comparison_data = []
                            for idx in top_10_indices:
                                if 'Crop Name' in encoders:
                                    crop_name = encoders['Crop Name'].inverse_transform([idx])[0]
                                    row = {'Crop': crop_name}
                                    
                                    for model_name, proba in prediction_probas.items():
                                        row[model_name] = proba[idx] * 100
                                    
                                    comparison_data.append(row)
                            
                            if comparison_data:
                                comp_df = pd.DataFrame(comparison_data)
                                
                                fig_comp = go.Figure()
                                
                                colors = ['#2E7D32', '#388E3C', '#43A047']
                                for idx, model_name in enumerate(prediction_probas.keys()):
                                    fig_comp.add_trace(go.Bar(
                                        name=model_name,
                                        x=comp_df['Crop'],
                                        y=comp_df[model_name],
                                        marker_color=colors[idx % len(colors)]
                                    ))
                                
                                fig_comp.update_layout(
                                    title="Top 10 Crop Probabilities: Model Comparison",
                                    xaxis_title="Crop Name",
                                    yaxis_title="Probability (%)",
                                    barmode='group',
                                    height=500,
                                    xaxis={'tickangle': -45}
                                )
                                
                                st.plotly_chart(fig_comp, use_container_width=True, key=f"comp_chart_{iteration}")
                                
                                st.markdown("**Analysis:** This chart shows how different models assign probabilities "
                                          "to the same crops, revealing agreement/disagreement patterns.")
                        
                        with perf_tabs[2]:
                            # Feature importance comparison across models
                            st.markdown("**Feature Importance Across Different Models**")
                            
                            importance_comparison = []
                            
                            for model_name, model in models.items():
                                if hasattr(model, 'feature_importances_'):
                                    for idx, (feature, importance) in enumerate(zip(config['feature_columns'], model.feature_importances_)):
                                        importance_comparison.append({
                                            'Model': model_name,
                                            'Feature': feature,
                                            'Importance': importance
                                        })
                            
                            if importance_comparison:
                                imp_comp_df = pd.DataFrame(importance_comparison)
                                
                                # Get top features
                                top_features = imp_comp_df.groupby('Feature')['Importance'].mean().nlargest(10).index
                                imp_comp_filtered = imp_comp_df[imp_comp_df['Feature'].isin(top_features)]
                                
                                fig_imp_comp = px.bar(
                                    imp_comp_filtered,
                                    x='Importance',
                                    y='Feature',
                                    color='Model',
                                    orientation='h',
                                    title="Top 10 Feature Importance Comparison",
                                    barmode='group',
                                    height=500
                                )
                                
                                st.plotly_chart(fig_imp_comp, use_container_width=True, key=f"imp_comp_chart_{iteration}")
                                
                                st.markdown("**Analysis:** Shows which features each model considers most important. "
                                          "Agreement across models indicates robust, reliable feature importance.")
                        
                        # Additional Insights Section
                        st.markdown("---")
                        st.subheader("💡 Insights & Recommendations")
                        
                        insight_cols = st.columns(2)
                        
                        with insight_cols[0]:
                            st.markdown("**🎯 Prediction Quality**")
                            
                            # Calculate consensus
                            pred_values = list(predictions.values())
                            unique_preds = len(set(pred_values))
                            
                            if unique_preds == 1:
                                st.success("✅ **Strong Consensus**: All models agree on the same crop!")
                                consensus_level = "High"
                            elif unique_preds == 2:
                                st.warning("⚠️ **Moderate Agreement**: Models show some disagreement.")
                                consensus_level = "Medium"
                            else:
                                st.error("❌ **Low Consensus**: Models disagree significantly.")
                                consensus_level = "Low"
                            
                            # Average confidence
                            avg_confidence = np.mean([prediction_probas[m][predictions[m]] * 100 for m in predictions.keys()])
                            
                            if avg_confidence > 80:
                                st.success(f"✅ **High Confidence**: Average {avg_confidence:.1f}%")
                            elif avg_confidence > 50:
                                st.warning(f"⚠️ **Moderate Confidence**: Average {avg_confidence:.1f}%")
                            else:
                                st.error(f"❌ **Low Confidence**: Average {avg_confidence:.1f}%")
                            
                            st.metric("Overall Prediction Quality", 
                                     "Excellent" if consensus_level == "High" and avg_confidence > 80 
                                     else "Good" if consensus_level in ["High", "Medium"] and avg_confidence > 60
                                     else "Fair" if avg_confidence > 40
                                     else "Poor")
                        
                        with insight_cols[1]:
                            st.markdown("**🌾 Crop Recommendations**")
                            
                            # Get most frequent prediction
                            from collections import Counter
                            pred_counter = Counter(pred_values)
                            most_common_pred = pred_counter.most_common(1)[0][0]
                            
                            if 'Crop Name' in encoders:
                                recommended_crop = encoders['Crop Name'].inverse_transform([most_common_pred])[0]
                                st.success(f"**Primary Recommendation:** {recommended_crop}")
                                
                                # Get alternative crops from ensemble
                                all_top_crops = set()
                                for proba in prediction_probas.values():
                                    top_3 = np.argsort(proba)[-3:][::-1]
                                    for idx in top_3:
                                        crop = encoders['Crop Name'].inverse_transform([idx])[0]
                                        all_top_crops.add(crop)
                                
                                st.markdown("**Alternative Options:**")
                                for crop in list(all_top_crops)[:5]:
                                    if crop != recommended_crop:
                                        st.write(f"• {crop}")
                        
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
