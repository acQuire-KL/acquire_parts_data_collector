# API Onboarding Guide

**Document:** API_Onboarding.md  
**Project:** Parts Data Collector (PDC)  
**Purpose:** Standard process for integrating new distributor APIs into the Parts Data Collector.

---

# Overview

All distributor integrations should follow the same structured process. The objective is to minimise development effort, ensure consistency between providers, and maintain a clean separation between provider-specific code and the core PDC application.

The process below should be followed whenever a new distributor API is added (for example DigiKey, Mouser, TME, Farnell, RS, Arrow, LCSC etc.).

---

# Step 1 – Register Developer Account

- Create a developer account.
- Register an application.
- Obtain API credentials.
- Record the API documentation URL.

Deliverables:

- Developer account
- Application registration
- API documentation link

---

# Step 2 – Configure Credentials

Add the required variables to:

```
.env.example
```

Example:

```text
DIGIKEY_CLIENT_ID=
DIGIKEY_CLIENT_SECRET=

MOUSER_API_KEY=

TME_TOKEN=
TME_APPLICATION_SECRET=
```

Never commit the `.env` file to Git.

---

# Step 3 – Connectivity Check

Create a standalone connectivity script.

Example:

```
tools/
    connectivity/

        digikey_check.py
        mouser_check.py
        tme_check.py
```

Purpose:

- Verify authentication.
- Verify endpoint.
- Verify request parameters.
- Verify API connectivity.
- Save raw JSON response.
- Produce concise console output.

The connectivity check should not modify the Knowledge Base or workbook.

---

# Step 4 – Capture Raw Response

Save the complete JSON response.

Location:

```
raw_responses/
```

Filename example:

```
TME_MCP1711T-25I_OT_20260726_192903.json
```

This response becomes the reference when implementing the provider mapper.

---

# Step 5 – Capability Review

Create a capability review document.

Example:

```
docs/
    DigiKey_Capability_Review.md
    Mouser_Capability_Review.md
    TME_Capability_Review.md
```

Record support for:

- Manufacturer
- Manufacturer Part Number
- Description
- Stock
- Lead Time
- MOQ
- Standard Pack Quantity
- Currency
- Price Breaks
- Datasheet
- Images
- Lifecycle
- Technical Parameters

Note any provider-specific limitations.

---

# Step 6 – Provider Implementation

Implement the provider under:

```
providers/<provider>/
```

Typical structure:

```
providers/
    digikey/
    mouser/
    tme/

        client.py
        mapper.py
        provider.py
        README.md
```

Responsibilities:

**client.py**

- Authentication
- HTTP requests
- Error handling

**mapper.py**

- Convert provider response into the common ProviderResult model.

**provider.py**

- Public interface used by PDC.

---

# Step 7 – Unit Testing

Before integration verify:

- Authentication
- Successful lookup
- No-match response
- API error handling
- Mapper correctness
- Invalid credentials
- Timeout handling

---

# Step 8 – Integration

Register the provider with PDC.

Verify:

- Workbook generation
- Knowledge Base updates
- Provider summary
- Regression tests

---

# Step 9 – Documentation

Update:

- README.md
- Provider README
- Release History
- Change Log

---

# Step 10 – Lessons Learned

Record any provider-specific observations.

Example:

## TME

The Product API documentation is hosted under:

```
https://api-doc.tme.eu/v2
```

However the actual API endpoint is:

```
https://api.tme.eu/products/search
```

The `/v2` component forms part of the documentation URL and must **not** be included in the API endpoint.

---

# Design Principles

Every provider should appear identical to the rest of PDC.

Provider-specific authentication, endpoints and response structures should be completely hidden behind the provider interface.

The remainder of PDC should never need to know how an individual distributor API operates.

---

# Future Improvements

Potential future enhancements include:

- Automatic provider discovery
- Dynamic provider registration
- Provider capability reporting
- API rate limit monitoring
- Automatic retry and back-off
- Health monitoring
- API version compatibility checking

---

# Revision History

| Version | Date | Description |
|----------|------------|--------------------------------|
| 1.0 | 2026-07-26 | Initial release. Created following successful DigiKey, Mouser and TME integrations. |