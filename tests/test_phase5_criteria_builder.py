"""Tests for Phase 5: Collaborative Criteria Builder."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from orchestration.diagnostics.criteria_builder import CriteriaBuilder, SuccessCriteria

# ============== Fixtures ==============


@pytest.fixture
def mock_executor():
    """Create a mock LLM executor."""
    executor = AsyncMock()
    executor.execute = AsyncMock()
    return executor


# ============== Unit Tests ==============


def test_criteria_builder_initialization(mock_executor):
    """Test CriteriaBuilder initializes correctly."""
    builder = CriteriaBuilder(mock_executor)
    assert builder.executor == mock_executor
    assert builder.max_questions == 5
    assert builder.question_callback is None


def test_criteria_builder_with_callback(mock_executor):
    """Test CriteriaBuilder with question callback."""

    def callback(q):
        return "test response"

    builder = CriteriaBuilder(mock_executor, question_callback=callback)
    assert builder.question_callback == callback


@pytest.mark.asyncio
async def test_build_criteria_basic(mock_executor):
    """Test basic criteria building flow."""
    # Mock responses
    mock_executor.execute.side_effect = [
        # Initial criteria
        json.dumps(
            {
                "criteria": [
                    "Login form renders correctly",
                    "Email and password fields accept input",
                    "Submit button is clickable",
                ]
            }
        ),
        # Questions
        json.dumps(
            {
                "questions": [
                    "What should happen when login fails?",
                    "Should there be password validation?",
                ]
            }
        ),
        # Refined criteria
        json.dumps(
            {
                "criteria": [
                    "Login form renders with email and password fields",
                    "Email validation shows error for invalid emails",
                    "Failed login displays appropriate error message",
                    "Successful login redirects to dashboard",
                ]
            }
        ),
    ]

    builder = CriteriaBuilder(mock_executor, max_questions=2)
    criteria = await builder.build_criteria("Build a login page")

    assert len(criteria.criteria) > 0
    assert isinstance(criteria.criteria, list)
    assert criteria.task == "Build a login page"
    assert criteria.confidence > 0


@pytest.mark.asyncio
async def test_build_criteria_with_context(mock_executor):
    """Test criteria building with context."""
    mock_executor.execute.side_effect = [
        json.dumps({"criteria": ["Criterion 1", "Criterion 2"]}),
        json.dumps({"questions": ["Question 1?"]}),
        json.dumps({"criteria": ["Refined 1", "Refined 2", "Refined 3"]}),
    ]

    builder = CriteriaBuilder(mock_executor, max_questions=1)
    criteria = await builder.build_criteria(
        "Build a dashboard", context={"framework": "React", "design": "Material UI"}
    )

    assert criteria.task == "Build a dashboard"
    assert len(criteria.criteria) > 0


@pytest.mark.asyncio
async def test_build_criteria_with_interactive_callback(mock_executor):
    """Test criteria building with interactive Q&A."""
    mock_executor.execute.side_effect = [
        json.dumps({"criteria": ["Initial criterion"]}),
        json.dumps({"questions": ["What colors should be used?"]}),
        json.dumps({"criteria": ["Refined criterion with blue colors"]}),
    ]

    responses = ["Blue and white"]
    response_index = [0]

    def callback(question):
        response = responses[response_index[0]]
        response_index[0] += 1
        return response

    builder = CriteriaBuilder(
        mock_executor, max_questions=1, question_callback=callback
    )
    criteria = await builder.build_criteria("Design a UI")

    assert len(criteria.questions_asked) == 1
    assert len(criteria.human_responses) == 1
    assert criteria.human_responses[0] == "Blue and white"


@pytest.mark.asyncio
async def test_propose_initial_criteria(mock_executor):
    """Test _propose_initial_criteria method."""
    mock_executor.execute.return_value = json.dumps(
        {"criteria": ["Criterion A", "Criterion B", "Criterion C"]}
    )

    builder = CriteriaBuilder(mock_executor)
    criteria = await builder._propose_initial_criteria("Test task", {})

    assert len(criteria) == 3
    assert "Criterion A" in criteria


@pytest.mark.asyncio
async def test_propose_initial_criteria_with_code_block(mock_executor):
    """Test parsing JSON from code block."""
    mock_executor.execute.return_value = """Here are the criteria:

```json
{
  "criteria": ["Test 1", "Test 2"]
}
```

