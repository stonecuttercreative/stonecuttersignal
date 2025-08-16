# Replit.md

## Overview

Stonecutter Signal is an AI-powered diagnostic analysis engine designed to analyze campaign briefs and generate strategic insights. The system processes marketing campaign briefs containing brand, industry, and concept information, then performs multi-step analysis to produce diagnostic scores and executive summaries. The engine uses OpenAI's GPT models for reasoning while maintaining proprietary orchestration logic in Python, creating a hybrid approach that combines external AI capabilities with internal business logic.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Engine Design
The system follows a pipeline architecture with sequential processing steps, each handling a specific aspect of campaign brief analysis. The main orchestration happens in Python (`StonecutterSignal` class) while leveraging OpenAI API calls for reasoning tasks.

### Processing Pipeline
- **Concept Separation**: Detects and splits multiple concepts within a single brief
- **Brand Clarification**: Enhances insufficient brand/context information
- **Classification**: Categorizes concepts using cluster and cultural archetype frameworks
- **Evidence Selection**: Identifies the top 3 most relevant evidence sources
- **Data Gathering**: Combines historical data with real-time evidence from external APIs
- **Context Building**: Merges internal LLM context with external data sources
- **Signal Evaluation**: Produces diagnostic scores in JSON format
- **Story Synthesis**: Generates executive summaries based on scores and context

### Resilience Mechanisms
The system implements a robust error handling pattern for all external calls:
1. Initial attempt with single retry
2. LLM-powered diagnosis of failures
3. Human intervention request when automated recovery fails
4. JSON validation with LLM-based reformatting for malformed responses

### Hybrid AI Architecture
The design separates concerns between external AI reasoning (OpenAI GPT-4o) and internal business logic. OpenAI handles analysis, classification, and content generation while Python manages workflow orchestration, data integration, and error handling.

### Extensibility Framework
The architecture includes placeholder hooks for future enhancements:
- Owned data ingestion capabilities
- Multi-concept scenario analysis
- Cultural archetype reframing functionality

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