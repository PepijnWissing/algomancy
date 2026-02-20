(utils-unit-ref)=
# Unit framework

## Overview
This module provides a small, self-contained framework to represent quantities,
units, and measured values with smart, human-friendly formatting. It is used
throughout the project (notably in KPI templates) to present values using the
most appropriate unit and number of digits without writing formatting logic in
multiple places.

### Core concepts
- **Quantity**: A domain of measurement (e.g., Length, Time, Data). A quantity owns
  a chain of related units and knows how they convert.
- **Unit**: A single unit with a symbol (e.g., m, s, B). Units are linked from
  smaller to larger and vice versa so values can scale up or down.
- **BaseMeasurement**: A formatting preference object: it stores the base unit for a
  value and how it should be displayed (min/max significant digits and decimal
  places, optional smallest/largest unit clamps).
- **Measurement**: A concrete value bound to a BaseMeasurement. It can be scaled to
  a better unit and formatted with the desired precision.

### Why this exists
Displaying 15320.0 seconds as "4.26 h" or 12_345_678 B as "11.77 MiB" should be
trivial for users of the framework, and consistent across the app. This module
centralizes unit chains, conversions, and pretty-printing so KPIs and UI code
just construct a Measurement and call `pretty()`.

### Formatting Preferences
- **min_digits** / **max_digits** bound the number of significant digits before a unit
  change is attempted. This keeps values compact while avoiding "0.00" noise.
- **decimals** controls the decimal places in the final formatted string.
- **smallest_unit** / **largest_unit** can be set to restrict automatic scaling range.

## Examples
:::{dropdown} {octicon}`eye` Example: length 
:color: success
TODO Explain example

```{code-block} python
:linenos:
 from algomancy_utils.unit import QUANTITIES, BaseMeasurement, Measurement
 
 length = QUANTITIES["length"]
 length_m = BaseMeasurement(
                base_unit=length["m"],
                min_digits=1, 
                max_digits=3, 
                decimals=2
            )
 for val in [0.000005, 0.025, 2.5, 250, 25_000, 2_500_000]:
     m = Measurement(length_m, val)
     print(m.pretty())
```
```
>> 5.00 μm
>> 25.12 mm
>> 2.50 m
>> 250.00 m
>> 25.00 km
>> 2.50 Mm
```
:::


:::{dropdown} {octicon}`eye` Example: Time with tighter bounds
:color: success
TODO Explain example 

```{code-block} python
:linenos:
time = QUANTITIES["time"]
# Clamp scaling between seconds and hours, show 1 decimal
prefs = BaseMeasurement(
            base_unit=time["s"], 
            min_digits=1, 
            max_digits=2, 
            decimals=1,
            smallest_unit="s", 
            largest_unit="h"
        )
for val in [0.5, 45, 3_665, 86_400]:
    print(Measurement(prefs, val).pretty())
```
```    
>> 0.5 s
>> 45.0 s
>> 1.0 h
>> 24.0 h
```
:::

:::{dropdown} {octicon}`eye` Example: Money
:color: success
TODO Explain example

```{code-block} python
:linenos:
money = QUANTITIES["money"]
usd = BaseMeasurement(
          base_unit=money["$"], 
          min_digits=0, 
          max_digits=3, 
          decimals=2
      )
print(Measurement(usd, 1_234_567).pretty())
```
```
>> $1.23M
```
:::

## Reference
```{eval-rst}
.. automodule:: algomancy_utils.unit
   :members:
   :show-inheritance:
   :member-order: bysource
```