import boto3
from typing import Dict, Any
from app.services.neo4j_service import Neo4jService

class AwsCollectorService:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, aws_region: str, neo4j_service: Neo4jService):
        """
        Initialize AWS collector service.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region to collect data from
            neo4j_service: Neo4j service for storing collected data
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.neo4j_service = neo4j_service
        
        # Initialize AWS session
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
    
    async def collect_and_store_aws_data(self):
        """
        Collect AWS data and store it in Neo4j.
        
        This is a simplified implementation for POC purposes.
        A full implementation would collect more resources and their relationships.
        """
        try:
            # Collect EC2 instances
            ec2_data = self._collect_ec2_instances()
            
            # Collect S3 buckets
            s3_data = self._collect_s3_buckets()
            
            # Collect VPCs
            vpc_data = self._collect_vpcs()
            
            # Collect security groups
            sg_data = self._collect_security_groups()
            
            # Collect IAM roles
            iam_data = self._collect_iam_roles()
            
            # Store data in Neo4j
            self._store_data_in_neo4j(ec2_data, s3_data, vpc_data, sg_data, iam_data)
            
            return {"status": "success", "message": "AWS data collected and stored in Neo4j"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _collect_ec2_instances(self) -> Dict[str, Any]:
        """Collect EC2 instances from AWS."""
        # In a real implementation, this would call the AWS API to get EC2 instances
        # For POC purposes, returning sample data
        return {
            "instances": [
                {"id": "i-123456789", "type": "t2.micro", "name": "web-server-1", "vpc_id": "vpc-12345"},
                {"id": "i-987654321", "type": "t2.medium", "name": "db-server-1", "vpc_id": "vpc-12345"}
            ]
        }
    
    def _collect_s3_buckets(self) -> Dict[str, Any]:
        """Collect S3 buckets from AWS."""
        # In a real implementation, this would call the AWS API to get S3 buckets
        # For POC purposes, returning sample data
        return {
            "buckets": [
                {"name": "my-data-bucket", "region": "us-east-1", "created": "2023-01-01"},
                {"name": "my-logs-bucket", "region": "us-east-1", "created": "2023-01-01"}
            ]
        }
    
    def _collect_vpcs(self) -> Dict[str, Any]:
        """Collect VPCs from AWS."""
        # In a real implementation, this would call the AWS API to get VPCs
        # For POC purposes, returning sample data
        return {
            "vpcs": [
                {"id": "vpc-12345", "cidr": "10.0.0.0/16", "name": "main-vpc", "region": "us-east-1"}
            ]
        }
    
    def _collect_security_groups(self) -> Dict[str, Any]:
        """Collect security groups from AWS."""
        # In a real implementation, this would call the AWS API to get security groups
        # For POC purposes, returning sample data
        return {
            "security_groups": [
                {"id": "sg-12345", "name": "web-sg", "vpc_id": "vpc-12345"},
                {"id": "sg-67890", "name": "db-sg", "vpc_id": "vpc-12345"}
            ]
        }
    
    def _collect_iam_roles(self) -> Dict[str, Any]:
        """Collect IAM roles from AWS."""
        # In a real implementation, this would call the AWS API to get IAM roles
        # For POC purposes, returning sample data
        return {
            "roles": [
                {"name": "ec2-role", "arn": "arn:aws:iam::123456789012:role/ec2-role"},
                {"name": "s3-access-role", "arn": "arn:aws:iam::123456789012:role/s3-access-role"}
            ]
        }
    
    def _store_data_in_neo4j(self, ec2_data, s3_data, vpc_data, sg_data, iam_data):
        """
        Store collected AWS data in Neo4j.
        
        In a real implementation, this would convert the AWS data to Cypher queries
        and execute them using the Neo4j service.
        """
        # For POC purposes, this is a simplified implementation
        # that just creates nodes and relationships for the sample data
        
        # Create VPC nodes
        for vpc in vpc_data["vpcs"]:
            self.neo4j_service.execute_query(
                """
                MERGE (v:VPC {id: $id})
                SET v.cidr = $cidr,
                    v.name = $name,
                    v.region = $region
                RETURN v
                """,
                {"id": vpc["id"], "cidr": vpc["cidr"], "name": vpc["name"], "region": vpc["region"]}
            )
        
        # Create EC2 nodes and relationships
        for instance in ec2_data["instances"]:
            self.neo4j_service.execute_query(
                """
                MATCH (v:VPC {id: $vpc_id})
                MERGE (i:EC2Instance {id: $id})
                SET i.type = $type,
                    i.name = $name
                MERGE (i)-[:BELONGS_TO]->(v)
                RETURN i, v
                """,
                {
                    "id": instance["id"],
                    "type": instance["type"],
                    "name": instance["name"],
                    "vpc_id": instance["vpc_id"]
                }
            )
        
        # Create S3 bucket nodes
        for bucket in s3_data["buckets"]:
            self.neo4j_service.execute_query(
                """
                MERGE (b:S3Bucket {name: $name})
                SET b.region = $region,
                    b.created = $created
                RETURN b
                """,
                {
                    "name": bucket["name"],
                    "region": bucket["region"],
                    "created": bucket["created"]
                }
            )
        
        # Create security group nodes and relationships
        for sg in sg_data["security_groups"]:
            self.neo4j_service.execute_query(
                """
                MATCH (v:VPC {id: $vpc_id})
                MERGE (sg:SecurityGroup {id: $id})
                SET sg.name = $name
                MERGE (sg)-[:BELONGS_TO]->(v)
                RETURN sg, v
                """,
                {
                    "id": sg["id"],
                    "name": sg["name"],
                    "vpc_id": sg["vpc_id"]
                }
            )
        
        # Create IAM role nodes
        for role in iam_data["roles"]:
            self.neo4j_service.execute_query(
                """
                MERGE (r:IAMRole {arn: $arn})
                SET r.name = $name
                RETURN r
                """,
                {
                    "arn": role["arn"],
                    "name": role["name"]
                }
            )
        
        # Create some sample relationships for demonstration
        # EC2 instance assumes IAM role
        self.neo4j_service.execute_query(
            """
            MATCH (i:EC2Instance {id: 'i-123456789'})
            MATCH (r:IAMRole {name: 'ec2-role'})
            MERGE (i)-[:ASSUMES]->(r)
            RETURN i, r
            """,
            {}
        )
        
        # IAM role has access to S3 bucket
        self.neo4j_service.execute_query(
            """
            MATCH (r:IAMRole {name: 's3-access-role'})
            MATCH (b:S3Bucket {name: 'my-data-bucket'})
            MERGE (r)-[:HAS_ACCESS_TO]->(b)
            RETURN r, b
            """,
            {}
        )
        
        # EC2 instance protected by security group
        self.neo4j_service.execute_query(
            """
            MATCH (i:EC2Instance {id: 'i-123456789'})
            MATCH (sg:SecurityGroup {id: 'sg-12345'})
            MERGE (i)-[:PROTECTED_BY]->(sg)
            RETURN i, sg
            """,
            {}
        )
        
        # EC2 instance has access to S3 bucket
        self.neo4j_service.execute_query(
            """
            MATCH (i:EC2Instance {id: 'i-987654321'})
            MATCH (b:S3Bucket {name: 'my-logs-bucket'})
            MERGE (i)-[:HAS_ACCESS_TO]->(b)
            RETURN i, b
            """,
            {}
        )