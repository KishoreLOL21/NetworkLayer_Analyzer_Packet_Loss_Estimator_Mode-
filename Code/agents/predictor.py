import os
import joblib
import tensorflow as tf
import numpy as np

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
        "flag_syn",
        "tcp_window_size",
        "tcp_len",
        "tcp_seq",
        "ip_len",
        "frame_time_delta",
        "tcp_srcport",
        "rolling_std_len",
        "rolling_loss_rate",
        "flag_push",
        "tcp_dstport",
        "tcp_ack",
        "flag_rst",
        "flag_fin",
        "seq_delta",
        "iat",
        "rolling_mean_len",
        "flag_ack",
        "ack_delta",
    ]

    def __init__(self, context):
        self.context = context

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MODEL_DIR = os.path.abspath(
            os.path.join(BASE_DIR, "..", "..", "Models")
        )

        self.rf  = joblib.load(os.path.join(MODEL_DIR, "random_forest_model.pkl"))
        self.svm = joblib.load(os.path.join(MODEL_DIR, "svm_model.pkl"))
        self.xgb = joblib.load(os.path.join(MODEL_DIR, "xgboost_model.pkl"))
        self.log = joblib.load(os.path.join(MODEL_DIR, "logistic_model.pkl"))

        self.tools = {
            "RandomForest": ModelTool("RandomForest", self.rf),
            "XGBoost": ModelTool("XGBoost", self.xgb),
            "SVM": ModelTool("SVM", self.svm),
            "Logistic": ModelTool("Logistic", self.log),
        }

        self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        self.pca    = joblib.load(os.path.join(MODEL_DIR, "pca.pkl"))

        try:
            self.nn = tf.keras.models.load_model(
                os.path.join(MODEL_DIR, "neural_network_model.h5"),
                compile=False
            )
            print("✅ PredictorAgent: Neural Network loaded")
        except Exception as e:
            print("⚠️ PredictorAgent: Neural Network skipped:", e)
            self.nn = None

    def _packet_to_array(self, packet: dict) -> np.ndarray:
        tcp_len = packet.get("payload_len", 0)
        ip_len  = tcp_len + 40

        feature_map = {
            "flag_syn": 0,
            "tcp_window_size": packet.get("tcp_window_size", 8192),
            "tcp_len": tcp_len,
            "tcp_seq": packet.get("seq", 0),
            "ip_len": ip_len,
            "frame_time_delta": packet.get("inter_arrival_time", 0),
            "tcp_srcport": packet.get("src_port", 0),
            "rolling_std_len": 0,
            "rolling_loss_rate": packet.get("rolling_loss_rate", 0),
            "flag_push": packet.get("retransmission", 0),
            "tcp_dstport": packet.get("dst_port", 0),
            "tcp_ack": packet.get("ack", 0),
            "flag_rst": 0,
            "flag_fin": 0,
            "seq_delta": 0,
            "iat": packet.get("inter_arrival_time", 0),
            "rolling_mean_len": tcp_len,
            "flag_ack": 1,
            "ack_delta": 0,
        }

        row = [feature_map[feat] for feat in self.FEATURE_ORDER]
        return np.array([row], dtype=np.float64)

    def preprocess(self, packet: dict) -> np.ndarray:
        try:
            X_raw = self._packet_to_array(packet)
            X_scaled = self.scaler.transform(X_raw)
            X_pca = self.pca.transform(X_scaled)
            return X_pca
        except Exception as e:
            print("⚠️ Preprocessing failed:", e)
            return None

    def run(self):
        packet = self.context.get("packet")

        if packet is None:
            print("⚠️ PredictorAgent: No packet found in context")
            return

        print("\n🤖 PredictorAgent running...")

        X = self.preprocess(packet)
        if X is None:
            return

        results = {}
        
        for name, tool in self.tools.items():
            try:
                pred = tool.execute(X)
                results[name] = int(pred[0])
            except Exception:
                results[name] = 0

        if self.nn is not None:
            try:
                nn_prob = float(self.nn.predict(X, verbose=0)[0][0])
                results["NeuralNet"] = int(nn_prob < 0.5)
                results["NN_Prob"] = nn_prob
            except Exception as e:
                print("⚠️ NN failed:", e)
                results["NeuralNet"] = 0
                results["NN_Prob"] = 0.0
        else:
            results["NeuralNet"] = 0
            results["NN_Prob"] = 0.0

        self.context.update("predictions", results)

        self.context.append("history", {
            "packet": packet,
            "predictions": results
        })

        self.context.append("logs", {
            "type": "prediction",
            "data": results
        })

        self.context.update("event", {
            "type": "prediction_completed",
            "data": results
        })

        print("📊 Predictor Output:",
              {k: v for k, v in results.items() if k != "NN_Prob"})