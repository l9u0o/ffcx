"An algebra for multi-linear forms."

__author__ = "Anders Logg (logg@tti-c.org)"
__date__ = "2004-09-27"
__copyright__ = "Copyright (c) 2004 Anders Logg"
__license__  = "GNU GPL Version 2"

# FFC modules
from finiteelement import FiniteElement
from derivative import Derivative
from transform import Transform
from index import Index

class Element:

    "Base class for elements of the algebra."

    pass

class BasisFunction(Element):

    """A BasisFunction represents a basis function on the reference
    cell and can be either an argument in the multi-linear form or an
    auxiliary basis function that will be removed in the
    contraction.

    A BasisFunction holds the following data:

        element - the corresponding FiniteElement
        index   - the Index of the BasisFunction"""

    def __init__(self, element, index = None):
        "Create BasisFunction."
        if index == None:
            self.element = element
            self.index = Index("primary")
        else:
            self.element = element
            self.index = Index(index)
        return

    def __add__(self, other):
        "Operator: BasisFunction + Element"
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = [Product(self)] + other.products
            return w
        else:
            raise RuntimeError, "Can't add BasisFunction with " + str(other)
        return

    def __sub__(self, other):
        "Operator: BasisFunction - Element"
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = [Product(self), Product(other)]
            w.products[1].constant *= -1.0
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = [Product(self), Product(other)]
            w.products[1].constant *= -1.0
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = [Product(self), Product(other)]
            w.products[1].constant *= -1.0
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = [Product(self)] + other.products
            for i in range(len(other.products) - 1):
                w.products[i + 1].constant *= -1.0                
            return w
        else:
            raise RuntimeError, "Can't subtract BasisFunction with " + str(other)
        return

    def __mul__(self, other):
        "Operator: BasisFunction * Element"
        if isinstance(other, BasisFunction):
            w = Product()
            w.factors = [Factor(self), Factor(other)]
            return w
        elif isinstance(other, Factor):
            w = Product()
            w.factors = [Factor(self), Factor(other)]
            return w
        elif isinstance(other, Product):
            w = Product()
            w.factors = [Factor(self)] + other.factors
            return w
        elif isinstance(other, Sum):
            w = Sum()
            for p in other.products:
                w.products += [self*p]
            return w
        else:
            raise RuntimeError, "Can't multiply BasisFunction with " + str(other)
        return

    def dx(self, index = None):
        "Operator: (d/dx)BasisFunction in given coordinate direction."
        i = Index() # Create new secondary index
        w = Factor(self)
        w.derivatives = [Derivative(i)]
        w.transforms = [Transform(i, index)]
        return w

    def __repr__(self):
        "Print nicely formatted representation of BasisFunction."
        if self.index.type == "primary":
            return "v" + str(self.index)
        else:
            return "w" + str(self.index)
        
class Factor(Element):

    """A Factor represents a (possibly) differentiated BasisFunction
    on the reference cell.

    A Factor holds the following data:

        basisfunction - the BasisFunction of the Factor
        derivatives   - a list of Derivatives applied to the BasisFunction
        transforms    - a list of corresponding Transforms"""
    
    def __init__(self, other = None):
        "Create Factor."
        if other == None:
            self.basisfunction = None
            self.derivatives = []
            self.transforms = []
        elif isinstance(other, BasisFunction):
            self.basisfunction = other
            self.derivatives = []
            self.transforms = []
        elif  isinstance(other, Factor):
            self.basisfunction = other.basisfunction
            self.derivatives = [] + other.derivatives
            self.transforms = [] + other.transforms
        else:
            raise RuntimeError, "Unable to create Factor from " + str(other)
        return

    def __add__(self, other):
        "Operator: Factor + Element"
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = [Product(self)] + other.products
            return w
        else:
            raise RuntimeError, "Can't add Factor with " + str(other)
        return

    def __sub__(self, other):
        "Operator: Factor - Element"
        # FIXME: remember to modify geometry tensor with a -
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = [Product(self)] + other.products
            return w
        else:
            raise RuntimeError, "Can't add Factor with " + str(other)
        return
    
    def __mul__(self, other):
        "Operator: Factor * Element"
        if isinstance(other, BasisFunction):
            w = Product()
            w.factors = [Factor(self), Factor(other)]
            return w
        elif isinstance(other, Factor):
            w = Product()
            w.factors = [Factor(self), Factor(other)]
            return w
        elif isinstance(other, Product):
            w = Product()
            w.factors = [Factor(self)] + other.factors
            return w
        elif isinstance(other, Sum):
            w = Sum()
            for p in other.products:
                w.products += [self*p]
            return w
        else:
            raise RuntimeError, "Can't multiply Factor with " + str(other)
        return

    def dx(self, index = None):
        "Operator: (d/dx)Factor in given coordinate direction."
        i = Index() # Create new secondary index
        w = Factor(self)
        w.derivatives = [Derivative(i)] + w.derivatives
        w.transforms = [Transform(i, index)] + w.derivatives
        return w

    def max_indices(self):
        """Compute the maximum indices [i0, i1] used by the Factor.
        If an index is not used, -1 is returned for that index."""
        
        i0 = -1
        i1 = -1
        if self.basisfunction.index.type == "primary":
            i0 = max(i0, self.basisfunction.index.index)
        elif self.basisfunction.index.type == "secondary":
            i1 = max(i1, self.basisfunction.index.index)
        for d in self.derivatives:
            if d.index.type == "primary":
                i0 = max(i0, d.index.index)
            elif d.index.type == "secondary":
                i1 = max(i1, d.index.index)
        return [i0, i1]
        
    def __repr__(self):
        "Print nicely formatted representation of Factor."
        output = ""
        if len(self.derivatives) > 0:
            output += "("
            for d in self.derivatives:
                output += d.__repr__()
            output += self.basisfunction.__repr__()
            output += ")"
        else:
            output += self.basisfunction.__repr__()
        return output
    
