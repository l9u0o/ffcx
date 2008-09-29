__author__ = "Marie Rognes (meg@math.uio.no)"
__date__ = "2006-10-23 -- 2007-10-30"
__copyright__ = "Copyright (C) 2006"
__license__  = "GNU GPL version 3 or any later version"

# Modified by Anders Logg 2007
# Modified by Kristian Oelgaard 2007

# Python modules
import sys
from sets import Set

# FFC common modules
from ffc.common.debug import *
from ffc.common.exceptions import *

# FFC compiler.language modules
from ffc.compiler.language.index import *
from ffc.compiler.language.algebra import *
from ffc.compiler.language.tokens import *
from ffc.compiler.language.integral import *

def simplify(form):
    """ Simplification of a form"""

    if not isinstance(form, Form):
        raise FormError, (form, "simplify assumes a Form as input.")

    debug("Simplifying form...")
    # Handle restrictions on exterior facets before simplifying
    #restriction_exterior(form)

    # Change constant restrictions on interior facets before simplifying
    change_constant_restrictions(form)

    # Simplify form by contracting indices and simplifying derivatives
    simplify_form(form)

    reassign_indices(form)

    debug("done")

def simplify_form(f):
    """ Take a Form f and contract indices, factorize, remove zero
    monomials, contract determinants and simplify derivatives. """
    
    # Contract indices. Note that we have to contract all indices
    # before we continue!
    previous = str(f)
    simplified = ""

    while(previous != simplified):
        reassign_indices(f)
        previous = str(f)
        f.monomials = contract_list(contract_monomials, f.monomials)
        simplified = str(f)

    # Factorize monomials
    f.monomials = contract_list(factorize_monomials, f.monomials)

    # Note that we iterate through a copy of the list since we want to
    # remove things from it while iterating.
    for monomial in f.monomials[:]:
        # Remove monomials with numeric = 0.0:
        if monomial.numeric == 0.0:
            f.monomials.remove(monomial)
            continue
        # Contract determinants:
        if monomial.determinants:
            monomial.determinants = contract_list(contract_determinants,
                                                  monomial.determinants)
        # Simplify each monomial with regard to derivatives.
        simplify_monomial(monomial)
        
def contract_list(contraction, monomials):
    """ Given a list of ..., run contraction on (all) pairs of these,
    and return the new list. contraction should return a tuple
    (result, contracted) where result is a list containing either the
    contracted result or the original input.""" 
    # meg: Again, please replace this if there is an easier/prettier
    # way of doing this.
    if len(monomials) < 2:
        return monomials 
    current = listcopy(monomials)
    i = 0
    while i < len(current):
        j = i+1
        while j < len(current):
            (q, contracted) = contraction(current[i], current[j])
            if contracted:
                current.remove(current[j])
                current[i] = q[0]      # (Note that j > i.)
            else:
                j +=1
        i += 1
    return current

def factorize_monomials(m, n):
    """ Given a two monomials, factorize any common factors and return
    the new monomials."""
    # meg: Not quite finished yet. Does very simple factorization now.
    mcopy = Monomial(m)
    ncopy = Monomial(n)
    mcopy.numeric = 1.0
    ncopy.numeric = 1.0
    if str(mcopy) == str(ncopy) and same_index_ranges(m, n):
        mcopy.numeric = m.numeric + n.numeric
        return([mcopy], True)
    return ([m, n], False)
    
def contract_monomials(m, n):
    if not (isinstance(m, Monomial) and isinstance(n, Monomial)):
        raise FormError, ((m, n), "contract_monomials can only contract monomials")
    # First, check to see if it is at all likely that these monomials
    # are contractable
    if not contraction_likely(m, n):
        return ([m, n], False)
    q = contract_indices(m, n)
    return (q, len(q) == 1)

def contract_determinants(d0, d1):
    if not (isinstance(d0, Determinant) and isinstance(d1, Determinant)):
        raise FormError, ((d0, d1), "contract_determinants can only contract determinants!")
    # Determinants are contracted by trying to multiply them:
    d = d0*d1
    if d: return ([d], True)
    else: return ([d0, d1], False)

