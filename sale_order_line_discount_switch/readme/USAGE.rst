#. Open *Sales* and create or edit a quotation or order.
#. On an order line (list or form), set **Discount type** to *Percentage* or
   *Fixed amount* (if you do not see the fields, enable optional columns in the list
   and ensure your user is allowed to apply line discounts).
#. In *Percentage* mode, enter the discount as a percentage (standard Odoo).
#. In *Fixed amount* mode, enter the fixed discount; subtotals and the equivalent
   percentage are computed as in *Sale Fixed Discount*.

When you change the mode, the other input is hidden and the unused amount is
cleared. Switching to *Fixed amount* with an existing percentage will propose a
matching fixed value based on the current unit price.
