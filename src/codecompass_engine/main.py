from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from tree_sitter import Parser
from tree_sitter_languages import get_language
import re

# --- Pydantic Models ---
# We no longer need an Enum. We will accept any language string.
class AnalysisRequest(BaseModel):
    language: str
    content: str

# --- Tree-sitter Service ---
class TreeSitterService:
    def __init__(self):
        self.parsers = {} # Start with an empty cache of parsers
        self.languages = {} # Cache for language objects
        print("Tree-sitter Service initialized with on-demand loading.")

    def _get_parser(self, language_name: str) -> Parser:
        """Dynamically loads a parser for a given language and caches it."""
        if language_name in self.parsers:
            return self.parsers[language_name]

        try:
            language = self.languages.get(language_name)
            if not language:
                language = get_language(language_name)
                self.languages[language_name] = language
            
            parser = Parser()
            parser.set_language(language)
            self.parsers[language_name] = parser
            print(f"Successfully loaded parser for: {language_name}")
            return parser
        except Exception as e:
            print(f"Failed to load parser for {language_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Parser for language '{language_name}' is not supported or failed to load.")

    def analyze_code(self, request: AnalysisRequest):
        """Analyzes a code snippet for various opportunities."""
        parser = self._get_parser(request.language)
        tree = parser.parse(bytes(request.content, "utf8"))
        
        opportunities = []
        
        # Run our finders
        hardcoded_secrets = self._find_hardcoded_secrets(tree, request.language)
        opportunities.extend(hardcoded_secrets)
        
        return {"status": "analyzed", "opportunities": opportunities}

    def _find_hardcoded_secrets(self, tree, language: str):
        """Uses a tree-sitter query to find potential hardcoded secrets."""
        # A tree-sitter query to find variable assignments with string literals
        query_string = """
        (assignment
          left: (identifier) @variable_name
          right: (string) @string_value)
        """
        # Different languages have different node names
        if language in ['python']:
            query_string = """
            (assignment
              left: (identifier) @variable_name
              right: (string) @string_value)
            """
        elif language in ['javascript', 'typescript']:
             query_string = """
            (variable_declarator
              name: (identifier) @variable_name
              value: [(template_string) @string_value (string) @string_value])
             """

        parser = self._get_parser(language)
        query = parser.language.query(query_string)
        captures = query.captures(tree.root_node)
        
        found_secrets = []
        SENSITIVE_VAR_REGEX = re.compile(r'key|secret|token|password|cred', re.IGNORECASE)
        HIGH_ENTROPY_REGEX = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9]{20,}')

        for node, name in captures:
            if name == 'variable_name':
                var_name_text = node.text.decode('utf8')
                # Find the corresponding string value for this variable
                for val_node, val_name in captures:
                    if val_name == 'string_value' and val_node.parent == node.parent:
                        string_val_text = val_node.text.decode('utf8').strip('\'"`')
                        
                        # Apply heuristics
                        if SENSITIVE_VAR_REGEX.search(var_name_text) and HIGH_ENTROPY_REGEX.search(string_val_text):
                            found_secrets.append({
                                "type": "HARDCODED_SECRET",
                                "line": node.start_point[0] + 1,
                                "variable": var_name_text
                            })
        return found_secrets

# --- FastAPI Application ---
app = FastAPI(
    title="CodeCompass Analysis Engine",
    description="The high-performance Python service for AI-powered code analysis.",
    version="1.0.0"
)

tree_sitter_service = TreeSitterService()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "CodeCompass Analysis Engine is running."}

@app.post("/analyze-file")
def analyze_file(request: AnalysisRequest):
    """
    Accepts a code file and language, analyzes it for opportunities,
    and returns the findings.
    """
    return tree_sitter_service.analyze_code(request)