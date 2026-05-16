"""
============================================================
AI MODEL - Random Forest Regressor untuk Prediksi Volume Sampah
Waste Volume Prediction System
============================================================
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from config import MODEL_CONFIG, DATA_DIR, MODELS_DIR


class WastePredictionModel:
    """Model AI untuk prediksi volume sampah."""

    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_columns = []
        self.metrics = {}
        self.feature_importances = {}

    def _prepare_features(self, df):
        """Siapkan fitur untuk model ML."""
        feature_df = df.copy()

        # Encode categorical columns
        categorical_cols = ["location", "zone", "season", "weather", "event_name", "kota_adm"]
        for col in categorical_cols:
            if col in feature_df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    feature_df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(
                        feature_df[col].astype(str)
                    )
                else:
                    # Handle unseen labels
                    known_labels = set(self.label_encoders[col].classes_)
                    feature_df[col] = feature_df[col].apply(
                        lambda x: x if x in known_labels else "unknown"
                    )
                    if "unknown" not in self.label_encoders[col].classes_:
                        self.label_encoders[col].classes_ = np.append(
                            self.label_encoders[col].classes_, "unknown"
                        )
                    feature_df[f"{col}_encoded"] = self.label_encoders[col].transform(
                        feature_df[col].astype(str)
                    )

        # Cyclical encoding for time features
        feature_df["month_sin"] = np.sin(2 * np.pi * feature_df["month"] / 12)
        feature_df["month_cos"] = np.cos(2 * np.pi * feature_df["month"] / 12)
        feature_df["dow_sin"] = np.sin(2 * np.pi * feature_df["day_of_week"] / 7)
        feature_df["dow_cos"] = np.cos(2 * np.pi * feature_df["day_of_week"] / 7)
        feature_df["doy_sin"] = np.sin(2 * np.pi * feature_df["day_of_year"] / 365)
        feature_df["doy_cos"] = np.cos(2 * np.pi * feature_df["day_of_year"] / 365)

        # Select feature columns
        self.feature_columns = [
            "population_density", "day_of_week", "day_of_month", "month",
            "day_of_year", "is_weekend", "has_event", "event_visitors",
            "temperature_c", "humidity_pct", "rainfall_mm",
            "location_encoded", "zone_encoded", "season_encoded",
            "weather_encoded", "event_name_encoded", "kota_adm_encoded",
            "month_sin", "month_cos", "dow_sin", "dow_cos",
            "doy_sin", "doy_cos",
        ]

        return feature_df[self.feature_columns]

    def train(self, df):
        """Train the prediction model."""
        print("🧠 Training AI model...")

        X = self._prepare_features(df)
        y = df["volume_kg"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=MODEL_CONFIG["test_size"],
            random_state=MODEL_CONFIG["random_state"],
        )

        # Random Forest model
        self.model = GradientBoostingRegressor(
            n_estimators=MODEL_CONFIG["n_estimators"],
            max_depth=MODEL_CONFIG["max_depth"],
            min_samples_split=MODEL_CONFIG["min_samples_split"],
            random_state=MODEL_CONFIG["random_state"],
            learning_rate=0.1,
            subsample=0.8,
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        self.metrics = {
            "mae": round(mean_absolute_error(y_test, y_pred), 2),
            "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
            "r2": round(r2_score(y_test, y_pred), 4),
            "mape": round(np.mean(np.abs((y_test - y_pred) / y_test)) * 100, 2),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # Feature importances
        importances = self.model.feature_importances_
        self.feature_importances = dict(
            sorted(
                zip(self.feature_columns, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        )

        print(f"✅ Model trained successfully!")
        print(f"   R² Score: {self.metrics['r2']}")
        print(f"   MAE: {self.metrics['mae']} kg")
        print(f"   RMSE: {self.metrics['rmse']} kg")
        print(f"   MAPE: {self.metrics['mape']}%")

        return self.metrics

    def predict(self, df):
        """Predict waste volume."""
        if self.model is None:
            raise ValueError("Model belum di-train! Jalankan train() terlebih dahulu.")

        X = self._prepare_features(df)
        predictions = self.model.predict(X)
        return np.maximum(predictions, 0)  # Ensure non-negative

    def save(self, filename="waste_model.pkl"):
        """Save model to disk."""
        model_path = os.path.join(MODELS_DIR, filename)
        model_data = {
            "model": self.model,
            "label_encoders": self.label_encoders,
            "feature_columns": self.feature_columns,
            "metrics": self.metrics,
            "feature_importances": self.feature_importances,
        }
        joblib.dump(model_data, model_path)
        print(f"💾 Model saved: {model_path}")

    def load(self, filename="waste_model.pkl"):
        """Load model from disk."""
        model_path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(model_path):
            return False

        model_data = joblib.load(model_path)
        self.model = model_data["model"]
        self.label_encoders = model_data["label_encoders"]
        self.feature_columns = model_data["feature_columns"]
        self.metrics = model_data["metrics"]
        self.feature_importances = model_data["feature_importances"]
        print(f"📦 Model loaded: {model_path}")
        return True


def train_and_save():
    """Train model and save to disk."""
    csv_path = os.path.join(DATA_DIR, "waste_historical.csv")
    if not os.path.exists(csv_path):
        print("❌ Data tidak ditemukan! Jalankan generate_data.py terlebih dahulu.")
        return None

    df = pd.read_csv(csv_path)
    model = WastePredictionModel()
    model.train(df)
    model.save()
    return model


if __name__ == "__main__":
    train_and_save()
