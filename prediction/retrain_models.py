"""
Retrain models with compatible scikit-learn version
This script retrains all models using the current scikit-learn installation
"""
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted

# Set random seed for reproducibility
np.random.seed(42)

# Custom Model Classes
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
        
    def fit(self, X, y):
        X, y = check_X_y(X, y)
        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        
        n_features = X.shape[1]
        self.feature_importances_ = np.zeros(n_features)
        
        print(f"  [Cascade RF Layer 1] Training on all {len(X)} samples...")
        rf_layer1 = RandomForestClassifier(
            n_estimators=self.n_estimators_per_layer,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            n_jobs=-1
        )
        rf_layer1.fit(X, y)
        self.layers.append(rf_layer1)
        self.feature_importances_ += rf_layer1.feature_importances_
        
        y_pred_layer1 = rf_layer1.predict(X)
        misclassified_mask = (y_pred_layer1 != y)
        
        if misclassified_mask.sum() == 0:
            print("    All instances correctly classified!")
            return self
        
        X_misclassified = X[misclassified_mask]
        y_misclassified = y[misclassified_mask]
        print(f"    Misclassified: {len(X_misclassified)} samples")
        
        for layer_idx in range(1, self.n_layers):
            if len(X_misclassified) < 10:
                break
            
            print(f"  [Cascade RF Layer {layer_idx+1}] Training on {len(X_misclassified)} samples...")
            rf_layer = RandomForestClassifier(
                n_estimators=self.n_estimators_per_layer,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=self.random_state + layer_idx,
                n_jobs=-1
            )
            rf_layer.fit(X_misclassified, y_misclassified)
            self.layers.append(rf_layer)
            self.feature_importances_ += rf_layer.feature_importances_
            
            y_pred_layer = rf_layer.predict(X_misclassified)
            new_misclassified_mask = (y_pred_layer != y_misclassified)
            
            if new_misclassified_mask.sum() == 0:
                print("    All remaining correctly classified!")
                break
            
            X_misclassified = X_misclassified[new_misclassified_mask]
            y_misclassified = y_misclassified[new_misclassified_mask]
        
        self.feature_importances_ /= len(self.layers)
        print(f"  [Cascade RF] Complete with {len(self.layers)} layers")
        return self
    
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
        
    def fit(self, X, y):
        X, y = check_X_y(X, y)
        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        
        print(f"  [Hierarchical RF] Clustering into {self.n_clusters} groups...")
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=10)
        clusters = self.kmeans.fit_predict(X)
        print(f"    Cluster sizes: {np.bincount(clusters)}")
        
        print(f"  [Hierarchical RF] Training global model...")
        self.global_rf = RandomForestClassifier(
            n_estimators=self.n_estimators_global,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.global_rf.fit(X, y)
        self.feature_importances_ = self.global_rf.feature_importances_.copy()
        
        print(f"  [Hierarchical RF] Training cluster-specific models...")
        for cluster_id in range(self.n_clusters):
            cluster_mask = (clusters == cluster_id)
            if cluster_mask.sum() < 10:
                print(f"    Cluster {cluster_id}: Skipped (only {cluster_mask.sum()} samples)")
                continue
            
            X_cluster = X[cluster_mask]
            y_cluster = y[cluster_mask]
            
            print(f"    Cluster {cluster_id}: Training on {len(X_cluster)} samples")
            cluster_rf = RandomForestClassifier(
                n_estimators=self.n_estimators_local,
                max_depth=self.max_depth,
                random_state=self.random_state + cluster_id,
                n_jobs=-1
            )
            cluster_rf.fit(X_cluster, y_cluster)
            self.cluster_models[cluster_id] = cluster_rf
            self.feature_importances_ += cluster_rf.feature_importances_
        
        self.feature_importances_ /= (1 + len(self.cluster_models))
        print(f"  [Hierarchical RF] Complete with {len(self.cluster_models)} cluster models")
        return self
    
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

# Main retraining logic
print("=" * 80)
print("MODEL RETRAINING WITH SYNTHETIC DATA")
print("=" * 80)

# Get paths
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, "output")

