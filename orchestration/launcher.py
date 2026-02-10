#!/usr/bin/env python3
"""
Agenticom Launcher

One-click launcher for Agenticom with GUI interface.
Automatically sets up LLM backends and provides easy access to all features.
"""

import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_api_keys():
    """Check if any API keys are configured"""
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    return has_anthropic, has_openai


def print_banner():
    """Print the Agenticom banner"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🏢 AGENTICOM - AI Agent Orchestration Framework              ║
║                                                                  ║
║     Version: 0.1.0                                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def print_status():
    """Print current status"""
    has_anthropic, has_openai = check_api_keys()

    print("📊 Status:")
    print(f"   OpenClaw (Claude):  {'✅ Ready' if has_anthropic else '❌ No API key'}")
    print(f"   Nanobot (GPT):      {'✅ Ready' if has_openai else '❌ No API key'}")
    print()

    if not has_anthropic and not has_openai:
        print("⚠️  No API keys configured!")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use Agenticom.")
        print()
        return False

    return True


def start_server(port: int = 8000):
    """Start the API server"""
    import uvicorn
    from orchestration.api import app

    print(f"🚀 Starting Agenticom server on http://localhost:{port}")
    print("   Press Ctrl+C to stop")
    print()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


def open_browser(port: int = 8000, delay: float = 2.0):
    """Open browser after delay"""
    time.sleep(delay)
    webbrowser.open(f"http://localhost:{port}")


def run_quick_demo():
    """Run a quick demo to test functionality"""
    print("🧪 Running Quick Demo...")
    print()

    try:
        from orchestration import (
            ContentFilter,
            LocalMemoryStore,
            create_feature_dev_team,
        )

        # Test guardrails
        print("   Testing Guardrails...")
        cf = ContentFilter(blocked_topics=["test"])
        result = cf.check("Hello world")
        print(f"   ✅ Guardrails: {'Working' if result.passed else 'Blocked'}")

        # Test memory
        print("   Testing Memory...")
        memory = LocalMemoryStore()
        memory.remember("Demo test", tags=["test"])
        results = memory.search("demo", limit=1)
        print(f"   ✅ Memory: {len(results)} entries found")

        # Test team creation
        print("   Testing Agent Teams...")
        team = create_feature_dev_team()
        print(f"   ✅ Teams: {len(team.agents)} agents, {len(team.steps)} steps")

        print()
        print("🎉 All systems operational!")
        print()
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def interactive_menu():
    """Show interactive menu"""
    while True:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📋 What would you like to do?")
        print()
        print("   1) 🚀 Start Web Server (recommended)")
        print("   2) 🧪 Run Quick Demo")
        print("   3) 💻 Open CLI Help")
        print("   4) 🔑 Configure API Keys")
        print("   5) 📚 Open Documentation")
        print("   6) ❌ Exit")
        print()

        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            port = 8000
            # Open browser in background
            browser_thread = threading.Thread(target=open_browser, args=(port,))
            browser_thread.daemon = True
            browser_thread.start()
            # Start server (blocks)
            start_server(port)
            break

        elif choice == "2":
            run_quick_demo()
            input("Press Enter to continue...")

        elif choice == "3":
            print()
            os.system(f"{sys.executable} -m orchestration.cli --help")
            print()
            input("Press Enter to continue...")

        elif choice == "4":
            configure_api_keys()

        elif choice == "5":
            webbrowser.open("https://github.com/wjlgatech/agentic-company")
            print("📚 Documentation opened in browser")
            input("Press Enter to continue...")

        elif choice == "6":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")

        print()


def configure_api_keys():
    """Interactive API key configuration"""
    print()
    print("🔑 API Key Configuration")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # Show current status
    has_anthropic, has_openai = check_api_keys()
    print(f"   Current Anthropic key: {'Set ✅' if has_anthropic else 'Not set ❌'}")
    print(f"   Current OpenAI key:    {'Set ✅' if has_openai else 'Not set ❌'}")
    print()

    # Get shell config file
    shell_rc = Path.home() / ".bashrc"
    if sys.platform == "darwin":
        zshrc = Path.home() / ".zshrc"
        if zshrc.exists():
            shell_rc = zshrc

    print("Enter your API keys (press Enter to skip):")
    print()

    # Anthropic
    anthropic_key = input("   Anthropic API key: ").strip()
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        # Persist to shell rc
        with open(shell_rc, "a") as f:
            f.write(f'\nexport ANTHROPIC_API_KEY="{anthropic_key}"\n')
        print("   ✅ Anthropic key saved")

    # OpenAI
    openai_key = input("   OpenAI API key: ").strip()
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        with open(shell_rc, "a") as f:
            f.write(f'\nexport OPENAI_API_KEY="{openai_key}"\n')
        print("   ✅ OpenAI key saved")

    if anthropic_key or openai_key:
        print()
        print(f"   Keys saved to {shell_rc}")
        print("   Restart your terminal or run: source ~/.bashrc")

    print()


def main():
    """Main entry point"""
    print_banner()

    # Check status
    has_keys = print_status()

    # Parse command line args
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "--serve" or cmd == "-s":
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
            start_server(port)

        elif cmd == "--demo" or cmd == "-d":
            run_quick_demo()

        elif cmd == "--help" or cmd == "-h":
            print("Usage: agenticom-launch [OPTIONS]")
            print()
            print("Options:")
            print("  --serve, -s [PORT]   Start web server (default: 8000)")
            print("  --demo, -d           Run quick demo")
            print("  --help, -h           Show this help")
            print()

        else:
            print(f"Unknown command: {cmd}")
            print("Use --help for available options")

    else:
        # Interactive mode
        interactive_menu()


if __name__ == "__main__":
    main()
