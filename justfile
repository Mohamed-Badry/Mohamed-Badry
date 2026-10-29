default: update

# Fetch latest GitHub stats into tools/profile/data/
fetch:
    uv run python tools/profile/fetch.py

# Render SVGs from tools/profile/data/ into assets/
render:
    uv run --with fonttools --with brotli python tools/profile/render.py

# Update README.md with generated assets and accessible alt text
readme:
    uv run python tools/profile/readme.py

# Run the complete pipeline (fetch, render, readme)
update: fetch render readme
