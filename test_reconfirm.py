from adaptive_agent import call_adaptive_agent

result = call_adaptive_agent("What is 2 + 2?")
print("WANTS SEARCH:", result["wants_search"])
print("ANSWER:", result["answer"])
print("RAW:", result["raw_output"])