def contraction_likely(m, n):
    """ Given two monomials/basisfunctions, check if they have the
    same numbers of basisfunctions, transforms, derivatives,
    components etc. (This is just intended as a preliminary check.)"""
    # Comparing monomials:
    if isinstance(m, Monomial) and isinstance(n, Monomial):
        if m.integral != n.integral:
            return False

        if m.numeric != n.numeric:
            return False

        if len(m.determinants) != len(n.determinants):
            return False
        for i in range (len(m.determinants)):
            if not m.determinants[i] == n.determinants[i]:
                return False

        if len(m.coefficients) != len(n.coefficients):
            return False
        for i in range(len(m.coefficients)):
            if not contraction_likely(m.coefficients[i], n.coefficients[i]):
                return False

        if len(m.transforms) != len(n.transforms):
            return False
        for i in range(len(m.transforms)):
            if not contraction_likely(m.transforms[i], n.transforms[i]):
                return False

        if len(m.basisfunctions) != len(n.basisfunctions):
            return False
        for i in range(len(m.basisfunctions)):
            if not contraction_likely(m.basisfunctions[i],
                                      n.basisfunctions[i]):
                return False
        return True

    # Comparing basis functions:
    elif isinstance(m, BasisFunction) and isinstance(n, BasisFunction):
        if m.element != n.element:
            return False
        if m.index != n.index:
            return False
        if m.restriction != n.restriction:
            return False
        if len(m.component) != len(n.component):
            return False
        if len(m.derivatives) != len(n.derivatives):
            return False
        return True

    # Comparing transforms:
    elif isinstance(m, Transform) and isinstance(n, Transform):
        if m.type != n.type or m.restriction != n.restriction:
            return False
        return True

    # Comparing coefficients:
    elif isinstance(m, Coefficient) and isinstance(n, Coefficient):
        if m.n0 != n.n0:
            return False
        if m.n1 != n.n1:
            return False
        return True

    # Others, not implemented
    else:
        return True
            
def contract_indices(m, n):
    """ Given two monomials, contract indices in the following way: If
    m and n only differ by one index, contract and replace this index."""
    indices = [{}, {}]

    # Extract the differences between the monomials
    differences = abbreviate(diff(m, n))

    # Extract the different index values:
    for attribute in differences:
        for [mv, nv] in differences[attribute]:
            # Each key/label in mv is also in nv by construction.
            for label in mv:  
                if indices[0].has_key(str(mv[label])):
                    indices[0][str(mv[label])] += [(label, mv[label])]
                else:
                    indices[0][str(mv[label])] = [(label, mv[label])]
                if indices[1].has_key(str(nv[label])):
                    indices[1][str(nv[label])] += [(label, nv[label])]
                else:
                    indices[1][str(nv[label])] = [(label, nv[label])]

    # We can contract the indices and thus the monomials, if there is
    # only a difference of one index and if there are at least two
    # occurances of this index. (Summation over _repeated_ indices.)
    if len(indices[0].keys()) == len(indices[1].keys()) == 1 \
           and len(indices[0].values()[0]) == 2:
        # Constructing the new index:
        i0 = indices[0].values()[0][0][1]
        i1 = indices[1].values()[0][0][1]

        # We only want to contract if each index value occurs once.
        common_indices = Set(i0.range) & Set(i1.range)
        if not common_indices:
            # Constucting the new monomial based on the old m:
            index = Index(i0) + Index(i1)
            q = Monomial(m)
            for (label, i) in indices[0][str(i0)]:
                s = "q.%s = index" % str(label)
                exec(s)
            return [q]

    return [m, n]

def simplify_monomial(monomial):
    """ Simpliy monomials with construction of the form:
    (dx_j/dX_i)(dX_l/dx_j) | (d/dX_l) => (d/dX_i)"""
    
    for basis in monomial.basisfunctions:
        success = 0
        first = None
        second = None
        
        # The derivatives of this basis function is a good
        # starting point so we run through these. We use index
        # notation since we may have to replace some of them.
        for i in range(len(basis.derivatives)):
            derivative = basis.derivatives[i]
            therestriction = basis.restriction
            success = 0
            theindex = derivative.index
            if theindex.type == Index.FIXED: break
            # Now, lets run through the transforms and see whether
            # there are two matching:
            for transform in monomial.transforms:
                if transform.type == Transform.JINV:
                    if (not cmp(transform.index0, theindex)
                        and transform.restriction == therestriction):
                        if not transform.index1.type == Index.FIXED:
                            first = transform
                            break
            # If there are no matching JINV-transforms, no hope of success.
            if not first: break

            for transform in monomial.transforms:
                if transform.type == Transform.J:
                    if (not cmp(transform.index1, first.index1)
                        and transform.restriction == therestriction):
                        if not transform.index0.type == Index.FIXED:
                            second = transform
                            success = 1
                            break

            if success == 1:
                # Now, we should first remove the transforms from
                # the transform list. Second: replace the old
                # derivative with the new one.
                basis.derivatives[i] = Derivative(derivative.element,
                                                  second.index0)
                monomial.transforms.remove(first) 
                monomial.transforms.remove(second)

