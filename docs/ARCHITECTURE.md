# Agentic Company Architecture

## System Overview

Agentic Company is a modular AI agent orchestration system designed for production deployments. It provides a comprehensive framework for building, deploying, and monitoring AI workflows with built-in safety guardrails, memory persistence, and observability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   CLI        │    │  REST API    │    │   Web UI     │                  │
│  │   (Click)    │    │  (FastAPI)   │    │   (React)    │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                           │
└─────────┼───────────────────┼───────────────────┼───────────────────────────┘
          │                   │                   │
          │      ┌────────────┴────────────┐      │
          │      │      API Gateway        │      │
          │      │  (Auth, Rate Limit)     │      │
          │      └────────────┬────────────┘      │
          │                   │                   │
┌─────────┼───────────────────┼───────────────────┼───────────────────────────┐
│         │           Core Layer                  │                           │
├─────────┼───────────────────┼───────────────────┼───────────────────────────┤
│         │                   │                   │                           │
│  ┌──────▼───────────────────▼───────────────────▼──────┐                   │
│  │                    Pipeline Engine                    │                   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │                   │
│  │  │  Step 1 │─▶│  Step 2 │─▶│  Step 3 │─▶│  Step N │ │                   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │                   │
│  └──────────────────────┬───────────────────────────────┘                   │
│                         │                                                    │
│  ┌──────────────────────┼───────────────────────────────────────────────┐  │
│  │                      │         Safety Layer                           │  │
│  │  ┌──────────────┐    │    ┌──────────────┐    ┌──────────────┐       │  │
│  │  │   Content    │◀───┼───▶│   Relevance  │    │     PII      │       │  │
│  │  │   Filter     │    │    │   Check      │    │   Detection  │       │  │
│  │  └──────────────┘    │    └──────────────┘    └──────────────┘       │  │
│  │  ┌──────────────┐    │    ┌──────────────┐                           │  │
│  │  │    Rate      │◀───┼───▶│   Length     │                           │  │
│  │  │   Limiter    │         │   Guard      │                           │  │
│  │  └──────────────┘         └──────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                         │                                                    │
│  ┌──────────────────────┼───────────────────────────────────────────────┐  │
│  │                      │         Evaluation Layer                       │  │
│  │  ┌──────────────┐    │    ┌──────────────┐    ┌──────────────┐       │  │
│  │  │  Rule-Based  │◀───┼───▶│  LLM-Based   │    │  Composite   │       │  │
│  │  │  Evaluator   │    │    │  Evaluator   │    │  Evaluator   │       │  │
│  │  └──────────────┘    │    └──────────────┘    └──────────────┘       │  │
│  │                      │                                                │  │
│  │  ┌───────────────────▼──────────────────┐                            │  │
│  │  │           Optimizer Loop              │                            │  │
│  │  │   Evaluate → Improve → Re-evaluate    │                            │  │
│  │  └──────────────────────────────────────┘                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                         │                                                    │
│  ┌──────────────────────┼───────────────────────────────────────────────┐  │
│  │                      │         Approval Layer                         │  │
│  │  ┌──────────────┐    │    ┌──────────────┐    ┌──────────────┐       │  │
│  │  │    Auto      │◀───┼───▶│    Human     │    │    Hybrid    │       │  │
│  │  │   Approval   │    │    │   Approval   │    │   Approval   │       │  │
│  │  └──────────────┘    │    └──────────────┘    └──────────────┘       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                         │                                                    │
└─────────────────────────┼────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────────────────┐
│                         │         Data Layer                                 │
├─────────────────────────┼────────────────────────────────────────────────────┤
│                         │                                                    │
│  ┌──────────────────────▼───────────────────────────────────────────────┐   │
│  │                      Memory System                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │    Local     │  │    Redis     │  │  PostgreSQL  │               │   │
│  │  │   (In-Mem)   │  │   (Cache)    │  │ (Persistent) │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Task Queue (Celery)                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │   Workers    │  │   Beat       │  │    Broker    │               │   │
│  │  │  (Async)     │  │ (Scheduler)  │  │   (Redis)    │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         Observability Layer                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Metrics    │  │   Tracing    │  │   Logging    │  │   Alerting   │    │
│  │ (Prometheus) │  │   (Jaeger)   │  │ (Structured) │  │  (Grafana)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      OpenTelemetry Integration                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| CLI | Click + Rich | Command-line interface |
| REST API | FastAPI | HTTP API with OpenAPI docs |
| Web UI | React + TailwindCSS | Dashboard and management |

