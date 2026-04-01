class ModelTool:
    def __init__(self, name, model):
        self.name = name
        self.model = model

    def execute(self, X):
        try:
            return self.model.predict(X)
        except Exception as e:
            print(f"⚠️ {self.name} failed:", e)
            return [0]