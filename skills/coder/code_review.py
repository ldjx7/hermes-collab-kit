import logging
from typing import Dict, Any, Optional

# Assume Coder class is available for performing the actual review via LLM
# from .coder import Coder # Uncomment if Coder is in a different file and needs explicit import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeReviewer:
    """
    Provides functionality to conduct automated code reviews using the Coder's review method.
    This class acts as an interface specifically for code review tasks.
    """
    def __init__(self, coder_instance: Optional[Any] = None): # Use Any to avoid circular import if Coder is in same file
        """
        Initializes the CodeReviewer.

        Args:
            coder_instance: An instance of the Coder class. If None, a new Coder instance is created.
        """
        # Lazy import Coder to prevent circular dependencies if Coder also imports CodeReviewer
        if coder_instance:
            self.coder = coder_instance
        else:
            try:
                from .coder import Coder, MockACPClient, MockGeminiClient
                self.coder = Coder(acp_client=MockACPClient(MockGeminiClient()))
            except ImportError as e:
                logger.error(f"Could not import Coder: {e}. Please ensure coder.py is accessible.")
                raise RuntimeError("Failed to initialize CodeReviewer due to missing Coder dependency.") from e
        logger.info("CodeReviewer initialized.")

    def review_code(self, code_content: str, review_requirements: Optional[str] = None) -> Dict[str, Any]:
        """
        Submits code for review to the underlying Coder's LLM capabilities.

        Args:
            code_content: The Python code content to be reviewed.
            review_requirements: Optional specific requirements or criteria for the review.

        Returns:
            A dictionary containing the review feedback (e.g., summary, issues, suggestions).

        Raises:
            Exception: Propagates exceptions from the Coder's review method.
        """
        logger.info(f"Starting code review for content (first 100 chars): {code_content[:100]}...")
        try:
            review_results = self.coder.review(code=code_content, requirements=review_requirements)
            logger.info("Code review completed successfully.")
            return review_results
        except Exception as e:
            logger.error(f"An error occurred during code review: {e}", exc_info=True)
            raise

    def format_review_output(self, review_data: Dict[str, Any]) -> str:
        """
        Formats the raw review data into a human-readable string.

        Args:
            review_data: The dictionary containing review feedback.

        Returns:
            A formatted string of the review results.
        """
        formatted_output = []
        if "summary" in review_data:
            formatted_output.append(f"Review Summary: {review_data['summary']}")
            formatted_output.append("-" * 30)

        if "issues" in review_data and review_data["issues"]:
            formatted_output.append("Identified Issues:")
            for issue in review_data["issues"]:
                line = f"Line {issue['line']}: " if 'line' in issue else ""
                severity = f"[{issue['severity']}] " if 'severity' in issue else ""
                description = issue.get('description', 'No description provided.')
                formatted_output.append(f"  - {line}{severity}{description}")
            formatted_output.append("-" * 30)
        else:
            formatted_output.append("No specific issues identified.")
            formatted_output.append("-" * 30)

        if "suggestions" in review_data and review_data["suggestions"]:
            formatted_output.append("Suggestions for Improvement:")
            for suggestion in review_data["suggestions"]:
                formatted_output.append(f"  - {suggestion}")
            formatted_output.append("-" * 30)
        else:
            formatted_output.append("No specific suggestions for improvement.")
            formatted_output.append("-" * 30)

        return "\n".join(formatted_output)