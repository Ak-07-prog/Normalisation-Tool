import re
import itertools

def parse_relation(input_str: str):
    """
    Parses a relation string like "R(A, B, C)" into name and attributes.
    Returns (relation_name, set_of_attributes).
    """
    input_str = input_str.strip()
    match = re.search(r"(\w+)\s*\((.+)\)", input_str)
    if not match:
        # Fallback: maybe just "A, B, C" was entered?
        if "(" not in input_str and ")" not in input_str:
             parts = [p.strip() for p in input_str.split(",") if p.strip()]
             if parts:
                 return "R", set(parts)
        # Try to handle "RelationName: A, B, C"
        if ":" in input_str:
            name, attrs = input_str.split(":", 1)
            return name.strip(), set(a.strip() for a in attrs.split(","))

        raise ValueError("Invalid relation format. Expected 'Name(Attr1, Attr2, ...)'")
    
    name = match.group(1)
    attrs_str = match.group(2)
    attributes = set(attr.strip() for attr in attrs_str.split(","))
    return name, attributes

def parse_fds(fd_str: str):
    """
    Parses a multi-line string of FDs like "A -> B, C".
    Returns a list of (lhs_set, rhs_set) tuples.
    """
    fds = []
    lines = fd_str.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Handle "A -> B" and "A → B"
        arrow = "->"
        if "→" in line:
            arrow = "→"
            
        if arrow in line:
            lhs_str, rhs_str = line.split(arrow)
            lhs = set(attr.strip() for attr in lhs_str.split(","))
            rhs = set(attr.strip() for attr in rhs_str.split(","))
            fds.append((lhs, rhs))
    return fds

def attribute_closure(attributes: set, fds: list):
    """
    Computes the closure of a set of attributes under the given FDs.
    """
    closure = attributes.copy()
    changed = True
    while changed:
        changed = False
        for lhs, rhs in fds:
            if lhs.issubset(closure):
                if not rhs.issubset(closure):
                    closure.update(rhs)
                    changed = True
    return closure

def find_candidate_keys(all_attrs: set, fds: list):
    """
    Finds all minimal candidate keys for the relation.
    """
    candidate_keys = []
    
    rhs_union = set()
    for lhs, rhs in fds:
        rhs_union.update(rhs)
    
    essential_attrs = all_attrs - rhs_union
    remaining_attrs = list(all_attrs - essential_attrs)
    
    def is_superkey_of_existing(candidate):
        for key in candidate_keys:
            if key.issubset(candidate):
                return True
        return False

    # Check from size 0 to len(remaining)
    for r in range(len(remaining_attrs) + 1):
        for combination in itertools.combinations(remaining_attrs, r):
            candidate = essential_attrs.union(combination)
            
            if is_superkey_of_existing(candidate):
                continue
                
            if attribute_closure(candidate, fds) == all_attrs:
                candidate_keys.append(candidate)
    
    if not candidate_keys:
        # Should not happen if all_attrs is correct, at least all_attrs is a superkey
        if attribute_closure(all_attrs, fds) == all_attrs:
             candidate_keys.append(all_attrs)

    return candidate_keys

