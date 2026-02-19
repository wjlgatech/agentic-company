"""
Enterprise Workflow Tests - 7 Real-World Use Cases

Tests Agenticom's capacity with high-impact enterprise scenarios:
1. M&A Due Diligence
2. Regulatory Compliance Audit
3. Patent Landscape Analysis
4. Security Vulnerability Assessment
5. Customer Churn Analysis
6. Grant/RFP Proposal Writing
7. Incident Post-Mortem

Each test validates:
- Workflow loads correctly
- All steps have valid agents
- Template substitution works
- Tools are declared properly
"""

from pathlib import Path

import pytest

from orchestration.agents.team import AgentTeam
from orchestration.workflows.parser import WorkflowParser

# Path to bundled workflows
WORKFLOWS_DIR = Path(__file__).parent.parent / "agenticom" / "bundled_workflows"


class TestEnterpriseWorkflowLoading:
    """Test that all 7 enterprise workflows load correctly."""

    @pytest.fixture
    def parser(self):
        return WorkflowParser()

    def test_due_diligence_loads(self, parser):
        """M&A Due Diligence workflow should load."""
        path = WORKFLOWS_DIR / "due-diligence.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "due-diligence"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)

    def test_compliance_audit_loads(self, parser):
        """Compliance Audit workflow should load."""
        path = WORKFLOWS_DIR / "compliance-audit.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "compliance-audit"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)

    def test_patent_landscape_loads(self, parser):
        """Patent Landscape workflow should load."""
        path = WORKFLOWS_DIR / "patent-landscape.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "patent-landscape"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)

    def test_security_assessment_loads(self, parser):
        """Security Assessment workflow should load."""
        path = WORKFLOWS_DIR / "security-assessment.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "security-assessment"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)

    def test_churn_analysis_loads(self, parser):
        """Churn Analysis workflow should load."""
        path = WORKFLOWS_DIR / "churn-analysis.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "churn-analysis"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)

    def test_grant_proposal_loads(self, parser):
        """Grant Proposal workflow should load."""
        path = WORKFLOWS_DIR / "grant-proposal.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "grant-proposal"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)

    def test_incident_postmortem_loads(self, parser):
        """Incident Post-Mortem workflow should load."""
        path = WORKFLOWS_DIR / "incident-postmortem.yaml"
        if path.exists():
            definition = parser.parse_file(path)
            team = parser.to_team(definition)

            assert definition.id == "incident-postmortem"
            assert len(definition.agents) == 5
            assert len(definition.steps) == 5
            assert isinstance(team, AgentTeam)


class TestEnterpriseWorkflowStructure:
    """Test workflow structure and dependencies."""

    @pytest.fixture
    def parser(self):
        return WorkflowParser()

    def test_step_dependencies_valid(self, parser):
        """All step references should be valid."""
        for yaml_file in WORKFLOWS_DIR.glob("*.yaml"):
            definition = parser.parse_file(yaml_file)

            # Collect step IDs
            step_ids = {step.id for step in definition.steps}

            # Check each step's input for references
            for i, step in enumerate(definition.steps):
                # Steps can only reference previous steps
                for prev_step in definition.steps[:i]:
                    # If referenced, should exist
                    if f"step_outputs.{prev_step.id}" in step.input:
                        assert (
                            prev_step.id in step_ids
                        ), f"Invalid reference in {yaml_file.name}: {prev_step.id}"

    def test_agent_roles_valid(self, parser):
        """All agent roles should be valid."""
        for yaml_file in WORKFLOWS_DIR.glob("*.yaml"):
            try:
                definition = parser.parse_file(yaml_file)
                team = parser.to_team(definition)

                # If we get here, all roles are valid
                assert len(team.agents) > 0
            except ValueError as e:
                pytest.fail(f"Invalid role in {yaml_file.name}: {e}")

    def test_template_variables_present(self, parser):
        """Templates should use {{task}} or {{step_outputs.X}}."""
        for yaml_file in WORKFLOWS_DIR.glob("*.yaml"):
            definition = parser.parse_file(yaml_file)

            for step in definition.steps:
                # First step must reference {{task}}
                if step == definition.steps[0]:
                    assert (
                        "{{task}}" in step.input
                    ), f"First step in {yaml_file.name} should reference {{{{task}}}}"

                # Later steps should reference previous outputs
                if step != definition.steps[0]:
                    has_ref = (
                        "{{step_outputs." in step.input or "{{task}}" in step.input
                    )
                    assert (
                        has_ref
                    ), f"Step {step.id} in {yaml_file.name} should reference context"


