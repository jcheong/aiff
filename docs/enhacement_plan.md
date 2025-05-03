# Project Enhancement Plan: Automated Immigration Form Filling
*(Incorporating Broader Document Support)*

This document outlines the planned enhancements to evolve the Automated Immigration Form Filling application beyond its initial Minimum Viable Product (MVP) state. The plan focuses on expanding form support, improving data extraction from diverse document types (including images), enhancing usability and trust, ensuring information currency, and preparing for production.

**Overall Goals:**

*   Increase the number of supported USCIS forms.
*   Improve data extraction accuracy and reliability from various input document types (PDF, TXT, Images like IDs, certificates, statements).
*   Provide a more robust, secure, and user-friendly experience.
*   Ensure information used by the RAG chatbot remains reasonably current.
*   Prepare the application for potential deployment and scaling.

---

## Phase 1: Foundational Improvements & Core Expansion

**Goal:** Address major MVP limitations, improve core reliability, **enable processing of common identity/evidence document formats (including images via OCR)**, and prepare the architecture for supporting multiple forms.

**Features:**

1.  **Multi-Form Architecture:**
    *   **Description:** Refactor the backend to handle multiple form types dynamically, not just the hardcoded I-765.
    *   **Tasks:**
        *   Design configuration schema (files or DB) for forms (template path, field definitions: name, description, type, validation rules).
        *   Update `/api/fill-form` and related frontend calls to accept/pass a `form_type` parameter.
        *   Modify `form_filler_service` to load configurations and adapt extraction prompts/filling logic based on the requested `form_type`.
    *   **Rationale:** Core requirement for expanding application utility. Enables future form additions.

2.  **OCR Integration (Image Processing) & Foundational Document Handling:**
    *   **Description:** Enable text extraction from common image file types (JPG, PNG, TIFF, etc.) using Optical Character Recognition (OCR). Establish basic handling for diverse document uploads.
    *   **Tasks:**
        *   Integrate an OCR solution:
            *   **Option A (Cloud API - Recommended):** Use Google Cloud Vision API. Install `google-cloud-vision` library, set up API key/auth, modify `text_extractor.py` to call the API for image types.
            *   **Option B (Local Engine - Requires Docker for Deployment):** Install Tesseract OCR engine, install `pytesseract`/`Pillow`, modify `text_extractor.py` to call local Tesseract. Package Tesseract in `Dockerfile` for deployment.
        *   Expand `ALLOWED_EXTENSIONS` in `document_service.py` for relevant image types.
        *   Ensure `document_service` and `text_extractor` gracefully handle these new types.
    *   **Rationale:** Critical first step to accept image-based documents like IDs, certificates, scanned forms, significantly expanding usability.

3.  **Basic User Accounts & Authentication:**
    *   **Description:** Implement user registration, login, password hashing, and session management. Secure API endpoints.
    *   **Tasks:**
        *   Choose Flask extensions (e.g., Flask-Login, Flask-SQLAlchemy, Flask-Migrate, Flask-Bcrypt).
        *   Define a User database model.
        *   Implement registration/login routes and forms/logic on frontend/backend.
        *   Apply `@login_required` decorators to relevant API endpoints.
        *   Configure secure session management.
    *   **Rationale:** Foundation for personalized experiences, data security, and future features like saving progress.

4.  **Enhanced Error Handling & Logging:**
    *   **Description:** Implement structured logging and more specific error handling throughout the application stack. Provide clearer feedback to the user.
    *   **Tasks:**
        *   Configure Python's `logging` module in Flask (file/console/cloud handlers).
        *   Add specific `try...except` blocks in services (OCR, LLM API, PDF processing, DB access).
        *   Define standard JSON error response format for the API.
        *   Update frontend to display user-friendly error messages based on API responses.
    *   **Rationale:** Improves maintainability, debuggability, and user experience during failures.

5.  **Refined Extraction Prompting & Basic Document Type Awareness:**
    *   **Description:** Enhance form configurations and LLM prompts to start handling common data points found across *different* document types (e.g., extracting "Name", "Date of Birth", "Address"). Improve field typing.
    *   **Tasks:**
        *   Review target fields for initial forms (e.g., I-765) and identify common data points likely found in standard supporting documents (IDs, birth certificates, prior notices).
        *   Refine field descriptions in form configurations to be slightly less document-specific where applicable (e.g., ask for "Applicant's Date of Birth").
        *   Enhance the main extraction prompt to instruct the LLM to look for requested data across *all* provided text, mentioning the text comes from various uploaded documents.
        *   Include data type hints (date, name, address components) in field configurations/prompts.
        *   Implement basic Python-based validation *after* LLM extraction based on the defined types/rules.
    *   **Rationale:** Prepares the LLM extraction step to utilize information from a mix of document types, improving data gathering versatility.

---

## Phase 2: Feature Enrichment & Usability

**Goal:** Build upon Phase 1, add support for more forms, improve the user workflow for data verification, **enhance AI's ability to understand and extract from specific common document types (IDs, certificates, notices)**, and increase usability.

**Features:**

1.  **Add Support for More Forms (Iterative):**
    *   **Description:** Incrementally add configurations for other high-priority USCIS forms (e.g., I-130, I-485, N-400).
    *   **Tasks (Repeat for each form):** Obtain template, inspect fields, create configuration, refine extraction prompt, test end-to-end.
    *   **Rationale:** Directly expands the application's core value proposition.

