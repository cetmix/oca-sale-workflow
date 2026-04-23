This module extends the Sale Order form to introduce a Discount Type selection field.

When a discount type is selected and a value entered, the corresponding module’s existing logic handles propagation
to all sale order lines (percentage applied via standard  discount  field; fixed amount applied via  discount_fixed  field).
This module does not re-implement the downstream propagation logic - it only controls which input is exposed.