class Product(Element):

    """A Product represents a product of Factors. Note that the list of
    Transforms of each Factor contained in a Product should be
    empty. When multiplying Factors to obtain a Product, the
    Transforms of all Factors will be collected in to a single list.

    A Product holds the following data:

        factors      - a list of Factors in the Product
        transforms   - a list of Transforms for all Factors
        coefficients - a list of Coefficients in the Product
        constant     - a constant contained in the Product"""

    def __init__(self, other = None):
        "Create Product."
        if other == None:
            self.factors = []
            self.transforms = []
            self.coefficients = []
            self.constant = 1.0
        elif isinstance(other, BasisFunction):
            self.factors = [Factor(other)]
            self.transforms = []
            self.coefficients = []
            self.constant = 1.0
        elif isinstance(other, Factor):
            self.factors = [other]
            self.transforms = []
            self.coefficients = []
            self.constant = 1.0
        elif isinstance(other, Product):
            self.factors = [] + other.factors
            self.transforms = [] + other.transforms
            self.coefficients = [] + other.coefficients
            self.constant = other.constant
        else:
            raise RuntimeError, "Unable to create Product from " + str(other)
        return
    
    def __add__(self, other):
        "Operator: Product + Element"
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = [Product(self)] + other.products
            return w
        else:
            raise RuntimeError, "Can't add Product with " + str(other)
        return

    def __sub__(self, other):
        "Operator: Product - Element"
        # FIXME: remember to modify geometry tensor with a -
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = [Product(self), Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = [Product(self)] + other.products
            return w
        else:
            raise RuntimeError, "Can't subtract Product with " + str(other)
        return
    
    def __mul__(self, other):
        "Operator: Product * Element"
        if isinstance(other, BasisFunction):
            w = Product()
            w.factors = self.factors + [Factor(other)]
            return w
        elif isinstance(other, Factor):
            w = Product()
            w.factors = self.factors + [Factor(other)]
            return w
        elif isinstance(other, Product):
            w = Product()
            w.factors = self.factors + other.factors
            return w
        elif isinstance(other, Sum):
            w = Sum()
            for p in other.products:
                w.products += [self*p]
            return w
        else:
            raise RuntimeError, "Can't multiply Product with " + str(other)
        return

    def dx(self, index = None):
        "Operator: (d/dx)Product in given coordinate direction."
        w = Sum()
        for i in range(len(self.factors)):
            p = Product()
            for j in range(len(self.factors)):
                if i == j:
                    p.factors += [self.factors[i].dx(index)]
                else:
                    p.factors += [self.factors[j]]
            w.products += [p]
        return w

    def rank(self):
        "Return rank [r0, r1] of tensor represented by the Product."
        i0 = -1
        i1 = -1
        for f in self.factors:
            [tmp0, tmp1] = f.max_indices()
            i0 = max(i0, tmp0)
            i1 = max(i1, tmp1)
        return [i0 + 1, i1 + 1]

    def dims(self, r0, r1):
        """Return dimensions for the tensor represented by the
        Product. This method involves some searching, but it
        shouldn't take too much time."""
        dimlist = []
        # First check dimensions for primary indices
        for i in range(r0):
            (dim, found) = self.primary_dim(i)
            if found:
                dimlist = dimlist + [dim]
            else:
                raise RuntimeError, "Unable to find primary index " + str(i)
        # Then check dimensions for secondary indices
        for i in range(r1):
            (dim, found) = self.secondary_dim(i)
            if found:
                dimlist = dimlist + [dim]
            else:
                raise RuntimeError, "Unable to find secondary index " + str(i)
        return dimlist

    def primary_dim(self, i):
        """Try to find primary dimension number i. If found, the
        dimension is returned as (dim, True). Otherwise (0, False) is
        returned."""
        for f in self.factors:
            # First check BasisFunction
            if f.basisfunction.index.type == "primary":
                if f.basisfunction.index.index == i:
                    return (f.basisfunction.element.spacedim, True)
            # Then check Derivatives
            for d in f.derivatives:
                if d.index.type == "primary":
                    if d.index.index == i:
                        return (f.basisfunction.element.shapedim, True)
        return (0, False)

    def secondary_dim(self, i):
        """Try to find secondary dimension number i. If found, the
        dimension is returned as (dim, True). Otherwise (0, False) is
        returned."""
        for f in self.factors:
            # First check BasisFunction
            if f.basisfunction.index.type == "secondary":
                if f.basisfunction.index.index == i:
                    return (f.basisfunction.element.spacedim, True)
            # Then check Derivatives
            for d in f.derivatives:
                if d.index.type == "secondary":
                    if d.index.index == i:
                        return (f.basisfunction.element.shapedim, True)
        return (0, False)
    
    def __repr__(self):
        "Print nicely formatted representation of Product."
        output = ""
        for i in range(len(self.factors)):
            if i < (len(self.factors) - 1):
                output += (self.factors[i].__repr__() + "*")
            else:
                output += self.factors[i].__repr__()
        return output

class Sum(Element):

    """A Sum represents a sum of Products. Each Product will be
    compiled separately, since different Products are probably of
    different rank.

    A Sum holds the following data:

        products - a list of Products (terms) in the Sum"""
    
    def __init__(self, other = None):
        "Create Sum."
        if other == None:
            self.products = []
        elif isinstance(other, BasisFunction):
            self.products = [Product(other)]
        elif isinstance(other, Factor):
            self.products = [Product(other)]
        elif isinstance(other, Product):
            self.products = [Product(other)]
        elif isinstance(other, Sum):
            self.products = [] + other.products
        else:
            raise RuntimeError, "Unable to create Sum from " + str(other)
        return

    def __add__(self, other):
        "Operator: Sum + Element"
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = self.products + [Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = self.products + [Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = self.products + [Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = self.products + other.products
            return w
        else:
            raise RuntimeError, "Can't add Sum with " + str(other)
        return

    def __sub__(self, other):
        "Operator: Sum - Element"
        # FIXME: remember to modify geometry tensor with a -
        if isinstance(other, BasisFunction):
            w = Sum()
            w.products = self.products + [Product(other)]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            w.products = self.products + [Product(other)]
            return w
        elif isinstance(other, Product):
            w = Sum()
            w.products = self.products + [Product(other)]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            w.products = self.products + other.products
            return w
        else:
            raise RuntimeError, "Can't add Sum with " + str(other)
        return
    
    def __mul__(self, other):
        "Operator: Sum * Element"
        if isinstance(other, BasisFunction):
            w = Sum()
            for p in self.products:
                w.products += [p*other]
            return w
        elif isinstance(other, Factor):
            w = Sum()
            for p in self.products:
                w.products += [p*other]
            return w
        elif isinstance(other, Product):
            w = Sum()
            for p in self.products:
                w.products += [p*other]
            return w
        elif isinstance(other, Sum):
            w = Sum()
            for p in self.products:
                for q in other.products:
                    w.products += [p*q]
            return w
        else:
            raise RuntimeError, "Can't multiply Sum with " + str(other)
        return

    def dx(self, index = None):
        "Operator: (d/dx)Sum in given coordinate direction."
        w = Sum()
        for p in self.products:
            w += p.dx(index)
        return w

    def __repr__(self):
        "Print nicely formatted representation of Sum."
        output = ""
        for i in range(len(self.products)):
            if i < (len(self.products) - 1):
                output += (self.products[i].__repr__() + " + ")
            else:
                output += self.products[i].__repr__()
        return output

if __name__ == "__main__":

    print "Testing algebra"
    print "---------------"

    element = FiniteElement("Lagrange", 1, "triangle")

    u = BasisFunction(element)
    v = BasisFunction(element)

    print "Testing long expression:"
    w = (((u*(u*v + u)*u + u*v)*u.dx(0)).dx(2)).dx(1)
    print w

    print

    print "Testing derivative of product:"
    w = (u*v*u).dx(0)
    print w

    print

    print "Testing derivative of sum:"
    w = (u + v).dx(0)
    print w

    print
    
    print "Testing Poisson:"
    i = Index()
    w = u.dx(i)*v.dx(i)
    print w

    print

    print "Testing Biharmonic:"
    i = Index()
    j = Index()
    w = u.dx(i).dx(i)*v.dx(j).dx(j)
    print w
