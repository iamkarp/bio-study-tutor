# Claude as Orchestrator — Setup Guide for a New Machine

This guide explains how to configure Claude Code so it acts as an **orchestrator** that coordinates Codex CLI and OpenCode/Kimi for multi-model coding workflows. Every step was tested on macOS (zsh). Linux is identical; Windows users should adapt paths.

---

## What this gives you

- Claude Code is the **main brain**: it plans, implements, and makes final calls
- **Codex CLI** (OpenAI) reviews or implements patches independently
- **OpenCode + Kimi K2.5** (Alibaba Model Studio) gives a cheap second opinion via API
- **Model routing**: Opus for hard/risky work, Sonnet for routine implementation

---

## Prerequisites

| Tool | Install |
|---|---|
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` |
| Node.js ≥ 18 | `brew install node` or https://nodejs.org |
| Codex CLI | `npm install -g @openai/codex` |
| OpenCode | `npm install -g opencode-ai` |
| Python ≥ 3.10 | `brew install python` (for helper scripts) |

Verify after installing:

```bash
claude --version
codex --version
opencode --version
```

---

## Step 1: Authenticate Claude Code

```bash
claude auth login
```

Follow the browser prompt. Verify:

```bash
claude auth status
```

This is a one-time step per machine. The session is stored in `~/.claude/`.

---

## Step 2: Authenticate Codex (OAuth only — no API key needed)

```bash
codex login
```

This opens a browser for OpenAI OAuth. Once done, Codex stores credentials locally. You never need to set `OPENAI_API_KEY` if you use OAuth.

Verify:

```bash
codex --version
```

---

## Step 3: Install the orchestrator skill

```bash
mkdir -p ~/.claude/skills
```

Clone or copy the skill directory into place:

```bash
# Option A: clone the repo that contains the skill
git clone https://github.com/jkarpeles/study-tutor ~/.claude/skills/build-study-tutor-repo
# then symlink or copy the multi-agent skill folder:
cp -R ~/.claude/skills/build-study-tutor-repo/skill ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2

# Option B: copy manually if you already have the files
cp -R /path/to/claude-orchestrated-multi-agent-skill-v2 ~/.claude/skills/
```

The skill directory must contain at minimum:

```
~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/
  Skill.md
  scripts/
    multi_agent_delegate.py
    claude_model_router.py
  resources/
    decision_rules.md
  examples/
    workflows.md
```

---

## Step 4: Wire the orchestration rules into global CLAUDE.md

The file `~/.claude/CLAUDE.md` is loaded into every Claude Code session automatically. Add the orchestration rules there so Claude knows to use this workflow without being told.

Open or create the file:

```bash
nano ~/.claude/CLAUDE.md   # or use any editor
```

Paste the following block (replace the skill path if yours differs):

```markdown
# Multi-Agent Orchestration (default workflow)

Claude Code is the **orchestrator and final decision-maker** for all coding work.
Full skill detail: `~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/Skill.md`

## Step 1 — Pick a Claude model

**Use Opus when:**
- Architecture, design, or ambiguous debugging
- Root-cause analysis or investigation
- High-risk changes: auth, billing, security, migrations, data loss, production
- Comparing/arbitrating conflicting reviewer outputs

**Use Sonnet when:**
- Well-scoped implementation or localized patch
- Tests, docs, boilerplate, renames
- Executing an already-approved plan
- Speed matters and the change is low-risk

**Default phase pattern:**
```
Opus → plan   →   Sonnet → implement   →   Codex/Kimi → review   →   Opus → arbitrate
```

Switch model mid-session with `/model`.

## Step 2 — Choose a route

| Route | Use when |
|---|---|
| `claude_only` | Simple task, no second opinion needed |
| `claude_then_codex_review` | Medium/large change, want OpenAI checking |
| `claude_then_qwen_review` | Cheaper review is enough |
| `codex_implement_then_claude_review` | Codex writes the patch, Claude reviews |
| `qwen_plan_then_claude_implement` | External plan first; Claude owns edits |
| `claude_then_codex_and_qwen_review` | High-risk: multiple reviewers |

## Step 3 — Delegate

```bash
# Codex review
python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/multi_agent_delegate.py \
  --target codex-review --include-git-diff --task "..."

# Kimi/OpenCode review
python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/multi_agent_delegate.py \
  --target qwen-review --include-git-diff --opencode-model "bailian-coding-plan/kimi-k2.5" --task "..."
```

## Step 4 — Final judgment

