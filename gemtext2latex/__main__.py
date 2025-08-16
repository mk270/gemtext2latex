"""gemtext2latex: Launcher.

© Martin Keegan <mk270@no.ucant.org> 2025.

Released under the Apache Software Licence, v2.0.
"""

import re
import sys

from gemtext2latex import main


sys.argv[0] = re.sub(r"__main__.py$", "gemtext2latex", sys.argv[0])
main()
