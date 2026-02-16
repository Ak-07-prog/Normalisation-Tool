from normalization import *

# Freelance Marketplace Test Case
print("Testing Freelance Marketplace normalization...")

# Relations provided in prompt
# But we need to test the logic. Let's create a scenario that requires normalization.
# Example: A big denormalized relation
# GigMix(GigID, ClientID, FreelancerID, Title, Budget, MilestoneID, Amount)
# FDs:
# GigID -> ClientID, FreelancerID, Title, Budget
# MilestoneID -> GigID, Amount

attrs_str = "GigMix(GigID, ClientID, FreelancerID, Title, Budget, MilestoneID, Amount)"
fds_str = """
GigID -> ClientID, FreelancerID, Title, Budget
MilestoneID -> GigID, Amount
"""

name, attrs = parse_relation(attrs_str)
fds = parse_fds(fds_str)
print(f"Relation: {name}, Attrs: {attrs}")
print(f"FDs: {fds}")

closure_milestone = attribute_closure({"MilestoneID"}, fds)
print(f"Closure(MilestoneID): {closure_milestone}")
# Expect: MilestoneID -> GigID, Amount -> (via GigID) ClientID, FreelancerID, Title, Budget
# So Closure should be ALL.

closure_gig = attribute_closure({"GigID"}, fds)
print(f"Closure(GigID): {closure_gig}")
# Expect: GigID + ClientID, FreelancerID, Title, Budget. Missing MilestoneID, Amount.

keys = find_candidate_keys(attrs, fds)
print(f"Candidate Keys: {keys}")
# Expect: {MilestoneID} should be a key because it determines everything?
# Wait. MilestoneID -> GigID, Amount. GigID -> others.
# So MilestoneID determines all.
# GigID does NOT determine MilestoneID.
# So MilestoneID is a key.

# Normal Form
nf, expl, violations = determine_normal_form(attrs, fds, keys)
print(f"Normal Form: {nf}")
print(f"Violations: {violations}")

# BCNF Decomposition
steps, finals = decompose_to_bcnf(name, attrs, fds)
for i, step in enumerate(steps):
    print(f"Step {i+1}:")
    print(f"  Decomposed: {step['current_relation']['name']}")
    print(f"  FD: {step['violating_fd']}")
    print(f"  New: {[r['name'] for r in step['new_relations']]}")
    print(f"  Attrs 1: {step['new_relations'][0]['attrs']}")
    print(f"  Attrs 2: {step['new_relations'][1]['attrs']}")

print("Final relations:")
for r in finals:
    print(f"  {r['name']}: {r['attrs']}")
