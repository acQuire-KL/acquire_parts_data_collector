# Datasheet Acquisition & Manufacturer Source Verification — Sprint 4.6.3b

## Objective

Sprint 4.6.3b turns the evidence model from 4.6.3a into an acquisition
capability.

Starting with a datasheet URL already discovered by PDC, the acquisition flow:

1. fetches the discovery URL and follows HTTP redirects;
2. records the final resolved URL;
3. rejects HTML/product pages that are not technical PDF documents;
4. identifies possible Manufacturer Source URLs from the final redirect target
   or embedded redirect/proxy parameters;
5. independently fetches a candidate Manufacturer Source URL;
6. verifies that the final response remains on a recognised manufacturer
   domain and is a PDF;
7. prefers the verified manufacturer document where available;
8. archives the Static Evidence Copy using the 4.6.3a naming/hash rules;
9. returns a complete `DatasheetEvidence` record containing the Active Source
   URL and local evidence path.

## Manufacturer Verification

A distributor redirect landing on a manufacturer domain is useful evidence,
but 4.6.3b deliberately performs an independent second fetch before setting:

`manufacturer_url_verified = true`

This means PDC can distinguish:

- a URL merely observed during distributor resolution; from
- a Manufacturer Source URL that PDC has independently proven it can access.

PDC never creates a manufacturer path by simply deleting distributor content
from a URL.

## PDF Validation

An HTTP 200 alone is insufficient because distributor/manufacturer links can
return product pages, consent pages or error HTML.

4.6.3b accepts a document as PDF evidence when at least one strong PDF signal
exists, including `%PDF-` file magic or an appropriate PDF response header.

## Failure Behaviour

Acquisition failures are returned as structured results:

- `Acquisition Failed`
- `Not a PDF`
- `Evidence Archived`
- `Manufacturer Evidence Archived`

A failed download does not create fake evidence and does not stop an entire
future batch process by raising an unhandled network exception.

## Static and Active Sources

The resulting evidence continues the 4.6.3a principle:

- **Static Evidence Copy** — exactly what PDC archived and hashed;
- **Active Source URL** — best currently verified live source.

This is the basis for a later automated **What's Changed** review.

## Testing Boundary

Regression tests do not call live distributor or manufacturer sites. Network
responses are injected through a mock fetcher, keeping the PDC regression
suite repeatable and fast.

The production `fetch_url()` implementation uses Python standard-library HTTP
support and can be exercised separately against real URLs.
