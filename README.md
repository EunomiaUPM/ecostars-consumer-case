# Ecostars Data Consumer Client: A Data Space Interaction Framework

## 1. Project Overview

![nifi](static/image_a.png "nifi")

This project defines the complete architectural framework for the Ecostars Data Consumer Client, a system engineered to operate within a federated data space based in Rainbow. The client's core mandate is to establish and manage the robust, bidirectional flow of information, enabling it to function as both a passive recipient of asynchronous data pushes and an active requester of on-demand data.

The architecture is strategically bifurcated into two primary operational branches, each addressing a distinct data interaction paradigm:

1. **The PUSH Model:** An event-driven ingestion path where the client receives data updates from external providers.
2. **The PULL Model:** A request-response path where the client actively queries data providers for specific information.

Both data streams converge into a unified persistence layer—a transactional database—which subsequently feeds a business intelligence and analytics platform (Metabase) for reporting, monitoring, and insight generation.

## 2. Architectural Branches

### 2.1. PUSH Model: Asynchronous Data Ingestion

This branch is designed for scenarios where the data consumer must react to data changes as they happen. It defines a "listener" architecture.

- **Endpoint Definition:** An API endpoint is exposed to the data space. This endpoint serves as the single point of entry for all asynchronous data updates pushed by registered data providers.
- **Ingestion & Curation:** Upon reception, the raw data is immediately funneled into an **Apache NiFi** data flow pipeline. This pipeline is responsible for the critical "ingest and cure" process:
  - **Validation:** Schema enforcement, data type checking, and validation against business rules.
  - **Transformation:** Normalization, cleansing, and enrichment of the data (e.g., joining with internal reference data, standardizing formats).
  - **Routing:** Directing data to appropriate tables or flagging it for manual review if it fails validation.
- **Persistence:** Once curated, the clean data is persisted in a **transactional database** (e.g., PostgreSQL, MySQL). This ensures data integrity, atomicity, and consistency (ACID compliance), making it a reliable source of truth.
- **Consumption:** This database is connected as a data source to **Metabase**, allowing for real-time dashboarding of incoming data.

### 2.2. PULL Model: On-Demand Data Retrieval

This branch empowers the client to proactively fetch data when needed, either on a schedule or triggered by an internal business event.

- **Internal Endpoint:** An internal service (e.g., a microservice, a scheduled job, or an internal API gateway) is defined. This service orchestrates the data request logic.
- **Data Request:** This internal service initiates synchronous requests to the data space provider's designated APIs. This process typically involves:
  - **Authentication:** Securely managing credentials (e.g., OAuth2 tokens) required by the provider.
  - **Parameterization:** Building dynamic queries (e.g., specifying date ranges, entity IDs, or specific data facets).
  - **Data Retrieval:** Executing the request (e.g., an `HTTP GET` call) and handling the response (typically a JSON or XML payload).
- **Population & Persistence:** The retrieved data payload is processed (this can also be orchestrated by an **Apache NiFi** flow triggered by the internal service) and then used to populate or update the **transactional database**. This ensures the data fetched on demand is integrated with the data received via the PUSH model.
- **Consumption:** The newly populated data becomes immediately available in **Metabase** for analysis, appearing alongside the PUSH-model data to provide a holistic view.

---

### 3. Core Technology Stack

<img src="static/image_b.png" width="400">

#### 3.1. Apache NiFi: The Data Logistics & Curation Engine

![nifi](static/nifi.png "nifi")

Apache NiFi serves as the central nervous system for all data movement and processing. It provides a visual, flow-based programming model ideal for managing the complexities of data ingestion from disparate sources.

- **Core Function:** NiFi orchestrates the entire Extract, Transform, and Load (ETL) pipeline in a visual, auditable, and resilient manner.
- **Key Features Utilized:**
  - **Visual Flow Management:** Data flows are designed as directed graphs of "Processors" (e.g., `ListenHTTP`, `InvokeHTTP`, `JoltTransformJSON`, `ValidateRecord`, `PutSQL`), making the logic transparent and easy to modify.
  - **Data Provenance:** NiFi automatically records a complete, chain-of-custody for every piece of data (a "FlowFile") that moves through the system. This provides full traceability from ingestion to persistence, which is critical for debugging and compliance.
  - **Back Pressure & Queuing:** NiFi inherently manages data flow rates, preventing downstream systems (like the database) from being overwhelmed by data spikes. Data is queued between processors, ensuring guaranteed delivery.
- **Role in PUSH Model:**
  1. A `ListenHTTP` or `ListenRELP` processor acts as the primary endpoint.
  2. Processors like `ValidateRecord` and `JoltTransformJSON` perform the curation.
  3. A `PutDatabaseRecord` or `PutSQL` processor loads the data into the transactional database.
- **Role in PULL Model:**
  1. A `GenerateFlowFile` processor can trigger the flow on a schedule (e.g., every hour).
  2. An `InvokeHTTP` processor makes the outbound API call to the data provider.
  3. Processors like `ExtractJSONPath` and `SplitJSON` parse the response.
  4. A `PutSQL` processor inserts/updates the data in the database.

#### 3.2. Metabase: The Self-Service Analytics & Visualization Platform

![nifi](static/metabase.png "metabase")

Metabase is the user-facing component of the architecture, democratizing data access and transforming the raw, persisted data into actionable business intelligence.

- **Core Function:** Provides an intuitive, question-based interface for non-technical users to explore, visualize, and share insights from the data.
- **Key Features Utilized:**
  - **Data Source Connection:** Metabase connects directly to the transactional database (PostgreSQL, MySQL, etc.) that NiFi populates.
  - **Self-Service Analytics:** Users can ask simple questions (e.g., "Show me all updates from Provider X in the last 7 days, grouped by data type") without writing SQL. Metabase generates the query, executes it, and suggests the best visualization (e.g., line chart, bar chart, table).
  - **Data Modeling:** A lightweight semantic layer allows administrators to enhance the raw database schema. This involves hiding irrelevant columns, creating user-friendly "Segments" (e.g., "Active Providers"), and defining "Metrics" (e.g., "Average Update Frequency").
  - **Interactive Dashboards:** Users can combine multiple "Questions" into comprehensive, auto-refreshing dashboards to monitor Key Performance Indicators (KPIs) of the data space integration.
  - **Alerts & Pulses:** Automated alerts can be configured to notify stakeholders via email or Slack when certain data thresholds are met (e.g., "Alert me if no data is received from the PUSH endpoint for 2 hours").

---

## 4, Deployment

Coming soon, but in the meanwhile, check out `/scripts` folder and feel free to run them all.
