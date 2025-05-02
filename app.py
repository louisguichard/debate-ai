from flask import (
    Flask,
    render_template,
    jsonify,
    Response,
    stream_with_context,
    request,
)
from dotenv import load_dotenv
from debate import Debate
import json
import time
import os

# Load environment variables
load_dotenv()

# Configure Flask app
app = Flask(__name__)

# Global variable to store debate
debate = None


@app.route("/")
def index():
    """Render the main debate page."""
    # Get list of debate examples
    debate_examples = []
    for filename in os.listdir("debate_examples"):
        if filename.endswith(".json"):
            with open(os.path.join("debate_examples", filename), "r") as f:
                config = json.load(f)
                debate_examples.append(
                    {"filename": filename, "title": config.get("title", "Untitled")}
                )

    return render_template("index.html", debate_examples=debate_examples)


@app.route("/start", methods=["POST"])
def start_debate():
    """Start the debate with specified config."""
    global debate
    config_path = request.json.get("config_path", "debate_config.json")
    print(f"Starting debate with config: {config_path}")
    debate = Debate(config_path=config_path)
    debate.start()
    return jsonify(debate.get_state())


@app.route("/create_config", methods=["POST"])
def create_config():
    """Create a new debate configuration from form data."""
    config_data = request.json

    # Save the configuration to a file
    with open("debate_config.json", "w") as f:
        json.dump(config_data, f, indent=4)

    return jsonify({"success": True, "config_path": "debate_config.json"})


@app.route("/stop", methods=["POST"])
def stop_debate():
    """Stop the debate."""
    debate.stop()
    return jsonify(debate.get_state())


@app.route("/resume", methods=["POST"])
def resume_debate():
    """Resume the debate."""
    debate.start()
    return jsonify(debate.get_state())


@app.route("/reset", methods=["POST"])
def reset_debate():
    """Reset the debate state."""
    debate.reset()
    return jsonify({})


@app.route("/next_turn", methods=["POST"])
def next_turn():
    """Generate the next debate turn."""
    debate.run_next_turn()
    debate.update_next_speaker()
    return jsonify(debate.get_state())


@app.route("/stream_debate")
def stream_debate():
    """Stream debate updates using Server-Sent Events (SSE)."""

    def generate():
        global debate
        # if not debate or not debate.debate_running:
        #     # Send initial empty state if no debate is running
        #     yield f"data: {json.dumps({})}\n\n"
        #     return

        while debate and debate.debate_running and not debate.debate_finished:
            if debate.current_turn >= debate.max_turns:
                debate.stop()
                yield f"data: {json.dumps(debate.get_state())}\n\n"
                break

            # Generate next turn
            debate.run_next_turn()

            # Update next speaker after a turn
            if not debate.debate_finished:
                debate.update_next_speaker()

            # Send the updated state as an SSE event
            yield f"data: {json.dumps(debate.get_state())}\n\n"

            # Wait a bit before next turn
            time.sleep(3)

        # Send final state update
        if debate:
            yield f"data: {json.dumps(debate.get_state())}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    app.run(debug=True)
