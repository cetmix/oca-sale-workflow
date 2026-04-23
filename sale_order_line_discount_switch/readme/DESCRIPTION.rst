This module adds a *discount type* on each sales order line: **Percentage** (native
behavior: the user types a percent) or **Fixed amount** (the logic from
``sale_fixed_discount``: a fixed value that keeps the line consistent with the same
totals, taxes, and invoice propagation as the base module). Only one mode is active
per line: the other input is hidden and the inactive amount is cleared so the
``sale_fixed_discount`` consistency rules are never violated in day-to-day use.
