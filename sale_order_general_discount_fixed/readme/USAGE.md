To use this module, you need to:

- Create a sale order and add at least one order line;
- In the **General Fixed Discount** field Enter the fixed discount amount in the sales order currency (e.g., `50.00`);
- The system will proportionally distribute this amount across all order lines, updating the **Fixed Discount** column (`discount_fixed`) on each line.

**Note:** If order lines are added, updated, or removed after setting the global fixed discount, the distribution is recalculated automatically.
