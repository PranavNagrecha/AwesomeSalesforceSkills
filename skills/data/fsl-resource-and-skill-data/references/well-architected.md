# Well-Architected Notes — FSL Resource and Skill Data

## Relevant Pillars

- **Reliability** — Certification data with EffectiveEndDate prevents unqualified resources from being scheduled for work requiring those certifications. Incorrect SkillLevel mapping or missing expiry dates creates a scheduling reliability gap where unqualified technicians receive appointments.
- **Performance** — Resources with a large number of ServiceResourceSkill records (especially expired ones) can slow scheduling engine skill matching. Periodically archiving or marking old expired skills as inactive improves scheduling query performance at scale.
- **Security** — Resource and skill data may include personally identifiable HR information (certification types, dates). Restrict access to ServiceResourceSkill records to dispatchers and HR roles via OWD and sharing rules.

## Architectural Tradeoffs

**Certification tracking via date range vs. custom certification object:** FSL's native mechanism for certification expiry is EffectiveEndDate on ServiceResourceSkill. This is sufficient for scheduling enforcement but lacks reminder workflows and renewal tracking. If certification management is a core business process, consider a custom certification object that drives ServiceResourceSkill lifecycle via automation.

**Fine-grained vs. coarse SkillLevel scale:** A 0–99999 range allows precise differentiation, but a simple scale (1=basic, 50=intermediate, 99=certified) is easier to maintain and sufficient for most scheduling policies. Choose the scale based on how many distinct competency levels the scheduling policy actually needs to distinguish.

## Anti-Patterns

1. **Loading SkillLevel as text** — SkillLevel is integer. Text values fail silently or error. Always transform source labels to a defined numeric mapping before loading.
2. **Not setting EffectiveEndDate on expiring certifications** — Resources with expired certifications continue appearing as scheduling candidates until EffectiveEndDate is set. Omitting expiry dates creates a scheduling compliance gap.
3. **Defining SkillLevel scale without checking SkillRequirement MinimumSkillLevel** — Mismatch between loaded SkillLevel scale and existing MinimumSkillLevel values makes appointments unschedulable.

## Official Sources Used

- ServiceResourceSkill (Field Service Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_data_model_service_resource_skill.htm
- Create Skills for Field Service (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_skills.htm
- ServiceResourceCapacity Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_serviceresourcecapacity.htm
- FSL Core Data Model Gallery (architect.salesforce.com) — https://architect.salesforce.com/diagrams/framework/data-model-gallery
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
