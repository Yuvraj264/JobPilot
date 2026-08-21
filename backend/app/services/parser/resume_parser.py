from typing import Dict, Any, Optional
from app.services.parser.text_extractor import TextExtractor
from app.services.parser.deterministic_parser import DeterministicParser
from app.services.parser.ai_provider import AIProvider, LocalMockAIProvider


class ResumeParser:
    """
    Modular Orchestrator for processing uploaded resume documents.
    Pipeline:
      1. Extract raw text via TextExtractor (PDF/DOCX)
      2. Layer 1: Run DeterministicParser for structured extraction
      3. Layer 2: Optionally enhance via AIProvider if configured
    """

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai_provider = ai_provider or LocalMockAIProvider()

    def parse_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Parses document file and returns structured dictionary representation.
        """
        # Step 1: Text extraction
        raw_text = TextExtractor.extract_text(file_path, file_type)

        # Step 2: Layer 1 Deterministic extraction
        parsed_data = DeterministicParser.parse(raw_text)

        # Step 3: Layer 2 AI enhancement (if applicable)
        if not isinstance(self.ai_provider, LocalMockAIProvider):
            try:
                ai_enhanced = self.ai_provider.generate_structured_output(
                    prompt=f"Extract structured resume details from text:\n{raw_text[:2000]}"
                )
                if ai_enhanced and "data" in ai_enhanced and isinstance(ai_enhanced["data"], dict):
                    # Merge AI findings with deterministic findings
                    for k, v in ai_enhanced["data"].items():
                        if v and not parsed_data.get(k):
                            parsed_data[k] = v
            except Exception as e:
                print(f"AI enhancement skipped due to error: {e}")

        # Retain raw text for quality & consistency analysis
        parsed_data["raw_text"] = raw_text
        return parsed_data
