from __future__ import annotations

"""External event integrations.

Currently: inbound Jira webhooks (``jira_events``) that turn Jira Automation
"Send web request" callbacks into a normalised :class:`JiraEvent` the agent can
react to. The HTTP entrypoint lives in ``app/api/webhooks.py``.
"""