External outputs are **advice, not authority**. Claude decides. Always run tests after patching.
```

---

## Step 5: Configure OpenCode with Alibaba/Kimi K2.5

OpenCode is the bridge to models beyond Codex. The default model is **Kimi K2.5** via Alibaba's Model Studio (DashScope).

### 5a. Get an Alibaba API key

1. Go to https://dashscope.aliyuncs.com and create an account
2. Create an API key from the console

### 5b. Create the OpenCode config

```bash
mkdir -p ~/.config/opencode
```

Create `~/.config/opencode/opencode.json`, putting the key directly in the file. `~/.config/` is local to your machine and not in any git repo, so this is safe.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "bailian-coding-plan/kimi-k2.5",
  "provider": {
    "bailian-coding-plan": {
      "npm": "@ai-sdk/anthropic",
      "name": "Model Studio Coding Plan",
      "options": {
        "baseURL": "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic/v1",
        "apiKey": "sk-sp-your-key-here"
      },
      "models": {
        "kimi-k2.5": {
          "name": "Kimi K2.5",
          "modalities": {
            "input": ["text", "image"],
            "output": ["text"]
          },
          "options": {
            "thinking": {"type": "enabled", "budgetTokens": 8192}
          },
          "limit": {"context": 262144, "output": 32768}
        },
        "qwen3-coder-plus": {
          "name": "Qwen3 Coder Plus",
          "modalities": {
            "input": ["text"],
            "output": ["text"]
          },
          "limit": {"context": 1000000, "output": 65536}
        }
      }
    }
  }
}
```

### 5c. Verify

```bash
opencode --version
# OpenCode will pick up the key automatically when you run it
```

---

## Step 6: Verify the full stack

```bash
# 1. Claude Code is authenticated
claude auth status

# 2. Codex is authenticated
codex --version

# 3. OpenCode can reach Alibaba (requires ALIBABA_API_KEY in env)
opencode --version

# 4. Skill scripts are present
ls ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/

# 5. Model router works
python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/claude_model_router.py \
  --task "Add unit tests for a CSV parser"
```

---

## Day-to-day usage

### Inside a Claude Code session

Claude will automatically use the multi-agent workflow for non-trivial tasks because the rules are in `~/.claude/CLAUDE.md`. You can also invoke the skill explicitly:

```
Use the Claude-Orchestrated Multi-Agent Coding skill. You are the orchestrator.
```

### Switch Claude model mid-session

```
/model
```

Then pick Opus or Sonnet from the menu.

### Start a session on a specific model

```bash
claude --model opus    # for planning / architecture
claude --model sonnet  # for implementation
```

### Manually trigger a Codex review

```bash
python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/multi_agent_delegate.py \
  --target codex-review \
  --include-git-diff \
  --task "Review this patch for correctness and missing tests."
```

### Manually trigger a Kimi K2.5 review

```bash
python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/multi_agent_delegate.py \
  --target qwen-review \
  --include-git-diff \
  --opencode-model "bailian-coding-plan/kimi-k2.5" \
  --task "Review this diff for bugs and edge cases."
```

### Get a model routing recommendation

```bash
python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/claude_model_router.py \
  --task "Debug a production auth failure"

python ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/claude_model_router.py \
  --prefer-full-ids \
  --task "Add batch CSV import with transaction rollback"
```

---

## Decision logic at a glance

```
Is the task ambiguous, architectural, or high-risk?
  YES → Opus plans first
  NO  → Sonnet can handle it directly

Does the change touch auth / billing / data / prod infra / migrations?
  YES → use claude_then_codex_and_qwen_review (both reviewers)
  NO  → one reviewer is usually enough, or none for small patches

Is Codex quota a concern?
  YES → use qwen-review (Kimi K2.5 via Alibaba) instead
  NO  → use codex-review for the most precise OpenAI/Codex feedback

Who decides?
  Always Claude. External reviewers advise; Claude accepts, revises, or rejects.
```

---

## Authentication persistence

| Tool | Stored where | Re-auth needed |
|---|---|---|
| Claude Code | `~/.claude/` | No (persistent) |
| Codex | OS keychain / `~/.codex/` | No (persistent) |
| OpenCode/Kimi | `~/.config/opencode/opencode.json` + env var | Only if key changes |

All three authentications survive reboots. On a new machine, run each auth step once.

---

## Troubleshooting

**`claude auth status` shows unauthenticated** → Run `claude auth login` again.

**`codex` command not found** → `npm install -g @openai/codex`, then `codex login`.

**OpenCode returns auth error** → Check `echo $ALIBABA_API_KEY` is set in your current shell. Make sure it's in `~/.zshrc` (not just the current session).

**`multi_agent_delegate.py` fails with "file not found"** → Check the skill path matches what's in your `CLAUDE.md`. Run `ls ~/.claude/skills/claude-orchestrated-multi-agent-skill-v2/scripts/` to confirm.

**Claude doesn't use the multi-agent flow automatically** → Verify `~/.claude/CLAUDE.md` exists and contains the orchestration block. Open a fresh Claude Code session after editing it.
