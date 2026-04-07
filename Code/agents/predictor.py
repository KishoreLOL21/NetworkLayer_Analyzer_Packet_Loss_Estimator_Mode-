import os
import joblib
import tensorflow as tf
import numpy as np
import pandas as pd


class ModelTool:
    def __init__(self, name, model):
        self.name = name
        self.model = model

    def execute(self, X):
        try:
            return self.model.predict(X)
        except Exception as e:
            print(f"⚠️ {self.name} prediction failed:", e)
            return [0]


class PredictorAgent:
    FEATURE_ORDER = [
        "flag_syn", "tcp_window_size", "tcp_len", "tcp_seq", "ip_len",
        "frame_time_delta", "tcp_srcport", "rolling_std_len",
        "rolling_loss_rate", "flag_push", "tcp_dstport", "tcp_ack",
        "flag_rst", "flag_fin", "seq_delta", "iat",
        "rolling_mean_len", "flag_ack", "ack_delta",
    ]

    def __init__(self, context):
        self.context = context

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "Models"))

        # Classical models
        self.rf  = joblib.load(os.path.join(MODEL_DIR, "random_forest_model.pkl"))
        self.svm = joblib.load(os.path.join(MODEL_DIR, "svm_model.pkl"))
        self.xgb = joblib.load(os.path.join(MODEL_DIR, "xgboost_model.pkl"))
        self.log = joblib.load(os.path.join(MODEL_DIR, "logistic_model.pkl"))

        self.tools = {
            "RandomForest": ModelTool("RF", self.rf),
            "XGBoost": ModelTool("XGB", self.xgb),
            "SVM": ModelTool("SVM", self.svm),
            "Logistic": ModelTool("LOG", self.log),
        }

        self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        self.pca    = joblib.load(os.path.join(MODEL_DIR, "pca.pkl"))

        # Neural Net
        try:
            self.nn = tf.keras.models.load_model(
                os.path.join(MODEL_DIR, "neural_network_model.h5"),
                compile=False
            )
        except:
            self.nn = None

        # LSTM (NEW)
        try:
            self.lstm = tf.keras.models.load_model(
                os.path.join(MOzDEL_DIR, "lstm_model.h5"),
                compile=False
            )
        except:
            self.lstm = None

        self.sequence_buffer = []
        self.sequence_length = 10

    def _packet_to_array(self, packet):
        iat = packet.get("inter_arrival_time", 0)
        tcp_len = packet.get("payload_len", 0)

        feature_map = {
            "flag_syn": 0,
            "tcp_window_size": packet.get("tcp_window_size", 8192),
            "tcp_len": tcp_len,
            "tcp_seq": packet.get("seq", 0),
            "ip_len": tcp_len + 40,
            "frame_time_delta": iat,
            "tcp_srcport": packet.get("src_port", 0),
            "rolling_std_len": packet.get("rolling_std_len", tcp_len),
            "rolling_loss_rate": packet.get("rolling_loss_rate", 0),
            "flag_push": packet.get("retransmission", 0),
            "tcp_dstport": packet.get("dst_port", 0),
            "tcp_ack": packet.get("ack", 0),
            "flag_rst": 0,
            "flag_fin": 0,
            "seq_delta": packet.get("seq_delta", 1),
            "iat": iat,
            "rolling_mean_len": tcp_len,
            "flag_ack": 1,
            "ack_delta": packet.get("ack_delta", 1),
        }

        return pd.DataFrame([{k: feature_map[k] for k in self.FEATURE_ORDER}])

    def preprocess(self, packet):
        try:
            X_raw = self._packet_to_array(packet)
            X_scaled = self.scaler.transform(X_raw)
            return self.pca.transform(X_scaled)
        except Exception as e:
            print("⚠️ Preprocessing failed:", e)
            return None

    def run(self):
        packet = self.context.get("packet")
        if packet is None:
            return

        print("\n🤖 PredictorAgent running...")

        X = self.preprocess(packet)
        if X is None:
            return

        results = {}

        # Classical models
        for name, tool in self.tools.items():
            results[name] = int(tool.execute(X)[0])

        # Neural Net
        if self.nn:
            prob = float(self.nn.predict(X, verbose=0)[0][0])
            results["NeuralNet"] = int(prob >= 0.5)
            results["NN_Prob"] = prob
        else:
            results["NeuralNet"] = 0
            results["NN_Prob"] = 0.0

        self.sequence_buffer.append(X[0])

        if len(self.sequence_buffer) > self.sequence_length:
            self.sequence_buffer.pop(0)

        if len(self.sequence_buffer) == self.sequence_length and self.lstm:
            seq = np.array(self.sequence_buffer).reshape(1, self.sequence_length, -1)
            prob = float(self.lstm.predict(seq, verbose=0)[0][0])
            results["LSTM"] = int(prob >= 0.5)
            results["LSTM_Prob"] = prob
        else:
            results["LSTM"] = 0
            results["LSTM_Prob"] = 0.0

        # MCP updates
        self.context.update("predictions", results)
        self.context.append("history", {"packet": packet, "predictions": results})
        self.context.append("logs", {"type": "prediction", "data": results})
        self.context.update("event", {"type": "prediction_completed", "data": results})

        print("📊 Predictor Output:", {k: v for k, v in results.items() if "Prob" not in k})