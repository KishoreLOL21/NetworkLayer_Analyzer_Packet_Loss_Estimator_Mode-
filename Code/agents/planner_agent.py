class PlannerAgent:
    def __init__(self, context):
        self.context = context

    def plan(self):
        packet = self.context.get("packet")

        if packet["rolling_loss_rate"] > 0.5:
            return ["predictor", "decision", "alert"]
        else:
            return ["predictor", "decision"]