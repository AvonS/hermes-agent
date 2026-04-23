#!/usr/bin/env python3
"""
Wiki Distill Tool - Process session messages to extract and file insights to the wiki.

This tool implements the auto-distillation functionality that runs at session end
or before context compression to extract valuable information from the conversation
and file it into the knowledge base using llm-wiki principles.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from hermes_constants import get_hermes_home
from tools.registry import tool_error

def _extract_entities_concepts(text: str) -> Tuple[Set[str], Set[str]]:
    """
    Extract potential entity and concept mentions from text.
    Very basic implementation - in production would use NER or more sophisticated methods.
    """
    # Simple heuristic: capitalized phrases, quoted terms, code-like terms
    entities = set()
    concepts = set()
    
    # Find quoted terms
    quoted = re.findall(r'"([^"]*)"|\'([^\']*)\'', text)
    for match in quoted:
        term = match[0] or match[1]
        if term and len(term) > 2:
            entities.add(term)
    
    # Find capitalized phrases (potential entities)
    cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    for phrase in cap_phrases:
        if len(phrase) > 2 and phrase not in ['The', 'This', 'That', 'And', 'Or', 'But']:
            entities.add(phrase)
    
    # Find technical terms (all caps or camelCase)
    tech_terms = re.findall(r'\b[A-Z]{2,}[A-Z0-9]*\b|\b[a-z]+[A-Z][a-zA-Z]*\b', text)
    for term in tech_terms:
        if len(term) > 2:
            concepts.add(term)
    
    # Find file paths and tool names
    file_tool_patterns = [
        r'\b\w+\.(py|js|ts|json|yaml|yml|md|txt)\b',
        r'\b(tool|function|class|method)\s+\w+\b',
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(tool|framework|library|model)\b'
    ]
    for pattern in file_tool_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                term = match[0] if match[0] else match[1]
            else:
                term = match
            if term and len(term) > 2:
                entities.add(term)
    
    return entities, concepts

def _extract_code_snippets(text: str) -> List[str]:
    """Extract code snippets from markdown code blocks."""
    # Simple extraction of code blocks
    code_blocks = re.findall(r'```(\w+)?\n([^}]*?)```', text, re.DOTALL)
    snippets = []
    for lang, code in code_blocks:
        if code.strip():
            # Truncate very long snippets
            snippet = code.strip()[:500]
            if len(code.strip()) > 500:
                snippet += "..."
            snippets.append(f"({lang or 'text'}) {snippet}")
    return snippets

def _extract_decisions_opens(text: str) -> Tuple[List[str], List[str]]:
    """Extract decisions made and open questions from text."""
    decisions = []
    open_questions = []
    
    # Decision indicators
    decision_patterns = [
        r'we\s+(decided|chose|selected|went with|will use)\s+[^.!?]*[.!?]',
        r'i\s+(decided|chose|selected|will use)\s+[^.!?]*[.!?]',
        r'decision:?\s*[^.!?]*[.!?]',
        r'we\s+should\s+[^.!?]*[.!?]',
        r'let\'s\s+[^.!?]*[.!?]'
    ]
    
    for pattern in decision_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        decisions.extend([m.strip() for m in matches if m.strip()])
    
    # Open question indicators
    question_patterns = [
        r'[^.!?]*\?(?=\s|$)',
        r'we\s+(need to|should|could|might)\s+[^.!?]*[.!?]',
        r'how\s+do\s+we\s+[^.!?]*[.!?]',
        r'what\s+if\s+[^.!?]*[.!?]',
        r'i\s+wonder\s+[^.!?]*[.!?]'
    ]
    
    for pattern in question_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        open_questions.extend([m.strip() for m in matches if m.strip() and len(m.strip()) > 10])
    
    # Deduplicate and limit
    decisions = list(dict.fromkeys(decisions))[:5]
    open_questions = list(dict.fromkeys(open_questions))[:5]
    
    return decisions, open_questions

def wiki_distill_session(
    session_messages: List[Dict[str, Any]] = None,
    wiki_path: str = None,
    action: str = "distill"  # distill, preview, or test
) -> str:
    """
    Distill session messages into wiki updates.
    
    Args:
        session_messages: List of message dicts (from session history). 
                         If None, attempts to load from current session (not implemented).
        wiki_path: Path to the wiki directory. If None, uses WIKI_PATH env var or ~/wiki.
        action: What to do - "distill" (perform actual updates), 
                "preview" (show what would be done), 
                "test" (run with sample data)
    
    Returns:
        JSON string with results.
    """
    # Determine wiki path
    if wiki_path is None:
        wiki_path = os.environ.get('WIKI_PATH', str(Path.home() / 'wiki'))
    wiki_path = Path(wiki_path)
    
    # If in test mode, use sample data
    if action == "test":
        session_messages = [
            {"role": "user", "content": "How do I fine-tune Llama 2 for medical QA? What are the best practices?"},
            {"role": "assistant", "content": "For fine-tuning Llama 2 on medical QA, you should use QLoRA with a learning rate of 1e-4. Consider using the MedMCQA dataset. Remember to use gradient accumulation and mixed precision training."},
            {"role": "user", "content": "Should I use LoRA or full fine-tuning?"},
            {"role": "assistant", "content": "For medical QA with limited data, LoRA (or QLoRA) is preferable to full fine-tuning. It's more parameter-efficient and reduces overfitting risk. Full fine-tuning would require more data and compute."},
            {"role": "user", "content": "What about evaluation metrics?"},
            {"role": "assistant", "content": "Use exact match and F1 score for QA evaluation. Also consider BERTScore and ROUGE-L for language quality."}
        ]
        action = "preview"  # Still preview with test data
    
    if session_messages is None:
        return tool_error(
            "Session messages are required for wiki_distill_session. "
            "In a real implementation, this would be pulled from the current session.",
            success=False
        )
    
    if not session_messages:
        return tool_error("No session messages provided.", success=False)
    
    # Combine all message content for analysis
    full_text = " ".join([
        msg.get("content", "") 
        for msg in session_messages 
        if msg.get("role") in ["user", "assistant"]
    ])
    
    if not full_text.strip():
        return tool_error("No content found in session messages.", success=False)
    
    # Extract insights
    entities, concepts = _extract_entities_concepts(full_text)
    code_snippets = _extract_code_snippets(full_text)
    decisions, open_questions = _extract_decisions_opens(full_text)
    
    # Prepare what would be done
    preview = {
        "session_analysis": {
            "total_messages": len(session_messages),
            "user_messages": len([m for m in session_messages if m.get("role") == "user"]),
            "assistant_messages": len([m for m in session_messages if m.get("role") == "assistant"]),
            "total_chars": len(full_text)
        },
        "extracted_entities": sorted(list(entities))[:10],
        "extracted_concepts": sorted(list(concepts))[:10],
        "code_snippets_found": len(code_snippets),
        "decisions_made": decisions,
        "open_questions": open_questions
    }
    
    if action == "preview":
        return json.dumps({
            "success": True,
            "action": "preview",
            "wiki_path": str(wiki_path),
            "preview": preview,
            "message": "Preview mode - no changes made to wiki. Use action='distill' to perform actual updates."
        })
    
    elif action == "distill":
        # In a real implementation, this would:
        # 1. For each high-confidence entity/concept, check if wiki page exists
        # 2. If exists: update with new information (using llm-wiki update principles)
        # 3. If not exists and meets notability threshold: create new page
        # 4. File noteworthy decisions, code snippets, open questions
        # 5. Update index.md and log.md
        #
        # For this prototype, we'll simulate the process
        
        # Simulate what would be created/updated
        would_create = []
        would_update = []
        
        # Simple notability: entities/concepts mentioned 2+ times in session
        # In reality would need frequency counting
        notable_entities = list(entities)[:3]  # Pretend these are notable
        notable_concepts = list(concepts)[:3]
        
        for entity in notable_entities:
            would_create.append(f"entities/{entity.lower().replace(' ', '-')}.md")
        
        for concept in notable_concepts:
            would_create.append(f"concepts/{concept.lower().replace(' ', '-')}.md")
        
        # Would update index.md and log.md
        would_update = ["index.md", "log.md"]
        
        # Would create a query page for the session
        session_summary = full_text[:200] + "..." if len(full_text) > 200 else full_text
        would_create.append(f"queries/session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
        
        return json.dumps({
            "success": True,
            "action": "distill",
            "wiki_path": str(wiki_path),
            "distillation_results": {
                "entities_processed": len(entities),
                "concepts_processed": len(concepts),
                "decisions_filed": len(decisions),
                "open_questions_filed": len(open_questions),
                "code_snippets_filed": len(code_snippets),
                "pages_would_create": would_create,
                "files_would_update": would_update,
                "session_summary_preview": session_summary
            },
            "message": "Distillation completed. In a full implementation, this would have updated the wiki. "
                     "This prototype shows what would be done."
        })
    
    else:
        return tool_error(f"Unknown action: {action}. Use 'distill', 'preview', or 'test'.", success=False)

# Tool registration schema
TOOL_SCHEMA = {
    "name": "wiki_distill_session",
    "description": "Distill session messages into wiki updates - extract entities, concepts, decisions, and file them into the knowledge base. Runs at session end or before context compression.",
    "parameters": {
        "type": "object",
        "properties": {
            "session_messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "assistant", "system", "tool"]},
                        "content": {"type": "string"}
                    }
                },
                "description": "List of session messages to distill. If omitted, attempts to use current session (not implemented in prototype)."
            },
            "wiki_path": {
                "type": "string",
                "description": "Path to the wiki directory. If omitted, uses WIKI_PATH environment variable or ~/wiki."
            },
            "action": {
                "type": "string",
                "enum": ["distill", "preview", "test"],
                "description": "What to do: 'distill' (perform updates), 'preview' (show what would be done), 'test' (run with sample data).",
                "default": "preview"
            }
        }
    }
}

# For direct testing
if __name__ == "__main__":
    # Test with sample data
    result = wiki_distill_session(
        action="test"
    )
    print(result)