# GitHub Environment Protection (production)

Protecting the `production` environment ensures manual approval and reviewer enforcement before deploy workflows proceed.

Recommended settings (UI):
1. Go to Settings → Environments → New environment → `production`.
2. Under "Protection rules" add required reviewers or teams who must approve deployments.
3. Optionally require wait timer and branch restrictions.

Using gh CLI to create environment (creates environment only):

  gh api --method PUT /repos/:owner/:repo/environments/production -f name=production

Currently, repository environments & their protection rules (required reviewers) are configured via the GitHub UI. After creating an environment, ensure the deploy workflow references `environment: production` (it does) and that reviewers are assigned.

If you want, provide permission for this agent to configure environment protection and it can be automated via the GitHub API.
