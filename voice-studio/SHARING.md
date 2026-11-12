# Private demo sharing

This installation supports a temporary HTTPS demo for explicitly allowed email addresses. The installed Cloudflare client supports protected Quick Tunnels with `--allowed-mail`. Visitors enter an allowed email address and a one-time code sent by Cloudflare. They do not need a Cloudflare account, Tailscale, or another app.

## Start and stop

On a fresh installation, install `cloudflared` with support for the `--allowed-mail` flag and create `logs/sharing-allowlist.json` containing a JSON list of the individual email addresses you choose. No allowlist or live tunnel configuration is included in Git.

1. Keep the regular Voice Studio running; the demo uses its inference worker.
2. Double-click **Start-Demo-Sharing.cmd**. It starts a separate loopback demo backend and prints the protected URL. If already running, it prints the current link.
3. Send that URL yourself to the invited people. This script does not send invitations.
4. Double-click **Stop-Demo-Sharing.cmd** to take the shared link offline. Your personal studio stays running. Stopping all of Voice Studio also stops sharing.

The current URL is stored in `logs/sharing.json`. It changes after stopping and starting a new tunnel. The email allowlist is in `logs/sharing-allowlist.json`, a local JSON list excluded from Git. Stop sharing before editing the list, then restart. The launcher refuses empty lists and wildcard domains, and refuses to start a tunnel if this client lacks email protection. It never falls back to an unauthenticated tunnel.

## What guests can access

- All invited guests share **one demo workspace**, under `data/demo/`. They can see audio, profiles, sessions, and exports saved there by other guests. A visible banner explains this.
- Personal data under `data/audio`, `data/references`, `data/profiles`, and `data/sessions` is handled by a separate server and is not routed through this tunnel.
- Demo generation and personal generation share the same local GPU worker. If it is busy, the other request receives a visible error and can be retried.
- Your PC, the inference worker, demo backend, and tunnel must stay running. Shutting down or stopping the tunnel ends access.
- The demo starts empty. Use recordings you are comfortable showing to everyone invited. Nothing is automatically copied from your personal voice profiles.
- Cloudflare transports the remote browser traffic, including uploaded audio and generated downloads. Synthesis still runs on this PC. This is remote sharing, not an offline connection.

## Verification

Verified October 15, 2026:

- Installed `cloudflared 2026.10.0` supports the email protection flag.
- Anonymous requests to the public studio, audio-library API, profiles API, and sessions API were redirected to Cloudflare authentication.
- A real browser loaded the Cloudflare email/code sign-in page.
- Demo health does not expose the local data-directory path.
- The configured public browser origin is accepted; unrelated origins are rejected.
- Local demo generation and personal-data isolation were tested with a temporary official sample reference. Test fixtures were removed from the demo afterward; verification artifacts stay in `data/tests/`.

Completing email-code authentication requires an invited person to enter the code from their own mailbox. The sign-in page and unauthenticated access controls were verified; mailbox delivery and a signed-in guest session require that final user check.

Primary documentation checked October 15, 2026: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/

Quick Tunnels are temporary testing/demo links with no uptime guarantee. This setup deliberately leaves existing Cloudflare configuration, personal services, and the personal studio listener unchanged.
