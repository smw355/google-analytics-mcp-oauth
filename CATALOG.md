# Google Analytics MCP Server

Connect your AI agents to Google Analytics 4 data. Query reports, explore account structure, inspect property configuration, and monitor real-time traffic — all through your Google account using OAuth.

## Authentication

Sign in with your Google account. The server requests read-only access to Google Analytics (`analytics.readonly`). Only data your Google account can already access in the GA4 interface is available here.

## Tools

### Account & Property Management

**`ga_get_account_summaries`**
Lists every GA4 account and property accessible to the authenticated user. Returns account names, property names, property IDs, property types, and hierarchy. Start here to discover the property IDs needed for all other tools.

**`ga_get_property_details`**
Returns full configuration for a specific GA4 property — timezone, currency, industry category, service level, and creation/update timestamps.

**`ga_list_google_ads_links`**
Lists all Google Ads accounts linked to a GA4 property, including customer IDs and personalization settings.

**`ga_list_property_annotations`**
Returns annotations (notes) added to a property for specific dates or date ranges. Useful for correlating traffic changes with business events like launches, campaigns, or deployments.

---

### Reporting

**`ga_run_report`**
Run a standard GA4 analytics report for any property. Supports custom date ranges, dimensions (session source, page, device, country, etc.), metrics (sessions, users, conversions, revenue, etc.), filters, ordering, and pagination. Returns dimension headers, metric headers, and row data.

**`ga_run_realtime_report`**
Returns live data for the last 30 minutes of activity on a property. Same dimension/metric/filter flexibility as the standard report. Useful for monitoring active campaigns, deployments, or incidents.

**`ga_get_custom_dimensions_and_metrics`**
Lists all custom dimensions and metrics defined for a property — those specific to your implementation rather than GA4 built-ins. Helpful for understanding what custom event data is available before building reports.

---

## Example Prompts

- *"What are all my GA4 properties and their IDs?"*
- *"Show me sessions and conversions for the last 30 days, broken down by source and medium."*
- *"How many active users are on the site right now, by device category?"*
- *"Compare traffic by country for properties/123456789 over the past 7 days."*
- *"What custom dimensions are configured for my e-commerce property?"*
- *"List any annotations added to this property in the past month."*
- *"Run a report on landing page performance — sessions, bounce rate, and conversions — for the last 90 days."*
