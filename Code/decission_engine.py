class DecisionEngine:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

        self.weights = {
            "RandomForest": 0.25,
            "XGBoost": 0.25,
            "SVM": 0.2,
            "Logistic": 0.15,
            "NeuralNet": 0.15
        }

    def decide(self, predictions):
        """
        predictions = {
            'RandomForest': 0/1,
            'XGBoost': 0/1,
            'SVM': 0/1,
            'Logistic': 0/1,
            'NeuralNet': 0/1,
            'NN_Prob': float (optional)
        }
        """

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

        print("\n🧠 Decision Debug Info:")
        print("   Raw Score:", round(score, 3))
        print("   Confidence:", round(confidence, 3))

        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "action": action
        }