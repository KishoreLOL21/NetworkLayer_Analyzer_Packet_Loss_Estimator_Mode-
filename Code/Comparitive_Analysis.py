import matplotlib.pyplot as plt

models = [
    "Logistic Regression",
    "Decision Tree",
    "Random Forest",
    "XGBoost",
    "Ensemble (Existing)",
    "Agentic AI (Proposed)"
]

accuracies = [85, 89, 93, 72, 90, 91]

# Different colors for each bar
colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan']

plt.figure()

bars = plt.bar(models, accuracies, color=colors)

# Add value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        height + 1,
        f'{height}%',
        ha='center',
        fontsize=10
    )

plt.xlabel("Models")
plt.ylabel("Accuracy (%)")
plt.title("Comparison of Packet Loss Prediction Models")

plt.xticks(rotation=30)
plt.ylim(0, 100)

plt.tight_layout()
plt.show()