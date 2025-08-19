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
    
    def parse_brief_fields(self, brief: str) -> Dict[str, str]:
        """
        Parse campaign brief to extract structured fields including optional Audience and Channels.
        
        Args:
            brief: The campaign brief string
            
        Returns:
            Dictionary with parsed fields (brand, category, concept, mode, audience, channels)
        """
        logger.info("Parsing brief fields")
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are a campaign brief parser. Extract the following fields from this brief:
- Brand (required)
- Category/Industry (required) 
- Concept (required)
- Mode (required)
- Audience (optional - target demographic/psychographic description)
- Channels (optional - distribution channels, comma-separated)

Return JSON format:
{{
  "brand": "<brand>",
  "category": "<category>", 
  "concept": "<concept>",
  "mode": "<mode>",
  "audience": "<audience or null>",
  "channels": "<channels or null>"
}}

Brief: {brief}"""
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields exist with defaults
            parsed_fields = {
                'brand': result.get('brand', 'Unknown'),
                'category': result.get('category', 'Unknown'),
                'concept': result.get('concept', brief),  # fallback to full brief
                'mode': result.get('mode', 'Unknown'),
                'audience': result.get('audience'),  # Can be None
                'channels': result.get('channels')   # Can be None
            }
            
            logger.info(f"Parsed brief fields - Audience: {'present' if parsed_fields['audience'] else 'not provided'}, Channels: {'present' if parsed_fields['channels'] else 'not provided'}")
            return parsed_fields
            
        except Exception as e:
            logger.error(f"Failed to parse brief fields: {str(e)}")
            # Fallback: return brief as concept with other fields unknown
            return {
                'brand': 'Unknown',
                'category': 'Unknown', 
                'concept': brief,
                'mode': 'Unknown',
                'audience': None,
                'channels': None
            }
    
    def check_audience_channels_specificity(self, audience: Optional[str], channels: Optional[str]) -> Dict[str, Any]:
        """
        Check if audience and channels are sufficiently specific for analysis.
        
        Args:
            audience: The audience field from brief parsing
            channels: The channels field from brief parsing
            
        Returns:
            Dictionary with specificity assessment and clarification question if needed
        """
        logger.info("Checking audience and channels specificity")
        
        try:
            # Build prompt to assess specificity
            assessment_prompt = f"""You are a campaign strategist. Assess whether the following audience and channels information is sufficiently specific for campaign analysis:

Audience: {audience or "Not provided"}
Channels: {channels or "Not provided"}

For each field, determine if it's:
1. Missing (None/null/empty)
2. Too vague (e.g., "general audience", "all platforms", "everyone", "digital")  
3. Sufficiently specific

If either field needs clarification, ask ONE clarification question for the most critical missing piece.

