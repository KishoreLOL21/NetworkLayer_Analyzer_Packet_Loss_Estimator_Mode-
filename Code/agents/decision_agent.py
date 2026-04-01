class DecisionAgent:
    def __init__(self, context, threshold=0.5):
        self.context = context
        self.threshold = threshold

        self.weights = {
            "RandomForest": 0.15,
            "XGBoost": 0.3,   
            "SVM": 0.1,
            "Logistic": 0.05,
            "NeuralNet": 0.2,
            "LSTM": 0.2,
        }

    def _decide(self, predictions):
        score = 0

        for model, weight in self.weights.items():
            score += predictions.get(model, 0) * weight

        # probability boosts
        score += 0.1 * predictions.get("NN_Prob", 0)
        score += 0.1 * predictions.get("LSTM_Prob", 0)

        max_score = sum(self.weights.values()) + 0.2
        confidence = score / max_score

        if confidence >= self.threshold:
            decision = "PACKET LOSS DETECTED"
            action = "Reduce congestion / Trigger alert"
        else:
            decision = "NO LOSS"
            action = "Continue monitoring"

        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "action": action,
            "raw_score": round(score, 3),
        }

    def run(self):
        predictions = self.context.get("predictions")
        if predictions is None:
            return

        print("\n🧠 DecisionAgent running...")

        decision = self._decide(predictions)

        print("   Score:", decision["raw_score"])
        print("   Confidence:", decision["confidence"])

        self.context.update("decision", {
            "decision": decision["decision"],
            "confidence": decision["confidence"],
            "action": decision["action"]
        })

        # FIX: use append instead of overwrite
        self.context.append("history", {
            "predictions": predictions,
            "decision": decision
        })

        self.context.append("logs", {
            "type": "decision",
            "data": decision
        })

        self.context.update("event", {
            "type": "decision_made",
            "data": decision
        })

        print("⚡ Final Decision:", decision["decision"])