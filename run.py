#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datastore.api import app
app.run(host='0.0.0.0', port=5001)