Return JSON:
{{
  "audience_specific": true/false,
  "channels_specific": true/false, 
  "needs_clarification": true/false,
  "clarification_question": "question text or null"
}}"""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": assessment_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Specificity check - Audience: {'specific' if result.get('audience_specific') else 'needs clarification'}, "
                       f"Channels: {'specific' if result.get('channels_specific') else 'needs clarification'}")
            
            return {
                'audience_specific': result.get('audience_specific', True),
                'channels_specific': result.get('channels_specific', True), 
                'needs_clarification': result.get('needs_clarification', False),
                'clarification_question': result.get('clarification_question')
            }
            
        except Exception as e:
            logger.error(f"Failed to check audience/channels specificity: {str(e)}")
            # Default to no clarification needed on error
            return {
                'audience_specific': True,
                'channels_specific': True,
                'needs_clarification': False,
                'clarification_question': None
            }
    
    def get_fallback_source(self, failed_source: str) -> Optional[str]:
        """
        Get fallback source based on predefined hierarchy.
        
        Args:
            failed_source: The source that failed
            
        Returns:
            Fallback source name or None if no fallback available
        """
        fallback_map = {
            'reddit': 'twitter',
            'tiktok': 'instagram', 
            'google_trends': 'semrush'
        }
        
        fallback = fallback_map.get(failed_source)
        if fallback:
            logger.info(f"Fallback routing: {failed_source} → {fallback}")
        
        return fallback
    
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
    
    def get_internal_context(self, brief: str, audience: Optional[str] = None) -> Dict[str, Any]:
        """
        Gather internal LLM context for historical analogies and patterns.
        
        Args:
            brief: The campaign brief string
            audience: Optional audience information to include in context
            
        Returns:
            Dictionary with internal context data
        """
        logger.info("Gathering internal context and analogies")
        
        # Build context string including audience if provided
        context_parts = [f"Campaign Brief: {brief}"]
        
        if audience:
            context_parts.append(f"Target Audience: {audience}")
            logger.info("Including audience information in internal context")
        
        # TODO: Implement internal context gathering
        # - Use OpenAI to find historical analogies
        # - Identify relevant patterns from internal knowledge
        # - Structure context data for analysis
        
        return {
            'context_text': '\n'.join(context_parts),
            'audience_included': bool(audience)
        }
    
    def resilient_external_call(self, source: str, query_text: str = "", attempted_fallback: bool = False) -> Dict[str, Any]:
        """
        Make external API call with resilience loop and fallback routing:
        1. Retry once on failure
        2. Try fallback source if available
        3. Use LLM diagnosis if fallback also fails
        4. Ask for human action if needed
        
        Args:
            source: External API source identifier
            query_text: Query text for the API call
            attempted_fallback: Whether this is already a fallback attempt
            
        Returns:
            Dictionary with call results or error information
        """
        logger.info(f"Making resilient external call to: {source}")
        
        def make_external_call(source_name: str, query: str):
            """Make the actual external API call based on source type."""
            if source_name in ["reddit"]:
                return self.fetch_reddit_posts(query)
            elif source_name in ["twitter", "instagram"]:
                return self.fetch_twitter_sentiment(query)
            elif source_name in ["google_trends", "semrush"]:
                return self.fetch_google_trends(query)
            elif source_name == "tiktok":
                return self.fetch_tiktok_data(query)
            else:
                raise ValueError(f"Unsupported source: {source_name}")
        
        last_error = None
        
        # Try the primary source with retries
        for attempt in range(self.max_retries + 1):
            try:
                result = make_external_call(source, query_text)
                logger.info(f"Successfully retrieved data from {source}")
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"External call attempt {attempt + 1} failed: {last_error}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
        
        # Primary source failed after retries - try fallback if available and not already attempted
        if not attempted_fallback:
            fallback_source = self.get_fallback_source(source)
            if fallback_source:
                logger.info(f"Attempting fallback routing from {source} to {fallback_source}")
                return self.resilient_external_call(fallback_source, query_text, attempted_fallback=True)
        
        # Both primary and fallback failed - use OpenAI suggestion
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"The following external data source returned an error: {last_error}. Suggest a fallback or next-best source for this campaign analysis."
                    }
                ]
            )
            
            fallback_suggestion = response.choices[0].message.content.strip()
            logger.info(f"OpenAI suggested fallback: {fallback_suggestion}")
            
            return {
                'source': source,
                'status': 'failed',
                'error': last_error,
                'fallback_suggestion': fallback_suggestion,
                'attempted_fallback': attempted_fallback
            }
            
        except Exception as openai_error:
            logger.error(f"Failed to get OpenAI fallback suggestion: {str(openai_error)}")
            return {
                'source': source,
                'status': 'failed', 
                'error': last_error,
                'fallback_suggestion': 'Consider using alternative data sources or manual research',
                'attempted_fallback': attempted_fallback
            }
    
    def fetch_reddit_posts(self, query: str) -> Dict[str, Any]:
        """Placeholder for Reddit API integration."""
        # TODO: Implement actual Reddit API call
        raise NotImplementedError("Reddit API integration not yet implemented")
    
    def fetch_twitter_sentiment(self, query: str) -> Dict[str, Any]:
        """Placeholder for Twitter API integration."""
        # TODO: Implement actual Twitter API call
        raise NotImplementedError("Twitter API integration not yet implemented")
    
    def fetch_google_trends(self, query: str) -> Dict[str, Any]:
        """Placeholder for Google Trends API integration."""
        # TODO: Implement actual Google Trends API call
        raise NotImplementedError("Google Trends API integration not yet implemented")
    
    def fetch_tiktok_data(self, query: str) -> Dict[str, Any]:
        """Placeholder for TikTok API integration."""
        # TODO: Implement actual TikTok API call
        raise NotImplementedError("TikTok API integration not yet implemented")
    
    def fetch_twitter_recent_search(self, concept: str, audience: str = "", max_results: int = 50) -> Dict[str, Any]:
        """
        Fetch recent tweets using Twitter API v2 search/recent endpoint.
        
        Args:
            concept: Campaign concept for search query
            audience: Target audience for query refinement
            max_results: Maximum number of results (default 50)
            
        Returns:
            Dictionary with Twitter search results
        """
        # TODO: Implement Twitter API v2 recent search
        # Endpoint: https://api.twitter.com/2/tweets/search/recent
        # Use Bearer Token from config
        # Query should combine concept and audience as keywords
        logger.info(f"Twitter API call - Concept: {concept}, Audience: {audience}")
        raise NotImplementedError("Twitter API v2 integration not yet implemented")
    
    def call_core_llm_panel(self, concept: str, audience: str = "") -> Dict[str, Any]:
        """
        Call Core LLM Evidence Panel (Claude, Perplexity, Gemini, Grok) in parallel.
        
        Args:
            concept: Campaign concept description
            audience: Target audience context
            
        Returns:
            Dictionary with all LLM responses
        """
        logger.info("Calling Core LLM Evidence Panel")
        
        prompt = f"Summarize the current public sentiment and emerging cultural discourse related to the following campaign concept in {audience or 'general'} context, including any key topics, positive/negative sentiment themes, and cultural momentum signals: {concept}"
        
        # TODO: Implement parallel calls to Claude, Perplexity, Gemini, Grok
        # For now, using OpenAI as placeholder for all LLMs
        try:
            responses = {}
            llm_models = ['claude', 'perplexity', 'gemini', 'grok']
            
            for llm in llm_models:
                try:
                    # Placeholder using OpenAI for all LLM calls
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user", 
                                "content": f"[{llm.upper()} SIMULATION] {prompt}"
                            }
                        ]
                    )
                    responses[llm] = response.choices[0].message.content
                    logger.info(f"Successfully called {llm} LLM")
                except Exception as e:
                    logger.error(f"Failed to call {llm}: {str(e)}")
                    responses[llm] = f"Error calling {llm}: {str(e)}"
            
            return {
                'source': 'core_llm_panel',
                'status': 'success',
                'data': responses
            }
            
        except Exception as e:
            logger.error(f"Core LLM panel failed: {str(e)}")
            return {
                'source': 'core_llm_panel',
                'status': 'failed',
                'error': str(e)
            }
    
    def call_specialist_llms(self, concept: str, audience: str = "", category: str = "") -> Dict[str, Any]:
        """
        Call specialist LLMs based on concept/audience criteria.
        
        Args:
            concept: Campaign concept description
            audience: Target audience
            category: Campaign category/industry
            
        Returns:
            Dictionary with specialist LLM responses
        """
        logger.info("Evaluating specialist LLM requirements")
        
        specialist_responses = {}
        
        # Check criteria for specialist LLMs
        concept_lower = concept.lower()
        audience_lower = (audience or "").lower()
        category_lower = (category or "").lower()
        
        try:
            # BloombergGPT for finance/investing
            if any(term in concept_lower or term in category_lower for term in ['finance', 'financial', 'investing', 'investment', 'bank', 'fintech', 'crypto', 'trading']):
                logger.info("Calling BloombergGPT for finance context")
                # TODO: Implement actual BloombergGPT API call
                specialist_responses['bloomberg_gpt'] = "BloombergGPT financial analysis placeholder"
            
            # Aleph Alpha for non-US/multilingual
            if any(term in audience_lower for term in ['international', 'global', 'european', 'asian', 'multilingual', 'non-us']):
                logger.info("Calling Aleph Alpha for international context")
                # TODO: Implement actual Aleph Alpha API call
                specialist_responses['aleph_alpha'] = "Aleph Alpha international analysis placeholder"
            
            # Mistral for non-US youth/Gen-Z
            if any(term in audience_lower for term in ['gen-z', 'genz', 'youth', 'young', 'teen']) and any(term in audience_lower for term in ['international', 'global', 'non-us']):
                logger.info("Calling Mistral for international youth context")
                # TODO: Implement actual Mistral API call
                specialist_responses['mistral'] = "Mistral international youth analysis placeholder"
            
            # GDELT for global news/public policy
            if any(term in concept_lower or term in category_lower for term in ['news', 'policy', 'political', 'government', 'public', 'global', 'world']):
                logger.info("Calling GDELT API for global news context")
                # TODO: Implement actual GDELT API call
                specialist_responses['gdelt'] = "GDELT global news analysis placeholder"
            
            return {
                'source': 'specialist_llms',
                'status': 'success',
                'data': specialist_responses
            }
            
        except Exception as e:
            logger.error(f"Specialist LLMs failed: {str(e)}")
            return {
                'source': 'specialist_llms',
                'status': 'failed',
                'error': str(e)
            }
    
    def gather_comprehensive_evidence(self, concept: str, audience: str = "", category: str = "", mode: str = "real-time") -> Dict[str, Any]:
        """
        # TODO: Re-enable Reddit/TikTok direct calls or replace with Brandwatch API when ready.
        
        Comprehensive evidence gathering using new layered approach.
        
        Args:
            concept: Campaign concept description
            audience: Target audience
            category: Campaign category/industry  
            mode: "real-time" or "historic" analysis mode
            
        Returns:
            Dictionary with aggregated evidence from all sources
        """
        logger.info(f"Starting comprehensive evidence gathering - Mode: {mode}")
        
        evidence_results = {}
        sources_attempted = []
        sources_successful = []
        
        try:
            # 1. Google Trends (always active in both modes)
            logger.info("Gathering Google Trends data")
            sources_attempted.append('google_trends')
            try:
                # Keep existing Google Trends call active
                trends_result = self.fetch_google_trends(concept)
                evidence_results['google_trends'] = trends_result
                sources_successful.append('google_trends')
            except Exception as e:
                logger.info(f"Google Trends call failed (expected): {str(e)}")
                evidence_results['google_trends'] = {'status': 'failed', 'error': str(e)}
            
            # 2. Twitter/X Recent Search (only in Real-Time mode)
            if mode.lower() == "real-time":
                logger.info("Gathering Twitter/X recent search data (Real-Time mode)")
                sources_attempted.append('twitter_recent')
                try:
                    twitter_result = self.fetch_twitter_recent_search(concept, audience)
                    evidence_results['twitter_recent'] = twitter_result
                    sources_successful.append('twitter_recent')
                except Exception as e:
                    logger.info(f"Twitter API call failed (expected): {str(e)}")
                    evidence_results['twitter_recent'] = {'status': 'failed', 'error': str(e)}
            else:
                logger.info("Skipping Twitter/X call (Historic mode)")
            
            # 3. Skip Reddit and TikTok direct API calls
            for skipped_source in ['reddit', 'tiktok']:
                sources_attempted.append(skipped_source)
                logger.info(f"DIRECT_API_CALL_SKIPPED: {skipped_source}")
                evidence_results[skipped_source] = {
                    'status': 'skipped',
                    'message': 'DIRECT_API_CALL_SKIPPED - temporarily disabled'
                }
            
            # 4. Core LLM Evidence Panel (always called in parallel)
            logger.info("Calling Core LLM Evidence Panel")
            sources_attempted.append('core_llm_panel')
            core_llm_result = self.call_core_llm_panel(concept, audience)
            evidence_results['core_llm_panel'] = core_llm_result
            if core_llm_result.get('status') == 'success':
                sources_successful.append('core_llm_panel')
            
            # 5. Conditional Specialist LLMs (sequential after core panel)
            logger.info("Evaluating Specialist LLM requirements")
            sources_attempted.append('specialist_llms')
            specialist_result = self.call_specialist_llms(concept, audience, category)
            evidence_results['specialist_llms'] = specialist_result
            if specialist_result.get('status') == 'success':
                sources_successful.append('specialist_llms')
            
            # 6. Aggregate all evidence into unified string
            unified_evidence = self.aggregate_evidence_to_string(evidence_results)
            
            return {
                'status': 'success',
                'mode': mode,
                'sources_attempted': sources_attempted,
                'sources_successful': sources_successful,
                'evidence_results': evidence_results,
                'unified_evidence': unified_evidence
            }
            
        except Exception as e:
            logger.error(f"Comprehensive evidence gathering failed: {str(e)}")
            return {
                'status': 'failed',
                'mode': mode,
                'sources_attempted': sources_attempted,
                'sources_successful': sources_successful,
                'error': str(e),
                'unified_evidence': "Evidence gathering failed"
            }
    
    def aggregate_evidence_to_string(self, evidence_results: Dict[str, Any]) -> str:
        """
        Aggregate all evidence sources into a single unified evidence string.
        
        Args:
            evidence_results: Dictionary of evidence from all sources
            
        Returns:
            Unified evidence string for scoring/story analysis
        """
        logger.info("Aggregating evidence into unified string")
        
        evidence_sections = []
        
        # Google Trends data
        if 'google_trends' in evidence_results:
            trends = evidence_results['google_trends']
            if trends.get('status') != 'failed':
                evidence_sections.append(f"GOOGLE TRENDS: {str(trends)}")
            else:
                evidence_sections.append("GOOGLE TRENDS: Data unavailable")
        
        # Twitter recent search data
        if 'twitter_recent' in evidence_results:
            twitter = evidence_results['twitter_recent']
            if twitter.get('status') != 'failed':
                evidence_sections.append(f"TWITTER RECENT: {str(twitter)}")
            else:
                evidence_sections.append("TWITTER RECENT: Data unavailable")
        
        # Core LLM Panel responses
        if 'core_llm_panel' in evidence_results:
            core_llms = evidence_results['core_llm_panel']
            if core_llms.get('status') == 'success' and 'data' in core_llms:
                evidence_sections.append("CORE LLM ANALYSIS:")
                for llm, response in core_llms['data'].items():
                    evidence_sections.append(f"  {llm.upper()}: {response}")
            else:
                evidence_sections.append("CORE LLM ANALYSIS: Analysis unavailable")
        
        # Specialist LLM responses
        if 'specialist_llms' in evidence_results:
            specialists = evidence_results['specialist_llms']
            if specialists.get('status') == 'success' and 'data' in specialists and specialists['data']:
                evidence_sections.append("SPECIALIST LLM ANALYSIS:")
                for llm, response in specialists['data'].items():
                    evidence_sections.append(f"  {llm.upper()}: {response}")
        
        # Skipped sources note
        skipped_sources = []
        for source in ['reddit', 'tiktok']:
            if source in evidence_results and evidence_results[source].get('status') == 'skipped':
                skipped_sources.append(source)
        
        if skipped_sources:
            evidence_sections.append(f"NOTE: Direct API calls temporarily disabled for: {', '.join(skipped_sources)}")
        
        unified_evidence = '\n\n'.join(evidence_sections)
        logger.info(f"Created unified evidence string with {len(unified_evidence)} characters")
        
        return unified_evidence
    
    def build_unified_context(self, internal_context: Dict[str, Any], external_results: List[Dict[str, Any]]) -> str:
        """
        Combine internal and external evidence into unified context.
        
        Args:
            internal_context: Internal context string
            external_results: List of external evidence data
            
        Returns:
            Unified context string
        """
        logger.info("Building unified context from internal and external sources")
        
        # Start with internal context
        context_text = internal_context.get('context_text', 'No internal context available') if internal_context else 'No internal context available'
        unified_text = f"INTERNAL CONTEXT:\n{context_text}\n\n"
        
        # Add external evidence
        unified_text += "EXTERNAL EVIDENCE:\n"
        
        if not external_results:
            unified_text += "No external evidence available\n"
        else:
            for i, result in enumerate(external_results, 1):
                if result:
                    source = result.get('source', f'Source {i}')
                    status = result.get('status', 'unknown')
                    
                    if status == 'failed':
                        unified_text += f"{i}. {source.upper()}: Failed to retrieve data\n"
                        if 'fallback_suggestion' in result:
                            unified_text += f"   Fallback suggestion: {result['fallback_suggestion']}\n"
                    else:
                        # For successful results, format the data
                        unified_text += f"{i}. {source.upper()}: "
                        if 'data' in result:
                            unified_text += f"{str(result['data'])}\n"
                        else:
                            unified_text += f"{str(result)}\n"
                    
                    unified_text += "\n"
        
        logger.info(f"Built unified context with {len(unified_text)} characters")
        return unified_text
    
    def evaluate_signal(self, unified_context: str, channels: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate the unified context and produce Signal scores in JSON format.
        
        Args:
            unified_context: The unified context string
            channels: Optional channels information for distribution_fit scoring
            
        Returns:
            Dictionary with Signal scores and metrics
        """
        logger.info("Evaluating Signal scores from unified context")
        
        try:
            # Build scoring prompt based on whether channels are provided
            base_scores = [
                "cultural_fit", "clarity", "emotional_resonance", 
                "differentiation", "conversation_fit", "memorability"
            ]
            
            if channels:
                # Include distribution_fit scoring
                prompt = f"""You are a creative effectiveness analyst.
Using only the following context:

---CONTEXT START---
{unified_context}
---CONTEXT END---

Distribution Channels: {channels}

Evaluate the campaign against the Stonecutter Signal Index.
Return a JSON object with:
{{
  "scores": {{
      "cultural_fit": (0–100),
      "clarity": (0–100),
      "emotional_resonance": (0–100),
      "differentiation": (0–100),
      "conversation_fit": (0–100),
      "memorability": (0–100),
      "distribution_fit": (0–100)
  }},
  "reasoning": "short explanation of why this overall score was given"
}}

Note: 
- conversation_fit measures how well the creative matches environments where people talk about it
- distribution_fit measures how well suited the creative is for the specified distribution channels"""
            else:
                # Exclude distribution_fit scoring
                prompt = f"""You are a creative effectiveness analyst.
Using only the following context:

---CONTEXT START---
{unified_context}
---CONTEXT END---

Evaluate the campaign against the Stonecutter Signal Index.
Return a JSON object with:
{{
  "scores": {{
      "cultural_fit": (0–100),
      "clarity": (0–100),
      "emotional_resonance": (0–100),
      "differentiation": (0–100),
      "conversation_fit": (0–100),
      "memorability": (0–100)
  }},
  "reasoning": "short explanation of why this overall score was given"
}}

Note: conversation_fit measures how well the creative matches environments where people talk about it"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Add distribution_fit note if channels not provided
            if not channels and 'scores' in result:
                result['distribution_fit_note'] = "Distribution Fit not evaluated (channels not provided)"
            
            logger.info("Successfully evaluated Signal scores")
            return result
            
        except Exception as e:
            logger.error(f"Failed to evaluate signal: {str(e)}")
            # Fallback scores
            fallback_scores = {
                "cultural_fit": 50,
                "clarity": 50,
                "emotional_resonance": 50,
                "differentiation": 50,
                "conversation_fit": 50,
                "memorability": 50
            }
            
            fallback_result = {
                "scores": fallback_scores,
                "reasoning": "Unable to evaluate due to error. Default scores provided."
            }
            
            if channels:
                fallback_result["scores"]["distribution_fit"] = 50
            else:
                fallback_result['distribution_fit_note'] = "Distribution Fit not evaluated (channels not provided)"
            
            return fallback_result
    
    def synthesize_story(self, scores: Dict[str, Any], context: str) -> str:
        """
        Generate executive summary "Signal Story" from scores and context.
        
        Args:
            scores: Signal scores and metrics
            context: Unified context string
            
        Returns:
            Executive summary string
        """
        logger.info("Synthesizing Signal Story")
        
        try:
            # Format scores for inclusion in prompt
            scores_text = json.dumps(scores, indent=2)
            
            prompt = f"""You are a narrative strategist.
