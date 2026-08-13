# Changelog

Notable changes to `tethysext-atcore`.

Versions are git tags, resolved at build time by `setuptools-scm`; there is no version
string in the source tree. Only changes that affect consumers of this package are
recorded here — behaviour changes, persisted-data shape changes, and additions or
removals of public helpers.

**Depend on a tag, not a commit.** Consumers that pin this package by raw commit SHA
(for example as a git submodule tracking `master`) can land on a state between tags, in
which a helper they import may not exist yet. That has already caused a downstream DAG
node to die with `ImportError` after its work had succeeded.

## Unreleased

### Changed

- A workflow step's condor sub-job statuses are now recorded per DAG node instead of
  being appended to a flat list. Concurrent nodes previously overwrote one another
  because the whole attributes document is re-serialized on every write, and a lost
  `FAILED` made a failed workflow report success. The write now takes a row lock, and
  keying by node also lets a retried node replace its own earlier status rather than
  leaving a stale `FAILED` behind.
- The authoritative statuses live under the `condor_job_statuses_by_node` step
  attribute, as `{node_name: status}`.
- The `condor_job_statuses` attribute is still written, as a plain list of the same
  status values. It exists so that a rollback to 1.16.2 or earlier still finds the
  shape it expects: that code calls `.append()` on the value and tests
  `STATUS_FAILED in statuses`, both of which misbehave against a dict. Do not read it
  directly.
- Steps still holding the old flat list are read through positional `_legacy_N` keys.
  Those entries carry no node identity, so a node that reported before the upgrade and
  then retries will leave its earlier status behind; this is logged when it happens.
  Draining in-flight DAGs before upgrading avoids it.
- The step's status store is now cleared and committed *before* the DAG is submitted
  rather than after. Nodes begin reporting as soon as DAGMan schedules them, so
  clearing afterwards could discard statuses that had already been committed.
- A failure to record `STATUS_COMPLETE` is no longer reported as a node failure. It is
  retried once on a fresh session and then logged, since the job's own work has already
  succeeded at that point.

### Added

- `get_step_statuses(step)` — the sanctioned way to read a step's sub-job statuses.
  Returns a list of status values and understands every shape written to date. Prefer
  it over reading either attribute directly.
- `initialize_step_statuses(step)` — clears the store ahead of a submission.
- `dag_node_name()` — resolves the running job's DAG node name from the job ad named by
  `_CONDOR_JOB_AD`, with a process-unique fallback. Cached for the process.

## 1.16.2

- Fixed a 40P01 deadlock on `app_users_resources` caused by write-on-read attribute
  getters (#182).

## 1.16.1

- Fixed use of `datetime.datetime.utcnow()`, deprecated in Python 3.12 (#181).
