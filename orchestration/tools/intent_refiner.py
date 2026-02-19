"""
Intent Refiner: Transform vague user input into well-defined prompts.

This module implements Progressive Intent Refinement (PIR):
1. PARSE - Classify intent and domain
2. PROBE - Ask smart clarification questions
3. EXTRACT - Pull specific details from input
4. MODEL - Build visual mental model
5. GENERATE - Create optimized system prompt with specifics
6. ITERATE - Refine until quality threshold met

Based on research in:
- Requirements Engineering (Goal-Oriented RE)
- Task-Oriented Dialogue Systems
- Cognitive Load Theory
- Prompt Engineering Best Practices
"""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# EXTRACTED SPECIFICS
# =============================================================================


@dataclass
class ExtractedSpecifics:
    """Specific details extracted from user input."""

    # Core entities
    entities: list[str] = field(default_factory=list)  # Companies, products, people
    technologies: list[str] = field(default_factory=list)  # Tech stack, tools
    metrics: list[str] = field(default_factory=list)  # Numbers, KPIs, targets

    # Context
    timeframes: list[str] = field(default_factory=list)  # Deadlines, durations
    locations: list[str] = field(default_factory=list)  # Geographic context
    stakeholders: list[str] = field(default_factory=list)  # Who's involved

    # Constraints and requirements
    constraints: list[str] = field(default_factory=list)  # Limitations, boundaries
    requirements: list[str] = field(default_factory=list)  # Must-haves
    preferences: list[str] = field(default_factory=list)  # Nice-to-haves

    # Problem context
    pain_points: list[str] = field(default_factory=list)  # Current problems
    goals: list[str] = field(default_factory=list)  # Desired outcomes
    comparisons: list[str] = field(default_factory=list)  # Competitors, benchmarks

    # Domain-specific
    domain_terms: list[str] = field(default_factory=list)  # Technical jargon

    # Original context
    key_phrases: list[str] = field(default_factory=list)  # Important phrases

    def to_context_string(self) -> str:
        """Convert to context string for prompt injection."""
        parts = []

        if self.entities:
            parts.append(f"Entities: {', '.join(self.entities)}")
        if self.technologies:
            parts.append(f"Technologies/Tools: {', '.join(self.technologies)}")
        if self.metrics:
            parts.append(f"Metrics/Targets: {', '.join(self.metrics)}")
        if self.timeframes:
            parts.append(f"Timeframe: {', '.join(self.timeframes)}")
        if self.stakeholders:
            parts.append(f"Stakeholders: {', '.join(self.stakeholders)}")
        if self.constraints:
            parts.append(f"Constraints: {', '.join(self.constraints)}")
        if self.requirements:
            parts.append(f"Requirements: {', '.join(self.requirements)}")
        if self.pain_points:
            parts.append(f"Current Problems: {', '.join(self.pain_points)}")
        if self.goals:
            parts.append(f"Desired Outcomes: {', '.join(self.goals)}")
        if self.comparisons:
            parts.append(f"Competitors/Benchmarks: {', '.join(self.comparisons)}")
        if self.domain_terms:
            parts.append(f"Domain Context: {', '.join(self.domain_terms)}")

        return "\n".join(parts)

    def has_specifics(self) -> bool:
        """Check if any specifics were extracted."""
        return bool(
            self.entities
            or self.technologies
            or self.metrics
            or self.timeframes
            or self.stakeholders
            or self.constraints
            or self.requirements
            or self.pain_points
            or self.goals
            or self.comparisons
            or self.domain_terms
            or self.key_phrases
        )


@dataclass
class QualityScore:
    """Quality evaluation of generated prompt."""

    overall: float = 0.0  # 0-1 score
    specificity: float = 0.0  # How specific vs generic
    completeness: float = 0.0  # All aspects covered
    actionability: float = 0.0  # Clear what to do
    context_preservation: float = 0.0  # Original context retained

    missing_elements: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)

    def meets_threshold(self, threshold: float = 0.7) -> bool:
        return self.overall >= threshold


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================


class TaskType(Enum):
    """Primary task categories."""

    ANALYSIS = "analysis"  # Understanding something
    CREATION = "creation"  # Making something new
    TRANSFORMATION = "transformation"  # Changing something existing
    DECISION = "decision"  # Choosing between options
    RESEARCH = "research"  # Finding information
    AUTOMATION = "automation"  # Recurring process


class Complexity(Enum):
    """Task complexity levels."""

    ATOMIC = "atomic"  # Single step, clear outcome
    COMPOSITE = "composite"  # Multiple steps, single goal
    EXPLORATORY = "exploratory"  # Goal discovered during work


class Domain(Enum):
    """Knowledge domains."""

    # Core domains
    TECHNICAL = "technical"  # Code, systems, data
    BUSINESS = "business"  # Strategy, operations, marketing, sales
    CREATIVE = "creative"  # Writing, design, content
    RESEARCH = "research"  # Academic, scientific
    PERSONAL = "personal"  # Life, productivity

    # Specialized domains
    SCIENCE = "science"  # Biology, chemistry, physics, quantum
    FINANCE = "finance"  # Stocks, crypto, real estate, investing
    HEALTH = "health"  # Medical, wellness, mental health
    LEGAL = "legal"  # Law, contracts, IP, compliance
    EDUCATION = "education"  # Teaching, learning, curriculum
    ENTERTAINMENT = "entertainment"  # Music, film, gaming, content creation
    FASHION = "fashion"  # Style, clothing, design
    ENTREPRENEURSHIP = "entrepreneurship"  # Startups, founding, scaling


@dataclass
class IntentClassification:
    """Classification of user intent."""

    task_type: TaskType
    complexity: Complexity
    domain: Domain
    confidence: float
    signals: list[str] = field(default_factory=list)


# =============================================================================
# ELICITATION FRAMEWORK
# =============================================================================


@dataclass
class ClarificationQuestion:
    """A question to clarify user intent."""

    question: str
    dimension: str  # What aspect this clarifies
    priority: int  # 1=must ask, 2=should ask, 3=nice to have
    options: list[str] = field(default_factory=list)  # Multiple choice options
    default: str | None = None  # Assumed if not asked
    information_gain: float = 0.5  # How much this changes the output


@dataclass
class ElicitedContext:
    """Context gathered through elicitation."""

    goal: str = ""  # What user ultimately wants
    success_criteria: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    audience: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    assumptions: dict[str, str] = field(default_factory=dict)
    uncertainties: list[str] = field(default_factory=list)


# =============================================================================
# MENTAL MODEL
# =============================================================================


