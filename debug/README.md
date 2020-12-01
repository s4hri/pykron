# Debugging tests

These are the files used for debugging certain properties of the Pykron which
are not suitable for general pytest directory.

All files are designed to use the supplied Pykron without installing it:
```python
import sys
sys.path.append('..')

from pykron.core import Pykron, PykronLogger
```
In order to launch them please do:
```
cd debug
python3 debug01.py
```
