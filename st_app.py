import streamlit as st
import os
import json
import time

from debate import Debate


# # # # # # # # # # # # #
# Page initialization
# # # # # # # # # # # # #


def load_debate_examples():
    debate_examples = []
    for filename in os.listdir("debate_examples"):
        with open(os.path.join("debate_examples", filename), "r") as f:
            config = json.load(f)
            debate_examples.append(config)
    debate_examples.sort(key=lambda x: x["title"])
    return debate_examples


def init_session_state():
    """Initialize all session state variables in one place for better organization."""

    if "debate_config" not in st.session_state:
        st.session_state.debate_config = None

    if "debate" not in st.session_state:
        st.session_state.debate = None

    if "debate_state" not in st.session_state:
        st.session_state.debate_state = {}

    if "agents" not in st.session_state:
        st.session_state.agents = [
            {"name": "", "role": "", "persona": "", "is_moderator": False}
        ]

    if "error_message" not in st.session_state:
        st.session_state.error_message = None

    if "debate_examples" not in st.session_state:
        st.session_state.debate_examples = load_debate_examples()

    if "create_expander" not in st.session_state:
        st.session_state.create_expander = True

    if "examples_expander" not in st.session_state:
        st.session_state.examples_expander = True

    if "add_agent" not in st.session_state:
        st.session_state.add_agent = False

    if "remove_agent" not in st.session_state:
        st.session_state.remove_agent = None

    if "moderator_idx" not in st.session_state:
        st.session_state.moderator_idx = None


# Initialize session variables
init_session_state()

# Title and subtitle
st.set_page_config(page_title="Debate AI", layout="wide")
st.markdown("<h1 style='text-align: center;'>💬 Debate AI</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3 style='text-align: center; color: grey;'>Watch AI agents debate topics in real-time</h3>",
    unsafe_allow_html=True,
)

# # # # # # # # # # # # #
# Debate configuration
# # # # # # # # # # # # #

col1, col2 = st.columns(2)

# Debate creation expander
with col1:
    st.markdown("### Create a new debate ✨")
    with st.expander(
        "Define the debate topic and participants",
        expanded=st.session_state.create_expander,
    ):
        # Add agent
        if st.session_state.add_agent:
            st.session_state.agents.append(
                {"name": "", "role": "", "persona": "", "is_moderator": False}
            )
            st.session_state.add_agent = False
            st.rerun()

        # Remove agent
        if st.session_state.remove_agent is not None:
            agent_idx = st.session_state.remove_agent
            st.session_state.agents.pop(agent_idx)
            st.session_state.remove_agent = None
            st.rerun()

        # Set moderator
        if st.session_state.moderator_idx is not None:
            mod_idx = st.session_state.moderator_idx
            for i in range(len(st.session_state.agents)):
                st.session_state.agents[i]["is_moderator"] = i == mod_idx

        # Debate form
        with st.form("create_debate_form"):
            title = st.text_input("Debate Title", "My Custom Debate")
            description = st.text_area(
                "Description", "A lively discussion on a custom topic."
            )
            max_turns = st.number_input(
                "Maximum Turns", min_value=1, max_value=100, value=20
            )
            agents = st.session_state.agents
            for i, agent in enumerate(agents):
                st.markdown(f"---\n**Participant {i + 1}**")
                agent_col1, agent_col2 = st.columns(2)

                with agent_col1:
                    agents[i]["name"] = st.text_input(
                        "Name",
                        value=agent.get("name", ""),
                        key=f"agent_name_form_{i}",
                    )

                with agent_col2:
                    agents[i]["role"] = st.text_input(
                        "Role",
                        value=agent.get("role", ""),
                        key=f"agent_role_form_{i}",
                    )

                agents[i]["persona"] = st.text_area(
                    "Persona (Optional)",
                    value=agent.get("persona", ""),
                    key=f"agent_persona_form_{i}",
                    height=100,
                )

                # Moderator checkbox and delete button
                _, moderator_col, _, delete_col, _ = st.columns([1, 4, 1, 4, 1])

                with moderator_col:
                    is_moderator = st.session_state.moderator_idx == i
                    if st.checkbox(
                        "Set as moderator",
                        value=is_moderator,
                        key=f"mod_{i}",
                    ):
                        st.session_state.moderator_idx = i
                    elif is_moderator:  # if it was checked but now unchecked
                        st.session_state.moderator_idx = None

                with delete_col:
                    if len(agents) > 1:
                        if st.form_submit_button(
                            f"❌ Remove participant {i + 1}",
                        ):
                            st.session_state.remove_agent = i

            st.markdown("---")
            st.write(" ")
            btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 3])

            with btn_col1:
                if st.form_submit_button(
                    "➕ Add participant", use_container_width=True
                ):
                    st.session_state.add_agent = True

            with btn_col3:
                if st.form_submit_button(
                    "Start debate 🚀", type="primary", use_container_width=True
                ):  # TODO: change color to green
                    # Create config
                    config = {
                        "title": title,
                        "description": description,
                        "max_turns": max_turns,
                        "agents": agents,
                    }
                    st.session_state.debate_config = config

                    # Collapse the expanders
                    if st.session_state.create_expander:
                        st.session_state.create_expander = False
                        st.session_state.examples_expander = False
                        st.rerun()

