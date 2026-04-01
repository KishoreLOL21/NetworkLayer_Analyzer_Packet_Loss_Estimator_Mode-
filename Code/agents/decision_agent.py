class DecisionAgent:
    def __init__(self, context, threshold=0.5):
        self.context = context
        self.threshold = threshold

        self.weights = {
            "RandomForest": 0.25,
            "XGBoost": 0.25,
            "SVM": 0.2,
            "Logistic": 0.15,
            "NeuralNet": 0.15
        }

    def _decide(self, predictions):
        score = 0

        for model, weight in self.weights.items():
            pred = predictions.get(model, 0)
            score += pred * weight

        if "NN_Prob" in predictions:
            nn_prob = predictions["NN_Prob"]
            score += 0.1 * nn_prob

        max_score = sum(self.weights.values()) + 0.1
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
            "raw_score": round(score, 3)
        }

    def run(self):
        """
        Reads predictions from context → writes decision to context
        """

        predictions = self.context.get("predictions")

        if predictions is None:
            print("⚠️ DecisionAgent: No predictions found in context")
            return

        print("\n🧠 DecisionAgent running...")

        decision = self._decide(predictions)

        print("\n🧠 Decision Debug Info:")
        print("   Raw Score:", decision["raw_score"])
        print("   Confidence:", decision["confidence"])

        self.context.update("decision", {
            "decision": decision["decision"],
            "confidence": decision["confidence"],
            "action": decision["action"]
        })

        history = self.context.get("history", [])
        history.append({
            "predictions": predictions,
            "decision": decision
        })
        self.context.update("history", history)

        self.context.update("event", {
            "type": "decision_made",
            "data": decision
        })

        print("⚡ Final Decision:", decision["decision"])