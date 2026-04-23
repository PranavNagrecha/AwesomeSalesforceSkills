# LWC Streaming Subscription Plan

## Channel

- Channel (`/event/...` or `/data/...`):
- Publisher (Apex / Flow / external):
- Expected events per minute:

## Replay Strategy

- [ ] `-1` new events only
- [ ] `-2` retained events (last 24h)
- [ ] tracked replayId with persistence

## Lifecycle

- connectedCallback subscribe target:
- disconnectedCallback unsubscribe:
- onError handler + backoff policy:

## Fan-Out

- One subscription at: (component path)
- Distribution: (custom events / parent callback / broadcast channel)

## Scale Check

- Subscribers per active user:
- Estimated daily deliveries:
- Within org allocation? Y / N

## Sign-Off

- [ ] Unsubscribe on disconnect.
- [ ] Error + reconnect with backoff.
- [ ] Idempotent handler.
- [ ] Fan-out avoids per-row subscription.
