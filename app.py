import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from normalization import (
    parse_relation,
    parse_fds,
    attribute_closure,
    find_candidate_keys,
    determine_normal_form,
    decompose_to_bcnf
)

# Page Configuration
st.set_page_config(
    page_title="DBMS Normalization Tool",
    page_icon="🗄️",
    layout="wide"
)

# Custom CSS for aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #0e1117;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("DBMS Normalization Tool")
st.sidebar.markdown("**Freelance Marketplace Edition**")
st.sidebar.markdown("---")
section = st.sidebar.radio("Go to Section", ["Input", "Computation", "Visualization", "Export"])

st.sidebar.markdown("---")
st.sidebar.info("This tool demonstrates normalization from 1NF to BCNF using a Decentralized Freelance Marketplace case study.")

# State Management
if 'relation_str' not in st.session_state:
    st.session_state.relation_str = "R(A, B, C, D, E)"
if 'fds_str' not in st.session_state:
    st.session_state.fds_str = "A -> B, C\nC -> D"

# Helper to load example
def load_example(example_type):
    if example_type == "Denormalized Marketplace (For Demo)":
        # A relation that needs normalization
        st.session_state.relation_str = "Marketplace(MilestoneID, GigID, ClientID, CompanyName, FreelancerID, FreelancerName, Title, GigBudget, Amount)"
        st.session_state.fds_str = """MilestoneID -> GigID, Amount
GigID -> ClientID, FreelancerID, Title, GigBudget
ClientID -> CompanyName
FreelancerID -> FreelancerName"""
    elif example_type == "Gigs (BCNF)":
        st.session_state.relation_str = "Gigs(GigID, ClientID, FreelancerID, Title, Description, Budget, Status)"
        st.session_state.fds_str = "GigID -> ClientID, FreelancerID, Title, Description, Budget, Status"
    elif example_type == "Freelancers (BCNF)":
        st.session_state.relation_str = "Freelancers(FreelancerID, Name, Email, Skills, Rating, Portfolio_URL, BankAccount)"
        st.session_state.fds_str = "FreelancerID -> Name, Email, Skills, Rating, Portfolio_URL, BankAccount"

# Main Layout
st.title("Normalization GUI Tool")

# --- INPUT SECTION ---
if section == "Input":
    st.header("1. Input Schema & Functional Dependencies")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown("### Load Examples")
        example_choice = st.selectbox(
            "Select Example",
            ["Denormalized Marketplace (For Demo)", "Gigs (BCNF)", "Freelancers (BCNF)"]
        )
        if st.button("Load Selected Example"):
            load_example(example_choice)
            st.rerun()

    with col1:
        st.subheader("Relation Schema")
        relation_input = st.text_input(
            "Enter Relation (e.g., R(A, B, C))",
            value=st.session_state.relation_str,
            help="Format: Name(Attr1, Attr2, ...)"
        )
        st.session_state.relation_str = relation_input

        st.subheader("Functional Dependencies")
        fds_input = st.text_area(
            "Enter FDs (one per line, e.g., A -> B)",
            value=st.session_state.fds_str,
            height=200,
            help="Format: LHS -> RHS (comma separated attributes)"
        )
        st.session_state.fds_str = fds_input
    
    # Validation preview
    st.markdown("### Preview Parsed Input")
    try:
        name, attrs = parse_relation(st.session_state.relation_str)
        fds = parse_fds(st.session_state.fds_str)
        st.success(f"**Relation:** {name}")
        st.write(f"**Attributes ({len(attrs)}):** {', '.join(sorted(attrs))}")
        st.write(f"**Functional Dependencies ({len(fds)}):**")
        for lhs, rhs in fds:
            st.code(f"{', '.join(sorted(lhs))} -> {', '.join(sorted(rhs))}")
    except Exception as e:
        st.error(f"Error parsing input: {e}")

