import os

# ENV-like variable
OPENSOURCE = True  # change to False to switch to LangChain + LangGraph


# ----------------------------
# Open-source inference (gpt4all)
# ----------------------------
def run_gpt4all(prompt: str):
    from gpt4all import GPT4All

    # load a small model that fits in ~4GB RAM
    model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf")

    with model.chat_session() as session:
        response = session.generate(prompt)
        return response


# ----------------------------
# Proprietary inference (LangChain + LangGraph)
# ----------------------------
def run_langchain(prompt: str):
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, END
    from typing import TypedDict

    # Define simple state for LangGraph
    class State(TypedDict):
        input: str
        output: str

    # Initialize LLM via LangChain (using OpenAI API)
    llm = ChatOpenAI(model="gpt-3.5-turbo")

    # Define node
    def call_model(state: State):
        result = llm.invoke(state["input"])
        return {"output": result.content}

    # Build graph
    graph = StateGraph(State)
    graph.add_node("llm", call_model)
    graph.set_entry_point("llm")
    graph.add_edge("llm", END)

    app = graph.compile()

    result = app.invoke({"input": prompt})
    return result["output"]


# ----------------------------
# Select backend dynamically
# ----------------------------
def run_inference(prompt: str):
    if OPENSOURCE:
        return run_gpt4all(prompt)
    else:
        return run_langchain(prompt)


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    print(run_inference("Explain the difference between stars and planets in simple words."))
