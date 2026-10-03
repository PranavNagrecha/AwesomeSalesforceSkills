import { DefineWorkflow, Schema } from "deno-slack-sdk/mod.ts";
import { Connectors } from "deno-slack-hub/mod.ts";

export const LogFollowUpWorkflow = DefineWorkflow({
  callback_id: "log_follow_up",
  title: "Log a Salesforce follow-up",
  input_parameters: {
    properties: {
      interactivity: { type: Schema.slack.types.interactivity },
      channel_id: { type: Schema.slack.types.channel_id },
      opportunity_id: { type: Schema.types.string },
      task_subject: { type: Schema.types.string },
    },
    required: ["interactivity", "channel_id", "opportunity_id", "task_subject"],
  },
});

const runFlow = LogFollowUpWorkflow.addStep(Connectors.Salesforce.functions.RunFlow, {
  flow_name: "AL_Slack_Log_Follow_Up",
  metadata: {
    opportunityId: LogFollowUpWorkflow.inputs.opportunity_id,
    taskSubject: LogFollowUpWorkflow.inputs.task_subject,
  },
  // Each person authenticates their own Salesforce account; requires a link trigger.
  salesforce_access_token: { credential_source: "END_USER" },
});

LogFollowUpWorkflow.addStep(Schema.slack.functions.SendMessage, {
  channel_id: LogFollowUpWorkflow.inputs.channel_id,
  message: `Follow-up logged in Salesforce (flow ${runFlow.outputs.flow_name}).`,
});

export default LogFollowUpWorkflow;
