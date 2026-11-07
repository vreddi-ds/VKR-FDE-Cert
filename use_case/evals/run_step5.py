import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "01_Product_Engineering/challenge"))
sys.path.insert(0, str(ROOT / "03_Retrieval/challenge"))
from dataclasses import replace

from app import research_mainframe_incident_history

from helpers.simulation import (
    simulate, scripted_user, make_llm_user,
    binary_judge, reached_goal, used_tools,
    efficiency, no_repeated_questions,
    no_errors, pass_k,
)
from use_case.evals.scenarios import SCENARIOS

MODEL = {"model": "anthropic/claude-haiku-4-5-20251001"}
OUTPUT = ROOT / "use_case/evals/tc4_step5_results.json"

def mara_agent(traj):
    question = next(
        text for speaker, text in reversed(traj.turns)
        if speaker == "user"
    )
    return research_mainframe_incident_history(question)

# Trying to send all questions instead of the latest. Since this not a conversational app. Just rying to simulate for learning purposes.
# def mara_agent(traj):
#     question = "\n".join(
#         text for speaker, text in traj.turns
#         if speaker == "user"
#     )
#     return research_mainframe_incident_history(question)

def score_trajectory(traj):
    return {
        "llm_judge": binary_judge(traj, MODEL),
        "reached_goal": reached_goal(traj),
        "used_tools": used_tools(traj),
        "efficiency": efficiency(traj),
        "no_repeated_questions": no_repeated_questions(traj),
        "no_errors": no_errors(traj),
    }

results = []

def save():
    OUTPUT.write_text(json.dumps(results, indent=2))

def run(scenario, user, mode, repeat):
    simulation_number = len(results) + 1

    print(
        f"\nSimulation {simulation_number}/12 | "
        f"{scenario.name} | {mode} | repeat {repeat}",
        flush=True,
    )
    # prevent the simulation from stopping prematurely when it detects keywords.
    # The reached_goal metric no longer uses the original success-keyword criteria.
    # It reflects the simulation's termination behavior, so it should not be treated as an independent measure of MARA's correctness.
    simulation_scenario = replace(scenario, success=[])
    traj = simulate(simulation_scenario, mara_agent, user)
    scores = score_trajectory(traj)

    record = {
        "simulation_number": simulation_number,
        "scenario": scenario.name,
        "mode": mode,
        "repeat": repeat,
        "turns": traj.agent_turns,
        "ended_because": traj.ended_because,
        "scores": scores,
        "errors": traj.errors,
        "transcript": traj.transcript,
    }

    results.append(record)
    save()

    print(
        f"  Judge={scores['llm_judge']} "
        f"Goal={scores['reached_goal']} "
        f"Turns={traj.agent_turns} "
        f"Ended={traj.ended_because}",
        flush=True,
    )

# Single simulation smoke test
if "--smoke-test" in sys.argv:
    OUTPUT = ROOT / "use_case/evals/tc4_step5_smoke_test.json"
    run(SCENARIOS[0], scripted_user, "scripted", 1)
    print(f"\nSmoke-test results saved: {OUTPUT}")
    sys.exit(0)

# Full simulation run
for scenario in SCENARIOS:
    run(scenario, scripted_user, "scripted", 1)

llm_user = make_llm_user(MODEL)

for scenario in SCENARIOS:
    for repeat in range(1, 4):
        run(scenario, llm_user, "llm_user", repeat)

print("\nPASS^K (LLM-user repeats, using judge verdict):")
for scenario in SCENARIOS:
    runs = [
        r for r in results
        if r["scenario"] == scenario.name
        and r["mode"] == "llm_user"
    ]
    successes = sum(r["scores"]["llm_judge"] == 1.0 for r in runs)
    print(
        scenario.name,
        f"successes={successes}/3",
        f"pass^3={pass_k(successes, 3, 3):.3f}",
    )

print(f"\nResults saved: {OUTPUT}")

