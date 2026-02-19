#!/usr/bin/env python3
"""
Natural Language Workflow Builder

Allows non-technical users to create AI agent workflows through
a simple conversational interface with multiple-choice questions.

Supports both text AND voice input!

No YAML knowledge required. No coding needed.
"""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# Voice input support
VOICE_AVAILABLE = False
try:
    import speech_recognition as sr

    VOICE_AVAILABLE = True
except ImportError:
    pass  # Voice not available, will use text-only


def get_voice_input(prompt: str = "Listening...", timeout: int = 5) -> str | None:
    """
    Get voice input from microphone.

    Returns transcribed text, or None if voice not available or failed.
    """
    if not VOICE_AVAILABLE:
        return None

    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print(f"🎤 {prompt}")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Listen with timeout
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

        # Use Google's free speech recognition
        text = recognizer.recognize_google(audio)
        print(f'   Heard: "{text}"')
        return text.lower().strip()

    except sr.WaitTimeoutError:
        print("   ⏱️ No speech detected (timeout)")
        return None
    except sr.UnknownValueError:
        print("   ❓ Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"   ❌ Speech service error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Voice error: {e}")
        return None


def install_voice_support():
    """Install voice input dependencies"""
    import subprocess

    print("📦 Installing voice support...")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "SpeechRecognition",
                "pyaudio",
                "--break-system-packages",
                "-q",
            ],
            check=True,
        )
        print("✅ Voice support installed! Restart to use voice input.")
        return True
    except Exception as e:
        print(f"❌ Failed to install: {e}")
        print("   Manual install: pip install SpeechRecognition pyaudio")
        return False


class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    YES_NO = "yes_no"
    TEXT = "text"
    NUMBER = "number"


@dataclass
class Choice:
    """A choice for multiple-choice questions"""

    key: str  # "a", "b", "c" etc.
    label: str
    description: str = ""
    value: Any = None


@dataclass
class Question:
    """A question to ask the user"""

    id: str
    text: str
    question_type: QuestionType
    choices: list[Choice] = field(default_factory=list)
    default: str | None = None
    help_text: str = ""
    required: bool = True

    @property
    def options(self) -> list[str]:
        """Get options as simple strings for display"""
        return [f"{c.key}) {c.label}" for c in self.choices]


@dataclass
class WorkflowConfig:
    """Configuration built from user responses"""

    name: str = ""
    description: str = ""
    goal: str = ""
    agents: list[str] = field(default_factory=list)
    needs_verification: bool = True
    needs_approval: bool = False
    guardrails: list[str] = field(default_factory=list)
    output_format: str = "yaml"


