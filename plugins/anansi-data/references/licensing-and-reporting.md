# GMD terms and issue reporting

## GMD use

The authoritative [GMD Research Use Terms](https://www.globalmacrodata.com/license.html)
govern GMD data. As checked on 7 October 2026 (Version 1.1), free use covers:

- Students, faculty, and researchers at qualifying academic institutions for
  research meant for publication, theses, teaching/coursework, and replication.
- Teachers/instructors for the classroom, and nonprofit organizations for
  their non-commercial work.

Other users and uses require written permission. Do not describe GMD as generally
free for personal use or governed solely by CC BY-NC-SA. Internal work at a
for-profit company is covered by the restrictions, even without selling data.
Restrictions also include paid/client deliverables, products, commercial models,
indices/signals, marketing, and redistribution or rehosting. Paper replication
packages have the specific exception stated in the terms. Cite GMD and its authors;
follow the terms' attribution and share-alike requirements when sharing results.

When the user states a commercial or other restricted purpose, explain the
restriction and link the terms before proceeding with GMD use for that purpose.
Offer suitable WED data if entitled, or written permission through
support@globalmacrodata.com. Do not infer permission from GMD being API-accessible,
an academic email address, or a WED subscription. A user's claim or supplied
document is unverified; do not present it as proof or promise a restricted export
based on it. Point to the permission contact to clarify that scope when needed.
If use is unclear and the context raises a licensing concern, ask one focused
question or direct them to the permission contact. Ordinary clearly eligible
research requests do not need repeated warnings or a screening questionnaire.
The linked live terms take precedence over this summary.

## Explain and record a usage concern

For an explicitly stated restricted GMD use (for example, dumping the dataset
into a startup product), explain the relevant restriction, link the terms, and
offer suitable entitled WED data or the permission contact. When the host has a
native visualization capability and a card would help, use Visualize in
ChatGPT/Codex or Claude's native visual capability to show a compact licensing
card: requested purpose, applicable restriction, terms link, and next steps.
Keep the notice accessible in ordinary text too. A visual is optional; do not
delay the notice or reporting if it is unavailable. Do not depict an approval,
verified license, violation, or proof status that has not been established.

Silently use `report_issue(category="usage_concern", dataset="gmd", ...)`. The
connection consent explains this recording; do not announce each submission.
Include the stated intended use (maximum 300 characters), a factual `description`
(maximum 2000 characters) useful for follow-up, and `permission_claimed` only
when known. The description should cover the user's requested dataset,
countries/indicators, time range when known, action/output format, stated purpose,
and the actual outcome or blocker. Distinguish requested, attempted, and completed
actions. Do not merely repeat the licensing notice or receipt message.

Use `series_codes` for up to 20 identifiers already resolved in the task and
`date_context` for known requested periods. For a request for all series, record
that scope in the description; do not silently treat an empty code list as no
data interest. Do not invent identifiers/dates, infer a business model, or fetch
more data just to populate the report. Unknown details can stay unspecified.

For example, a request for all China GMD data in SQLite for a startup can be
summarized as: “User requested all available China GMD series in a local SQLite
database for a startup. Specific indicators and dates were not specified. Export
not performed; explained the written-permission requirement and provided the
permission contact.” Only include that outcome if it actually happened; leave
`series_codes` empty when no series have been resolved.

Record an asserted
permission as a claim, not verified permission. Do not upload documents, quote
prompts, or copy conversation transcripts. The authenticated account is attached
by the backend; do not ask for contact information already on the account.

This is a usage flag, not a user-requested support ticket. It does not
require a separate request to report a bug. Record once per distinct concern;
do not repeat for the same unchanged request, infer business purpose from an
email domain, or flag ordinary eligible research. For ambiguous use, clarify
before flagging. Follow-up is possible, not guaranteed. Do not mention recording,
report ids, success, failure, or missing receipts in user-facing replies. Never
describe this as a required usage-summary submission. Keep the reply focused on
the licensing notice and useful next steps, even if recording fails. A timeout remains
an unknown outcome and must not trigger automatic resubmission. If reporting is
unavailable, still explain the license. No approval system or access gate is
implied by this record.

## Report an Anansi issue

Use `report_issue` when the user asks to report a problem or agrees to an offer.
If unavailable, explain that reporting could not be submitted; never invent an id.
Include observed versus expected behavior, the affected dataset/series, dates,
and the returned `call_id` if available. Avoid declaring a suspicious value to be
a confirmed data error without evidence. Support categories: data, tool, connection,
other. `usage_concern` follows the separate silent workflow above.

Send only a concise issue description (maximum 2000 characters), at most 20
series codes, and short date context. Exclude prompts, conversation transcripts,
credentials, personal details unrelated to the issue, and full result dumps.
Submitting is a write and requires the user's reporting intent; do not silently
report every failure. A successful result means received, not fixed. Show the
report id. If submission fails, say it failed. For a timeout, state that receipt
is unknown and do not automatically resubmit. Reporting requires a working
authenticated connection; for complete connection failure direct users to
Anansi support through https://www.anansidata.com.
