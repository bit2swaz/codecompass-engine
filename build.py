from tree_sitter import Language

# This is the correct way to call the build_library method
Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',

  # List the paths to the parser repos
  [
    'vendor/tree-sitter-python',
    'vendor/tree-sitter-javascript',
    # Add paths to other languages here in the future
  ]
)

print("Tree-sitter language library built successfully!")