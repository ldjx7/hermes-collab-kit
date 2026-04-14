import logging
from typing import List, Dict, Any, Optional

# Assume Coder class is available for performing the actual test generation via LLM
# from .coder import Coder # Uncomment if Coder is in a different file and needs explicit import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestGenerator:
    """
    Generates unit tests for given Python code using the Coder's implementation method.
    This class specializes in providing an interface for test generation tasks.
    """
    def __init__(self, coder_instance: Optional[Any] = None): # Use Any to avoid circular import if Coder is in same file
        """
        Initializes the TestGenerator.

        Args:
            coder_instance: An instance of the Coder class. If None, a new Coder instance is created.
        """
        # Lazy import Coder to prevent circular dependencies if Coder also imports TestGenerator
        if coder_instance:
            self.coder = coder_instance
        else:
            try:
                from .coder import Coder, MockACPClient, MockGeminiClient
                self.coder = Coder(acp_client=MockACPClient(MockGeminiClient()))
            except ImportError as e:
                logger.error(f"Could not import Coder: {e}. Please ensure coder.py is accessible.")
                raise RuntimeError("Failed to initialize TestGenerator due to missing Coder dependency.") from e
        logger.info("TestGenerator initialized.")

    def generate_tests(self, code_to_test: str, test_requirements: Optional[str] = None) -> str:
        """
        Generates unit tests for the provided Python code using an LLM.

        Args:
            code_to_test: The Python code for which to generate tests.
            test_requirements: Optional specific requirements or scenarios for the tests.

        Returns:
            A string containing the generated Python unit tests.

        Raises:
            Exception: Propagates exceptions from the Coder's implement method (used for generation).
        """
        logger.info(f"Starting test generation for code (first 100 chars): {code_to_test[:100]}...")
        task_description = (
            "Generate comprehensive unit tests for the following Python code. "
            "Use the `unittest` framework. Ensure good test coverage including "
            "edge cases and error handling if applicable.\n"
        )
        if test_requirements:
            task_description += f"\nSpecific test requirements: {test_requirements}\n"
        
        task_description += "Provide only the Python code for the tests, enclosed in a markdown code block."

        try:
            # Reusing the implement method of Coder for test generation
            # as it's essentially a code generation task.
            generated_tests = self.coder.implement(task_description=task_description, existing_code=code_to_test)
            logger.info("Test generation completed successfully.")
            return generated_tests
        except Exception as e:
            logger.error(f"An error occurred during test generation: {e}", exc_info=True)
            raise

    def _extract_test_functions(self, test_code: str) -> List[str]:
        """
        (Placeholder) Extracts individual test functions from the generated test code.
        This could be used for more granular test execution or analysis.

        Args:
            test_code: The full string of generated test code.

        Returns:
            A list of strings, each representing a test function.
        """
        # This is a simplified placeholder. A real implementation might use AST parsing.
        logger.debug("Attempting to extract test functions (placeholder).")
        test_functions = []
        current_function = []
        in_function = False
        
        for line in test_code.splitlines():
            if line.strip().startswith("def test_"):
                if in_function and current_function:
                    test_functions.append("\n".join(current_function).strip())
                    current_function = []
                in_function = True
                current_function.append(line)
            elif in_function and (line.startswith(" ") or line.startswith("\t")): # part of the function body
                current_function.append(line)
            elif in_function and not (line.startswith(" ") or line.startswith("\t")): # end of function
                if current_function:
                    test_functions.append("\n".join(current_function).strip())
                current_function = []
                in_function = False
            elif not in_function and current_function: # if there was a function and loop ended without finding another def test_
                 test_functions.append("\n".join(current_function).strip())
                 current_function = []
        if current_function: # add the last function if it exists
            test_functions.append("\n".join(current_function).strip())
        
        if not test_functions and "def test_" in test_code: # simple fallback if parsing fails
            logger.warning("Simplified test function extraction failed, returning full code as a single 'function'.")
            return [test_code]

        return test_functions