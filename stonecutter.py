"""
Stonecutter Signal - AI-powered diagnostic analysis engine for campaign briefs.

This script orchestrates the analysis flow using OpenAI GPT for reasoning
while maintaining proprietary orchestration logic in Python.
"""

import json
import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class StonecutterSignal:
    """Main class for Stonecutter Signal diagnostic analysis engine."""
    
    def __init__(self):
        self.max_retries = 1
        self.retry_delay = 2
    
    def separate_concepts(self, brief: str) -> List[str]:
        """
        Analyze campaign brief and detect if multiple concepts exist.
        Split them if needed using OpenAI analysis.
        
        Args:
            brief: The campaign brief string
            
        Returns:
            List of separated concept strings
        """
        logger.info("Separating concepts from brief")
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a campaign analysis assistant. Does the following brief contain more than one distinctly different campaign concept? If yes, output a JSON list of the split concepts. If no, output a JSON list with a single element.\n\nBrief: {brief}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Handle different possible JSON structures
            if isinstance(result, list):
                concepts = result
            elif isinstance(result, dict) and 'concepts' in result:
                concepts = result['concepts']
            else:
                # Fallback: assume single concept
                concepts = [brief]
            
            logger.info(f"Separated {len(concepts)} concept(s)")
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to separate concepts: {str(e)}")
            # Fallback to original brief as single concept
            return [brief]
    
    def brand_clarification_prompt(self, brief: str) -> Dict[str, Any]:
        """
        Check if brand/context information is sufficient.
        Generate clarification questions if needed.
        
        Args:
            brief: The campaign brief string
            
        Returns:
            Dictionary with clarification status and questions if needed
        """
        logger.info("Checking brand context clarity")
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a senior brand strategist. Please assess whether the following campaign brief includes sufficient understanding of the brand (values, audience, positioning). If not, ask one clarification question. If yes, return 'OK'.\n\nBrief: {brief}"
                    }
                ]
            )
            
            result = response.choices[0].message.content.strip()
            
            if result.upper() == 'OK':
                return {
                    'status': 'sufficient',
                    'message': 'Brand context is sufficient',
                    'clarification_needed': False
                }
            else:
                return {
                    'status': 'needs_clarification',
                    'message': result,
                    'clarification_needed': True
                }
                
        except Exception as e:
            logger.error(f"Failed to assess brand clarity: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error assessing brand context: {str(e)}',
                'clarification_needed': False
            }
    
    def classify_concept_and_archetype(self, brief: str) -> Dict[str, str]:
        """
        Classify the concept into cluster and cultural archetype using OpenAI.
        
        Args:
            brief: The campaign brief string
            
        Returns:
            Dictionary with cluster and archetype classifications
        """
        logger.info("Classifying concept and archetype")
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a cultural strategist. Classify the following campaign concept into (1) concept cluster (e.g. 'product benefit', 'purpose-led', 'social commentary', 'innovation showcase', etc.), and (2) cultural archetype (e.g. 'challenger', 'humanist', 'magician', 'sage', etc.). Output as JSON:\n{{\n  \"cluster\": \"<cluster>\",\n  \"archetype\": \"<archetype>\"\n}}\n\nConcept: {brief}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            classification = {
                'cluster': result.get('cluster', 'unknown'),
                'archetype': result.get('archetype', 'unknown')
            }
            
            logger.info(f"Classified as cluster: {classification['cluster']}, archetype: {classification['archetype']}")
            return classification
            
        except Exception as e:
            logger.error(f"Failed to classify concept and archetype: {str(e)}")
            # Fallback classification
            return {
                'cluster': 'unknown',
                'archetype': 'unknown'
            }
    
    def select_sources(self, cluster: str, archetype: str) -> List[str]:
        """
        Select the top 3 most relevant evidence sources based on classification.
        
        Args:
            cluster: The concept cluster classification
            archetype: The cultural archetype classification
            
        Returns:
            List of top 3 evidence source identifiers
        """
        logger.info(f"Selecting evidence sources for cluster: {cluster}, archetype: {archetype}")
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"You are an insight strategist. Given the cluster = {cluster} and archetype = {archetype}, list the three best evidence sources (e.g. \"reddit\", \"twitter\", \"tiktok\", \"google_trends\", \"meta_ad_library\", \"news\"). Return them as a JSON list of strings, e.g. [\"reddit\",\"twitter\",\"google_trends\"]. Do not include explanations or extra text."
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Handle different possible JSON structures
            if isinstance(result, list):
                sources = result
            elif isinstance(result, dict) and 'sources' in result:
                sources = result['sources']
            elif isinstance(result, dict):
                # Try to find a list in any key
                for key, value in result.items():
                    if isinstance(value, list):
                        sources = value
                        break
                else:
                    sources = ['reddit', 'twitter', 'google_trends']  # fallback
            else:
                sources = ['reddit', 'twitter', 'google_trends']  # fallback
            
            # Ensure we have exactly 3 sources
            sources = sources[:3]  # Take first 3
            while len(sources) < 3:
                fallback_sources = ['reddit', 'twitter', 'google_trends', 'news', 'tiktok']
                for fallback in fallback_sources:
                    if fallback not in sources:
                        sources.append(fallback)
                        break
                if len(sources) >= 3:
                    break
            
            logger.info(f"Selected evidence sources: {sources}")
            return sources
            
        except Exception as e:
            logger.error(f"Failed to select sources: {str(e)}")
            # Fallback sources
            return ['reddit', 'twitter', 'google_trends']
    
    def get_internal_context(self, brief: str) -> Dict[str, Any]:
        """
        Gather internal LLM context for historical analogies and patterns.
        
        Args:
            brief: The campaign brief string
            
        Returns:
            Dictionary with internal context data
        """
        # TODO: Implement internal context gathering
        # - Use OpenAI to find historical analogies
        # - Identify relevant patterns from internal knowledge
        # - Structure context data for analysis
        logger.info("Gathering internal context and analogies")
        pass
    
    def resilient_external_call(self, source: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make external API call with resilience loop:
        1. Retry once on failure
        2. Use LLM diagnosis if retry fails
        3. Ask for human action if needed
        
        Args:
            source: External API source identifier
            params: Parameters for the API call
            
        Returns:
            Dictionary with call results or error information
        """
        # TODO: Implement resilient external call logic
        # - Attempt initial API call
        # - Implement retry mechanism with delay
        # - Use OpenAI to diagnose failures
        # - Structure response for human intervention if needed
        logger.info(f"Making resilient external call to: {source}")
        
        for attempt in range(self.max_retries + 1):
            try:
                # TODO: Implement actual external API call
                # Based on source parameter, call appropriate external API
                # Handle authentication, parameters, and response processing
                pass
            except Exception as e:
                logger.warning(f"External call attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    # TODO: Use OpenAI to diagnose the failure
                    # Generate human-readable error explanation
                    # Return structured error response
                    pass
        pass
    
    def build_unified_context(self, internal: Dict[str, Any], external: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine internal and external evidence into unified context.
        
        Args:
            internal: Internal context data
            external: List of external evidence data
            
        Returns:
            Unified context dictionary
        """
        # TODO: Implement context unification logic
        # - Merge internal and external data sources
        # - Resolve conflicts and inconsistencies using OpenAI
        # - Create structured unified context
        logger.info("Building unified context from internal and external sources")
        pass
    
    def evaluate_signal(self, unified_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the unified context and produce Signal scores in JSON format.
        
        Args:
            unified_context: The unified context data
            
        Returns:
            Dictionary with Signal scores and metrics
        """
        # TODO: Implement signal evaluation logic
        # - Use OpenAI to analyze unified context
        # - Generate quantitative Signal scores
        # - Validate and structure JSON output
        logger.info("Evaluating Signal scores from unified context")
        pass
    
    def synthesize_story(self, scores: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Generate executive summary "Signal Story" from scores and context.
        
        Args:
            scores: Signal scores and metrics
            context: Unified context data
            
        Returns:
            Executive summary string
        """
        # TODO: Implement story synthesis logic
        # - Use OpenAI to create narrative summary
        # - Integrate key insights and scores
        # - Generate executive-level communication
        logger.info("Synthesizing Signal Story")
        pass
    
    def validate_and_reformat_json(self, json_data: str) -> Dict[str, Any]:
        """
        Validate JSON output and reformat via LLM if malformed.
        
        Args:
            json_data: JSON string to validate
            
        Returns:
            Valid JSON dictionary
        """
        # TODO: Implement JSON validation and reformatting
        # - Attempt to parse JSON
        # - Use OpenAI to fix malformed JSON if needed
        # - Return validated dictionary
        logger.info("Validating and reformatting JSON output")
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON validation failed: {str(e)}")
            # TODO: Use OpenAI to fix malformed JSON
            pass
    
    # Future expansion hooks - leave as pass for now
    def run_owned_data_ingest(self, data_source: str) -> Dict[str, Any]:
        """Future hook for owned data ingestion capabilities."""
        logger.info("Future hook: Owned data ingest")
        pass
    
    def run_multi_concept_scenario_analysis(self, concepts: List[str]) -> Dict[str, Any]:
        """Future hook for multi-concept scenario analysis."""
        logger.info("Future hook: Multi-concept scenario analysis")
        pass
    
    def run_cultural_archetype_reframe(self, archetype: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Future hook for cultural archetype reframing."""
        logger.info("Future hook: Cultural archetype reframing")
        pass


def run_signal_engine(brief: str) -> Dict[str, Any]:
    """
    Main execution flow for Stonecutter Signal analysis.
    
    Args:
        brief: The campaign brief to analyze
        
    Returns:
        Complete analysis results including scores and story
    """
    logger.info("Starting Stonecutter Signal analysis")
    
    # Initialize the engine
    engine = StonecutterSignal()
    
    try:
        # Step 1: Separate concepts if multiple exist
        # TODO: Handle multiple concepts by processing each separately
        concepts = engine.separate_concepts(brief)
        logger.info(f"Identified {len(concepts)} concept(s)")
        
        # For now, process the first concept (TODO: handle multiple concepts)
        current_concept = concepts[0] if concepts else brief
        
        # Step 2: Check and clarify brand context
        # TODO: Loop back for clarification if needed
        clarification = engine.brand_clarification_prompt(current_concept)
        
        # Step 3: Classify concept and determine archetype
        # TODO: Use classification results to guide analysis
        classification = engine.classify_concept_and_archetype(current_concept)
        
        # Step 4: Select relevant evidence sources
        # TODO: Use cluster and archetype for source selection
        cluster = classification.get('cluster', '')
        archetype = classification.get('archetype', '')
        sources = engine.select_sources(cluster, archetype)
        
        # Step 5: Gather internal context and analogies
        # TODO: Combine with external evidence
        internal_context = engine.get_internal_context(current_concept)
        
        # Step 6: Collect external evidence with resilience
        # TODO: Gather evidence from all selected sources
        external_evidence = []
        for source in sources:
            try:
                evidence = engine.resilient_external_call(source)
                external_evidence.append(evidence)
            except Exception as e:
                logger.error(f"Failed to gather evidence from {source}: {str(e)}")
        
        # Step 7: Build unified context
        # TODO: Merge internal and external data effectively
        unified_context = engine.build_unified_context(internal_context, external_evidence)
        
        # Step 8: Evaluate and score the signal
        # TODO: Generate comprehensive scoring metrics
        signal_scores = engine.evaluate_signal(unified_context)
        
        # Step 9: Synthesize executive summary
        # TODO: Create compelling narrative summary
        signal_story = engine.synthesize_story(signal_scores, unified_context)
        
        # Step 10: Validate final output
        # TODO: Ensure JSON compliance and completeness
        final_results = {
            'concepts': concepts,
            'classification': classification,
            'sources_used': sources,
            'signal_scores': signal_scores,
            'signal_story': signal_story,
            'timestamp': time.time(),
            'status': 'success'
        }
        
        # Validate JSON structure
        validated_results = engine.validate_and_reformat_json(json.dumps(final_results))
        
        logger.info("Stonecutter Signal analysis completed successfully")
        return validated_results
        
    except Exception as e:
        logger.error(f"Signal analysis failed: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e),
            'timestamp': time.time()
        }


if __name__ == "__main__":
    # Example usage - remove in production
    sample_brief = "Brand: TechCorp, Industry: Software, Concept: AI-powered productivity suite"
    results = run_signal_engine(sample_brief)
    print(json.dumps(results, indent=2))
