import streamlit as st
import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import io
import time

# Configure the app
st.set_page_config(
    page_title="Cloud Cartography NL Query System",
    page_icon="☁️",
    layout="wide"
)

# App title and description
st.title("Cloud Cartography NL Query System")
st.markdown("""
This application uses Cartography to build a knowledge graph of your AWS infrastructure and allows you to query it using natural language.
""")

# Backend API URLs
API_BASE_URL = "http://localhost:8000/api/v1"
QUERIES_URL = f"{API_BASE_URL}/queries/"
CARTOGRAPHY_URL = f"{API_BASE_URL}/cartography/run"

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'graph_initialized' not in st.session_state:
    st.session_state.graph_initialized = False

# Function to process and visualize graph data
def visualize_graph(graph_data):
    if not graph_data['nodes']:
        st.warning("No data returned for this query.")
        return
    
    # Create a NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes with their properties
    node_labels = {}
    node_colors = []
    node_types = []
    
    # Define color map for different node types (based on Cartography schema)
    color_map = {
        'AWSAccount': '#3498db',  # Blue
        'EC2Instance': '#2ecc71',  # Green
        'EC2SecurityGroup': '#e74c3c',  # Red
        'S3Bucket': '#f39c12',  # Orange
        'IAMRole': '#9b59b6',  # Purple
        'AWSVpc': '#1abc9c',  # Turquoise
        'LoadBalancer': '#34495e',  # Dark blue
        'DBInstance': '#e67e22',  # Dark orange
        'AWSUser': '#95a5a6',  # Gray
        'DynamoDBTable': '#d35400',  # Brown
        'LambdaFunction': '#27ae60',  # Dark green
    }
    
    default_color = '#bdc3c7'  # Light gray for unknown types
    
    # Add nodes to the graph
    for node in graph_data['nodes']:
        G.add_node(node['id'])
        
        # Create node label based on available properties
        # Cartography often uses 'name' or 'id' as main identifiers
        label = node['properties'].get('name', 
                node['properties'].get('instanceid',
                node['properties'].get('bucketname',
                node['properties'].get('arn',
                node['properties'].get('id', node['id'])))))
        
        node_labels[node['id']] = label
        
        # Determine node color based on type (label in Neo4j)
        node_type = node['labels'][0] if node['labels'] else 'Unknown'
        node_types.append(node_type)
        node_colors.append(color_map.get(node_type, default_color))
    
    # Add edges to the graph
    edge_labels = {}
    for rel in graph_data['relationships']:
        G.add_edge(rel['start_node'], rel['end_node'])
        edge_labels[(rel['start_node'], rel['end_node'])] = rel['type']
    
    # Set up the plot
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=700, alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, arrows=True, arrowsize=15)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    
    plt.title("Cloud Infrastructure Graph", fontsize=16)
    plt.axis('off')
    
    # Convert plot to image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Display the image
    st.image(buf, caption='Cloud Infrastructure Graph Visualization', use_column_width=True)
    
    # Create a legend for node types that are in the graph
    unique_types = list(set(node_types))
    if unique_types:
        st.subheader("Legend")
        # Calculate how many columns based on the number of types
        num_cols = min(len(unique_types), 5)  # Max 5 columns
        legend_cols = st.columns(num_cols)
        
        for i, node_type in enumerate(unique_types):
            col_idx = i % num_cols
            with legend_cols[col_idx]:
                color = color_map.get(node_type, default_color)
                st.markdown(
                    f'<div style="background-color: {color}; '
                    f'width: 20px; height: 20px; display: inline-block; '
                    f'margin-right: 5px; border: 1px solid black;"></div> {node_type}',
                    unsafe_allow_html=True
                )
    
    # Display node and relationship tables
    st.subheader("Nodes")
    nodes_df = []
    for node in graph_data['nodes']:
        node_info = {
            'ID': node['id'],
            'Type': node['labels'][0] if node['labels'] else 'Unknown'
        }
        # Add all properties (up to a reasonable amount)
        for k, v in list(node['properties'].items())[:10]:  # Limit to first 10 properties
            node_info[k] = v
        nodes_df.append(node_info)
    
    if nodes_df:
        nodes_df = pd.DataFrame(nodes_df)
        st.dataframe(nodes_df)
    
    st.subheader("Relationships")
    rels_df = []
    for rel in graph_data['relationships']:
        rel_info = {
            'Source': node_labels.get(rel['start_node'], rel['start_node']),
            'Relationship': rel['type'],
            'Target': node_labels.get(rel['end_node'], rel['end_node'])
        }
        # Add properties if any
        for k, v in rel['properties'].items():
            rel_info[k] = v
        rels_df.append(rel_info)
    
    if rels_df:
        rels_df = pd.DataFrame(rels_df)
        st.dataframe(rels_df)

# AWS Credentials and Cartography Initialization Section
st.header("AWS Setup & Cartography Initialization")
st.markdown("""
Enter your AWS credentials to run Cartography and build a knowledge graph of your infrastructure.
This is required before you can query your infrastructure.
""")

