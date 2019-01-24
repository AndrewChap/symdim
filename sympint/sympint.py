import pint
import sympy
ureg = pint.UnitRegistry()

# Class that inherits from sympy.Symbol but also gets the 'parent' attribute so we can find the Sympint instance from the symbol
class Symbol(sympy.Symbol):
    def __init__(self,name,parent=None):
        super().__new__(name=name,cls=sympy.Symbol) # call sympy.symbol __new__ method
        self.parent = parent # assign parent

# Main Sympint class
class Sympint:
    def __init__(self,
                 symbol=None,
                 expression=None,
                 unit=None,
                 value=None):
        # If first input is a float or int, assign it to Value and make it dimensionless
        # example: Sympint(42)
        if isinstance(symbol,float) or isinstance(symbol,int):
            self.value = symbol
            self.unit = ureg.dimensionless
            self.symbol = None
            self.expression = sympy.Number(symbol)
            return
        # else, symbol should be a string or another sympy symbol
        # Take input symbol as a string or a 
        # sympy.Symbol and store it as a sympy.Symbol
        elif isinstance(symbol,str):
            self.symbol = Symbol(symbol,parent=self)
        else:
            self.symbol = symbol
        # If Sympint object has no expression, 
        # set its expression to its own symbol
        # If it doesn't have a symbol, set it
        # to an empty string
        if expression is None:
            if self.symbol is None:
                self.expression = None
            else:
                self.expression = self.symbol
        else:
            self.expression = expression
        
        # unit must be of type 
        # pint.unit.build_unit_class.<locals>.Unit
        # (no error handling for this yet)
        self.unit = unit
        
        # Value must be float, won't work if some Sympints are floats and some Sympints are ints
        if value is not None:
            self.value = float(value)
        else:
            self.value = None
            
    # Set the symbol of sympy part of the object
    def set_symbol(self,string):
        self.symbol = symbol(string,parent=self)

    # Set the symbol equal to an expression.
    def equals(self,other):
        if other.expression != self.symbol:
            self.expression = other.expression
        if (self.unit is None or self.unit == ureg.dimensionless) and (other.unit is not None and other.unit != ureg.dimensionless):
            self.unit = other.unit
        if self.value is None and other.value is not None:
            self.value = other.value

    # solve the expression for other, and return a new Sympint for the solution
    # currently just returns the first expression in the list.  If you wanted
    # to return multiple solutions, remove the [0] and iterate through them.
    def solve_for(self,other):
        eq = sympy.Eq(self.symbol,self.expression)
        expression = sympy.solve(eq,other.symbol)[0]
        output = Sympint(symbol=other.symbol,expression=expression)
        output.evaluate()
        return output
    
    # Recursively evaluate self.expression to get the units and value of the expression
    def evaluate(self):
        if self.expression.is_Symbol:
            self.symbol = self.expression.parent.symbol
            self.value = self.expression.parent.value
            self.unit = self.expression.parent.unit
        else:
            try:
                self.value = float(self.expression)
                self.unit = ureg.dimensionless
            except:
                output = Sympint()
                if self.expression.is_Mul or self.expression.is_Add:
                    for i,arg_sympy in enumerate(self.expression.args):
                        arg = Sympint(expression=arg_sympy)
                        arg.evaluate()
                        if i == 0:
                            output = arg
                        else:
                            if self.expression.is_Mul:
                                output = output*arg
                            elif self.expression.is_Add:
                                output = output + arg
                elif self.expression.is_Pow:
                    arg = Sympint(expression=self.expression.as_base_exp()[0])
                    exponent = Sympint(expression=self.expression.as_base_exp()[1])
                    arg.evaluate()
                    exponent.evaluate()
                    output = arg**exponent
                    
                self.unit = output.unit
                self.value = output.value
            
    # override the add, subtract, multiply, divide, and power operations
    def __add__(self,other):
        return self.override_operator(other,'__add__')
    def __sub__(self,other):
        return self.override_operator(other,'__sub__')
    def __mul__(self,other):
        return self.override_operator(other,'__mul__')
    __rmul__ = __mul__
    def __truediv__ (self,other):
        return self.override_operator(other,'__truediv__')
    def __intdiv__ (self,other):
        return self.override_operator(other,'__intdiv__')
    def __pow__(self,other):
        return self.override_operator(other,'__pow__')
    
    # helper function for overriding add, subtract, multiply, divide, and power operations
    def override_operator(self,other,operator):
        # if the other is not a Sympint, then it is either a number or a sympy number, so we make a Sympint out of it
        if not isinstance(other,Sympint):
            try:
                expression = sympy.Number(other)
            except:
                #try expression = sympy.Symbol(other)
                expression = other
            try:
                value = float(other)
                unit = ureg.dimensionless
            except:
                value = None
                unit = None
                raise ValueError('cannot convert {} to value'.format(other))
            other=Sympint(expression=expression,value=value,unit=unit)
        # Now other is definitely a Sympint
        # Apply operator to expressions
        expression = getattr(self.expression,operator)(other.expression)
        try:
            unit = getattr(self.unit, operator)(other.unit)
        except:
            if self.unit is None or other.unit is None:
                unit = None

        if self.unit is None or other.unit is None: # if units are unknown
            unit = None
        elif operator == '__pow__' and other.unit == ureg.dimensionless:
            unit = self.unit**other.value
        else:
            try:   # try applying the operator to the units to see if we get a usable result
                unit = getattr(self.unit, operator)(other.unit)
            except:
                if self.unit == other.unit:
                    unit = self.unit
                else:
                    raise ValueError('ValueError: units "{}" and "{}" do not match for operation method "{}"'.format(self.unit,other.unit,operator))

        # set the value of the result
        if self.value is not None and other.value is not None:
            value = getattr(self.value, operator)(other.value)
        #elif self.value is not None:
        #    value = self.value
        else:
            value = None
        return Sympint(symbol=None,expression=expression,unit=unit,value=value)
    
    # override __repr__ geared specifically for Jupyter notebooks
    def __repr__(self):
        # first display the sympy expression
        if self.symbol is not None and self.expression == self.symbol:
            display(self.symbol)
        elif self.symbol is not None and self.expression is not None:
            display(sympy.Eq(self.symbol,self.expression))
        elif self.expression is not None:
            display(self.expression)
        # then return the symbol, value, and unit for printing
        if self.symbol is None:
            symbol = 'unnamed'
        else:
            symbol = self.symbol
        if self.unit is None:
            unit = 'Unknown units'
        else:
            # can only convert to base units after multiplying by one!
            unit = str((1.0*self.unit).to_base_units())[4:]
        if self.value is None:
            value = '\b' # delete space so we don't have two spaces
        else:
            value = self.value
        # kludge alert: printing base units puts a '1.0 ' in front,
        # so we trim off the first four characters.
        return '{} = {} [{}]'.format(symbol,value,unit)
