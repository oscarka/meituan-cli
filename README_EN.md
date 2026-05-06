# Meituan AI CLI 🍜

> **Transform the Meituan App into an AI-callable API Tool.**
> Powered by UIAutomator2 + ADB for direct physical-level visual control. Zero packet sniffing, zero reverse engineering, and 100% anti-ban. Built specifically as a pure "robotic arm" for AI Agents (ClawBot, Claude, GPT).

## ✨ Core Breakthroughs (v2.0)

1. **Anti-Ban Architecture**: Avoids all HTTP packet sniffing and protocol reverse engineering. It purely simulates human touch and swipe gestures on the screen.
2. **Dynamic Visual Radar**: Completely abandons rigid coordinate-based clicks! For complex store UIs like Luckin Coffee or McDonald's (where lengthy item descriptions push the "Add" button out of place), we've developed a proprietary Y-axis clustering algorithm to accurately lock onto the nearest `+`, `Select Specs`, or `Select Combo` buttons.
3. **Multi-Level Spec Auto-Adaptation**: Intelligently detects secondary pop-ups (e.g., temperature, sweetness, cup size), automatically selects default options, and cleans up persistent modal dialogs.
4. **Business Logic Interception**: Accurately intercepts and translates complex business exceptions—like "Minimum delivery amount not met (short by ¥7)" or "Mandatory items not selected"—into structured error messages for the LLM to process.

---

## Architecture

```
Claude / Kimi / Any AI Agent
        │
        │ HTTP JSON API (Skill Invocation)
        ▼
   cli.py serve (HTTP Control Server :18080)
        │
        │ UIAutomator2 + ADB (Simulated Clicks)
        ▼
   Meituan App (Android Phone/Emulator)
```

## 🤖 AI Agent Deep Dive: Kimi End-to-End Ordering

We provide a built-in demo script `simulate_agent.py` that allows you to experience an unattended ordering flow using the Moonshot Kimi LLM:

```bash
# Ensure the cli server is running, then execute the demo script
python simulate_agent.py
```
*The LLM will automatically plan the route: Search Store -> Enter Store -> Switch to Delivery -> In-Store Search -> Add to Cart -> Go to Checkout.*

## ⚠️ Security & Disclaimer

- **Strict Security Baseline**: The `checkout` interface will **NEVER automatically process payments**. All ordering flows will safely halt at the official Meituan "Confirm Order / Payment" screen, requiring human biometric authentication (fingerprint/FaceID) or a password to finalize.
- **Environment Requirements**: Due to its purely visual-driven nature, high-frequency operations might trigger the platform's anti-bot slider CAPTCHA. In the current version, if a slider is encountered, the script will throw an error, requiring a human to manually swipe the screen once to unlock.
- **Network Requirements**: The AI must be on the same LAN as the computer running this code (or exposed via public port mapping like ngrok) to communicate.
