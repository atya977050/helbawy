#!/usr/bin/env python3
"""
🚀 مستودع الإصلاح والإنشاء الذكي (Repair & Creator Repository CLI)
Autonomous Software Architect, Generator, Diagnostician, and Repair Engine.
"""

import argparse
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENGINE_DIR = BASE_DIR / "engine"
REPORTS_DIR = BASE_DIR / "reports"

sys.path.insert(0, str(ENGINE_DIR))

try:
    from generator import CodeGeneratorEngine
except ImportError:
    CodeGeneratorEngine = None

try:
    from repair import DeepRepairEngine
except ImportError:
    DeepRepairEngine = None

def print_banner():
    print("=" * 65)
    print(" 🚀 مستودع الإصلاح والإنشاء الذكي (Repair & Creator Agent v2.0)")
    print(" Software Scaffolding, Architecture, Deep Repair & Verification")
    print("=" * 65)

def cmd_create(args):
    print_banner()
    print(f"[*] Command: CREATE PROJECT -> {args.name}")
    if CodeGeneratorEngine:
        generator = CodeGeneratorEngine(args.name, args.type)
        res = generator.scaffold()
        print(json.dumps(res, indent=2))
    else:
        print("[-] Error: generator engine not found.")

def cmd_repair(args):
    print_banner()
    print(f"[*] Command: REPAIR PROJECT -> {args.path}")
    if DeepRepairEngine:
        engine = DeepRepairEngine(args.path)
        res = engine.execute_repairs()
        print(json.dumps(res, indent=2))
    else:
        print("[-] Error: repair engine not found.")

def cmd_full(args):
    print_banner()
    print(f"[*] Running Full Autonomous Lifecycle (Create + Repair + Verify) on: {args.name}")
    
    if CodeGeneratorEngine:
        gen = CodeGeneratorEngine(args.name, "webrtc_app")
        gen.scaffold()
    
    if DeepRepairEngine:
        rep = DeepRepairEngine(args.name)
        rep.execute_repairs()
        
    print("\n" + "=" * 65)
    print(" 🎉 Full lifecycle completed! Project is fully generated, patched, and verified.")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="Repair & Creator Repository CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_create = subparsers.add_parser("create", help="Scaffold a new software project")
    p_create.add_argument("--name", default="bulbul-app", help="Project folder name")
    p_create.add_argument("--type", default="webrtc_app", help="Project template type")

    p_repair = subparsers.add_parser("repair", help="Repair an existing project codebase")
    p_repair.add_argument("--path", default="./bulbul-app", help="Path to project")

    p_full = subparsers.add_parser("full", help="Execute complete create -> repair -> verify cycle")
    p_full.add_argument("--name", default="bulbul-app", help="Project name")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "create": cmd_create,
        "repair": cmd_repair,
        "full": cmd_full
    }

    if args.command in commands:
        commands[args.command](args)

if __name__ == "__main__":
    main()