# Fixed: Properly structure the form without nested expanders
with st.form("aws_credentials_form"):
    aws_access_key = st.text_input("AWS Access Key ID", type="password")
    aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
    aws_region = st.text_input("AWS Region", value="us-east-1")
    openai_api_key = st.text_input("OpenAI API Key (for NL processing)", type="password")
    
    use_sample_data = st.checkbox("Use sample data instead of real AWS credentials", value=True)
    
    # Advanced options as checkboxes and sliders (not in an expander)
    st.subheader("Advanced Options")
    collect_dns = st.checkbox("Collect DNS Records", value=False)
    collect_gcp = st.checkbox("Collect GCP Data (requires GCP credentials)", value=False)
    collect_okta = st.checkbox("Collect Okta Data (requires Okta credentials)", value=False)
    days_of_data = st.slider("Number of days of data to sync", min_value=1, max_value=30, value=7)
    
    submitted = st.form_submit_button("Run Cartography & Initialize Knowledge Graph")
    
    if submitted:
        with st.spinner('Running Cartography and building knowledge graph...'):
            try:
                # Send request to backend to run Cartography
                payload = {
                    "aws_access_key_id": aws_access_key if not use_sample_data else "",
                    "aws_secret_access_key": aws_secret_key if not use_sample_data else "",
                    "aws_region": aws_region,
                    "openai_api_key": openai_api_key,
                    "use_sample_data": use_sample_data,
                    "advanced_options": {
                        "collect_dns": collect_dns,
                        "collect_gcp": collect_gcp,
                        "collect_okta": collect_okta,
                        "days_of_data": days_of_data
                    }
                }
                
                response = requests.post(
                    CARTOGRAPHY_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Knowledge graph initialized successfully! {result.get('message', '')}")
                    st.session_state.graph_initialized = True
                    
                    # Show sample queries that can be used
                    st.subheader("Sample Queries")
                    st.markdown("""
                    Try these sample queries:
                    - Show me all EC2 instances in my AWS account
                    - What S3 buckets have public access?
                    - Which EC2 instances are in the default VPC?
                    - Show me IAM roles with admin access
                    - Which security groups allow access from the internet?
                    - Show me unencrypted S3 buckets
                    - Which EC2 instances can access sensitive S3 buckets?
                    """)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Query Section - Only show if the graph has been initialized
if st.session_state.graph_initialized:
    st.header("Query Your Cloud Infrastructure")
    
    # Input for natural language query
    with st.form("query_form"):
        nl_query = st.text_area(
            "Enter your cloud infrastructure query:", 
            "Show me all EC2 instances in my AWS account",
            height=100
        )
        include_details = st.checkbox("Include query details in response", value=True)
        
        # Create columns for the form buttons
        cols = st.columns([1, 1, 3])
        with cols[0]:
            submitted = st.form_submit_button("Submit Query")
        with cols[1]:
            clear = st.form_submit_button("Clear Results")

    # Process the query if submitted
    if submitted:
        with st.spinner('Processing your query...'):
            try:
                response = requests.post(
                    QUERIES_URL,
                    json={"natural_language_query": nl_query, "include_query_details": include_details},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add to query history
                    st.session_state.query_history.append({
                        "query": nl_query,
                        "result": result
                    })
                    
                    # Display query details if available
                    if include_details and result.get('query_details'):
                        st.subheader("Query Details")
                        st.markdown("**Cypher Query:**")
                        st.code(result['query_details']['cypher_query'], language='cypher')
                        
                        if result['query_details'].get('explanation'):
                            st.markdown("**Explanation:**")
                            st.info(result['query_details']['explanation'])
                    
                    # Visualize the graph
                    st.subheader("Graph Results")
                    visualize_graph(result['graph_data'])
                    
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Add a query history section
    if st.session_state.query_history:
        with st.expander("Query History"):
            for i, item in enumerate(st.session_state.query_history):
                st.markdown(f"**Query {i+1}:** {item['query']}")
                if st.button(f"Rerun Query {i+1}"):
                    nl_query = item['query']
                    with st.spinner('Processing your query...'):
                        try:
                            response = requests.post(
                                QUERIES_URL,
                                json={"natural_language_query": nl_query, "include_query_details": include_details},
                                headers={"Content-Type": "application/json"}
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                # Display query details if available
                                if include_details and result.get('query_details'):
                                    st.subheader("Query Details")
                                    st.markdown("**Cypher Query:**")
                                    st.code(result['query_details']['cypher_query'], language='cypher')
                                    
                                    if result['query_details'].get('explanation'):
                                        st.markdown("**Explanation:**")
                                        st.info(result['query_details']['explanation'])
                                
                                # Visualize the graph
                                st.subheader("Graph Results")
                                visualize_graph(result['graph_data'])
                                
                            else:
                                st.error(f"Error: {response.status_code} - {response.text}")
                        
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
else:
    st.info("Please set up your AWS credentials and run Cartography to initialize the knowledge graph.")