def diff(m, n, key = None):
    """ Take two elements and returns the difference between these in
    an appropriate manner.""" 

    # Dictionaries containing each version when m and n are different
    mversion = {}
    nversion = {}

    if isinstance(m, list) and isinstance(n, list):
        #The difference of two lists (of equal length!)
        diffs = []
        if len(m) == len(n):
            for i in range(len(m)):
                difference = diff(m[i], n[i], key[i])
                if not is_empty(difference):
                    diffs += [difference]
            return diffs
        else:
            raise FormError("Only know how to diff lists of equal length.")
        
    elif isinstance(m, Monomial) and isinstance(n, Monomial):
        # The difference between two monomials
        coeffids = ["coefficients[%d]" % i for i in range(len(m.coefficients))]
        coeffdiff = diff(m.coefficients, n.coefficients, coeffids)
        tids = ["transforms[%d]" % i for i in range(len(m.transforms))]
        tdiff = diff(m.transforms, n.transforms, tids)
        dictionary = {'coefficients': coeffdiff, 'transforms': tdiff}

        # Treat the basis functions items separately:
        bids = ["basisfunctions[%d]." % i
                for i in range(len(m.basisfunctions))]
        bdiff = diff(m.basisfunctions, n.basisfunctions, bids)
        for dict in bdiff:
            for key in dict:
                if dictionary.has_key(key):
                    dictionary[key] += dict[key]
                else:
                    dictionary[key] = dict[key]
        return abbreviate(dictionary)
        
    elif isinstance(m, BasisFunction) and isinstance(n, BasisFunction):
        # The difference between two basis functions
        idiff = diff(m.index, n.index, key + "index")
        cids = [key + "component[%d]" % i for i in range(len(m.component))]
        cdiff = diff(m.component, n.component, cids)
        dids = [key + "derivatives[%d]" % i for i in range(len(m.derivatives))]
        ddiff = diff(m.derivatives, n.derivatives, dids)
        return abbreviate({'index': idiff, 'component': cdiff,
                           'derivatives': ddiff})

    elif isinstance(m, Index) and isinstance(n, Index):
        # The difference between two indices. Note that we have to be
        # careful about the comparison here, since we in this case do
        # not want a0 == a0+2 for instance.
        if not str(m) == str(n):
            mversion[key] = m
            nversion[key] = n

    elif isinstance(m, Transform) and isinstance(n, Transform):
        # The index difference between two transforms
        if not m.index0 == n.index0:
            mversion[key + ".index0"] = m.index0
            nversion[key + ".index0"] = n.index0
        if not m.index1 == n.index1:
            mversion[key + ".index1"] = m.index1
            nversion[key + ".index1"] = n.index1
        
    elif isinstance(m, Derivative) and isinstance(n, Derivative):
        # The index difference between two derivatives:
        if not m.index == n.index:
            mversion[key + ".index"] = m.index
            nversion[key + ".index"] = n.index

    elif isinstance(m, Coefficient) and isinstance(n, Coefficient):
        # The index difference between two coefficients
        if not m.index == n.index:
            mversion[key + ".index"] = m.index
            nversion[key + ".index"] = n.index
        
    else:
        raise FormError, ((m, n), "Diff is not implemented between such elements")

    if mversion:
        return [mversion, nversion]
    else:
        return []

# def restriction_exterior(form):
#     """Removing restrictions on exterior facets.
#        If this makes monomial terms equal, all but one monomial term will be deleted."""

#     # List of numbers of monomials with removed restrictions on exterior facets
#     removed_restrictions = []
#     for i in range(len(form.monomials)):
#         p = form.monomials[i]
#         for v in p.basisfunctions:
#             type = p.integral.type
#             if type == Integral.EXTERIOR_FACET:
#                 if not (v.restriction == None or v.restriction == Restriction.CONSTANT):
#                     # Remove restriction and keep track of the monomial number
#                     v.restriction = None
#                     removed_restrictions += [i]

#     # Create a set of the removed restrictions, (remove duplicate numbers) and get monomials
#     removed_restrictions = tuple(set(removed_restrictions))
#     monomials = [form.monomials[r] for r in removed_restrictions]

#     # If any restrictions were moved
#     if monomials:
#         # The first monomial is always unique
#         unique = [monomials[0]]
#         for i in range(1,len(monomials)):
#             p = monomials[i]
#             equals = False
#             # Check if monomial already exists
#             for p0 in unique:
#                 if contraction_likely(p,p0):
#                     if not diff(p,p0):
#                         # If there are no differences the monmials are equal
#                         equals = True

#             # If monomial is redundant, remove it. Otherwise add it to the list of uniuqe monomials
#             if equals:
#                 form.monomials.remove(p)
#             else:
#                 unique += [p]

# meg: FIXME: Needs revisiting:

def same_index_ranges(m, n):
    """Two monomials can have the same string representation while the
    index ranges for the basis functions differ. Thus, take two
    monomials, check whether they have the same index ranges."""
    # First check that the two monomials have the same string
    # representation:
    mcopy = Monomial(m)
    ncopy = Monomial(n)
    mcopy.numeric = 1.0
    ncopy.numeric = 1.0
    if str(mcopy) != str(ncopy):
        return False
    # Then go through the basis functions and their component indices
    # and check whether the ranges are really the same.
    for i in range(len(m.basisfunctions)):
        m_component = m.basisfunctions[i].component
        n_component = n.basisfunctions[i].component
        for j in range(len(m_component)):
            if (m_component[j].range != n_component[j].range):
                return False
    return True

def change_constant_restrictions(form):
    """Change Restriction.CONSTANT to Restriction.PLUS on interior facets"""

    for m in form.monomials:
        if m.integral.type == Integral.INTERIOR_FACET:
            for v in m.basisfunctions:
                if v.restriction == Restriction.CONSTANT:
                    v.restriction = Restriction.PLUS