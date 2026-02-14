from copy import deepcopy

BLOGS_SEED = [
    {
        "id": "1",
        "slug": "ai-assistant-vs-ai-agent",
        "title": "AI Assistant vs AI Agent",
        "subheader": "Reactive assistants vs goal-driven agents",
        "description": "A simple way to understand reactive assistants and autonomous agents",
        "content": None,
        "external_url": None,
        "status": "published",
        "tags": ["ai", "agents", "system-design"],
        "sections": [
            {
                "id": "1-1",
                "title": "AI Assistant",
                "level": 1,
                "content": "An AI Assistant is fundamentally reactive. It waits for user input and responds to prompts. It does not decide next actions on its own.",
                "children": []
            },
            {
                "id": "1-2",
                "title": "AI Agent",
                "level": 1,
                "content": "An AI Agent is goal-oriented. It can plan actions, use tools, observe results, and adapt in a loop until the objective is reached.",
                "children": []
            },
            {
                "id": "1-3",
                "title": "Why the Difference Matters",
                "level": 1,
                "content": "Assistants are easier to control and predictable. Agents are more powerful but need stronger reliability, monitoring, and safety guardrails.",
                "children": []
            },
            {
                "id": "1-4",
                "title": "Quick Rule of Thumb",
                "level": 1,
                "content": "If AI waits for your next prompt, it behaves like an assistant. If AI decides what to do next toward a goal, it behaves like an agent.",
                "children": []
            },
            {
                "id": "1-5",
                "title": "Closing",
                "level": 1,
                "content": "AI Assistants help humans think. AI Agents help systems act. Choosing the right mode is a system design choice.",
                "children": []
            }
        ],
        "created_at": "2026-01-31T00:00:00Z",
        "updated_at": "2026-01-31T00:00:00Z",
    },
    {
        "id": "2",
        "slug": "coding-agent",
        "title": "What is a Coding Agent?",
        "subheader": "A model wrapped with tools and execution loop",
        "description": "What is a Coding Agent?",
        "content": None,
        "external_url": None,
        "status": "published",
        "tags": ["ai", "agents", "coding"],
        "sections": [
            {
                "id": "2-1",
                "title": "Definition",
                "level": 1,
                "content": "A coding agent is not just a model. It is a system with tool access, iterative execution, and contextual code retrieval.",
                "children": []
            },
            {
                "id": "2-2",
                "title": "What It Can Do",
                "level": 1,
                "content": "It can search code, edit files, run commands, and iterate on errors until builds and tests pass.",
                "children": []
            }
        ],
        "created_at": "2026-01-31T00:00:00Z",
        "updated_at": "2026-01-31T00:00:00Z",
    },
    {
        "id": "3",
        "slug": "hierarchical-permissions-tree",
        "title": "Beyond RBAC: Building a Recursive Entitlement Engine for Buy-Side SaaS",
        "subheader": "From Root to Leaf permission flow",
        "description": "From Root to Leaf: How Hierarchical Permissions Streamline Trade Execution and Audits",
        "content": None,
        "external_url": "https://medium.com/@rashekarmudigonda/from-root-to-leaf-how-hierarchical-permissions-streamline-trade-execution-and-audits-a8fc2f69d6c0",
        "status": "published",
        "tags": ["system-design", "fintech", "rbac"],
        "sections": [],
        "created_at": "2025-12-10T00:00:00Z",
        "updated_at": "2025-12-10T00:00:00Z",
    },
    {
        "id": "4",
        "slug": "distributed-systems",
        "title": "Distributed Systems",
        "subheader": "Scalability, fault tolerance, and consistency",
        "description": "Scalability, fault tolerance, and consistency",
        "content": None,
        "external_url": None,
        "status": "published",
        "tags": ["distributed-systems"],
        "sections": [
            {
                "id": "4-1",
                "title": "What is a Distributed System?",
                "level": 1,
                "content": "A distributed system is a collection of independent computers that appears as one coherent system.",
                "children": []
            },
            {
                "id": "4-2",
                "title": "Core Concepts",
                "level": 1,
                "content": "Key ideas that define distributed system behavior:",
                "children": [
                    {
                        "id": "4-2-1",
                        "title": "CAP Theorem",
                        "level": 2,
                        "content": "Trade-off between consistency, availability, and partition tolerance.",
                        "children": []
                    },
                    {
                        "id": "4-2-2",
                        "title": "Consensus",
                        "level": 2,
                        "content": "Agreement across nodes on a shared state.",
                        "children": []
                    },
                    {
                        "id": "4-2-3",
                        "title": "Replication",
                        "level": 2,
                        "content": "Data copied across nodes for durability and read scale.",
                        "children": []
                    },
                    {
                        "id": "4-2-4",
                        "title": "Fault Tolerance",
                        "level": 2,
                        "content": "System continues operation despite node/network failures.",
                        "children": []
                    }
                ]
            }
        ],
        "created_at": "2026-01-31T00:00:00Z",
        "updated_at": "2026-01-31T00:00:00Z",
    },
    {
        "id": "5",
        "slug": "system-design",
        "title": "System Design Basics",
        "subheader": "Foundations of scalable architecture",
        "description": "Foundations of designing scalable systems",
        "content": None,
        "external_url": None,
        "status": "published",
        "tags": ["system-design"],
        "sections": [
            {
                "id": "5-1",
                "title": "Overview",
                "level": 1,
                "content": "System design focuses on building systems that scale horizontally and handle failures gracefully.",
                "children": []
            }
        ],
        "created_at": "2026-01-31T00:00:00Z",
        "updated_at": "2026-01-31T00:00:00Z",
    },
]

BLOGS = deepcopy(BLOGS_SEED)
