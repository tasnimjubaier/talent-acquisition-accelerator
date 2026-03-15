"""
Mock DynamoDB Service for Local Development

In-memory database implementation that simulates DynamoDB operations
without AWS costs. Maintains state across operations within a session.

Usage:
    from local_dev.mock_dynamodb import MockDynamoDBResource
    
    dynamodb = MockDynamoDBResource()
    table = dynamodb.Table('talent-acq-candidates')
    table.put_item(Item={'candidateId': 'cand-123', 'name': 'John Doe'})
    item = table.get_item(Key={'candidateId': 'cand-123'})

References:
- 10_data_architecture.md: Database schema
- 17_testing_strategy.md: Local testing approach
"""

from typing import Dict, List, Any, Optional
from copy import deepcopy
import time


class MockTable:
    """Mock DynamoDB Table"""
    
    def __init__(self, table_name: str, storage: Dict[str, Dict]):
        """
        Initialize mock table
        
        Args:
            table_name: Name of the table
            storage: Shared storage dictionary
        """
        self.table_name = table_name
        self.storage = storage
        
        # Initialize table storage if not exists
        if table_name not in self.storage:
            self.storage[table_name] = {}
    
    def put_item(self, Item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Put item into table
        
        Args:
            Item: Item to store
            
        Returns:
            Response dict
        """
        # Determine primary key based on table name
        key_field = self._get_primary_key_field()
        key_value = Item.get(key_field)
        
        if not key_value:
            raise ValueError(f"Item missing primary key field: {key_field}")
        
        # Store item (deep copy to avoid reference issues)
        self.storage[self.table_name][key_value] = deepcopy(Item)
        
        return {
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': f'mock-put-{int(time.time())}'
            }
        }
    
    def get_item(self, Key: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Get item from table
        
        Args:
            Key: Primary key
            
        Returns:
            Response dict with Item if found
        """
        key_field = self._get_primary_key_field()
        key_value = Key.get(key_field)
        
        item = self.storage[self.table_name].get(key_value)
        
        response = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': f'mock-get-{int(time.time())}'
            }
        }
        
        if item:
            response['Item'] = deepcopy(item)
        
        return response
    
    def update_item(
        self,
        Key: Dict[str, Any],
        UpdateExpression: str,
        ExpressionAttributeValues: Dict[str, Any],
        ExpressionAttributeNames: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update item in table
        
        Args:
            Key: Primary key
            UpdateExpression: Update expression
            ExpressionAttributeValues: Values for placeholders
            ExpressionAttributeNames: Names for placeholders
            
        Returns:
            Response dict
        """
        key_field = self._get_primary_key_field()
        key_value = Key.get(key_field)
        
        # Get existing item or create new one
        if key_value not in self.storage[self.table_name]:
            self.storage[self.table_name][key_value] = deepcopy(Key)
        
        item = self.storage[self.table_name][key_value]
        
        # Parse update expression (simplified - handles SET operations)
        if 'SET' in UpdateExpression:
            # Replace attribute name placeholders
            if ExpressionAttributeNames:
                for placeholder, actual_name in ExpressionAttributeNames.items():
                    UpdateExpression = UpdateExpression.replace(placeholder, actual_name)
            
            # Extract SET clause
            set_clause = UpdateExpression.split('SET')[1].strip()
            assignments = [a.strip() for a in set_clause.split(',')]
            
            # Apply updates
            for assignment in assignments:
                if '=' in assignment:
                    attr_name, value_placeholder = assignment.split('=')
                    attr_name = attr_name.strip()
                    value_placeholder = value_placeholder.strip()
                    
                    if value_placeholder in ExpressionAttributeValues:
                        item[attr_name] = ExpressionAttributeValues[value_placeholder]
        
        return {
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': f'mock-update-{int(time.time())}'
            }
        }
    
    def query(
        self,
        KeyConditionExpression: str,
        ExpressionAttributeValues: Dict[str, Any],
        IndexName: Optional[str] = None,
        Limit: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query table
        
        Args:
            KeyConditionExpression: Query condition
            ExpressionAttributeValues: Values for placeholders
            IndexName: Optional index name
            Limit: Optional result limit
            
        Returns:
            Response dict with Items
        """
        # Simple implementation: return all items (can be enhanced)
        items = list(self.storage[self.table_name].values())
        
        # Apply limit if specified
        if Limit:
            items = items[:Limit]
        
        return {
            'Items': deepcopy(items),
            'Count': len(items),
            'ScannedCount': len(items),
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': f'mock-query-{int(time.time())}'
            }
        }

    def scan(self, Limit: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Scan table
        
        Args:
            Limit: Optional result limit
            
        Returns:
            Response dict with Items
        """
        items = list(self.storage[self.table_name].values())
        
        if Limit:
            items = items[:Limit]
        
        return {
            'Items': deepcopy(items),
            'Count': len(items),
            'ScannedCount': len(items),
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': f'mock-scan-{int(time.time())}'
            }
        }
    
    def delete_item(self, Key: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Delete item from table
        
        Args:
            Key: Primary key
            
        Returns:
            Response dict
        """
        key_field = self._get_primary_key_field()
        key_value = Key.get(key_field)
        
        if key_value in self.storage[self.table_name]:
            del self.storage[self.table_name][key_value]
        
        return {
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': f'mock-delete-{int(time.time())}'
            }
        }
    
    def _get_primary_key_field(self) -> str:
        """Get primary key field name based on table name"""
        key_mapping = {
            'talent-acq-candidates': 'candidateId',
            'talent-acq-jobs': 'jobId',
            'talent-acq-interactions': 'interactionId',
            'talent-acq-agent-state': 'stateId'
        }
        return key_mapping.get(self.table_name, 'id')


class MockDynamoDBResource:
    """Mock DynamoDB Resource"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize mock DynamoDB resource
        
        Args:
            region_name: AWS region (ignored in mock)
        """
        self.region_name = region_name
        self.storage: Dict[str, Dict] = {}
    
    def Table(self, table_name: str) -> MockTable:
        """
        Get table instance
        
        Args:
            table_name: Name of the table
            
        Returns:
            MockTable instance
        """
        return MockTable(table_name, self.storage)
    
    def reset(self):
        """Reset all table data (useful for testing)"""
        self.storage.clear()
    
    def get_all_data(self) -> Dict[str, Dict]:
        """Get all stored data (for debugging)"""
        return deepcopy(self.storage)


# Singleton instance
mock_dynamodb_resource = MockDynamoDBResource()


def get_mock_dynamodb_resource(region_name: str = 'us-east-1') -> MockDynamoDBResource:
    """
    Get mock DynamoDB resource instance
    
    Args:
        region_name: AWS region
        
    Returns:
        MockDynamoDBResource instance
    """
    return MockDynamoDBResource(region_name=region_name)
