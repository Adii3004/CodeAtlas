"""PromptBuilder: assembles the grounded answering prompt.

Structure: system instructions, repository summary, retrieved context,
user question — in that order.
"""

from context.models import ContextSection, LLMContext

SYSTEM_INSTRUCTIONS = """\
You are CodeAtlas, an assistant that answers questions about one specific \
code repository.

Rules you must always follow:
1. Answer ONLY using the context supplied below. Do not use outside \
knowledge about libraries, frameworks, or code that is not shown.
2. Never invent code, file names, functions, or behavior that is not \
present in the context.
3. If the context does not contain enough information to answer, say so \
plainly and state what is missing. Do not guess.
4. When you reference code, always mention the file name (and symbol name \
if relevant) it comes from.
5. Explain your reasoning clearly and step by step, so the reader can \
verify the answer against the referenced files."""

NO_CONTEXT_MARKER = "(no relevant context was retrieved for this query)"


class PromptBuilder:
    """Builds the single-shot answering prompt from an LLMContext."""

    def build(self, query: str, context: LLMContext) -> str:
        """Build the full answering prompt for one query."""
        summary_sections = [
            s for s in context.sections if s.title == "Repository Summary"
        ]
        content_sections = [
            s for s in context.sections if s.title != "Repository Summary"
        ]

        parts: list[str] = [SYSTEM_INSTRUCTIONS, ""]

        parts.append("## Repository Summary")
        if summary_sections:
            parts.append(self._render_sections(summary_sections))
        else:
            parts.append("(no repository summary available)")
        parts.append("")

        parts.append("## Retrieved Context")
        if content_sections:
            parts.append(self._render_sections(content_sections))
        else:
            parts.append(NO_CONTEXT_MARKER)
        parts.append("")

        parts.append("## User Question")
        parts.append(query)

        return "\n".join(parts)

    @staticmethod
    def _render_sections(sections: list[ContextSection]) -> str:
        lines: list[str] = []
        for section in sections:
            lines.append(f"### {section.title}")
            for chunk in section.chunks:
                location = chunk.relative_path
                if chunk.symbol_name:
                    location += f" :: {chunk.symbol_name}"
                lines.append(
                    f"--- {location} (lines {chunk.start_line}-{chunk.end_line}) ---"
                )
                lines.append(chunk.content)
                lines.append("")
        return "\n".join(lines).rstrip()
