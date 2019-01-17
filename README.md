# sympint
A python class that uses the best parts from Sympy and Pint to do equation manipulation and dimensional analysis in Jupyter Notebooks.

## Examples:
```python
S = Sympint
x = S('x', unit=ureg.meter, value=5.0)
L = S('L', unit=ureg.meter, value=3.0)
Zw = S('Z_w')
T0 = S('T_0', unit=ureg.kelvin,value=300.0)
T0.equals(Zw**(x/L-S(1)/S(2))) # enclose '1' and '2' in Sympint so python doesn't evaluate them 1/2 as 0.5
display(T0)
# now solve for Zw, whatever that is
Zw = T0.solve_for(Zw)
display(Zw)
```

will display

![Sample Sympint output](https://raw.githubusercontent.com/AndrewChap/sympint/master/images/sympint.png)

## TO-DO:
* Add tests
* Display units in TeX
* Refactor some of the kludges
* Instead of storing `unit` and `value` as two separate fields, it might be better to only use one field of Pint units, and have a flag as to whether we know the value or only the units, and display it accordingly.
* Look into derivatives/integration in Sympy and see if we can implement that with Pint
