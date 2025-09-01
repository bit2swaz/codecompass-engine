from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from tree_sitter import Language, Parser
import os

# --- Pydantic Models for API Data Structure ---
class SupportedLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"

class CodeFile(BaseModel):
    language: SupportedLanguage
    content: str

# --- Tree-sitter Service ---
class TreeSitterService:
    def __init__(self):
        # Define the path for our compiled language library
        self.library_path = 'build/my-languages.so'
        
        # Build the library if it doesn't exist
        if not os.path.exists(self.library_path):
            print("Language library not found. Building...")
            Language.build_library(
                # Store the library in the `build` directory
                self.library_path,
                # List the paths to the parser repos
                [
                    'vendor/tree-sitter-python',
                    'vendor/tree-sitter-javascript'
                ]
            )
            print("Language library built successfully.")

        self.parsers = {
            'python': Parser(),
            'javascript': Parser()
        }
        PY_LANGUAGE = Language(self.library_path, 'python')
        JS_LANGUAGE = Language(self.library_path, 'javascript')
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

# Create a single instance of our service to be used by the app
tree_sitter_service = TreeSitterService()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "CodeCompass Analysis Engine is running."}

@app.post("/parse-file")
def parse_file(file: CodeFile):
    """
    Accepts a code file, parses it using tree-sitter, 
    and returns the root node's type to confirm success.
    """
    return tree_sitter_service.parse(file)