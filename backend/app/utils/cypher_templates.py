from typing import Dict, Any


def get_template_by_intent(intent: str) -> Dict[str, Any]:
    """
    Get a Cypher query template based on the query intent.
    
    Args:
        intent: The identified intent of the query
        
    Returns:
        A dictionary containing the Cypher query and parameters
    """
    templates = {
        "ec2_to_s3_access": {
            "query": """
            MATCH path = (i:EC2Instance)-[r:HAS_ACCESS_TO]->(b:S3Bucket)
            RETURN path, i, r, b
            LIMIT 25
            """,
            "parameters": {},
            "description": "EC2 instances with access to S3 buckets"
        },
        "security_group_resources": {
            "query": """
            MATCH path = (sg:SecurityGroup)-[r]->(target)
            WHERE target:EC2Instance OR target:S3Bucket OR target:SecurityGroup
            RETURN path, sg, r, target
            LIMIT 25
            """,
            "parameters": {},
            "description": "Security groups and the resources they protect or have access to"
        },
        "vpc_resources": {
            "query": """
            MATCH path = (vpc:VPC)<-[:BELONGS_TO]-(resource)
            WHERE resource:EC2Instance OR resource:Subnet OR resource:SecurityGroup
            RETURN path, vpc, resource
            LIMIT 25
            """,
            "parameters": {},
            "description": "Resources that belong to VPCs"
        },
        "iam_permissions": {
            "query": """
            MATCH path = (i:EC2Instance)-[:ASSUMES]->(r:IAMRole)-[access:HAS_ACCESS_TO]->(resource)
            RETURN path, i, r, access, resource
            LIMIT 25
            """,
            "parameters": {},
            "description": "IAM roles assumed by EC2 instances and the resources they can access"
        },
        "general_resources": {
            "query": """
            MATCH (n)
            WHERE n:EC2Instance OR n:S3Bucket OR n:SecurityGroup OR n:VPC OR n:IAMRole
            WITH n
            LIMIT 25
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, r, m
            """,
            "parameters": {},
            "description": "General overview of cloud resources and their relationships"
        }
    }
    
    return templates.get(intent, templates["general_resources"])


def get_resource_specific_template(resource_type: str) -> Dict[str, Any]:
    """
    Get a Cypher query template for a specific resource type.
    
    Args:
        resource_type: The AWS resource type (e.g., 'ec2', 's3', 'sg')
        
    Returns:
        A dictionary containing the Cypher query and parameters
    """
    templates = {
        "ec2": {
            "query": """
            MATCH (i:EC2Instance)
            WITH i
            LIMIT 25
            OPTIONAL MATCH (i)-[r]-(related)
            RETURN i, r, related
            """,
            "parameters": {},
            "description": "EC2 instances and their relationships"
        },
        "s3": {
            "query": """
            MATCH (b:S3Bucket)
            WITH b
            LIMIT 25
            OPTIONAL MATCH (b)-[r]-(related)
            RETURN b, r, related
            """,
            "parameters": {},
            "description": "S3 buckets and their relationships"
        },
        "sg": {
            "query": """
            MATCH (sg:SecurityGroup)
            WITH sg
            LIMIT 25
            OPTIONAL MATCH (sg)-[r]-(related)
            RETURN sg, r, related
            """,
            "parameters": {},
            "description": "Security groups and their relationships"
        },
        "vpc": {
            "query": """
            MATCH (v:VPC)
            WITH v
            LIMIT 25
            OPTIONAL MATCH (v)-[r]-(related)
            RETURN v, r, related
            """,
            "parameters": {},
            "description": "VPCs and their relationships"
        },
        "iam": {
            "query": """
            MATCH (r:IAMRole)
            WITH r
            LIMIT 25
            OPTIONAL MATCH (r)-[rel]-(related)
            RETURN r, rel, related
            """,
            "parameters": {},
            "description": "IAM roles and their relationships"
        }
    }
    
    return templates.get(resource_type, templates["ec2"])


def get_relationship_specific_template(relationship_type: str) -> Dict[str, Any]:
    """
    Get a Cypher query template for a specific relationship type.
    
    Args:
        relationship_type: The relationship type (e.g., 'access', 'belongs_to')
        
    Returns:
        A dictionary containing the Cypher query and parameters
    """
    templates = {
        "access": {
            "query": """
            MATCH path = (source)-[r:HAS_ACCESS_TO]->(target)
            RETURN path, source, r, target
            LIMIT 25
            """,
            "parameters": {},
            "description": "Resources with access to other resources"
        },
        "belongs_to": {
            "query": """
            MATCH path = (resource)-[r:BELONGS_TO]->(parent)
            RETURN path, resource, r, parent
            LIMIT 25
            """,
            "parameters": {},
            "description": "Resources that belong to other resources"
        },
        "located_in": {
            "query": """
            MATCH path = (resource)-[r:LOCATED_IN]->(location)
            RETURN path, resource, r, location
            LIMIT 25
            """,
            "parameters": {},
            "description": "Resources located in regions or subnets"
        },
        "assumes": {
            "query": """
            MATCH path = (i:EC2Instance)-[r:ASSUMES]->(role:IAMRole)
            RETURN path, i, r, role
            LIMIT 25
            """,
            "parameters": {},
            "description": "EC2 instances assuming IAM roles"
        },
        "protected_by": {
            "query": """
            MATCH path = (resource)-[r:PROTECTED_BY]->(sg:SecurityGroup)
            RETURN path, resource, r, sg
            LIMIT 25
            """,
            "parameters": {},
            "description": "Resources protected by security groups"
        }
    }
    
    return templates.get(relationship_type, templates["access"])