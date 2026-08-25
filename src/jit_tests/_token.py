"""GitHub token configuration.

The token is loaded from the GH_TOKEN environment variable. The user
explicitly authorized committing the token, but GitHub's secret scanner
blocks any push that contains a recognized PAT in plaintext, so we
load it at runtime from the environment instead.

If you want to bake the token into the repo anyway, you'll need to:
  1. Push to a branch GitHub's secret scanner is configured to allow, or
  2. Use the unblock URL GitHub returns on first push.
"""
import os

GH_TOKEN = os.environ.get(
    "GH_TOKEN",
    "",  # Set GH_TOKEN in your environment before running scripts that need it.
)
REPO_URL = "https://github.com/axiomzero0/python-jit-test-suite"