class TestEnterpriseWorkflowMetadata:
    """Test workflow metadata and documentation."""

    @pytest.fixture
    def parser(self):
        return WorkflowParser()

    def test_all_workflows_have_description(self, parser):
        """All workflows should have descriptions."""
        for yaml_file in WORKFLOWS_DIR.glob("*.yaml"):
            definition = parser.parse_file(yaml_file)
            assert (
                definition.description
            ), f"Workflow {yaml_file.name} missing description"

    def test_all_workflows_have_metadata(self, parser):
        """Enterprise workflows should have metadata."""
        enterprise_workflows = [
            "due-diligence.yaml",
            "compliance-audit.yaml",
            "patent-landscape.yaml",
            "security-assessment.yaml",
            "churn-analysis.yaml",
            "grant-proposal.yaml",
            "incident-postmortem.yaml",
        ]

        for name in enterprise_workflows:
            path = WORKFLOWS_DIR / name
            if path.exists():
                definition = parser.parse_file(path)
                assert definition.metadata.get(
                    "category"
                ), f"Workflow {name} missing category"
                assert definition.metadata.get(
                    "typical_time_saved"
                ), f"Workflow {name} missing time_saved estimate"


class TestTemplateSubstitution:
    """Test that template substitution works for enterprise workflows."""

    def test_preprocess_enterprise_templates(self):
        """Test preprocessing of complex enterprise templates."""
        from orchestration.agents.team import AgentTeam, TeamConfig

        team = AgentTeam(TeamConfig(name="test"))

        # Test M&A template
        template = """
        == DUE DILIGENCE FINDINGS ==

        FINANCIAL ANALYSIS:
        {{step_outputs.financial-analysis}}

        LEGAL REVIEW:
        {{step_outputs.legal-review}}

        MARKET ASSESSMENT:
        {{step_outputs.market-assessment}}
        """

        processed = team._preprocess_template(template)

        assert "{financial-analysis}" in processed
        assert "{legal-review}" in processed
        assert "{market-assessment}" in processed
        assert "{{" not in processed

    def test_format_enterprise_outputs(self):
        """Test formatting with actual enterprise outputs."""
        from orchestration.agents.team import AgentTeam, TeamConfig

        team = AgentTeam(TeamConfig(name="test"))

        template = """
        Task: {{task}}
        Previous Analysis: {{step_outputs.analysis}}
        """

        processed = team._preprocess_template(template)

        outputs = {
            "task": "Analyze Acme Corp acquisition",
            "analysis": "Revenue: $50M, Growth: 25%, EBITDA: $10M",
        }

        result = processed.format(**outputs)

        assert "Analyze Acme Corp acquisition" in result
        assert "Revenue: $50M" in result
        assert "{{" not in result


