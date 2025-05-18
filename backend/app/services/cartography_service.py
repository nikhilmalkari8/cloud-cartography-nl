import subprocess
import os
import json
import time
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CartographyService:
    def __init__(
        self, 
        neo4j_uri: str, 
        neo4j_user: str, 
        neo4j_password: str
    ):
        """
        Initialize the Cartography service.
        
        Args:
            neo4j_uri: Neo4j URI (e.g., bolt://localhost:7687)
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
    
    async def run_cartography(
        self, 
        aws_access_key_id: str = "",
        aws_secret_access_key: str = "",
        aws_region: str = "us-east-1",
        use_sample_data: bool = False,
        advanced_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run Cartography to collect cloud infrastructure data and store it in Neo4j.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region
            use_sample_data: Whether to use sample data instead of real AWS credentials
            advanced_options: Additional options for Cartography
            
        Returns:
            Dictionary with the result of the Cartography run
        """
        try:
            # Set environment variables for Cartography
            env = os.environ.copy()
            
            if not use_sample_data:
                env["AWS_ACCESS_KEY_ID"] = aws_access_key_id
                env["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key
                env["AWS_DEFAULT_REGION"] = aws_region
                
            env["NEO4J_URI"] = self.neo4j_uri
            env["NEO4J_USER"] = self.neo4j_user
            env["NEO4J_PASSWORD"] = self.neo4j_password
            
            cmd = [
                "cartography",
                "--neo4j-uri", self.neo4j_uri,
                "--neo4j-user", self.neo4j_user,
                "--neo4j-password-env-var", "NEO4J_PASSWORD"
            ]
            
            # Add options based on advanced_options
            if advanced_options:
                if use_sample_data:
                    cmd.append("--mock")
                    
                # AWS Sync options
                if not use_sample_data:
                    cmd.append("--aws-sync")
                    
                    # Days of data to sync
                    days = advanced_options.get("days_of_data", 7)
                    cmd.extend(["--days", str(days)])
                
                # DNS collection
                if advanced_options.get("collect_dns", False):
                    cmd.append("--collection-dns")
                
                # GCP collection
                if advanced_options.get("collect_gcp", False):
                    cmd.append("--gcp-sync")
                
                # Okta collection
                if advanced_options.get("collect_okta", False):
                    cmd.append("--okta-sync")
            elif use_sample_data:
                # Default to mock data if use_sample_data is True
                cmd.append("--mock")
            else:
                # Default to AWS sync if not using sample data
                cmd.append("--aws-sync")
            
            logger.info(f"Running cartography with command: {' '.join(cmd)}")
            
            # Run Cartography as a subprocess
            # This runs asynchronously to not block the event loop
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for the process to complete
            stdout, stderr = await process.communicate()
            
            # Check if the process completed successfully
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Cartography completed successfully",
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else ""
                }
            else:
                # If Cartography failed, try to load sample data if use_sample_data is True
                if use_sample_data:
                    logger.warning("Cartography mock mode failed, falling back to sample data load")
                    return await self.run_sample_data_load()
                
                return {
                    "status": "error",
                    "message": "Cartography failed",
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "return_code": process.returncode
                }
                
        except Exception as e:
            logger.error(f"Error running Cartography: {str(e)}", exc_info=True)
            
            # If an exception occurred and we're using sample data, try to load sample data
            if use_sample_data:
                logger.warning("Cartography exception, falling back to sample data load")
                return await self.run_sample_data_load()
            
            return {
                "status": "error",
                "message": f"Error running Cartography: {str(e)}"
            }
    
    async def run_sample_data_load(self) -> Dict[str, Any]:
        """
        Load sample data into Neo4j if Cartography's mock mode fails.
        This is a fallback method that uses direct Cypher queries.
        
        Returns:
            Dictionary with the result of the sample data load
        """
        try:
            # Import Neo4jService here to avoid circular imports
            from app.services.neo4j_service import Neo4jService
            
            # Create a Neo4j service
            neo4j_service = Neo4jService(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password
            )
            
            # Clear existing data
            neo4j_service.execute_query("MATCH (n) DETACH DELETE n")
            
            # Load sample data for AWS account
            neo4j_service.execute_query("""
                CREATE (a:AWSAccount {id: 'sample-account', name: 'Sample AWS Account', accountid: '123456789012'})
                RETURN a
            """)
            
            # Load sample data for VPCs
            neo4j_service.execute_query("""
                MATCH (a:AWSAccount {id: 'sample-account'})
                CREATE (v1:AWSVpc {id: 'vpc-12345', name: 'Production VPC', vpcid: 'vpc-12345', cidr_block: '10.0.0.0/16', region: 'us-east-1'})
                CREATE (v2:AWSVpc {id: 'vpc-67890', name: 'Development VPC', vpcid: 'vpc-67890', cidr_block: '10.1.0.0/16', region: 'us-east-1'})
                CREATE (v1)-[:RESOURCE_OF]->(a)
                CREATE (v2)-[:RESOURCE_OF]->(a)
                RETURN v1, v2
            """)
            
            # Load sample data for EC2 instances
            neo4j_service.execute_query("""
                MATCH (a:AWSAccount {id: 'sample-account'})
                MATCH (v1:AWSVpc {id: 'vpc-12345'})
                MATCH (v2:AWSVpc {id: 'vpc-67890'})
                
                CREATE (i1:EC2Instance {id: 'i-12345', name: 'Web Server', instanceid: 'i-12345', instancetype: 't2.micro', region: 'us-east-1', state: 'running'})
                CREATE (i2:EC2Instance {id: 'i-67890', name: 'Database Server', instanceid: 'i-67890', instancetype: 'm5.large', region: 'us-east-1', state: 'running'})
                CREATE (i3:EC2Instance {id: 'i-abcde', name: 'Dev Server', instanceid: 'i-abcde', instancetype: 't2.medium', region: 'us-east-1', state: 'stopped'})
                
                CREATE (i1)-[:RESOURCE_OF]->(a)
                CREATE (i2)-[:RESOURCE_OF]->(a)
                CREATE (i3)-[:RESOURCE_OF]->(a)
                
                CREATE (i1)-[:PART_OF_VPC]->(v1)
                CREATE (i2)-[:PART_OF_VPC]->(v1)
                CREATE (i3)-[:PART_OF_VPC]->(v2)
                
                RETURN i1, i2, i3
            """)
            
            # Load sample data for security groups
            neo4j_service.execute_query("""
                MATCH (a:AWSAccount {id: 'sample-account'})
                MATCH (v1:AWSVpc {id: 'vpc-12345'})
                MATCH (v2:AWSVpc {id: 'vpc-67890'})
                
                CREATE (sg1:EC2SecurityGroup {id: 'sg-12345', name: 'Web Security Group', groupid: 'sg-12345', description: 'Security group for web servers'})
                CREATE (sg2:EC2SecurityGroup {id: 'sg-67890', name: 'DB Security Group', groupid: 'sg-67890', description: 'Security group for database servers'})
                CREATE (sg3:EC2SecurityGroup {id: 'sg-abcde', name: 'Dev Security Group', groupid: 'sg-abcde', description: 'Security group for development servers'})
                
                CREATE (sg1)-[:RESOURCE_OF]->(a)
                CREATE (sg2)-[:RESOURCE_OF]->(a)
                CREATE (sg3)-[:RESOURCE_OF]->(a)
                
                CREATE (sg1)-[:MEMBER_OF_VPC]->(v1)
                CREATE (sg2)-[:MEMBER_OF_VPC]->(v1)
                CREATE (sg3)-[:MEMBER_OF_VPC]->(v2)
                
                RETURN sg1, sg2, sg3
            """)
            
            # Connect EC2 instances to security groups
            neo4j_service.execute_query("""
                MATCH (i1:EC2Instance {id: 'i-12345'})
                MATCH (i2:EC2Instance {id: 'i-67890'})
                MATCH (i3:EC2Instance {id: 'i-abcde'})
                MATCH (sg1:EC2SecurityGroup {id: 'sg-12345'})
                MATCH (sg2:EC2SecurityGroup {id: 'sg-67890'})
                MATCH (sg3:EC2SecurityGroup {id: 'sg-abcde'})
                
                CREATE (i1)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg1)
                CREATE (i2)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg2)
                CREATE (i3)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg3)
                
                RETURN i1, i2, i3, sg1, sg2, sg3
            """)
            
            # Add inbound rules to security groups
            neo4j_service.execute_query("""
                MATCH (sg1:EC2SecurityGroup {id: 'sg-12345'})
                MATCH (sg2:EC2SecurityGroup {id: 'sg-67890'})
                
                CREATE (r1:EC2SecurityGroupRule {id: 'sgr-12345', ruleid: 'sgr-12345', protocol: 'tcp', fromport: 80, toport: 80, cidr_block: '0.0.0.0/0'})
                CREATE (r2:EC2SecurityGroupRule {id: 'sgr-67890', ruleid: 'sgr-67890', protocol: 'tcp', fromport: 3306, toport: 3306, cidr_block: '10.0.0.0/16'})
                
                CREATE (sg1)-[:HAS_INBOUND_RULE]->(r1)
                CREATE (sg2)-[:HAS_INBOUND_RULE]->(r2)
                
                RETURN r1, r2
            """)
            
            # Create sample S3 buckets
            neo4j_service.execute_query("""
                MATCH (a:AWSAccount {id: 'sample-account'})
                
                CREATE (b1:S3Bucket {id: 's3-12345', name: 'sample-data-bucket', bucketname: 'sample-data-bucket', region: 'us-east-1', created: '2023-01-01'})
                CREATE (b2:S3Bucket {id: 's3-67890', name: 'sample-logs-bucket', bucketname: 'sample-logs-bucket', region: 'us-east-1', created: '2023-01-01'})
                CREATE (b3:S3Bucket {id: 's3-abcde', name: 'sample-public-bucket', bucketname: 'sample-public-bucket', region: 'us-east-1', created: '2023-01-01', public: true})
                
                CREATE (b1)-[:RESOURCE_OF]->(a)
                CREATE (b2)-[:RESOURCE_OF]->(a)
                CREATE (b3)-[:RESOURCE_OF]->(a)
                
                RETURN b1, b2, b3
            """)
            
            # Create IAM roles
            neo4j_service.execute_query("""
                MATCH (a:AWSAccount {id: 'sample-account'})
                
                CREATE (r1:IAMRole {id: 'role-12345', name: 'EC2AdminRole', rolename: 'EC2AdminRole', arn: 'arn:aws:iam::123456789012:role/EC2AdminRole'})
                CREATE (r2:IAMRole {id: 'role-67890', name: 'S3ReadOnlyRole', rolename: 'S3ReadOnlyRole', arn: 'arn:aws:iam::123456789012:role/S3ReadOnlyRole'})
                
                CREATE (r1)-[:RESOURCE_OF]->(a)
                CREATE (r2)-[:RESOURCE_OF]->(a)
                
                RETURN r1, r2
            """)
            
            # Create relationships between EC2 instances and IAM roles
            neo4j_service.execute_query("""
                MATCH (i1:EC2Instance {id: 'i-12345'})
                MATCH (i2:EC2Instance {id: 'i-67890'})
                MATCH (r1:IAMRole {id: 'role-12345'})
                MATCH (r2:IAMRole {id: 'role-67890'})
                
                CREATE (i1)-[:HAS_ROLE]->(r1)
                CREATE (i2)-[:HAS_ROLE]->(r2)
                
                RETURN i1, i2, r1, r2
            """)
            
            # Create IAM policies and attach to roles
            neo4j_service.execute_query("""
                MATCH (r1:IAMRole {id: 'role-12345'})
                MATCH (r2:IAMRole {id: 'role-67890'})
                
                CREATE (p1:IAMPolicy {id: 'policy-12345', name: 'AdminPolicy', policyname: 'AdminPolicy', arn: 'arn:aws:iam::aws:policy/AdministratorAccess'})
                CREATE (p2:IAMPolicy {id: 'policy-67890', name: 'S3ReadOnlyPolicy', policyname: 'S3ReadOnlyPolicy', arn: 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'})
                
                CREATE (r1)-[:HAS_POLICY]->(p1)
                CREATE (r2)-[:HAS_POLICY]->(p2)
                
                RETURN p1, p2
            """)
            
            return {
                "status": "success",
                "message": "Sample data loaded successfully"
            }
            
        except Exception as e:
            logger.error(f"Error loading sample data: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error loading sample data: {str(e)}"
            }