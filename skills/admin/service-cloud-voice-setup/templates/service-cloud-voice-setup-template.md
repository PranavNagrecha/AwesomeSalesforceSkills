# Service Cloud Voice Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `service-cloud-voice-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Voice add-on license active?** Yes / No
- **My Domain deployed to all users?** Yes / No
- **Omni-Channel enabled?** Yes / No
- **Existing Amazon Connect instance to import?** Yes (instance ARN: ___) / No (wizard will create new)
- **Transcription required?** Yes / No
- **After Conversation Work Time required?** Yes / Max ACW duration: ___ seconds
- **AWS region for contact center:** ___
- **Number of phone numbers to claim:** ___

## Approach

Which pattern from SKILL.md applies?

- [ ] Greenfield provisioning via guided wizard (no existing Amazon Connect instance)
- [ ] Import of existing Amazon Connect instance
- [ ] Enabling transcription on existing contact center
- [ ] Configuring After Conversation Work Time only

**Reason for chosen pattern:** (explain)

## Provisioning Checklist

Copy and tick as you complete each step:

- [ ] Prerequisites verified (license, My Domain, Omni-Channel, admin permission set)
- [ ] Guided wizard started at Setup > Service Cloud Voice > Contact Centers > New
- [ ] Amazon Connect instance provisioned (or imported) without error
- [ ] Phone number(s) claimed and associated with inbound contact flow
- [ ] Voice service channel (VoiceCall) confirmed in Omni-Channel > Service Channels
- [ ] Voice service channel added to Omni-Channel queue and routing configuration
- [ ] Service Cloud Voice permission set assigned to agents
- [ ] Service Cloud Voice Transcription permission set assigned to supervisors (if transcription enabled)
- [ ] Live Media Streaming enabled in AWS console (required for transcription)
- [ ] Call Transcription enabled on Salesforce contact center record (if transcription enabled)
- [ ] After Conversation Work Time duration configured in Setup
- [ ] After Conversation Work Time enabled on contact center record (if ACW required)
- [ ] End-to-end test call completed (inbound call routed, VoiceCall record created)
- [ ] Transcript verified on VoiceCall record during live call (if transcription enabled)
- [ ] ACW presence status verified after call completion (if ACW enabled)
- [ ] No orphaned Amazon Connect instances in AWS from failed partial runs

## AWS Configuration Summary

| Setting | Value |
|---|---|
| Amazon Connect instance alias | |
| AWS region | |
| Phone number(s) claimed | |
| Live Media Streaming enabled | Yes / No |
| Kinesis Video Stream name | |

## Notes

Record any deviations from the standard pattern and why.
