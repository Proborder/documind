from fastapi import APIRouter

from app.api.dependencies import LLMClientDep
from app.core.exceptions import LLMProviderException, LLMProviderHTTPException
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("", response_model=AgentResponse)
async def run_agent(llm_client: LLMClientDep, payload: AgentRequest) -> AgentResponse:
    try:
        return await AgentService(llm_client=llm_client).run_agent(payload)
    except LLMProviderException as ex:
        raise LLMProviderHTTPException from ex