class ConversationBuilder:
    """
    Conversational workflow builder that guides users through
    creating agent teams with natural language.

    Example:
        builder = ConversationBuilder()

        # In a loop:
        question = builder.get_current_question()
        print(question.text)
        for choice in question.choices:
            print(f"  {choice.key}) {choice.label}")

        answer = input("> ")
        builder.answer(answer)

        if builder.is_complete():
            yaml_content = builder.generate_yaml()
    """

    def __init__(self):
        self.config = WorkflowConfig()
        self.current_step = 0
        self.answers: dict[str, Any] = {}
        self._build_questions()

    def _build_questions(self):
        """Build the question flow with helpful examples"""
        self.questions = [
            # Step 1: What do you want to build?
            Question(
                id="goal",
                text="👋 Hi! What would you like your AI team to help you with?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "a",
                        "Build a new feature ⭐ Most Popular",
                        "Ex: 'Add user login', 'Create dashboard', 'Build API endpoint'",
                        "feature",
                    ),
                    Choice(
                        "b",
                        "Fix a bug",
                        "Ex: 'Fix crash on login', 'Debug slow query', 'Resolve timeout'",
                        "bugfix",
                    ),
                    Choice(
                        "c",
                        "Write content",
                        "Ex: 'Write blog post', 'Create documentation', 'Draft email'",
                        "content",
                    ),
                    Choice(
                        "d",
                        "Review & improve code",
                        "Ex: 'Review PR #123', 'Optimize performance', 'Security audit'",
                        "review",
                    ),
                    Choice(
                        "e",
                        "Something else",
                        "I'll describe my custom task in the next step",
                        "custom",
                    ),
                ],
                help_text="Just pick what sounds closest - you can customize later!",
            ),
            # Step 2: Custom goal (if "something else")
            Question(
                id="custom_goal",
                text="📝 Great! Describe what you'd like the AI team to do:",
                question_type=QuestionType.TEXT,
                help_text="Examples: 'Migrate database to PostgreSQL', 'Refactor auth module', 'Generate test data'",
                required=False,  # Only shown if "custom" selected
            ),
            # Step 3: Name your workflow
            Question(
                id="name",
                text="🏷️ What should we call this workflow?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "a",
                        "feature-builder",
                        "Good for: new features, components, modules",
                        "feature-builder",
                    ),
                    Choice(
                        "b",
                        "bug-fixer",
                        "Good for: debugging, fixing issues, patches",
                        "bug-fixer",
                    ),
                    Choice(
                        "c",
                        "content-creator",
                        "Good for: docs, articles, reports, emails",
                        "content-creator",
                    ),
                    Choice(
                        "d",
                        "code-reviewer",
                        "Good for: PRs, audits, refactoring",
                        "code-reviewer",
                    ),
                    Choice(
                        "e",
                        "custom-workflow",
                        "I'll use my own name (type it next)",
                        "custom",
                    ),
                ],
                help_text="Pick a name or choose 'custom' to type your own",
            ),
            # Step 3b: Custom name (if "custom" selected)
            Question(
                id="custom_name",
                text="🏷️ Type your workflow name:",
                question_type=QuestionType.TEXT,
                default="my-workflow",
                help_text="Use lowercase with dashes, like: my-cool-workflow",
                required=False,
            ),
            # Step 4: Which agents do you need?
            Question(
                id="agents",
                text="🤖 Which AI agents should be on your team?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "a",
                        "Full team ⭐ Recommended",
                        "5 agents: Planner→Developer→Verifier→Tester→Reviewer (thorough)",
                        "full",
                    ),
                    Choice(
                        "b",
                        "Quick team (3 agents)",
                        "Planner→Developer→Verifier (fast, good for small tasks)",
                        "quick",
                    ),
                    Choice(
                        "c",
                        "Research & Write team",
                        "Researcher→Analyst→Writer (great for content/docs)",
                        "research",
                    ),
                    Choice(
                        "d",
                        "Solo developer",
                        "Just 1 Developer agent (fastest, simple tasks only)",
                        "single",
                    ),
                    Choice(
                        "e",
                        "Let me pick specific agents",
                        "Choose exactly which agents you want",
                        "custom",
                    ),
                ],
                help_text="Full team catches more mistakes; Quick team is faster",
            ),
            # Step 5: Custom agents (if "let me pick")
            Question(
                id="custom_agents",
                text="👥 Which agents do you want? (type numbers separated by commas)",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice("1", "📋 Planner", "Breaks big tasks into clear steps"),
                    Choice("2", "💻 Developer", "Writes and modifies code"),
                    Choice("3", "🔍 Verifier", "Checks code quality & correctness"),
                    Choice("4", "🧪 Tester", "Writes and runs tests"),
                    Choice("5", "⭐ Reviewer", "Final approval before done"),
                    Choice("6", "🔬 Researcher", "Gathers info from docs/web"),
                    Choice("7", "✍️ Writer", "Creates written content"),
                    Choice("8", "📊 Analyst", "Analyzes data & finds insights"),
                ],
                help_text="Popular combos: '1,2,3' (plan-code-verify) or '6,8,7' (research-analyze-write)",
                required=False,
            ),
            # Step 6: Should agents verify each other?
            Question(
                id="verification",
                text="🔍 Should agents double-check each other's work?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "y",
                        "Yes ⭐ Recommended",
                        "Verifier reviews Developer's code (catches 90% of bugs early!)",
                        True,
                    ),
                    Choice(
                        "n",
                        "No, skip verification",
                        "Faster but may miss mistakes (only for quick prototypes)",
                        False,
                    ),
                ],
                default="y",
                help_text="Cross-verification adds ~30 sec but catches most bugs",
            ),
            # Step 7: Human approval needed?
            Question(
                id="approval",
                text="👤 Do you want to approve actions before they run?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "y",
                        "Yes, I'll review first",
                        "Pause for your approval before: deploys, file changes, API calls",
                        True,
                    ),
                    Choice(
                        "n",
                        "No, run automatically ⭐ Recommended",
                        "AI team works autonomously (you can still see all logs)",
                        False,
                    ),
                ],
                default="n",
                help_text="Use 'Yes' for production deploys; 'No' for dev/testing",
            ),
            # Step 8: Safety guardrails
            Question(
                id="guardrails",
                text="🛡️ What safety level do you want?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "a",
                        "Standard ⭐ Recommended",
                        "Blocks: passwords, API keys, credit cards, toxic content",
                        "standard",
                    ),
                    Choice(
                        "b",
                        "Maximum security",
                        "All above + rate limiting + extra content checks",
                        "maximum",
                    ),
                    Choice(
                        "c",
                        "Minimal",
                        "Just toxic content filter (faster, less protection)",
                        "minimal",
                    ),
                    Choice(
                        "d",
                        "None (not recommended)",
                        "No safety checks (only for isolated testing)",
                        "none",
                    ),
                ],
                default="a",
                help_text="Standard is great for most use cases",
            ),
            # Step 9: Confirm
            Question(
                id="confirm",
                text="✅ Ready to create your workflow?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                choices=[
                    Choice(
                        "y",
                        "Yes, generate it! 🚀",
                        "Creates YAML + Python code you can run immediately",
                        True,
                    ),
                    Choice(
                        "n", "No, start over", "Go back to the first question", False
                    ),
                ],
                help_text="You can always edit the generated files later",
            ),
        ]

    def get_current_question(self) -> Question | None:
        """Get the current question to ask"""
        if self.current_step >= len(self.questions):
            return None

        question = self.questions[self.current_step]

        # Skip conditional questions if not applicable
        if question.id == "custom_goal" and self.answers.get("goal") != "custom":
            self.current_step += 1
            return self.get_current_question()

        if question.id == "custom_name" and self.answers.get("name") != "custom":
            self.current_step += 1
            return self.get_current_question()

        if question.id == "custom_agents" and self.answers.get("agents") != "custom":
            self.current_step += 1
            return self.get_current_question()

        return question

    def answer(self, response: str) -> bool:
        """
        Process user's answer.

        Returns True if answer was valid, False if invalid.
        """
        question = self.get_current_question()
        if question is None:
            return False

        response = response.strip().lower()

        # Validate based on question type
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            valid_keys = [c.key.lower() for c in question.choices]
            if response not in valid_keys:
                return False
            # Store the value, not the key
            for choice in question.choices:
                if choice.key.lower() == response:
                    self.answers[question.id] = (
                        choice.value if choice.value is not None else response
                    )
                    break

        elif question.question_type == QuestionType.YES_NO:
            if response in ["y", "yes", "yeah", "yep", "1", "true"]:
                self.answers[question.id] = True
            elif response in ["n", "no", "nope", "0", "false"]:
                self.answers[question.id] = False
            else:
                return False

        elif question.question_type == QuestionType.TEXT:
            if question.required and not response:
                response = question.default or ""
            self.answers[question.id] = response

        elif question.question_type == QuestionType.NUMBER:
            try:
                self.answers[question.id] = int(response)
            except ValueError:
                return False

        # Handle special case: "confirm" = no means go back
        if question.id == "confirm" and self.answers.get("confirm") is False:
            self.current_step = 0  # Start over
            self.answers = {}
            return True

        self.current_step += 1
        return True

    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return self.current_step >= len(self.questions)

    def get_progress(self) -> tuple[int, int]:
        """Get current progress (current, total)"""
        return (self.current_step + 1, len(self.questions))

    def _get_agents_list(self) -> list[str]:
        """Convert agent selection to list"""
        agents_choice = self.answers.get("agents", "full")

        agent_presets = {
            "full": ["planner", "developer", "verifier", "tester", "reviewer"],
            "quick": ["planner", "developer", "verifier"],
            "research": ["researcher", "analyst", "writer"],
            "single": ["developer"],
        }

        if agents_choice == "custom":
            custom = self.answers.get("custom_agents", "1,2,3")
            agent_map = {
                "1": "planner",
                "2": "developer",
                "3": "verifier",
                "4": "tester",
                "5": "reviewer",
                "6": "researcher",
                "7": "writer",
                "8": "analyst",
            }
            return [
                agent_map[n.strip()]
                for n in custom.split(",")
                if n.strip() in agent_map
            ]

        return agent_presets.get(agents_choice, agent_presets["full"])

    def _get_guardrails_list(self) -> list[str]:
        """Convert guardrails selection to list"""
        choice = self.answers.get("guardrails", "standard")

        guardrail_presets = {
            "maximum": ["content-filter", "pii-detection", "rate-limiter"],
            "standard": ["content-filter", "pii-detection"],
            "minimal": ["content-filter"],
            "none": [],
        }

        return guardrail_presets.get(choice, guardrail_presets["standard"])

    def generate_yaml(self) -> str:
        """Generate YAML workflow from collected answers"""
        # Handle custom name vs preset name
        name_choice = self.answers.get("name", "custom-workflow")
        if name_choice == "custom":
            name = (
                self.answers.get("custom_name", "my-workflow").lower().replace(" ", "-")
            )
        else:
            name = name_choice.lower().replace(" ", "-")
        goal = self.answers.get("goal", "feature")
        custom_goal = self.answers.get("custom_goal", "")
        agents = self._get_agents_list()
        verification = self.answers.get("verification", True)
        approval = self.answers.get("approval", False)
        guardrails = self._get_guardrails_list()

        # Build description
        descriptions = {
            "feature": "Build new features with planning, implementation, and verification",
            "bugfix": "Find and fix bugs systematically",
            "content": "Research and create written content",
            "review": "Review code and suggest improvements",
            "custom": custom_goal or "Custom workflow",
        }
        description = descriptions.get(goal, "Custom workflow")

        # Build YAML
        lines = [
            f"# {name.replace('-', ' ').title()} Workflow",
            "# Generated by Agenticom Workflow Builder",
            "",
            f"id: {name}",
            f"name: {name.replace('-', ' ').title()}",
            "description: |",
            f"  {description}",
            "",
            "agents:",
        ]

        # Add agents
        for agent in agents:
            lines.append(f"  - role: {agent}")
            if guardrails and agent in ["planner", "developer"]:
                lines.append("    guardrails:")
                for g in guardrails:
                    lines.append(f"      - {g}")

        lines.append("")
        lines.append("steps:")

        # Generate steps based on agents
        step_templates = {
            "planner": {
                "id": "plan",
                "input": "Create a detailed plan for: {task}",
                "expects": "Clear step-by-step plan with acceptance criteria",
            },
            "researcher": {
                "id": "research",
                "input": "Research the following topic: {task}",
                "expects": "Comprehensive research notes with sources",
            },
            "developer": {
                "id": "implement",
                "input": "Implement the following: {plan}",
                "expects": "Working code that meets requirements",
            },
            "writer": {
                "id": "write",
                "input": "Write content based on: {research}",
                "expects": "Well-structured, clear content",
            },
            "analyst": {
                "id": "analyze",
                "input": "Analyze: {research}",
                "expects": "Key insights and actionable conclusions",
            },
            "verifier": {
                "id": "verify",
                "input": "Verify the work: {implement}",
                "expects": "All acceptance criteria met",
            },
            "tester": {
                "id": "test",
                "input": "Test: {implement}",
                "expects": "All tests passing",
            },
            "reviewer": {
                "id": "review",
                "input": "Final review: {implement}",
                "expects": "Approved for deployment",
            },
        }

        prev_step = "task"
        for i, agent in enumerate(agents):
            if agent not in step_templates:
                continue

            template = step_templates[agent]
            step_id = template["id"]

            lines.append(f"  - id: {step_id}")
            lines.append(f"    agent: {agent}")

            # Update input reference
            input_text = template["input"]
            if prev_step != "task":
                input_text = input_text.replace("{task}", f"{{{prev_step}}}")
            lines.append(f'    input: "{input_text}"')
            lines.append(f'    expects: "{template["expects"]}"')

            # Add verification
            if verification and agent == "developer" and "verifier" in agents:
                lines.append("    verified_by: verifier")
                lines.append("    max_retries: 3")

            # Add approval for final step
            if approval and i == len(agents) - 1:
                lines.append("    requires_approval: true")

            lines.append("")
            prev_step = step_id

        return "\n".join(lines)

    def generate_python(self) -> str:
        """Generate Python code from collected answers"""
        # Handle custom name vs preset name
        name_choice = self.answers.get("name", "custom-workflow")
        if name_choice == "custom":
            name = (
                self.answers.get("custom_name", "my-workflow").lower().replace(" ", "-")
            )
        else:
            name = name_choice.lower().replace(" ", "-")
        agents = self._get_agents_list()
        verification = self.answers.get("verification", True)
        approval = self.answers.get("approval", False)
        guardrails = self._get_guardrails_list()

        lines = [
            "# Generated by Agenticom Workflow Builder",
            "from orchestration import (",
            "    TeamBuilder,",
            "    AgentRole,",
        ]

        if guardrails:
            lines.append("    GuardrailPipeline,")
            if "content-filter" in guardrails:
                lines.append("    ContentFilter,")
            if "pii-detection" in guardrails:
                lines.append("    PIIGuardrail,")
            if "rate-limiter" in guardrails:
                lines.append("    RateLimiter,")

        lines.extend(
            [
                ")",
                "",
                "# Build the team",
                f'team = (TeamBuilder("{name}")',
            ]
        )

        # Add agents
        for agent in agents:
            lines.append(f"    .with_{agent}()")

        # Add steps
        role_map = {
            "planner": "AgentRole.PLANNER",
            "developer": "AgentRole.DEVELOPER",
            "verifier": "AgentRole.VERIFIER",
            "tester": "AgentRole.TESTER",
            "reviewer": "AgentRole.REVIEWER",
            "researcher": "AgentRole.RESEARCHER",
            "writer": "AgentRole.WRITER",
            "analyst": "AgentRole.ANALYST",
        }

        prev_step = "task"
        for i, agent in enumerate(agents):
            step_id = agent[:4]  # Short id
            role = role_map.get(agent, "AgentRole.DEVELOPER")

            step_line = f'    .step("{step_id}", {role}, "Process: {{{prev_step}}}"'

            if verification and agent == "developer" and "verifier" in agents:
                step_line += ", verified_by=AgentRole.VERIFIER"

            if approval and i == len(agents) - 1:
                step_line += ", requires_approval=True"

            step_line += ")"
            lines.append(step_line)
            prev_step = step_id

        lines.extend(
            [
                "    .build())",
                "",
                "# Run the workflow",
                "import asyncio",
                'result = asyncio.run(team.run("Your task here"))',
                'print(f"Success: {result.success}")',
            ]
        )

        return "\n".join(lines)

    def get_summary(self) -> str:
        """Get a human-readable summary of the configuration"""
        agents = self._get_agents_list()
        guardrails = self._get_guardrails_list()

        summary = [
            "",
            "📋 Your Workflow Summary:",
            "─" * 40,
            f"  Name: {self.answers.get('name', 'my-workflow')}",
            f"  Goal: {self.answers.get('goal', 'feature')}",
            "",
            f"  Agents ({len(agents)}):",
        ]

        agent_icons = {
            "planner": "📋",
            "developer": "💻",
            "verifier": "🔍",
            "tester": "🧪",
            "reviewer": "⭐",
            "researcher": "🔬",
            "writer": "✍️",
            "analyst": "📊",
        }

        for agent in agents:
            icon = agent_icons.get(agent, "🤖")
            summary.append(f"    {icon} {agent.title()}")

        summary.extend(
            [
                "",
                f"  Cross-verification: {'✅ Yes' if self.answers.get('verification') else '❌ No'}",
                f"  Human approval: {'✅ Yes' if self.answers.get('approval') else '❌ No'}",
                "",
                f"  Guardrails ({len(guardrails)}):",
            ]
        )

        guardrail_icons = {
            "content-filter": "🚫",
            "pii-detection": "🔐",
            "rate-limiter": "⏱️",
        }

        for g in guardrails:
            icon = guardrail_icons.get(g, "🛡️")
            summary.append(f"    {icon} {g}")

        if not guardrails:
            summary.append("    (none)")

        summary.append("─" * 40)

        return "\n".join(summary)


