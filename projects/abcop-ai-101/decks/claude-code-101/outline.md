# Installing Claude Code

## 3 Install Options
- Claude Desktop
  - Best for viewing artifacts
- VS Code Extension
  - Best for working in code, editing specific sections
- Claude Code CLI
  - Most fancy features

This training will focus on Claude Code CLI, but most of these principles apply across the board

I'll note where differences occur


# How Does It Work?

## Multi-Turn Conversation

- Type some prompt (turn)
- Claude Answers (turn)
- Type another prompt (turn)
- Claude Answers again (turn)

What's actually happening here?
- Every turn, the entire chat history is included
- Context builds up over time

Every subsequent prompt fills up the model's "Memory" aka the Context Window

## Context Window
- A memory-load that the agent carries of the current session

### Too Much Context
- lots of information to process, some of it contradictory
- Hallucinations, mistakes
- Takes effort to clear up memory

Example: Think of Simon Says game:
  - Red, Red+Green, Red+Green+Green, Red+Green+Green+Blue 
  - Go on long enough, and you'll make a mistake because it's too hard to remember

### Too Little Context
- very little information
- Making educated guesses
- Takes effort to investigate and gather information

Example: Bug Reporting
  - A good bug report describes the issue, Steps to Reproduce and Expected vs Actual
  - "It doesn't work" or "Page doesn't look right"

### Just Right Context
- Enough information to get the job done
- Making informed guesses
- Has everything it needs to do the task (might still do some small investigation)


# Getting it Just Right

## Starting Strong
Two main strategies

- Prompt Engineering
  - Writing a good and useful prompt

- Claude Setup
  - Good supporting files

## Prompt Engineering

The Five S's (Not an industry term, just something I find helpful)
- Situation - What's the situation? What are you trying to do?
- Single Task — one thing per ask
- Short Sentences — longer isn't better
- Specific Examples — copy+paste examples, reference files
- Success Criteria — what "done" looks like

Example:
- "Fix the login bug and any other bugs you find along the way and make no mistakes"

Fixed:
- "Fix the login bug in @Login.tsx. Here is an error log describing the issue: <pasted_text>. Tests need to pass and tsc needs to compile without issues"

Situation - Trying to fix a bug
Single Task - Focused on just one bug in login
Short Sentences - 3 simple senteces vs 1 run-on
Specific Examples - linked @Login.tsx and copy+pasted the error logs
Success Criteria - Tests should pass and tsc compilation should not raise issues

Fill out what you can - general guidelines, not hard rules

Tool for later that should help

## Claude Setup

Prompt Engineering still important, but less so with a good Claude Setup

Smartly imports context from supporting files through different mechanisms

- Memories
  - CLAUDE.md, AutoMemory, Rules (.claude/rules/*.md)
  - Map of your project, important commands, gotchas

- Skills
  - Repeatable instructions for common workflows

Examples:
- CLAUDE.md
```
<come up with example>
```

- SKILL.md
```
<come up with example>
```

## How they Fit In

During your session, Claude will load in context automatically
- Automatically at the start of the session
- When reading/writing specific files
- When doing a specific task

### CLAUDE.md
- Loads at start
- User/Project levels

### MEMORY.md
- Auto-managed by Claude
- Stored at the user/global level, but per-project

### Rules
- Load globally or for specific files or subfolders

### Skills
- Invoked deliberately or "Smartly" by Claude



## CLAUDE.md

Project-Level:
- Include architecture notes
- build, test, deploy
- Important details about the code
- ReadMe.md
- Link to external documents

/init to set up a project-level CLAUDE.md

User-Level:
- Applies to all claude sessions
- Use sparingly

MEMORY.md
- Project-level
- Claude-managed


## Rules
Path-Scoped
- When reading files at a specific path
- Separate guidance for *.cs vs *.ts
<list example>

Global
- functionally similar to CLAUDE.md


## Skills
Encompasses a repeatable task(s) or workflow

- Simple list of steps
- Complex set of branches
- Recipe or Instruction book

# Good Practices

## model selection

### Haiku
- Quick lookup

### Sonnet
- Good for most standard coding tasks

### Opus
- Best for complex tasks, planning

## Plan Mode
- Forces claude to gather as much information as it can
- Review the plan before working
- Huge token saver, since this lets you see the work to be done - you can redirect accordingly

## Context Management

### clear
Moving on to a new task?
- Open a new chat, or /clear

### rewind
Mistake or unhappy with prompt?
- rather than re-prompt, rewind to a previous point in the conversation

### compact
Out of memory but still need to work?
- compact <describe the information you want to retain>


## Abcop Playbooks
Review the install process
Preview some of the rules
Preview some of the skills

### prompt-helper

### karpathy.md


## Favorite Pro-Tips

### brainstorming

### diagnose

### adversarial-review

### simplify

### findskills



