Follow the same requirements as *Sale Fixed Discount*:

#. Give users the *Discount on lines* / per-line discount permission (e.g. enable
   *Sales > Configuration > Settings* under *Pricing* and grant the technical group
   ``product.group_discount_per_so_line`` to sales users as needed).
#. ``account_invoice_fixed_discount`` is installed automatically with the
   dependency chain; no extra parameters are required for this add-on.
