# Debate AI

A Python web application to generate debates between AI agents using the Gemini API. The application allows users to define different AI personas and debate settings, then orchestrates a debate between these agents.

## Features

- Configure debate topics and parameters
- Define multiple AI agents with unique roles and personas
- AI-driven selection of which agent speaks next based on conversation flow
- Web interface for viewing real-time AI debates

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

**Run the web application using Streamlit**
```
streamlit run st_app.py
```
This will open the application in your default web browser (usually `http://localhost:8501`).
* Use the web interface to **create a new debate configuration** or **load an existing example**.

**Alternative: Flask Application**

1. **Configure your debate:** Edit the `debate_config.json` file or choose an example from `debate_examples/`. Define:
   * Debate title and description
   * Number of max turns
   * Agent profiles (name, role, persona)

2. **Run the Flask application:**
   ```
   python app.py
   ```

3. **Open a web browser** and navigate to `http://localhost:5000`.

4. The web interface will display the debate based on the loaded configuration.