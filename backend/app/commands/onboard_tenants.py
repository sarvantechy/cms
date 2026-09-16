"""Command-line entry point for idempotent initial tenant onboarding."""

import argparse

from app.config import settings
from app.db.session import owner_session
from app.domains.tenancy.onboarding import TenantOnboardingService


def _arguments() -> argparse.Namespace:
    """Parse explicit onboarding options from the command line."""

    parser = argparse.ArgumentParser(description="Onboard initial CMS tenants")
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Create approved synthetic administrator accounts using DEMO_SEED_PASSWORD",
    )
    return parser.parse_args()


def main() -> None:
    """Synchronize the authorization catalogue and initial INDUS tenants."""

    arguments = _arguments()
    if arguments.seed_demo and not settings.demo_seed_password:
        raise RuntimeError("DEMO_SEED_PASSWORD is required with --seed-demo")

    with owner_session() as session:
        service = TenantOnboardingService(session)
        tenants = service.onboard_initial_tenants()
        if arguments.seed_demo:
            service.seed_demo_administrators(settings.demo_seed_password or "")
            service.seed_demo_platform_administrator(settings.demo_seed_password or "")
            service.seed_demo_academics()
            service.seed_demo_operations()
            service.seed_demo_portal_roles(settings.demo_seed_password or "")
        tenant_names = tuple(tenant.display_name for tenant in tenants)

    print(f"Onboarded {len(tenant_names)} tenants: {', '.join(tenant_names)}")


if __name__ == "__main__":
    main()
