# Sprint 4.5 Housekeeping Step 4B - Output Cleanup

Knowledge Base Population reports are now a current working set rather than a
run archive. A new run overwrites the same `KB_POPULATION__*` filenames and
removes superseded timestamped machine-generated population reports.

Human-edited Candidate Review files are excluded from automatic cleanup because
they may contain engineering decisions that have not yet been promoted.
Run timestamps remain inside `KB_POPULATION__SUMMARY.json` and
`KB_POPULATION__RUN_LOG.txt`.

No Knowledge Base raw provider evidence, Knowledge History, input file, or
Parts Master staging data is deleted by this change.
