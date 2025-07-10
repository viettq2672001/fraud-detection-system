# 🕵️‍♂️ Transaction Analyzer - Copilot Agent Demo (MCP GitHub Server)

This project demonstrates how **GitHub Copilot Agent** can automate a full-day development task — from generating Python code to executing it, pushing changes, creating a pull request, and reviewing — all within a **secure GitHub Enterprise (MCP) Server** environment.

---

## 🎯 Use Case

**Goal**: Identify suspicious customer transactions (potential fraud patterns) from logs.

Traditionally, this task would take a developer 6–8 hours. With GitHub Copilot Agent, it is automated in minutes — including:

- 🧠 Code generation
- 🧪 Local execution
- 📤 Git commit & push
- 🔁 Pull request creation
- 🗂️ Code review & merge

---

## 📁 Project Structure

```
├── analyze_logs.py         # Main script to process and flag suspicious transactions
├── sample_logs.csv         # Input transaction log data (50+ rows)
├── result.json             # Output with flagged suspicious activities
├── test_analyze_logs.py    # Unit tests for core logic
├── README.md               # This file
```

---

## 🧪 How It Works

1. **Input**: A CSV file (`sample_logs.csv`) with transaction history including:
   - `transaction_id`, `customer_id`, `timestamp`, `amount`, `location`, `merchant_category`

2. **Detection Rules**:
   - High-value transactions (`amount > $1000`)
   - Unusual geographic activity within short timeframes
   - Frequent transactions within an hour (e.g., >3 per hour)

3. **Output**:
   - A `result.json` file with suspicious transactions and reason flags

---

## 🚀 Getting Started

### 1. Run the Analyzer

```bash
python analyze_logs.py --input sample_logs.csv --output result.json
```

### 2. Run Tests

```bash
pytest test_analyze_logs.py
```

---

## 🤖 GitHub Copilot Agent Workflow

> All steps performed in MCP GitHub Server

- `/copilot` prompted to write script, tests, and documentation
- Code was generated and auto-committed to a new branch
- Copilot pushed branch and created pull request
- Copilot explained code, added logging, and reviewed itself
- Developer merged the reviewed PR

---

## 🔒 Enterprise Secure Workflow

This demonstration uses:
- **GitHub Copilot Enterprise**
- **GitHub Enterprise Server (MCP)** in a private network
- Ensures **data isolation**, **compliance**, and **no external code leaks**

---

## 📦 Example Output (`result.json`)

```json
[
  {
    "transaction_id": "TX10010",
    "customer_id": "CUST001",
    "reason": ["High amount", "Rapid city change"],
    "amount": 6000.0,
    "location": "Las Vegas",
    "timestamp": "2025-07-08T11:20:55"
  }
]
```

---

## 📚 Bonus

You can extend this project to:
- Integrate with GitHub Actions for automatic validation
- Visualize results in a dashboard
- Combine Copilot with internal enterprise data search

---

## 🧑‍💼 Maintainers

This repository is part of a **GitHub Copilot Agent Pilot** for enterprise productivity in secure development environments.

---