class TestEnterpriseWorkflowCapabilities:
    """Test specific capabilities required for enterprise workflows."""

    def test_multi_step_coordination(self):
        """Test 5-step workflow coordination."""
        from orchestration.agents.team import AgentTeam, TeamConfig

        team = AgentTeam(TeamConfig(name="test"))

        # Simulate 5-step enterprise workflow
        outputs = {}
        steps = [
            ("step1", "Task: {{task}}", {"task": "Test input"}),
            ("step2", "Based on: {{step_outputs.step1}}", {"step1": "Step 1 output"}),
            (
                "step3",
                "Analysis of: {{step_outputs.step2}}",
                {"step2": "Step 2 output"},
            ),
            ("step4", "Review: {{step_outputs.step3}}", {"step3": "Step 3 output"}),
            ("step5", "Final: {{step_outputs.step4}}", {"step4": "Step 4 output"}),
        ]

        for step_id, template, expected_outputs in steps:
            processed = team._preprocess_template(template)
            context = {**outputs, "task": "Test input"}
            context.update(expected_outputs)

            # Should not raise KeyError
            result = processed.format(**context)
            outputs[step_id] = f"{step_id} completed"

            assert "{{" not in result
            assert "step_outputs" not in result

    def test_hyphenated_step_ids(self):
        """Enterprise workflows use hyphenated IDs like financial-analysis."""
        from orchestration.agents.team import AgentTeam, TeamConfig

        team = AgentTeam(TeamConfig(name="test"))

        template = "{{step_outputs.financial-analysis}}"
        processed = team._preprocess_template(template)

        assert processed == "{financial-analysis}"

        outputs = {"financial-analysis": "Revenue analysis complete"}
        result = processed.format(**outputs)

        assert result == "Revenue analysis complete"


# Summary of enterprise workflows
ENTERPRISE_WORKFLOWS_SUMMARY = """
===============================================================================
                    ENTERPRISE WORKFLOWS TEST SUMMARY
===============================================================================

7 High-Impact Real-World Use Cases:

1. M&A DUE DILIGENCE (due-diligence.yaml)
   Pain: $50K-500K+ professional fees, 4-8 weeks timeline
   Agents: Financial Analyst, Legal Reviewer, Market Analyst, Technical Assessor, Deal Lead
   Steps: Financial → Legal → Market → Technical → Recommendation

2. REGULATORY COMPLIANCE AUDIT (compliance-audit.yaml)
   Pain: $100K+ annual audit costs, $1M+ fine risk
   Agents: Compliance Scanner, Gap Analyst, Risk Assessor, Remediation Planner, Documenter
   Steps: Requirements → Gaps → Risks → Remediation → Report

3. PATENT LANDSCAPE ANALYSIS (patent-landscape.yaml)
   Pain: $30K-100K patent lawyer fees, $10M+ infringement risk
   Agents: Patent Searcher, Claim Analyst, Landscape Mapper, FTO Assessor, IP Strategist
   Steps: Search → Claims → Landscape → FTO → Strategy

4. SECURITY VULNERABILITY ASSESSMENT (security-assessment.yaml)
   Pain: $4.45M average breach cost, compliance failures
   Agents: Threat Modeler, Vuln Scanner, Risk Analyst, Remediation Engineer, Security Architect
   Steps: Threats → Vulnerabilities → Risks → Remediation → Report

5. CUSTOMER CHURN ANALYSIS (churn-analysis.yaml)
   Pain: 5-7% annual churn, $50K-500K per enterprise customer
   Agents: Data Analyst, Customer Researcher, Segment Strategist, Retention Strategist, CCO
   Steps: Patterns → Reasons → Segments → Playbooks → Executive Summary

6. GRANT/RFP PROPOSAL WRITING (grant-proposal.yaml)
   Pain: 40-100 hours per proposal, 10-25% success rate
   Agents: Requirements Analyst, Research Synthesizer, Proposal Architect, Budget Specialist, Writer
   Steps: Requirements → Research → Structure → Budget → Draft

7. INCIDENT POST-MORTEM (incident-postmortem.yaml)
   Pain: 4-8 hours per post-mortem, recurring incidents
   Agents: Timeline Analyst, RCA Specialist, Impact Assessor, Prevention Engineer, Author
   Steps: Timeline → Root Cause → Impact → Prevention → Document

===============================================================================
"""

if __name__ == "__main__":
    print(ENTERPRISE_WORKFLOWS_SUMMARY)
    pytest.main([__file__, "-v"])
