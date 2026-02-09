# Contributing to 2048 AI Graphical Interface

First off, thank you for considering contributing! Projects that bridge the gap between complex AI engines and real-world usability thrive on community input. Whether you are fixing a bug, improving the UI, or adding a new feature, your help is appreciated.

## 🧩 How You Can Help

We are currently looking for assistance in the following areas:

* **UI/UX Improvements:**
  Enhancing the Tkinter interface for clarity, responsiveness, and visual feedback (board, score, AI suggestion arrows, and message area).

* **Server Integration & Robustness:**
  Improving client-side handling of AI server responses, including timeouts, malformed replies, and optional integration with the original **macroxue 2048 AI server** (platform-dependent).

* **Game Analytics & Instrumentation:**
  Helping implement statistical tracking features such as:

  * Distribution of `2` vs. `4` tile spawns over time.
  * Move history logging and exploratory “win probability” or outcome metrics.

* **Cross-Platform Compatibility:**
  Ensuring consistent behavior across **Windows and Linux**, especially for input handling, networking, and UI rendering.

* **Documentation & Examples:**
  Improving README clarity, adding annotated screenshots, usage examples, and setup notes—especially around running the macroxue server on Linux and connecting to it from a different machine over LAN.


## 🛠️ Development Environment

To get started with development:

1. **Fork the repository** on GitHub.

2. **Clone your fork** locally:
```bash
git clone https://github.com/sght500/2048-ai-gui.git
```

3. **Install dependencies**:
```bash
pip install requests
```


## 🧪 Testing Your Changes

Before submitting a Pull Request, you must verify that your changes do not break the "Human-in-the-Loop" workflow.

**Important:** We use a dummy server to simulate AI responses without needing the full C++ engine compiled. Please ensure you test your changes against the `mock_ai_server.py` before submitting.

1. Start the mock server in one terminal:
```bash
python server/mock_ai_server.py
```

2. Run the GUI in another:
```bash
python client/gui_client.py
```

3. Verify that state transitions (Setup → Thinking → Move Waiting → Move Done) function as expected.

## 📬 Pull Request Process

1. Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/amazing-new-ui
```

2. Commit your changes with clear, descriptive commit messages.

3. Push your branch to your fork.

4. Open a Pull Request against our `main` branch.

5. Provide a brief description of what you changed and, if possible, a screenshot of the UI changes.


## 📜 Coding Standards

* **State Machine Integrity:** Ensure that manual score editing and tile clicking remain disabled in the correct states to prevent logic drift.

* **Platform Awareness:** Always consider how your changes affect MacOS vs. Windows/Linux users (especially regarding mouse button bindings).

* **Readability:** Add docstrings to new methods and maintain the existing color palette for consistency.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our [CODE OF CONDUCT](CODE_OF_CONDUCT.md) and treat all contributors with respect.

---