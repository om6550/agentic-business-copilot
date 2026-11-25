# Agentic AI Business Operations Copilot

An AI-powered business operations assistant built for **Laxmi Engineering Trailer** to combine business knowledge retrieval, agent-based tool routing, customer management, product information, quotation workflows, and workflow automation in a single application.

## Overview

The **Agentic AI Business Operations Copilot** is a local AI application designed to assist with day-to-day business operations.

The system combines:

- Retrieval-Augmented Generation (RAG)
- Agent-based question routing
- Business tools
- SQLite database operations
- Product and inventory information
- Customer profiles and quotation history
- FastAPI backend APIs
- Streamlit dashboard
- Local LLM inference using Ollama
- ChromaDB vector search
- n8n workflow automation

The project is designed as a practical AI business assistant prototype rather than a generic chatbot.

---

## Key Features

### 1. Agent-Based Question Routing

User questions are classified and routed to the appropriate business capability.

Examples:

- Product information
- Customer information
- Inventory
- Quotations
- Warranty information
- Business knowledge
- Analytics

The routing layer also validates tool arguments before execution.

---

### 2. Retrieval-Augmented Generation (RAG)

Business documents are converted into chunks, embedded using:

`all-MiniLM-L6-v2`

and stored in ChromaDB.

The system retrieves relevant business knowledge before generating an answer.

Current knowledge sources include:

- `company_faq.txt`
- `product_catalog.txt`
- `sales_policy.txt`
- `warranty_policy.txt`

This allows the assistant to answer using business-specific information instead of relying only on the language model's general knowledge.

---

### 3. Product Information

The assistant can retrieve product information such as:

- Product name
- Category
- Capacity
- Base price
- Description
- Recommended use

Example products include:

- Standard Tractor Trailer
- Hydraulic Trailer
- Heavy Duty Trailer
- Agriculture Trailer Pro
- Custom Trailer

---

### 4. Customer Management

The application supports business customer operations including:

- Customer registration
- Customer search
- Customer profiles
- Customer quotation history

Customer and business records are stored locally using SQLite.

---

### 5. Quotation Workflow

The system can prepare quotation drafts using customer and product information.

Quotation information can include:

- Customer details
- Product
- Quantity
- Base price
- Applicable adjustments
- Total amount
- Important notes

The system also includes quotation review functionality.

Final customer-facing actions can be routed through human approval.

---

### 6. Warranty Knowledge

The assistant can retrieve warranty-related business information from the dedicated warranty knowledge source.

Examples include:

- Warranty coverage
- Overloading-related conditions
- Warranty claims
- Warranty limitations

---

### 7. Sales Policy

The system includes a dedicated sales-policy knowledge source covering:

- Product pricing rules
- Quotation rules
- Customer approval requirements
- Data safety
- Inventory verification

The assistant avoids inventing unsupported payment-policy information when it is not present in the available business policy.

---

### 8. Inventory

The system includes inventory-related business tools for checking product availability and inventory information.

The business logic requires inventory information to be checked before confirming product availability.

---

### 9. FastAPI Backend

The project provides a local FastAPI backend for business operations.

Backend endpoints include functionality for:

- Health checking
- Customer management
- Quotation preparation
- Quotation review
- Quotation automation

Default backend address:

`http://127.0.0.1:8000`

---

### 10. Streamlit Dashboard

A Streamlit interface provides an interactive frontend for the business assistant.

The dashboard communicates with the FastAPI backend to perform business operations.

---

### 11. Local LLM

The project uses **Ollama** for local language-model inference.

This allows the project to run without requiring a paid external LLM API.

The application is designed to use local models such as:

- TinyLlama
- Qwen3 0.6B

Model selection is configured in the LLM layer.

---

### 12. Workflow Automation

The project includes integration with **n8n** for quotation-related workflow automation.

The FastAPI backend contains an automation webhook configuration for the local n8n instance.

Default n8n webhook target:

`http://localhost:5678/webhook/prepare-quotation`

---

## System Architecture

```text
                    User
                     |
                     v
              Streamlit Dashboard
                     |
                     v
              FastAPI Backend
                     |
                     v
             Agent / Router Layer
                     |
        +------------+-------------+
        |            |             |
        v            v             v
      Tools         RAG         Workflows
        |            |             |
        v            v             v
     SQLite       ChromaDB        n8n
        |            |
        |            v
        |       Sentence
        |      Transformers
        |            |
        +------------+
                     |
                     v
                Local LLM
                 Ollama