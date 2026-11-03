# Example configurations

One `cats.yaml` per deployment shape. Copy the one matching your deployment to the pack root as
`cats.yaml`, replace every `CHANGE_ME`, then follow "Configuration and Setup" in `../README.md`.

| | LZA from CodePipeline | LZA as an ECS task (LzaDeployment account) |
|---|---|---|
| **AWS Control Tower** | `control-tower-standard.yaml` (the default Universal Configuration) | `control-tower-container.yaml` (the AWS European Sovereign Cloud package) |
| **AWS Organizations only** | `organizations-standard.yaml` | `organizations-container.yaml` |

The files differ in two places, explained in each header. Without Control Tower,
`deploy_role_name` is `OrganizationAccountAccessRole`. On a container deployment, the
LzaDeployment account is listed and tagged `lza-deployment`, `test_selection.provides` declares
`container-deployment`, and the `LZA_CONFIG_*` variables name the configuration bucket.

Organizations-only with CodePipeline has no CI environment and is untested; the other three run
in CI on live environments.
