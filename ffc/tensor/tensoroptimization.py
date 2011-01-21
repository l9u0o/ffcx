__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2010-02-08"
__copyright__ = "Copyright (C) 2010 " + __author__
__license__  = "GNU GPL version 3 or any later version"

# Python modules
from numpy import shape

# FFC modules
from ffc.log import warning, info, error
from ffc.utils import product

# Try importing FErari
try:
    import ferari
    from ferari import binary
except:
    ferari = None

def optimize_integral_ir(ir, parameters):
    """
    Compute optimized intermediate representation of integral.

    Note that this function modifies the given intermediate
    representation directly, rather than working on a copy.
    """

    # Skip optimization if FErari is not installed
    if ferari is None:
        warning("FErari not installed, skipping tensor optimizations")
        return ir

    # Skip optimization if requested
    if "no_ferari" in parameters:
        warning("Skipping FErari optimizations as requested.")
        return ir

    # Extract data from intermediate representation
    AK = ir["AK"]
    domain_type = ir["domain_type"]
    num_facets = ir["num_facets"]
    rank = ir["rank"]

    # Optimize cell integrals
    if domain_type == "cell":
        for (k, (A0, GK, dummy)) in enumerate(AK):
            ir["AK"][k] = (A0, GK, _optimize_tensor_contraction(A0.A0, rank))

    # Optimize exterior facet integrals
    elif domain_type == "exterior_facet":
        for i in range(num_facets):
            for (k, (A0, GK, dummy)) in enumerate(AK[i]):
                ir["AK"][i][k] = (A0, GK, _optimize_tensor_contraction(A0.A0, rank))

    # Optimize interior facet integrals
    elif domain_type == "interior_facet":
        for i in range(num_facets):
            for j in range(num_facets):
                for (k, (A0, GK, dummy)) in enumerate(AK[i][j]):
                    ir["AK"][i][j][k] = (A0, GK, _optimize_tensor_contraction(A0.A0, rank))

    # Unhandled integral type
    else:
        error("Unhandled integral type: " + str(domain_type))

    return ir

def _optimize_tensor_contraction(A0, rank):
    "Compute optimized tensor contraction for given reference tensor."

    # Select FErari optimization algorithm
    if rank == 2:
        optimize = binary.optimize
    elif rank == 1:
        optimize = binary.optimize_action
    else:
        warning("Tensor optimization only available for rank 1 and 2 tensors, skipping optimizations")
        return None

    # Write a message
    info("Calling FErari to optimize tensor of size %s (%d entries)",
         " x ".join(str(d) for d in shape(A0)), product(shape(A0)))#

    # Compute optimized tensor contraction
    return optimize(A0)