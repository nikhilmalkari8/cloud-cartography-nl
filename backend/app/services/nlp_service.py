import requests
from typing import Dict, Any
from app.models.query import CypherQueryDetails
import logging
import json
import os

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self, openai_api_key: str, openai_model: str = "gpt-3.5-turbo"):  # Changed default model
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        
    async def translate_to_cypher(self, natural_language_query: str) -> CypherQueryDetails:
        """
        Translate a natural language query to a Cypher query.
        
        Args:
            natural_language_query: The natural language query to translate
            
        Returns:
            CypherQueryDetails object containing the Cypher query and parameters
        """
        try:
            # Cartography's schema is different from our custom schema
            # We need to use a specific prompt that reflects Cartography's data model
            prompt = f"""
            You are an expert in translating natural language queries about AWS cloud infrastructure into Cypher queries for Neo4j.
            The data was collected using Cartography, which creates a graph database with AWS resources and their relationships.
            
            Here are the main node types in the graph:
            - AWSAccount: AWS accounts
            - EC2Instance: EC2 instances
            - S3Bucket: S3 buckets
            - EC2SecurityGroup: Security groups
            - AWSVpc: VPCs
            - IAMRole: IAM roles
            - IAMPolicy: IAM policies
            
            Here are important relationships between nodes:
            - (EC2Instance)-[:RESOURCE_OF]->(AWSAccount)
            - (S3Bucket)-[:RESOURCE_OF]->(AWSAccount)
            - (EC2SecurityGroup)-[:RESOURCE_OF]->(AWSAccount)
            - (AWSVpc)-[:RESOURCE_OF]->(AWSAccount)
            - (IAMRole)-[:RESOURCE_OF]->(AWSAccount)
            - (EC2Instance)-[:PART_OF_VPC]->(AWSVpc)
            - (EC2SecurityGroup)-[:MEMBER_OF_VPC]->(AWSVpc)
            - (EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
            - (EC2SecurityGroup)-[:HAS_INBOUND_RULE]->(EC2SecurityGroupRule)
            - (EC2Instance)-[:HAS_ROLE]->(IAMRole)
            - (IAMRole)-[:HAS_POLICY]->(IAMPolicy)
            
            Important node properties:
            - EC2Instance: id, name, instanceid, instancetype, region, state
            - S3Bucket: id, name, bucketname, region, created, public
            - EC2SecurityGroup: id, name, groupid, description
            - AWSVpc: id, name, vpcid, cidr_block, region
            - IAMRole: id, name, rolename, arn
            - IAMPolicy: id, name, policyname, arn
            
            Translate the following natural language query into a Cypher query that returns the relevant nodes and relationships.
            Always include LIMIT 100 at the end of your query to prevent returning too many results.
            If the query involves relationships, make sure to return the full path.
            
            Natural language query: {natural_language_query}
            
            Your response must be a valid JSON object with the following structure:
            {{
                "cypher_query": "The Cypher query that should be executed",
                "parameters": {{}},
                "explanation": "A brief explanation of what the query is doing"
            }}
            
            Return ONLY the JSON object and nothing else.
            """
            
            # Using the OpenAI REST API directly instead of the Python client
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            # Check if the model supports response_format
            supported_models = ["gpt-4-turbo", "gpt-4", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-3.5-turbo", "gpt-3.5-turbo-1106"]
            
            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": "You are a Cypher query expert for cloud infrastructure graphs."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0
            }
            
            # Only add response_format for supported models
            if any(supported_model in self.openai_model for supported_model in supported_models):
                payload["response_format"] = {"type": "json_object"}
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            response_data = response.json()
            result_content = response_data['choices'][0]['message']['content']
            
            # Try to parse the response as JSON
            try:
                result = json.loads(result_content)
            except json.JSONDecodeError:
                # If parsing fails, try to extract JSON from the text
                import re
                json_match = re.search(r'({.*})', result_content.replace('\n', ' '), re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        raise Exception("Could not extract valid JSON from OpenAI response")
                else:
                    raise Exception("Could not extract JSON from OpenAI response")
            
            return CypherQueryDetails(
                cypher_query=result.get("cypher_query", ""),
                parameters=result.get("parameters", {}),
                explanation=result.get("explanation", "")
            )
            
        except Exception as e:
            logger.error(f"Error translating query to Cypher: {str(e)}", exc_info=True)
            
            # Determine which type of query the user is asking for
            query = natural_language_query.lower()
            
            # Use template-based fallback queries based on keywords
            if "ec2" in query or "instance" in query:
                if "vpc" in query:
                    cypher = """
                    MATCH (i:EC2Instance)-[:PART_OF_VPC]->(v:AWSVpc)
                    RETURN i, v LIMIT 100
                    """
                    explanation = "Finding EC2 instances and their VPCs"
                elif "security" in query:
                    cypher = """
                    MATCH (i:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
                    RETURN i, sg LIMIT 100
                    """
                    explanation = "Finding EC2 instances and their security groups"
                elif "role" in query or "iam" in query:
                    cypher = """
                    MATCH (i:EC2Instance)-[:HAS_ROLE]->(r:IAMRole)
                    RETURN i, r LIMIT 100
                    """
                    explanation = "Finding EC2 instances and their IAM roles"
                else:
                    cypher = """
                    MATCH (i:EC2Instance)
                    WITH i LIMIT 100
                    OPTIONAL MATCH (i)-[r]-(related)
                    RETURN i, r, related
                    """
                    explanation = "Showing EC2 instances and their relationships"
            elif "s3" in query or "bucket" in query:
                if "public" in query:
                    cypher = """
                    MATCH (b:S3Bucket)
                    WHERE b.public = true
                    WITH b LIMIT 100
                    OPTIONAL MATCH (b)-[r]-(related)
                    RETURN b, r, related
                    """
                    explanation = "Finding public S3 buckets"
                else:
                    cypher = """
                    MATCH (b:S3Bucket)
                    WITH b LIMIT 100
                    OPTIONAL MATCH (b)-[r]-(related)
                    RETURN b, r, related
                    """
                    explanation = "Showing S3 buckets and their relationships"
            elif "security" in query or "group" in query:
                if "rule" in query or "allow" in query or "internet" in query:
                    cypher = """
                    MATCH (sg:EC2SecurityGroup)-[:HAS_INBOUND_RULE]->(rule:EC2SecurityGroupRule)
                    WHERE rule.cidr_block = '0.0.0.0/0'
                    RETURN sg, rule LIMIT 100
                    """
                    explanation = "Finding security groups that allow access from the internet"
                else:
                    cypher = """
                    MATCH (sg:EC2SecurityGroup)
                    WITH sg LIMIT 100
                    OPTIONAL MATCH (sg)-[r]-(related)
                    RETURN sg, r, related
                    """
                    explanation = "Showing security groups and their relationships"
            elif "vpc" in query:
                cypher = """
                MATCH (v:AWSVpc)
                WITH v LIMIT 100
                OPTIONAL MATCH (v)-[r]-(related)
                RETURN v, r, related
                """
                explanation = "Showing VPCs and their relationships"
            elif "role" in query or "iam" in query:
                if "admin" in query:
                    cypher = """
                    MATCH (r:IAMRole)-[:HAS_POLICY]->(p:IAMPolicy)
                    WHERE p.name CONTAINS 'Admin' OR p.policyname CONTAINS 'Admin'
                    RETURN r, p LIMIT 100
                    """
                    explanation = "Finding IAM roles with admin access"
                else:
                    cypher = """
                    MATCH (r:IAMRole)
                    WITH r LIMIT 100
                    OPTIONAL MATCH (r)-[rel]-(related)
                    RETURN r, rel, related
                    """
                    explanation = "Showing IAM roles and their relationships"
            else:
                # Default fallback query
                cypher = """
                MATCH (n)
                WHERE n:AWSAccount OR n:EC2Instance OR n:S3Bucket OR n:EC2SecurityGroup OR n:AWSVpc OR n:IAMRole
                WITH n LIMIT 50
                OPTIONAL MATCH (n)-[r]-(related)
                RETURN n, r, related
                """
                explanation = "Showing general cloud infrastructure overview"
            
            return CypherQueryDetails(
                cypher_query=cypher,
                parameters={},
                explanation=f"Error translating query: {str(e)}. {explanation}."
            )