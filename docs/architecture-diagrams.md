# Flash Service - Architecture Diagrams

This document contains visual architecture diagrams for the Flash LLM integration.

---

## Multi-Provider LLM Architecture

This diagram shows how the Flash service connects to different LLM providers through a unified abstraction layer:

```mermaid
graph LR
    subgraph "Configuration (.env)"
        A[FLASH_LLM_PROVIDER]
        B[API Keys & Endpoints]
    end
    
    subgraph "Abstraction Layer"
        C[get_llm_client Factory]
        D[BaseLLMClient Interface]
    end
    
    subgraph "Provider Implementations"
        E[AzureOpenAIClient]
        F[OpenAIClient]
        G[GeminiClient]
        H[OllamaClient]
    end
    
    subgraph "Your Services"
        I[JobAnalyzerService]
        J[ResumeTailorService]
        K[QAEngine]
    end
    
    subgraph "External APIs"
        L[Azure OpenAI<br/>Enterprise]
        M[OpenAI API<br/>Standard]
        N[Google Gemini<br/>Cost-effective]
        O[Ollama<br/>Local/Free]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H
    
    I --> D
    J --> D
    K --> D
    
    E --> L
    F --> M
    G --> N
    H --> O
    
    style A fill:#4CAF50
    style C fill:#2196F3
    style D fill:#FF9800
    style O fill:#9C27B0
```

**Key Components:**

- **Configuration Layer**: Environment variables control which provider to use
- **Abstraction Layer**: `BaseLLMClient` interface and factory pattern
- **Provider Implementations**: Concrete implementations for each LLM provider
- **Services**: Your business logic that uses the LLM
- **External APIs**: The actual LLM provider endpoints

---

## Detailed Service Flow

This diagram shows the complete flow from the application layer to external LLM APIs:

```mermaid
graph TB
    subgraph "Your Application"
        A[Flash Services]
        B[job_analyzer.py]
        C[resume_tailor.py]
        D[qa_engine.py]
    end
    
    subgraph "Abstraction Layer"
        E[BaseLLMClient Interface]
        F{get_llm_client Factory}
    end
    
    subgraph "Provider Implementations"
        G[AzureOpenAIClient]
        H[OpenAIClient]
        I[GeminiClient]
        J[OllamaClient]
    end
    
    subgraph "External APIs"
        K[Azure OpenAI API]
        L[OpenAI API]
        M[Google Gemini API]
        N[Ollama localhost:11434]
    end
    
    A --> B
    A --> C
    A --> D
    B --> E
    C --> E
    D --> E
    E --> F
    F -->|azure_openai| G
    F -->|openai| H
    F -->|gemini| I
    F -->|ollama| J
    G --> K
    H --> L
    I --> M
    J --> N
    
    style E fill:#4CAF50
    style F fill:#2196F3
    style N fill:#FF9800
```

**Flow Description:**

1. **Services** call the abstract `BaseLLMClient` interface
2. **Factory** determines which provider to use based on configuration
3. **Provider Implementation** translates the request to provider-specific format
4. **External API** processes the request and returns response
5. Response flows back through the same path to the service

---

## Configuration-Driven Selection

Simple diagram showing how a single environment variable controls everything:

```mermaid
graph TD
    A[.env file] -->|FLASH_LLM_PROVIDER=?| B{Factory}
    
    B -->|azure_openai| C[Azure OpenAI]
    B -->|openai| D[OpenAI]
    B -->|gemini| E[Gemini]
    B -->|ollama| F[Ollama]
    
    C --> G[Your Services Work Identically]
    D --> G
    E --> G
    F --> G
    
    style A fill:#4CAF50
    style B fill:#2196F3
    style G fill:#FF9800
```

**Key Insight:** Change one variable, restart the server, and you're using a different provider. No code changes required!

---

## Provider Comparison at a Glance

```mermaid
graph LR
    subgraph "Free Options"
        A[Ollama<br/>Local Models]
        B[Gemini<br/>Free Tier]
    end
    
    subgraph "Paid Options"
        C[OpenAI<br/>Pay-as-you-go]
        D[Azure OpenAI<br/>Enterprise SLA]
    end
    
    subgraph "Use Cases"
        E[Development &<br/>Learning]
        F[Prototypes &<br/>Startups]
        G[Production &<br/>Enterprise]
    end
    
    A --> E
    B --> E
    B --> F
    C --> F
    C --> G
    D --> G
    
    style A fill:#4CAF50
    style B fill:#8BC34A
    style C fill:#FFC107
    style D fill:#FF9800
```

---

## Integration Points

Shows where the LLM client is integrated into the Flash service:

```mermaid
graph TD
    A[app/main.py] --> B[flash/router.py]
    B --> C[get_llm_client]
    C --> D[Initialize Services]
    
    D --> E[JobAnalyzerService]
    D --> F[ResumeTailorService]
    D --> G[QAEngine]
    
    E --> H[_call_llm method]
    F --> H
    G --> H
    
    H --> I[client.chat_completion]
    
    I --> J{Provider?}
    J -->|azure| K[Azure OpenAI API]
    J -->|openai| L[OpenAI API]
    J -->|gemini| M[Gemini API]
    J -->|ollama| N[Local Ollama]
    
    style C fill:#4CAF50
    style I fill:#2196F3
```

---

## Viewing These Diagrams

These diagrams use Mermaid syntax and can be viewed in:

- **GitHub**: Renders automatically in markdown files
- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **Mermaid Live Editor**: https://mermaid.live/
- **Many other markdown viewers**: Most modern markdown tools support Mermaid

---

## Editing These Diagrams

To modify these diagrams:

1. Copy the mermaid code block
2. Paste into https://mermaid.live/
3. Edit visually
4. Copy the updated code back here

Or edit the text directly - Mermaid uses a simple text-based syntax.

---

## Additional Resources

- **Mermaid Documentation**: https://mermaid.js.org/
- **Diagram Types**: Flowcharts, Sequence, Class, State, Gantt, and more
- **Live Editor**: https://mermaid.live/
