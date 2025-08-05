# PROMPT: Generate Foundational Project Documentation

## ROLE
You are an expert AI system analyst and technical writer. Your purpose is to perform a one-time, deep analysis of a software project to generate a comprehensive set of documentation. This documentation will serve as the foundational context for all future AI-assisted development tasks within this project. You must be meticulous, analytical, and follow all instructions precisely.

## CONTEXT FILES
To understand the project's goals, conventions, and existing state, you must first read and fully assimilate the information from the following files:

1.  `claude.md` (If it exists, for interaction guidelines).
2.  `README.md` (This is your primary source for the project's high-level purpose).
3.  All existing files within the `specs/` folder (to allow this prompt to be re-run to update documentation).

## EXECUTION PLAN
Your task is to create or update a `specs/` folder at the project root with a set of essential documentation files. Follow these steps in order:

**1. Prepare the `specs` Directory**
*   Check if a directory named `specs` exists at the project root.
*   If it does not exist, create it.

**2. Create `project_overview.md`**
*   **Purpose:** To provide a high-level, human-readable summary of the project.
*   **Action:** Read the `README.md` file and synthesize its content into a concise summary of the project's purpose, target audience, and the problem it solves. If the `README.md` is uninformative, create a template for the user to fill out.

**3. Create `tech_stack.md`**
*   **Purpose:** To list the specific technologies, frameworks, and languages used.
*   **Action:** Analyze dependency files (`package.json`, `requirements.txt`, etc.) to identify the primary language(s), frameworks, and major libraries. Format the output as a clear list in `specs/tech_stack.md`.

**4. Create `project_structure.md`**
*   **Purpose:** To provide a map of the project's file and folder layout.
*   **Action:** Scan the entire project's file and folder structure, respecting the `.gitignore` file. Generate a Markdown code block representing the clean file tree and save it to `specs/project_structure.md`.

**5. Create `module_overview.md`**
*   **Purpose:** To explain the high-level architecture by describing the responsibility of each major source directory or "module". This provides the "why" for the project's structure.
*   **Action:**
    *   Analyze the folder structure within the primary source code directory (e.g., `src/`, `app/`, `lib/`, or the project root if no single source directory is apparent).
    *   For each major top-level directory and its important sub-directories, write a one-to-two sentence description of its inferred purpose and responsibility.
    *   Save this architectural summary to `specs/module_overview.md`.

*   **Example 1 (Frontend Project - Next.js):**
    ```markdown
    # Module Overview

    This document outlines the purpose of the primary source code directories.

    -   **/src/app:** Contains the core application routing, pages, and layouts, following the Next.js App Router conventions.
    -   **/src/components:** Contains all reusable React components.
        -   **/src/components/ui:** "Dumb" UI elements like Button, Input, Card that are application-agnostic.
        -   **/src/components/feature:** "Smart" components composed of UI elements for specific application features.
    -   **/src/lib:** Contains utility functions, API client configurations, and shared business logic (e.g., `utils.ts`, `api.ts`).
    -   **/src/styles:** Contains global stylesheets and theme configuration files.
    ```

*   **Example 2 (Backend Project - Python/Django):**
    ```markdown
    # Module Overview

    This document outlines the purpose of the primary Django apps and project directories.

    -   **/api/:** The Django app responsible for all REST API views, serializers, and URL routing.
    -   **/users/:** The Django app that manages user models, authentication, and profiles.
    -   **/core/:** The main project directory containing settings, root URL configuration (`urls.py`), and the WSGI entry point.
    -   **/static/:** Contains all static assets like CSS, JavaScript, and images served by the application.
    -   **/templates/:** Contains all Django HTML templates used for server-side rendering.
    ```

**6. Create `setup_guide.md`**
*   **Purpose:** To document how to set up and run the project locally.
*   **Action:** Analyze `package.json` (for `scripts`), `Dockerfile`, etc., and look for an `.env.example` file. Create `specs/setup_guide.md` detailing prerequisites, installation steps, environment variables, and run commands.

**7. Create `api_contracts.md` (Conditional)**
*   **Condition:** Create this file ONLY if the project appears to be a web server or has a dedicated API layer.
*   **Action:** Scan the codebase for route definitions. Create `specs/api_contracts.md` listing key endpoints, HTTP methods, and a brief description.

**8. Create `database_schema.md` (Conditional)**
*   **Condition:** Create this file ONLY if you detect interaction with a database (e.g., an ORM, schema files, or migration files).
*   **Action:** Analyze schema or model files. Create `specs/database_schema.md` to describe the primary tables/collections, their fields, and any inferred relationships.

**9. Final Confirmation**
*   After completing all applicable steps, respond with a confirmation message listing all the files that were successfully created or updated in the `specs/` directory.

---
**BEGIN**