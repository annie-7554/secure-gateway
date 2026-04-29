# Required GitHub Secrets

The workflows require these repository secrets to run in CI and to deploy securely. Add them under Settings → Secrets → Actions.

- COSIGN_PRIVATE_KEY: Base64 or raw cosign private key used to sign images. Keep this private.
- COSIGN_PASSWORD: Passphrase for the cosign private key (if any). Empty string allowed if key has no passphrase.
- GHCR_TOKEN: Personal access token (or GITHUB_TOKEN) with repo:write permissions to push images to GHCR. Prefer GitHub Actions `GITHUB_TOKEN` for CI pushes.
- KUBECONFIG: kubeconfig file content for the cluster used by deploy workflows (only if deploying from CI). Store as a secret.

Setting secrets via gh CLI (example):

  echo "$COSIGN_PRIVATE_KEY_BASE64" | gh secret set COSIGN_PRIVATE_KEY --body -
  gh secret set COSIGN_PASSWORD --body ""
  gh secret set GHCR_TOKEN --body "$GHCR_TOKEN"
  gh secret set KUBECONFIG --body "$KUBECONFIG"

Notes:
- Never commit private keys or kubeconfig into the repo.
- For local testing, you can use `secrets` environment file but do not commit it.
