# Contributing to Orquestra 🎶

First off, thank you for considering contributing to Orquestra! We welcome contributions from everyone, regardless of experience level. Your help is invaluable in making Orquestra a robust, comprehensive, and community-driven platform for quantum resource estimation.

This document provides guidelines for contributing to Orquestra. Please take a moment to review it before you get started.

## 🎯 Project Goals

Orquestra aims to:
*   Provide an **accurate and transparent** tool for quantum resource estimation.
*   Support **academic research** by offering a research-grade, extensible platform.
*   Facilitate **hardware co-design** and **algorithm feasibility studies**.
*   Bridge the gap between **theoretical quantum algorithms and practical implementation**.
*   Foster a **collaborative community** around quantum resource management.

## Ways to Contribute

There are many ways to contribute to Orquestra:

*   📝 **Reporting Bugs**: If you find a bug, please open an issue on GitHub. Include as much detail as possible: steps to reproduce, expected behavior, actual behavior, Orquestra version, and your environment.
*   💡 **Suggesting Enhancements/Features**: Have an idea for a new feature or an improvement to an existing one? Open an issue to discuss it. We value well-reasoned proposals.
*   💻 **Code Contributions**: Fixing bugs, implementing new features, or improving existing code.
*   📚 **Documentation**: Improving our READMEs, technical papers, API documentation, or user guides.
*   🧪 **Testing**: Adding unit tests, integration tests, or helping validate our estimation algorithms.
*   🗣️ **Community Support**: Answering questions in GitHub Issues or Discussions.

## 🚀 Getting Started with Development

1.  **Set up your environment**:
    *   Ensure you have Node.js, npm (or yarn/pnpm), and Rust (for the Tauri application) installed.
    *   For the Python SDK, ensure you have Python 3.8+ and pip.
    *   Follow the detailed setup instructions in our main [README.md](./README.md).
2.  **Fork the repository**: Click the "Fork" button on the [Orquestra GitHub page](https://github.com/orquestra-ai/orquestra-qre).
3.  **Clone your fork**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/orquestra-qre.git
    cd orquestra-qre
    ```
4.  **Install dependencies**:
    *   For the Tauri app (frontend & backend): `npm install`
    *   For the Python SDK (in `python-sdk/` directory): `pip install -e .[dev]` (for editable install with dev dependencies)
5.  **Create a new branch** for your changes (see Branching Strategy below).

## 🌿 Branching Strategy

We follow a simple branching model:

*   `main`: This is the primary branch representing the latest stable release. Direct pushes to `main` are restricted.
*   **Feature Branches**: Create a new branch from `main` for each new feature or bug fix.
    *   Name your branches descriptively, e.g., `feature/new-estimation-metric`, `fix/ui-rendering-bug`, `docs/improve-readme`.
    *   Example: `git checkout -b feature/my-awesome-feature main`
*   **Pull Requests**: Once your feature or fix is complete, open a Pull Request (PR) to merge your branch into `main`.

##  estándares de codificación

To maintain code quality and consistency, we use the following tools and standards:

### General
*   Use UTF-8 encoding for all text files.
*   Avoid trailing whitespace.

### TypeScript/React (Frontend - `src/` directory)
*   **Linting**: ESLint (configuration likely in `.eslintrc.cjs` or `package.json`). Please ensure your code passes linting checks.
*   **Formatting**: Prettier (configuration likely in `.prettierrc` or `package.json`). We recommend setting up your editor to format on save.
*   **Type Checking**: TypeScript. Strive for strong typing and avoid `any` where possible.

### Rust (Backend - `src-tauri/` directory)
*   **Formatting**: `rustfmt`. Run `cargo fmt` before committing.
*   **Linting**: `clippy`. Run `cargo clippy` and address warnings.
*   Follow standard Rust API guidelines and idioms.

### Python (SDK - `python-sdk/` directory)
*   **Formatting**: Black. Run `black .` in the `python-sdk` directory.
*   **Linting**: Ruff (preferred) or Flake8. Configuration in `pyproject.toml` or `.flake8`.
*   **Type Checking**: Mypy. Add type hints to your Python code. Configuration in `pyproject.toml`.
*   **Import Sorting**: isort. Configuration in `pyproject.toml`.
*   Follow PEP 8 style guidelines.

We will set up GitHub Actions to automatically check these standards on Pull Requests.

## 💬 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps in creating an explicit commit history and makes it easier to automate changelog generation.

Each commit message should consist of a **header**, a **body**, and a **footer**.
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

*   **Type**: Must be one of the following:
    *   `feat`: A new feature.
    *   `fix`: A bug fix.
    *   `docs`: Documentation only changes.
    *   `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
    *   `refactor`: A code change that neither fixes a bug nor adds a feature.
    *   `perf`: A code change that improves performance.
    *   `test`: Adding missing tests or correcting existing tests.
    *   `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm).
    *   `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs).
    *   `chore`: Other changes that don't modify `src` or `test` files.
*   **Scope (optional)**: A noun describing the section of the codebase affected (e.g., `estimation`, `ui`, `python-sdk`, `docs`).
*   **Description**: A short, imperative mood description of the change (e.g., "add Quantum Volume estimation").

Example:
```
feat(estimation): add Quantum Volume calculation module
```
```
fix(ui): correct display of gate parameters in circuit view

Previously, parameters for RX gates were not shown. This commit
ensures they are displayed correctly.
```

## 📬 Pull Request (PR) Process

1.  Ensure your code adheres to the [Coding Standards](#-coding-standards).
2.  If you've added new features, include or update **tests**.
3.  If you've changed APIs or added functionality, update the relevant **documentation** (READMEs, technical docs, code comments).
4.  Make sure your branch is up-to-date with the `main` branch. Rebase if necessary:
    ```bash
    git checkout main
    git pull origin main
    git checkout your-feature-branch
    git rebase main
    ```
5.  Open a Pull Request from your fork's feature branch to the `orquestra-ai/orquestra-qre:main` branch.
6.  Provide a clear title and description for your PR, explaining the "what" and "why" of your changes. Reference any related issues.
7.  Ensure all CI checks (linting, tests, builds) pass.
8.  Engage in the code review process. Be prepared to discuss your changes and make adjustments based on feedback.
9.  Once the PR is approved and all checks pass, a maintainer will merge it.

## 📜 Code of Conduct

All contributors are expected to adhere to our [Code of Conduct](./CODE_OF_CONDUCT.md). Please read it to understand the standards of behavior we expect in our community.

## 📝 Developer Certificate of Origin (DCO)

To ensure that contributions are properly licensed and that contributors have the right to submit their work, we use the Developer Certificate of Origin (DCO). By signing off on your commits, you are certifying that you wrote or otherwise have the right to contribute the code and that you agree to the DCO terms.

You can sign off on your commits by using the `-s` or `--signoff` flag with `git commit`:
```bash
git commit -s -m "feat(python-sdk): implement circuit to_qasm method"
```
This will add a `Signed-off-by: Your Name <your.email@example.com>` line to your commit message. Please ensure your Git `user.name` and `user.email` are configured correctly.

## ❓ Questions & Getting Help

If you have questions about contributing, need help with your development setup, or want to discuss an idea:
*   Open an **Issue** on GitHub for specific questions or discussions related to a bug/feature.
*   Use **GitHub Discussions** (if enabled on the repository) for broader questions or community discussions.

Thank you for your interest in contributing to Orquestra! We look forward to your contributions.
