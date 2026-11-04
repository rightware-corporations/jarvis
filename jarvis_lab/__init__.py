"""VEXEL Jarvis remote test adapters; never include real OS tools by default."""

from jarvis_lab.headless import create_headless_assistant, memory_for_subject

__all__ = ["create_headless_assistant", "memory_for_subject"]
