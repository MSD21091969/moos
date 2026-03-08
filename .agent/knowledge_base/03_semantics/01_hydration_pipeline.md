# Hydration Pipeline

## Purpose

Describe the lifecycle from authored syntax to evaluated and projected structure.

## Canonicality

Canonical for hydration lifecycle rules.

## Seed stages

1. authored
2. validated
3. materialized
4. evaluated
5. projected

## Canonical stage mapping

| Stage        | Stratum | Description                                                |
| ------------ | ------- | ---------------------------------------------------------- |
| authored     | S0      | Declared syntax and references before schema checks        |
| validated    | S1      | Inputs admitted for realization after validation           |
| materialized | S2      | Graph-ready programs and structures prepared for execution |
| evaluated    | S3      | Contingent graph state after execution or replay           |
| projected    | S4      | Derived views such as UI lenses, embeddings, and metrics   |

## Rule

A projected view is not the same thing as foundational semantics.
Hydration produces contingent realizations without collapsing the distinction
between source, state, and view.
