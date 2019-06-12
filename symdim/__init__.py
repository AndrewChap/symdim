import sympy
from astropy import units as u

# Class that inherits from sympy.Symbol but also gets the 'parent' attribute so we can find the SymDim instance from the symbol
class Symbol(sympy.Symbol):
    def __init__(self,name,nonnegative=True,parent=None):
        super().__new__(name=name,nonnegative=nonnegative,real=True,cls=sympy.Symbol) # call sympy.symbol __new__ method
        self.parent = parent # assign parent
        
class SymDim:
    def __init__(self,
                 name=None,
                 unit=None,
                 value=None,
                 expression=None,
                 valueKnown=False,
                 equals=None,
                 nonnegative=True,
                ):
        
        
        if isinstance(name,str):
            # e.g. SymDim('a')
            self.name = name
            self.symbol = Symbol(self.name,nonnegative=nonnegative,parent=self)
        else:
            # e.g. SymDim(4) or SymDim(expression=a*b)
            self.name = '\mathrm{unnamed\,expr.}'
            try:
                self.symbol = sympy.Number(name)
                self.unit = u.dimensionless_unscaled
            except:
                self.symbol = None
            if isinstance(name,int) or isinstance(name,float):
                value = name
                unit = u.dimensionless_unscaled
            
        
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
            self.unit = u.dimensionless_unscaled
        else:
            self.unit = None
    
    # Value is only used as an input variable
    def set_value(self,value,valueKnown=True):
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
        #pdb.set_trace()
        if self.unit is None:
            self.unit = other.unit
        if other.unit is not None and self.unit.decompose() != other.unit.decompose():
            # known issue, sometimes pint will not recognize equivalent units,
            # which is why we don't raise an error here
            print('Warning: units of {} and {} do not match'.format(self,other))
            self.unit = other.unit
        other_expression = other.get_expression()
        while isinstance(other_expression,SymDim):
            other_expression = other_expression.expression
        self.set_expression(other_expression)
        
        self.expressionKnown = True
        if self.valueKnown is False:
            self.valueKnown = other.valueKnown
        
    # currently just returns the first expression in the list.  If you wanted
    # to return multiple solutions, remove the [0] and iterate through them.
    def solve_for(self,other):
        # for example, if we want to solve z=x*y for y, we would call:
        # >>> y = z.solve_for(y)
        # and our inputs in this function would be:
        #    self = SymDim(name='z',expression=x*y)
        #    other = SymDim(name='y',expression=y)

        # create an equation, e.g. sympy.Eq(z,x*y)
        eq = sympy.Eq(self.symbol,self.expression)
        # solve the equation for other, e.g. sympy.solve(z=x*y,y), which returns z/x
        expressions = sympy.solve(eq,other.expression)
        # Create a new SymDim with name of what we are solving for equal to expression
        
        outputs = [SymDim(name=other.name,expression=expression) for expression in expressions if sympy.I not in expression.atoms()]
        # Evaluate the expression to get units
        [output.evaluate() for output in outputs]
        return outputs
    
    def simplify_expression(self):
        self.set_expression(sympy.simplify(self.expression))
        
    def evaluate(self):
        # if our expression is a Symbol, set our SymDim's values to the Symbol's parent's values
        if isinstance(self.expression,Symbol):
            self.symbol = self.expression.parent.symbol
            self.valueKnown = self.expression.parent.valueKnown
            self.unit = self.expression.parent.unit
        elif isinstance(self.expression,SymDim):
            self.valueKnown = self.expression.valueKnown
            self.unit = self.expression.unit
        elif isinstance(self.expression,sympy.Number):
            self.valueKnown = True
            self.unit = float(self.expression)*u.dimensionless_unscaled
        else:
            if self.expression.is_Mul or self.expression.is_Add:
                for i,arg_sympy in enumerate(self.expression.args):
                    arg = SymDim(expression=arg_sympy)
                    arg.evaluate()                    
                    if i == 0:
                        output = arg
                    else:
                        if self.expression.is_Mul:
                            output = output*arg
                        elif self.expression.is_Add:
                            output = output + arg
            elif self.expression.is_Pow:
                arg = SymDim(expression=self.expression.as_base_exp()[0])
                exponent = SymDim(expression=self.expression.as_base_exp()[1])
                arg.evaluate()
                exponent.evaluate()
                output = arg**exponent
            else:
                raise ValueError('expression {} not implemented'.format(self.expression))
            self.valueKnown = output.valueKnown
            self.unit = output.unit
        
    def substitute(self,takeOut,putIn):
        self.set_expression(self.expression.subs(takeOut.symbol,putIn.symbol))
        
    def simplify(self):
        self.expression = self.expression.simplify()
        
    def derivative(self,diff):
        derivative = sympy.diff(self.expression,diff.symbol)
        result = SymDim(expression=derivative)
        result.evaluate()
        return result
        
    # definite or indefinite integral
    def integrate(self,diff,lo=None,hi=None):
        if lo is None and hi is None:
            integrand = sympy.integrate(self.expression,diff.symbol)
            result = SymDim(expression=integrand)
            result.evaluate()
            return result
        elif lo is not None and hi is not None:
            if not isinstance(lo,SymDim):
                if lo == 0:
                    lo = SymDim(0)
                else:
                    if diff.unit.unit == u.dimensionless_unscaled:
                        name = diff.name+'_\\mathrm{lo}='+self.latex_float(lo)
                    else:
                        name = '\\left['+diff.name+'_\\mathrm{lo}='+self.latex_float(lo)+'\\,'+diff.unit.decompose().unit._repr_latex_().replace('$','')+'\\right]'
                    lo = SymDim(name=name,unit=diff.unit.unit,value=lo)
            if not isinstance(hi,SymDim):
                if hi == 0:
                    hi = SymDim(0)
                else:
                    if diff.unit.unit == u.dimensionless_unscaled:
                        name = diff.name+'_\\mathrm{hi}='+self.latex_float(hi)
                    else:
                        name = '\\left['+diff.name+'_\\mathrm{hi}='+self.latex_float(hi)+'\\,'+diff.unit.decompose().unit._repr_latex_().replace('$','')+'\\right]'
                    hi = SymDim(name=name,unit=diff.unit.unit,value=hi)
                #hi = sympy.Number(hi)
            integrand_hi = self.integrate(diff)
            integrand_hi.substitute(diff,hi)
            #integrand_hi.plug_in_value(hi) # not yet correctly implemented with units
            integrand_lo = self.integrate(diff)
            integrand_lo.substitute(diff,lo)
            #integrand_lo.plug_in_value(lo) # not yet correctly implemented with units
            
            result = integrand_hi - integrand_lo
            result.simplify_expression()
            result.evaluate()
            return result
        else:
            raise ValueError('integral input must have either no bounds or both bounds specified')
        
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
        if not isinstance(other,SymDim):
            #try:
                # other is an expression
             #   other = SymDim(expression=other)
            #except:
                # other is an int or float
                other = SymDim(other)
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
        # return unnamed SymDim
        return SymDim(name='\mathrm{unnamed\,expr.}',unit=unit,expression=expression,valueKnown=valueKnown)

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
        return 'SymDim(name={},expression={},unit={},valueKnown={})'.format(self.name,self.expression,self.unit,self.valueKnown)

    def _repr_latex_(self):
        latex_rep = []
        latex_rep.append('$$')
        latex_rep.append(self.name)
        if self.expressionKnown:
            latex_rep.append('=')
            latex_rep.append(super(type(self.expression), self.expression)._repr_latex_().replace('\\displaystyle ','').replace('$',''))
        latex_rep.append('\\;\\left[')
        if self.valueKnown:
            latex_rep.append('{}\\;'.format(self.latex_float(self.unit.decompose().value)))
        if self.unit is None:
            latex_rep.append('\\mathrm{unitless}')
        else:
            if self.unit == u.dimensionless_unscaled:
                latex_rep.append('\\mathrm{dimensionless}')
            else:
                latex_rep.append(self.unit.decompose().unit._repr_latex_().replace('$',''))
        latex_rep.append('\\right]')
        latex_rep.append('$$')
        return ' '.join(latex_rep)
