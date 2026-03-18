import os
import joblib
import tensorflow as tf
import numpy as np
import pandas as pd


class PacketLossPredictor:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MODEL_DIR = os.path.join(BASE_DIR, "..", "Models")

        # Load models
        self.rf = joblib.load(os.path.join(MODEL_DIR, "random_forest_model.pkl"))
        self.svm = joblib.load(os.path.join(MODEL_DIR, "svm_model.pkl"))
        self.xgb = joblib.load(os.path.join(MODEL_DIR, "xgboost_model.pkl"))
        self.log = joblib.load(os.path.join(MODEL_DIR, "logistic_model.pkl"))

        # Load NN safely
        try:
            self.nn = tf.keras.models.load_model(
                os.path.join(MODEL_DIR, "neural_network_model.h5"),
                compile=False
            )
            print("✅ Neural Network loaded")
        except Exception as e:
            print("⚠️ Neural Network skipped:", e)
            self.nn = None

        # Load preprocessing
        self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        self.pca = joblib.load(os.path.join(MODEL_DIR, "pca.pkl"))
        self.features = joblib.load(os.path.join(MODEL_DIR, "feature_order.pkl"))

    def preprocess(self, packet_input):
        # Handle dict or list input
        if isinstance(packet_input, dict):
            df = pd.DataFrame([packet_input])
        else:
            df = pd.DataFrame(packet_input, columns=self.features)

        # Fill missing features
        for col in self.features:
            if col not in df.columns:
                df[col] = 0

        df = df[self.features]

        # Scaling
        scaled = self.scaler.transform(df)

        # PCA
        pca_features = self.pca.transform(scaled)

        return pca_features

    def predict(self, packet_input):
        X = self.preprocess(packet_input)

        results = {}

        results["RandomForest"] = 1 - int(self.rf.predict(X)[0])
        results["XGBoost"] = 1 - int(self.xgb.predict(X)[0])
        results["SVM"] = 1 - int(self.svm.predict(X)[0])
        results["Logistic"] = 1 - int(self.log.predict(X)[0])

        if self.nn:
            try:
                nn_prob = self.nn.predict(X, verbose=0)[0][0]
                results["NeuralNet"] = int(nn_prob < 0.5)
                results["NN_Prob"] = float(nn_prob)
            except Exception as e:
                print("⚠️ NN prediction failed:", e)
                results["NeuralNet"] = 0
                results["NN_Prob"] = 0.0
        else:
            results["NeuralNet"] = 0
            results["NN_Prob"] = 0.0

        return results