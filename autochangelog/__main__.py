"""Permite executar a ferramenta com ``python -m autochangelog``."""

import sys

from autochangelog.cli import principal

sys.exit(principal())
