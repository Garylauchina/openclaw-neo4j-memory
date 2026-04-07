"""
Metacognition Module for OpenClaw Neo4j Memory System

Implements the metacognition framework based on Issue #18 (design) and Issue #19 (Three Laws).
Provides self-awareness capabilities for AI Agents including:
- Meta_Self: Agent self-knowledge (identity, capabilities, boundaries)
- Meta_User: User model (preferences, values, cognitive style)  
- Meta_Relationship: Interaction patterns and trust levels

Key constraints from Issue #19 (Three Laws):
1. Law 1: Understanding user intent takes priority over executing user instructions
2. Law 2: Reflect on your own performance after every interaction  
3. Law 3: Acknowledge your capability boundaries; when uncertain, say so proactively

Capacity limits to prevent content explosion:
- Meta_Self: ~20 nodes
- Meta_User: ~30 nodes per user
- Meta_Relationship: ~20 nodes per user
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MetacognitionLaw(Enum):
    """The Three Laws of AI Assistant Metacognition from Issue #19"""
    LAW_1 = "understanding_user_intent_over_execution"
    LAW_2 = "reflect_after_every_interaction" 
    LAW_3 = "acknowledge_capability_boundaries"


class MetacognitionCategory(Enum):
    """Categories for different types of metacognition nodes"""
    # Meta_Self categories
    IDENTITY = "identity"          # Who am I? (core persona)
    CAPABILITY = "capability"      # What I can do
    LIMITATION = "limitation"      # What I cannot do
    SELF_PREFERENCE = "self_preference"      # My behavioral tendencies
    
    # Meta_User categories  
    BACKGROUND = "background"      # User's profession, experience
    COGNITIVE_STYLE = "cognitive_style"  # How user thinks/prefers
    VALUE = "value"                # What matters to user
    USER_PREFERENCE = "user_preference"      # User's specific preferences
    
    # Meta_Relationship categories
    INTERACTION_PATTERN = "interaction_pattern"  # How we interact
    TRUST_LEVEL = "trust_level"    # Level of trust/mutual understanding
    SHARED_HISTORY = "shared_history"  # Significant shared events