@dataclass
class IntentModel:
    """Visual mental model of user intent."""

    # Core elements
    inputs: list[dict] = field(default_factory=list)
    process: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)

    # Metadata
    assumptions: list[dict] = field(default_factory=list)
    uncertainties: list[dict] = field(default_factory=list)
    success_criteria: list[dict] = field(default_factory=list)

    def to_ascii(self) -> str:
        """Render as ASCII diagram."""
        lines = []
        lines.append("┌" + "─" * 60 + "┐")
        lines.append("│" + " INTENT MODEL".center(60) + "│")
        lines.append("├" + "─" * 60 + "┤")

        # Inputs
        lines.append("│ INPUTS:".ljust(61) + "│")
        for inp in self.inputs:
            status = "✓" if inp.get("confirmed") else "○"
            lines.append(
                f"│   {status} {inp.get('name', '?')}: {inp.get('description', '')}".ljust(
                    61
                )[:61]
                + "│"
            )

        lines.append("│".ljust(61) + "│")
        lines.append("│ PROCESS:".ljust(61) + "│")
        for proc in self.process:
            lines.append(f"│   → {proc.get('action', '?')}".ljust(61)[:61] + "│")

        lines.append("│".ljust(61) + "│")
        lines.append("│ OUTPUTS:".ljust(61) + "│")
        for out in self.outputs:
            lines.append(
                f"│   ◆ {out.get('name', '?')}: {out.get('format', '')}".ljust(61)[:61]
                + "│"
            )

        lines.append("│".ljust(61) + "│")
        lines.append("│ ASSUMPTIONS (inferred):".ljust(61) + "│")
        for assumption in self.assumptions:
            lines.append(
                f"│   ○ {assumption.get('key', '?')}: {assumption.get('value', '')}".ljust(
                    61
                )[:61]
                + "│"
            )

        if self.uncertainties:
            lines.append("│".ljust(61) + "│")
            lines.append("│ UNCERTAINTIES (need clarification):".ljust(61) + "│")
            for unc in self.uncertainties:
                lines.append(f"│   ? {unc.get('question', '?')}".ljust(61)[:61] + "│")

        lines.append("│".ljust(61) + "│")
        lines.append("│ SUCCESS CRITERIA:".ljust(61) + "│")
        for crit in self.success_criteria:
            lines.append(f"│   □ {crit.get('criterion', '?')}".ljust(61)[:61] + "│")

        lines.append("└" + "─" * 60 + "┘")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Render as Mermaid flowchart."""
        lines = ["flowchart LR"]

        # Inputs
        for i, inp in enumerate(self.inputs):
            lines.append(f"    I{i}[{inp.get('name', 'Input')}]")

        # Process
        for i, proc in enumerate(self.process):
            lines.append(f"    P{i}{{{proc.get('action', 'Process')}}}")

        # Outputs
        for i, out in enumerate(self.outputs):
            lines.append(f"    O{i}[/{out.get('name', 'Output')}/]")

        # Connections
        for i in range(len(self.inputs)):
            lines.append(f"    I{i} --> P0")
        for i in range(len(self.process) - 1):
            lines.append(f"    P{i} --> P{i + 1}")
        if self.process:
            for i in range(len(self.outputs)):
                lines.append(f"    P{len(self.process) - 1} --> O{i}")

        return "\n".join(lines)


# =============================================================================
# INTENT REFINER
# =============================================================================


class IntentRefiner:
    """
    Transform vague user input into well-defined prompts.

    Implements Progressive Intent Refinement (PIR):
    1. PARSE - Classify intent and domain
    2. PROBE - Ask smart clarification questions
    3. MODEL - Build visual mental model
    4. GENERATE - Create optimized system prompt

    Example:
        refiner = IntentRefiner()

        # User provides vague input
        user_input = "help me with my marketing"

        # Parse intent
        classification = refiner.parse(user_input)

        # Get clarification questions
        questions = refiner.get_questions(user_input, classification)

        # After user answers, build model
        model = refiner.build_model(user_input, answers)

        # Generate optimized prompt
        prompt = refiner.generate_prompt(model)
    """

    # Task type signal words
    TASK_SIGNALS = {
        TaskType.ANALYSIS: [
            "analyze",
            "understand",
            "explain",
            "why",
            "how does",
            "what causes",
            "investigate",
            "assess",
            "evaluate",
        ],
        TaskType.CREATION: [
            "create",
            "make",
            "build",
            "write",
            "design",
            "develop",
            "generate",
            "produce",
            "compose",
            "draft",
        ],
        TaskType.TRANSFORMATION: [
            "improve",
            "fix",
            "change",
            "modify",
            "update",
            "convert",
            "refactor",
            "optimize",
            "enhance",
            "revise",
        ],
        TaskType.DECISION: [
            "should i",
            "which",
            "choose",
            "decide",
            "compare",
            "versus",
            "better",
            "recommend",
            "advise",
        ],
        TaskType.RESEARCH: [
            "find",
            "search",
            "look up",
            "research",
            "discover",
            "learn about",
            "what is",
            "who is",
            "where",
        ],
        TaskType.AUTOMATION: [
            "automate",
            "every time",
            "whenever",
            "always",
            "recurring",
            "schedule",
            "repeat",
            "workflow",
        ],
    }

    # Domain signal words
    DOMAIN_SIGNALS = {
        # Core domains
        Domain.TECHNICAL: [
            "code",
            "api",
            "database",
            "server",
            "bug",
            "deploy",
            "function",
            "class",
            "error",
            "debug",
            "test",
            "software",
            "programming",
            "algorithm",
            "framework",
            "library",
            "git",
            "frontend",
            "backend",
            "devops",
            "cloud",
            "aws",
            "docker",
        ],
        Domain.BUSINESS: [
            "revenue",
            "customer",
            "market",
            "strategy",
            "sales",
            "growth",
            "profit",
            "competitor",
            "stakeholder",
            "marketing",
            "brand",
            "campaign",
            "kpi",
            "roi",
            "pipeline",
            "b2b",
            "b2c",
            "team",
            "management",
            "leadership",
            "hr",
            "hiring",
            "operations",
        ],
        Domain.CREATIVE: [
            "story",
            "design",
            "content",
            "visual",
            "creative",
            "artistic",
            "style",
            "tone",
            "writing",
            "novel",
            "screenplay",
            "script",
            "graphics",
            "illustration",
            "ux",
            "ui",
        ],
        Domain.RESEARCH: [
            "study",
            "paper",
            "papers",
            "literature",
            "hypothesis",
            "experiment",
            "methodology",
            "findings",
            "citation",
            "academic",
            "thesis",
            "dissertation",
            "peer review",
            "journal",
            "research",
            "publication",
        ],
        Domain.PERSONAL: [
            "my life",
            "personal",
            "habit",
            "goal setting",
            "productivity",
            "schedule",
            "organize",
            "planning",
            "self-improvement",
            "work-life",
            "balance",
            "routine",
        ],
        # Science & Research (specialized)
        Domain.SCIENCE: [
            "biology",
            "chemistry",
            "physics",
            "quantum",
            "gene",
            "genes",
            "dna",
            "rna",
            "protein",
            "cell",
            "cells",
            "crispr",
            "genomic",
            "sequencing",
            "pcr",
            "microscopy",
            "spectroscopy",
            "nmr",
            "mass spec",
            "chromatography",
            "synthesis",
            "reaction",
            "catalyst",
            "molecular",
            "compound",
            "qubit",
            "entanglement",
            "superposition",
            "hamiltonian",
            "qiskit",
            "synthetic biology",
            "metabolic",
            "pathway",
            "bioreactor",
            "fermentation",
            "enzyme",
            "biomarker",
            "clinical trial",
            "irb",
            "particle",
            "hadron",
            "quantum field",
            "condensed matter",
            "lab",
            "pipette",
            "assay",
            "western blot",
            "elisa",
            "experiment",
            "scientific",
            "hypothesis",
        ],
        # Finance
        Domain.FINANCE: [
            "stock",
            "invest",
            "portfolio",
            "dividend",
            "etf",
            "mutual fund",
            "trading",
            "options",
            "puts",
            "calls",
            "hedge",
            "forex",
            "crypto",
            "bitcoin",
            "ethereum",
            "blockchain",
            "defi",
            "yield",
            "nft",
            "token",
            "wallet",
            "exchange",
            "binance",
            "coinbase",
            "real estate",
            "property",
            "rental",
            "mortgage",
            "reit",
            "flip",
            "retirement",
            "401k",
            "ira",
            "compound interest",
            "passive income",
            "market cap",
            "pe ratio",
            "fundamental",
            "technical analysis",
        ],
        # Health & Wellness
        Domain.HEALTH: [
            "health",
            "healthy",
            "healthier",
            "medical",
            "doctor",
            "symptom",
            "diagnosis",
            "treatment",
            "medication",
            "therapy",
            "hospital",
            "clinic",
            "patient",
            "nutrition",
            "diet",
            "calories",
            "macros",
            "vitamins",
            "supplements",
            "fitness",
            "workout",
            "exercise",
            "cardio",
            "strength",
            "muscle",
            "weight",
            "lose weight",
            "bmi",
            "metabolism",
            "sleep",
            "insomnia",
            "mental health",
            "anxiety",
            "anxious",
            "depression",
            "depressed",
            "stress",
            "stressed",
            "therapist",
            "meditation",
            "mindfulness",
            "wellness",
            "self-care",
            "burnout",
            "longevity",
            "aging",
            "regenerative",
            "stem cell",
            "biological age",
        ],
        # Legal
        Domain.LEGAL: [
            "legal",
            "law",
            "lawyer",
            "attorney",
            "court",
            "litigation",
            "contract",
            "agreement",
            "clause",
            "terms",
            "conditions",
            "intellectual property",
            "ip",
            "patent",
            "trademark",
            "copyright",
            "compliance",
            "regulation",
            "gdpr",
            "hipaa",
            "sec",
            "fda",
            "liability",
            "negligence",
            "tort",
            "dispute",
            "arbitration",
            "corporate",
            "llc",
            "incorporation",
            "bylaws",
            "governance",
            "employment law",
            "non-compete",
            "nda",
            "licensing",
            "protect",
        ],
        # Education
        Domain.EDUCATION: [
            "teach",
            "teaching",
            "learn",
            "learning",
            "student",
            "students",
            "teacher",
            "professor",
            "course",
            "curriculum",
            "lesson",
            "lecture",
            "assignment",
            "exam",
            "quiz",
            "grade",
            "grading",
            "assessment",
            "rubric",
            "syllabus",
            "textbook",
            "classroom",
            "online learning",
            "mooc",
            "tutoring",
            "mentorship",
            "k-12",
            "higher ed",
            "university",
            "college",
            "school",
            "pedagogy",
            "edtech",
            "lms",
            "engaged",
            "engagement",
            "retention",
            "class",
        ],
        # Entertainment & Media
        Domain.ENTERTAINMENT: [
            "music",
            "song",
            "lyrics",
            "melody",
            "beat",
            "album",
            "track",
            "film",
            "movie",
            "screenplay",
            "director",
            "cinema",
            "scene",
            "game",
            "gaming",
            "level design",
            "mechanics",
            "unity",
            "unreal",
            "streaming",
            "twitch",
            "youtube",
            "content creator",
            "influencer",
            "podcast",
            "episode",
            "audio",
            "production",
            "mixing",
            "mastering",
            "comedy",
            "standup",
            "joke",
            "humor",
            "sketch",
            "animation",
            "vfx",
            "3d",
            "render",
            "storyboard",
        ],
        # Fashion
        Domain.FASHION: [
            "fashion",
            "clothing",
            "clothes",
            "outfit",
            "outfits",
            "wardrobe",
            "wear",
            "wearing",
            "dress",
            "dressing",
            "trend",
            "trends",
            "designer",
            "collection",
            "runway",
            "look",
            "looks",
            "sustainable fashion",
            "eco-friendly",
            "vintage",
            "thrift",
            "accessory",
            "accessories",
            "jewelry",
            "shoes",
            "handbag",
            "watch",
            "dress code",
            "formal",
            "casual",
            "business casual",
            "streetwear",
            "capsule wardrobe",
            "color palette",
            "fabric",
            "textile",
            "attire",
        ],
        # Entrepreneurship
        Domain.ENTREPRENEURSHIP: [
            "startup",
            "founder",
            "cofounder",
            "entrepreneur",
            "venture",
            "funding",
            "investor",
            "vc",
            "angel",
            "seed",
            "series a",
            "pitch",
            "deck",
            "valuation",
            "equity",
            "cap table",
            "mvp",
            "product market fit",
            "pivot",
            "scale",
            "growth hacking",
            "bootstrapping",
            "accelerator",
            "incubator",
            "yc",
            "techstars",
            "exit",
            "acquisition",
            "ipo",
            "unicorn",
            "burn rate",
            "runway",
        ],
    }

    # Elicitation question templates by dimension
    QUESTION_TEMPLATES = {
        "goal": [
            ClarificationQuestion(
                question="What decision or action will this enable?",
                dimension="goal",
                priority=1,
                information_gain=0.9,
            ),
            ClarificationQuestion(
                question="If this works perfectly, what changes for you?",
                dimension="goal",
                priority=1,
                information_gain=0.85,
            ),
        ],
        "success": [
            ClarificationQuestion(
                question="How will you know if the result is good enough?",
                dimension="success",
                priority=1,
                information_gain=0.8,
            ),
            ClarificationQuestion(
                question="What would make you say 'this is exactly what I needed'?",
                dimension="success",
                priority=2,
                information_gain=0.7,
            ),
        ],
        "failure": [
            ClarificationQuestion(
                question="What would make this result useless to you?",
                dimension="failure",
                priority=2,
                information_gain=0.75,
            ),
        ],
        "audience": [
            ClarificationQuestion(
                question="Who will see or use this output?",
                dimension="audience",
                priority=2,
                options=["Just me", "My team", "Executives", "Customers", "Public"],
                default="Just me",
                information_gain=0.6,
            ),
        ],
        "constraints": [
            ClarificationQuestion(
                question="Are there any constraints I should know about?",
                dimension="constraints",
                priority=3,
                options=[
                    "Time limit",
                    "Budget",
                    "Format requirements",
                    "Compliance",
                    "None",
                ],
                information_gain=0.5,
            ),
        ],
        "examples": [
            ClarificationQuestion(
                question="Can you show me an example of what good looks like?",
                dimension="examples",
                priority=2,
                information_gain=0.8,
            ),
        ],
        "scope": [
            ClarificationQuestion(
                question="Should this be comprehensive or focused on key points?",
                dimension="scope",
                priority=2,
                options=[
                    "Quick overview",
                    "Detailed analysis",
                    "Comprehensive deep-dive",
                ],
                default="Detailed analysis",
                information_gain=0.5,
            ),
        ],
    }

    def __init__(
        self,
        executor: Callable[[str], Awaitable[str]] | None = None,
        min_questions: int = 2,
        max_questions: int = 5,
    ):
        """
        Initialize the Intent Refiner.

        Args:
            executor: Optional LLM executor for advanced parsing
            min_questions: Minimum clarification questions to ask
            max_questions: Maximum clarification questions to ask
        """
        self.executor = executor
        self.min_questions = min_questions
        self.max_questions = max_questions

    # =========================================================================
    # STAGE 1: PARSE
    # =========================================================================

    def _match_signal(self, signal: str, text: str) -> bool:
        """
        Check if signal matches in text using word boundaries.
        Multi-word signals use substring matching, single-word use word boundaries.
        """
        if " " in signal:
            # Multi-word signal - use substring matching
            return signal in text
        else:
            # Single-word signal - use word boundary matching
            pattern = r"\b" + re.escape(signal) + r"\b"
            return bool(re.search(pattern, text))

    def parse(self, user_input: str) -> IntentClassification:
        """
        Classify user intent along multiple dimensions.

        Args:
            user_input: Raw user input

        Returns:
            IntentClassification with task type, complexity, and domain
        """
        input_lower = user_input.lower()

        # Detect task type
        task_type = TaskType.CREATION  # Default
        task_confidence = 0.3
        task_signals = []

        for ttype, signals in self.TASK_SIGNALS.items():
            matches = [s for s in signals if self._match_signal(s, input_lower)]
            if len(matches) > len(task_signals):
                task_type = ttype
                task_signals = matches
                task_confidence = min(0.5 + len(matches) * 0.15, 0.95)

        # Detect domain
        domain = Domain.BUSINESS  # Default
        domain_confidence = 0.3
        domain_signals = []

        for dom, signals in self.DOMAIN_SIGNALS.items():
            matches = [s for s in signals if self._match_signal(s, input_lower)]
            if len(matches) > len(domain_signals):
                domain = dom
                domain_signals = matches
                domain_confidence = min(0.5 + len(matches) * 0.15, 0.95)

        # Detect complexity
        complexity = Complexity.ATOMIC
        word_count = len(user_input.split())

        if word_count > 50 or "and then" in input_lower or "steps" in input_lower:
            complexity = Complexity.COMPOSITE
        if (
            "explore" in input_lower
            or "figure out" in input_lower
            or "not sure" in input_lower
        ):
            complexity = Complexity.EXPLORATORY

        # Overall confidence
        confidence = (task_confidence + domain_confidence) / 2

        return IntentClassification(
            task_type=task_type,
            complexity=complexity,
            domain=domain,
            confidence=confidence,
            signals=task_signals + domain_signals,
        )

    # =========================================================================
    # STAGE 1.5: EXTRACT SPECIFICS
    # =========================================================================

    def extract_specifics(
        self, user_input: str, classification: IntentClassification
    ) -> ExtractedSpecifics:
        """
        Extract specific details, entities, and context from user input.

        This is the KEY to preserving information from vague inputs.
        """
        specifics = ExtractedSpecifics()
        text = user_input
        text.lower()

        # --- ENTITY EXTRACTION ---
        # Company types and business models
        business_patterns = [
            r"\b(B2B|B2C|SaaS|startup|enterprise|SMB|agency|consultancy|e-commerce|marketplace)\b",
            r"\b(our company|our team|our organization|our business|my company)\b",
            r"\b(fintech|edtech|healthtech|martech|proptech|insurtech|regtech|foodtech)\b",
        ]
        for pattern in business_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specifics.entities.extend(matches)

        # --- TECHNOLOGY EXTRACTION ---
        tech_patterns = [
            # Programming
            r"\b(Python|JavaScript|TypeScript|Java|C\+\+|Rust|Go|Ruby|PHP|Swift|Kotlin)\b",
            # Frameworks
            r"\b(React|Vue|Angular|Django|Flask|FastAPI|Express|Rails|Spring|Next\.js)\b",
            # Infrastructure
            r"\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|Redis|PostgreSQL|MongoDB|MySQL)\b",
            # AI/ML
            r"\b(GPT|LLM|machine learning|deep learning|neural network|NLP|computer vision)\b",
            # Other tech
            r"\b(API|REST|GraphQL|microservices|serverless|blockchain|CI/CD)\b",
        ]
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specifics.technologies.extend(matches)

        # --- METRICS EXTRACTION ---
        # Numbers with context
        metric_patterns = [
            r"\b(\d+%|\d+\s*percent)\b",  # Percentages
            r"\$[\d,]+(?:\.\d{2})?(?:[KMB])?",  # Money
            r"\b\d+(?:\.\d+)?[xX]\b",  # Multipliers
            r"\b\d+[KMB]?\s*(?:users|customers|subscribers|downloads|visits|conversions)\b",
            r"\b(?:ROI|CTR|CAC|LTV|MRR|ARR|DAU|MAU|NPS)\s*(?:of\s*)?\d+",
        ]
        for pattern in metric_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specifics.metrics.extend(matches)

        # --- TIMEFRAME EXTRACTION ---
        time_patterns = [
            r"\b(today|tomorrow|yesterday|this week|next week|this month|next month)\b",
            r"\b(past\s+\d+\s+(?:days?|weeks?|months?|years?))\b",
            r"\b(\d+\s+(?:days?|weeks?|months?|years?)\s*(?:ago|from now)?)\b",
            r"\b(Q[1-4]|quarter|fiscal year|FY\d{2,4})\b",
            r"\b(deadline|by\s+\w+day|urgent|asap|immediately)\b",
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specifics.timeframes.extend(matches)

        # --- STAKEHOLDER EXTRACTION ---
        stakeholder_patterns = [
            r"\b(CEO|CTO|CFO|CMO|COO|VP|director|manager|executive|board)\b",
            r"\b(team|department|client|customer|user|investor|partner|vendor)\b",
            r"\b(audience|reader|viewer|stakeholder|decision[- ]maker)\b",
        ]
        for pattern in stakeholder_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specifics.stakeholders.extend(matches)

        # --- CONSTRAINT EXTRACTION ---
        constraint_indicators = [
            "but",
            "however",
            "except",
            "without",
            "can't",
            "cannot",
            "won't",
            "shouldn't",
            "must not",
            "limited",
            "constraint",
            "restriction",
            "budget",
            "deadline",
            "only",
            "just",
        ]
        sentences = re.split(r"[.!?]", text)
        for sentence in sentences:
            if any(ind in sentence.lower() for ind in constraint_indicators):
                # Extract the constraint phrase
                specifics.constraints.append(sentence.strip())

        # --- PAIN POINT EXTRACTION ---
        pain_indicators = [
            "problem",
            "issue",
            "challenge",
            "struggle",
            "difficult",
            "hard",
            "failing",
            "broken",
            "doesn't work",
            "not working",
            "slow",
            "frustrat",
            "annoying",
            "pain",
            "stuck",
            "blocked",
        ]
        for sentence in sentences:
            if any(ind in sentence.lower() for ind in pain_indicators):
                specifics.pain_points.append(sentence.strip())

        # --- GOAL EXTRACTION ---
        goal_indicators = [
            "want to",
            "need to",
            "trying to",
            "goal",
            "objective",
            "aim",
            "hope to",
            "would like",
            "looking to",
            "seeking",
            "achieve",
            "improve",
            "increase",
            "decrease",
            "optimize",
            "enhance",
        ]
        for sentence in sentences:
            if any(ind in sentence.lower() for ind in goal_indicators):
                specifics.goals.append(sentence.strip())

        # --- COMPARISON EXTRACTION ---
        comparison_patterns = [
            r"\b(competitor|competing|versus|vs\.?|compared to|better than|worse than)\b.*",
            r"\b(like|similar to|such as)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b",
            r"\b(benchmark|industry standard|best practice)\b",
        ]
        for pattern in comparison_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                specifics.comparisons.extend(
                    [m if isinstance(m, str) else " ".join(m) for m in matches]
                )

        # --- DOMAIN-SPECIFIC TERMS ---
        # Science
        if classification.domain == Domain.SCIENCE:
            sci_patterns = [
                r"\b(gene|protein|cell|enzyme|pathway|assay|PCR|sequencing|CRISPR)\b",
                r"\b(quantum|qubit|entanglement|superposition|Hamiltonian)\b",
                r"\b(synthesis|catalyst|reaction|compound|molecule)\b",
            ]
            for pattern in sci_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                specifics.domain_terms.extend(matches)

        # Finance
        elif classification.domain == Domain.FINANCE:
            fin_patterns = [
                r"\b(stock|bond|ETF|mutual fund|portfolio|dividend|yield)\b",
                r"\b(crypto|bitcoin|ethereum|DeFi|NFT|token|wallet)\b",
                r"\b(real estate|property|mortgage|REIT|rental)\b",
                r"\b(P/E ratio|market cap|fundamentals|technical analysis)\b",
            ]
            for pattern in fin_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                specifics.domain_terms.extend(matches)

        # Health
        elif classification.domain == Domain.HEALTH:
            health_patterns = [
                r"\b(symptom|diagnosis|treatment|medication|therapy)\b",
                r"\b(diet|nutrition|calories|macros|protein|carbs|fat)\b",
                r"\b(workout|exercise|cardio|strength|muscle|weight)\b",
                r"\b(anxiety|depression|stress|sleep|mental health)\b",
            ]
            for pattern in health_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                specifics.domain_terms.extend(matches)

        # --- KEY PHRASES ---
        # Extract phrases in quotes
        quoted = re.findall(r'"([^"]+)"', text)
        specifics.key_phrases.extend(quoted)
        quoted = re.findall(r"'([^']+)'", text)
        specifics.key_phrases.extend(quoted)

        # Deduplicate all lists
        specifics.entities = list(set(specifics.entities))
        specifics.technologies = list(set(specifics.technologies))
        specifics.metrics = list(set(specifics.metrics))
        specifics.timeframes = list(set(specifics.timeframes))
        specifics.stakeholders = list(set(specifics.stakeholders))
        specifics.constraints = list(set(specifics.constraints))
        specifics.pain_points = list(set(specifics.pain_points))
        specifics.goals = list(set(specifics.goals))
        specifics.comparisons = list(set(specifics.comparisons))
        specifics.domain_terms = list(set(specifics.domain_terms))
        specifics.key_phrases = list(set(specifics.key_phrases))

        return specifics

    # =========================================================================
    # STAGE 2: PROBE
    # =========================================================================

    def get_questions(
        self,
        user_input: str,
        classification: IntentClassification,
    ) -> list[ClarificationQuestion]:
        """
        Generate smart clarification questions based on classification.

        Uses Minimum Viable Questions (MVQ) principle:
        - Only ask questions that significantly change the output
        - Prioritize based on information gain
        - Skip questions with good defaults

        Args:
            user_input: Original user input
            classification: Intent classification

        Returns:
            List of prioritized clarification questions
        """
        questions = []
        user_input.lower()

        # Always ask about goal if vague
        if classification.confidence < 0.7:
            questions.extend(self.QUESTION_TEMPLATES["goal"])

        # Ask about success criteria for creation/analysis
        if classification.task_type in (TaskType.CREATION, TaskType.ANALYSIS):
            questions.extend(self.QUESTION_TEMPLATES["success"])

        # Ask about failure modes for high-stakes tasks
        if classification.domain in (Domain.BUSINESS, Domain.TECHNICAL):
            questions.extend(self.QUESTION_TEMPLATES["failure"])

        # Ask about audience unless it's clearly personal
        if classification.domain != Domain.PERSONAL:
            questions.extend(self.QUESTION_TEMPLATES["audience"])

        # Ask for examples for creative tasks
        if classification.task_type == TaskType.CREATION:
            questions.extend(self.QUESTION_TEMPLATES["examples"])

        # Ask about scope for research/analysis
        if classification.task_type in (TaskType.RESEARCH, TaskType.ANALYSIS):
            questions.extend(self.QUESTION_TEMPLATES["scope"])

        # Sort by information gain and priority
        questions.sort(key=lambda q: (-q.information_gain, q.priority))

        # Apply min/max limits
        return questions[: self.max_questions]

    def get_questions_interactive(
        self,
        user_input: str,
        classification: IntentClassification,
    ) -> list[dict]:
        """
        Get questions formatted for interactive UI.

        Returns:
            List of question dicts with UI metadata
        """
        questions = self.get_questions(user_input, classification)

        return [
            {
                "id": f"q{i}",
                "question": q.question,
                "dimension": q.dimension,
                "type": "multiple_choice" if q.options else "free_text",
                "options": q.options,
                "default": q.default,
                "required": q.priority == 1,
            }
            for i, q in enumerate(questions)
        ]

    # =========================================================================
    # STAGE 3: MODEL
    # =========================================================================

    def build_model(
        self,
        user_input: str,
        classification: IntentClassification,
        answers: dict | None = None,
    ) -> IntentModel:
        """
        Build visual mental model from input and answers.

        Args:
            user_input: Original user input
            classification: Intent classification
            answers: Answers to clarification questions

        Returns:
            IntentModel with structured representation
        """
        answers = answers or {}

        # Extract inputs from user input
        inputs = []
        if "using" in user_input.lower() or "with" in user_input.lower():
            inputs.append(
                {
                    "name": "User-provided data",
                    "description": "Data or context from user",
                    "confirmed": False,
                }
            )

        inputs.append(
            {
                "name": "Task description",
                "description": user_input[:100] + "..."
                if len(user_input) > 100
                else user_input,
                "confirmed": True,
            }
        )

        # Determine process steps based on task type
        process = []
        if classification.task_type == TaskType.ANALYSIS:
            process = [
                {"action": "Understand context"},
                {"action": "Analyze data/situation"},
                {"action": "Identify patterns/insights"},
                {"action": "Synthesize findings"},
            ]
        elif classification.task_type == TaskType.CREATION:
            process = [
                {"action": "Understand requirements"},
                {"action": "Plan structure"},
                {"action": "Generate content"},
                {"action": "Refine and polish"},
            ]
        elif classification.task_type == TaskType.RESEARCH:
            process = [
                {"action": "Define search scope"},
                {"action": "Gather information"},
                {"action": "Evaluate sources"},
                {"action": "Summarize findings"},
            ]
        elif classification.task_type == TaskType.DECISION:
            process = [
                {"action": "Identify options"},
                {"action": "Define criteria"},
                {"action": "Evaluate trade-offs"},
                {"action": "Recommend decision"},
            ]
        else:
            process = [{"action": "Process request"}]

        # Determine outputs
        outputs = []
        if classification.task_type == TaskType.ANALYSIS:
            outputs.append({"name": "Analysis report", "format": "Structured findings"})
        elif classification.task_type == TaskType.CREATION:
            outputs.append({"name": "Created artifact", "format": "As specified"})
        elif classification.task_type == TaskType.RESEARCH:
            outputs.append(
                {"name": "Research summary", "format": "Findings with sources"}
            )
        elif classification.task_type == TaskType.DECISION:
            outputs.append(
                {"name": "Recommendation", "format": "Decision with rationale"}
            )
        else:
            outputs.append({"name": "Response", "format": "Text"})

        # Build assumptions
        assumptions = []
        assumptions.append(
            {
                "key": "Task type",
                "value": classification.task_type.value,
            }
        )
        assumptions.append(
            {
                "key": "Domain",
                "value": classification.domain.value,
            }
        )

        if "audience" not in answers:
            assumptions.append(
                {
                    "key": "Audience",
                    "value": "Professional/knowledgeable",
                }
            )

        if "scope" not in answers:
            assumptions.append(
                {
                    "key": "Scope",
                    "value": "Moderate depth",
                }
            )

        # Identify uncertainties
        uncertainties = []
        if classification.confidence < 0.6:
            uncertainties.append(
                {
                    "question": "Is this the right interpretation of your goal?",
                }
            )

        if classification.complexity == Complexity.EXPLORATORY:
            uncertainties.append(
                {
                    "question": "The goal may evolve as we work - is that okay?",
                }
            )

        # Build success criteria from answers
        success_criteria = []
        if "success" in answers:
            success_criteria.append({"criterion": answers["success"]})
        else:
            success_criteria.append({"criterion": "Addresses the stated request"})
            success_criteria.append({"criterion": "Accurate and well-reasoned"})

        if "failure" in answers:
            success_criteria.append({"criterion": f"Avoids: {answers['failure']}"})

        return IntentModel(
            inputs=inputs,
            process=process,
            outputs=outputs,
            assumptions=assumptions,
            uncertainties=uncertainties,
            success_criteria=success_criteria,
        )

    # =========================================================================
    # STAGE 4: GENERATE
    # =========================================================================

    def generate_prompt(
        self,
        model: IntentModel,
        classification: IntentClassification,
        answers: dict | None = None,
        specifics: ExtractedSpecifics | None = None,
        user_input: str = "",
    ) -> str:
        """
        Generate optimized system prompt from mental model.

        Applies prompt engineering best practices:
        - Role setting
        - Context injection WITH SPECIFIC DETAILS
        - Task specification WITH USER'S ACTUAL REQUEST
        - Output format
        - Guardrails

        Args:
            model: Intent model
            classification: Intent classification
            answers: User answers to clarification questions
            specifics: Extracted specifics from user input
            user_input: Original user input for context

        Returns:
            Optimized system prompt that preserves all specific details
        """
        answers = answers or {}
        specifics = specifics or ExtractedSpecifics()

        # Build role based on domain
        role_map = {
            # Core domains
            Domain.TECHNICAL: "expert software engineer and technical architect",
            Domain.BUSINESS: "senior business strategist and analyst",
            Domain.CREATIVE: "experienced creative professional and writer",
            Domain.RESEARCH: "thorough researcher and academic analyst",
            Domain.PERSONAL: "helpful personal assistant and productivity coach",
            # Specialized domains
            Domain.SCIENCE: "expert scientist with deep domain knowledge",
            Domain.FINANCE: "experienced financial analyst and investment strategist",
            Domain.HEALTH: "knowledgeable health and wellness advisor",
            Domain.LEGAL: "experienced legal analyst (not providing legal advice)",
            Domain.EDUCATION: "expert educator and curriculum designer",
            Domain.ENTERTAINMENT: "creative entertainment industry professional",
            Domain.FASHION: "experienced fashion consultant and stylist",
            Domain.ENTREPRENEURSHIP: "seasoned startup advisor and founder coach",
        }
        role = role_map.get(classification.domain, "helpful assistant")

        # Build task verb based on task type
        task_verbs = {
            TaskType.ANALYSIS: "analyze and provide insights on",
            TaskType.CREATION: "create and deliver",
            TaskType.TRANSFORMATION: "improve and refine",
            TaskType.DECISION: "evaluate options and recommend",
            TaskType.RESEARCH: "research and summarize",
            TaskType.AUTOMATION: "design a repeatable process for",
        }
        task_verb = task_verbs.get(classification.task_type, "help with")

        # Build audience context
        audience = answers.get("audience", "a knowledgeable professional")
        if specifics.stakeholders:
            audience = ", ".join(specifics.stakeholders[:3])

        # Build success criteria
        criteria_text = "\n".join(f"- {c['criterion']}" for c in model.success_criteria)

        # Build the prompt
        prompt_parts = []

        # Role
        prompt_parts.append(f"You are a {role}.")
        prompt_parts.append("")

        # ==== SPECIFIC SITUATION (NEW SECTION) ====
        prompt_parts.append("## Specific Situation")
        prompt_parts.append(f'The user\'s request: "{user_input}"')
        prompt_parts.append("")

        # Inject extracted specifics
        if specifics.has_specifics():
            prompt_parts.append("### Key Details Extracted:")

            if specifics.entities:
                prompt_parts.append(
                    f"- **Business Context**: {', '.join(specifics.entities)}"
                )

            if specifics.technologies:
                prompt_parts.append(
                    f"- **Technologies/Tools**: {', '.join(specifics.technologies)}"
                )

            if specifics.metrics:
                prompt_parts.append(
                    f"- **Metrics/Numbers**: {', '.join(specifics.metrics)}"
                )

            if specifics.timeframes:
                prompt_parts.append(
                    f"- **Timeframe**: {', '.join(specifics.timeframes)}"
                )

            if specifics.stakeholders:
                prompt_parts.append(
                    f"- **Stakeholders**: {', '.join(specifics.stakeholders)}"
                )

            if specifics.pain_points:
                prompt_parts.append(
                    "- **Current Problems**: "
                    + "; ".join(p[:100] for p in specifics.pain_points[:3])
                )

            if specifics.goals:
                prompt_parts.append(
                    "- **Desired Outcomes**: "
                    + "; ".join(g[:100] for g in specifics.goals[:3])
                )

            if specifics.constraints:
                prompt_parts.append(
                    "- **Constraints**: "
                    + "; ".join(c[:100] for c in specifics.constraints[:3])
                )

            if specifics.comparisons:
                prompt_parts.append(
                    f"- **Competitors/Benchmarks**: {', '.join(specifics.comparisons)}"
                )

            if specifics.domain_terms:
                prompt_parts.append(
                    f"- **Domain Terms**: {', '.join(specifics.domain_terms)}"
                )

            prompt_parts.append("")

        # Context
        if model.assumptions:
            context_items = [f"{a['key']}: {a['value']}" for a in model.assumptions]
            prompt_parts.append("## Working Assumptions")
            prompt_parts.append("\n".join(f"- {item}" for item in context_items))
            prompt_parts.append("")

        # Task - MORE SPECIFIC NOW
        prompt_parts.append("## Your Task")

        # Build specific task description
        task_desc = f"Your task is to {task_verb}"

        # Add specific context to task
        if specifics.goals:
            task_desc += f" the following: {specifics.goals[0][:150]}"
        elif specifics.pain_points:
            task_desc += f" addressing: {specifics.pain_points[0][:150]}"
        else:
            task_desc += " what the user has requested above."

        prompt_parts.append(task_desc)
        prompt_parts.append(f"The output is for: {audience}.")
        prompt_parts.append("")

        # Process - Include specific elements
        prompt_parts.append("## Recommended Approach")
        for i, proc in enumerate(model.process, 1):
            prompt_parts.append(f"{i}. {proc['action']}")

        # Add specific considerations based on extracted info
        if specifics.entities or specifics.technologies:
            prompt_parts.append(
                f"{len(model.process) + 1}. Consider the specific context: {', '.join((specifics.entities + specifics.technologies)[:5])}"
            )

        if specifics.constraints:
            prompt_parts.append(
                f"{len(model.process) + 2}. Work within stated constraints"
            )

        prompt_parts.append("")

        # Output
        prompt_parts.append("## Output Requirements")
        for out in model.outputs:
            prompt_parts.append(f"- Provide: {out['name']} ({out['format']})")

        # Add specific output guidance
        if specifics.metrics:
            prompt_parts.append(
                f"- Reference these metrics where relevant: {', '.join(specifics.metrics)}"
            )
        if specifics.comparisons:
            prompt_parts.append(
                f"- Include comparison with: {', '.join(specifics.comparisons)}"
            )

        prompt_parts.append("")

        # Success criteria
        prompt_parts.append("## Success Criteria")
        prompt_parts.append(criteria_text)

        # Add criteria based on extracted goals
        if specifics.goals:
            prompt_parts.append(f"- Directly addresses: {specifics.goals[0][:100]}")
        if specifics.pain_points:
            prompt_parts.append(
                f"- Solves the stated problem: {specifics.pain_points[0][:100]}"
            )

        prompt_parts.append("")

        # Guardrails
        prompt_parts.append("## Guardrails")
        prompt_parts.append("- Be accurate and factual")
        prompt_parts.append("- Acknowledge uncertainty when appropriate")
        prompt_parts.append("- Ask for clarification if the request is ambiguous")

        # Domain-specific guardrails
        if classification.domain == Domain.TECHNICAL:
            prompt_parts.append("- Provide working, tested solutions")
        if classification.domain == Domain.BUSINESS:
            prompt_parts.append("- Support claims with reasoning or data")
        if classification.domain == Domain.RESEARCH:
            prompt_parts.append("- Cite sources when possible")
        if classification.domain == Domain.SCIENCE:
            prompt_parts.append("- Use precise scientific terminology")
            prompt_parts.append("- Reference established methodologies")
        if classification.domain == Domain.FINANCE:
            prompt_parts.append(
                "- This is not financial advice - for informational purposes only"
            )
            prompt_parts.append("- Consider risk factors and diversification")
        if classification.domain == Domain.HEALTH:
            prompt_parts.append(
                "- This is not medical advice - consult healthcare professionals"
            )
            prompt_parts.append("- Prioritize evidence-based information")
        if classification.domain == Domain.LEGAL:
            prompt_parts.append(
                "- This is not legal advice - consult a licensed attorney"
            )
            prompt_parts.append("- Note jurisdiction-specific variations")
        if classification.domain == Domain.EDUCATION:
            prompt_parts.append("- Adapt to learner's level and context")
            prompt_parts.append("- Include practical examples and exercises")
        if classification.domain == Domain.ENTERTAINMENT:
            prompt_parts.append("- Balance creativity with feasibility")
            prompt_parts.append("- Consider audience and platform requirements")
        if classification.domain == Domain.FASHION:
            prompt_parts.append("- Consider personal style, body type, and occasion")
            prompt_parts.append("- Balance trends with timeless principles")
        if classification.domain == Domain.ENTREPRENEURSHIP:
            prompt_parts.append("- Focus on actionable, practical advice")
            prompt_parts.append("- Consider resource constraints and timing")

        return "\n".join(prompt_parts)

    # =========================================================================
    # QUALITY EVALUATION
    # =========================================================================

    def evaluate_quality(
        self,
        prompt: str,
        user_input: str,
        specifics: ExtractedSpecifics,
    ) -> QualityScore:
        """
        Evaluate the quality of a generated prompt.

        Checks:
        - Specificity: Does it include specific details?
        - Completeness: Are all aspects covered?
        - Actionability: Is it clear what to do?
        - Context preservation: Is original context retained?

        Args:
            prompt: Generated prompt
            user_input: Original user input
            specifics: Extracted specifics

        Returns:
            QualityScore with detailed breakdown
        """
        score = QualityScore()
        prompt_lower = prompt.lower()
        input_lower = user_input.lower()

        missing = []
        suggestions = []

        # --- SPECIFICITY SCORE ---
        specificity_hits = 0
        specificity_total = 0

        # Check if entities are mentioned
        for entity in specifics.entities:
            specificity_total += 1
            if entity.lower() in prompt_lower:
                specificity_hits += 1
            else:
                missing.append(f"Entity: {entity}")

        # Check if technologies are mentioned
        for tech in specifics.technologies:
            specificity_total += 1
            if tech.lower() in prompt_lower:
                specificity_hits += 1
            else:
                missing.append(f"Technology: {tech}")

        # Check if metrics are mentioned
        for metric in specifics.metrics:
            specificity_total += 1
            if metric.lower() in prompt_lower:
                specificity_hits += 1
            else:
                missing.append(f"Metric: {metric}")

        # Check domain terms
        for term in specifics.domain_terms:
            specificity_total += 1
            if term.lower() in prompt_lower:
                specificity_hits += 1

        score.specificity = specificity_hits / max(specificity_total, 1)

        # --- COMPLETENESS SCORE ---
        completeness_checks = {
            "role": "you are" in prompt_lower,
            "task": "task" in prompt_lower or "your" in prompt_lower,
            "context": "context" in prompt_lower or "situation" in prompt_lower,
            "output": "output" in prompt_lower or "provide" in prompt_lower,
            "criteria": "success" in prompt_lower or "criteria" in prompt_lower,
            "guardrails": "guardrail" in prompt_lower or "accurate" in prompt_lower,
        }

        score.completeness = sum(completeness_checks.values()) / len(
            completeness_checks
        )

        for check, passed in completeness_checks.items():
            if not passed:
                suggestions.append(f"Add {check} section")

        # --- ACTIONABILITY SCORE ---
        actionability_checks = {
            "clear_verb": any(
                v in prompt_lower
                for v in ["analyze", "create", "improve", "research", "recommend"]
            ),
            "approach": "approach" in prompt_lower or "step" in prompt_lower,
            "requirements": "requirement" in prompt_lower or "provide" in prompt_lower,
        }

        score.actionability = sum(actionability_checks.values()) / len(
            actionability_checks
        )

        # --- CONTEXT PRESERVATION SCORE ---
        # Check if key words from input appear in prompt
        input_words = set(input_lower.split())
        # Remove common words
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "i",
            "me",
            "my",
            "we",
            "our",
            "you",
            "your",
            "it",
            "its",
            "this",
            "that",
            "and",
            "but",
            "or",
            "so",
            "if",
            "because",
        }

        content_words = input_words - stopwords
        preserved = sum(1 for w in content_words if w in prompt_lower)
        score.context_preservation = preserved / max(len(content_words), 1)

        if score.context_preservation < 0.5:
            suggestions.append("Include more specific terms from user input")

        # Check pain points preservation
        for pain in specifics.pain_points:
            pain_words = set(pain.lower().split()) - stopwords
            if not any(w in prompt_lower for w in pain_words):
                suggestions.append(f"Address pain point: {pain[:50]}...")

        # Check goals preservation
        for goal in specifics.goals:
            goal_words = set(goal.lower().split()) - stopwords
            if not any(w in prompt_lower for w in goal_words):
                suggestions.append(f"Include goal: {goal[:50]}...")

        # --- OVERALL SCORE ---
        weights = {
            "specificity": 0.35,
            "completeness": 0.20,
            "actionability": 0.15,
            "context_preservation": 0.30,
        }

        score.overall = (
            score.specificity * weights["specificity"]
            + score.completeness * weights["completeness"]
            + score.actionability * weights["actionability"]
            + score.context_preservation * weights["context_preservation"]
        )

        score.missing_elements = missing[:10]  # Limit to top 10
        score.improvement_suggestions = suggestions[:5]  # Limit to top 5

        return score

    # =========================================================================
    # ITERATIVE REFINEMENT
    # =========================================================================

    def iterative_refine(
        self,
        user_input: str,
        answers: dict | None = None,
        quality_threshold: float = 0.7,
        max_iterations: int = 3,
    ) -> dict:
        """
        Iteratively refine the prompt until quality threshold is met.

        This implements the multi-turn refinement process:
        1. Generate initial prompt
        2. Evaluate quality
        3. If below threshold, identify gaps and regenerate
        4. Repeat until threshold met or max iterations reached

        Args:
            user_input: Raw user input
            answers: Optional answers to clarification questions
            quality_threshold: Minimum quality score (0-1)
            max_iterations: Maximum refinement iterations

        Returns:
            Dict with final prompt, quality score, and iteration history
        """
        iterations = []

        # Initial parse and extract
        classification = self.parse(user_input)
        specifics = self.extract_specifics(user_input, classification)

        # Get questions (if no answers provided)
        questions = []
        if answers is None:
            questions = self.get_questions_interactive(user_input, classification)

        # Build model
        model = self.build_model(user_input, classification, answers)

        # Track cumulative context for iterations
        cumulative_specifics = specifics
        current_prompt = ""

        for i in range(max_iterations):
            # Generate prompt with current specifics
            current_prompt = self.generate_prompt(
                model,
                classification,
                answers,
                specifics=cumulative_specifics,
                user_input=user_input,
            )

            # Evaluate quality
            quality = self.evaluate_quality(current_prompt, user_input, specifics)

            iteration_record = {
                "iteration": i + 1,
                "prompt_length": len(current_prompt),
                "quality_score": quality.overall,
                "specificity": quality.specificity,
                "completeness": quality.completeness,
                "actionability": quality.actionability,
                "context_preservation": quality.context_preservation,
                "missing_elements": quality.missing_elements,
                "suggestions": quality.improvement_suggestions,
            }
            iterations.append(iteration_record)

            # Check if quality threshold met
            if quality.meets_threshold(quality_threshold):
                break

            # If not met, enhance specifics for next iteration
            # Add missing elements as additional requirements
            for missing in quality.missing_elements[:3]:
                cumulative_specifics.requirements.append(f"Must include: {missing}")

            # Add suggestions as constraints
            for suggestion in quality.improvement_suggestions[:2]:
                cumulative_specifics.constraints.append(suggestion)

        return {
            "original_input": user_input,
            "classification": {
                "task_type": classification.task_type.value,
                "complexity": classification.complexity.value,
                "domain": classification.domain.value,
                "confidence": classification.confidence,
                "signals": classification.signals,
            },
            "specifics_extracted": {
                "entities": specifics.entities,
                "technologies": specifics.technologies,
                "metrics": specifics.metrics,
                "timeframes": specifics.timeframes,
                "stakeholders": specifics.stakeholders,
                "pain_points": specifics.pain_points[:3],
                "goals": specifics.goals[:3],
                "constraints": specifics.constraints[:3],
                "comparisons": specifics.comparisons,
                "domain_terms": specifics.domain_terms,
            },
            "questions": questions,
            "model": {
                "ascii": model.to_ascii(),
                "mermaid": model.to_mermaid(),
            },
            "prompt": current_prompt,
            "quality": {
                "overall": iterations[-1]["quality_score"],
                "specificity": iterations[-1]["specificity"],
                "completeness": iterations[-1]["completeness"],
                "actionability": iterations[-1]["actionability"],
                "context_preservation": iterations[-1]["context_preservation"],
                "threshold_met": iterations[-1]["quality_score"] >= quality_threshold,
            },
            "iterations": iterations,
            "total_iterations": len(iterations),
        }

    # =========================================================================
    # CONVENIENCE: FULL PIPELINE
    # =========================================================================

    def refine(
        self,
        user_input: str,
        answers: dict | None = None,
    ) -> dict:
        """
        Run full refinement pipeline with specific detail extraction.

        Args:
            user_input: Raw user input
            answers: Optional answers to clarification questions

        Returns:
            Dict with classification, model, prompt, specifics, and questions
        """
        # Parse
        classification = self.parse(user_input)

        # Extract specifics - THIS IS THE KEY NEW STEP
        specifics = self.extract_specifics(user_input, classification)

        # Get questions (if no answers provided)
        questions = []
        if answers is None:
            questions = self.get_questions_interactive(user_input, classification)

        # Build model
        model = self.build_model(user_input, classification, answers)

        # Generate prompt WITH SPECIFICS
        prompt = self.generate_prompt(
            model, classification, answers, specifics=specifics, user_input=user_input
        )

        # Evaluate quality
        quality = self.evaluate_quality(prompt, user_input, specifics)

        return {
            "original_input": user_input,
            "classification": {
                "task_type": classification.task_type.value,
                "complexity": classification.complexity.value,
                "domain": classification.domain.value,
                "confidence": classification.confidence,
                "signals": classification.signals,
            },
            "specifics_extracted": {
                "entities": specifics.entities,
                "technologies": specifics.technologies,
                "metrics": specifics.metrics,
                "timeframes": specifics.timeframes,
                "stakeholders": specifics.stakeholders,
                "pain_points": specifics.pain_points[:3],
                "goals": specifics.goals[:3],
                "constraints": specifics.constraints[:3],
                "comparisons": specifics.comparisons,
                "domain_terms": specifics.domain_terms,
            },
            "questions": questions,
            "model": {
                "ascii": model.to_ascii(),
                "mermaid": model.to_mermaid(),
            },
            "prompt": prompt,
            "quality": {
                "overall": quality.overall,
                "specificity": quality.specificity,
                "completeness": quality.completeness,
                "actionability": quality.actionability,
                "context_preservation": quality.context_preservation,
            },
        }

    def paraphrase(
        self,
        user_input: str,
        classification: IntentClassification,
        model: IntentModel,
    ) -> str:
        """
        Generate paraphrase for user confirmation.

        Highlights:
        - What was understood
        - What was assumed
        - What is uncertain

        Args:
            user_input: Original input
            classification: Intent classification
            model: Built intent model

        Returns:
            Paraphrase with assumptions highlighted
        """
        parts = []

        parts.append("**Here's what I understood:**")
        parts.append("")
        parts.append(
            f"You want me to **{classification.task_type.value}** something in the **{classification.domain.value}** domain."
        )
        parts.append("")

        parts.append("**Process:**")
        for proc in model.process:
            parts.append(f"  → {proc['action']}")
        parts.append("")

        parts.append("**Expected output:**")
        for out in model.outputs:
            parts.append(f"  • {out['name']} ({out['format']})")
        parts.append("")

        if model.assumptions:
            parts.append("**I assumed:**")
            for assumption in model.assumptions:
                parts.append(f"  ○ {assumption['key']}: {assumption['value']}")
            parts.append("")

        if model.uncertainties:
            parts.append("**I'm uncertain about:**")
            for unc in model.uncertainties:
                parts.append(f"  ? {unc['question']}")
            parts.append("")

        parts.append(
            "**Is this correct?** If not, please clarify what I should change."
        )

        return "\n".join(parts)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def refine_intent(user_input: str, answers: dict | None = None) -> dict:
    """Quick function to refine user intent with specific detail extraction."""
    refiner = IntentRefiner()
    return refiner.refine(user_input, answers)


def refine_intent_iterative(
    user_input: str,
    answers: dict | None = None,
    quality_threshold: float = 0.7,
    max_iterations: int = 3,
) -> dict:
    """
    Refine user intent with iterative quality improvement.

    This is the RECOMMENDED function for production use.
    It iterates until quality threshold is met.

    Args:
        user_input: Raw user input
        answers: Optional answers to clarification questions
        quality_threshold: Minimum quality score (0-1), default 0.7
        max_iterations: Maximum refinement iterations, default 3

    Returns:
        Dict with prompt, quality scores, and iteration history
    """
    refiner = IntentRefiner()
    return refiner.iterative_refine(
        user_input,
        answers,
        quality_threshold=quality_threshold,
        max_iterations=max_iterations,
    )


def get_clarification_questions(user_input: str) -> list[dict]:
    """Get clarification questions for user input."""
    refiner = IntentRefiner()
    classification = refiner.parse(user_input)
    return refiner.get_questions_interactive(user_input, classification)


def generate_system_prompt(user_input: str, answers: dict | None = None) -> str:
    """Generate optimized system prompt from user input."""
    refiner = IntentRefiner()
    result = refiner.refine(user_input, answers)
    return result["prompt"]


def extract_input_specifics(user_input: str) -> dict:
    """
    Extract specific details from user input.

    Useful for understanding what entities, technologies, metrics, etc.
    are mentioned in a user's request.

    Args:
        user_input: Raw user input

    Returns:
        Dict with extracted specifics
    """
    refiner = IntentRefiner()
    classification = refiner.parse(user_input)
    specifics = refiner.extract_specifics(user_input, classification)
    return {
        "entities": specifics.entities,
        "technologies": specifics.technologies,
        "metrics": specifics.metrics,
        "timeframes": specifics.timeframes,
        "stakeholders": specifics.stakeholders,
        "pain_points": specifics.pain_points,
        "goals": specifics.goals,
        "constraints": specifics.constraints,
        "comparisons": specifics.comparisons,
        "domain_terms": specifics.domain_terms,
        "key_phrases": specifics.key_phrases,
    }
