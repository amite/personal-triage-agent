
def main [] {
    print "Checking dependencies..."
    let cmd = 'import chromadb; import sentence_transformers; print("✓ Dependencies installed")'
    uv run python -c $cmd
}