# Load existing debate expander
with col2:
    st.markdown("### Use a debate example 📂")
    with st.expander(
        "Select a debate example", expanded=st.session_state.examples_expander
    ):
        examples = st.session_state.debate_examples
        options_list = ["Select a debate to load..."] + [
            config["title"] for config in examples
        ]

        selected_example = st.selectbox(
            "Choose a debate:",
            options=options_list,
            index=0,
            label_visibility="collapsed",
        )

        if selected_example != "Select a debate to load...":
            st.session_state.debate_config = examples[
                options_list[1:].index(selected_example)
            ]
            # Collapse the expanders
            if st.session_state.examples_expander:
                st.session_state.create_expander = False
                st.session_state.examples_expander = False
                st.rerun()


# # # # # # # # # # # # #
# Start debate
# # # # # # # # # # # # #

st.markdown("--- ")  # Add a separator before the active debate

config = st.session_state.debate_config
if config:
    # Create debate object
    if not st.session_state.debate:
        debate = Debate(config)
        st.session_state.debate = debate
        debate.start()
        state = debate.get_state()
        st.session_state.debate_state = state
    else:
        # Use existing debate object
        debate = st.session_state.debate
        state = st.session_state.debate_state

    # Display debate info
    st.header(f"Debate: {state['title']}")
    st.caption(state["description"])

    # Controls
    col1, col2, col3 = st.columns([1.5, 3, 1.5])

    # Stop/resume debate button
    with col1:
        if state.get("is_running"):
            if st.button("⏹️ Stop Debate", use_container_width=True):
                debate.stop()
                st.session_state.debate_state = debate.get_state()
                st.rerun()
        elif not state.get("is_finished"):
            if st.button("▶️ Resume Debate", type="primary", use_container_width=True):
                debate.start()  # Resumes the debate
                st.session_state.debate_state = debate.get_state()
                st.rerun()

    # Reset & choose new debate button
    with col3:
        if st.button("🔄 Reset & Choose New", use_container_width=True):
            st.session_state.debate = None
            st.session_state.debate_state = {}
            st.session_state.debate_config = None
            st.session_state.agents = [
                {"name": "", "role": "", "persona": "", "is_moderator": False}
            ]
            st.session_state.add_agent = False
            st.session_state.remove_agent = None
            st.session_state.moderator_idx = None
            st.session_state.create_expander = True
            st.session_state.examples_expander = True
            st.rerun()

    # Status display
    if state.get("is_finished"):
        status_text = f"Status: 🏁 Finished after {state.get('current_turn', 0)} turns."
    elif state.get("is_running"):
        next_speaker = state.get("next_speaker", "...")
        status_text = f"Status: 🏃 Running (Turn {state.get('current_turn', 0)}/{state.get('max_turns', 'N/A')}) - Next: **{next_speaker}**"
    else:  # Paused
        status_text = f"Status: ⏸️ Paused (Turn {state.get('current_turn', 0)}/{state.get('max_turns', 'N/A')})"
    st.info(status_text)

    # Participants
    st.subheader("Participants")
    num_agents = len(state["agents"])
    cols = st.columns(min(num_agents, 4))  # Max 4 columns
    agent_index = 0
    for agent in state["agents"]:
        with cols[agent_index % len(cols)]:
            # Add a moderator badge if this agent is the moderator
            if agent.get("is_moderator", False):
                st.markdown(f"**{agent['name']}** 🎭")
            else:
                st.markdown(f"**{agent['name']}**")
            st.caption(f"_{agent['role']}_")
        agent_index += 1

    # Transcript
    st.subheader("Transcript")
    transcript_container = st.container(height=500)
    if state.get("transcript"):
        with transcript_container:
            for entry in state["transcript"]:
                with st.chat_message(name=entry["speaker"]):
                    st.markdown(entry["message"])
    else:
        with transcript_container:
            st.write("Debate hasn't started yet.")

    # Flow
    if debate and state.get("is_running") and not state.get("is_finished"):
        new_entry = debate.run_next_turn()
        if not debate.debate_finished:
            debate.update_next_speaker()
        st.session_state.debate_state = debate.get_state()
        if not debate.get_state().get("is_finished"):
            time.sleep(3)

        st.rerun()
