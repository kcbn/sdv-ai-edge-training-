from __future__ import annotations

import argparse
import json
import os

from dev_platform.bedrock_chat import BedrockChat


def main() -> None:
    parser = argparse.ArgumentParser(description="Week 1 Bedrock HMI chat (dev path only).")
    parser.add_argument("--text", required=True)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Call Bedrock (uses AWS credentials).")
    args = parser.parse_args()
    dry_run = not args.live
    if args.live:
        os.environ.setdefault("AWS_REGION", os.environ.get("AWS_REGION", "ap-southeast-2"))
    result = BedrockChat().complete(args.text, dry_run=dry_run)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
