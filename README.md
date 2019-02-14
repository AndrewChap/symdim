# SymDim
A python class that uses the computer algebra of [SymPy](https://github.com/sympy/sympy) and the unit system of [Astropy](https://github.com/astropy/astropy) to do equation manipulation and dimensional analysis in Jupyter Notebooks.  SymPy's dimensional analysis is lacking and Astropy doesn't contain equation manipulation, so this is an attempt to combine the best of both worlds.  The idea is to manipulate equations and then check the units and evaluate them as needed.

## Examples:
```python
S = Sympint
from astropy import units as u
x = S('x', unit=u.m, value=5.0)
L = S('L', unit=u.m, value=3.0)
Zw = S('Z_w')
T0 = S('T_0', unit=u.K,value=300.0)
T0.equals(Zw**(x/L-S(1)/S(2))) # enclose '1' and '2' in Sympint so python doesn't evaluate 1/2 as 0.5
display(T0)
# now solve for Zw, whatever that is
Zw = T0.solve_for(Zw)
display(Zw)
```

will display

![Sample Sympint output](https://raw.githubusercontent.com/AndrewChap/sympint/master/images/sympint.png)

## TO-DO:
* Add tests
* Refactor some of the kludges
* Add Equation class (inherit from SymPy's equations)
