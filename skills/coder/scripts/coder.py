import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Assume skill classes are available relative to the skill package root
from ..coder import Coder, MockACPClient, MockGeminiClient
from ..code_review import CodeReviewer
from ..test_gen import TestGenerator

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_coder_clients() -> Coder:
    """
    Sets up and returns an initialized Coder instance with mock clients.
    In a real scenario, this would likely involve proper client configuration
    and possibly dependency injection.

    Returns:
        An instance of the Coder class.
    """
    gemini_client = MockGeminiClient()
    acp_client = MockACPClient(gemini_client)
    coder = Coder(acp_client=acp_client)
    return coder

def main():
    """
    Main entry point for the Coder CLI tool.
    Handles command-line argument parsing and dispatches to appropriate Coder functionalities.
    """
    parser = argparse.ArgumentParser(
        description="Coder CLI: An AI-powered tool for code implementation, review, and test generation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Implement command
    implement_parser = subparsers.add_parser(
        "implement", help="Implement a new feature or code based on a description."
    )
    implement_parser.add_argument(
        "task_description", type=str,
        help="A clear description of the task or feature to implement."
    )
    implement_parser.add_argument(
        "--input-file", "-i", type=Path,
        help="Optional: Path to an existing code file to use as context for implementation."
    )
    implement_parser.add_argument(
        "--output-file", "-o", type=Path,
        help="Optional: Path to save the implemented code. If not provided, prints to stdout."
    )

    # Review command
    review_parser = subparsers.add_parser(
        "review", help="Review provided code for issues and improvements."
    )
    review_parser.add_argument(
        "code_file", type=Path,
        help="Path to the code file to be reviewed."
    )
    review_parser.add_argument(
        "--requirements", "-r", type=str,
        help="Optional: Additional requirements or guidelines for the review."
    )
    review_parser.add_argument(
        "--output-file", "-o", type=Path,
        help="Optional: Path to save the review report. If not provided, prints to stdout."
    )

    # Testgen command
    testgen_parser = subparsers.add_parser(
        "testgen", help="Generate unit tests for provided code."
    )
    testgen_parser.add_argument(
        "code_file", type=Path,
        help="Path to the code file for which to generate tests."
    )
    testgen_parser.add_argument(
        "--requirements", "-r", type=str,
        help="Optional: Specific requirements or scenarios for the generated tests."
    )
    testgen_parser.add_argument(
        "--output-file", "-o", type=Path,
        help="Optional: Path to save the generated tests. If not provided, prints to stdout."
    )

    args = parser.parse_args()

    coder_instance = setup_coder_clients()

    if args.command == "implement":
        existing_code_content: Optional[str] = None
        if args.input_file:
            try:
                existing_code_content = args.input_file.read_text(encoding='utf-8')
                logger.info(f"Read existing code from {args.input_file}")
            except FileNotFoundError:
                logger.error(f"Input file not found: {args.input_file}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Error reading input file {args.input_file}: {e}")
                sys.exit(1)
        
        try:
            implemented_code = coder_instance.implement(
                task_description=args.task_description,
                existing_code=existing_code_content
            )
            if args.output_file:
                args.output_file.write_text(implemented_code, encoding='utf-8')
                logger.info(f"Implemented code saved to {args.output_file}")
            else:
                print(implemented_code)
        except Exception as e:
            logger.error(f"Implementation failed: {e}", exc_info=True)
            sys.exit(1)

    elif args.command == "review":
        try:
            code_content = args.code_file.read_text(encoding='utf-8')
            logger.info(f"Read code for review from {args.code_file}")
        except FileNotFoundError:
            logger.error(f"Code file not found: {args.code_file}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading code file {args.code_file}: {e}")
            sys.exit(1)
        
        reviewer = CodeReviewer(coder_instance=coder_instance)
        try:
            review_results = reviewer.review_code(
                code_content=code_content,
                review_requirements=args.requirements
            )
            formatted_review = reviewer.format_review_output(review_results)
            if args.output_file:
                args.output_file.write_text(formatted_review, encoding='utf-8')
                logger.info(f"Review report saved to {args.output_file}")
            else:
                print(formatted_review)
        except Exception as e:
            logger.error(f"Code review failed: {e}", exc_info=True)
            sys.exit(1)

    elif args.command == "testgen":
        try:
            code_content = args.code_file.read_text(encoding='utf-8')
            logger.info(f"Read code for test generation from {args.code_file}")
        except FileNotFoundError:
                logger.error(f"Code file not found: {args.code_file}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading code file {args.code_file}: {e}")
            sys.exit(1)

        test_generator = TestGenerator(coder_instance=coder_instance)
        try:
            generated_tests = test_generator.generate_tests(
                code_to_test=code_content,
                test_requirements=args.requirements
            )
            if args.output_file:
                args.output_file.write_text(generated_tests, encoding='utf-8')
                logger.info(f"Generated tests saved to {args.output_file}")
            else:
                print(generated_tests)
        except Exception as e:
            logger.error(f"Test generation failed: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    main()