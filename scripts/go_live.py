#!/usr/bin/env python3
"""
FREE11 Go Live Script
=====================
One-click production deployment with safety guardrails.

Usage:
    # Dry run (no changes)
    python go_live.py --dry-run
    
    # Production (requires confirmation)
    python go_live.py --confirm-production
    
    # Rollback to sandbox
    python go_live.py --rollback
"""

import argparse
import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Setup logging
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "go_live.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
ENV_FILE = Path("/app/backend/.env")
BACKUP_FILE = Path("/app/backend/.env.backup")

PRODUCTION_CONFIG = {
    "FREE11_ENV": "production",
    "ENABLE_LIVE_VOUCHERS": "true",
    "ENABLE_LIVE_EMAIL": "true",
}

SANDBOX_CONFIG = {
    "FREE11_ENV": "sandbox",
    "ENABLE_LIVE_VOUCHERS": "false",
    "ENABLE_LIVE_EMAIL": "false",
}

SENSITIVE_KEYS = [
    "RESEND_API_KEY",
    "SLACK_WEBHOOK_URL",
    "ALERT_EMAIL",
]


def load_env_file():
    """Load current .env file as dict"""
    env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key] = value.strip('"').strip("'")
    return env


def save_env_file(env: dict):
    """Save dict to .env file"""
    with open(ENV_FILE, 'w') as f:
        for key, value in env.items():
            # Preserve quotes for values with spaces
            if ' ' in str(value) or not value:
                f.write(f'{key}="{value}"\n')
            else:
                f.write(f'{key}={value}\n')


def backup_env():
    """Create backup of current .env"""
    if ENV_FILE.exists():
        import shutil
        shutil.copy(ENV_FILE, BACKUP_FILE)
        logger.info(f"Backup created: {BACKUP_FILE}")


def restore_backup():
    """Restore .env from backup"""
    if BACKUP_FILE.exists():
        import shutil
        shutil.copy(BACKUP_FILE, ENV_FILE)
        logger.info(f"Restored from backup: {BACKUP_FILE}")
        return True
    else:
        logger.error("No backup file found!")
        return False


def check_prerequisites(env: dict) -> list:
    """Check if all prerequisites for production are met"""
    issues = []
    
    # Check required API keys
    if not env.get("RESEND_API_KEY") or env.get("RESEND_API_KEY") == "your-resend-api-key":
        issues.append("RESEND_API_KEY not configured (required for email notifications)")
    
    # Check optional but recommended
    if not env.get("SLACK_WEBHOOK_URL"):
        issues.append("SLACK_WEBHOOK_URL not set (recommended for alerts)")
    
    if not env.get("ALERT_EMAIL"):
        issues.append("ALERT_EMAIL not set (recommended for critical alerts)")
    
    return issues


def secondary_confirmation(feature: str) -> bool:
    """Request secondary confirmation for sensitive features"""
    print(f"\n{'='*60}")
    print(f"SECONDARY CONFIRMATION REQUIRED")
    print(f"{'='*60}")
    print(f"\nYou are about to enable: {feature}")
    print("This will affect real users and real money.")
    print("\nType 'ENABLE' to confirm, or anything else to skip:")
    
    response = input("> ").strip()
    return response == "ENABLE"


def dry_run(env: dict):
    """Perform dry run - show what would change"""
    logger.info("=" * 60)
    logger.info("DRY RUN MODE - No changes will be made")
    logger.info("=" * 60)
    
    print("\n--- Current Configuration ---")
    for key in PRODUCTION_CONFIG.keys():
        current = env.get(key, "NOT SET")
        print(f"  {key}: {current}")
    
    print("\n--- After Go Live ---")
    for key, value in PRODUCTION_CONFIG.items():
        print(f"  {key}: {value}")
    
    print("\n--- Prerequisites Check ---")
    issues = check_prerequisites(env)
    if issues:
        for issue in issues:
            print(f"  [WARNING] {issue}")
    else:
        print("  [OK] All prerequisites met")
    
    print("\n--- Sensitive Keys Status ---")
    for key in SENSITIVE_KEYS:
        status = "SET" if env.get(key) and env.get(key) != f"your-{key.lower()}" else "NOT SET"
        print(f"  {key}: {status}")
    
    logger.info("Dry run complete. Use --confirm-production to apply changes.")


