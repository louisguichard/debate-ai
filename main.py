import os
import google.genai as genai
from dotenv import load_dotenv

from debate import Debate
from agent import Agent
from utils import load_debate_config


def main():
    """Main function to run the debate."""
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Configure Gemini API
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            raise ValueError("Please set GEMINI_API_KEY in environment variables")
        client = genai.Client(api_key=GEMINI_API_KEY)

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

        # Create and run debate
        debate = Debate(
            title=config["title"],
            description=config["description"],
            agents=agents,
            client=client,
            max_turns=config.get("max_turns", 5),
        )
        debate.run_debate()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
