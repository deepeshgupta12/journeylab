"""Connector framework — STEP-005.01.

Every outbound call in this product goes through `HttpConnector`. Nothing else
may hold an HTTP client, which is what makes the controls in `egress`,
`resilience` and `schema_gate` unforgettable rather than merely documented.
"""
