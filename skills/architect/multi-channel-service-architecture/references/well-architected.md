# Well-Architected Notes — Multi Channel Service Architecture

## Relevant Pillars

- **Scalability** — Multi-channel architectures must handle volume growth per channel independently. Adding SMS as a new channel should not require re-architecting phone or email routing. Omni-Channel capacity weights and skills-based routing allow horizontal scaling by adding agents and adjusting weights rather than redesigning the routing model.
- **Reliability** — Channel failures must be isolated. If the Amazon Connect telephony link goes down, chat and email channels should continue operating. Designing each channel as an independent entry point that converges at the Omni-Channel routing layer ensures fault isolation. Monitoring must cover each channel independently.
- **Operational Excellence** — A unified multi-channel architecture reduces operational overhead by consolidating routing configuration, agent training, and reporting into a single model. Topic-based queues instead of channel-based queues simplify workforce management. Standardized capacity weights across channels enable predictable agent utilization modeling.
- **Security** — Each channel has distinct security considerations. Service Cloud Voice calls traverse Amazon Connect (external AWS infrastructure). Messaging sessions may carry PII in persistent conversation threads. Email-to-Case processes inbound email that may contain malicious attachments. The architecture must address data residency, encryption in transit, and attachment scanning per channel.

## Architectural Tradeoffs

**Single routing strategy vs. per-channel flexibility.** Using one Omni-Channel routing strategy (e.g., skills-based) across all channels simplifies administration and enables true cross-channel load balancing. However, some channels have unique routing needs — phone calls may need geographic routing while chats need language-based routing. The tradeoff is between unified simplicity and per-channel optimization. The recommended approach is skills-based routing with channel-specific skills as attributes.

**Persistent vs. session-based conversations.** Messaging for In-App/Web supports persistent (asynchronous) conversations where customers can leave and return. This is architecturally different from session-based Live Agent. Persistent conversations require a strategy for conversation ownership — who picks up a returning customer's thread? The tradeoff is between customer convenience and agent assignment complexity. Enhanced Omni-Channel with conversation ownership rules addresses this.

**Channel deflection vs. channel availability.** Offering all channels simultaneously can overwhelm agents and increase cost. Deflection strategies (e.g., chatbot as front door, self-service before phone) reduce cost per contact but add architectural complexity and customer friction. The tradeoff is between cost optimization and customer experience. Measure channel resolution rates and CSAT per channel to find the right balance.

## Anti-Patterns

1. **Channel-siloed routing** — Creating separate Omni-Channel queues per channel (phone queue, chat queue, email queue) instead of topic-based queues. This prevents cross-channel load balancing and wastes agent capacity. Agents in the "phone queue" sit idle when calls drop while the "chat queue" overflows. Use topic-based queues with capacity weights to control channel distribution.

2. **Ignoring capacity weight tuning** — Deploying multi-channel Omni-Channel with default or guessed capacity weights and never adjusting them. Weights must be calibrated against observed average handle times per channel. A chat that takes 8 minutes should have a different weight than a phone call averaging 15 minutes. Schedule quarterly capacity weight reviews using Omni-Channel reports.

3. **Designing around legacy Live Agent** — Building new multi-channel architectures on Live Agent instead of Messaging for In-App/Web. Live Agent is legacy as of Spring '24 (Messaging GA). New implementations should use Messaging exclusively. Existing Live Agent deployments should have a migration timeline.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Messaging for In-App and Web Overview — https://help.salesforce.com/s/articleView?id=sf.livemessage_overview.htm
- Service Cloud Voice Overview — https://help.salesforce.com/s/articleView?id=sf.voice_about.htm