Hope this helps!"""

    builder = CriteriaBuilder(mock_executor)
    criteria = await builder._propose_initial_criteria("Task", {})

    assert len(criteria) == 2


@pytest.mark.asyncio
async def test_generate_questions(mock_executor):
    """Test _generate_questions method."""
    mock_executor.execute.return_value = json.dumps(
        {"questions": ["Question 1?", "Question 2?", "Question 3?"]}
    )

    builder = CriteriaBuilder(mock_executor)
    questions = await builder._generate_questions("Task", {}, ["Criterion 1"])

    assert len(questions) == 3
    assert all(q.endswith("?") for q in questions)


@pytest.mark.asyncio
async def test_refine_criteria(mock_executor):
    """Test _refine_criteria method."""
    mock_executor.execute.return_value = json.dumps(
        {
            "criteria": [
                "Refined criterion 1",
                "Refined criterion 2",
                "Refined criterion 3",
                "Refined criterion 4",
            ]
        }
    )

    builder = CriteriaBuilder(mock_executor)
    refined = await builder._refine_criteria(
        "Task", {}, ["Initial 1", "Initial 2"], ["Q1?", "Q2?"], ["A1", "A2"]
    )

    assert len(refined) == 4
    assert "Refined" in refined[0]


@pytest.mark.asyncio
async def test_error_handling_fallback(mock_executor):
    """Test graceful fallback on LLM errors."""
    # Mock LLM to raise exception
    mock_executor.execute.side_effect = Exception("LLM error")

    builder = CriteriaBuilder(mock_executor, max_questions=1)
    criteria = await builder.build_criteria("Test task")

    # Should return fallback criteria
    assert len(criteria.criteria) > 0
    assert isinstance(criteria.criteria, list)


def test_extract_json():
    """Test JSON extraction from text."""
    builder = CriteriaBuilder(MagicMock())

    # From code block
    text1 = '```json\n{"key": "value"}\n```'
    assert builder._extract_json(text1) == '{"key": "value"}'

    # From generic code block
    text2 = '```\n{"key": "value"}\n```'
    assert builder._extract_json(text2) == '{"key": "value"}'

    # Plain JSON
    text3 = '{"key": "value"}'
    assert builder._extract_json(text3) == '{"key": "value"}'


def test_calculate_confidence():
    """Test confidence calculation."""
    builder = CriteriaBuilder(MagicMock())

    # No questions
    assert builder._calculate_confidence(0, 0) == 0.5

    # All questions answered
    assert builder._calculate_confidence(5, 5) == 0.9

    # Most questions answered
    assert builder._calculate_confidence(5, 4) == 0.9

    # Some questions answered
    assert builder._calculate_confidence(5, 3) == 0.8

    # Few questions answered
    assert builder._calculate_confidence(5, 1) == 0.6


# ============== SuccessCriteria Tests ==============


def test_success_criteria_to_dict():
    """Test SuccessCriteria.to_dict() conversion."""
    criteria = SuccessCriteria(
        task="Test task",
        criteria=["Criterion 1", "Criterion 2"],
        questions_asked=["Q1?", "Q2?"],
        human_responses=["A1", "A2"],
        confidence=0.85,
        metadata={"key": "value"},
    )

    result = criteria.to_dict()

    assert result["task"] == "Test task"
    assert len(result["criteria"]) == 2
    assert len(result["questions_asked"]) == 2
    assert len(result["human_responses"]) == 2
    assert result["confidence"] == 0.85
    assert result["metadata"]["key"] == "value"


def test_success_criteria_defaults():
    """Test SuccessCriteria default values."""
    criteria = SuccessCriteria(task="Test")

    assert criteria.criteria == []
    assert criteria.questions_asked == []
    assert criteria.human_responses == []
    assert criteria.confidence == 0.0
    assert criteria.metadata == {}


# ============== Integration Tests (Require LLM) ==============


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_criteria_real_llm():
    """Test criteria building with real LLM.

    Note: This test requires a real LLM executor to be configured.
    """
    pytest.importorskip("anthropic")

    try:
        from orchestration.integrations.unified import auto_setup_executor

        executor = auto_setup_executor()
    except Exception:
        pytest.skip("No LLM executor available")

    builder = CriteriaBuilder(executor, max_questions=2)
    criteria = await builder.build_criteria(
        "Build a user authentication system",
        context={"language": "Python", "framework": "FastAPI"},
    )

    # Verify result structure
    assert isinstance(criteria, SuccessCriteria)
    assert len(criteria.criteria) >= 3
    assert all(isinstance(c, str) for c in criteria.criteria)
    assert 0.0 <= criteria.confidence <= 1.0

    # Log for manual inspection
    print("\n" + "=" * 60)
    print("Real LLM Criteria Builder Result")
    print("=" * 60)
    print(f"Task: {criteria.task}")
    print(f"\nCriteria ({len(criteria.criteria)}):")
    for i, criterion in enumerate(criteria.criteria, 1):
        print(f"  {i}. {criterion}")
    print(f"\nQuestions Asked ({len(criteria.questions_asked)}):")
    for i, question in enumerate(criteria.questions_asked, 1):
        print(f"  {i}. {question}")
    print(f"\nConfidence: {criteria.confidence}")
    print("=" * 60)
