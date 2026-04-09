from agents.predictor import PredictorAgent
from agents.decision_agent import DecisionAgent
from agents.planner_agent import PlannerAgent
from agents.feedback_agent import FeedbackAgent
from mcp.context import MCPContext


class AgentOrchestrator:
    def __init__(self):
        self.context = MCPContext()

        self.agents = {
            "predictor": PredictorAgent(self.context),
            "decision": DecisionAgent(self.context),
            "feedback": FeedbackAgent(self.context),
        }

        self.planner = PlannerAgent(self.context)

        self.event_handlers = {
            "prediction_completed": ["decision"],
            "decision_made": ["feedback"]
        }

    def run(self, packet):
        self.context.update("event", None)
        self.context.update("packet", packet)

        print("\n🚀 Orchestrator started")

        try:
            plan = self.planner.plan()
        except Exception as e:
            print("⚠️ Planner failed:", e)
            return None

        for step in plan:
            if step not in self.agents:
                continue

            self._execute_agent(step)

        decision = self.context.get("decision")

        print("\n🏁 Final Output:", decision)

        return decision

    def _execute_agent(self, agent_name):
        """
        Executes an agent and handles event-driven chaining
        """

        try:
            print(f"\n⚙️ Executing agent: {agent_name}")
            self.agents[agent_name].run()
        except Exception as e:
            print(f"⚠️ Agent {agent_name} failed:", e)
            return

        while True:
            event = self.context.get("event")

            if not event:
                break

            event_type = event.get("type")

            self.context.update("event", None)

            next_agents = self.event_handlers.get(event_type, [])

            for next_agent in next_agents:
                if next_agent in self.agents:
                    try:
                        print(f"🔁 Triggered by event → {next_agent}")
                        self.agents[next_agent].run()
                    except Exception as e:
                        print(f"⚠️ Event-triggered agent {next_agent} failed:", e)