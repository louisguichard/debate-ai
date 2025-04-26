import os
import google.genai as genai
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

from debate import Debate
from agent import Agent
from utils import load_debate_config

# Load environment variables
load_dotenv()

# Configure Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", os.urandom(24))

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in environment variables.")
client = genai.Client(api_key=GEMINI_API_KEY)

# Global variable to store debate
debate = None


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/start_debate")
def start_debate():
    """Initialize a new debate and generate first turn."""
    global debate

    # Load debate configuration
    config = load_debate_config("debate_config.json")

    # Create agents from config
    agents = []
    for agent_config in config["agents"]:
        agent = Agent(
            name=agent_config["name"],
            role=agent_config["role"],
            persona=agent_config.get("persona", ""),
        )
        agents.append(agent)

    # Create moderator if not in the list
    has_moderator = any("moderator" in agent.role.lower() for agent in agents)
    if not has_moderator:
        moderator = Agent(
            name="Moderator",
            role="Debate Moderator",
            persona="Your task is to introduce the debate and participants, then guide the discussion. You may introduce new aspects, ask specific participants to address certain points, or summarize key points made. If you believe the debate should conclude now, clearly state 'The debate is now concluded' at the end of your message.",
        )
        agents.append(moderator)

    # Create debate object
    debate = Debate(
        title=config["title"],
        description=config["description"],
        agents=agents,
        client=client,
        max_turns=config.get("max_turns", 5),
    )

    # Generate first turn
    turn_data = generate()

    return jsonify(
        {
            "status": "started",
            "title": config["title"],
            "description": config["description"],
            "agents": [a.to_dict() for a in agents],
            "turn": turn_data,
        }
    )


@app.route("/generate")
def generate():
    """Generate the next turn in the debate."""
    global debate

    if debate is None:
        return jsonify({"error": "No debate in progress. Start a debate first."})

    # Generate the next turn using the debate object
    entry = debate.generate_next_turn()

    # Return the result
    return {"entry": entry, "concluded": debate.debate_concluded}


if __name__ == "__main__":
    app.run(debug=True)
