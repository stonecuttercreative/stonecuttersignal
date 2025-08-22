# Replit.md

## Overview

Stonecutter Signal is an AI-powered diagnostic analysis engine designed to analyze campaign briefs and generate strategic insights. The system processes marketing campaign briefs containing brand, industry, and concept information, then performs multi-step analysis to produce diagnostic scores and executive summaries. The engine uses OpenAI's GPT models for reasoning while maintaining proprietary orchestration logic in Python, creating a hybrid approach that combines external AI capabilities with internal business logic.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Engine Design
The system follows a pipeline architecture with sequential processing steps, each handling a specific aspect of campaign brief analysis. The main orchestration happens in Python (`StonecutterSignal` class) while leveraging OpenAI API calls for reasoning tasks.

### Processing Pipeline
- **Brief Parsing**: Extracts structured fields including optional Audience and Channels information
- **Concept Separation**: Detects and splits multiple concepts within a single brief
- **Brand Clarification**: Enhances insufficient brand/context information
- **Classification**: Categorizes concepts using cluster and cultural archetype frameworks
- **Audience/Channels Clarification**: Interactive check for specificity of targeting and distribution fields
- **Evidence Selection**: Identifies the top 3 most relevant evidence sources
- **Data Gathering**: Combines historical data with real-time evidence from external APIs
- **Context Building**: Merges internal LLM context with external data sources (includes audience targeting)
- **Signal Evaluation**: Produces diagnostic scores in JSON format with conditional distribution_fit scoring
- **Story Synthesis**: Generates executive summaries based on scores and context

### Resilience Mechanisms
The system implements a robust error handling pattern for all external calls:
1. Initial attempt with single retry
2. LLM-powered diagnosis of failures
3. Human intervention request when automated recovery fails
4. JSON validation with LLM-based reformatting for malformed responses

### Hybrid AI Architecture
The design separates concerns between external AI reasoning and internal business logic. The system now supports multiple LLM providers (OpenAI, Claude, Gemini, Grok, Perplexity, Mistral) with automatic arbitration of responses. Python manages workflow orchestration, data integration, provider coordination, and error handling. When multiple providers are available, their responses are weighted and combined for improved reliability and consensus scoring.

### Extensibility Framework
The architecture includes placeholder hooks for future enhancements:
- Owned data ingestion capabilities
- Multi-concept scenario analysis
- Cultural archetype reframing functionality
- Real API integration for providers (currently using mock responses with deterministic scoring)
- Custom provider weight optimization based on historical performance
- Advanced consensus algorithms beyond simple weighted medians

## Recent Updates (August 2025)

### Enhanced Dashboard with Comprehensive Visualizations (Latest)
- **Six Interactive Charts**: Time-series, provider latency, participation pie, distribution histogram, radar, and activity heatmap
- **Real-time Metrics Endpoints**: REST API endpoints for `/metrics/timeseries`, `/metrics/providers`, `/metrics/distribution`, `/metrics/latest`, `/metrics/activity`
- **Chart.js Integration**: Professional visualizations with proper colors, legends, and responsive design
- **Comprehensive Analytics**: Signal strength trends, provider performance analysis, score distributions, and activity tracking
- **Enhanced Navigation**: Direct links to all metrics endpoints and JSON data for API consumers

### Hardened Persistence System with Dashboard (Latest)
- **Absolute Path Configuration**: Database and JSONL paths now use absolute paths for consistency across engine and dashboard
- **Robust Error Handling**: Comprehensive logging and error handling in persistence layer with graceful fallbacks
- **Enhanced SQLite Store**: Thread-safe connections with proper isolation levels and detailed logging
- **Unified Data Access**: Dashboard HTML and JSON endpoints use identical data sources ensuring consistency
- **Sample Seeding Script**: `run_sample.py` populates dashboard with realistic test data for demonstration
- **Diagnostic Tools**: `scripts/check_db.py` provides database status and run statistics
- **Signal Scores Integration**: Confidence, consensus, and diversity metrics properly stored and displayed
- **Real-time Persistence**: All analysis runs automatically saved to SQLite and JSONL for historical tracking

## Recent Updates (August 2025)

