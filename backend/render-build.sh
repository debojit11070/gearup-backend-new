#!/usr/bin/env bash
set -e

pip install --upgrade pip

# Force pre-built wheels for the pydantic stack (avoids Rust compilation
# on fresh Python versions where the sdist is the only available source).
pip install --only-binary=:all: pydantic pydantic-core pydantic-settings || true

pip install -r requirements.txt