def determine_normal_form(relation_attrs, fds, candidate_keys):
    """
    Determines the highest normal form (1NF, 2NF, 3NF, BCNF) and explains violations.
    Returns (NormalFormString, ExplanationString, ViolatingFDs).
    """
    prime_attributes = set()
    for key in candidate_keys:
        prime_attributes.update(key)
        
    violations_2nf = []
    violations_3nf = []
    violations_bcnf = []
    
    for lhs, rhs in fds:
        # Filter FDs to those relevant to this relation (LHS and RHS in relation_attrs)
        if not lhs.issubset(relation_attrs) or not rhs.issubset(relation_attrs):
            continue
            
        clean_rhs = rhs - lhs
        if not clean_rhs:
            continue

        # Check BCNF: LHS must be a superkey
        # Note: We must check if LHS is a superkey *in this relation*.
        # Computing closure using ALL fds, then checking if it covers relation_attrs.
        lhs_closure = attribute_closure(lhs, fds)
        is_superkey = relation_attrs.issubset(lhs_closure)
            
        if not is_superkey:
            violations_bcnf.append((lhs, clean_rhs, "LHS is not a superkey"))
            
            # Check 2NF
            is_proper_subset_of_key = False
            for key in candidate_keys:
                if lhs.issubset(key) and lhs != key:
                    is_proper_subset_of_key = True
                    break
            
            non_prime_rhs = clean_rhs - prime_attributes
            
            if is_proper_subset_of_key and non_prime_rhs:
                 violations_2nf.append((lhs, non_prime_rhs, "Partial dependency"))

            # Check 3NF
            if not is_proper_subset_of_key:
                 if non_prime_rhs:
                     violations_3nf.append((lhs, non_prime_rhs, "Transitive dependency"))

    if violations_2nf:
        return "1NF", "Violates 2NF (Partial Dependencies detected).", violations_2nf
    
    if violations_3nf:
        return "2NF", "Violates 3NF (Transitive Dependencies detected).", violations_3nf
        
    if violations_bcnf:
        return "3NF", "Violates BCNF (Dependencies where LHS is not a superkey detected).", violations_bcnf
        
    return "BCNF", "Satisfies BCNF (All determinants are superkeys).", []

def decompose_to_bcnf(relation_name, relation_attrs, fds):
    """
    Decomposes relation into BCNF step by step.
    Returns (steps, final_schemas).
    """
    steps = []
    final_schemas = []
    queue = [{'name': relation_name, 'attrs': relation_attrs}]
    
    iterations = 0
    while queue and iterations < 50:
        iterations += 1
        schema = queue.pop(0)
        attrs = schema['attrs']
        name = schema['name']
        
        # Find violation in this schema
        violation = None
        
        # We need to consider all FDs that apply to this schema
        # An FD X->Y applies if X and Y are in attrs. 
        # But crucially, we must check if X->Y violates BCNF *restricted to this schema*.
        # i.e., X closure (using global FDs) intersection attrs does NOT contain all attrs.
        
        for lhs, rhs in fds:
            # Check if FD lhs is in this relation
            if not lhs.issubset(attrs):
                continue
            
            # Compute closure of LHS
            full_closure = attribute_closure(lhs, fds)
            
            # Project closure to current attributes
            local_closure = full_closure.intersection(attrs)
            
            # Check if this defines a functional dependency X -> (local_closure - X) within this relation
            determined_in_relation = local_closure - lhs
            
            if not determined_in_relation:
                continue
                
            # Check if X is a superkey for this relation
            if not attrs.issubset(local_closure):
                # Found violation: X -> determined_in_relation
                # This FD holds in 'attrs' but X is not a superkey of 'attrs'
                violation = (lhs, determined_in_relation)
                break
        
        if violation:
            X, Y = violation
            
            # Split
            # R1 = X U Y
            attrs1 = X.union(Y)
            name1 = f"{name}_1"
            
            # R2 = R - Y (really R - (Y - X))
            attrs2 = attrs - (Y - X)
            name2 = f"{name}_2"
            
            schema1 = {'name': name1, 'attrs': attrs1}
            schema2 = {'name': name2, 'attrs': attrs2}
            
            steps.append({
                'current_relation': schema,
                'violating_fd': f"{set(X)} -> {set(Y)}",
                'new_relations': [schema1, schema2],
                'explanation': f"Decomposed {name} because {set(X)} -> {set(Y)} violates BCNF. {set(X)} determines {set(Y)} but is not a superkey."
            })
            
            queue.append(schema1)
            queue.append(schema2)
        else:
            final_schemas.append(schema)
            
    return steps, final_schemas
