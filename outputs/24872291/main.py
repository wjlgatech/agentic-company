# main.py
"""
AI Content Creation Multi-Agent Workflow System
Main orchestration module for managing the entire content creation pipeline
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from agents.content_discovery import ContentDiscoveryAgent
from agents.strategic_planning import StrategicPlanningAgent
from agents.script_generation import ScriptGenerationAgent
from agents.visual_creation import VisualContentAgent
from agents.video_production import VideoProductionAgent
from agents.quality_assurance import QualityAssuranceAgent
from agents.publication import PublicationAgent
from agents.analytics import AnalyticsAgent
from interfaces.client_interface import ClientDecisionInterface
from core.workflow_engine import WorkflowOrchestrationEngine
from core.models import WorkflowState, ContentItem, VideoProject
from core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CLIENT = "waiting_client"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowResult:
    """Result of complete workflow execution"""
    success: bool
    video_url: Optional[str]
    analytics_data: Dict[str, Any]
    execution_time: float
    errors: List[str]

class AIContentWorkflowSystem:
    """Main system orchestrator for AI content creation workflow"""
    
    def __init__(self, config: Config):
        self.config = config
        self.workflow_engine = WorkflowOrchestrationEngine(config)
        self.client_interface = ClientDecisionInterface(config)
        
        # Initialize all agents
        self.content_discovery = ContentDiscoveryAgent(config)
        self.strategic_planning = StrategicPlanningAgent(config)
        self.script_generation = ScriptGenerationAgent(config)
        self.visual_creation = VisualContentAgent(config)
        self.video_production = VideoProductionAgent(config)
        self.quality_assurance = QualityAssuranceAgent(config)
        self.publication = PublicationAgent(config)
        self.analytics = AnalyticsAgent(config)
        
    async def run_daily_workflow(self) -> WorkflowResult:
        """Execute the complete daily content creation workflow"""
        start_time = datetime.now()
        workflow_id = f"workflow_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting workflow {workflow_id}")
            
            # Step 1: Content Discovery & Curation (5 min target)
            content_candidates = await self.content_discovery.discover_content()
            
            # Step 2: Strategic Content Planning (2 min target)
            strategic_options = await self.strategic_planning.generate_strategies(content_candidates)
            
            # Step 3: Client Decision Point 1 - Content Selection
            selected_content = await self.client_interface.get_content_selection(strategic_options)
            
            # Step 4: Script Generation (3 min target)
            script = await self.script_generation.generate_script(selected_content)
            
            # Step 5: Client Decision Point 2 - Script Approval
            approved_script = await self.client_interface.get_script_approval(script)
            
            # Step 6: Visual Content Creation (4 min target)
            visuals = await self.visual_creation.create_visuals(approved_script)
            
            # Step 7: Video Production (15 min target)
            video_draft = await self.video_production.produce_video(approved_script, visuals)
            
            # Step 8: Quality Assurance (2 min target)
            qa_result = await self.quality_assurance.review_video(video_draft)
            
            # Step 9: Client Final Approval
            if qa_result.requires_client_review:
                final_approval = await self.client_interface.get_final_approval(video_draft, qa_result)
                if not final_approval.approved:
                    return WorkflowResult(False, None, {}, 0, ["Client rejected final video"])
            
            # Step 10: Publication & Distribution (3 min target)
            publication_result = await self.publication.publish_video(video_draft)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            
            # Start analytics tracking
            await self.analytics.start_tracking(publication_result.video_url)
            
            logger.info(f"Workflow {workflow_id} completed in {execution_time:.2f} minutes")
            
            return WorkflowResult(
                success=True,
                video_url=publication_result.video_url,
                analytics_data={"workflow_id": workflow_id, "execution_time": execution_time},
                execution_time=execution_time,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            return WorkflowResult(
                success=False,
                video_url=None,
                analytics_data={},
                execution_time=(datetime.now() - start_time).total_seconds() / 60,
                errors=[str(e)]
            )

if __name__ == "__main__":
    config = Config.load_from_env()
    system = AIContentWorkflowSystem(config)
    
    async def main():
        result = await system.run_daily_workflow()
        print(f"Workflow completed: {result.success}")
        if result.video_url:
            print(f"Video published: {result.video_url}")
    
    asyncio.run(main())