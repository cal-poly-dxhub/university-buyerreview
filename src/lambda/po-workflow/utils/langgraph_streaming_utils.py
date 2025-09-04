import streamlit as st
import json
from state import PipelineState
import pandas as pd
import numpy as np


def safe_for_json(obj, skip_keys=None):
    if skip_keys is None:
        skip_keys = set()

    if isinstance(obj, float) and (obj != obj):  # NaN check
        return None
    elif isinstance(obj, bytes):
        return f"[{len(obj)} bytes]"
    elif isinstance(obj, pd.DataFrame):
        return obj.replace({np.nan: None}).to_dict(orient="records")
    elif isinstance(obj, dict):
        return {k: safe_for_json(v, skip_keys) for k, v in obj.items() if k not in skip_keys}
    elif isinstance(obj, list):
        return [safe_for_json(item, skip_keys) for item in obj]
    else:
        return obj


# ---- DEEP MERGE ----
def deep_update(d, u, path=""):
    changes = []
    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            sub_changes = deep_update(d[k], v, path + f"{k}.")
            changes.extend(sub_changes)
        else:
            if d.get(k) != v:
                changes.append(path + k)
            d[k] = v
    return changes

# ---- PIPELINE STREAM ----
async def run_json_pipeline_with_stream(uploaded_files, pipeline):
    initial_state: PipelineState = {"uploaded_files": uploaded_files}

    output_container = st.container()
    cumulative_state = {}
    changed_keys = []

    agent_counter = 0
    step_log = []

    async for step in pipeline.astream(initial_state):
        for agent_name, agent_output in step.items():
            agent_counter += 1
            step_log.append(agent_name)

            # Show per-agent output in expander
            with output_container.expander(f"✅ Agent: {agent_name}", expanded=False):
                st.json(agent_output)

            # Merge and track changes
            changed_keys = deep_update(cumulative_state, {agent_name: agent_output})

    # 🎉 Done
    st.sidebar.success(f"Pipeline Completed ✅")
    st.sidebar.markdown(f"**Agents Run:** {agent_counter}")
    st.sidebar.markdown("**Changed Keys:**")
    for key in changed_keys:
        st.sidebar.code(key)

    # 📦 Final State Viewer
    st.sidebar.markdown("### 🧾 Final JSON State")
    st.sidebar.json(cumulative_state)

        # Just before download:
    clean_output = safe_for_json(cumulative_state, skip_keys={"pdf_summary"})
    json_str = json.dumps(clean_output, indent=2)

    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name="classification_results.json",
        mime="application/json"
    )

    flattened_output = {}

    for agent_output in cumulative_state.values():
        if isinstance(agent_output, dict):
            for k, v in agent_output.items():
                flattened_output[k] = v

    return flattened_output