2.  **User Interface for Form Selection:**
    *   **Description:** Allow users to choose the desired form from a list of supported forms in the frontend.
    *   **Tasks:** Backend API endpoint to list forms, React UI for selection, pass selected form type to backend.
    *   **Rationale:** Essential UI component for the multi-form architecture.

3.  **Data Review & Editing Interface:**
    *   **Description:** Implement a crucial step where users can review, edit, and confirm the data *extracted* by the LLM before it's used to fill the final PDF.
    *   **Tasks:** Backend endpoint (`/api/extract-data`?) returns extracted JSON. Modify `/api/fill-form` to accept verified JSON. Develop React UI for displaying/editing extracted data.
    *   **Rationale:** Critical for ensuring accuracy and building user trust, as LLM extraction is imperfect.

4.  **Document-Specific Extraction Strategies (Advanced):**
    *   **Description:** Implement more sophisticated logic to identify the *type* of uploaded document (e.g., Passport, Birth Certificate, I-94, Bank Statement, USCIS Notice) and potentially use different, tailored LLM prompts or fine-tuned models optimized for extracting data from that specific document layout/structure.
    *   **Tasks:**
        *   Develop document classification logic (heuristics, keywords, separate LLM/ML model).
        *   If classified, route text to specialized extraction prompts OR add detected document type as context to the main prompt.
        *   Requires significant prompt engineering, potentially data collection for fine-tuning specific document extractors.
    *   **Rationale:** Greatly improves extraction accuracy by leveraging knowledge of standard document layouts and expected fields.

5.  **Automated RAG Data Updates:**
    *   **Description:** Implement a background process to periodically check for updates on key USCIS web pages and refresh the vector database content for the RAG chatbot.
    *   **Tasks:** Develop web scraping scripts, implement change detection logic, integrate with data loading/re-indexing process, set up scheduler (Celery Beat, Cloud Scheduler, etc.).
    *   **Rationale:** Keeps chatbot information more current without constant manual intervention.

6.  **Handling Multi-Page Documents & Source Tracking:**
    *   **Description:** Improve text extraction to retain page number information. Enhance the LLM extraction process to pinpoint the source page/document for extracted data when possible.
    *   **Tasks:** Modify `text_extractor` (for PDF/OCR) to include page markers. Update LLM prompts to request source attribution. Display source information in the Data Review UI (from 2.3).
    *   **Rationale:** Essential for user verification when dealing with many documents; improves trustworthiness.

---

## Phase 3: Advanced Features & Production Readiness

**Goal:** Add sophisticated AI features, enhance security and robustness, and prepare for reliable cloud deployment and scaling.

**Features:**

1.  **Confidence Scores & Source Highlighting:**
    *   **Description:** Enhance LLM extraction to provide confidence scores. Display scores and verified source information (from 2.6) prominently in the review interface.
    *   **Tasks:** Advanced prompt engineering or alternative confidence estimation methods. Integrate data tracking into RAG/extraction pipeline. Enhance Review/Edit UI.
    *   **Rationale:** Increases user trust and significantly aids the data verification process.

2.  **RAG on Uploaded Documents (Targeted Q&A):**
    *   **Description:** Allow users to ask natural language questions specifically about the content of the documents they uploaded within their current session.
    *   **Tasks:** Design temporary/session-specific vector storage. On upload: Chunk/Embed/Store vectors with session ID. New API/chat mode for session Q&A querying session-specific vectors. Implement data cleanup.
    *   **Rationale:** Adds significant value by allowing users to interrogate their own evidence documents easily.

3.  **Comprehensive Testing Suite:**
    *   **Description:** Develop a robust suite of automated tests (unit, integration, end-to-end).
    *   **Tasks:** Implement tests using `pytest`, `Jest`/`React Testing Library`, `Cypress`/`Playwright`. Integrate into CI/CD.
    *   **Rationale:** Ensures code quality, catches regressions, builds confidence for deployment and refactoring.

4.  **Deployment to Cloud (GCP Example):**
    *   **Description:** Prepare and deploy the application to a cloud environment.
    *   **Tasks:** Containerize using Docker (including Tesseract if chosen over Cloud Vision API). Set up GCP services (Cloud Run/GKE, Cloud SQL, Cloud Storage, Artifact Registry). Configure networking, IAM. Set up CI/CD pipeline (Cloud Build, GitHub Actions).
    *   **Rationale:** Makes the application publicly available, scalable, and manageable.

5.  **Monitoring & Alerting:**
    *   **Description:** Implement real-time monitoring of application performance, resource usage, and errors, with alerts for critical issues.
    *   **Tasks:** Integrate with Cloud Monitoring/Logging or third-party tools (Sentry, Datadog). Define key metrics, dashboards, and alert policies.
    *   **Rationale:** Enables proactive identification and resolution of production issues.

---

## Ongoing Activities (Across All Phases)

*   **Security Hardening:** Regular dependency scanning, secure coding practices, rate limiting, PII protection review.
*   **Dependency Management:** Regularly update Python (pip) and Node (npm/yarn) packages.
*   **Documentation:** Maintain/update README, architecture diagrams, API documentation, code comments.
*   **Cost Optimization:** Monitor cloud and third-party API costs. Optimize resource usage and query patterns.
*   **User Feedback Integration:** Establish channels for user feedback and incorporate it into prioritization and feature refinement.
*   **Legal & Compliance:** Regularly review data handling practices against privacy regulations. Consult legal counsel regarding application scope, liability, and terms of service.

---