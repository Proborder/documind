import json
import re
from typing import Any

from anthropic.types import MessageParam

from app.core.config import settings
from app.schemas.agent import AgentRequest, AgentResponse, AgentToolCall
from app.services.base import BaseService


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def extract_numbers(text: str) -> list[float]:
    matches = re.findall(r"[-+]?\d+(?:[.,]\d+)?", text)
    return [float(match.replace(",", ".")) for match in matches]


class AgentService(BaseService):
    tools = [
        {
            "name": "count_words",
            "description": "Count words in the provided text.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to count words in.",
                    }
                },
                "required": ["text"],
            },
        },
        {
            "name": "extract_numbers",
            "description": "Extract all numeric values from the provided text.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract numbers from.",
                    }
                },
                "required": ["text"],
            },
        },
    ]

    async def run_agent(self, payload: AgentRequest) -> AgentResponse:
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": (
                    f"Question:\n{payload.query}\n\n"
                    f"Document text:\n{payload.document_text}"
                ),
            }
        ]
        tools_called: list[AgentToolCall] = []
        answer = ""
        system_prompt = (
            "You are a document analysis agent. "
            "Use the available tools when they are needed to answer the question. "
            "If the question asks for word counts or numeric values, call the relevant tools. "
            "You may call multiple tools in one step. "
            "When using tools, pass the exact full document text as the text argument."
        )

        for iteration in range(1, settings.AGENT_MAX_ITERATIONS + 1):
            response = await self.llm_client.create_message(
                messages=messages,
                system=system_prompt,
                tools=self.tools
            )
            response_text = self._extract_text(response.content)
            if response_text:
                answer = response_text

            if response.stop_reason != "tool_use":
                return AgentResponse(
                    answer=answer,
                    tools_called=tools_called,
                    iterations=iteration
                )

            assistant_content: list[dict[str, Any]] = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

            messages.append({"role": "assistant", "content": assistant_content})
            tool_results: list[dict[str, Any]] = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = dict(block.input or {})
                result = self._execute_tool(tool_name, tool_input)
                tools_called.append(
                    AgentToolCall(name=tool_name, input=tool_input, result=result)
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            if not tool_results:
                return AgentResponse(
                    answer=answer,
                    tools_called=tools_called,
                    iterations=iteration,
                    truncated=True,
                )

            messages.append({"role": "user", "content": tool_results})

        return AgentResponse(
            answer=answer,
            tools_called=tools_called,
            iterations=settings.AGENT_MAX_ITERATIONS,
            truncated=True
        )

    @staticmethod
    def _execute_tool(name: str, tool_input: dict[str, Any]) -> Any:
        text = str(tool_input.get("text", ""))
        if name == "count_words":
            return count_words(text)
        if name == "extract_numbers":
            return extract_numbers(text)
        return {"error": f"Unknown tool: {name}"}

    @staticmethod
    def _extract_text(content) -> str:
        answer = ""
        for block in content:
            if block.type == "text":
                answer += block.text
        return answer
