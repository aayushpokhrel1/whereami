// vitest-pool-workers types `env` as ProvidedEnv. Without this it has no
// bindings and every test that touches env.BOARD fails to type-check.
declare module "cloudflare:test" {
  interface ProvidedEnv extends Env {}
}
