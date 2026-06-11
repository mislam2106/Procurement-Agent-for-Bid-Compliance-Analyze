"""Tests for the orchestrator pipeline."""

import pytest
from unittest.mock import patch, MagicMock
from src.orchestrator import BidComplianceOrchestrator, BidAnalysisState


def test_bid_analysis_state_defaults():
    state = BidAnalysisState()
    assert state.source_filename == ""
    assert state.metadata is None
    assert state.compliance_checklist is None
    assert state.oem_checklist is None
    assert state.envelope_contents is None


def test_orchestrator_invalid_file():
    orch = BidComplianceOrchestrator()
    with pytest.raises(FileNotFoundError):
        orch.run("nonexistent_file.pdf")