Write a short, clear executive summary (no more than 200 words) of the campaign's relevance and cultural momentum based on the following scores and supporting context. Use a matter-of-fact tone (professional but real).

SCORES:
{scores_text}

CONTEXT:
{context}"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            story = response.choices[0].message.content.strip()
            logger.info("Successfully synthesized Signal Story")
            return story
            
        except Exception as e:
            logger.error(f"Failed to synthesize story: {str(e)}")
            return "Unable to generate executive summary due to processing error. Please review the scores and context manually."
    
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
        # Step 0: Parse brief fields to extract optional Audience and Channels
        brief_fields = engine.parse_brief_fields(brief)
        audience = brief_fields.get('audience')
        channels = brief_fields.get('channels')
        
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
        
        # Step 3.5: Check if audience/channels need clarification
        specificity_check = engine.check_audience_channels_specificity(audience, channels)
        
        if specificity_check.get('needs_clarification') and specificity_check.get('clarification_question'):
            print(f"\n🤔 {specificity_check['clarification_question']}")
            clarification_response = input("Your answer: ")
            
            # Update the appropriate field based on the clarification
            if not specificity_check.get('audience_specific') and (not audience or audience.lower() in ['general audience', 'everyone', 'all']):
                brief_fields['audience'] = clarification_response
                audience = clarification_response
                logger.info(f"Updated audience with clarification: {audience}")
            elif not specificity_check.get('channels_specific') and (not channels or channels.lower() in ['all platforms', 'digital', 'everywhere']):
                brief_fields['channels'] = clarification_response  
                channels = clarification_response
                logger.info(f"Updated channels with clarification: {channels}")
        
        # Step 4: Select relevant evidence sources
        # TODO: Use cluster and archetype for source selection  
        # TODO: Consider audience field for future source routing improvements
        cluster = classification.get('cluster', '')
        archetype = classification.get('archetype', '')
        sources = engine.select_sources(cluster, archetype)
        
        # Step 5: Gather internal context and analogies
        # TODO: Combine with external evidence
        internal_context = engine.get_internal_context(current_concept, audience)
        
        # Step 6: Comprehensive Evidence Gathering (New Layered Approach)
        # Get category from brief fields for specialist LLM routing
        category = brief_fields.get('category', '')
        
        # Use new comprehensive evidence gathering system
        evidence_data = engine.gather_comprehensive_evidence(
            concept=current_concept,
            audience=audience or "",
            category=category,
            mode="real-time"  # TODO: Allow user to specify mode
        )
        
        # Extract tracking information for final results
        sources_attempted = evidence_data.get('sources_attempted', [])
        sources_successful = evidence_data.get('sources_successful', [])
        
        # Step 7: Build unified context using new evidence approach
        # Combine internal context with unified evidence string
        internal_context_text = internal_context.get('context_text', 'No internal context available')
        unified_evidence_text = evidence_data.get('unified_evidence', 'No evidence available')
        
        unified_context = f"INTERNAL CONTEXT:\n{internal_context_text}\n\nEXTERNAL CULTURAL EVIDENCE:\n{unified_evidence_text}"
        
        # Step 8: Evaluate and score the signal (with channels for distribution_fit)
        signal_scores = engine.evaluate_signal(unified_context, channels)
        
        # Step 9: Synthesize executive summary
        signal_story = engine.synthesize_story(signal_scores, unified_context)
        
        # Print results for immediate review
        print("\n=== SIGNAL SCORES ===")
        print(json.dumps(signal_scores, indent=2))
        print("\n=== SIGNAL STORY ===")
        print(signal_story)
        print("\n=== END ANALYSIS ===")
        
        # Step 10: Validate final output
        # TODO: Ensure JSON compliance and completeness
        final_results = {
            'brief_fields': brief_fields,
            'concepts': concepts,
            'classification': classification,
            'sources_planned': sources,
            'sources_attempted': sources_attempted,
            'sources_successful': sources_successful,
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
    print("=== STONECUTTER SIGNAL ANALYSIS ===")
    print()
    
    # Prompt user for campaign brief input
    user_brief = input("📝 Please paste your full campaign brief (Brand, Category, Concept, Mode, and optionally Audience and Channels): ")
    
    print("\nRunning analysis for your campaign brief...")
    
    result = run_signal_engine(user_brief)
    
    print("\n=== COMPLETE ANALYSIS RESULTS ===")
    print(json.dumps(result, indent=2))
