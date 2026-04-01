class FeedbackAgent:
    def __init__(self, context):
        self.context = context

    def run(self):
        decision = self.context.get("decision")
        actual = self.context.get("ground_truth")

        if actual is None:
            return

        if decision and decision["decision"] != actual:
            print("⚠️ FeedbackAgent: Model mismatch detected")

            self.context.update("model_adjustment_needed", True)

            self.context.append("logs", {
                "type": "feedback",
                "issue": "prediction_mismatch",
                "decision": decision,
                "actual": actual
            })