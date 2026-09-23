import asyncio
from typing import Dict, Any, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from app.agents.research_agent import ResearchAgent
from app.agents.strategist_agent import StrategistAgent
from app.agents.writer_agent import WriterAgent
from app.agents.quality_agent import QualityAgent
from app.agents.revision_agent import RevisionAgent
from app.services.markdown_service import MarkdownService
from app.config import settings

class WorkflowState(TypedDict):
    job_id: str
    job_data: Dict[str, Any]
    status: str
    current_step: str
    retry_count: int
    revision_notes: Optional[str]
    error_message: Optional[str]

class ContentWorkflow:
    @staticmethod
    async def node_research(state: WorkflowState) -> WorkflowState:
        job_id = state["job_id"]
        job_data = state["job_data"]
        try:
            await ResearchAgent.run(job_id, job_data)
            return {
                **state,
                "status": "RESEARCH_COMPLETE",
                "current_step": "RESEARCH_COMPLETE"
            }
        except Exception as e:
            return {
                **state,
                "status": "FAILED",
                "error_message": f"Research node failed: {str(e)}"
            }

    @staticmethod
    async def node_strategy(state: WorkflowState) -> WorkflowState:
        job_id = state["job_id"]
        job_data = state["job_data"]
        try:
            await StrategistAgent.run(job_id, job_data)
            return {
                **state,
                "status": "BRIEF_COMPLETE",
                "current_step": "BRIEF_COMPLETE"
            }
        except Exception as e:
            return {
                **state,
                "status": "FAILED",
                "error_message": f"Strategy node failed: {str(e)}"
            }

    @staticmethod
    async def node_writing(state: WorkflowState) -> WorkflowState:
        job_id = state["job_id"]
        job_data = state["job_data"]
        revision_notes = state.get("revision_notes")
        try:
            await WriterAgent.run(job_id, job_data, revision_notes=revision_notes)
            return {
                **state,
                "status": "DRAFT_COMPLETE",
                "current_step": "DRAFT_COMPLETE"
            }
        except Exception as e:
            return {
                **state,
                "status": "FAILED",
                "error_message": f"Writing node failed: {str(e)}"
            }

    @staticmethod
    async def node_revision(state: WorkflowState) -> WorkflowState:
        job_id = state["job_id"]
        job_data = state["job_data"]
        try:
            await RevisionAgent.run(job_id, job_data)
            return {
                **state,
                "status": "DRAFT_COMPLETE",
                "current_step": "DRAFT_COMPLETE"
            }
        except Exception as e:
            return {
                **state,
                "status": "FAILED",
                "error_message": f"Revision node failed: {str(e)}"
            }

    @staticmethod
    async def node_quality_check(state: WorkflowState) -> WorkflowState:
        job_id = state["job_id"]
        job_data = state["job_data"]
        retry_count = state.get("retry_count", 0)

        try:
            passed, result_status, metrics = await QualityAgent.evaluate_and_finalize(job_id, job_data)

            if passed:
                return {
                    **state,
                    "status": "AWAITING_APPROVAL",
                    "current_step": "FINAL_READY",
                    "revision_notes": None
                }
            else:
                if retry_count < settings.MAX_REVISION_ATTEMPTS:
                    return {
                        **state,
                        "status": "REVISION_REQUIRED",
                        "current_step": "REVISION_REQUIRED",
                        "retry_count": retry_count + 1,
                        "revision_notes": "Quality check flagged claim inaccuracies or keyword density issues. Executing targeted revision."
                    }
                else:
                    return {
                        **state,
                        "status": "MANUAL_REVIEW_REQUIRED",
                        "current_step": "MANUAL_REVIEW_REQUIRED",
                        "error_message": f"Quality audit findings unresolved after {retry_count} revision attempts. Manual review required."
                    }
        except Exception as e:
            return {
                **state,
                "status": "FAILED",
                "error_message": f"Quality node failed: {str(e)}"
            }

    @classmethod
    def build_graph(cls):
        workflow = StateGraph(WorkflowState)

        workflow.add_node("research", cls.node_research)
        workflow.add_node("strategy", cls.node_strategy)
        workflow.add_node("writing", cls.node_writing)
        workflow.add_node("revision", cls.node_revision)
        workflow.add_node("quality_check", cls.node_quality_check)

        workflow.set_entry_point("research")

        workflow.add_edge("research", "strategy")
        workflow.add_edge("strategy", "writing")
        workflow.add_edge("writing", "quality_check")
        workflow.add_edge("revision", "quality_check")

        def route_quality(state: WorkflowState):
            if state["status"] == "AWAITING_APPROVAL":
                return END
            elif state["status"] == "REVISION_REQUIRED":
                return "revision"
            else:
                return END

        workflow.add_conditional_edges("quality_check", route_quality)

        return workflow.compile()

