from predictor import PacketLossPredictor
from decission_engine import DecisionEngine


class PacketLossAgent:
    def __init__(self):
        self.predictor = PacketLossPredictor()
        self.decision_engine = DecisionEngine()

    def process_packet(self, packet):
        print("\n🔍 Incoming Packet:", packet)

        predictions = self.predictor.predict(packet)

        # Print only model outputs (exclude NN_Prob for clarity)
        display_preds = {k: v for k, v in predictions.items() if k != "NN_Prob"}
        print("📊 Model Predictions:", display_preds)

        decision = self.decision_engine.decide(predictions)

        print("🧠 Decision:", decision["decision"])
        print("📈 Confidence:", decision["confidence"])
        print("⚡ Action:", decision["action"])

        return decision