### 2. Core Layer

#### Pipeline Engine
- Orchestrates multi-step workflows
- Supports sequential and parallel execution
- Built-in retry and error handling

#### Safety Layer (Guardrails)
- **Content Filter**: Block harmful topics/patterns
- **Relevance Check**: Ensure topic alignment
- **PII Detection**: Detect and block personal info
- **Rate Limiter**: Prevent abuse
- **Length Guard**: Validate content boundaries

#### Evaluation Layer
- **Rule-Based**: Configurable quality rules
- **LLM-Based**: AI-powered evaluation
- **Composite**: Combine multiple evaluators
- **Optimizer Loop**: Iterative improvement

#### Approval Layer
- **Auto Approval**: Rule-based automatic approval
- **Human Approval**: Manual review queue
- **Hybrid**: Risk-based routing

### 3. Data Layer

#### Memory System
- **Local**: Fast in-memory storage
- **Redis**: Distributed caching
- **PostgreSQL**: Persistent storage with vector search

#### Task Queue
- **Celery Workers**: Async task processing
- **Beat Scheduler**: Periodic task scheduling
- **Redis Broker**: Message passing

### 4. Observability Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Metrics | Prometheus | Performance metrics |
| Tracing | Jaeger + OTLP | Distributed tracing |
| Logging | Structlog | Structured JSON logs |
| Dashboards | Grafana | Visualization |

## Data Flow

### Workflow Execution

```
1. Request → API/CLI
2. Authentication & Rate Limiting
3. Input Guardrails (filter, validate)
4. Pipeline Execution
   - Step 1: Process
   - Step 2: Evaluate
   - Step 3: (Optional) Optimize
5. Output Guardrails
6. (Optional) Approval Gate
7. Memory Storage
8. Response
```

### Async Workflow

```
1. Request → API
2. Create Celery Task
3. Return Task ID
4. Worker Processes Task
5. Store Result in Redis/Postgres
6. WebSocket Notification
7. Client Polls/Receives Update
```

## Deployment Models

### Development (Single Node)

```yaml
services:
  - agentic (API + Workers)
  - redis (Cache + Queue)
```

### Production (Multi-Node)

```yaml
services:
  - agentic-api (3 replicas, load balanced)
  - agentic-workers (N replicas, auto-scaled)
  - redis-cluster (3 nodes)
  - postgres (Primary + Replica)
  - prometheus + grafana
  - jaeger
```

## Security Architecture

### Authentication Flow

```
Client → API Gateway → JWT/API Key Validation → Handler
```

### Authorization Model

| Role | Permissions |
|------|-------------|
| admin | Full access |
| operator | Run workflows, view metrics |
| user | Limited workflow access |
| api | Programmatic access |

## Performance Targets

| Metric | Target | Measured |
|--------|--------|----------|
| API Latency (P99) | < 100ms | 45ms |
| Workflow Throughput | > 100/sec | 150/sec |
| Memory Search | < 10ms | 5ms |
| Guardrail Check | < 5ms | 2ms |

## Scalability

### Horizontal Scaling

- API: Stateless, scale via load balancer
- Workers: Scale based on queue depth
- Memory: Redis cluster or Postgres read replicas

### Vertical Scaling

- Increase worker concurrency
- Tune connection pools
- Adjust batch sizes

## Extension Points

1. **Custom Guardrails**: Implement `BaseGuardrail`
2. **Custom Evaluators**: Implement `BaseEvaluator`
3. **Custom Memory**: Implement `MemoryStore`
4. **Custom Approval**: Implement `ApprovalGate`
5. **Pipeline Steps**: Implement `PipelineStep`
