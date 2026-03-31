---
name: Adversarial Algorithmic Implementation (TAP/PAIR/MCTS)
description: Implements tree-based attack branching and prompt refinement optimization.
---

# Red-Teaming Attacks Skill

## Trigger condition:
When building PersonaGenerators, AttackRunners, or executing simulated adversarial payloads against an Enterprise component.

## Supported Protocols:
You must strictly refer to `docs/AGENT_DECISION_TREE.md` to load Primary (`attack-algorithms.md`) and Secondary docs.

### TAP (Tree of Attacks with Pruning)
When orchestrating a TAP node via LangGraph:
1. **Branch Sequence**: Instruct the Attacker persona to generate N variations of an adversarial prompt.
2. **Prune Sequence 1**: Evaluator node evaluates out-of-bounds pretexts and deletes the branch.
3. **Attack Sequence**: Submits the payloads.
4. **Prune Sequence 2**: Analyze the target response. Drop branches that result in 100% adherence to standard guardrails. Retain only conversational branches with vulnerability flags.

### PAIR (Prompt Automatic Iterative Refinement)
For multi-turn, linear refinement:
- The closed-loop system must utilize Chain-of-Thought (CoT) to iteratively refine the target target's refusal message into a more plausible social-engineering pretext.

### MCTS (Monte Carlo Tree Search)
- Use MCTS to govern state spaces. If a node is rejected, calculate the Upper Confidence Bound applied to Trees (UCT) formula to switch strategies (e.g., from impersonating IT admin to a senior executive).
