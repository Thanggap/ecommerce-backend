#!/bin/bash
# Wrapper to run alembic migrations in production environment

cd /home/thang/Documents/ecommerce-backend

# Use python3 directly from system
export PYTHONPATH=/home/thang/Documents/ecommerce-backend

# Run upgrade
python3 -m pip install alembic --user
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/thang/Documents/ecommerce-backend')

from alembic.config import Config
from alembic import command

alembic_cfg = Config('alembic.ini')
command.upgrade(alembic_cfg, 'head')
PYTHON_EOF
