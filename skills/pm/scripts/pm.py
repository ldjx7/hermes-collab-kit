#!/usr/bin/env python3
"""
CLI Entry Point for the PM Skill.
"""
import argparse
import logging
import sys
import os

# Add the parent directory to sys.path to allow importing the skills module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from skills.pm import ProjectManager

def setup_logging(verbose: bool):
    """Configures the logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def main():
    parser = argparse.ArgumentParser(description="Hermes Collab Kit - PM Skill CLI")
    parser.add_argument(
        "request", 
        type=str, 
        help="The natural language request or task description for the PM."
    )
    parser.add_argument(
        "--workspace", 
        type=str, 
        default=".", 
        help="Path to the workspace directory (default: current directory)."
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Enable verbose debug logging."
    )

    args = parser.parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger("pm_cli")
    logger.info("Starting PM CLI...")

    try:
        # Initialize the PM system
        pm = ProjectManager(workspace_path=args.workspace)
        
        # Process the request
        result = pm.handle_request(args.request)
        
        # Output the result
        if result["status"] == "success":
            logger.info("Request processed successfully.")
            for task_id, info in result.get("data", {}).items():
                print(f"Task ID: {task_id}")
                print(f"  Title: {info['task_title']}")
                print(f"  Assigned Agent: {info['assigned_agent']}")
                print("-" * 40)
        else:
            logger.error(f"Failed to process request: {result.get('message')}")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Fatal error in PM CLI: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()