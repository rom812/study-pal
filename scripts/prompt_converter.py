#!/usr/bin/env python3
"""
Prompt Converter - Converts natural language prompts into structured format
for optimal Cursor Code Agent interactions.

Usage:
    python scripts/prompt_converter.py "your natural prompt here"
    OR
    python scripts/prompt_converter.py (interactive mode)
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional


class PromptConverter:
    """Converts natural language prompts to structured format."""
    
    def __init__(self):
        self.structure_template = {
            "CONTEXT": "",
            "INTENT": "",
            "CONSTRAINTS": [],
            "ACCEPTANCE_CRITERIA": [],
            "PRIORITIES": []
        }
    
    def analyze_prompt(self, prompt: str) -> Dict[str, any]:
        """Analyze natural prompt and extract structured components."""
        structured = {
            "CONTEXT": self._extract_context(prompt),
            "INTENT": self._extract_intent(prompt),
            "CONSTRAINTS": self._extract_constraints(prompt),
            "ACCEPTANCE_CRITERIA": self._extract_criteria(prompt),
            "PRIORITIES": self._extract_priorities(prompt)
        }
        return structured
    
    def _extract_context(self, prompt: str) -> str:
        """Extract context information from prompt."""
        # Look for file references, current state descriptions
        context_indicators = [
            r'in\s+(?:the\s+)?([a-zA-Z_/\.]+\.(?:py|yaml|md|json|txt|ts|tsx|js|jsx))',
            r'([a-zA-Z_/\.]+\.(?:py|yaml|md|json|txt|ts|tsx|js|jsx))\s+(?:file|module|class|component)',
            r'([a-zA-Z_/\.]+/[a-zA-Z_/\.]+\.(?:py|yaml|md|json|txt|ts|tsx|js|jsx))',  # paths with slashes
            r'([a-zA-Z_]+_agent\.py)',  # agent files
            r'currently\s+(?:has|does|is|uses)',
            r'right\s+now',
            r'existing\s+(?:code|implementation|system)'
        ]
        
        context_parts = []
        for pattern in context_indicators:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                context_parts.extend(matches)
        
        # Remove duplicates and filter
        context_parts = list(set(context_parts))
        context_parts = [p for p in context_parts if len(p) > 3]  # Filter very short matches
        
        if context_parts:
            return f"Current state involves: {', '.join(context_parts)}"
        return "No specific context detected - please add file paths or current state description"
    
    def _extract_intent(self, prompt: str) -> str:
        """Extract intent/action from prompt."""
        # Look for action verbs
        action_verbs = [
            r'(add|create|implement|build|make|write|generate)',
            r'(fix|repair|resolve|solve|correct)',
            r'(refactor|improve|optimize|enhance|update)',
            r'(remove|delete|eliminate)',
            r'(modify|change|alter|update)',
            r'(integrate|connect|link)',
            r'(test|verify|validate)'
        ]
        
        intent_parts = []
        for pattern in action_verbs:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                intent_parts.append(matches[0])
                break
        
        # Extract the main task description
        sentences = re.split(r'[.!?]\s+', prompt)
        main_sentence = sentences[0] if sentences else prompt
        
        if intent_parts:
            return f"{intent_parts[0].capitalize()}: {main_sentence}"
        return main_sentence.capitalize()
    
    def _extract_constraints(self, prompt: str) -> List[str]:
        """Extract constraints and requirements."""
        constraints = []
        
        # Look for constraint indicators
        constraint_patterns = [
            r'(?:must|should|need to|required to|have to)\s+(?:not\s+)?(.+?)(?:\.|,|$)',
            r'(?:don\'?t|do not|avoid|prevent)\s+(.+?)(?:\.|,|$)',
            r'(?:follow|use|maintain|keep|preserve)\s+(.+?)(?:\.|,|$)',
            r'(?:without|without\s+breaking|maintain)\s+(.+?)(?:\.|,|$)',
        ]
        
        for pattern in constraint_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            constraints.extend([m.strip() for m in matches if m.strip()])
        
        # Default constraints if none found
        if not constraints:
            constraints.append("Maintain existing functionality")
            constraints.append("Follow existing code patterns")
            constraints.append("Ensure all tests pass")
        
        return constraints[:5]  # Limit to 5 most relevant
    
    def _extract_criteria(self, prompt: str) -> List[str]:
        """Extract acceptance criteria."""
        criteria = []
        
        # Look for criteria indicators
        criteria_patterns = [
            r'(?:should|must|need to)\s+(?:be able to|work|support|handle)\s+(.+?)(?:\.|,|$)',
            r'(?:when|after|once)\s+(.+?)(?:\.|,|$)',
            r'(?:verify|ensure|check|test)\s+(?:that\s+)?(.+?)(?:\.|,|$)',
        ]
        
        for pattern in criteria_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            criteria.extend([m.strip() for m in matches if m.strip()])
        
        # Default criteria if none found
        if not criteria:
            criteria.append("Functionality works as expected")
            criteria.append("No breaking changes")
            criteria.append("Tests pass")
        
        return criteria[:5]  # Limit to 5 most relevant
    
    def _extract_priorities(self, prompt: str) -> List[str]:
        """Extract priorities or order of work."""
        priorities = []
        
        # Look for priority indicators
        priority_patterns = [
            r'(?:first|priority|start with|begin with|focus on)\s+(.+?)(?:\.|,|$)',
            r'(?:then|next|after that|followed by)\s+(.+?)(?:\.|,|$)',
        ]
        
        for pattern in priority_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            priorities.extend([m.strip() for m in matches if m.strip()])
        
        # If no explicit priorities, infer from intent
        if not priorities:
            intent = self._extract_intent(prompt)
            if intent:
                priorities.append(intent)
        
        return priorities[:5]  # Limit to 5 most relevant
    
    def format_structured_prompt(self, structured: Dict[str, any]) -> str:
        """Format structured prompt as markdown."""
        output = []
        output.append("## Structured Prompt\n")
        
        if structured["CONTEXT"]:
            output.append(f"**CONTEXT:** {structured['CONTEXT']}\n")
        
        if structured["INTENT"]:
            output.append(f"**INTENT:** {structured['INTENT']}\n")
        
        if structured["CONSTRAINTS"]:
            output.append("**CONSTRAINTS:**")
            for constraint in structured["CONSTRAINTS"]:
                output.append(f"  - {constraint}")
            output.append("")
        
        if structured["ACCEPTANCE_CRITERIA"]:
            output.append("**ACCEPTANCE_CRITERIA:**")
            for criterion in structured["ACCEPTANCE_CRITERIA"]:
                output.append(f"  - {criterion}")
            output.append("")
        
        if structured["PRIORITIES"]:
            output.append("**PRIORITIES:**")
            for i, priority in enumerate(structured["PRIORITIES"], 1):
                output.append(f"  {i}. {priority}")
            output.append("")
        
        return "\n".join(output)
    
    def convert(self, prompt: str) -> str:
        """Convert natural prompt to structured format."""
        structured = self.analyze_prompt(prompt)
        return self.format_structured_prompt(structured)


def interactive_mode():
    """Run in interactive mode."""
    converter = PromptConverter()
    
    print("=" * 70)
    print("Prompt Converter - Interactive Mode")
    print("Enter your natural language prompt (or 'quit' to exit)")
    print("=" * 70)
    print()
    
    while True:
        try:
            user_input = input("Your prompt: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n" + "=" * 70)
            print("STRUCTURED PROMPT:")
            print("=" * 70)
            print()
            result = converter.convert(user_input)
            print(result)
            print("=" * 70)
            print()
            print("💡 Tip: Review and refine the structured prompt above.")
            print("   Add specific file paths, constraints, and acceptance criteria.")
            print("   Copy the structured prompt to use with Cursor Code Agent.")
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        prompt = " ".join(sys.argv[1:])
        converter = PromptConverter()
        result = converter.convert(prompt)
        print(result)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()

