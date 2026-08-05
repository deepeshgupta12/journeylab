# `services/`

Workspace root for JourneyLab domain, data, retrieval, AI, ML and workflow services.

Populated from **STEP-002** onward. See
[docs/product/01-product/PRODUCT_SCOPE.md](../docs/product/01-product/PRODUCT_SCOPE.md).

Module import boundaries are enforced in CI (STEP-001.02): a cross-module
import that bypasses a package's public interface fails the build.
