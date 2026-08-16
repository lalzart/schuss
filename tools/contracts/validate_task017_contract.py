#!/usr/bin/env python3
"""Validate the completed Task 017 contract boundary."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];PATH=ROOT/'docs/tasks/017-curated-core-and-headless-reference-instruments.md'
def main():
 t=PATH.read_text(encoding='utf-8');required=['## Goal and why it exists','## Dependency','## In scope after the dependency closes','## Out of scope','## Inputs and deliverables','## Acceptance tests','## Decisions Task 017 may make','## Decisions Task 017 must not make','## Completion report'];missing=[x for x in required if x not in t]
 if missing or '12 new families' not in t or 'exactly two reference instruments' not in t or 'accepted locally through evidence level 2' not in t or 'levels 3-8 are `not-run`' not in t:print('Task 017 contract validation failed',file=sys.stderr);return 1
 print(json.dumps({'schema_version':'task017-contract-validator-v1','status':'valid','required_sections':len(required),'dependency':'task-016-complete','implementation_status':'complete','selected_families':12,'reference_instruments':2},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
