"""The local report sections, one module each.

Every module in this package is imported here, and each registers itself on
``report_sections``, so adding a section is adding one file. A section that
needs data some indexes lack (outcomes, for one) returns ``None`` from
``collect`` when the data is absent and is then left out of the report.
"""

from __future__ import annotations

import importlib
import pkgutil

for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_module.name}")
