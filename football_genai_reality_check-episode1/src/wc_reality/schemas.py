from __future__ import annotations

GROUNDING_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "question": {"type": "string"},
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "fact_id": {"type": "string"},
                    "claim": {"type": "string"},
                    "source_title": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["fact_id", "claim", "source_title", "source_url"],
            },
        },
        "abstained": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "notes": {"type": "string"},
    },
    "required": ["question", "answer", "citations", "abstained", "confidence", "notes"],
}

def empty_answer(question: str, reason: str) -> dict:
    return {
        "question": question,
        "answer": f"I do not have enough local evidence to answer that reliably. {reason}",
        "citations": [],
        "abstained": True,
        "confidence": 0.0,
        "notes": reason,
    }