### Multi-Provider Arbitration System (Latest)
- **Pluggable Architecture**: Added support for OpenAI, Anthropic Claude, Google Gemini, xAI Grok, Perplexity, and Mistral providers
- **Real Claude Integration**: Anthropic Claude provider with actual API calls, telemetry tracking, and soft fallback to mock responses
- **Real Gemini Integration**: Google Gemini provider with actual API calls, telemetry tracking, and soft fallback to mock responses
- **Real Perplexity Integration**: Perplexity provider with actual API calls using httpx, telemetry tracking, and soft fallback to mock responses
- **Grok Provider**: xAI Grok provider with telemetry and soft fallback (ready for real API when live)
- **Soft Fallbacks**: When API keys are missing, providers automatically use mock responses so runs never fail
- **Weighted Arbitration**: Provider responses are combined using configurable weights and confidence scoring from cross-model agreement
- **Telemetry System**: Tracks latency, model information, and token usage per provider for performance monitoring
- **A/B Comparison Tools**: Scripts to compare individual provider contributions versus arbitrated results
- **Backward Compatibility**: All existing functionality preserved with seamless fallback to OpenAI-only mode when provider system unavailable
- **Configuration System**: Comprehensive settings with feature flags, provider toggles, and weight configurations via environment variables

### Platform_Fit to Conversation_Fit Migration
- **Legacy Support**: Automatic mapping of legacy "platform_fit" scores to "conversation_fit"  
- **Structured Notes**: Distribution_fit notes moved to proper "notes" object structure
- **Audience Integration**: Target audience information now displayed in final output when provided
- **Non-Interactive Mode**: Added flag to skip interactive clarification for programmatic testing
- **Validation Testing**: Comprehensive test suite validates backward compatibility and new features

### Enhanced Intake System
- **Optional Fields**: Added support for Audience and Channels fields in campaign briefs
- **Backwards Compatibility**: System operates normally when optional fields are absent
- **Structured Parsing**: OpenAI-powered extraction of brief components into structured data

### Updated Scoring Framework
- **Renamed Metric**: "platform_fit" → "conversation_fit" (measures creative fit for discussion environments)
- **Conditional Scoring**: "distribution_fit" scored only when Channels field provided
- **Clear Notifications**: Explicit notes when distribution analysis unavailable

### Improved Context Integration
- **Audience Targeting**: Target demographic information included in internal context when available
- **Enhanced Narratives**: Signal Story generation incorporates audience insights for better recommendations

### Interactive Clarification System
- **Smart Detection**: AI-powered assessment of audience and channels specificity
- **Targeted Questions**: Single clarification question for missing or vague targeting information
- **Seamless Continuation**: Analysis resumes from classification point after user input
- **Quality Control**: Prevents analysis with insufficient targeting context

### Fallback Routing System
- **Automatic Failover**: Predefined hierarchy for data source failures (reddit→twitter, tiktok→instagram, google_trends→semrush)
- **Single Attempt**: One fallback attempt per source to prevent infinite switching
- **Enhanced Tracking**: Detailed logging of sources planned, attempted, and successful
- **Graceful Degradation**: Continues with OpenAI suggestions when both primary and fallback sources fail

### Evidence Layer Refactor (Latest)
- **Layered Architecture**: Multi-tier evidence gathering with Core LLM Panel + Specialist LLMs
- **Mode Support**: Real-time vs Historic analysis modes with conditional API routing
- **Core LLM Panel**: Parallel calls to Claude, Perplexity, Gemini, Grok for cultural analysis
- **Specialist LLMs**: Conditional routing (BloombergGPT for finance, Aleph Alpha for international, Mistral for global youth, GDELT for news/policy)
- **Unified Evidence**: All sources aggregated into single cultural context string
- **API Management**: Twitter v2 Recent Search (real-time only), Google Trends (always active), Reddit/TikTok temporarily disabled
- **Backwards Compatibility**: Preserves all existing scoring and output structures

## External Dependencies

### AI Services
- **OpenAI API**: Primary reasoning engine using GPT-4o model for analysis, classification, and content generation

### Development Environment
- **Python**: Core runtime environment for orchestration logic
- **Logging**: Built-in Python logging for system monitoring and debugging

### Future Integrations
The system is designed to accommodate:
- External data APIs for real-time evidence gathering
- Historical data sources for contextual analysis
- Validation services for JSON output formatting