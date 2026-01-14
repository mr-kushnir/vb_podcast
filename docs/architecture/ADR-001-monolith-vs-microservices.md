# ADR-001: Modular Monolith Architecture

**Status**: Accepted
**Date**: 2026-01-14
**Decision Makers**: ARCHITECT agent (via /run pipeline)
**Context**: POD-1 - AI Morning Podcast Portal

## Context and Problem Statement

We need to decide the high-level architecture for the podcast portal. Should we use:
1. Pure monolith
2. Microservices
3. Modular monolith
4. Serverless functions

## Decision Drivers

- **Simplicity**: Single developer/small team, minimize operational complexity
- **Cost**: Optimize for Yandex Cloud costs
- **Scalability**: Daily cron job, not high traffic
- **Development Speed**: Need rapid iteration
- **Maintainability**: Easy to debug and modify

## Considered Options

### Option 1: Pure Microservices
**Pros**:
- Independent scaling
- Technology diversity
- Clear separation of concerns

**Cons**:
- High operational complexity (orchestration, monitoring, networking)
- Expensive for low traffic
- Overkill for daily cron + simple web portal
- Debugging distributed systems is hard

### Option 2: Pure Monolith
**Pros**:
- Simple deployment
- Easy to develop and debug
- Low cost

**Cons**:
- Can become tangled spaghetti code
- Hard to test components in isolation
- All-or-nothing deployment

### Option 3: Modular Monolith (CHOSEN)
**Pros**:
- Single codebase, single deployment
- Clear module boundaries (can extract to microservices later if needed)
- Easy to test with mocked dependencies
- Simple deployment to Yandex Serverless Container
- Low operational cost

**Cons**:
- Requires discipline to maintain module boundaries
- Shared failure domain

### Option 4: Serverless Functions
**Pros**:
- Pay-per-invocation pricing
- Auto-scaling

**Cons**:
- Cold starts for daily cron
- Complex state management
- Vendor lock-in

## Decision Outcome

**Chosen option: Modular Monolith**

We will build a single FastAPI application with clear module boundaries:

```
src/
├── news/          # News collection module
├── script/        # Script generation module
├── audio/         # TTS module
├── portal/        # Web frontend module
├── automation/    # Cron/scheduler module
├── common/        # Shared utilities
└── main.py        # FastAPI entry point
```

Each module has:
- Clear interfaces (dependency injection)
- Own tests
- Minimal coupling
- Can be extracted to microservice if needed

## Deployment Strategy

- **Development**: Run locally with `uvicorn`
- **Production**: Deploy to Yandex Serverless Container
  - Single Docker image
  - Auto-scaling (though traffic will be low)
  - Integrated with Yandex Cloud services (YDB, S3)

## Consequences

**Positive**:
- Fast development velocity
- Easy debugging (single process, clear logs)
- Low cost (single container, minimal resources)
- Can scale later to microservices if needed

**Negative**:
- Must maintain module discipline
- Entire app restarts on deployment (acceptable for daily cron use case)

**Mitigation**:
- Use dependency injection (FastAPI Depends)
- Clear interface contracts
- Comprehensive unit tests for each module
- Integration tests for end-to-end flows

## Validation

Success criteria:
- ✅ Single deployment artifact
- ✅ Module boundaries enforced via imports
- ✅ Each module can be tested independently
- ✅ Deployment time < 2 minutes
- ✅ Cold start time < 5 seconds

## Related Decisions

- ADR-002: Async processing patterns
- ADR-003: Error handling strategy
- ADR-004: Data storage approach