def go_live(env: dict, skip_secondary: bool = False):
    """Enable production mode"""
    logger.info("=" * 60)
    logger.info("GOING LIVE - Production Mode")
    logger.info("=" * 60)
    
    # Check prerequisites
    issues = check_prerequisites(env)
    warnings = [i for i in issues if "recommended" in i.lower()]
    blockers = [i for i in issues if "required" in i.lower()]
    
    if blockers:
        logger.error("BLOCKED: Cannot go live due to missing requirements:")
        for blocker in blockers:
            logger.error(f"  - {blocker}")
        return False
    
    if warnings:
        logger.warning("Warnings (non-blocking):")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    # Create backup
    backup_env()
    
    # Apply base production config
    for key, value in PRODUCTION_CONFIG.items():
        env[key] = value
        logger.info(f"Set {key}={value}")
    
    # Secondary confirmation for live vouchers
    if not skip_secondary:
        if not secondary_confirmation("LIVE VOUCHER PROVIDERS (real money)"):
            env["ENABLE_LIVE_VOUCHERS"] = "false"
            logger.info("Live vouchers DISABLED by user")
        else:
            logger.info("Live vouchers ENABLED")
    
    # Secondary confirmation for live email
    if not skip_secondary:
        if not secondary_confirmation("LIVE EMAIL (Resend API)"):
            env["ENABLE_LIVE_EMAIL"] = "false"
            logger.info("Live email DISABLED by user")
        else:
            logger.info("Live email ENABLED")
    
    # Save configuration
    save_env_file(env)
    
    # Log final state
    logger.info("=" * 60)
    logger.info("GO LIVE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  FREE11_ENV: {env.get('FREE11_ENV')}")
    logger.info(f"  ENABLE_LIVE_VOUCHERS: {env.get('ENABLE_LIVE_VOUCHERS')}")
    logger.info(f"  ENABLE_LIVE_EMAIL: {env.get('ENABLE_LIVE_EMAIL')}")
    logger.info("")
    logger.info("IMPORTANT: Restart backend to apply changes:")
    logger.info("  sudo supervisorctl restart backend")
    
    return True


def rollback():
    """Rollback to sandbox mode"""
    logger.info("=" * 60)
    logger.info("ROLLBACK - Returning to Sandbox Mode")
    logger.info("=" * 60)
    
    env = load_env_file()
    
    # Apply sandbox config
    for key, value in SANDBOX_CONFIG.items():
        env[key] = value
        logger.info(f"Set {key}={value}")
    
    save_env_file(env)
    
    logger.info("=" * 60)
    logger.info("ROLLBACK COMPLETE")
    logger.info("=" * 60)
    logger.info("Backend is now in SANDBOX mode")
    logger.info("")
    logger.info("IMPORTANT: Restart backend to apply changes:")
    logger.info("  sudo supervisorctl restart backend")
    
    return True


def show_status():
    """Show current deployment status"""
    env = load_env_file()
    
    print("\n" + "=" * 60)
    print("FREE11 Deployment Status")
    print("=" * 60)
    
    env_mode = env.get("FREE11_ENV", "sandbox")
    is_production = env_mode == "production"
    
    print(f"\nEnvironment: {'🟢 PRODUCTION' if is_production else '🟡 SANDBOX'}")
    print(f"  FREE11_ENV: {env_mode}")
    print(f"  ENABLE_LIVE_VOUCHERS: {env.get('ENABLE_LIVE_VOUCHERS', 'false')}")
    print(f"  ENABLE_LIVE_EMAIL: {env.get('ENABLE_LIVE_EMAIL', 'false')}")
    
    print("\nAPI Keys:")
    for key in SENSITIVE_KEYS:
        value = env.get(key, "")
        if value and value != f"your-{key.lower()}":
            print(f"  {key}: ✅ Configured")
        else:
            print(f"  {key}: ❌ Not configured")
    
    print("\nBackup Status:")
    if BACKUP_FILE.exists():
        import os
        mtime = datetime.fromtimestamp(os.path.getmtime(BACKUP_FILE))
        print(f"  Backup exists: {BACKUP_FILE}")
        print(f"  Created: {mtime}")
    else:
        print("  No backup file")
    
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="FREE11 Go Live Script - Production Deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python go_live.py --status          # Check current status
  python go_live.py --dry-run         # Preview changes
  python go_live.py --confirm-production  # Go live
  python go_live.py --rollback        # Return to sandbox
        """
    )
    
    parser.add_argument(
        "--confirm-production",
        action="store_true",
        help="Confirm production deployment (required to go live)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback to sandbox mode"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current deployment status"
    )
    parser.add_argument(
        "--skip-secondary",
        action="store_true",
        help="Skip secondary confirmations (not recommended)"
    )
    
    args = parser.parse_args()
    
    # Load current config
    env = load_env_file()
    
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"Go Live Script executed at {timestamp}")
    logger.info(f"Arguments: {vars(args)}")
    
    if args.status:
        show_status()
    elif args.dry_run:
        dry_run(env)
    elif args.rollback:
        rollback()
    elif args.confirm_production:
        success = go_live(env, skip_secondary=args.skip_secondary)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        print("\nERROR: Must specify --dry-run, --confirm-production, --rollback, or --status")
        sys.exit(1)


if __name__ == "__main__":
    main()
