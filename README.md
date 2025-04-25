# Debate AI

A Python application to generate debates between AI agents using the Gemini API. The application allows users to define different AI personas and debate settings, then orchestrates a debate between these agents.

## Features

- Define multiple AI agents with unique roles and personas
- Include a moderator agent to guide the debate flow
- Configure debate topics and parameters
- AI-driven selection of which agent speaks next based on conversation flow

## Requirements

- Python
- Gemini API key

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

1. Configure your debate by editing the `debate_config.json` file. Define:
   - Debate title and description
   - Number of max turns 
   - Agent profiles (name, role, persona)

2. Run the application:
   ```
   python main.py
   ```

3. The debate will execute automatically, starting with the moderator introducing the topic and participants.

4. The debate will conclude when either:
   - Maximum turns are reached, or
   - The moderator concluding the debate.