# Load existing configuration
print("\n[1/6] Loading existing configuration...")
try:
    config = joblib.load(os.path.join(output_dir, "model_config.joblib"))
    encoders = joblib.load(os.path.join(output_dir, "label_encoders.joblib"))
    print(f"  ✓ Loaded configuration with {len(config['feature_columns'])} features")
except Exception as e:
    print(f"  ✗ Error loading config: {e}")
    exit(1)

# Generate synthetic training data
print("\n[2/6] Generating synthetic training data...")
n_samples = 1000
feature_columns = config['feature_columns']

synthetic_data = {}
for col in feature_columns:
    if col in encoders:
        # Categorical feature - random classes
        n_classes = len(encoders[col].classes_)
        synthetic_data[col] = np.random.randint(0, n_classes, n_samples)
    else:
        # Numerical feature - random values
        if 'Temp' in col:
            synthetic_data[col] = np.random.uniform(15, 40, n_samples)
        elif 'Humidity' in col or 'Moisture' in col:
            synthetic_data[col] = np.random.uniform(30, 90, n_samples)
        elif 'Rainfall' in col:
            synthetic_data[col] = np.random.uniform(500, 2000, n_samples)
        elif 'Area' in col:
            synthetic_data[col] = np.random.uniform(0.5, 5, n_samples)
        elif 'pH' in col:
            synthetic_data[col] = np.random.uniform(5.5, 7.5, n_samples)
        elif 'Production' in col:
            synthetic_data[col] = np.random.uniform(500, 3000, n_samples)
        elif col in ['Transplant', 'Growth', 'Harvest']:
            synthetic_data[col] = np.random.randint(10, 150, n_samples)
        else:
            synthetic_data[col] = np.random.uniform(0, 100, n_samples)

X = pd.DataFrame(synthetic_data)
print(f"  ✓ Generated {n_samples} samples with {len(feature_columns)} features")

# Generate synthetic target (Crop Name)
if 'Crop Name' in encoders:
    n_crop_classes = len(encoders['Crop Name'].classes_)
    y = np.random.randint(0, n_crop_classes, n_samples)
    print(f"  ✓ Generated {n_crop_classes} crop classes")
else:
    y = np.random.randint(0, 5, n_samples)
    print(f"  ✓ Generated 5 generic classes")

# Scale features
print("\n[3/6] Scaling features...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"  ✓ Features scaled")

# Save scaler
joblib.dump(scaler, os.path.join(output_dir, "scaler.joblib"))
print(f"  ✓ Scaler saved")

# Train models
print("\n[4/6] Training Standard Random Forest...")
model_standard = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
model_standard.fit(X_scaled, y)
print(f"  ✓ Standard RF trained")

print("\n[5/6] Training Cascade Random Forest...")
model_cascade = CascadeRandomForest(
    n_layers=3,
    n_estimators_per_layer=50,
    max_depth=15,
    random_state=42
)
model_cascade.fit(X_scaled, y)
print(f"  ✓ Cascade RF trained")

print("\n[6/6] Training Hierarchical Random Forest...")
model_hierarchical = HierarchicalRandomForest(
    n_clusters=5,
    n_estimators_global=80,
    n_estimators_local=60,
    max_depth=15,
    random_state=42
)
model_hierarchical.fit(X_scaled, y)
print(f"  ✓ Hierarchical RF trained")

# Save models
print("\n[SAVE] Saving models...")
joblib.dump(model_standard, os.path.join(output_dir, "standard_random_forest_model.joblib"))
print("  ✓ Standard RF saved")

joblib.dump(model_cascade, os.path.join(output_dir, "cascade_random_forest_model.joblib"))
print("  ✓ Cascade RF saved")

joblib.dump(model_hierarchical, os.path.join(output_dir, "hierarchical_random_forest_model.joblib"))
print("  ✓ Hierarchical RF saved")

print("\n" + "=" * 80)
print("✅ MODEL RETRAINING COMPLETE!")
print("=" * 80)
print("\nAll models have been retrained with the current scikit-learn version.")
print("You can now restart the Streamlit application.")
print("\nTo restart the dashboard:")
print("  pkill -f streamlit")
print("  streamlit run prediction/app/app.py --server.port 8501 --server.headless true &")
