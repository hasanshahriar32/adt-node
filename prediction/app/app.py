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
    page_title="🌾 Crop Yield Prediction System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme
st.markdown("""
<script>
    var stApp = window.parent.document.querySelector('.stApp');
    if (stApp) {
        stApp.classList.remove('stApp--dark');
        stApp.classList.add('stApp--light');
    }
</script>
""", unsafe_allow_html=True)

# Custom CSS for agricultural styling
st.markdown("""
<style>
    /* Main background with agricultural feel */
    .stApp {
        background: linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 50%, #C5E1A5 100%);
    }
    
    /* Main container styling */
    .main .block-container {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(46, 125, 50, 0.15);
    }
    
    /* Header styling with agricultural theme */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1B5E20;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(139, 195, 74, 0.3);
        font-family: 'Georgia', serif;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #33691E;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Section headers with earthy gradient */
    .section-header {
        background: linear-gradient(90deg, #558B2F 0%, #689F38 50%, #7CB342 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 12px;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        box-shadow: 0 3px 10px rgba(85, 139, 47, 0.3);
        border: 2px solid #8BC34A;
    }
    
    /* Info boxes with farm-inspired colors */
    .info-box {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 6px solid #4CAF50;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(76, 175, 80, 0.2);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        border-left: 6px solid #FFA726;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(255, 167, 38, 0.2);
    }
    
    /* Metric cards with natural tones */
    .stMetric {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F8E9 100%);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(139, 195, 74, 0.15);
        border: 1px solid #C5E1A5;
    }
    
    /* Expander with organic feel */
    div[data-testid="stExpander"] {
        background: linear-gradient(135deg, #F9FBE7 0%, #F0F4C3 100%);
        border-radius: 10px;
        border: 2px solid #CDDC39;
        box-shadow: 0 2px 8px rgba(205, 220, 57, 0.2);
    }
    
    /* Sidebar with field-inspired background */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #DCEDC8 0%, #C5E1A5 100%);
        border-right: 3px solid #8BC34A;
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent;
    }
    
    /* Crop cards */
    .crop-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F8E9 100%);
        border-radius: 10px;
        padding: 0.5rem;
        margin: 0.3rem 0;
        box-shadow: 0 2px 6px rgba(139, 195, 74, 0.2);
        border: 1px solid #AED581;
    }
    
    /* Buttons with agricultural accent */
    .stButton > button {
        background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        box-shadow: 0 3px 8px rgba(76, 175, 80, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        transform: translateY(-2px);
    }
    
    /* Tabs with natural styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(135deg, #DCEDC8 0%, #C5E1A5 100%);
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #F1F8E9;
        border-radius: 8px;
        color: #33691E;
        font-weight: 600;
        border: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
        color: white;
        border: 2px solid #2E7D32;
    }
    
    /* Progress bars with green theme */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #66BB6A 0%, #4CAF50 100%);
    }
    
    /* Success/warning/error messages */
    .stSuccess {
        background: linear-gradient(135deg, #C8E6C9 0%, #A5D6A7 100%);
        border-left: 6px solid #4CAF50;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FFE082 0%, #FFD54F 100%);
        border-left: 6px solid #FFA726;
    }
    
    .stError {
        background: linear-gradient(135deg, #FFCDD2 0%, #EF9A9A 100%);
        border-left: 6px solid #F44336;
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
        # Register custom classes in the main module to fix unpickling
        import sys
        current_module = sys.modules[__name__]
        if not hasattr(current_module, 'CascadeRandomForest'):
            current_module.CascadeRandomForest = CascadeRandomForest
        if not hasattr(current_module, 'HierarchicalRandomForest'):
            current_module.HierarchicalRandomForest = HierarchicalRandomForest
        
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
        return None, "Connection error - Check if simulation is running"
    except Exception as e:
        return None, f"Error: {str(e)}"

def prepare_features(telemetry_data, user_inputs, feature_columns):
    """Prepare feature vector from telemetry and user inputs"""
    feature_dict = {}
    
    if 'telemetry' in telemetry_data:
        feature_dict['Avg Temp'] = telemetry_data['telemetry'].get('temperature', 25)
        feature_dict['Avg Humidity'] = telemetry_data['telemetry'].get('humidity', 70)
        feature_dict['Soil Moisture'] = telemetry_data['telemetry'].get('soilMoisture', 35)
    
    feature_dict.update(user_inputs)
    
    if 'Max Temp' in feature_dict and 'Min Temp' in feature_dict:
        feature_dict['Temp_Range'] = feature_dict['Max Temp'] - feature_dict['Min Temp']
    
    if 'Max Relative Humidity' in feature_dict and 'Min Relative Humidity' in feature_dict:
        feature_dict['Humidity_Range'] = feature_dict['Max Relative Humidity'] - feature_dict['Min Relative Humidity']
    
    if 'Avg Temp' in feature_dict and 'Avg Humidity' in feature_dict:
        feature_dict['Temp_Humidity_Index'] = feature_dict['Avg Temp'] * feature_dict['Avg Humidity'] / 100
    
    df = pd.DataFrame([feature_dict])
    
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[feature_columns]

def encode_and_scale(df, encoders, scaler, feature_columns):
    """Encode categorical variables and scale features"""
    df_processed = df.copy()
    
    for col, encoder in encoders.items():
        if col in df_processed.columns:
            try:
                df_processed[col] = encoder.transform(df_processed[col].astype(str))
            except:
                df_processed[col] = 0
    
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
    st.markdown('<div class="main-header">🌾 Advanced Crop Yield Prediction System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Model AI-Powered Agricultural Decision Support Platform</div>', unsafe_allow_html=True)
    
    # Load models
    models, config, encoders, scaler, error = load_models()
    
    if error:
        st.error(f"❌ **System Error:** Unable to load prediction models\n\n`{error}`")
        st.info("📋 **Action Required:** Ensure model files are present in `prediction/output/` directory")
        return
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ System Configuration")
        
        st.markdown("### 🌐 Data Source")
        api_url = st.text_input(
            "API Endpoint",
            value="https://adt-node.onrender.com/api/telemetry",
            help="Node-RED simulation API endpoint URL"
        )
        
        st.markdown("### 🔄 Update Settings")
        auto_refresh = st.checkbox("Enable Auto-Refresh", value=True)
        refresh_interval = st.slider("Refresh Interval (seconds)", 1, 60, 5)
        
        st.markdown("---")
        st.markdown("### 📊 Model Information")
        st.info(f"""
        **Active Models:** {len(models)}
        - Standard Random Forest
        - Cascade Random Forest  
        - Hierarchical Random Forest
        
        **Features:** {len(config['feature_columns'])}
        **Crop Classes:** {len(encoders['Crop Name'].classes_) if 'Crop Name' in encoders else 'N/A'}
        """)
        
        st.markdown("---")
        st.caption("💡 Configure farm parameters below the dashboard")
    
    # Farm Parameters Configuration
    districts = list(encoders['District'].classes_) if 'District' in encoders else ['District_A']
    seasons = list(encoders['Season'].classes_) if 'Season' in encoders else ['Kharif', 'Rabi']
    
    with st.expander("⚙️ **Farm Parameters Configuration**", expanded=False):
        st.markdown("#### Enter your farm details for accurate predictions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 📍 Location & Timing")
            district = st.selectbox("District", districts, key="district_input")
            season = st.selectbox("Season", seasons, key="season_input")
            area = st.number_input("Farm Area (Hectares)", min_value=0.1, value=1.0, step=0.1, key="area_input")
            ap_ratio = st.number_input("Area-Production Ratio", min_value=0.0, value=0.5, step=0.1, key="ap_ratio_input")
        
        with col2:
            st.markdown("##### 🌦️ Environmental Conditions")
            total_rainfall = st.number_input("Annual Rainfall (mm)", min_value=0.0, value=800.0, step=10.0, key="rainfall_input")
            ph_level = st.number_input("Soil pH Level", min_value=0.0, max_value=14.0, value=6.5, step=0.1, key="ph_input")
            max_temp = st.number_input("Maximum Temperature (°C)", min_value=-10.0, max_value=50.0, value=35.0, step=0.5, key="max_temp_input")
            min_temp = st.number_input("Minimum Temperature (°C)", min_value=-10.0, max_value=50.0, value=20.0, step=0.5, key="min_temp_input")
        
        with col3:
            st.markdown("##### 🌱 Production & Growth")
            production = st.number_input("Expected Production", min_value=0.0, value=1000.0, step=100.0, key="production_input")
            max_humidity = st.slider("Maximum Humidity (%)", 0, 100, 90, key="max_humidity_input")
            min_humidity = st.slider("Minimum Humidity (%)", 0, 100, 50, key="min_humidity_input")
        
        st.markdown("##### 📅 Crop Growth Stages (days)")
        gcol1, gcol2, gcol3 = st.columns(3)
        with gcol1:
            transplant = st.number_input("Transplanting", min_value=0, value=30, step=1, key="transplant_input")
        with gcol2:
            growth = st.number_input("Growth Period", min_value=0, value=90, step=1, key="growth_input")
        with gcol3:
            harvest = st.number_input("Harvest Time", min_value=0, value=120, step=1, key="harvest_input")
    
    st.markdown("---")
    
    # Main content area with organized sections
    if auto_refresh:
        placeholder = st.empty()
        iteration = 0
        
        while True:
            iteration += 1
            with placeholder.container():
                # Fetch simulation data
                data, fetch_error = fetch_simulation_data(api_url)
                
                if fetch_error:
                    st.error(f"❌ **Data Fetch Error:** {fetch_error}")
                    st.warning("⚠️ **Troubleshooting:**\n- Verify the API endpoint URL\n- Check if simulation service is running\n- Ensure network connectivity")
                else:
                    # ===== SECTION 1: LIVE SENSOR DATA =====
                    st.markdown('<div class="section-header">📡 Live Environmental Monitoring</div>', unsafe_allow_html=True)
                    
                    tel_cols = st.columns([1, 1, 1, 1, 1])
                    
                    if 'telemetry' in data:
                        tel = data['telemetry']
                        tel_cols[0].metric("🌡️ Temperature", f"{tel.get('temperature', 0):.1f}°C", 
                                          delta=f"{tel.get('temperature', 0) - 25:.1f}°C")
                        tel_cols[1].metric("💧 Humidity", f"{tel.get('humidity', 0):.1f}%",
                                          delta=f"{tel.get('humidity', 0) - 60:.1f}%")
                        tel_cols[2].metric("🌱 Soil Moisture", f"{tel.get('soilMoisture', 0):.1f}%",
                                          delta=f"{tel.get('soilMoisture', 0) - 40:.1f}%")
                        tel_cols[3].metric("📍 Device", data.get('deviceId', 'N/A')[:15])
                        tel_cols[4].metric("⏰ Updated", datetime.now().strftime("%H:%M:%S"))
                    
                    st.markdown("---")
                    
                    # Prepare features
                    user_inputs = {
                        'Area': area, 'AP Ratio': ap_ratio, 'District': district, 'Season': season,
                        'Total Rainfall': total_rainfall, 'Production': production,
                        'Max Temp': max_temp, 'Min Temp': min_temp,
                        'Max Relative Humidity': max_humidity, 'Min Relative Humidity': min_humidity,
                        'pH Level': ph_level, 'Transplant': transplant, 'Growth': growth, 'Harvest': harvest
                    }
                    
                    try:
                        features_df = prepare_features(data, user_inputs, config['feature_columns'])
                        features_scaled = encode_and_scale(features_df, encoders, scaler, config['feature_columns'])
                        
                        # Make predictions
                        predictions = {}
                        prediction_probas = {}
                        
                        for model_name, model in models.items():
                            prediction = model.predict(features_scaled)[0]
                            proba = model.predict_proba(features_scaled)[0]
                            predictions[model_name] = prediction
                            prediction_probas[model_name] = proba
                        
                        # Create two-column layout for organized display
                        left_col, right_col = st.columns([1, 1])
                        
                        # ===== LEFT COLUMN: PREDICTIONS =====
                        with left_col:
                            st.markdown('<div class="section-header">🎯 AI Model Predictions</div>', unsafe_allow_html=True)
                            
                            # Main predictions with images
                            for model_name in models.keys():
                                with st.container():
                                    pred_idx = predictions[model_name]
                                    proba = prediction_probas[model_name]
                                    
                                    if 'Crop Name' in encoders:
                                        crop_name = encoders['Crop Name'].inverse_transform([pred_idx])[0]
                                        confidence = proba[pred_idx] * 100
                                        
                                        # Model prediction card
                                        st.markdown(f"**{model_name}**")
                                        pred_col1, pred_col2 = st.columns([1, 2])
                                        
                                        with pred_col1:
                                            try:
                                                img_url = get_crop_image_url(crop_name)
                                                st.image(img_url, width=120)
                                            except:
                                                st.write("🌾")
                                        
                                        with pred_col2:
                                            st.metric("Recommended Crop", crop_name, 
                                                     f"{confidence:.1f}% confidence")
                                            st.progress(confidence / 100)
                                        
                                        st.markdown("---")
                            
                            # Top 5 recommendations
                            st.markdown("##### 🏆 Top 5 Alternative Crops")
                            
                            tabs = st.tabs([m for m in models.keys()])
                            
                            for idx, (model_name, proba) in enumerate(prediction_probas.items()):
                                with tabs[idx]:
                                    top_5_indices = np.argsort(proba)[-5:][::-1]
                                    
                                    for rank, class_idx in enumerate(top_5_indices, 1):
                                        if 'Crop Name' in encoders:
                                            crop_name = encoders['Crop Name'].inverse_transform([class_idx])[0]
                                            confidence = proba[class_idx] * 100
                                            
                                            rec_col1, rec_col2 = st.columns([1, 4])
                                            with rec_col1:
                                                try:
                                                    st.image(get_crop_image_url(crop_name), width=60)
                                                except:
                                                    st.write(f"{rank}.")
                                            with rec_col2:
                                                st.markdown(f"**{crop_name}**")
                                                st.progress(confidence / 100)
                                                st.caption(f"Confidence: {confidence:.2f}%")
                        
                        # ===== RIGHT COLUMN: ANALYTICS =====
                        with right_col:
                            st.markdown('<div class="section-header">📊 Performance Analytics</div>', unsafe_allow_html=True)
                            
                            # Consensus indicator
                            unique_preds = len(set(predictions.values()))
                            agreement = ((len(predictions) - unique_preds + 1) / len(predictions)) * 100
                            
                            if agreement >= 80:
                                st.success(f"✅ **Strong Model Consensus:** {agreement:.0f}% agreement")
                            elif agreement >= 50:
                                st.warning(f"⚠️ **Moderate Consensus:** {agreement:.0f}% agreement")
                            else:
                                st.error(f"❌ **Low Consensus:** {agreement:.0f}% agreement - Results may vary")
                            
                            # Model confidence comparison
                            st.markdown("##### 📈 Model Confidence Levels")
                            
                            conf_data = []
                            for model_name, proba in prediction_probas.items():
                                pred_idx = predictions[model_name]
                                conf_data.append({
                                    'Model': model_name,
                                    'Confidence': proba[pred_idx] * 100
                                })
                            
                            conf_df = pd.DataFrame(conf_data)
                            
                            fig_conf = px.bar(
                                conf_df, 
                                x='Model', 
                                y='Confidence',
                                text='Confidence',
                                color='Confidence',
                                color_continuous_scale='Greens'
                            )
                            fig_conf.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                            fig_conf.update_layout(height=300, showlegend=False, yaxis_range=[0, 100])
                            st.plotly_chart(fig_conf, use_container_width=True, key=f"conf_{iteration}")
                            
                            # Environmental gauges
                            st.markdown("##### 🌡️ Environmental Conditions")
                            
                            gauge_cols = st.columns(3)
                            
                            with gauge_cols[0]:
                                fig_temp = go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=tel.get('temperature', 0) if 'telemetry' in data else 0,
                                    title={'text': "Temp (°C)"},
                                    gauge={'axis': {'range': [0, 50]}, 'bar': {'color': "#FF5722"},
                                           'steps': [{'range': [0, 20], 'color': "lightblue"},
                                                    {'range': [20, 35], 'color': "lightgreen"},
                                                    {'range': [35, 50], 'color': "lightyellow"}]}
                                ))
                                fig_temp.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
                                st.plotly_chart(fig_temp, use_container_width=True, key=f"temp_{iteration}")
                            
                            with gauge_cols[1]:
                                fig_hum = go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=tel.get('humidity', 0) if 'telemetry' in data else 0,
                                    title={'text': "Humidity (%)"},
                                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2196F3"},
                                           'steps': [{'range': [0, 40], 'color': "lightyellow"},
                                                    {'range': [40, 70], 'color': "lightgreen"},
                                                    {'range': [70, 100], 'color': "lightblue"}]}
                                ))
                                fig_hum.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
                                st.plotly_chart(fig_hum, use_container_width=True, key=f"hum_{iteration}")
                            
                            with gauge_cols[2]:
                                fig_soil = go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=tel.get('soilMoisture', 0) if 'telemetry' in data else 0,
                                    title={'text': "Soil (%)"},
                                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#8D6E63"},
                                           'steps': [{'range': [0, 30], 'color': "#FFCCBC"},
                                                    {'range': [30, 60], 'color': "#A1887F"},
                                                    {'range': [60, 100], 'color': "#6D4C41"}]}
                                ))
                                fig_soil.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
                                st.plotly_chart(fig_soil, use_container_width=True, key=f"soil_{iteration}")
                        
                        # ===== SECTION 2: DETAILED ANALYSIS (Full Width) =====
                        st.markdown("---")
                        st.markdown('<div class="section-header">🔬 Detailed Model Analysis</div>', unsafe_allow_html=True)
                        
                        analysis_tabs = st.tabs([
                            "📊 Performance Metrics", 
                            "📈 Probability Distribution", 
                            "🎯 Feature Importance",
                            "📉 Confidence Analysis",
                            "🔍 Feature Comparison"
                        ])
                        
                        with analysis_tabs[0]:
                            # Performance comparison table
                            perf_data = []
                            for model_name, proba in prediction_probas.items():
                                pred_idx = predictions[model_name]
                                confidence = proba[pred_idx] * 100
                                top_5 = np.mean(np.sort(proba)[-5:]) * 100
                                entropy = -np.sum(proba * np.log(proba + 1e-10))
                                
                                perf_data.append({
                                    'Model': model_name,
                                    'Prediction': encoders['Crop Name'].inverse_transform([pred_idx])[0],
                                    'Confidence (%)': f"{confidence:.2f}",
                                    'Top-5 Avg (%)': f"{top_5:.2f}",
                                    'Entropy': f"{entropy:.3f}",
                                    'Certainty': "High" if confidence > 80 else "Medium" if confidence > 50 else "Low"
                                })
                            
                            st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)
                            
                            st.markdown("""
                            <div class="info-box">
                            <strong>📖 Metric Definitions:</strong><br>
                            • <strong>Confidence:</strong> Model's certainty about its top prediction<br>
                            • <strong>Top-5 Avg:</strong> Average probability across top 5 predictions (higher = more decisive)<br>
                            • <strong>Entropy:</strong> Prediction uncertainty measure (lower = more certain)<br>
                            • <strong>Certainty:</strong> Overall reliability assessment
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with analysis_tabs[1]:
                            # Probability distribution
                            primary_proba = prediction_probas["Standard RF"]
                            top_10 = np.argsort(primary_proba)[-10:][::-1]
                            
                            dist_data = []
                            for idx in top_10:
                                crop_name = encoders['Crop Name'].inverse_transform([idx])[0]
                                dist_data.append({
                                    'Crop': crop_name,
                                    'Probability (%)': primary_proba[idx] * 100
                                })
                            
                            dist_df = pd.DataFrame(dist_data)
                            
                            fig_dist = px.bar(
                                dist_df, 
                                x='Probability (%)', 
                                y='Crop',
                                orientation='h',
                                text='Probability (%)',
                                color='Probability (%)',
                                color_continuous_scale='Greens'
                            )
                            fig_dist.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                            fig_dist.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                            st.plotly_chart(fig_dist, use_container_width=True, key=f"dist_{iteration}")
                        
                        with analysis_tabs[2]:
                            # Feature importance
                            if hasattr(models["Standard RF"], 'feature_importances_'):
                                importances = models["Standard RF"].feature_importances_
                                feature_names = config['feature_columns']
                                
                                imp_df = pd.DataFrame({
                                    'Feature': feature_names,
                                    'Importance': importances
                                }).sort_values('Importance', ascending=False).head(15)
                                
                                fig_imp = px.bar(
                                    imp_df,
                                    x='Importance',
                                    y='Feature',
                                    orientation='h',
                                    color='Importance',
                                    color_continuous_scale='Viridis'
                                )
                                fig_imp.update_layout(
                                    height=500, 
                                    yaxis={'categoryorder': 'total ascending'},
                                    title="Top 15 Most Important Features"
                                )
                                st.plotly_chart(fig_imp, use_container_width=True, key=f"imp_{iteration}")
                        
                        with analysis_tabs[3]:
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
                                
                                st.markdown("""
                                <div class="info-box">
                                <strong>📊 Analysis:</strong> This chart shows how different models assign probabilities 
                                to the same crops, revealing agreement/disagreement patterns.
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with analysis_tabs[4]:
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
                                
                                st.markdown("""
                                <div class="info-box">
                                <strong>🔍 Analysis:</strong> Shows which features each model considers most important. 
                                Agreement across models indicates robust, reliable feature importance.
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # ===== SECTION 3: INSIGHTS & RECOMMENDATIONS =====
                        st.markdown("---")
                        st.markdown('<div class="section-header">💡 Insights & Recommendations</div>', unsafe_allow_html=True)
                        
                        insight_cols = st.columns(2)
                        
                        with insight_cols[0]:
                            st.markdown("#### 🎯 Prediction Quality Assessment")
                            
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
                            
                            quality_score = "Excellent" if consensus_level == "High" and avg_confidence > 80 \
                                          else "Good" if consensus_level in ["High", "Medium"] and avg_confidence > 60 \
                                          else "Fair" if avg_confidence > 40 else "Poor"
                            
                            st.metric("Overall Prediction Quality", quality_score)
                        
                        with insight_cols[1]:
                            st.markdown("#### 🌾 Crop Recommendations")
                            
                            # Get most frequent prediction
                            from collections import Counter
                            pred_counter = Counter(pred_values)
                            most_common_pred = pred_counter.most_common(1)[0][0]
                            
                            if 'Crop Name' in encoders:
                                recommended_crop = encoders['Crop Name'].inverse_transform([most_common_pred])[0]
                                st.success(f"**🏆 Primary Recommendation:** {recommended_crop}")
                                
                                # Get alternative crops from ensemble
                                all_top_crops = set()
                                for proba in prediction_probas.values():
                                    top_3 = np.argsort(proba)[-3:][::-1]
                                    for idx in top_3:
                                        crop = encoders['Crop Name'].inverse_transform([idx])[0]
                                        all_top_crops.add(crop)
                                
                                st.markdown("**🌱 Alternative Options:**")
                                alternatives = [crop for crop in list(all_top_crops)[:5] if crop != recommended_crop]
                                for alt_crop in alternatives:
                                    st.write(f"• {alt_crop}")
                        
                        # Raw data viewer
                        with st.expander("🔍 View Raw Data & Debug Info"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**API Response:**")
                                st.json(data)
                            with col2:
                                st.markdown("**Feature Vector:**")
                                st.dataframe(features_df)
                    
                    except Exception as e:
                        st.error(f"❌ **Prediction Error:** {str(e)}")
                        st.exception(e)
            
            time.sleep(refresh_interval)
    
    else:
        st.info("✋ **Auto-Refresh Disabled**\n\nEnable 'Auto Refresh' in the sidebar to start real-time predictions.")

if __name__ == "__main__":
    main()
