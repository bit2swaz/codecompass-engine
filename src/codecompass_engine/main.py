from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from tree_sitter import Parser
from tree_sitter_languages import get_language # Use the high-level helper
import os

# --- Pydantic Models ---
class SupportedLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"

class CodeFile(BaseModel):
    language: SupportedLanguage
    content: str

# --- Tree-sitter Service ---
class TreeSitterService:
    def __init__(self):
        self.parsers = {
            'python': Parser(),
            'javascript': Parser()
        }
        # Use the get_language helper which handles the library path automatically
        PY_LANGUAGE = get_language('python')
        JS_LANGUAGE = get_language('javascript')
        
        self.parsers['python'].set_language(PY_LANGUAGE)
        self.parsers['javascript'].set_language(JS_LANGUAGE)
        
        print("Tree-sitter parsers loaded successfully.")

    def parse(self, file: CodeFile):
        parser = self.parsers.get(file.language.value)
        if not parser:
            raise HTTPException(status_code=400, detail=f"Parser for language '{file.language}' not available.")
        
        tree = parser.parse(bytes(file.content, "utf8"))
        return {"status": "parsed", "root_node_type": tree.root_node.type}

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

@app.post("/parse-file")
def parse_file(file: CodeFile):
    return tree_sitter_service.parse(file)