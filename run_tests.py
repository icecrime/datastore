#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api import tests
tests.main()
