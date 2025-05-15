import openai
from typing import Dict, Any
from app.models.query import CypherQueryDetails
from app.utils.cypher_templates import get_template_by_intent, get_resource_specific_template, get_relationship_specific_template

class NLPService:
    def __init__(self, openai_api_key: str, openai_model: str = "gpt-4"):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        openai.api_key = openai_api_key
        
    async def translate_to_cypher(self, natural_language_query: str) -> CypherQueryDetails:
        """
        Translate a natural language query to a Cypher query.
        
        Args:
            natural_language_query: The natural language query to translate
            
        Returns:
            CypherQueryDetails object containing the Cypher query and parameters
        """
        # First, determine the intent of the query
        intent_details = await self._determine_query_intent(natural_language_query)
        intent = intent_details.get("intent", "general_resources")
        resource_type = intent_details.get("resource_type")
        relationship_type = intent_details.get("relationship_type")
        
        # Get the appropriate template based on the intent
        template = None
        if intent in ["ec2_to_s3_access", "security_group_resources", "vpc_resources", "iam_permissions", "general_resources"]:
            template = get_template_by_intent(intent)
        elif resource_type:
            template = get_resource_specific_template(resource_type)
        elif relationship_type:
            template = get_relationship_specific_template(relationship_type)
        else:
            template = get_template_by_intent("general_resources")
        
        # For a real implementation, we'd customize the template based on specifics in the query
        # For this POC, we'll just use the template as is
        
        return CypherQueryDetails(
            cypher_query=template["query"],
            parameters={},
            explanation=f"Query intent: {intent}. {template['description']}."
        )
    
    async def _determine_query_intent(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Use OpenAI to determine the intent of the natural language query.
        
        Args:
            natural_language_query: The natural language query
            
        Returns:
            Dictionary containing the intent and other details
        """
        prompt = f"""
        Analyze the following cloud infrastructure query and determine its intent.
        Choose the most appropriate intent from the following options:
        - ec2_to_s3_access: Queries about EC2 instances accessing S3 buckets
        - security_group_resources: Queries about security groups and protected resources
        - vpc_resources: Queries about resources in VPCs
        - iam_permissions: Queries about IAM roles and permissions
        - general_resources: General queries about cloud resources
        
        Or identify a specific resource type:
        - ec2: EC2 instances
        - s3: S3 buckets
        - sg: Security groups
        - vpc: VPCs
        - iam: IAM roles
        
        Or identify a relationship type:
        - access: Resources with access to other resources
        - belongs_to: Resources that belong to other resources
        - located_in: Resources located in regions or subnets
        - assumes: EC2 instances assuming IAM roles
        - protected_by: Resources protected by security groups
        
        Query: {natural_language_query}
        
        Return only a JSON object with the following structure:
        {{
            "intent": "<selected intent>",
            "resource_type": "<resource type if applicable, otherwise null>",
            "relationship_type": "<relationship type if applicable, otherwise null>"
        }}
        """
        
        try:
            response = openai.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a cloud infrastructure query analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            intent_data = response.choices[0].message.content
            
            # For a real implementation, we'd parse the JSON properly
            # For this POC, we'll return a simple intent
            # In practice, this would be properly parsed from the response
            
            import json
            return json.loads(intent_data)
            
        except Exception as e:
            # Fallback to general resources if OpenAI call fails
            print(f"Error determining query intent: {str(e)}")
            return {"intent": "general_resources", "resource_type": None, "relationship_type": None}