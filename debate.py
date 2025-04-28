import json
import random
import time


class Debate:
    def __init__(self, title, description, agents, client, max_turns):
        self.title = title
        self.description = description
        self.agents = agents
        self.max_turns = max_turns
        self.transcript = []
        self.current_turn = 0
        self.model = "gemini-2.0-flash"
        self.delay = 5
        self.debate_concluded = False
        self.client = client

    def generate_agent_prompt(self, agent):
        """Generate a prompt for the agent to respond in the debate."""
        debate_context = f"""
Title: {self.title}
Description: {self.description}
Participants: {", ".join([f"{a.name} ({a.role})" for a in self.agents])}

You are {agent.name}, {agent.role}.
Your persona: {agent.persona}

Current debate status:
"""
        # Add the transcript so far
        for entry in self.transcript:
            debate_context += f"{entry['speaker']}: {entry['message']}\n\n"
        if self.current_turn == 0:
            debate_context += "The debate hasn't started yet. Introduce the topic and the participants.\n\n"

        debate_context += f"""
Based on the debate so far, provide your next contribution as {agent.name}.
Your response should reflect your role and persona.
Be concise and to the point. You can respond with just a few words, a sentence or sometimes a few sentences.
"""
        return debate_context

    def determine_next_speaker(self):
        """Determine who should speak next based on the current debate context."""
        # First turn - find moderator by role
        if self.current_turn == 0:
            for agent in self.agents:
                if "moderator" in agent.role.lower():
                    return agent

        # Determine the next speaker
        prompt = f"""
Based on the following debate transcript, determine which participant should speak next.
Choose the participant who would most naturally continue the conversation based on:
1. Who hasn't spoken recently
2. Who has been directly addressed or challenged
3. Who might have the most relevant perspective to add now

Debate Title: {self.title}
Debate Description: {self.description}

Participants:
{json.dumps([a.to_dict() for a in self.agents], indent=2)}

Transcript so far:
{json.dumps(self.transcript, indent=2)}

IMPORTANT: Return ONLY the EXACT full name of the next speaker from the list below:
{", ".join([agent.name for agent in self.agents])}
Do not include any other text, just the name.
"""
        response = self.client.models.generate_content(
            model=self.model, contents=prompt
        )
        next_speaker_name = response.text.strip()

        # Match the name to an agent - exact match first
        for agent in self.agents:
            if agent.name == next_speaker_name:
                return agent

        # If no match, select someone randomly
        print(
            f"Warning: Could not identify next speaker from '{next_speaker_name}', falling back to random selection"
        )
        last_speaker = self.transcript[-1]["speaker"]
        remaining_agents = [
            agent for agent in self.agents if agent.name != last_speaker
        ]
        selected = random.choice(remaining_agents)
        print(f"Random speaker selected: {selected.name}")
        return selected

    def generate_agent_response(self, agent):
        """Generate a response from the agent using Gemini."""
        prompt = self.generate_agent_prompt(agent)
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=prompt
            )
            message = response.text.strip()

            # Check if conclusion phrase is in the message
            if "the debate is now concluded" in message.lower():
                self.debate_concluded = True

            return message
        except Exception as e:
            print(f"Error generating response for {agent.name}: {e}")
            return f"[Error generating response for {agent.name}]"

    def generate_next_turn(self):
        """Generate the next turn in the debate, updating the transcript internally."""

        # Determine who speaks next
        speaker = self.determine_next_speaker()
        time.sleep(self.delay)

        # Generate the response
        message = self.generate_agent_response(speaker)
        time.sleep(self.delay)

        # Increment turn
        self.current_turn += 1

        # Record in transcript
        entry = {
            "turn": self.current_turn,
            "speaker": speaker.name,
            "message": message,
        }
        self.transcript.append(entry)

        # Check if debate is concluded
        if (
            "the debate is now concluded" in message.lower()
            or self.current_turn >= self.max_turns
        ):
            self.debate_concluded = True

        # Return entry for UI
        return {
            "turn": self.current_turn,
            "speaker": speaker.name,
            "role": speaker.role,
            "message": message,
        }
