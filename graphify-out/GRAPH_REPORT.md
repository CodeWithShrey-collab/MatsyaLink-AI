# Graph Report - D:\PROJECTS\MatsyaLink-AI  (2026-07-20)

## Corpus Check
- Corpus is ~12,238 words - fits in a single context window. You may not need a graph.

## Summary
- 143 nodes · 271 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.68)
- Token cost: 1,000 input · 500 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Repositories & Config|Repositories & Config]]
- [[_COMMUNITY_LangGraph State Machine|LangGraph State Machine]]
- [[_COMMUNITY_Frontend & Scripts|Frontend & Scripts]]
- [[_COMMUNITY_Decision Tools|Decision Tools]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Integrations|Integrations]]
- [[_COMMUNITY_Core Concepts|Core Concepts]]
- [[_COMMUNITY_Prompts|Prompts]]
- [[_COMMUNITY_Data Concepts|Data Concepts]]

## God Nodes (most connected - your core abstractions)
1. `get_settings()` - 18 edges
2. `initial_state()` - 14 edges
3. `log_event()` - 13 edges
4. `DomainModel` - 12 edges
5. `CSVRepository` - 12 edges
6. `GoogleSheetsRepository` - 10 edges
7. `get_repository()` - 9 edges
8. `build_graph()` - 8 edges
9. `submission_validation_node()` - 7 edges
10. `Settings` - 6 edges

## Surprising Connections (you probably didn't know these)
- `MarketplaceRepository` --uses--> `Settings`  [INFERRED]
  repositories.py → config.py
- `CSVRepository` --uses--> `Settings`  [INFERRED]
  repositories.py → config.py
- `GoogleSheetsRepository` --uses--> `Settings`  [INFERRED]
  repositories.py → config.py
- `freshness_analysis_node()` --calls--> `get_settings()`  [EXTRACTED]
  nodes.py → config.py
- `_gemini_decision()` --calls--> `get_settings()`  [EXTRACTED]
  nodes.py → config.py

## Communities (10 total, 2 thin omitted)

### Community 0 - "Repositories & Config"
Cohesion: 0.09
Nodes (11): ABC, Central configuration for MatsyaLink AI.  The application is usable without cl, Settings, CSVRepository, GoogleSheetsRepository, MarketplaceRepository, Google Sheets repository with a local CSV adapter for credential-free demos., Simple, persistent local adapter that mirrors the three sheet tabs. (+3 more)

### Community 1 - "LangGraph State Machine"
Cohesion: 0.14
Nodes (24): LangGraph topology and true conditional routing for MatsyaLink AI., DecisionType, _best_market(), buyer_retrieval_node(), buyer_scoring_node(), decision_node(), _first(), freshness_analysis_node() (+16 more)

### Community 2 - "Frontend & Scripts"
Cohesion: 0.16
Nodes (19): build_graph(), run_agent(), initial_state(), Return a fully initialized state so UI and tests can inspect every field., load_scenarios(), main(), Run the three presentation scenarios and print their LangGraph traces., _bar() (+11 more)

### Community 3 - "Decision Tools"
Cohesion: 0.14
Nodes (17): BuyerScore, FreshnessStatus, get_repository(), calculate_buyer_score(), _clean_key(), _float(), _freshness_compatible(), generate_analytics() (+9 more)

### Community 4 - "Domain Models"
Cohesion: 0.15
Nodes (16): BaseModel, Buyer, Catch, DecisionOutput, DemandLevel, DomainModel, Fisher, Market (+8 more)

### Community 5 - "Integrations"
Cohesion: 0.27
Nodes (8): get_settings(), Send a buyer offer using Gmail SMTP, or return a safe dry-run preview., send_buyer_notification(), main(), Create/update the three prototype tabs from the bundled CSV datasets., read_rows(), isolated_repository(), Keep graph persistence tests away from the checked-in demo ledger.

### Community 6 - "Core Concepts"
Cohesion: 0.67
Nodes (3): Buyer Matching, Gemini Decision, LangGraph Agent

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Integrations` to `Repositories & Config`, `LangGraph State Machine`, `Frontend & Scripts`, `Decision Tools`?**
  _High betweenness centrality (0.392) - this node is a cross-community bridge._
- **Why does `get_repository()` connect `Decision Tools` to `Repositories & Config`, `Integrations`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `CSVRepository` connect `Repositories & Config` to `Decision Tools`, `Integrations`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **What connects `Central configuration for MatsyaLink AI.  The application is usable without cl`, `LangGraph topology and true conditional routing for MatsyaLink AI.`, `Extensible domain models for the MatsyaLink AI marketplace.` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Repositories & Config` be split into smaller, more focused modules?**
  _Cohesion score 0.08817204301075268 - nodes in this community are weakly interconnected._
- **Should `LangGraph State Machine` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `Decision Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._