"""Offline CLI for read-only IMPERIAL operational guards; JSON stdin to JSON stdout."""
import argparse
import json
import sys
from imperial_plugins.render_resource_guard import assess_render_events
from imperial_plugins.mission_truth_gate import assess_nca_readiness
from imperial_plugins.camera_rights_preflight import preflight_camera_source

MAX_BYTES = 131072


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline, no-credentials operational inspection")
    parser.add_argument("--kind", choices=("render", "nca", "camera"), required=True)
    parser.add_argument("--now", required=True, help="Offset-aware ISO8601 timestamp")
    parser.add_argument("--service-id", help="Render service ID, required for render")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("INPUT_TOO_LARGE")
        payload = json.loads(raw)
        if args.kind == "render":
            if not args.service_id:
                raise ValueError("SERVICE_ID_REQUIRED")
            output = assess_render_events(args.service_id, payload, now=args.now)
        elif args.kind == "nca":
            output = assess_nca_readiness(payload, now=args.now)
        else:
            output = preflight_camera_source(payload, now=args.now)
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"accepted": False, "reason": str(exc).split(":", 1)[0][:80],
                          "execution_authorized": False}), file=sys.stdout)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