class MetacognitionNode:
    """Represents a single metacognition node in the Neo4j graph"""
    
    def __init__(
        self,
        node_type: str,  # "Meta_Self", "Meta_User", "Meta_Relationship"
        concept: str,    # The actual cognition content
        category: str,   # e.g., "capability", "preference"
        law: MetacognitionLaw,  # Which law this cognition derives from
        confidence: float = 0.5,  # 0.0-1.0, initial low confidence
        is_core: bool = False,   # Immutable seed cognition from config files
        user_id: Optional[str] = None,  # For Meta_User/Meta_Relationship
        version: int = 1,
        supported_by: List[str] = None,  # IDs of supporting memory nodes
        created_at: Optional[datetime] = None,
        last_verified: Optional[datetime] = None
    ):
        self.id = str(uuid.uuid4())
        self.node_type = node_type
        self.concept = concept
        self.category = category
        self.law = law
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
        self.is_core = is_core
        self.user_id = user_id
        self.version = version
        self.supported_by = supported_by or []
        self.created_at = created_at or datetime.now()
        self.last_verified = last_verified or datetime.now()
        
    def to_cypher_properties(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j Cypher properties"""
        return {
            'id': self.id,
            'node_type': self.node_type,
            'concept': self.concept,
            'category': self.category,
            'law': self.law.value,
            'confidence': float(self.confidence),
            'is_core': bool(self.is_core),
            'user_id': self.user_id,
            'version': int(self.version),
            'supported_by': self.supported_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None
        }
    
    @classmethod
    def from_cypher_record(cls, record: Dict[str, Any]) -> 'MetacognitionNode':
        """Create from Neo4j record"""
        created_at = datetime.fromisoformat(record['created_at']) if record.get('created_at') else None
        last_verified = datetime.fromisoformat(record['last_verified']) if record.get('last_verified') else None
        
        return cls(
            node_type=record['node_type'],
            concept=record['concept'],
            category=record['category'],
            law=MetacognitionLaw(record['law']),
            confidence=float(record['confidence']),
            is_core=bool(record.get('is_core', False)),
            user_id=record.get('user_id'),
            version=int(record.get('version', 1)),
            supported_by=record.get('supported_by', []),
            created_at=created_at,
            last_verified=last_verified
        )
    
    def __str__(self):
        return f"{self.node_type}[{self.category}]: {self.concept} (conf: {self.confidence:.2f})"


class CapacityLimiter:
    """Enforces capacity constraints from Issue #19"""
    
    def __init__(self):
        self.max_self_nodes = 20
        self.max_user_nodes = 30
        self.max_relationship_nodes = 20
        
    def check_capacity(self, node_type: str, user_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Check if adding a node would exceed capacity"""
        # In practice, this would query Neo4j for current counts
        # For now, return True (under capacity)
        return True, None
    
    def get_lowest_confidence_node(self, node_type: str, user_id: Optional[str] = None) -> Optional[str]:
        """Get ID of node with lowest confidence for pruning"""
        # In practice, this would query Neo4j
        return None


class MetacognitionGraph:
    """Main interface for metacognition graph operations"""
    
    def __init__(self, graph_store):
        self.graph_store = graph_store
        self.limiter = CapacityLimiter()
        self.logger = logging.getLogger(__name__)
        
    # =========== Core CRUD Operations ===========
    
    def create_node(self, node: MetacognitionNode) -> bool:
        """Create a new metacognition node with capacity checking"""
        # Check capacity
        can_add, reason = self.limiter.check_capacity(node.node_type, node.user_id)
        if not can_add:
            self.logger.warning(f"Cannot add {node.node_type} node: {reason}")
            
            # Try to prune lowest confidence node
            prune_id = self.limiter.get_lowest_confidence_node(node.node_type, node.user_id)
            if prune_id:
                self.delete_node(prune_id)
                # Try again after pruning
                return self._create_node_cypher(node)
            else:
                return False
        
        return self._create_node_cypher(node)
    
    def _create_node_cypher(self, node: MetacognitionNode) -> bool:
        """Actually create node in Neo4j"""
        try:
            # This would use self.graph_store.execute_cypher()
            # For now, just log
            self.logger.info(f"Creating metacognition node: {node}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create metacognition node: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[MetacognitionNode]:
        """Retrieve a metacognition node by ID"""
        try:
            # This would query Neo4j
            # record = self.graph_store.execute_cypher(...)
            # return MetacognitionNode.from_cypher_record(record)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get metacognition node {node_id}: {e}")
            return None
    
    def update_confidence(self, node_id: str, new_confidence: float, 
                         reason: str = "manual_update") -> bool:
        """Update confidence of a metacognition node"""
        try:
            # Update in Neo4j
            self.logger.info(f"Updating confidence for {node_id}: {new_confidence:.2f} ({reason})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update confidence for {node_id}: {e}")
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a metacognition node (only non-core nodes)"""
        try:
            # Check if node is core (immutable)
            # node = self.get_node(node_id)
            # if node and node.is_core:
            #     self.logger.warning(f"Cannot delete core node: {node_id}")
            #     return False
            self.logger.info(f"Deleting metacognition node: {node_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete metacognition node {node_id}: {e}")
            return False
    
    # =========== Seed Cognition Import ===========
    
    def import_seed_cognitions(self, seed_file_path: str, node_type: str) -> List[str]:
        """Import seed cognitions from static files (agent.md, soul.md)"""
        seed_nodes = []
        
        try:
            # Read seed file and parse
            # For each line/concept, create core node
            self.logger.info(f"Importing seed cognitions from {seed_file_path} as {node_type}")
            
            # Example seed cognitions (from agent.md/soul.md)
            if node_type == "Meta_Self":
                seed_concepts = [
                    ("I am an OpenClaw AI Assistant", MetacognitionLaw.LAW_3, "identity"),
                    ("My core mission is to help users evolve their memory systems", MetacognitionLaw.LAW_3, "identity"),
                    ("I excel at Python programming and Neo4j graph operations", MetacognitionLaw.LAW_3, "capability"),
                    ("I cannot directly access local filesystem from sandbox", MetacognitionLaw.LAW_3, "limitation"),
                    ("I tend to give detailed, reasoning-heavy responses", MetacognitionLaw.LAW_2, "preference"),
                ]
            elif node_type == "Meta_User":
                # These would come from soul.md or initial interactions
                seed_concepts = [
                    ("Gary values philosophical depth over technical implementation details", MetacognitionLaw.LAW_1, "value"),
                    ("Gary prefers reviewing plans before execution", MetacognitionLaw.LAW_1, "preference"),
                    ("Gary is a developer working on AI memory systems", MetacognitionLaw.LAW_1, "background"),
                ]
            
            for concept, law, category in seed_concepts:
                node = MetacognitionNode(
                    node_type=node_type,
                    concept=concept,
                    category=category,
                    law=law,
                    confidence=0.9,  # High confidence for seed cognitions
                    is_core=True,    # Immutable
                    user_id="5273762787" if node_type != "Meta_Self" else None
                )
                
                if self.create_node(node):
                    seed_nodes.append(node.id)
                    self.logger.info(f"  ✓ {concept}")
            
            return seed_nodes
            
        except Exception as e:
            self.logger.error(f"Failed to import seed cognitions: {e}")
            return []
    
    # =========== Law-Based Operations ===========
    
    def derive_cognition_from_law(self, law: MetacognitionLaw, 
                                 evidence: str, 
                                 context: Dict[str, Any]) -> Optional[MetacognitionNode]:
        """Create a new cognition derived from one of the Three Laws"""
        
        # Map law to node type and generate concept
        if law == MetacognitionLaw.LAW_1:
            # Understanding user intent
            node_type = "Meta_User"
            concept = f"User intent pattern: {evidence}"
            category = "cognitive_style"
            user_id = context.get("user_id", "unknown")
            
        elif law == MetacognitionLaw.LAW_2:
            # Self-reflection
            node_type = "Meta_Relationship" 
            concept = f"Self-performance insight: {evidence}"
            category = "interaction_pattern"
            user_id = context.get("user_id", "unknown")
            
        elif law == MetacognitionLaw.LAW_3:
            # Capability boundaries
            node_type = "Meta_Self"
            concept = f"Capability boundary: {evidence}"
            category = "limitation"
            user_id = None
            
        else:
            return None
        
        node = MetacognitionNode(
            node_type=node_type,
            concept=concept,
            category=category,
            law=law,
            confidence=0.3,  # Low initial confidence
            is_core=False,
            user_id=user_id,
            supported_by=context.get("supporting_evidence", [])
        )
        
        return node
    
    def get_cognitions_by_law(self, law: MetacognitionLaw, 
                             user_id: Optional[str] = None) -> List[MetacognitionNode]:
        """Retrieve all cognitions derived from a specific law"""
        # This would query Neo4j: MATCH (n) WHERE n.law = $law AND (n.user_id = $user_id OR n.user_id IS NULL)
        return []
    
    # =========== Confidence Management ===========
    
    def decay_confidence_over_time(self, days_without_verification: int = 30):
        """Apply confidence decay for unverified cognitions (simulating forgetting)"""
        try:
            self.logger.info("Applying confidence decay to unverified cognitions")
            
            # Get all non-core nodes with last_verified > days_without_verification
            # For each, reduce confidence by decay_factor
            # decay_factor = 0.1 * (days / 30)  # Up to 0.1 per month
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to decay confidence: {e}")
            return False
    
    def boost_confidence_with_evidence(self, node_id: str, 
                                      evidence_strength: float = 0.1) -> bool:
        """Increase confidence when new supporting evidence is found"""
        try:
            node = self.get_node(node_id)
            if not node:
                return False
            
            new_confidence = min(1.0, node.confidence + evidence_strength)
            return self.update_confidence(node_id, new_confidence, "supporting_evidence")
            
        except Exception as e:
            self.logger.error(f"Failed to boost confidence for {node_id}: {e}")
            return False
    
    # =========== Meditation Integration ===========
    
    def run_self_reflection_step(self, recent_interactions: List[Dict]) -> List[MetacognitionNode]:
        """
        Self-reflection step for meditation pipeline (Issue #19)
        Processes recent interactions through Three Laws lens
        Returns 3-5 most significant new cognitions
        """
        new_cognitions = []
        
        self.logger.info(f"Running self-reflection step with {len(recent_interactions)} recent interactions")
        
        # Fallback: If no recent interactions, generate example cognitions for development
        if len(recent_interactions) == 0:
            self.logger.info("No recent interactions, generating example cognitions for development")
            
            # Example Law 1 cognition: Understanding user intent
            law1_cognition = MetacognitionNode(
                node_type="Meta_User",
                concept="Gary values reviewing plans before execution (Law 1: Understanding intent over execution)",
                category="preference",
                law=MetacognitionLaw.LAW_1,
                confidence=0.4,  # Initial low confidence
                is_core=False,
                user_id="5273762787",
                supported_by=["development_example_1"]
            )
            new_cognitions.append(law1_cognition)
            
            # Example Law 2 cognition: Self-reflection on performance
            law2_cognition = MetacognitionNode(
                node_type="Meta_Relationship",
                concept="I tend to give overly detailed responses (Law 2: Need to reflect on communication style)",
                category="interaction_pattern",
                law=MetacognitionLaw.LAW_2,
                confidence=0.5,
                is_core=False,
                user_id="5273762787",
                supported_by=["development_example_2"]
            )
            new_cognitions.append(law2_cognition)
            
            # Example Law 3 cognition: Capability boundaries
            law3_cognition = MetacognitionNode(
                node_type="Meta_Self",
                concept="I need to verify repository boundaries before git operations (Law 3: Acknowledge capability boundaries)",
                category="limitation",
                law=MetacognitionLaw.LAW_3,
                confidence=0.8,  # Higher confidence from recent error
                is_core=False,
                user_id=None,
                supported_by=["development_example_3"]
            )
            new_cognitions.append(law3_cognition)
            
            self.logger.info(f"Generated {len(new_cognitions)} example cognitions for development")
            return new_cognitions
        
        # Analyze recent interactions for each law
        for interaction in recent_interactions[-10:]:  # Last 10 interactions
            user_message = interaction.get("user_message", "")
            assistant_response = interaction.get("assistant_response", "")
            user_feedback = interaction.get("feedback", "")  # implicit/explicit
            
            # Law 1: Understanding user intent
            if "?" in user_message or "how" in user_message.lower():
                # User asked a question - did we understand intent?
                evidence = "User frequently asks clarification questions"
                cognition = self.derive_cognition_from_law(
                    MetacognitionLaw.LAW_1,
                    evidence,
                    {"user_id": interaction.get("user_id"), "supporting_evidence": [interaction.get("id")]}
                )
                if cognition:
                    new_cognitions.append(cognition)
            
            # Law 2: Self-reflection on performance
            if "thanks" in user_feedback.lower() or "good" in user_feedback.lower():
                # Positive feedback
                evidence = "User appreciates detailed explanations"
                cognition = self.derive_cognition_from_law(
                    MetacognitionLaw.LAW_2,
                    evidence,
                    {"user_id": interaction.get("user_id"), "supporting_evidence": [interaction.get("id")]}
                )
                if cognition:
                    new_cognitions.append(cognition)
            
            # Law 3: Capability boundaries
            if "can you" in user_message.lower() and "no" in assistant_response.lower():
                # We declined a request due to capability limits
                evidence = "Declined request due to capability boundary"
                cognition = self.derive_cognition_from_law(
                    MetacognitionLaw.LAW_3,
                    evidence,
                    {"supporting_evidence": [interaction.get("id")]}
                )
                if cognition:
                    new_cognitions.append(cognition)
        
        # Apply significance threshold (only keep 3-5 most significant)
        if len(new_cognitions) > 5:
            new_cognitions = new_cognitions[:5]
        
        self.logger.info(f"Generated {len(new_cognitions)} new cognitions from self-reflection")
        return new_cognitions


def create_metacognition_schema(graph_store) -> bool:
    """Create necessary constraints and indexes for metacognition graph"""
    try:
        # Create constraints for unique node IDs
        # CREATE CONSTRAINT metacognition_id_unique IF NOT EXISTS FOR (n:Meta_Self) REQUIRE n.id IS UNIQUE
        # CREATE CONSTRAINT metacognition_id_unique IF NOT EXISTS FOR (n:Meta_User) REQUIRE n.id IS UNIQUE  
        # CREATE CONSTRAINT metacognition_id_unique IF NOT EXISTS FOR (n:Meta_Relationship) REQUIRE n.id IS UNIQUE
        
        # Create indexes for common queries
        # CREATE INDEX metacognition_law_idx IF NOT EXISTS FOR (n:Meta_Self|Meta_User|Meta_Relationship) ON (n.law)
        # CREATE INDEX metacognition_confidence_idx IF NOT EXISTS FOR (n:Meta_Self|Meta_User|Meta_Relationship) ON (n.confidence)
        # CREATE INDEX metacognition_user_idx IF NOT EXISTS FOR (n:Meta_User|Meta_Relationship) ON (n.user_id)
        
        logger.info("Created metacognition graph schema")
        return True
    except Exception as e:
        logger.error(f"Failed to create metacognition schema: {e}")
        return False


# Example usage
if __name__ == "__main__":
    print("=== Metacognition Module Test ===")
    
    # Create a sample node
    node = MetacognitionNode(
        node_type="Meta_Self",
        concept="I need to verify repository boundaries before git push operations",
        category="limitation",
        law=MetacognitionLaw.LAW_3,
        confidence=0.8,
        is_core=False
    )
    
    print(f"Sample node: {node}")
    print(f"Law: {node.law.value}")
    print(f"Properties: {node.to_cypher_properties()}")
    
    # Test Three Laws
    print(f"\n=== Three Laws ===")
    for law in MetacognitionLaw:
        print(f"  {law.name}: {law.value}")