# --- COMPUTATION SECTION ---
elif section == "Computation":
    st.header("2. Computational Analysis")
    
    try:
        name, attrs = parse_relation(st.session_state.relation_str)
        fds = parse_fds(st.session_state.fds_str)
    except:
        st.error("Please provide valid inputs in the 'Input' section first.")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["Attribute Closures", "Candidate Keys", "Normal Form Status", "BCNF Decomposition"])

    with tab1:
        st.subheader("Compute Attribute Closures")
        
        # All attributes closure
        if st.button("Compute Closures for All Attributes"):
            results = []
            for attr in sorted(attrs):
                closure = attribute_closure({attr}, fds)
                results.append({"Attribute": attr, "Closure": ", ".join(sorted(closure))})
            st.table(pd.DataFrame(results))
            
        # Custom closure
        st.markdown("#### Custom Closure Check")
        custom_attrs = st.multiselect("Select Attributes", sorted(attrs))
        if st.button("Compute Custom Closure"):
            if custom_attrs:
                closure = attribute_closure(set(custom_attrs), fds)
                st.info(f"Closure({', '.join(custom_attrs)}) = " + "{ " + ", ".join(sorted(closure)) + " }")
            else:
                st.warning("Select at least one attribute.")

    with tab2:
        st.subheader("Candidate Keys")
        if st.button("Find Candidate Keys"):
            with st.spinner("Calculating candidate keys..."):
                keys = find_candidate_keys(attrs, fds)
            
            if keys:
                st.success(f"Found {len(keys)} Candidate Key(s):")
                for k in keys:
                    st.markdown(f"- **{{ {', '.join(sorted(k))} }}**")
            else:
                st.warning("No candidate keys found (check your FDs and Attributes).")

    with tab3:
        st.subheader("Normal Form Analysis")
        if st.button("Analyze Normal Form"):
            with st.spinner("Analyzing..."):
                keys = find_candidate_keys(attrs, fds)
                nf, explanation, violations = determine_normal_form(attrs, fds, keys)
            
            st.metric("Highest Normal Form", nf)
            st.info(explanation)
            
            if violations:
                st.markdown("### Violations Detected:")
                for lhs, rhs, reason in violations:
                    with st.expander(f"{', '.join(sorted(lhs))} -> {', '.join(sorted(rhs))}", expanded=True):
                        st.write(f"**Reason:** {reason}")
                        st.write(f"**LHS:** {', '.join(sorted(lhs))}")
                        st.write(f"**RHS (Violating):** {', '.join(sorted(rhs))}")
                
                st.warning("👉 To fix these violations, click the **BCNF Decomposition** tab at the top of this section!")

    with tab4:
        st.subheader("Normalize to BCNF (Step-by-Step)")
        if st.button("Run BCNF Decomposition"):
            steps, finals = decompose_to_bcnf(name, attrs, fds)
            
            if not steps:
                st.success("The relation is already in BCNF!")
            else:
                for i, step in enumerate(steps):
                    st.markdown(f"### Step {i+1}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.error(f"**Violating FD:** {step['violating_fd']}")
                        st.write(f"**Input Relation:** {step['current_relation']['name']}")
                        st.caption(f"Attributes: {step['current_relation']['attrs']}")
                    with col_b:
                        st.success("**Decomposition Result:**")
                        for new_r in step['new_relations']:
                            st.write(f"- **{new_r['name']}**: {new_r['attrs']}")
                        st.info(step['explanation'])
                    st.divider()
                
                st.subheader("Final BCNF Schema")
                for r in finals:
                    st.code(f"{r['name']}({', '.join(sorted(r['attrs']))})")

# --- VISUALIZATION SECTION ---
elif section == "Visualization":
    st.header("3. Dependency Graph Visualization")
    
    try:
        name, attrs = parse_relation(st.session_state.relation_str)
        fds = parse_fds(st.session_state.fds_str)
    except:
        st.error("Invalid Input.")
        st.stop()

    if st.button("Generate FD Graph"):
        G = nx.DiGraph()
        
        # Add nodes
        G.add_nodes_from(attrs)
        
        # Add edges for FDs
        # For X -> Y, we verify complexity. 
        # Visualization simplified: Node from EACH X attribute to EACH Y attribute?
        # Or Compound nodes? Simple directed graph A->B is best for students.
        
        for lhs, rhs in fds:
            for l in lhs:
                for r in rhs:
                    G.add_edge(l, r)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        pos = nx.spring_layout(G, k=0.3)
        
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=2000, font_size=10, font_weight='bold', 
                arrows=True, edge_color='gray', ax=ax)
        
        st.pyplot(fig)
        st.caption("Directed graph where edge A -> B implies functional dependency A determines B (partially or fully).")

# --- EXPORT SECTION ---
elif section == "Export":
    st.header("4. Export SQL Schema")
    
    try:
        name, attrs = parse_relation(st.session_state.relation_str)
        fds = parse_fds(st.session_state.fds_str)
    except:
        st.error("Invalid Input.")
        st.stop()
        
    if st.button("Generate SQL"):
        steps, finals = decompose_to_bcnf(name, attrs, fds)
        
        sql_output = "-- SQL Schema for Decentralized Freelance Marketplace\n\n"
        
        # Simple heuristic for types
        def get_type(attr_name):
            attr_name = attr_name.lower()
            if "id" in attr_name:
                return "INT"
            if "price" in attr_name or "amount" in attr_name or "budget" in attr_name:
                return "DECIMAL(10, 2)"
            if "date" in attr_name:
                return "DATE"
            if "description" in attr_name or "terms" in attr_name:
                return "TEXT"
            return "VARCHAR(255)"
        
        for r in finals:
            table_name = r['name']
            columns = []
            
            # Find primary keys for this relation to add PRIMARY KEY constraint
            # We assume the whole relation key is a good PK.
            # We need to re-find keys for each decomposed relation to be accurate,
            # but for BCNF, the determinants used to split are usually keys.
            # Let's just create table.
            
            for attr in sorted(r['attrs']):
                col_type = get_type(attr)
                columns.append(f"    {attr} {col_type}")
            
            create_stmt = f"CREATE TABLE {table_name} (\n"
            create_stmt += ",\n".join(columns)
            create_stmt += "\n);\n"
            
            sql_output += create_stmt + "\n"
            
        st.code(sql_output, language="sql")
        st.success("SQL generated successfully!")
