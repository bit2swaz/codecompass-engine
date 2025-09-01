import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from tree_sitter import Parser
from tree_sitter_languages import get_language
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Pydantic Models for API Data Structure ---
class AnalysisRequest(BaseModel):
    language: str
    content: str

class Opportunity(BaseModel):
    type: str
    line: int
    variable: str

class AnalysisResponse(BaseModel):
    status: str
    opportunities: list[dict]

# --- Tree-sitter Service ---
class TreeSitterService:
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        print("Tree-sitter Service initialized with on-demand loading.")

    def _get_parser(self, language_name: str) -> Parser:
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
            raise HTTPException(status_code=500, detail=f"Parser for language '{language_name}' is not supported.")

    def find_opportunities(self, request: AnalysisRequest) -> list[Opportunity]:
        parser = self._get_parser(request.language)
        tree = parser.parse(bytes(request.content, "utf8"))
        
        opportunities = []
        # We can add more universal finders here later
        opportunities.extend(self._find_hardcoded_secrets(tree, request.language))
        return opportunities

    def _find_hardcoded_secrets(self, tree, language: str) -> list[Opportunity]:
        query_string = """
        (variable_declarator
          name: (identifier) @variable_name
          value: [(template_string) @string_value (string) @string_value])
        """
        if language == 'python':
            query_string = """
            (assignment
              left: (identifier) @variable_name
              right: (string) @string_value)
            """
        
        parser = self._get_parser(language)
        query = parser.language.query(query_string)
        captures = query.captures(tree.root_node)
        
        found_secrets = []
        SENSITIVE_VAR_REGEX = re.compile(r'key|secret|token|password|cred', re.IGNORECASE)
        HIGH_ENTROPY_REGEX = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9]{20,}')

        variable_nodes = {node.id: node for node, name in captures if name == 'variable_name'}
        value_nodes = {node.id: node for node, name in captures if name == 'string_value'}

        for node, name in captures:
            if name == 'variable_name':
                var_name_text = node.text.decode('utf8')
                for val_node, val_name in captures:
                    if val_name == 'string_value' and val_node.parent and val_node.parent.id == node.parent.id:
                        string_val_text = val_node.text.decode('utf8').strip('\'"`')
                        if SENSITIVE_VAR_REGEX.search(var_name_text) and HIGH_ENTROPY_REGEX.search(string_val_text):
                            found_secrets.append(Opportunity(
                                type="HARDCODED_SECRET",
                                line=node.start_point[0] + 1,
                                variable=var_name_text
                            ))
        return found_secrets

# --- AI Service ---
class AIService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("AI Service initialized.")

    def create_universal_prompt(self, language: str, code_snippet: str) -> str:
        # This is the universal, language-agnostic prompt
        return f"""
        You are CodeCompass, a world-class principal software engineer and an expert in the programming language: {language}.
        
        Perform a holistic code review of the following code snippet, which is written in {language}.
        
        Analyze the code for any and all issues related to:
        - Performance bottlenecks
        - Readability and code style
        - Security vulnerabilities
        - Maintainability and anti-patterns
        - Adherence to modern best practices for {language}
        
        If you find opportunities for improvement, respond ONLY with a valid JSON object containing a single key "opportunities", which is a list of objects.
        Each opportunity object must have the following keys: "title" (a short, descriptive title), "problem" (a simple, one-paragraph explanation with an analogy), and "solution" (a brief, step-by-step explanation using numbered points separated by '\\n').
        
        If you find NO opportunities, respond ONLY with an empty JSON object: {{"opportunities": []}}.
        
        Do not include ```json markdown wrappers in your response.
        
        Code Snippet to Analyze:
        ```
        {code_snippet}
        ```
        """

    async def generate_insights(self, request: AnalysisRequest) -> list[dict]:
        prompt = self.create_universal_prompt(request.language, request.content)
        try:
            response = await self.model.generate_content_async(prompt)
            # A more robust JSON parsing
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text.strip())
            data = json.loads(cleaned_response)
            return data.get("opportunities", [])
        except Exception as e:
            print(f"AI insight generation failed: {e}")
            return []


# --- FastAPI Application ---
app = FastAPI(
    title="CodeCompass Analysis Engine",
    description="The high-performance Python service for AI-powered code analysis.",
    version="1.0.0"
)

tree_sitter_service = TreeSitterService()
ai_service = AIService()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "CodeCompass Analysis Engine is running."}

@app.post("/analyze-file", response_model=AnalysisResponse)
async def analyze_file(request: AnalysisRequest):
    """
    Accepts a code file and language, analyzes it with tree-sitter and AI,
    and returns the findings.
    """
    # For now, we are going straight to the AI.
    # In the future, we can combine tree-sitter findings with AI findings.
    ai_opportunities = await ai_service.generate_insights(request)
    
    return AnalysisResponse(status="analyzed", opportunities=ai_opportunities)

# Need to import json for the AI service
import json
