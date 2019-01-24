import pint
import sympy
ureg = pint.UnitRegistry()

# Class that inherits from sympy.Symbol but also gets the 'parent' attribute so we can find the Sympint instance from the symbol
class Symbol(sympy.Symbol):
    def __init__(self,name,parent=None):
        super().__new__(name=name,cls=sympy.Symbol) # call sympy.symbol __new__ method
        self.parent = parent # assign parent
        
class SymPint:
    def __init__(self,
                 name=None,
                 unit=None,
                 value=None,
                 symVal=None,
                 expression=None,
                 valueKnown=False,
                 equals=None,
                ):
        
        
        if isinstance(name,str):
            # e.g. SymPint('a')
            self.name = name
            self.symbol = Symbol(self.name,parent=self)
        else:
            # e.g. SymPint(4) or SymPint(expression=a*b)
            self.name = '\mathrm{unnamed\,expr.}'
            try:
                self.symbol = sympy.Number(name)
                self.unit = ureg.dimensionless
            except:
                self.symbol = None
            if isinstance(name,int) or isinstance(name,float):
                value = float(name)
                unit = ureg.dimensionless
            
        
        self.set_expression(expression)
        self.set_unit(unit,value)
        self.set_value(value,valueKnown)
        
        if equals is not None:
            self.equals(equals)
    
    # unit stores both our unit and value
    def set_unit(self,unit,value):
        if unit is not None:
            self.unit = unit
        elif value is not None:
            self.unit = ureg.dimensionless
        else:
            self.unit = None
    
    # Value is only used as an input variable
    def set_value(self,value,valueKnown):
        if value is not None and valueKnown is False:
            self.unit = value*self.unit
            self.valueKnown = True
        elif valueKnown is False:
            if self.unit is not None:
                self.unit = 1.0*self.unit
            self.valueKnown = False
        else:
            self.valueKnown = True
    
    def set_expression(self,expression):
        if expression is not None:
            self.expression = expression
            self.expressionKnown = True
        else:
            try:
                self.expression = self.symbol
            except:
                self.expression = None
            self.expressionKnown = False
            
    def get_expression(self):
        if self.expressionKnown:
            return self.expression
        else:
            return self
            
    # sets everything equal to other except for name
    def equals(self,other):
        if self.unit is None:
            self.unit = other.unit
        if other.unit is not None and self.unit.to_base_units() != other.unit.to_base_units():
            # known issue, sometimes pint will not recognize equivalent units,
            # which is why we don't raise an error here
            print('Warning: units of {} and {} do not match'.format(self,other))
            self.unit = other.unit
        self.set_expression(other.get_expression())
        self.expressionKnown = True
        if self.valueKnown is False:
            self.valueKnown = other.valueKnown
        
    # currently just returns the first expression in the list.  If you wanted
    # to return multiple solutions, remove the [0] and iterate through them.
    def solve_for(self,other):
        # for example, if we want to solve z=x*y for y, we would call:
        # >>> y = z.solve_for(y)
        # and our inputs in this function would be:
        #    self = SymPint(name='z',expression=x*y)
        #    other = SymPint(name='y',expression=y)

        # create an equation, e.g. sympy.Eq(z,x*y)
        eq = sympy.Eq(self.symbol,self.expression)
        # solve the equation for other, e.g. sympy.solve(z=x*y,y), which returns z/x
        expressions = sympy.solve(eq,other.expression)
        # Create a new SymPint with name of what we are solving for equal to expression
        outputs = [SymPint(name=other.name,expression=expression) for expression in expressions]
        # Evaluate the expression to get units
        [output.evaluate() for output in outputs]
        return outputs
    
    #def evaluate(self):
        
    
    def evaluate(self):
        # if our expression is a Symbol, set our SymPint's values to the Symbol's parent's values
        if isinstance(self.expression,Symbol):
            self.symbol = self.expression.parent.symbol
            self.valueKnown = self.expression.parent.valueKnown
            self.unit = self.expression.parent.unit
        elif isinstance(self.expression,SymPint):
            self.valueKnown = self.expression.valueKnown
            self.unit = self.expression.unit
        elif isinstance(self.expression,sympy.Number):
            self.valueKnown = True
            self.unit = float(self.expression)*ureg.dimensionless
        else:
            if self.expression.is_Mul or self.expression.is_Add:
                for i,arg_sympy in enumerate(self.expression.args):
                    arg = SymPint(expression=arg_sympy)
                    arg.evaluate()                    
                    if i == 0:
                        output = arg
                    else:
                        if self.expression.is_Mul:
                            output = output*arg
                        elif self.expression.is_Add:
                            output = output + arg
            elif self.expression.is_Pow:
                arg = SymPint(expression=self.expression.as_base_exp()[0])
                exponent = SymPint(expression=self.expression.as_base_exp()[1])
                arg.evaluate()
                exponent.evaluate()
                output = arg**exponent
            else:
                raise ValueError('operation {} not implemented'.format(operator))
            self.valueKnown = output.valueKnown
            self.unit = output.unit
        
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
        #pdb.set_trace()
        return self.override_operator(other,'__pow__')
    
    def override_operator(self,other,operator):
        #pdb.set_trace()
        if not isinstance(other,SymPint):
            #try:
                # other is an expression
             #   other = SymPint(expression=other)
            #except:
                # other is an int or float
                other = SymPint(other)
        try:
            expression = getattr(self.expression,operator)(other.expression)
        except:
            # If above fails, we fall back to sympy's operator
            return getattr(self.symbol,operator)(other)
        
        
        if self.unit is not None and other.unit is not None:
            unit = getattr(self.unit,operator)(other.unit)
        else:
            unit = None
        valueKnown = self.valueKnown and other.valueKnown
        # return unnamed SymPint
        return SymPint(name='\mathrm{unnamed\,expr.}',unit=unit,expression=expression,valueKnown=valueKnown)

    # this function is from Lauritz V. Thaulow's answer on 
    # https://stackoverflow.com/questions/13490292/format-number-using-latex-notation-in-python
    def latex_float(self,f):
        float_str = "{0:.4g}".format(f)
        if "e" in float_str:
            base, exponent = float_str.split("e")
            return "{0} \\times 10^{{{1}}}".format(base, int(exponent))
        else:
            return float_str
    
    def __repr__(self):
        return 'SymPint(name={},expression={},unit={},valueKnown={})'.format(self.name,self.expression,self.unit,self.valueKnown)

    def _repr_latex_(self):
        latex_rep = []
        latex_rep.append('$$')
        latex_rep.append(self.name)
        if self.expressionKnown:
            latex_rep.append('=')
            latex_rep.append(super(type(self.expression), self.expression)._repr_latex_().replace('\\displaystyle ','').replace('$',''))
        latex_rep.append('\\;\\left[')
        if self.valueKnown:
            latex_rep.append('{}\\;'.format(self.latex_float(self.unit.to_base_units().magnitude)))
        if self.unit is None:
            latex_rep.append('\\mathrm{unitless}')
        else:
            if self.unit.dimensionless:
                latex_rep.append('\\mathrm{dimensionless}')
            else:
                latex_rep.append(self.unit.to_base_units().units._repr_latex_().replace('$',''))
        latex_rep.append('\\right]')
        latex_rep.append('$$')
        return ' '.join(latex_rep)