def run_conversation(voice_mode: bool = False) -> str | None:
    """
    Run the conversational workflow builder interactively.

    Args:
        voice_mode: If True, use voice input (falls back to text if unavailable)

    Returns the generated YAML content, or None if cancelled.
    """
    builder = ConversationBuilder()

    print("\n" + "=" * 50)
    print("🏢 AGENTICOM WORKFLOW BUILDER")
    print("=" * 50)

    # Voice mode setup
    use_voice = False
    if voice_mode:
        if VOICE_AVAILABLE:
            use_voice = True
            print("\n🎤 VOICE MODE ENABLED")
            print("   Speak your answer, or type to override")
        else:
            print("\n⚠️ Voice not available. Install with:")
            print("   pip install SpeechRecognition pyaudio")
            install = input("   Install now? (y/n): ").strip().lower()
            if install in ["y", "yes"]:
                install_voice_support()

    print("\nLet's create your AI team step by step.")
    if use_voice:
        print("🎤 Speak or type your answer (say the letter like 'A' or 'B')")
    else:
        print("Type your answer or press Enter for the default.\n")

    while not builder.is_complete():
        question = builder.get_current_question()
        if question is None:
            break

        current, total = builder.get_progress()
        print(f"\n[{current}/{total}] {question.text}")

        if question.help_text:
            print(f"   💡 {question.help_text}")

        if question.choices:
            print()
            for choice in question.choices:
                desc = f" - {choice.description}" if choice.description else ""
                print(f"   {choice.key}) {choice.label}{desc}")

        # Get input (voice or text)
        response = None

        if use_voice:
            print()
            voice_text = get_voice_input(
                "Say your choice (A, B, C...) or describe what you want:"
            )
            if voice_text:
                # Parse voice input - look for letter choices
                voice_lower = voice_text.lower()
                for choice in question.choices:
                    # Match "a", "option a", "choice a", "letter a", etc.
                    if (
                        voice_lower == choice.key.lower()
                        or f"option {choice.key.lower()}" in voice_lower
                        or f"choice {choice.key.lower()}" in voice_lower
                        or f"letter {choice.key.lower()}" in voice_lower
                        or choice.label.lower() in voice_lower
                    ):
                        response = choice.key.lower()
                        break

                # Also check for yes/no
                if response is None and question.question_type == QuestionType.YES_NO:
                    if any(
                        w in voice_lower
                        for w in ["yes", "yeah", "yep", "sure", "okay", "ok"]
                    ):
                        response = "y"
                    elif any(w in voice_lower for w in ["no", "nope", "nah"]):
                        response = "n"

                # For text questions, use the raw voice input
                if response is None and question.question_type == QuestionType.TEXT:
                    response = voice_text

                if response is None:
                    print(f"   🎤 Heard: '{voice_text}' - didn't match an option")

        # Fall back to text input
        if response is None:
            if question.default:
                prompt = f"> [{question.default}] "
            else:
                prompt = "> "

            response = input(prompt).strip()

        # Use default if empty
        if not response and question.default:
            response = question.default

        if not builder.answer(response):
            print("   ❌ Invalid answer, please try again.")

    if builder.is_complete():
        print(builder.get_summary())

        yaml_content = builder.generate_yaml()

        print("\n📄 Generated YAML:")
        print("─" * 40)
        print(yaml_content)
        print("─" * 40)

        # Get save confirmation
        save_response = None
        if use_voice:
            save_response = get_voice_input("Say 'yes' to save or 'no' to skip:")

        if save_response is None:
            save_response = input("\n💾 Save to file? (y/n) [y]: ").strip().lower()

        if save_response in ["", "y", "yes", "yeah", "yep", "save"]:
            # Get workflow name
            name_choice = builder.answers.get("name", "workflow")
            if name_choice == "custom":
                name = builder.answers.get("custom_name", "workflow")
            else:
                name = name_choice
            filename = f"{name}.yaml"
            Path(filename).write_text(yaml_content)
            print(f"   ✅ Saved to {filename}")

        return yaml_content

    return None


if __name__ == "__main__":
    run_conversation()
