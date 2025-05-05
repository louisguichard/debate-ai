import google.genai as genai
import os
import json
import random
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in environment variables.")


class Agent:
    """Represents a participant in the debate."""

    def __init__(self, name, role, persona, is_moderator=False):
        self.name = name if name else role
        self.role = role
        self.persona = persona
        self.is_moderator = is_moderator

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "persona": self.persona,
            "is_moderator": self.is_moderator,
        }


class Debate:
    """Manages the state and flow of the AI debate."""

    def __init__(
        self,
        config=None,
        config_path=None,
        model_name="gemini-2.0-flash-lite",
    ):
        """Initialize the debate with its parameters."""
        self.config = config
        self.model_name = model_name
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.reset()
        self.initialize_debate(config_path)

    def initialize_debate(self, config_path=None):
        """Loads debate configuration from the JSON file."""

        if not self.config:  # load from config_path
            with open(config_path, "r") as f:
                self.config = json.load(f)

        # Create agents from config
        agents = []
        for agent_config in self.config["agents"]:
            agent = Agent(
                name=agent_config["name"],
                role=agent_config["role"],
                persona=agent_config.get("persona", ""),
                is_moderator=agent_config.get("is_moderator", False),
            )
            agents.append(agent)

        # Create moderator if not in the list
        has_moderator = any(agent.is_moderator for agent in agents)
        if not has_moderator:
            moderator = Agent(
                name="Moderator",
                role="Debate Moderator",
                persona="Your task is to introduce the debate and participants, then guide the discussion. You may introduce new aspects, ask specific participants to address certain points, or summarize key points made. If you believe the debate should conclude now, clearly state 'The debate is now concluded' at the end of your message.",
                is_moderator=True,
            )
            agents = [moderator] + agents

        # Initialize debate parameters
        self.title = self.config["title"]
        self.description = self.config["description"]
        self.max_turns = self.config.get("max_turns", 10)
        self.agents = agents

        # Set debate language
        self.language = self.detect_language()

        # Initialize the next speaker
        self.update_next_speaker()

    def detect_language(self):
        """Auto-detect the debate language based on title, description, and personas."""
        # Combine all texts
        texts = f"{self.title}\n{self.description}"
        for agent in self.agents:
            texts += f"\n{agent.persona}"

        # Ask Gemini to detect the language
        prompt = f"""
        Based on the following texts, determine what language it's in.
        Simply respond with the name of the language in English. The only available options are the following: English, French or Other.
        
        Texts to analyze:
        {texts}
        """

        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        detected_language = response.text.strip()
        if detected_language not in ["English", "French", "Other"]:
            print(
                f"Warning: Auto-detected language {detected_language} is not in the available options. Falling back to English."
            )
            detected_language = "English"
        return detected_language

    def reset(self):
        """Resets the debate state to its initial condition."""
        self.transcript = []
        self.current_turn = 0
        self.debate_running = False
        self.debate_finished = False
        self.next_speaker = None
        print("Debate reset.")

    def start(self):
        """Starts the debate."""
        self.debate_running = True
        self.debate_finished = False
        print("Debate started.")

    def stop(self):
        """Stops the debate."""
        self.debate_running = False
        print("Debate stopped.")

    def generate_prompt(self, agent):
        """Generate a prompt for the agent to respond in the debate."""
        debate_context = f"""
Debate topic: {self.title}
Debate description: {self.description}
Participants: {", ".join([f"{a.name} ({a.role})" for a in self.agents])}
Debate language: {self.language}

You are {agent.name}, playing the role of {agent.role}.
Your persona: {agent.persona}

Current debate transcript:
"""
        # Special instruction for first turn
        if self.current_turn == 0:
            debate_context += "(The debate is just starting. As the moderator, introduce the topic and participants.)"

        # Add the transcript so far
        else:
            for entry in self.transcript:
                debate_context += f"{entry['speaker']}: {entry['message']}"

        debate_context += f"""
Based on the debate so far, provide your next contribution as {agent.name}.
Your response should reflect your role and persona.
Be concise and to the point. You can respond with just a few words, a sentence or sometimes a few sentences.
"""
        if agent.is_moderator:
            debate_context += "You will be the moderator of this debate. After introducing the debate and its participants, you will guide the discussion. If the debate has come to an end, clearly state 'The debate is now closed' at the end of your message."

        debate_context += f"You MUST respond in {self.language} language."
        return debate_context

    def update_next_speaker(self):
        """Update the next speaker based on the current debate context."""
        # Moderator is always the first speaker
        if self.current_turn == 0:
            for agent in self.agents:
                if agent.is_moderator:
                    self.next_speaker = agent
                    return
            # If no moderator found
            print("Warning: No moderator found. Falling back to first agent.")
            self.next_speaker = self.agents[0]
            return

        # Use Gemini to determine the next speaker
        prompt = f"""
Based on the following debate transcript, determine which participant should speak next.
Choose the participant who would most naturally continue the conversation based on:
1. Who hasn't spoken recently
2. Who has been directly addressed or challenged
3. Who might have the most relevant perspective to add now

Debate Title: {self.title}
Debate Description: {self.description}

Participants and their Roles:
{json.dumps([{"name": a.name, "role": a.role} for a in self.agents], indent=2)}

Transcript:
{json.dumps(self.transcript, indent=2)}

Which participant should speak next to continue the debate?

Answer with ONLY the EXACT full name of the participant from this list: {", ".join([agent.name for agent in self.agents])}
Do not include any other text, reasoning, or formatting. Just the name.
"""
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        next_speaker = response.text.strip()

        # Find the agent by name
        for agent in self.agents:
            if agent.name.lower() == next_speaker.lower():
                self.next_speaker = agent
                return

        # Fallback: don't choose the last speaker
        print(
            f"Warning: Could not identify next speaker from response '{next_speaker}'. Falling back to non-repeating random selection."
        )
        last_speaker = self.transcript[-1]["speaker"] if self.transcript else None
        available_agents = [a for a in self.agents if a.name != last_speaker]
        self.next_speaker = random.choice(available_agents)

    def run_next_turn(self):
        """Determines the next speaker, generates their message, and updates the state."""

        if self.current_turn >= self.max_turns:
            self.debate_finished = False
            self.debate_running = False
            print(f"Reached maximum turns ({self.max_turns}).")
            return None
        print(f"Turn {self.current_turn + 1}: {self.next_speaker.name}")

        prompt = self.generate_prompt(self.next_speaker)

        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        message = response.text.strip()

        # Check for moderator's conclusion phrase
        if "the debate is now concluded" in message.lower():
            self.debate_finished = True
            self.debate_running = False
            print("Debate concluded by moderator.")

        entry = {"speaker": self.next_speaker.name, "message": message}
        self.transcript.append(entry)
        self.current_turn += 1
        return entry

    def get_state(self):
        """Returns the current state of the debate for the UI."""
        return {
            "title": self.title,
            "description": self.description,
            "agents": [a.to_dict() for a in self.agents],
            "transcript": self.transcript,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "is_running": self.debate_running,
            "is_finished": self.debate_finished,
            "next_speaker": self.next_speaker.name if self.next_speaker else None,
            "language": self.language,
        }
