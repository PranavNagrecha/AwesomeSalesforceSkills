

## Education Cloud Developer
## Guide
## Version 66.0, Spring ’26
Last updated: April 3, 2026

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
Chapter 1: Introduction to Education Cloud. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Chapter 2: Release Notes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
Chapter 3: Education Cloud Data Model Overview. . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Chapter 4: Education Cloud Standard Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
AcademicCredential. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
AcademicInterest. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
AcademicOrder. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
AcademicSession. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
AcademicTerm. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
AcademicTermEnrollment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
AcademicTermPolicyRule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
AcadTermEnrlPolicyRuleLog. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 32
AcademicTermRegstrnTimeline. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36
AcademicYear. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
ApplicationDecision. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
ApplicationRecommendation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
ApplicationRecommender. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
ApplicationRenderMethod. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
ApplnRenderMethodAssignment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 54
ApplicationReview. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 56
ApplicationSectionDefinition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61
ApplicationStageDefinition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
ApplnStageSectionDefinition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
ApplicationTimeline. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 65
CaseTeamMemberProgram. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 68
CompetencyRelatedObject. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 70
ConstituentRole. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 73
ContactProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 77
CourseCreditTransferAppln. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 84
CourseOfferingParticipant. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 92
CourseOfrPtcpActvtyGrd. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 98
CourseOfferingPtcpResult. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
CourseOfrgRubricCriterion. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 106
CourseOfferingSchedule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 109
CourseOfferingScheduleTmpl. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
EducationalCharacteristic. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
EducCharacteristicAssignment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 121

EducCharacteristicType. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 125
EducCharReqAssignment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 127
EducCharReqRelationship. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 130
EducCharRequirement. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 132
EducationalInfoRequest. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 135
EducInstitutionOffering. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 138
EducInstSearchableProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 142
ExternalLearning. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 165
IndividualApplicationTask. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 169
IndividualApplicationTaskItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 173
InvolvementGroup. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 174
InvolvementGroupMember. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 179
LearnerPathway. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 183
LearnerPathwayItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 186
LearnerProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 191
LearnerProgram. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 201
LearnerProgramRequirement. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 206
LearnerProgramRqmtProgress. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 209
Learning. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 212
LearningAchievement. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 217
LearningCourse. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 221
LearningEquivalency. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 228
LearningEquivalencyLearning. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 231
LearningEqvAchvMapping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 232
LearningFoundationItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 234
LearningOutcomeItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 238
LearningPathwayTemplate. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 241
LearningPathwayTemplateItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 243
LearningPathwayTmplPgmPlan. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 247
LearningProgram. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 249
LearningProgramPlan. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 255
LearningProgramPlanRqmt. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 259
LearningRule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 262
MentoringProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 265
PersonAcademicCredential. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 268
PersonAffinity. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 271
PersonDisability. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 274
PersonPublicProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 278
PersonPublicProfilePrefSet. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 282
PersonTrait. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 285
PriceBookAcademicInterval. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 288
PriorLearningEvaluation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 290
ProgramTermApplnTimeline. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 293
PulseCheck. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 296
## Contents

PulseCheckTemplate. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 301
ProviderOffering. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 305
RgltyCodeRegClauseVer. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 308
RgltyCodeViolRegClVer. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 309
SuccessTeam. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 311
WatchlistedLearner. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 315
WorkTypeGroupRole. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 319
Chapter 5: Education Cloud Fields on Standard Objects. . . . . . . . . . . . . . . . . . . . . . 321
ActionPlanTemplate. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 322
ActionPlanTemplateAssignment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 322
Assessment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 324
AssessmentEnvelope. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 324
AssessmentEnvelopeItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 326
AssessmentQuestion. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 326
AssessmentQuestionResponse. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 327
Award. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 328
Benefit. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 328
BenefitAssignment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 329
BenefitDisbursement. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 330
BenefitType. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 331
BusinessOperationsProcess. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 332
BusinessProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 332
ComplianceControl. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 335
CourseOffering. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 335
CourseOfferingRelationship. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 338
DocumentChecklistItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 340
GiftCommitmentSchedule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 341
GoalAssignment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 342
GoalDefinition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 343
IndividualApplication. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 344
Location. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 348
PersonCompetency. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 348
PersonEducation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 349
PersonEmployment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 352
PersonExamination. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 362
PersonLifeEvent. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 369
PreliminaryApplicationRef. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 370
Program. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 372
RecurrenceSchedule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 373
RegulatoryCode. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 374
ServiceTerritoryMember. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 375
Waitlist. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 375
## Contents

Chapter  6:  Education  Cloud  Associated  Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . 377
StandardObjectNameChangeEvent. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 378
StandardObjectNameFeed. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 379
StandardObjectNameHistory. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 385
StandardObjectNameOwnerSharingRule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 387
StandardObjectNameShare. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 389
Chapter 7: Education Cloud Standard Value Set Names and Standard Picklist
Fields. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 391
Chapter 8: Education Cloud Tooling API Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . 395
CourseWaitlistConfig. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 396
LearningAchievementConfig. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 397
LocationUse. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 400
Chapter  9:  Education  Cloud  Business  APIs. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 403
REST  Reference. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 404
Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 404
Request  Bodies. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 417
Response  Bodies. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 442
Chapter  10:  Fundraising. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 477
Fundraising  Standard  Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 478
DocGenerationQueryResult. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 480
DonorGiftConcept. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 482
DonorGiftConceptOpportunity. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 488
DonorGiftSummary. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 490
GiftActuarialEntry. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 504
GiftStewardship. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 509
GiftStewardshipActivity. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 513
GiftAgreement. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 516
GiftBatch. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 519
GiftCommitment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 523
GiftCmtChangeAttrLog. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 534
GiftCommitmentSchedule. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 538
GiftDefaultDesignation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 545
GiftDefaultSoftCredit. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 547
GiftDesignation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 550
GiftEntry. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 556
GiftRefund. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 569
GiftSoftCredit. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 573
GiftTransaction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 576
GiftTransactionDesignation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 588
GiftTribute. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 591
GiftValueForecast. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 596
## Contents

OutreachSourceCode. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 599
OutreachSummary. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 604
PartyCategory. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 609
PartyPhilanthropicAssessment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 612
PartyPhilanthropicIndicator. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 621
PartyPhilanthropicMilestone. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 628
PartyPhilanthropicOccurrence. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 636
PartyPhilanthropicRsrchPrfl. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 642
PaymentInstrument. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 647
PlannedGift. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 652
PlannedGiftAnnuityRate. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 664
PlannedGiftPerformance. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 667
Fundraising  Fields  on  Other  Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 670
ContactPointAddress. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 671
ContactProfile. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 678
ListEmail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 681
Fundraising Business APIs. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 686
Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 687
Request  Bodies. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 701
Response  Bodies. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 727
Fundraising  Invocable  Actions. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 750
Close Gift Commitment Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 750
Manage Custom Gift Commitment Schedules Action. . . . . . . . . . . . . . . . . . . . . . . . . 751
Manage  Gift  Default  Designations  Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 753
Manage Gift Transaction Designations Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 755
Manage Recurring Gift Commitment Schedule Action. . . . . . . . . . . . . . . . . . . . . . . . 756
Process Gift Entries Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 758
Pause Gift Commitment Schedule Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 761
Process  Gift  Commitment  Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 763
Resume  Gift  Commitment  Schedule  Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 764
Update  Processed  Gift  Entries  Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 766
Fundraising Metadata API Types. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 768
AffinityScoreDefinition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 768
Flow  for  Fundraising. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 773
Fundraising  Tooling  API  Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 774
FundraisingConfig. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 775
FieldMappingConfig. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 780
FieldMappingConfigItem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 783
GiftEntryGridTemplate. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 784
## Contents



CHAPTER 1Introduction to Education Cloud
## EDITIONS
Available in: Lightning
## Experience
in Performance, Enterprise,
## Developer,
and Unlimited editions that
have Education Cloud
enabled.
Use Education Cloud to support the entire learner experience,
including managing applications, scheduling, courses, facilities,
and more.
Education Cloud draws on the power of Salesforce to connect
insights across recruitment, admissions, and student success for a
unified view of every learner's journey. With Salesforce at the center
of your institution's information technology solution, important
tasks can be completed in less time, at scale, and in collaboration
between departments. A single source of truth creates a complete
student profile, so your institution can offer personalized
experiences that translate into successful lifetime learners — from
prospective student to engaged alum.
## 1

CHAPTER 2Release Notes
View the latest features from Education Cloud.
## Education Cloud Release Notes
## 2

CHAPTER 3Education Cloud Data Model Overview
## EDITIONS
Available in: Lightning
## Experience
in Performance, Enterprise,
## Developer,
and Unlimited editions that
have Education Cloud
enabled.
Learn about the objects and relationships within the Education
Cloud data model.
View entity relationship diagrams from Education Cloud on the
Salesforce Architects site to understand associations between the
objects:
## •
## Education Cloud Academic Operations Data Model
## •
Education Cloud Recruitment and Admissions Data Model
## •
## Education Cloud Student Success Data Model
## •
## Education Cloud Appointment Scheduling Data Model
## •
## Education Cloud Fundraising Data Model
## 3

CHAPTER 4Education Cloud Standard Objects
## EDITIONS
Available in: Lightning
## Experience
in Performance, Enterprise,
## Developer,
and Unlimited editions that
have Education Cloud
enabled.
This section lists standard objects available for use with Education
## Cloud.
Some fields may not be listed for some objects. To see the system
fields for each object, see System Fields in the Object Reference for
Salesforce and Lightning Platform.
To verify the complete list of fields for an object, use a describe call
from the API or inspect with an appropriate tool. For example,
inspect the WSDL or use a schema viewer.
In this chapter ...
•AcademicCredential
•AcademicInterest
•AcademicOrder
•AcademicSession
•AcademicTerm
•AcademicTermEnrollment
•AcademicTermPolicyRule
•AcadTermEnrlPolicyRuleLog
•AcademicTermRegstrnTimeline
•AcademicYear
•ApplicationDecision
•ApplicationRecommendation
•ApplicationRecommender
•ApplicationRenderMethod
•ApplnRenderMethodAssignment
•ApplicationReview
•ApplicationSectionDefinition
•ApplicationStageDefinition
•ApplnStageSectionDefinition
•ApplicationTimeline
•CaseTeamMemberProgram
•CompetencyRelatedObject
•ConstituentRole
•ContactProfile
•CourseCreditTransferAppln
•CourseOfferingParticipant
•CourseOfrPtcpActvtyGrd
•CourseOfferingPtcpResult
•CourseOfrgRubricCriterion
•CourseOfferingSchedule
•CourseOfferingScheduleTmpl
•EducationalCharacteristic
•EducCharacteristicAssignment
•EducCharacteristicType
•EducCharReqAssignment
•EducCharReqRelationship
## 4

•EducCharRequirement
•EducationalInfoRequest
•EducInstitutionOffering
•EducInstSearchableProfile
•ExternalLearning
•IndividualApplicationTask
•IndividualApplicationTaskItem
•InvolvementGroup
•InvolvementGroupMember
•LearnerPathway
•LearnerPathwayItem
•LearnerProfile
•LearnerProgram
•LearnerProgramRequirement
•LearnerProgramRqmtProgress
•Learning
•LearningAchievement
•LearningCourse
•LearningEquivalency
•LearningEquivalencyLearning
•LearningEqvAchvMapping
•LearningFoundationItem
•LearningOutcomeItem
•LearningPathwayTemplate
•LearningPathwayTemplateItem
•LearningPathwayTmplPgmPlan
•LearningProgram
•LearningProgramPlan
•LearningProgramPlanRqmt
•LearningRule
•MentoringProfile
•PersonAcademicCredential
•PersonAffinity
•PersonDisability
•PersonPublicProfile
•PersonPublicProfilePrefSet
•PersonTrait
•PriceBookAcademicInterval
•PriorLearningEvaluation
•ProgramTermApplnTimeline
•PulseCheck
•PulseCheckTemplate
## 5
## Education Cloud Standard Objects

•ProviderOffering
•RgltyCodeRegClauseVer
•RgltyCodeViolRegClVer
•SuccessTeam
•WatchlistedLearner
•WorkTypeGroupRole
## 6
## Education Cloud Standard Objects

AcademicCredential
A credential which can be earned by learners. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
IssuerId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account of the issuer institution associated with the Academic Credential.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Academic Credential.
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of Academic Credential.
Possible values are:
## •
AssociateDegree
## •
Bachelor'sDegree
## •
## Badge
## •
DoctoralDegree
## •
## Certificate
## •
Master'sDegree
## •
SecondaryDiploma
## 7
AcademicCredentialEducation Cloud Standard Objects

AcademicInterest
Represents a person's academic interest. This object is available in API version 62.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Term associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Refers To
AcademicTerm
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact associated with the Academic Interest.
## 8
AcademicInterestEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
reference
ContactRequestId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact Request associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
ContactRequest
## Refers To
ContactRequest
## Type
reference
EducationalInfoRequestId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Educational Info Request associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
EducationalInfoRequest
## Refers To
EducationalInfoRequest
## Type
reference
IndividualApplicationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Individual Application associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
IndividualApplication
## Refers To
IndividualApplication
## 9
AcademicInterestEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LeadId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The lead for the person who expressed the Academic Interest.
This field is a relationship field.
## Relationship Name
## Lead
## Refers To
## Lead
## Type
reference
LearningProgramId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning Program associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
LearningProgram
## Refers To
LearningProgram
## 10
AcademicInterestEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string or number assigned to the Academic Interest.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Opportunity associated with the Academic Interest.
This field is a relationship field.
## Relationship Name
## Opportunity
## Refers To
## Opportunity
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
date
ReceivedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the interest from the person was received.
## Type
picklist
## Source
## 11
AcademicInterestEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the source from where the Academic Interest was sent.
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the Academic Interest.
## Type
string
## Subscription
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The subscription that the person is requesting.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AcademicInterestHistory on page 385
History is available for tracked fields of the object.
AcademicInterestOwnerSharingRule on page 387
Sharing rules are available for the object.
AcademicInterestShare on page 389
Sharing is available for the object.
AcademicOrder
Represents a junction between an academic interval, such as an academic term, and an order. This object is available in API version 66.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 12
AcademicOrderEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
AcademicIntervalId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The academic interval that's associated with the order.
This field is a polymorphic relationship field.
## Relationship Name
AcademicInterval
## Refers To
AcademicSession, AcademicTerm, AcademicYear
## Type
reference
ContactId
## Properties
## Filter, Group, Nillable, Sort
## Description
The contact that's associated with the Academic Order.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
string
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the academic order.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 13
AcademicOrderEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the academic order.
## Type
string
OrderDetailsIdentifier
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The execution identifier that's associated with the academic order.
## Type
reference
OrderId
## Properties
## Create, Filter, Group, Sort
## Description
The order that's associated with the academic order.
This field is a relationship field.
## Relationship Name
## Order
## Relationship Type
## Master-detail
## Refers To
Order (the master object)
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
## 14
AcademicOrderEducation Cloud Standard Objects

AcademicOrderFeed on page 379
Feed tracking is available for the object.
AcademicOrderHistory on page 385
History is available for tracked fields of the object.
AcademicSession
Records course offering period. Specifies time periods based on an institution’s calendar whether that is semesters, quarters, trimesters,
or other terms. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Term associated with the Academic Session.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Relationship Type
## Lookup
## Refers To
AcademicTerm
## Type
dateTime
AddDropDeadline
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The last date when a student can add or drop a course, without a record of registration on
their academic period.
## Type
dateTime
AuditDueDate
## 15
AcademicSessionEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The last date for a student to audit a course and take it without seeking a grade or credit.
## Type
dateTime
ClassEndDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when classes end for the Academic Session.
## Type
dateTime
ClassStartDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when classes start for the Academic Session.
## Type
dateTime
CourseWithdrawDeadline
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when withdraw from a course is recorded on the student’s academic record.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Academic Session.
## Type
dateTime
ExamEndDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when exams for the Academic Session end.
## Type
dateTime
ExamStartDate
## 16
AcademicSessionEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when exams for the Academic Session start.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Academic Session is active (true) or not (false).
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## 17
AcademicSessionEducation Cloud Standard Objects

DetailsField
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
dateTime
ResultAvailabilityDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when the result of the course offering is announced.
## Type
dateTime
ResultDueDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The last date to submit the result of a course offering, such as grades.
## 18
AcademicSessionEducation Cloud Standard Objects

DetailsField
## Type
restricted picklist
## Season
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the season related to the Academic Session.
Possible values are:
## •
## Fall
## •
## Spring
## •
## Summer
## •
## Winter
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the type of Academic Session.
Possible values are:
## •
FirstSemester
## •
MiniTerm
## •
## Others
## •
## Quarter
## •
SecondSemester
## •
## Semester
## •
## Term1
## •
## Term2
## •
## Term3
## •
## Term4
## •
## Trimester
AcademicTerm
Defines an academic period which may hold other more defined time periods within it to create a specific time for reporting and offerings.
This object is available in API version 57.0 and later.
## 19
AcademicTermEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicYearId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic year that's associated with the Academic Term.
This field is a relationship field.
## Relationship Name
AcademicYear
## Relationship Type
## Lookup
## Refers To
AcademicYear
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Academic Term.
## Type
dateTime
EndDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when the Academic Term ends.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Academic Term is active (true) or not (false).
## 20
AcademicTermEducation Cloud Standard Objects

DetailsField
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
dateTime
LateRegistrationDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date from when the applications are considered as late submissions.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## 21
AcademicTermEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
dateTime
RegistrationCloseDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The last date for the students to register for the Academic Term.
## Type
dateTime
RegistrationOpenDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date from when the students can begin to register for the Academic Term.
## Type
picklist
## Season
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the season related to the Academic Term.
## 22
AcademicTermEducation Cloud Standard Objects

DetailsField
Possible values are:
## •
## Fall
## •
## Spring
## •
## Summer
## •
## Winter
## Type
dateTime
StartDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when the Academic Term starts.
AcademicTermEnrollment
Represents information about a student's enrollment in an Academic Term. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
AcademicStanding
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The learner's performance and progress for the term.
Possible values are:
## •
AcademicDismissal
## •
AcademicProbation
## •
AcademicWarning
## •
GoodStanding
## •
Honors/Dean'sList
## •
ReinstatementStatus
## 23
AcademicTermEnrollmentEducation Cloud Standard Objects

DetailsField
## •
RequiredWithdrawal
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Term associated with the Academic Term Enrollment.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Relationship Type
## Lookup
## Refers To
AcademicTerm
## Type
reference
AcademicTermRegstrnTimelineId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Term Registration Timeline associated with the Academic Term Enrollment.
This field is a relationship field.
## Relationship Name
AcademicTermRegstrnTimeline
## Refers To
AcademicTermRegstrnTimeline
## Type
double
CumulativeGradePointAverage
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The learner's cumulative grade point average, that is the average of all grade points achieved.
## Type
date
EnrollmentDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date that the student enrolled in the Academic Term.
## 24
AcademicTermEnrollmentEducation Cloud Standard Objects

DetailsField
## Type
picklist
EnrollmentReason
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The reason the student enrolled in the Academic Term.
Possible values are:
## •
## Continuing
## •
FirstTime
## •
## Re-admit
## •
## Transferin
## Type
picklist
EnrollmentStatus
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the status of a student's enrollment in the Academic Term.
Possible values are:
## •
## Active
## •
## Dropout
## •
## Expelled
## •
## Graduated
## •
No show
## •
## Other
## •
## Transferred
## •
## Withdrawn
## Type
date
ExitDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the student left the institution.
## Type
string
ExitReason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 25
AcademicTermEnrollmentEducation Cloud Standard Objects

DetailsField
## Description
The reason that the student left the institution.
## Type
int
HoursAttempted
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of credit hours or contact hours attempted by a student during the Academic
## Term.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearnerAccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account of the person associated with the Academic Term Enrollment.
## 26
AcademicTermEnrollmentEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
LearnerAccount
## Relationship Type
## Lookup
## Refers To
## Account
## Type
reference
LearnerContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact person associated with the Academic Term Enrollment.
This field is a relationship field.
## Relationship Name
LearnerContact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 27
AcademicTermEnrollmentEducation Cloud Standard Objects

DetailsField
## Description
The Opportunity associated with the Academic Term Enrollment.
## Relationship Name
## Opportunity
## Relationship Type
## Lookup
## Refers To
## Opportunity
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
StudentAcademicLevel
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the student's applicable point in the education process.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## •
ProfessionalEducation
## •
## Undergraduate
## 28
AcademicTermEnrollmentEducation Cloud Standard Objects

DetailsField
## Type
picklist
StudyYearClassification
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the student's year of study classification.
Possible values are:
## •
## Freshman
## •
## Junior
## •
## Senior
## •
## Sophomore
## Type
string
TermGradePointAverage
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learner's grade point average for the Academic Term.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AcademicTermEnrollmentFeed on page 379
Feed tracking is available for the object.
AcademicTermEnrollmentHistory on page 385
History is available for tracked fields of the object.
AcademicTermEnrollmentShare on page 389
Sharing is available for the object.
AcademicTermPolicyRule
Represents a junction between Academic Term and Expression Set objects where an expression set is used as a policy rule for the
academic term. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 29
AcademicTermPolicyRuleEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The parent Academic Term associated with the Policy Rule.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Relationship Type
## Master-detail
## Refers To
AcademicTerm (the master object)
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Academic Term Policy Rule.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Academic Term Policy Rule.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 30
AcademicTermPolicyRuleEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Name of the Academic Term Policy Rule.
## Type
reference
PolicyRuleId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Expression Set that's used as the policy rule for the associated Academic Term.
This field is a relationship field.
## Relationship Name
PolicyRule
## Refers To
ExpressionSet
## Type
picklist
UsageType
## Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
## Description
Specifies the usage type of the Academic Term Policy Rule.
Possible values are:
## •
Bre—Default
## •
GpaCalculation—GPA Calculation
## 31
AcademicTermPolicyRuleEducation Cloud Standard Objects

DetailsField
The default value is Bre.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AcademicTermPolicyRuleHistory on page 385
History is available for tracked fields of the object.
AcadTermEnrlPolicyRuleLog
Represents the log of the policy rule calculation runs for an academic term enrollment. This object is available in API version 64.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermEnrollmentId
## Properties
## Create, Filter, Group, Sort
## Description
The Academic Term Enrollment associated with the Academic Term Enrollment Policy Rule
## Log.
This field is a relationship field.
## Relationship Name
AcademicTermEnrollment
## Relationship Type
## Master-detail
## Refers To
AcademicTermEnrollment (the master object)
## Type
reference
AcademicTermId
## 32
AcadTermEnrlPolicyRuleLogEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Group, Sort
## Description
The Academic Term associated with the Academic Term Enrollment Policy Rule Log.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Refers To
AcademicTerm
## Type
dateTime
CalculatedDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date on which the result is calculated.
## Type
double
CalculatedNumericResult
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The numeric result that's calculated using the Policy Rule.
## Type
string
CalculatedTextResult
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The text result that's calculated using the Policy Rule.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Academic Term Enrollment Policy Rule
## Log.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
## 33
AcadTermEnrlPolicyRuleLogEducation Cloud Standard Objects

DetailsField
The default value is USD.
## Type
string
JobIdentifier
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The identifier for the job that calculates the result.
## Type
picklist
JobType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of job that's run using the policy rule.
Possible values are:
## •
## Adhoc
## •
## Batch
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Academic Term Enrollment Policy Rule Log.
## 34
AcadTermEnrlPolicyRuleLogEducation Cloud Standard Objects

DetailsField
## Type
reference
PolicyRuleId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Policy Rule expression set associated with the Academic Term Enrollment Policy Rule
## Log.
This field is a relationship field.
## Relationship Name
PolicyRule
## Refers To
ExpressionSet
## Type
dateTime
PublishedDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date on which the result is published.
## Type
picklist
## Scope
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the scope of the Academic Term Enrollment Policy Rule Log.
Possible values are:
## •
HoldsAndBlock—Holds and Block
## •
RegistrationTimeline—Registration Timeline
## •
TermGpa—Term GPA
## Type
picklist
## Status
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies whether the result is calculated or published.
Possible values are:
## •
## Calculated
## •
## Published
## 35
AcadTermEnrlPolicyRuleLogEducation Cloud Standard Objects

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AcadTermEnrlPolicyRuleLogHistory on page 385
History is available for tracked fields of the object.
AcademicTermRegstrnTimeline
Represents the registration time window for an academic term. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The academic term associated with the academic term registration timeline.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Refers To
AcademicTerm
## Type
picklist
## Category
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the category of the academic term related to the academic term registration timeline.
Possible values are:
## •
EarlyDecision
## •
RegularDecision
## 36
AcademicTermRegstrnTimelineEducation Cloud Standard Objects

DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the academic term registration timeline.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
string
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the academic term registration timeline.
## Type
reference
EligibilityCriteriaId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
TThe Eligibility Criteria expression set associated with the Academic Term Registration
## Timeline.
This field is a relationship field.
## Relationship Name
EligibilityCriteria
## Refers To
ExpressionSet
## Type
boolean
IsDefault
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the academic term registration timeline is the default for the related
academic term (true) or not (false).
The default value is false.
## 37
AcademicTermRegstrnTimelineEducation Cloud Standard Objects

DetailsField
## Type
boolean
IsPublished
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the academic term registration timeline is published (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the academic term registration timeline.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## 38
AcademicTermRegstrnTimelineEducation Cloud Standard Objects

DetailsField
## Refers To
## Group, User
## Type
dateTime
RegistrationCloseDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when registration closes.
## Type
dateTime
RegistrationOpenDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when registration opens.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AcademicTermRegstrnTimelineHistory on page 385
History is available for tracked fields of the object.
AcademicTermRegstrnTimelineOwnerSharingRule on page 387
Sharing rules are available for the object.
AcademicTermRegstrnTimelineShare on page 389
Sharing is available for the object.
AcademicYear
Defines an academic year period. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 39
AcademicYearEducation Cloud Standard Objects

## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Academic Year.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## 40
AcademicYearEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
string
## Year
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the Academic Year.
ApplicationDecision
Represents information about the academic standing of an applicant. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 41
ApplicationDecisionEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account associated with the Application Decision.
This field is a relationship field.
## Relationship Name
## Account
## Relationship Type
## Lookup
## Refers To
## Account
## Type
picklist
ApplicantDecision
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the applicant’s decision.
Possible values are:
## •
## Accept
## •
## Decline
## •
## Defer
## •
## Withdraw
## Type
picklist
ApplicationDecision
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the decision on the application.
Possible values are:
## •
## Admit
## •
## Cancelled
## •
## Deny
## •
## Enroll
## •
## Waitlist
## 42
ApplicationDecisionEducation Cloud Standard Objects

DetailsField
## Type
reference
ApplicationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The application for which the decision is announced.
This field is a polymorphic relationship field.
## Relationship Name
## Application
## Relationship Type
## Lookup
## Refers To
IndividualApplication
## Type
textarea
## Comment
## Properties
## Create, Nillable, Update
## Description
The information about the decision provided on the application.
## Type
reference
DecisionAuthorityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Identifier for the decision authority person.
## Relationship Name
DecisionAuthority
## Relationship Type
## Lookup
## Refers To
## User
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## 43
ApplicationDecisionEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## 44
ApplicationDecisionEducation Cloud Standard Objects

DetailsField
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
PreliminaryApplicationRefId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Identifier for the preliminary application reference.
## Relationship Name
PreliminaryApplicationRef
## Relationship Type
## Lookup
## Refers To
PreliminaryApplicationRef
## Type
double
## Score
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The calculated score for assessments related to an application decision.
ApplicationRecommendation
Represents information about the recommendation for an individual application. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ApplicationRecommenderId
## 45
ApplicationRecommendationEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact associated with the recommendation as the recommender.
This field is a relationship field.
## Relationship Name
ApplicationRecommender
## Relationship Type
## Lookup
## Refers To
ApplicationRecommender
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
it’s possible the user accessed this record or list view (LastReferencedDate) but didn’t
view it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## 46
ApplicationRecommendationEducation Cloud Standard Objects

DetailsField
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
textarea
## Recommendation
## Properties
## Create, Nillable, Update
## Description
The content submitted as the recommendation.
## Type
reference
SurveyResponseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The survey response associated with the application recommendation.
This field is a relationship field. It’s available in API version 62.0 and later.
## Relationship Name
SurveyResponse
## 47
ApplicationRecommendationEducation Cloud Standard Objects

DetailsField
## Refers To
SurveyResponse
ApplicationRecommender
Represents a junction between an individual application and the recommender of the application. This object is available in API version
57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ApplicationId
## Properties
## Create, Filter, Group, Sort
## Description
The individual application that's associated with the recommender.
This field is a relationship field.
## Relationship Name
## Application
## Relationship Type
## Lookup
## Refers To
IndividualApplication
## Type
boolean
DoesSendSurvey
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether automation sends a recommendation survey to the recommender (true)
or not (false). This field is available in API version 62.0 and later.
The default value is false
## 48
ApplicationRecommenderEducation Cloud Standard Objects

DetailsField
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
it’s possible the user accessed this record or list view (LastReferencedDate) but didn’t
view it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## 49
ApplicationRecommenderEducation Cloud Standard Objects

DetailsField
## Type
picklist
RecommendationStatus
## Properties
Create, Filter, Restricted picklist, Group, Sort, Update
## Description
Specifies the status of the recommendation.
Possible values are:
## •
Canceled. This value is available in API version 62.0 and later.
## •
## Requested
## •
## Submitted
## Type
reference
RecommenderId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact associated with the application as a recommender.
This field is a relationship field.
## Relationship Name
## Recommender
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
date
SubmittedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the date on which the recommendation was submitted.
## Type
string
SurveyDeveloperName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The developer name of the survey sent to the recommender. This field is available in API
version 62.0 and later.
## 50
ApplicationRecommenderEducation Cloud Standard Objects

DetailsField
## Type
string
SurveySubject
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The ID of the survey subject record. Used for tracking recommender types. This field is available
in API version 62.0 and later.
## Type
date
VerificationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date and time of the recommendation verification. This field is available in API version
62.0 and later.
## Type
picklist
VerificationStatus
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The verification status of the application. This field is available in API version 62.0 and later.
Possible values are:
## •
## Accepted
## •
## Not Verified
## •
## Rejected
## •
## Waived
ApplicationRenderMethod
Represents how a part of an application can be rendered. This object is available in API version 60.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 51
ApplicationRenderMethodEducation Cloud Standard Objects

## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Application Render Method.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
textarea
MethodName
## Properties
## Create, Nillable, Update
## Description
The name of the render method associated with the application.
## Type
reference
MethodRecordId
## 52
ApplicationRenderMethodEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The record ID of the method that's associated with the Application Render Method.
This field is a polymorphic relationship field.
## Relationship Name
MethodRecord
## Relationship Type
## Lookup
## Refers To
OmniProcess, OmniUiCard
## Type
picklist
MethodType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of method that's used to render components in the application.
Possible values are:
## •
FlexCard
## •
OmniScript
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Application Render Method.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The owner of the Application Render Method.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## 53
ApplicationRenderMethodEducation Cloud Standard Objects

DetailsField
## Refers To
## Group, User
## Type
picklist
UsageType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the usage type of the Application Render Method.
Possible values are:
## •
RecruitmentAndAdmissions—Recruitment and Admissions
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
ApplicationRenderMethodHistory on page 385
History is available for tracked fields of the object.
ApplicationRenderMethodOwnerSharingRule on page 387
Sharing rules are available for the object.
ApplicationRenderMethodShare on page 389
Sharing is available for the object.
ApplnRenderMethodAssignment
Represents an assignment of the application render method to a component that's rendered in the application. This object is available
in API version 60.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ApplicationComponentId
## 54
ApplnRenderMethodAssignmentEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The component that's rendered in an application.
This field is a relationship field.
## Relationship Name
ApplicationComponent
## Relationship Type
## Lookup
## Refers To
ApplicationStageDefinition
## Type
reference
ApplicationRenderMethodId
## Properties
## Create, Filter, Group, Sort
## Description
The Application Render Method associated with the component that's rendered in an
application.
This field is a relationship field.
## Relationship Name
ApplicationRenderMethod
## Relationship Type
## Lookup
## Refers To
ApplicationRenderMethod
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
boolean
IsActive
## 55
ApplnRenderMethodAssignmentEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the assignment is active (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Application Render Method Assignment.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
ApplnRenderMethodAssignmentHistory on page 385
History is available for tracked fields of the object.
ApplnRenderMethodAssignmentOwnerSharingRule on page 387
Sharing rules are available for the object.
ApplnRenderMethodAssignmentShare on page 389
Sharing is available for the object.
ApplicationReview
Represents a review performed against the specified application. This object is available in API version 57.0 and later.
## 56
ApplicationReviewEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
AcademicTerm
## Properties
## Filter, Group, Nillable, Sort
## Description
Specifies the academic term associated with the application.
## Type
picklist
ApplicationCategory
## Properties
## Filter, Group, Nillable, Sort
## Description
Specifies the category of the application based on the admission decision period.
Possible values are:
## •
EarlyDecision
## •
RegularDecision
## Type
reference
ApplicationId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The application that is in review.
This field is a relationship field.
## Relationship Name
## Application
## Relationship Type
## Lookup
## Refers To
IndividualApplication
## Type
picklist
ApplicationRecommendation
## 57
ApplicationReviewEducation Cloud Standard Objects

DetailsField
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the recommendation provided by the reviewer for the application into the institution.
Possible values are:
## •
## Admit
## •
AdmitwithConditions
## •
## Deny
## •
## Pending
## Type
date
AssignedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the date on which the application is assigned for review.
## Type
textarea
## Comment
## Properties
## Create, Nillable, Update
## Description
The information added by the reviewer about the application that's in review.
## Type
textarea
## Condition
## Properties
## Create, Nillable, Update
## Description
The condition that’s applicable to an applicant.
## Type
date
DueDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last date by which the application review should be completed.
## Type
date
EndDate
## 58
ApplicationReviewEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the application review was completed.
## Type
reference
InstitutionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The institution's account related to the application review.
This field is a relationship field.
## Relationship Name
## Institution
## Refers To
## Account
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## 59
ApplicationReviewEducation Cloud Standard Objects

DetailsField
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ReviewedById
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Identifier of the reviewer of the application.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## User
## Type
double
## Score
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The calculated score for assessments related to an application review.
## Type
dateTime
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the application review started.
## 60
ApplicationReviewEducation Cloud Standard Objects

DetailsField
## Type
picklist
## Status
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the status of the application review.
Possible values are:
## •
## Cancelled
## •
## Completed
## •
## In Progress
## •
## Not Started
## Type
dateTime
SubmissionDate
## Properties
## Filter, Group, Nillable, Sort,
## Description
The date when the applicant submitted the application.
## Type
picklist
## Type
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the application review.
This field is available in API version 64.0 and later.
Possible values are:
## •
StaffReview
ApplicationSectionDefinition
Represents the section of an application. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 61
ApplicationSectionDefinitionEducation Cloud Standard Objects

## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Application Section Definition.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Application Section Definition is active (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Application Section Definition.
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the Application Section Definition.
Possible values are:
## •
## Recruitmentand Admissions
ApplicationStageDefinition
Represents a stage of an application. This object is available in API version 59.0 and later.
## 62
ApplicationStageDefinitionEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Application Stage Definition.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Application Stage Definition.
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the Application Stage Definition.
Possible values are:
## •
## Recruitmentand Admissions
ApplnStageSectionDefinition
Represents a junction between an application stage definition and application section definition. This object is available in API version
59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 63
ApplnStageSectionDefinitionEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
ApplicationSectionDefinitionId
## Properties
## Create, Filter, Group, Sort
## Description
The Application Section Definition associated with the Application Stage Section Definition.
This field is a relationship field.
## Relationship Name
ApplicationSectionDefinition
## Relationship Type
## Lookup
## Refers To
ApplicationSectionDefinition
## Type
reference
ApplicationStageDefinitionId
## Properties
## Create, Filter, Group, Sort
## Description
The Application Stage Definition associated with the Application Stage Section Definition.
This field is a relationship field.
## Relationship Name
ApplicationStageDefinition
## Relationship Type
## Lookup
## Refers To
ApplicationStageDefinition
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Application Stage Section Definition.
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## 64
ApplnStageSectionDefinitionEducation Cloud Standard Objects

DetailsField
## Description
Specifies the type of the Application Stage Section Definition.
Possible values are:
## •
## Recruitmentand Admissions
ApplicationTimeline
Represents the milestone dates in the application process. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
ApplicationCategory
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the category of the application based on the admission decision period.
Possible values are:
## •
EarlyDecision
## •
RegularDecision
## Type
date
ApplicationCloseDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last date when domestic applicants can apply for admission.
## Type
date
ApplicationOpenDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 65
ApplicationTimelineEducation Cloud Standard Objects

DetailsField
## Description
The date when applicants can start to apply for admission.
## Type
date
DecisionReleaseDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the application decision is announced.
## Type
date
EarlyActionCloseDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last date when applicants can apply for early action admission.
## Type
date
EarlyActionOpenDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when applicants can start to apply for early action admission.
## Type
date
EarlyApplicationCloseDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last date when applicants can apply early for admission.
## Type
date
EarlyApplicationOpenDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when applicants can start to apply early for admission.
## Type
date
EarlyApplnDecisionRelDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 66
ApplicationTimelineEducation Cloud Standard Objects

DetailsField
## Description
The date when the application decision for early applicants is announced.
## Type
date
GraduationApplnDeadline
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last date for the students to apply for graduation.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
## 67
ApplicationTimelineEducation Cloud Standard Objects

DetailsField
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of application timeline.
Possible values are:
## •
## Admissions
CaseTeamMemberProgram
Represents mapping information between Case Team Member and Program. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 68
CaseTeamMemberProgramEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Sort
## Description
The case that's associated with the case team member.
This field is a relationship field.
## Relationship Name
## Case
## Relationship Type
## Lookup
## Refers To
## Case
## Type
string
CaseTeamMember
## Properties
## Create, Filter, Group, Sort, Update
## Description
The case team member that is mapped to one or more programs.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 69
CaseTeamMemberProgramEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the case team member program record.
## Type
reference
ProgramId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The program that is mapped to case team members.
This field is a relationship field.
## Relationship Name
## Program
## Relationship Type
## Lookup
## Refers To
## Program
CompetencyRelatedObject
Represents a junction between competency and another object. This object is available in API version 64.0 and later.
## 70
CompetencyRelatedObjectEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
CompetencyId
## Properties
## Create, Filter, Group, Sort
## Description
The competency related to the object.
This field is a relationship field.
## Relationship Name
## Competency
## Relationship Type
## Master-detail
## Refers To
Competency (the master object)
## Type
picklist
CompetencyType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of the competency.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the competency related object.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## 71
CompetencyRelatedObjectEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the competency related object record.
## Type
reference
RelatedToId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The object related to the competency.
This field is a polymorphic relationship field.
## Relationship Name
RelatedTo
## Refers To
InvolvementGroup, LearningCourse, Program
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
CompetencyRelatedObjectHistory on page 385
History is available for tracked fields of the object.
## 72
CompetencyRelatedObjectEducation Cloud Standard Objects

ConstituentRole
Contains information about roles associated with the individual. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ContextRecordId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The record of the context that's associated with the constituent.
This field is a relationship field.
## Relationship Name
ContextRecord
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
string
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The short description of the constituent's role in the system.
## Type
date
EffectiveEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date from when the constituent role becomes inactive.
## Type
date
EffectiveStartDate
## 73
ConstituentRoleEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date from when the constituent role becomes active.
## Type
reference
InstitutionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The institution's account related to the constituent role.
This field is a relationship field.
## Relationship Name
## Institution
## Refers To
## Account
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## 74
ConstituentRoleEducation Cloud Standard Objects

DetailsField
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
PersonId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The individual associated with the constituent role.
This field is a polymorphic relationship field.
## Relationship Name
## Person
## Relationship Type
## Lookup
## 75
ConstituentRoleEducation Cloud Standard Objects

DetailsField
## Refers To
## Account, Contact, Individual
## Type
picklist
RoleType
## Properties
Create, Filter, Restricted picklist, Group, Sort, Update
## Description
Specifies the type of constituent role.
Possible values are:
## •
## Alumni
## •
## Applicant
## •
## Donor
## •
## Faculty
## •
## Mentee
## •
## Mentor
## •
## Parent
## •
## Participant
## •
PhilanthropicProspect
## •
## Prospect
## •
## Staff
## •
## Student
## •
## Suspect
## •
## Volunteer
## Type
picklist
## Status
## Properties
Create, Filter, Restricted picklist, Group, Sort, Update
## Description
The status of the constituent role.
Possible values are:
## •
## Active
## •
## Admitted
## •
## Current
## •
## Enrolled
## •
## Former
## 76
ConstituentRoleEducation Cloud Standard Objects

ContactProfile
Represents information about an individual, such as their ethnicity, citizenship, birth place, race, and so on. This object is available in API
version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
date
AdvancementGraduationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the person's first graduation from your institution.
## Type
picklist
AdvancementType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The classification that matches the role or relationship of the person with the institution.
Possible values are:
## •
## Alumni
## •
Faculty/Staff
## •
OtherIndividual
## •
## Parent
## •
PublicInstitutionFoundationBoardMember
## •
## Student
## •
Trustee/Boardof Directors
## Type
reference
BirthCountryId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The individual's country of birth.
## 77
ContactProfileEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
BirthCountry
## Relationship Type
## Lookup
## Refers To
GeoCountry
## Type
string
BirthPlace
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The individual's place of birth.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort
## Description
The contact associated with the contact profile record.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
picklist
## Ethnicity
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the ethnicity of the individual.
Possible values are:
## •
## Hispanicor Latino
## •
## Not Hispanicor Latino
## •
## Not Selected
## 78
ContactProfileEducation Cloud Standard Objects

DetailsField
## Type
picklist
GenerationalCohort
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The person's age group, or generational cohort, based on their birth date.
Possible values are:
## •
BabyBoomers(1946-1964)
## •
GenerationAlpha(2013-2025)
## •
GenerationX (1965-1980)
## •
GenerationZ (1997-2012)
## •
## Millennials(1981-1996)
## •
SilentGeneration(1928-1945)
## Type
picklist
GraduationAchievement
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the person's highest achievement on graduation.
Possible values are:
## •
AssociateDegree
## •
## Certificateor Award
## •
MultipleDegrees
## •
Non-Graduate
## •
## Other
## •
PostgraduateDegree
## •
SecondaryDiploma
## •
UndergraduateDegree
## Type
picklist
GraduationCohort
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The group of graduates the person belongs to based on their graduation date.
Possible values are:
## •
0-5 YearsSinceGraduation
## •
11-20YearsSinceGraduation
## 79
ContactProfileEducation Cloud Standard Objects

DetailsField
## •
21-30YearsSinceGraduation
## •
31-40YearsSinceGraduation
## •
41-50YearsSinceGraduation
## •
50+ YearsSinceGraduation
## •
6-10YearsSinceGraduation
## Type
boolean
HasFerpaParentalDisclosure
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates permission to make FERPA Parental Disclosure (true) or not (false).
The default value is false.
## Type
boolean
HasFerpaThrdPtyDisclosure
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates permission to make FERPA Third-Party Disclosure (true) or not (false).
The default value is false.
## Type
picklist
HighestEducationLevel
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the highest educational qualification of the individual
Possible values are:
## •
## Graduate
## •
HighSchool
## •
## Masters
## •
## Other
## •
PhD
## Type
boolean
IsFirstGenerationStudent
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## 80
ContactProfileEducation Cloud Standard Objects

DetailsField
## Description
Indicates whether the individual is the first generation to enroll in education beyond high
school.
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Location
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The location where the contact currently resides.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## 81
ContactProfileEducation Cloud Standard Objects

DetailsField
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
picklist
MilitaryBranch
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the military branch if the individual has ever enlisted in the military.
Possible values are:
## •
## Air Force
## •
## Army
## •
CoastGuard
## •
MarineCorps
## •
## Navy
## •
## Other
## •
SpaceForce
## Type
picklist
MilitaryService
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the current status of military service.
Possible values are:
## •
ActiveDuty
## •
ActiveReserve
## •
## Fulltime
## •
## Other
## •
## Parttime
## •
## Retired
## •
## Unknown
## •
## Veteran
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## 82
ContactProfileEducation Cloud Standard Objects

DetailsField
## Description
The name for this record.
## Type
reference
PrimaryCitizenshipId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The primary citizenship held by the individual.
This field is a relationship field.
## Relationship Name
PrimaryCitizenship
## Relationship Type
## Lookup
## Refers To
GeoCountry
## Type
picklist
PrimaryCitizenshipType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of primary citizenship held by the individual.
Possible values are:
## •
## Asylum
## •
## National
## •
## Other
## •
## Refugee
## Type
multipicklist
## Race
## Properties
## Create, Filter, Nillable, Update
## Description
Specifies the race of the individual.
Possible values are:
## •
AlaskaNative
## •
AmericanIndian
## •
## Asian
## •
Blackor AfricanAmerican
## 83
ContactProfileEducation Cloud Standard Objects

DetailsField
## •
NativeHawaiianor OtherPacificIslander
## •
## White
## Type
reference
SecondaryCitizenshipId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The secondary citizenship of the individual if they hold dual citizenship.
This field is a relationship field.
## Relationship Name
SecondaryCitizenship
## Relationship Type
## Lookup
## Refers To
GeoCountry
## Type
picklist
SecondaryCitizenshipType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of secondary citizenship held by the individual.
Possible values are:
## •
## Asylum
## •
## National
## •
## Other
## •
## Refugee
## Type
url
## Website
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A website that’s associated with the contact.
CourseCreditTransferAppln
Represents the details of a course credit transfer application. This object is available in API version 65.0 and later.
## 84
CourseCreditTransferApplnEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ApprovedLearningEquivalencyId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The approved Learning Equivalency related to the Course Credit Transfer Application.
This field is a relationship field.
## Relationship Name
ApprovedLearningEquivalency
## Refers To
LearningEquivalency
## Type
reference
ApprovedLearningId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The approved Learning related to the Course Credit Transfer Application.
This field is a relationship field.
## Relationship Name
ApprovedLearning
## Refers To
## Learning
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Case related to the Course Credit Transfer Application.
This field is a relationship field.
## Relationship Name
## Case
## 85
CourseCreditTransferApplnEducation Cloud Standard Objects

DetailsField
## Refers To
## Case
## Type
reference
IndividualApplicationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The application that's associated with this course credit transfer application.
This field is a relationship field.
## Relationship Name
IndividualApplication
## Refers To
IndividualApplication
## Type
boolean
IsForEstimate
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether course credit transfer application is only for estimation (true) or not (false).
The default value is false.
## Type
boolean
IsInProgress
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the external learning that's associated with this course credit transfer
application is in progress (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 86
CourseCreditTransferApplnEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
LearningAcademicSeason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic season of the learning for the Course Credit Transfer Application.
## Type
date
LearningAcademicYear
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic year of the learning for the Course Credit Transfer Application.
## Type
reference
LearningAchievementId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning Achievement related to the Course Credit Transfer Application.
This field is a relationship field.
## Relationship Name
LearningAchievement
## Refers To
LearningAchievement
## Type
double
LearningDuration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The duration of the learning for the Course Credit Transfer Application.
## 87
CourseCreditTransferApplnEducation Cloud Standard Objects

DetailsField
## Type
picklist
LearningDurationUnit
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the duration unit of the learning for the Course Credit Transfer Application.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
date
LearningEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the external learning.
## Type
string
LearningIdentifier
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The identifier of the learning for the Course Credit Transfer Application.
## Type
string
LearningLetterGrade
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The letter grade of the learning for the Course Credit Transfer Application.
## Type
string
LearningName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the learning for the Course Credit Transfer Application.
## 88
CourseCreditTransferApplnEducation Cloud Standard Objects

DetailsField
## Type
double
LearningNumericGrade
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The letter grade of the learning for the Course Credit Transfer Application.
## Type
date
LearningStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the external learning.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Course Credit Transfer Application.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The identifier for the owner of the record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
PriorLearningEvaluationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The prior learning evaluation record that groups all course credit transfer applications for an
institution into one transfer credit estimate.
This field is a relationship field.
## 89
CourseCreditTransferApplnEducation Cloud Standard Objects

DetailsField
## Relationship Name
PriorLearningEvaluation
## Refers To
PriorLearningEvaluation
## Type
string
## Provider
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The provider of the Course Credit Transfer Application.
## Type
reference
RequestedLearningEquivalencyId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The requested Learning Equivalency related to the Course Credit Transfer Application.
This field is a relationship field.
## Relationship Name
RequestedLearningEquivalency
## Refers To
LearningEquivalency
## Type
reference
RequestedLearningId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The requested Learning related to the Course Credit Transfer Application.
This field is a relationship field.
## Relationship Name
RequestedLearning
## Refers To
## Learning
## Type
picklist
ReviewType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## 90
CourseCreditTransferApplnEducation Cloud Standard Objects

DetailsField
## Description
Specifies review type of the Course Credit Transfer Application based on submitted
information.
Possible values are:
## •
NotReviewed
## •
## Official
## •
## Unofficial
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the Course Credit Transfer Application.
Possible values are:
## •
ApplicationDecision
## •
## Approved
## •
## Cancelled
## •
ConditionallyApproved
## •
## Denied
## •
FacultyReview
## •
## In Review
## •
## Processing
## Type
picklist
## Type
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of credit requested for transfer.
Possible values are:
## •
## Education
## •
## Employment
## •
## Examination
## •
## Military
## •
## Other
## 91
CourseCreditTransferApplnEducation Cloud Standard Objects

CourseOfferingParticipant
Represents information about a student's enrollment in a Course Offering. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermEnrollmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Term associated with the Course Offering Participant.
This field is a relationship field.
## Relationship Name
AcademicTermEnrollment
## Relationship Type
## Lookup
## Refers To
AcademicTermEnrollment
## Type
dateTime
AddedToWaitlist
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the course offering participant is added to the waitlist.
## Type
reference
CourseOfferingId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Course Offering associated with the Course Offering Participant.
This field is a relationship field.
## Relationship Name
CourseOffering
## 92
CourseOfferingParticipantEducation Cloud Standard Objects

DetailsField
## Relationship Type
## Lookup
## Refers To
CourseOffering
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the course offering participant.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
DroppedDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the student registered for the course.
This field is available in API version 64.0 and later.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the participant's involvement in the course ended.
## Type
dateTime
EnrollmentOfferDeclined
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the course offering participant declines an enrollment offer.
## Type
dateTime
EnrollmentOfferExpiration
## 93
CourseOfferingParticipantEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the enrollment offer expires.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
boolean
IsRepeatAttempt
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the participant has previously taken the course (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## 94
CourseOfferingParticipantEducation Cloud Standard Objects

DetailsField
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ParticipantAccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account associated with the Course Offering Participant.
This field is a relationship field.
## Relationship Name
ParticipantAccount
## Relationship Type
## Lookup
## Refers To
## Account
## 95
CourseOfferingParticipantEducation Cloud Standard Objects

DetailsField
## Type
picklist
ParticipantAffiliation
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The participant's role in the course.
Possible values are:
## •
## Aide
## •
## Student
## •
## Teacher
## Type
reference
ParticipantContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact record associated with the Course Offering Participant.
This field is a relationship field.
## Relationship Name
ParticipantContact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
picklist
ParticipationStatus
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the participation status of the participant in the course.
Possible values are:
## •
## Audit
## •
## Completed
## •
DeclinedWaitlist
## •
## Dropped
## •
Eligibleto EnrollfromWaitlist
## •
## Enrolled
## •
ExpiredWaitlistEnrollmentOffer
## 96
CourseOfferingParticipantEducation Cloud Standard Objects

DetailsField
## •
## Facilitating
## •
## Failed
## •
## In Cart
## •
## On Hold
## •
RemovedfromWaitlist
## •
TransferCredit
## •
WaitlistEnrollmentOfferin Cart
## •
## Waitlisted
## •
## Withdrew
## Type
dateTime
RegistrationDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the student removed the course from the registration.
This field is available in API version 64.0 and later.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the participant's involvement in the course began.
## Type
textarea
## Summary
## Properties
## Create, Nillable, Update
## Description
The summary associated with the Course Offering Participant.
## Type
int
WaitlistScore
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The weighted value that determines the position of the course offering participant on the
waitlist.
## 97
CourseOfferingParticipantEducation Cloud Standard Objects

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
CourseOfferingParticipantFeed on page 379
Feed tracking is available for the object.
CourseOfferingParticipantHistory on page 385
History is available for tracked fields of the object.
CourseOfferingParticipantShare on page 389
Sharing is available for the object.
CourseOfrPtcpActvtyGrd
https://gus.lightning.force.com/lightning/r/MDS_Entity__c/a7BEE000000QYE92AO/view This object is available in API version 65.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learner account associated with the course offering participant activity grade.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
picklist
ActivityType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of activity, such as an assignment or quiz.
## 98
CourseOfrPtcpActvtyGrdEducation Cloud Standard Objects

DetailsField
Possible values are:
## •
## Assignment
## •
## Attendance
## •
## Exam
## •
GroupProject
## •
## Lab Assignment
## •
## Participation
## •
## Quiz
## Type
textarea
## Comments
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Comments related to the activity grade.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The learner contact associated with the course offering participant activity grade.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
reference
CourseOfferingParticipantId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The course offering participant associated with the course offering participant activity grade.
This field is a relationship field.
## Relationship Name
CourseOfferingParticipant
## Refers To
CourseOfferingParticipant
## 99
CourseOfrPtcpActvtyGrdEducation Cloud Standard Objects

DetailsField
## Type
reference
CourseOfrgRubricCriterionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The course offering rubric criterion associated with the course offering participant activity
grade.
This field is a relationship field.
## Relationship Name
CourseOfrgRubricCriterion
## Refers To
CourseOfrgRubricCriterion
## Type
boolean
IsActivityInProgress
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the activity is in progress (true) or not (false).
The default value is false.
## Type
boolean
IsActivityLate
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the activity is late (true) or not (false).
The default value is false.
## Type
boolean
IsActivityMissing
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the activity is missing (true) or not (false).
The default value is false.
## Type
boolean
IsIncomplete
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## 100
CourseOfrPtcpActvtyGrdEducation Cloud Standard Objects

DetailsField
## Description
Indicates whether the activity is incomplete (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
LetterGrade
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The letter grade the course offering participant achieved for the activity.
## Type
double
MaximumMark
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The maximum score for the activity.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The autonumbered name for the activity.
## 101
CourseOfrPtcpActvtyGrdEducation Cloud Standard Objects

DetailsField
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
int
PercentileRank
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The percentile rank the course offering particpant achieved for the activity.
## Type
double
## Score
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The score the course offering participant achieved for the activity.
## Type
date
ScoreDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date on which the activity was scored.
## Type
picklist
ScoreStatus
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the status of the score for the activity grade, such as submitted, not submitted, or
fully graded.
Possible values are:
## 102
CourseOfrPtcpActvtyGrdEducation Cloud Standard Objects

DetailsField
## •
FullyGraded
## •
## Not Submitted
## •
## Submitted
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
CourseOfrPtcpActvtyGrdHistory on page 385
History is available for tracked fields of the object.
CourseOfrPtcpActvtyGrdOwnerSharingRule on page 387
Sharing rules are available for the object.
CourseOfrPtcpActvtyGrdShare on page 389
Sharing is available for the object.
CourseOfferingPtcpResult
Represents the outcome of a student's participation in a course. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
CourseOfferingParticipantId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Course Offering Participant associated with the Course Offering Participant Result.
This field is a relationship field.
## Relationship Name
CourseOfferingParticipant
## Relationship Type
## Lookup
## 103
CourseOfferingPtcpResultEducation Cloud Standard Objects

DetailsField
## Refers To
CourseOfferingParticipant
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The unit of measurement for completion of the course.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
reference
EvaluatorContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact that assigns the result associated with the Course Offering Participant Result.
This field is a relationship field.
## Relationship Name
EvaluatorContact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## 104
CourseOfferingPtcpResultEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
LetterGrade
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The letter grade awarded to the participant for completing the course.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
Course Offering Participant Result auto-generated name.
## Type
double
NumericGrade
## Properties
## Create, Filter, Nillable, Sort, Update
## 105
CourseOfferingPtcpResultEducation Cloud Standard Objects

DetailsField
## Description
The value that's assigned to a Letter Grade.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
ParticipantResultStatus
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type or status of the participant's result. For example, Pass or Fail.
Possible values are:
## •
Fail—Failed
## •
## Incomplete
## •
Pass—Passed
## •
Withdraw—Withdrew
## Type
double
UnitsEarned
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Units of value awarded for completing the course.
CourseOfrgRubricCriterion
Represents an activity rubric criterion for a course offering. This object is available in API version 65.0 and later.
## 106
CourseOfrgRubricCriterionEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
ActivityType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of activity, such as assignment or quiz.
Possible values are:
## •
## Assignment
## •
## Attendance
## •
## Exam
## •
GroupProject
## •
## Lab Assignment
## •
## Participation
## •
## Quiz
## Type
int
CountedInstances
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of instances of the activity represented by the record that are counted toward
the final grade.
## Type
reference
CourseOfferingId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The course offering associated with the course offering rubric criterion.
This field is a relationship field.
## Relationship Name
CourseOffering
## 107
CourseOfrgRubricCriterionEducation Cloud Standard Objects

DetailsField
## Refers To
CourseOffering
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
A description of the course offering rubric criterion.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
int
MaximumInstances
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The maximum number of times the activity represented by the record can occur within a
term.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the course offering rubric criterion.
## 108
CourseOfrgRubricCriterionEducation Cloud Standard Objects

DetailsField
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
double
## Weight
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The weight of the course offering rubric criterion.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
CourseOfrgRubricCriterionHistory on page 385
History is available for tracked fields of the object.
CourseOfrgRubricCriterionOwnerSharingRule on page 387
Sharing rules are available for the object.
CourseOfrgRubricCriterionShare on page 389
Sharing is available for the object.
CourseOfferingSchedule
Represents information about the schedule defined for a Course Offering. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 109
CourseOfferingScheduleEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
CourseOfferingId
## Properties
## Create, Filter, Group, Sort
## Description
The Course Offering that's associated with the Course Offering Schedule.
This field is a relationship field.
## Relationship Name
CourseOffering
## Relationship Type
## Lookup
## Refers To
CourseOffering
## Type
reference
CourseOfferingScheduleTmplId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Course Offering Schedule Template associated with the Course Offering Schedule. If a
Course Offering Schedule Template is specified, the StartTime, EndTime and Days
from the Course Offering Schedule Template are used.
This field is a relationship field.
## Relationship Name
CourseOfferingScheduleTmpl
## Relationship Type
## Lookup
## Refers To
CourseOfferingScheduleTmpl
## Type
string
## Description
## Properties
## Create, Filter, Group, Sort, Update
## Description
The description of the Course Offering Schedule Template.
## Type
date
EndDate
## 110
CourseOfferingScheduleEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the course offering schedule.
## Type
time
EndTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The time of day when the Course Offering meeting ends.
## Type
boolean
IsFriday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Friday.
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
boolean
IsMonday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Monday.
The default value is false.
## Type
boolean
IsSaturday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## 111
CourseOfferingScheduleEducation Cloud Standard Objects

DetailsField
## Description
Indicates that the Course Offering occurs on Saturday.
The default value is false.
## Type
boolean
IsSunday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Sunday.
The default value is false.
## Type
boolean
IsThursday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Thursday.
The default value is false.
## Type
boolean
IsTuesday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Tuesday.
The default value is false.
## Type
boolean
IsWednesday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Wednesday.
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 112
CourseOfferingScheduleEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LocationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The education facility Location that's associated with the Course Offering Schedule.
This field is a relationship field.
## Relationship Name
## Location
## Relationship Type
## Lookup
## Refers To
## Location
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## 113
CourseOfferingScheduleEducation Cloud Standard Objects

DetailsField
## Type
string
RecurrencePattern
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The RRULE that describes the recurrence pattern for the course offering schedule. Supports
a subset of the RFC 5545 standard for internet calendaring and scheduling. For example, a
recurrence pattern of every day for five days would be
## RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the course offering schedule, which is required when there is a recurrence
pattern.
## Type
time
StartTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The time of day when the Course Offering meeting starts.
## Type
picklist
## Type
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of course offering schedule, such as class, lab, or exam.
CourseOfferingScheduleTmpl
Represents a template that can be used to define a course schedule. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 114
CourseOfferingScheduleTmplEducation Cloud Standard Objects

## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Update
## Description
The description of the Course Offering Schedule Template.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the course offering schedule.
## Type
time
EndTime
## Properties
## Create, Filter, Sort, Update
## Description
The time of day when the Course Offering meeting ends.
## Type
boolean
IsFriday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Friday.
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
boolean
IsMonday
## 115
CourseOfferingScheduleTmplEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Monday.
The default value is false.
## Type
boolean
IsSaturday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Saturday.
The default value is false.
## Type
boolean
IsSunday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Sunday.
The default value is false.
## Type
boolean
IsThursday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Thursday.
The default value is false.
## Type
boolean
IsTuesday
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Tuesday.
The default value is false.
## Type
boolean
IsWednesday
## 116
CourseOfferingScheduleTmplEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that the Course Offering occurs on Wednesday.
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## 117
CourseOfferingScheduleTmplEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
string
RecurrencePattern
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The RRULE that describes the recurrence pattern for the course offering schedule. Supports
a subset of the RFC 5545 standard for internet calendaring and scheduling. For example, a
recurrence pattern of every day for five days would be
## RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the course offering schedule, which is required when there is a recurrence
pattern.
## Type
time
StartTime
## Properties
## Create, Filter, Sort, Update
## Description
The time of day when the Course Offering meeting starts.
## Type
picklist
## Type
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 118
CourseOfferingScheduleTmplEducation Cloud Standard Objects

DetailsField
## Description
The type of course offering schedule, such as class, lab, or exam.
EducationalCharacteristic
Represents a characteristic about a student such as the student's major or student-athlete status. You can use educational characteristics
to filter and search for data and customize the student experience. This object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational characteristic.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the educational characteristic.
## Type
reference
EducCharacteristicTypeId
## Properties
## Create, Filter, Group, Sort, Update
## 119
EducationalCharacteristicEducation Cloud Standard Objects

DetailsField
## Description
The educational characteristic type that's associated with the educational characteristic.
This field is a relationship field.
## Relationship Name
EducCharacteristicType
## Refers To
EducCharacteristicType
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the educational characteristic is active (true) or not (false). An active
educational characteristic can be assigned to a student.
The default value is false.
## Type
boolean
IsVisibleToStudent
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the educational characteristic is searchable in the student portal (true) or
not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## 120
EducationalCharacteristicEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the educational characteristic.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
EducationalCharacteristicChangeEvent on page 378
Change events are available for the object.
EducationalCharacteristicFeed on page 379
Feed tracking is available for the object.
EducationalCharacteristicHistory on page 385
History is available for tracked fields of the object.
EducationalCharacteristicShare on page 389
Sharing is available for the object.
EducCharacteristicAssignment
Represents the assignment of an educational characteristic to a student. Assignments are active for an academic interval such as an
academic year or semester. This object is available in API version 66.0 and later.
## 121
EducCharacteristicAssignmentEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account that's associated with the educational characteristic assignment.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
dateTime
ActiveFrom
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when the educational characteristic assignment becomes active.
## Type
dateTime
ActiveTo
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date when the educational characteristic assignment becomes inactive.
## Type
reference
AppliesToId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic interval that's associated with the educational characteristic assignment.
This field is a polymorphic relationship field.
## 122
EducCharacteristicAssignmentEducation Cloud Standard Objects

DetailsField
## Relationship Name
AppliesTo
## Refers To
AcademicSession, AcademicTerm, AcademicYear
## Type
textarea
## Comments
## Properties
## Create, Nillable, Update
## Description
The comments that are associated with the educational characteristic assignment.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact who is associated with the educational characteristic assignment.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational characteristic assignment.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
reference
EducationalCharacteristicId
## Properties
## Create, Filter, Group, Sort, Update
## 123
EducCharacteristicAssignmentEducation Cloud Standard Objects

DetailsField
## Description
The educational characteristic that's associated with the educational characteristic assignment.
This field is a relationship field.
## Relationship Name
EducationalCharacteristic
## Refers To
EducationalCharacteristic
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the educational characteristic assignment.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## 124
EducCharacteristicAssignmentEducation Cloud Standard Objects

DetailsField
## Refers To
## Group, User
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
EducCharacteristicAssignmentChangeEvent on page 378
Change events are available for the object.
EducCharacteristicAssignmentFeed on page 379
Feed tracking is available for the object.
EducCharacteristicAssignmentHistory on page 385
History is available for tracked fields of the object.
EducCharacteristicAssignmentShare on page 389
Sharing is available for the object.
EducCharacteristicType
Represents a category of educational characteristics such as major or campus. This object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational characteristic type.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## 125
EducCharacteristicTypeEducation Cloud Standard Objects

DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the educational characteristic type.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the educational characteristic type.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## 126
EducCharacteristicTypeEducation Cloud Standard Objects

DetailsField
## Refers To
## Group, User
## Type
reference
ParentEducCharTypeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The parent educational characteristic type that's related to the educational characteristic
type.
This field is a relationship field.
## Relationship Name
ParentEducCharType
## Refers To
EducCharacteristicType
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
EducCharacteristicTypeChangeEvent on page 378
Change events are available for the object.
EducCharacteristicTypeFeed on page 379
Feed tracking is available for the object.
EducCharacteristicTypeHistory on page 385
History is available for tracked fields of the object.
EducCharacteristicTypeShare on page 389
Sharing is available for the object.
EducCharReqAssignment
Represents the assignment of an educational characteristic requirement to a learning or course offering. This object is available in API
version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 127
EducCharReqAssignmentEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
AssignmentRecordId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The learning or course offering that's associated with the educational characteristic
requirement assignment.
This field is a polymorphic relationship field.
## Relationship Name
AssignmentRecord
## Refers To
CourseOffering, Learning
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational characteristic requirement
assignment.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
reference
EducCharRequirementId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The educational characteristic requirement that's associated with the educational characteristic
requirement assignment.
This field is a relationship field.
## Relationship Name
EducCharRequirement
## Refers To
EducCharRequirement
## 128
EducCharReqAssignmentEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the educational characteristic requirement assignment.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
## 129
EducCharReqAssignmentEducation Cloud Standard Objects

EducCharReqAssignmentChangeEvent on page 378
Change events are available for the object.
EducCharReqAssignmentFeed on page 379
Feed tracking is available for the object.
EducCharReqAssignmentHistory on page 385
History is available for tracked fields of the object.
EducCharReqAssignmentShare on page 389
Sharing is available for the object.
EducCharReqRelationship
Represents the logic between multiple educational characteristics that defines an educational characteristic requirement. This object is
available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational characteristic requirement
relationship.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
reference
EducCharRequirementId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The child educational characteristic requirement that's associated with the educational
characteristic requirement relationship.
## 130
EducCharReqRelationshipEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
EducCharRequirement
## Refers To
EducCharRequirement
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the educational characteristic requirement relationship.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## 131
EducCharReqRelationshipEducation Cloud Standard Objects

DetailsField
## Type
reference
ParentEducCharRequirementId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The parent educational characteristic requirement that's associated with the educational
characteristic requirement relationship.
This field is a relationship field.
## Relationship Name
ParentEducCharRequirement
## Refers To
EducCharRequirement
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
EducCharReqRelationshipChangeEvent on page 378
Change events are available for the object.
EducCharReqRelationshipFeed on page 379
Feed tracking is available for the object.
EducCharReqRelationshipHistory on page 385
History is available for tracked fields of the object.
EducCharReqRelationshipShare on page 389
Sharing is available for the object.
EducCharRequirement
Represents a definition of the educational characteristics that are needed to meet an educational requirement. This object is available
in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 132
EducCharRequirementEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
BaseCharacteristicId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The educational characteristic that's associated with the educational characteristic
requirement.
This field is a relationship field.
## Relationship Name
BaseCharacteristic
## Refers To
EducationalCharacteristic
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational characteristic assignment.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
boolean
IsVisible
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the educational characteristic requirement is searchable in the student
portal (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 133
EducCharRequirementEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the educational characteristic requirement.
## Type
picklist
OperationType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The logical operator that's associated with the educational characteristic requirement, for
example, AND.
Possible values are:
## •
And—AND
## •
Or—OR
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## 134
EducCharRequirementEducation Cloud Standard Objects

DetailsField
## Refers To
## Group, User
EducationalInfoRequest
Represents details about a request for information (RFI) raised by prospective students, parents, or counselors. This object is available in
API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicDurationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic term or academic year that's associated with the Educational Information
## Request.
This field is a polymorphic relationship field.
## Relationship Name
AcademicDuration
## Relationship Type
## Lookup
## Refers To
AcademicTerm, AcademicYear
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Sort
## Description
The case that's associated with the request for information.
This field is a relationship field.
## 135
EducationalInfoRequestEducation Cloud Standard Objects

DetailsField
## Relationship Name
## Case
## Relationship Type
## Lookup
## Refers To
## Case
## Type
picklist
## Category
## Properties
Create, Filter, Restricted picklist, Group, Sort, Update
## Description
Specifies the category for which the Request for Information is raised.
Possible values are:
## •
## Academic
## •
## Admission
## •
FinancialAid
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learning that's associated with the request for information.
## 136
EducationalInfoRequestEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Opportunity associated with the Educational Info Request.
## Relationship Name
## Opportunity
## Relationship Type
## Lookup
## Refers To
## Opportunity
## Type
reference
RequesterId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The account of the person associated with the request for information.
This field is a relationship field.
## Relationship Name
## Requester
## Relationship Type
## Lookup
## Refers To
## Account
## 137
EducationalInfoRequestEducation Cloud Standard Objects

DetailsField
## Type
picklist
SubCategory
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the sub-category for which the Request for Information is raised.
Possible values are:
## •
ApplicationProcess
## •
## Housing
## •
ProgramInfo
## •
## Scholarship
## •
TuitionFee
EducInstitutionOffering
Represents a junction between an institution's account and other objects, such as program, learning program, and academic term. This
object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic term related to the institution offering.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Refers To
AcademicTerm
## 138
EducInstitutionOfferingEducation Cloud Standard Objects

DetailsField
## Type
reference
ApplicationTimelineId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The application timeline related to the institution offering.
This field is a relationship field.
## Relationship Name
ApplicationTimeline
## Refers To
ApplicationTimeline
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the educational institution offering.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
reference
EducInstitutionAccountId
## Properties
## Create, Filter, Group, Sort
## Description
The institution's account related to the institution offering.
This field is a relationship field.
## Relationship Name
EducInstitutionAccount
## Relationship Type
## Master-detail
## Refers To
Account (the master object)
## Type
date
EndDate
## 139
EducInstitutionOfferingEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the institution offering.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the institution offering is active (true) or not (false).
The default value is false.
## Type
boolean
IsPubliclySearchable
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the institution offering is publicly searchable (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningProgramId
## 140
EducInstitutionOfferingEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learning program related to the institution offering.
This field is a relationship field.
## Relationship Name
LearningProgram
## Refers To
LearningProgram
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the educational institution offering.
## Type
reference
ProgramId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The program related to the institution offering.
This field is a relationship field.
## Relationship Name
## Program
## Refers To
## Program
## Type
reference
ProgramTermApplnTimelineId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The program term application timeline related to the institution offering.
This field is a relationship field.
## Relationship Name
ProgramTermApplnTimeline
## Refers To
ProgramTermApplnTimeline
## 141
EducInstitutionOfferingEducation Cloud Standard Objects

DetailsField
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the institution offering.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
EducInstitutionOfferingHistory on page 385
History is available for tracked fields of the object.
EducInstSearchableProfile
Represents information about an educational institution aggregated from other objects for Criteria-Based Search and Filter. This object
is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The institution's account related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## 142
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Type
address
## Address
## Properties
## Filter, Nillable
## Description
The address of the educational institution.
## Type
reference
BusinessProfileId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The business profile related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
BusinessProfile
## Refers To
BusinessProfile
## Type
string
## City
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The city where the educational institution is located.
## Type
string
## Country
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The country where the educational institution is located.
## Type
picklist
CountryCode
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The country code of the country where the educational institution is located.
Possible values are:
## •
AD—Andorra
## 143
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
AE—United Arab Emirates
## •
AF—Afghanistan
## •
AG—Antigua and Barbuda
## •
AI—Anguilla
## •
AL—Albania
## •
AM—Armenia
## •
AO—Angola
## •
AQ—Antarctica
## •
AR—Argentina
## •
AT—Austria
## •
AU—Australia
## •
AW—Aruba
## •
AX—Aland Islands
## •
AZ—Azerbaijan
## •
BA—Bosnia and Herzegovina
## •
BB—Barbados
## •
BD—Bangladesh
## •
BE—Belgium
## •
BF—Burkina Faso
## •
BG—Bulgaria
## •
BH—Bahrain
## •
BI—Burundi
## •
BJ—Benin
## •
BL—Saint Barthélemy
## •
BM—Bermuda
## •
BN—Brunei Darussalam
## •
BO—Bolivia, Plurinational State of
## •
BQ—Bonaire, Sint Eustatius and Saba
## •
BR—Brazil
## •
BS—Bahamas
## •
BT—Bhutan
## •
BV—Bouvet Island
## •
BW—Botswana
## •
BY—Belarus
## •
BZ—Belize
## •
CA—Canada
## •
CC—Cocos (Keeling) Islands
## •
CD—Congo, the Democratic Republic of the
## 144
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
CF—Central African Republic
## •
CG—Congo
## •
CH—Switzerland
## •
CI—Cote d'Ivoire
## •
CK—Cook Islands
## •
CL—Chile
## •
CM—Cameroon
## •
CN—China
## •
CO—Colombia
## •
CR—Costa Rica
## •
CV—Cape Verde
## •
CW—Curaçao
## •
CX—Christmas Island
## •
CY—Cyprus
## •
CZ—Czechia
## •
DE—Germany
## •
DJ—Djibouti
## •
DK—Denmark
## •
DM—Dominica
## •
DO—Dominican Republic
## •
DZ—Algeria
## •
EC—Ecuador
## •
EE—Estonia
## •
EG—Egypt
## •
EH—Western Sahara
## •
ER—Eritrea
## •
ES—Spain
## •
ET—Ethiopia
## •
FI—Finland
## •
FJ—Fiji
## •
FK—Falkland Islands (Malvinas)
## •
FO—Faroe Islands
## •
FR—France
## •
GA—Gabon
## •
GB—United Kingdom
## •
GD—Grenada
## •
GE—Georgia
## •
GF—French Guiana
## 145
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
GG—Guernsey
## •
GH—Ghana
## •
GI—Gibraltar
## •
GL—Greenland
## •
GM—Gambia
## •
GN—Guinea
## •
GP—Guadeloupe
## •
GQ—Equatorial Guinea
## •
GR—Greece
## •
GS—South Georgia and the South Sandwich Islands
## •
GT—Guatemala
## •
GW—Guinea-Bissau
## •
GY—Guyana
## •
HM—Heard Island and McDonald Islands
## •
HN—Honduras
## •
HR—Croatia
## •
HT—Haiti
## •
HU—Hungary
## •
ID—Indonesia
## •
IE—Ireland
## •
IL—Israel
## •
IM—Isle of Man
## •
IN—India
## •
IO—British Indian Ocean Territory
## •
IQ—Iraq
## •
IS—Iceland
## •
IT—Italy
## •
JE—Jersey
## •
JM—Jamaica
## •
JO—Jordan
## •
JP—Japan
## •
KE—Kenya
## •
KG—Kyrgyzstan
## •
KH—Cambodia
## •
KI—Kiribati
## •
KM—Comoros
## •
KN—Saint Kitts and Nevis
## •
KR—Korea, Republic of
## 146
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
KW—Kuwait
## •
KY—Cayman Islands
## •
KZ—Kazakhstan
## •
LA—Lao People's Democratic Republic
## •
LB—Lebanon
## •
LC—Saint Lucia
## •
LI—Liechtenstein
## •
LK—Sri Lanka
## •
LR—Liberia
## •
LS—Lesotho
## •
LT—Lithuania
## •
LU—Luxembourg
## •
LV—Latvia
## •
LY—Libya
## •
MA—Morocco
## •
MC—Monaco
## •
MD—Moldova, Republic of
## •
ME—Montenegro
## •
MF—Saint Martin (French part)
## •
MG—Madagascar
## •
MK—North Macedonia
## •
ML—Mali
## •
MM—Myanmar
## •
MN—Mongolia
## •
MO—Macao
## •
MQ—Martinique
## •
MR—Mauritania
## •
MS—Montserrat
## •
MT—Malta
## •
MU—Mauritius
## •
MV—Maldives
## •
MW—Malawi
## •
MX—Mexico
## •
MY—Malaysia
## •
MZ—Mozambique
## •
NA—Namibia
## •
NC—New Caledonia
## •
NE—Niger
## 147
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
NF—Norfolk Island
## •
NG—Nigeria
## •
NI—Nicaragua
## •
NL—Netherlands
## •
NO—Norway
## •
NP—Nepal
## •
NR—Nauru
## •
NU—Niue
## •
NZ—New Zealand
## •
OM—Oman
## •
PA—Panama
## •
PE—Peru
## •
PF—French Polynesia
## •
PG—Papua New Guinea
## •
PH—Philippines
## •
PK—Pakistan
## •
PL—Poland
## •
PM—Saint Pierre and Miquelon
## •
PN—Pitcairn
## •
PS—Palestine
## •
PT—Portugal
## •
PY—Paraguay
## •
QA—Qatar
## •
RE—Reunion
## •
RO—Romania
## •
RS—Serbia
## •
RU—Russian Federation
## •
RW—Rwanda
## •
SA—Saudi Arabia
## •
SB—Solomon Islands
## •
SC—Seychelles
## •
SE—Sweden
## •
SG—Singapore
## •
SH—Saint Helena, Ascension and Tristan da Cunha
## •
SI—Slovenia
## •
SJ—Svalbard and Jan Mayen
## •
SK—Slovakia
## •
SL—Sierra Leone
## 148
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
SM—San Marino
## •
SN—Senegal
## •
SO—Somalia
## •
SR—Suriname
## •
SS—South Sudan
## •
ST—Sao Tome and Principe
## •
SV—El Salvador
## •
SX—Sint Maarten (Dutch part)
## •
SZ—Eswatini
## •
TC—Turks and Caicos Islands
## •
TD—Chad
## •
TF—French Southern Territories
## •
TG—Togo
## •
TH—Thailand
## •
TJ—Tajikistan
## •
TK—Tokelau
## •
TL—Timor-Leste
## •
TM—Turkmenistan
## •
TN—Tunisia
## •
TO—Tonga
## •
TR—Türkiye
## •
TT—Trinidad and Tobago
## •
TV—Tuvalu
## •
TW—Taiwan
## •
TZ—Tanzania, United Republic of
## •
UA—Ukraine
## •
UG—Uganda
## •
US—United States
## •
UY—Uruguay
## •
UZ—Uzbekistan
## •
VA—Holy See (Vatican City State)
## •
VC—Saint Vincent and the Grenadines
## •
VE—Venezuela, Bolivarian Republic of
## •
VG—Virgin Islands, British
## •
VN—Vietnam
## •
VU—Vanuatu
## •
WF—Wallis and Futuna
## •
WS—Samoa
## 149
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
XK—Kosovo
## •
YE—Yemen
## •
YT—Mayotte
## •
ZA—South Africa
## •
ZM—Zambia
## •
ZW—Zimbabwe
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to theeducational institution searchable profile.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
reference
EducInstitutionOfferingId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The institution offering related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
EducInstitutionOffering
## Refers To
EducInstitutionOffering
## Type
textarea
EducationalInstitutionFormat
## Properties
## Create, Nillable, Update
## Description
The education format at the educational institution.
## Type
url
EducationalInstitutionImageUrl
## 150
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The URL of the image for the educational institution.
## Type
string
EducationalInstitutionName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the educational institution.
## Type
picklist
EducationalInstitutionType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the educational institution.
Possible values are:
## •
## Charter
## •
## Private
## •
## Public
## Type
picklist
GeocodeAccuracy
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The accuracy rating for the geocode of the educational institution. The accuracy rating
contains information about the location of a latitude and longitude.
Possible values are:
## •
## Address
## •
## Block
## •
## City
## •
## County
## •
ExtendedZip—Extended Zip
## •
NearAddress—Near Address
## •
## Neighborhood
## •
## State
## •
## Street
## 151
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
## Unknown
## •
## Zip
## Type
textarea
GradesOffered
## Properties
## Create, Nillable, Update
## Description
The grades offered by the educational institution.
## Type
string
GradesOfferedSummary
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The category of grades the educational institution offers.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
double
## Latitude
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The latitude where the educational institution is located.
## 152
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Type
picklist
LearningAcademicLevel
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the academic level offered by the educational institution.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## •
ProfessionalEducation
## •
## Undergraduate
## Type
textarea
LearningCategory
## Properties
## Create, Nillable, Update
## Description
The learning category of the educational institution.
## Type
textarea
LearningFormat
## Properties
## Create, Nillable, Update
## Description
The learning format of the educational institution.
## Type
textarea
LearningGrade
## Properties
## Create, Nillable, Update
## Description
The learning grade of the educational institution.
## 153
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learning record related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
## Learning
## Refers To
## Learning
## Type
url
LearningImageUrl
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The URL of the image for the learning record related to the educational institution.
## Type
reference
LearningProgramId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learning program related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
LearningProgram
## Refers To
LearningProgram
## Type
string
LearningProgramName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the learning program offered by the educational institution.
## Type
double
## Longitude
## 154
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The longitude where the educational institution is located.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The autonumbered name of the educational institution searchable profile.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who is the owner of this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
string
PostalCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The postal code of the educational institution.
## Type
reference
ProviderId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The provider related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
## Provider
## 155
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Refers To
## Account
## Type
string
ProviderName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the provider for the educational institution.
## Type
string
## State
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The state where the educational institution is located.
## Type
picklist
StateCode
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The state code of the state where the educational institution is located.
Possible values are:
## •
01—Hokkaido
## •
02—Akita
## •
03—Iwate
## •
04—Miyagi
## •
05—Aichi
## •
06—Yamagata
## •
07—Fukushima
## •
08—Ibaraki
## •
09—Tochigi
## •
10—Gunma
## •
11—Saitama
## •
12—Tianjin
## •
13—Tokyo
## •
14—Shanxi
## •
15—Niigata
## •
16—Toyama
## 156
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
17—Ishikawa
## •
18—Fukui
## •
19—Yamanashi
## •
20—Nagano
## •
21—Liaoning
## •
22—Shizuoka
## •
23—Heilongjiang
## •
24—Mie
## •
25—Shiga
## •
26—Kyoto
## •
27—Osaka
## •
28—Hyogo
## •
29—Nara
## •
30—Wakayama
## •
31—Tottori
## •
32—Shimane
## •
33—Zhejiang
## •
34—Hiroshima
## •
35—Yamaguchi
## •
36—Tokushima
## •
37—Shandong
## •
38—Ehime
## •
39—Kochi
## •
40—Fukuoka
## •
41—Saga
## •
42—Nagasaki
## •
43—Kumamoto
## •
44—Oita
## •
45—Miyazaki
## •
46—Kagoshima
## •
47—Okinawa
## •
50—Chongqing
## •
51—Sichuan
## •
52—Guizhou
## •
53—Yunnan
## •
54—Xizang
## •
61—Shaanxi
## •
62—Gansu
## 157
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
63—Qinghai
## •
64—Ningxia
## •
65—Xinjiang
## •
71—Taiwan
## •
91—Hong Kong
## •
92—Macao
## •
AB—Alberta
## •
AC—Acre
## •
ACT—Australian Capital Territory
## •
AG—Aguascalientes
## •
AK—Alaska
## •
AL—Alessandria
## •
AM—Amazonas
## •
AN—Andaman and Nicobar Islands
## •
AO—Aosta
## •
AP—Ascoli Piceno
## •
AQ—L'Aquila
## •
AR—Arunachal Pradesh
## •
AS—Assam
## •
AT—Asti
## •
AV—Avellino
## •
AZ—Arizona
## •
BA—Bari
## •
BC—British Columbia
## •
BG—Bergamo
## •
BI—Biella
## •
BL—Belluno
## •
BN—Benevento
## •
BO—Bologna
## •
BR—Brindisi
## •
BS—Brescia
## •
BT—Barletta-Andria-Trani
## •
BZ—Bolzano
## •
CA—California
## •
CB—Campobasso
## •
CE—Clare
## •
CH—Chihuahua
## •
CI—Carbonia-Iglesias
## 158
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
CL—Colima
## •
CM—Campeche
## •
CN—Cuneo
## •
CO—Cork
## •
CR—Cremona
## •
CS—Cosenza
## •
CT—Connecticut
## •
CW—Carlow
## •
CZ—Catanzaro
## •
D—Dublin
## •
DC—District of Columbia
## •
DD—Daman and Diu
## •
DE—Delaware
## •
DF—Federal District
## •
DG—Durango
## •
DL—Donegal
## •
DN—Dadra and Nagar Haveli
## •
EN—Enna
## •
ES—Espírito Santo
## •
FC—Forlì-Cesena
## •
FE—Ferrara
## •
FG—Foggia
## •
FI—Florence
## •
FL—Florida
## •
FM—Fermo
## •
FR—Frosinone
## •
G—Galway
## •
GA—Goa
## •
GE—Genoa
## •
GJ—Gujarat
## •
GO—Gorizia
## •
GR—Guerrero
## •
GT—Guanajuato
## •
HG—Hidalgo
## •
HI—Hawaii
## •
HP—Himachal Pradesh
## •
HR—Haryana
## •
IA—Iowa
## 159
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
ID—Idaho
## •
IL—Illinois
## •
IM—Imperia
## •
IN—Indiana
## •
IS—Isernia
## •
JA—Jalisco
## •
JH—Jharkhand
## •
JK—Jammu and Kashmir
## •
KA—Karnataka
## •
KE—Kildare
## •
KK—Kilkenny
## •
KL—Kerala
## •
KR—Crotone
## •
KS—Kansas
## •
KY—Kerry
## •
LA—Louisiana
## •
LC—Lecco
## •
LD—Longford
## •
LE—Lecce
## •
LH—Louth
## •
LI—Livorno
## •
LK—Limerick
## •
LM—Leitrim
## •
LO—Lodi
## •
LS—Laois
## •
LT—Latina
## •
LU—Lucca
## •
MA—Massachusetts
## •
MB—Monza and Brianza
## •
MC—Macerata
## •
MD—Maryland
## •
ME—Mexico State
## •
MG—Minas Gerais
## •
MH—Meath
## •
MI—Milan
## •
ML—Meghalaya
## •
MN—Monaghan
## •
MO—Morelos
## 160
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
MP—Madhya Pradesh
## •
MS—Mississippi
## •
MT—Montana
## •
MZ—Mizoram
## •
NA—Nayarit
## •
NB—New Brunswick
## •
NC—North Carolina
## •
ND—North Dakota
## •
NE—Nebraska
## •
NH—New Hampshire
## •
NJ—New Jersey
## •
NL—Nuevo León
## •
NM—New Mexico
## •
NO—Novara
## •
NS—Nova Scotia
## •
NSW—New South Wales
## •
NT—Northwest Territories
## •
NU—Nuoro
## •
NV—Nevada
## •
NY—New York
## •
OA—Oaxaca
## •
OG—Ogliastra
## •
OH—Ohio
## •
OK—Oklahoma
## •
ON—Ontario
## •
OR—Oristano
## •
OT—Olbia-Tempio
## •
OY—Offaly
## •
PA—Pennsylvania
## •
PB—Punjab
## •
PC—Piacenza
## •
PD—Padua
## •
PE—Prince Edward Island
## •
PG—Perugia
## •
PI—Pisa
## •
PN—Pordenone
## •
PO—Prato
## •
PR—Parma
## 161
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
PT—Pistoia
## •
PU—Pesaro and Urbino
## •
PV—Pavia
## •
PY—Puducherry
## •
PZ—Potenza
## •
QC—Quebec
## •
QE—Querétaro
## •
QLD—Queensland
## •
QR—Quintana Roo
## •
RA—Ravenna
## •
RC—Reggio Calabria
## •
RE—Reggio Emilia
## •
RG—Ragusa
## •
RI—Rieti
## •
RJ—Rio de Janeiro
## •
RM—Rome
## •
RN—Roscommon
## •
RO—Rovigo
## •
RR—Roraima
## •
RS—Rio Grande do Sul
## •
SA—South Australia
## •
SC—South Carolina
## •
SD—South Dakota
## •
SE—Sergipe
## •
SI—Sinaloa
## •
SK—Sikkim
## •
SL—San Luis Potosí
## •
SO—Sonora
## •
SP—São Paulo
## •
SR—Syracuse
## •
SS—Sassari
## •
SV—Savona
## •
TA—Tipperary
## •
TAS—Tasmania
## •
TB—Tabasco
## •
TE—Teramo
## •
TG—Telangana
## •
TL—Tlaxcala
## 162
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## •
TM—Tamaulipas
## •
TN—Trento
## •
TO—Turin
## •
TP—Trapani
## •
TR—Tripura
## •
TS—Trieste
## •
TV—Treviso
## •
TX—Texas
## •
UD—Udine
## •
UP—Uttar Pradesh
## •
UT—Uttarakhand
## •
VA—Virginia
## •
VB—Verbano-Cusio-Ossola
## •
VC—Vercelli
## •
VE—Veracruz
## •
VI—Vicenza
## •
VIC—Victoria
## •
VR—Verona
## •
VS—Medio Campidano
## •
VT—Viterbo
## •
VV—Vibo Valentia
## •
WA—Western Australia
## •
WB—West Bengal
## •
WD—Waterford
## •
WH—Westmeath
## •
WI—Wisconsin
## •
WV—West Virginia
## •
WW—Wicklow
## •
WX—Wexford
## •
WY—Wyoming
## •
YT—Yukon Territories
## •
YU—Yucatán
## •
ZA—Zacatecas
## Type
textarea
## Street
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 163
EducInstSearchableProfileEducation Cloud Standard Objects

DetailsField
## Description
The street where the educational institution is located.
## Type
textarea
SupportProgramFormat
## Properties
## Create, Nillable, Update
## Description
The format of the support program at the educational institution.
## Type
reference
SupportProgramId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The support program related to the educational institution searchable profile.
This field is a relationship field.
## Relationship Name
SupportProgram
## Refers To
## Program
## Type
url
SupportProgramImageUrl
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The URL of the image for the educational institution's support program.
## Type
string
SupportProgramName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the support program at the educational institution.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
## 164
EducInstSearchableProfileEducation Cloud Standard Objects

EducInstSearchableProfileHistory on page 385
History is available for tracked fields of the object.
EducInstSearchableProfileOwnerSharingRule on page 387
Sharing rules are available for the object.
EducInstSearchableProfileShare on page 389
Sharing is available for the object.
ExternalLearning
Represents information that defines a training that is made available by an external provider as a course, program, or on-site experience,
for a contact. This object is available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the External Learning.
## Type
double
## Duration
## Properties
## Filter, Nillable, Sort
## Description
The duration of the External Learning.
## Type
picklist
DurationUnit
## Properties
Filter, Group, Nillable, Restricted picklist, Sort
## Description
Specifies the duration unit of the External Learning.
Possible values are:
## •
ClockHours
## 165
ExternalLearningEducation Cloud Standard Objects

DetailsField
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
picklist
FieldOfStudy
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the field of study for the External Learning.
Possible values are:
## •
Careerand TechnicalEducation
## •
## Composite
## •
CriticalReading
## •
## English
## •
EnglishLanguageArts
## •
Fineand PerformingArts
## •
ForeignLanguageand Literature
## •
Lifeand PhysicalSciences
## •
## Mathematics
## •
MilitaryScience
## •
## Other
## •
Physical,Health,and SafetyEducation
## •
## Reading
## •
ReligiousEducationand Theology
## •
## Science
## •
SocialSciencesand History
## •
SocialStudies
## •
## Writing
## Type
string
## Identifier
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The identifier of the External Learning.
## 166
ExternalLearningEducation Cloud Standard Objects

DetailsField
## Type
boolean
IsActive
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the External Learning is active (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort
## Description
The parent Learning related to the External Learning.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Master-detail
## Refers To
Learning (the master object)
## Type
string
## Name
## 167
ExternalLearningEducation Cloud Standard Objects

DetailsField
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the External Learning.
## Type
reference
ProviderId
## Properties
## Filter, Group, Nillable, Sort
## Description
The educational institution related to the External Learning.
This field is a relationship field.
## Relationship Name
## Provider
## Refers To
## Account
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the transfer status of the External Learning.
Possible values are:
## •
InReview—In Review
## •
NonTransferable—Non Transferable
## •
## Pending
## •
## Transferable
## Type
picklist
## Type
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the External Learning.
Possible values are:
## •
## Education
## •
## Employment
## •
## Examination
## •
## Military
## 168
ExternalLearningEducation Cloud Standard Objects

DetailsField
## •
## Other
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
ExternalLearningHistory on page 385
History is available for tracked fields of the object.
IndividualApplicationTask
Represents a task related to an application. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ApplicationDecisionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Application Decision associated with the Individual Application Task.
This field is a relationship field.
## Relationship Name
ApplicationDecision
## Refers To
ApplicationDecision
## Type
reference
ApplicationReviewId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Application Review associated with the Individual Application Task.
## 169
IndividualApplicationTaskEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
ApplicationReview
## Refers To
ApplicationReview
## Type
reference
ApplicationStageDefinitionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Application Stage Definition associated with the Application Task.
This field is a relationship field.
## Relationship Name
ApplicationStageDefinition
## Relationship Type
## Lookup
## Refers To
ApplicationStageDefinition
## Type
string
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the Individual Application Task.
## Type
date
DueDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date by which the Individual Application Task must be completed.
## Type
dateTime
EndDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the Individual Application Task ends.
## 170
IndividualApplicationTaskEducation Cloud Standard Objects

DetailsField
## Type
reference
IndividualApplicationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Individual Application associated with the Individual Application Task.
This field is a relationship field.
## Relationship Name
IndividualApplication
## Relationship Type
## Lookup
## Refers To
IndividualApplication
## Type
boolean
IsRequired
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Individual Application Task is required (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Individual Application Task.
## Type
reference
PreliminaryApplicationRefId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Preliminary Application Reference associated with the Individual Application Task.
This field is a relationship field.
## Relationship Name
PreliminaryApplicationRef
## Relationship Type
## Lookup
## 171
IndividualApplicationTaskEducation Cloud Standard Objects

DetailsField
## Refers To
PreliminaryApplicationRef
## Type
url
SavedApplicationUrl
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The URL of a saved application that's associated with the Individual Application Task.
## Type
int
SequenceNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The sequence in which the Individual Application Task must be performed.
## Type
dateTime
StartDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the Individual Application Task starts.
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the Individual Application Task.
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the Individual Application Task.
Possible values are:
## •
## Recruitmentand Admissions
## 172
IndividualApplicationTaskEducation Cloud Standard Objects

IndividualApplicationTaskItem
Represents a junction between an Application Item and an Individual Application Task. This object is available in API version 62.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
ApplicationItem
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Application Item associated with the Individual Application Task Item.
## Type
string
ApplicationItemType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of Application Item associated with the Individual Application Task Item.
## Type
reference
IndividualApplicationTaskId
## Properties
## Create, Filter, Group, Sort
## Description
The Individual Application Task associated with the Individual Application Task Item.
This field is a relationship field.
## Relationship Name
IndividualApplicationTask
## Relationship Type
## Master-detail
## Refers To
IndividualApplicationTask (the master object)
## 173
IndividualApplicationTaskItemEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
## Type
int
SequenceNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The sequence number of the individual application task item.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
IndividualApplicationTaskItemHistory on page 385
History is available for tracked fields of the object.
InvolvementGroup
Represents an involvement group in an institution. This object is available in API version 64.0 and later.
## 174
InvolvementGroupEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
ActivitySeason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the activity season of the involvement group.
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the involvement group.
## Type
reference
CoachId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact related to the coach of the involvement group.
This field is a relationship field.
## Relationship Name
## Coach
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the involvement group.
Possible values are:
## •
GBP—British Pound
## 175
InvolvementGroupEducation Cloud Standard Objects

DetailsField
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the involvement group.
## Type
date
FoundingDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date on which the involvement group was founded.
## Type
boolean
IsSelfEnrollment
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether self enrollment is allowed in the involvement group (true) or not (false).
The default value is false.
## Type
boolean
IsSponsored
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the involvement group is sponsored (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 176
InvolvementGroupEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LeaderId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact related to the leader of the involvement group.
This field is a relationship field.
## Relationship Name
## Leader
## Refers To
## Contact
## Type
picklist
LeaderRole
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the role of the leader in the involvement group.
## Type
reference
LocationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The location related to the involvement group.
This field is a relationship field.
## Relationship Name
## Location
## Refers To
## Location
## 177
InvolvementGroupEducation Cloud Standard Objects

DetailsField
## Type
int
MaximumMemberCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The maximum number of members allowed in the involvement group.
## Type
picklist
## Mode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the mode in which the involvement group operates.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the involvement group.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the current status of involvement group.
## 178
InvolvementGroupEducation Cloud Standard Objects

DetailsField
## Type
reference
SupervisorId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact related to the supervisor of the involvement group.
This field is a relationship field.
## Relationship Name
## Supervisor
## Refers To
## Contact
## Type
picklist
## Type
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the type of the involvement group.
## Type
url
WebsiteUrl
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The website URL of the involvement group.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
InvolvementGroupHistory on page 385
History is available for tracked fields of the object.
InvolvementGroupOwnerSharingRule on page 387
Sharing rules are available for the object.
InvolvementGroupShare on page 389
Sharing is available for the object.
InvolvementGroupMember
Represents a member in an institution's involvement group. This object is available in API version 64.0 and later.
## 179
InvolvementGroupMemberEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact related to the involvement group member.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the involvement group member.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the involvement group member.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 180
InvolvementGroupMemberEducation Cloud Standard Objects

DetailsField
## Description
The date the member left the involvement group.
## Type
reference
InvolvementGroupId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The involvement group related to the involvement group member.
This field is a relationship field.
## Relationship Name
InvolvementGroup
## Refers To
InvolvementGroup
## Type
picklist
InvolvementLevel
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the member's level of involvement in the involvement group.
Possible values are:
## •
## High
## •
## Low
## •
## Middle
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the member is active in the involvement group (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 181
InvolvementGroupMemberEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the involvement group member.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
RelatedToId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The resource related to the involvement group member.
This field is a polymorphic relationship field.
## Relationship Name
RelatedTo
## Refers To
AcademicTerm, AcademicYear
## 182
InvolvementGroupMemberEducation Cloud Standard Objects

DetailsField
## Type
picklist
## Role
## Properties
## Create, Filter, Group, Sort, Update
## Description
The role of the member in the involvement group.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The date the member joined the involvement group.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
InvolvementGroupMemberHistory on page 385
History is available for tracked fields of the object.
InvolvementGroupMemberOwnerSharingRule on page 387
Sharing rules are available for the object.
InvolvementGroupMemberShare on page 389
Sharing is available for the object.
LearnerPathway
Represents the learner's planned path to completion of their enrolled learning programs. This object is available in API version 61.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## 183
LearnerPathwayEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Learner Pathway.
## Type
boolean
IsPrimary
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Learner Pathway is primary (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## 184
LearnerPathwayEducation Cloud Standard Objects

DetailsField
## Type
reference
LearnerContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The learner associated with the Learner Pathway.
This field is a relationship field.
## Relationship Name
LearnerContact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Learner Pathway.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the Learner Pathway.
## 185
LearnerPathwayEducation Cloud Standard Objects

DetailsField
Possible values are:
## •
## Approved
## •
## Draft
## •
PendingApproval
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearnerPathwayHistory on page 385
History is available for tracked fields of the object.
LearnerPathwayOwnerSharingRule on page 387
Sharing rules are available for the object.
LearnerPathwayShare on page 389
Sharing is available for the object.
LearnerPathwayItem
Represents a requirement with completion details in the Learner Pathway. This object is available in API version 61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicSessionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Session in which the Learner Pathway Item is taken.
This field is a relationship field.
## Relationship Name
AcademicSession
## Relationship Type
## Lookup
## 186
LearnerPathwayItemEducation Cloud Standard Objects

DetailsField
## Refers To
AcademicSession
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The allocated length of time for the Learner Pathway Item.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the unit of measurement for the duration.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 187
LearnerPathwayItemEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearnerPathwayId
## Properties
## Create, Filter, Group, Sort
## Description
The Learner Pathway that contains the Learner Pathway Item.
This field is a relationship field.
## Relationship Name
LearnerPathway
## Relationship Type
## Master-detail
## Refers To
LearnerPathway (the master object)
## Type
reference
LearnerProgramRequirementId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learner Program Requirement that the Learner Pathway Item satisfies.
This field is a relationship field.
## Relationship Name
LearnerProgramRequirement
## Relationship Type
## Lookup
## Refers To
LearnerProgramRequirement
## 188
LearnerPathwayItemEducation Cloud Standard Objects

DetailsField
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning associated with the Learner Pathway Item.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
reference
LearningPathwayTemplateItemId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning Pathway Template Item from which the Learner Pathway Item was created.
This field is a relationship field.
## Relationship Name
LearningPathwayTemplateItem
## Relationship Type
## Lookup
## Refers To
LearningPathwayTemplateItem
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Learner Pathway Item.
## Type
picklist
## Season
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the season in which the Learner Pathway Item is taken.
## 189
LearnerPathwayItemEducation Cloud Standard Objects

DetailsField
Possible values are:
## •
## Fall
## •
## Spring
## •
## Summer
## •
## Winter
## Type
int
SequenceNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The display position of the Learner Pathway Item.
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of Learner Pathway Item.
Possible values are:
## •
## Requirement
## •
RequirementPlaceholder—Requirement Placeholder
## •
SeasonPlaceholder—Season Placeholder
## •
YearPlaceholder—Year Placeholder
## Type
picklist
## Year
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the year in which the Learner Pathway Item is taken.
Possible values are:
## •
## Year1
## •
## Year2
## •
## Year3
## •
## Year4
## •
## Year5
## 190
LearnerPathwayItemEducation Cloud Standard Objects

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearnerPathwayItemHistory on page 385
History is available for tracked fields of the object.
LearnerProfile
Represents information about a learner's profile. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
AcademicLevel
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the learner's academic level.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## •
ProfessionalEducation
## •
## Undergraduate
## Type
picklist
AcademicStanding
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## 191
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Description
Specifies the learner's academic standing.
Possible values are:
## •
AcademicDismissal
## •
AcademicProbation
## •
AcademicWarning
## •
GoodStanding
## •
Honors/Dean'sList
## •
ReinstatementStatus
## •
RequiredWithdrawal
## Type
reference
AcademicTermEnrollmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Term Enrollment associated with the Learner Profile.
This field is a relationship field.
## Relationship Name
AcademicTermEnrollment
## Refers To
AcademicTermEnrollment
## Type
string
AdmitTerm
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic term in which the learner was admitted to the education institute.
## Type
string
## College
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the college associated with the Learner Profile.
## Type
string
## Concentration
## 192
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the specialization subject of the learner.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort
## Description
The Contact associated with the Learner Profile.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Master-detail
## Refers To
Contact (the master object)
## Type
reference
ContactProfileId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact Profile associated with the Learner Profile.
This field is a relationship field.
## Relationship Name
ContactProfile
## Refers To
ContactProfile
## Type
double
CumulativeGpa
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The cumulative grade point average of the learner.
## Type
picklist
CurrencyIsoCode
## 193
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Learner Profile.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
email
## Email
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The email address of the learner.
## Type
picklist
EnrollmentReason
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the learner's enrollment reason.
Possible values are:
## •
## Continuing
## •
FirstTime
## •
## Re-admit
## •
## Transferin
## Type
picklist
EnrollmentStatus
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the learner's enrollment status for the academic term.
Possible values are:
## •
## Active
## •
## Dropout
## •
## Expelled
## •
## Graduated
## 194
LearnerProfileEducation Cloud Standard Objects

DetailsField
## •
No show
## •
## Other
## •
## Transferred
## •
## Withdrawn
## Type
date
ExpectedGraduationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learner's expected graduation date.
## Type
picklist
## Gender
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the learner's gender.
## Type
boolean
HasParentalFerpa
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether parental FERPA block is applicable on the learner's records (true) or not
## (false).
The default value is false.
## Type
boolean
HasThirdPartyFerpa
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether third-party FERPA block is applicable on the learner's records (true) or not
## (false).
The default value is false.
## Type
string
InstructionMode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 195
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Description
Specifies the mode of instructions of the learner's classes.
## Type
boolean
IsAthlete
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is an athlete (true) or not (false).
The default value is false.
## Type
boolean
IsCampusResident
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner resides on campus (true) or not (false).
The default value is false.
## Type
boolean
IsDeceased
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is deceased (true) or not (false).
The default value is false.
## Type
boolean
IsEnrolledInCareerServices
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is enrolled in career services at the institute (true) or not (false).
The default value is false.
## Type
boolean
IsEnrolledInDualDegree
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is enrolled in dual degree (true) or not (false).
## 196
LearnerProfileEducation Cloud Standard Objects

DetailsField
The default value is false.
## Type
boolean
IsFirstGenerationStudent
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is a first generation student (true) or not (false).
The default value is false.
## Type
boolean
IsInternationalStudent
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is an international student (true) or not (false).
The default value is false.
## Type
boolean
IsPellGrantEligible
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is eligible for the Pell Grant (true) or not (false).
The default value is false.
## Type
boolean
IsTransferStudent
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the learner is a transfer student (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 197
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Major
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the learner's major.
## Type
string
MajorDeclarationTerm
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic term in which the learner declared their major.
## Type
string
MatriculationTerm
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The academic term in which the learner enrolled at the institute.
## Type
string
## Minor
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the learner's minor.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## 198
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Description
The name of the Learner Profile.
## Type
reference
PrimaryAdvisorId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The User that is the primary advisor associated with the Learner Profile.
This field is a relationship field.
## Relationship Name
PrimaryAdvisor
## Refers To
## User
## Type
string
PrimaryAdvisorName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the learner's primary advisor.
## Type
picklist
## Pronouns
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the learner's preferred gender pronouns.
Possible values are:
## •
He/Him
## •
He/They
## •
## Not Listed
## •
She/Her
## •
She/They
## •
They/Them
## Type
string
SecondConcentration
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 199
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Description
Specifies the second specialization subject of the learner.
## Type
string
SecondMajor
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the learner's second major.
## Type
string
SecondMinor
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the learner's second minor.
## Type
reference
SecondaryAdvisorId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The User that is the secondary advisor associated with the Learner Profile.
This field is a relationship field.
## Relationship Name
SecondaryAdvisor
## Refers To
## User
## Type
string
SecondaryAdvisorName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the learner's secondary advisor.
## Type
string
StudentIdNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 200
LearnerProfileEducation Cloud Standard Objects

DetailsField
## Description
The identifier issued to the learner by the institution.
## Type
picklist
StudyYearClassification
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the learner's study year classification.
Possible values are:
## •
## Freshman
## •
## Junior
## •
## Senior
## •
## Sophomore
## Type
double
TotalUnitsCompleted
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total number of units completed by the learner.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearnerProfileHistory on page 385
History is available for tracked fields of the object.
LearnerProgram
Represents details of a Learning Program Plan that's created for a learner. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 201
LearnerProgramEducation Cloud Standard Objects

## Fields
DetailsField
## Type
picklist
CatalogYear
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learner's catalog year, which is the year they began studying at the institution.
## Type
picklist
ClassCohort
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name for a group of students working through the same program at a similar pace.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
Description of the Learner Program.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date that the learner exited the program.
## Type
date
ExpectedGraduationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The learner's expected graduation date.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## 202
LearnerProgramEducation Cloud Standard Objects

DetailsField
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearnerAccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Account associated with the learner that the Learning Program Plan is assigned to.
This field is a relationship field.
## Relationship Name
LearnerAccount
## Relationship Type
## Lookup
## Refers To
## Account
## Type
reference
LearnerContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact record for the learner that the Learning Program Plan is assigned to.
## 203
LearnerProgramEducation Cloud Standard Objects

DetailsField
This field is a relationship field.
## Relationship Name
LearnerContact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
reference
LearningProgramPlanId
## Properties
## Create, Filter, Group, Sort, Update
## Description
Learning Program Plan that’s associated with the Learner Program.
This field is a relationship field.
## Relationship Name
LearningProgramPlan
## Relationship Type
## Lookup
## Refers To
LearningProgramPlan
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Name of a Learning Program Plan for an individual learner.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 204
LearnerProgramEducation Cloud Standard Objects

DetailsField
## Description
The Opportunity associated with the Learner Program.
## Relationship Name
## Opportunity
## Relationship Type
## Lookup
## Refers To
## Opportunity
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ParentLearnerProgramId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The parent learner program associated with the learner program.
## Relationship Name
ParentLearnerProgram
## Relationship Type
## Lookup
## Refers To
LearnerProgram
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 205
LearnerProgramEducation Cloud Standard Objects

DetailsField
## Description
The date that the learner began the program.
## Type
picklist
## Status
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Status of the learner's participation in the program.
Possible values are:
## •
## Abandoned
## •
## Active
## •
## Completed
## •
## Not Started
## •
## Paused
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearnerProgramHistory on page 385
History is available for tracked fields of the object.
LearnerProgramOwnerSharingRule on page 387
Sharing rules are available for the object.
LearnerProgramShare on page 389
Sharing is available for the object.
LearnerProgramRequirement
Represents details of the requirement that a learner is required to complete in their assigned Learning Program Plan.  This object is
available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 206
LearnerProgramRequirementEducation Cloud Standard Objects

## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
Description of a Learner Program Requirement.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearnerProgramId
## Properties
## Create, Filter, Group, Sort
## Description
Learning Program Plan assigned to a learner.
This field is a relationship field.
## 207
LearnerProgramRequirementEducation Cloud Standard Objects

DetailsField
## Relationship Name
LearnerProgram
## Relationship Type
## Lookup
## Refers To
LearnerProgram
## Type
reference
LearningProgramPlanRqmtId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Learning Program Plan associated with the Learner Program Requirement.
This field is a relationship field.
## Relationship Name
LearningProgramPlanRqmt
## Relationship Type
## Lookup
## Refers To
LearningProgramPlanRqmt
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Name of the Learning Program Requirement that’s assigned to an individual.
## Type
picklist
## Status
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## 208
LearnerProgramRequirementEducation Cloud Standard Objects

DetailsField
## Description
Status of the learner’s progress towards meeting the requirement.
Possible values are:
## •
## Active
## •
## Completed
## •
## Exempt
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearnerProgramRequirementHistory on page 385
History is available for tracked fields of the object.
LearnerProgramRqmtProgress
Represents information about the progress of a requirement that a learner is required to complete as a part of the assigned program
plan. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Learning Program Requirement Progress.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## 209
LearnerProgramRqmtProgressEducation Cloud Standard Objects

DetailsField
## Description
The allocated length of time for completion of the Requirement.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The unit of measurement for length of time for the completion of the Requirement. Example
values include Credit Hour, Contact Hour, Hours, Weeks, Quarters, Semesters, and Years.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## 210
LearnerProgramRqmtProgressEducation Cloud Standard Objects

DetailsField
## Type
reference
LearnerProgramRequirementId
## Properties
## Create, Filter, Group, Sort
## Description
The Learner Program Requirement associated with this Learner Program Requirement
## Progress.
This field is a relationship field.
## Relationship Name
LearnerProgramRequirement
## Relationship Type
## Lookup
## Refers To
LearnerProgramRequirement
## Type
reference
LearningOutcomeItemId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Learning Outcome Item used to fulfill the requirement.
This field is a relationship field.
## Relationship Name
LearningOutcomeItem
## Relationship Type
## Lookup
## Refers To
LearningOutcomeItem
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## 211
LearnerProgramRqmtProgressEducation Cloud Standard Objects

DetailsField
## Description
The name of the Learning Program Requirement Progress that tracks the completion of a
requirement.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearnerProgramRqmtProgressHistory on page 385
History is available for tracked fields of the object.
## Learning
Represents information that defines a training that can be made available as a course, program, or on-site experience, for a contact.  This
object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
AcademicLevel
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The applicable point in the education process.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## 212
LearningEducation Cloud Standard Objects

DetailsField
## •
ProfessionalEducation
## •
## Undergraduate
## Type
date
ActiveFromDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Date the Learning framework became active.
## Type
date
ActiveToDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Date the Learning framework became inactive.
## Type
multipicklist
## Category
## Properties
Create, Filter, Nillable, Restricted picklist, Update
## Description
Specifies the category of the learning.
Possible values are:
## •
## Business
## •
## Education
## •
HealthSciences
## •
LiberalArts
## •
## STEM
## •
SocialScience
## Type
string
CipCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Classification of Instructional Programming code that identifies the program or field of study.
## Type
textarea
## Description
## 213
LearningEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Nillable, Update
## Description
Description of the Learning framework.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The allocated length of time for completion of the Learning.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The unit of measurement for the length of time for completion.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
multipicklist
## Format
## Properties
Create, Filter, Nillable, Restricted picklist, Update
## Description
Specifies the format in which the learning is offered.
Possible values are:
## •
## Hybrid
## •
In person
## •
## Virtual
## Type
multipicklist
## Grade
## Properties
Create, Filter, Nillable, Restricted picklist, Update
## 214
LearningEducation Cloud Standard Objects

DetailsField
## Description
Specifies the grade of the learning.
Possible values are:
## •
## 1
## •
## 10
## •
## 11
## •
## 12
## •
## 2
## •
## 3
## •
## 4
## •
## 5
## •
## 6
## •
## 7
## •
## 8
## •
## 9
## •
## EY
## •
## K
## •
## KS1
## •
## KS2
## •
## KS3
## •
## KS4
## •
## P
## •
## PK3
## •
## PK4
## Type
url
ImageUrl
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The URL to an image for the learning.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Specifies that the Learning framework is active.
The default value is false.
## 215
LearningEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Name of the Learning framework.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ProviderId
## 216
LearningEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Account of the institution that provides the Learning.
This field is a relationship field.
## Relationship Name
## Provider
## Relationship Type
## Lookup
## Refers To
## Account
## Type
picklist
## Type
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of Learning.
Possible values are:
## •
ExternalLearning
## •
LearningCourse
## •
LearningProgram
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningHistory on page 385
History is available for tracked fields of the object.
LearningOwnerSharingRule on page 387
Sharing rules are available for the object.
LearningShare on page 389
Sharing is available for the object.
LearningAchievement
Represents information about the outcome of a learning activity.  This object is available in API version 57.0 and later.
## 217
LearningAchievementEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
## Abbreviation
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Short name for a Learning Achievement.
## Type
picklist
AcademicLevel
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The applicable point in the education process.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## •
ProfessionalEducation
## •
## Undergraduate
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
Description of a Learning Achievement.
## 218
LearningAchievementEducation Cloud Standard Objects

DetailsField
## Type
picklist
FieldOfStudy
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The academic subject related to the course of study.
Possible values are:
## •
Careerand TechnicalEducation
## •
## Composite
## •
CriticalReading
## •
## English
## •
EnglishLanguageArts
## •
Fineand PerformingArts
## •
ForeignLanguageand Literature
## •
Lifeand PhysicalSciences
## •
## Mathematics
## •
MilitaryScience
## •
## Other
## •
Physical,Health,and SafetyEducation
## •
## Reading
## •
ReligiousEducationand Theology
## •
## Science
## •
SocialSciencesand History
## •
SocialStudies
## •
## Writing
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
reference
IssuerId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 219
LearningAchievementEducation Cloud Standard Objects

DetailsField
## Description
The institution that grants the credential.
This field is a relationship field.
## Relationship Name
## Issuer
## Relationship Type
## Lookup
## Refers To
## Account
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## 220
LearningAchievementEducation Cloud Standard Objects

DetailsField
## Description
Name of a Learning Achievement that represents a modeled qualification, achievement, or
other program outcome. Used to provide a meaningful mapping between Learnings and
the result of their successful completion.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
string
## Specialization
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Narrows the category, subject, area of study, discipline, or general branch of knowledge that
the achievement was awarded for.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningAchievementHistory on page 385
History is available for tracked fields of the object.
LearningAchievementOwnerSharingRule on page 387
Sharing rules are available for the object.
LearningAchievementShare on page 389
Sharing is available for the object.
LearningCourse
Represents information about a course that’s required in a learning framework.  This object is available in API version 57.0 and later.
## 221
LearningCourseEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
AcademicLevel
## Properties
Filter, Group, Nillable, Restricted picklist, Sort
## Description
The applicable point in the education process.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## •
ProfessionalEducation
## •
## Undergraduate
## Type
date
ActiveFromDate
## Properties
## Filter, Group, Nillable, Sort
## Description
Date the Learning framework became active.
## Type
date
ActiveToDate
## Properties
## Filter, Group, Nillable, Sort
## Description
Date the Learning framework became inactive.
## 222
LearningCourseEducation Cloud Standard Objects

DetailsField
## Type
string
CipCode
## Properties
## Filter, Group, Nillable, Sort
## Description
Classification of Instructional Programming code that identifies the program or field of study.
## Type
picklist
CourseLevelDescription
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The general type or level of instruction provided throughout the course.
Possible values are:
## •
Acceptedas highschoolequivalent
## •
## Advanced
## •
AdvancedPlacement
## •
## Basic
## •
Careerand TechnicalEducation
## •
## College-level
## •
CoreSubject
## •
DualCredit
## •
EnglishLanguageLearner
## •
## General
## •
## Giftedand Talented
## •
GraduationCredit
## •
## Honors
## •
InternationalBaccalaureate
## •
## Other
## •
## Remedial
## •
## Studentswithdisabilities
## •
## Untracked
## Type
string
CourseNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number that identifies the level of the course and helps organize the course catalog.
## 223
LearningCourseEducation Cloud Standard Objects

DetailsField
## Type
picklist
CourseType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the learning course. For example, Lab, Lecture, Exam, and Practice are
possible course types.
Possible values are:
## •
## Drill
## •
## Exam
## •
## Lab
## •
## Lecture
## •
## Recitation
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Learning Course.
## Type
double
## Duration
## Properties
## Filter, Nillable, Sort
## Description
The allocated length of time for completion of the Learning Course.
## 224
LearningCourseEducation Cloud Standard Objects

DetailsField
## Type
picklist
DurationUnit
## Properties
Filter, Group, Restricted picklist, Nillable, Sort
## Description
The unit of measurement for the length of time for completion.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
picklist
FieldOfStudy
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The academic subject related to the course of study.
Possible values are:
## •
Careerand TechnicalEducation
## •
## Composite
## •
CriticalReading
## •
## English
## •
EnglishLanguageArts
## •
Fineand PerformingArts
## •
ForeignLanguageand Literature
## •
Lifeand PhysicalSciences
## •
## Mathematics
## •
MilitaryScience
## •
## Other
## •
Physical,Health,and SafetyEducation
## •
## Reading
## •
ReligiousEducationand Theology
## •
## Science
## •
SocialSciencesand History
## •
SocialStudies
## •
## Writing
## 225
LearningCourseEducation Cloud Standard Objects

DetailsField
## Type
boolean
IsActive
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the Learning Course is active (true) or not (false).
The default value is false.
## Type
boolean
IsLinkedOnly
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Learning Course is a linked-only course (true) or not (false).
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## 226
LearningCourseEducation Cloud Standard Objects

DetailsField
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort
## Description
Learning (unique parent field) associated with a Learning Course.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Name of a course of study that represents a single unit of teaching that typically lasts one
term.
## Type
reference
ProviderId
## Properties
## Filter, Group, Nillable, Sort
## Description
The Account of the institution that provides the Learning Course.
## Type
string
SubjectAbbreviation
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 227
LearningCourseEducation Cloud Standard Objects

DetailsField
## Description
Abbreviation of the Academic Subject for the course of study. For example, MAT =
## Mathematics.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningCourseHistory on page 385
History is available for tracked fields of the object.
LearningEquivalency
Represents the details of the equivalency between external and internal learnings. This object is available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the Learning Equivalency.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date until which the Learning Equivalency is effective.
## Type
boolean
IsActive
## 228
LearningEquivalencyEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Learning Equivalency is active (true) or not (false).
The default value is false.
## Type
boolean
IsPublished
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Learning Equivalency is published (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Learning Equivalency.
## Type
reference
OwnerId
## 229
LearningEquivalencyEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The identifier for the owner of the record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
date
StartDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The date from which the Learning Equivalency is effective.
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of the Learning Equivalency.
Possible values are:
## •
## Discrete
## •
## General
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningEquivalencyHistory on page 385
History is available for tracked fields of the object.
LearningEquivalencyOwnerSharingRule on page 387
Sharing rules are available for the object.
LearningEquivalencyShare on page 389
Sharing is available for the object.
## 230
LearningEquivalencyEducation Cloud Standard Objects

LearningEquivalencyLearning
Represents a junction between a learning equivalency and a learning. Use this object to filter learning equivalencies by learning. This
object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
reference
LearningEquivalencyId
## Properties
## Create, Filter, Group, Sort
## Description
The learning equivalency associated with the record.
This field is a relationship field.
## Relationship Name
LearningEquivalency
## Relationship Type
## Master-detail
## 231
LearningEquivalencyLearningEducation Cloud Standard Objects

DetailsField
## Refers To
LearningEquivalency (the master object)
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The learning associated with the record.
This field is a relationship field.
## Relationship Name
## Learning
## Refers To
## Learning
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Learning Equivalency Learning.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningEquivalencyLearningHistory on page 385
History is available for tracked fields of the object.
LearningEqvAchvMapping
Represents the mapping between a learning equivalency, internal achievement group, and external achievement group. This object is
available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 232
LearningEqvAchvMappingEducation Cloud Standard Objects

## Fields
DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningEquivalencyId
## Properties
## Create, Filter, Group, Sort
## Description
The parent Learning Equivalency related to the Learning Equivalency Achievement Mapping.
This field is a relationship field.
## Relationship Name
LearningEquivalency
## Relationship Type
## Master-detail
## Refers To
LearningEquivalency (the master object)
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Learning Equivalency Achievement Mapping.
## 233
LearningEqvAchvMappingEducation Cloud Standard Objects

DetailsField
## Type
reference
SourceId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The source Learning Achievement related to the Learning Equivalency Achievement Mapping.
This field is a relationship field.
## Relationship Name
## Source
## Refers To
LearningAchievement
## Type
reference
TargetId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The target Learning Achievement related to the Learning Equivalency Achievement Mapping.
This field is a relationship field.
## Relationship Name
## Target
## Refers To
LearningAchievement
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningEqvAchvMappingHistory on page 385
History is available for tracked fields of the object.
LearningFoundationItem
Represents information about the prerequisite, co-requisite, or the recommended learning that’s required for a learning outcome.  This
object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 234
LearningFoundationItemEducation Cloud Standard Objects

## Fields
DetailsField
## Type
string
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The category associated with the Learning Foundation Item.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The allocated length of time for completion of the Learning.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The unit of measurement for length of time for completion of the Learning.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## 235
LearningFoundationItemEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningAchievementId
## Properties
## Create, Filter, Group, Sort, Update
## Description
A modeled qualification, achievement, or other program outcome used for the Learning
## Foundation.
This field is a relationship field.
## Relationship Name
LearningAchievement
## Relationship Type
## Lookup
## Refers To
LearningAchievement
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort, Update
## Description
Prerequisite, co-requisite or recommended Learning to attain a Learning Achievement.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Lookup
## 236
LearningFoundationItemEducation Cloud Standard Objects

DetailsField
## Refers To
## Learning
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
double
MinimumNumericGrade
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The minimum numeric grade that is required to meet the learning foundation requirement.
This is applicable to Learner Program and Course Offering Participant Result.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
Name of the mapping between the Learning and the Learning Achievement requirements.
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Type of Learning Foundation Item.
Possible values are:
## •
## Co-requisite
## •
## Prerequisite
## •
## Recommended
## 237
LearningFoundationItemEducation Cloud Standard Objects

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningFoundationItemHistory on page 385
History is available for tracked fields of the object.
LearningOutcomeItem
Represents information about the mapping between the learnings and the related outcome.  This object is available in API version 57.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The category associated with the Learning Outcome Item.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The allocated length of time for completion of the Learning.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The unit of measurement for length of time for the completion of the Learning.
Possible values are:
## •
ClockHours
## 238
LearningOutcomeItemEducation Cloud Standard Objects

DetailsField
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
boolean
IsPrimary
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Learning Outcome Item is primary (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningAchievementId
## 239
LearningOutcomeItemEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Learning Achievement that’s granted upon the completion of the Learning.
This field is a relationship field.
## Relationship Name
LearningAchievement
## Relationship Type
## Lookup
## Refers To
LearningAchievement
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort
## Description
The Learning framework that's related to the Learning Outcome Item.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
double
MinimumNumericGrade
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The minimum numeric grade that is required to meet the learning foundation requirement.
This is applicable to Learner Program and Course Offering Participant Result.
## 240
LearningOutcomeItemEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
Name of the mapping between the Learning and the Learning Achievements that it provides.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningOutcomeItemHistory on page 385
History is available for tracked fields of the object.
LearningPathwayTemplate
Represents a template that a learner can apply to create a planned learning path. This object is available in API version 61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## 241
LearningPathwayTemplateEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Nillable, Update
## Description
The description of the Learning Pathway Template.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Learning Pathway Template.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## 242
LearningPathwayTemplateEducation Cloud Standard Objects

DetailsField
## Refers To
## Group, User
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The status of the Learning Pathway Template.
Possible values are:
## •
## Active
## •
## Archived
## •
## Draft
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningPathwayTemplateHistory on page 385
History is available for tracked fields of the object.
LearningPathwayTemplateOwnerSharingRule on page 387
Sharing rules are available for the object.
LearningPathwayTemplateShare on page 389
Sharing is available for the object.
LearningPathwayTemplateItem
Represents a requirement with completion details in the Learning Pathway Template. This object is available in API version 61.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 243
LearningPathwayTemplateItemEducation Cloud Standard Objects

## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The allocated length of time for the Learning Pathway Template Item.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the unit of measurement for the duration.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 244
LearningPathwayTemplateItemEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning associated with the Learning Pathway Template Item.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
reference
LearningPathwayTemplateId
## Properties
## Create, Filter, Group, Sort
## Description
The Learning Pathway Template that contains the Learning Pathway Template Item.
This field is a relationship field.
## Relationship Name
LearningPathwayTemplate
## Relationship Type
## Master-detail
## Refers To
LearningPathwayTemplate (the master object)
## Type
reference
LearningProgramPlanRequirementId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 245
LearningPathwayTemplateItemEducation Cloud Standard Objects

DetailsField
## Description
The Learning Program Plan Requirement that's fulfilled by the the Learning Pathway Template
## Item.
This field is a relationship field.
## Relationship Name
LearningProgramPlanRequirement
## Relationship Type
## Lookup
## Refers To
LearningProgramPlanRqmt
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Learning Pathway Template Item.
## Type
picklist
## Season
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the season in which the Learning Pathway Template Item is taken.
Possible values are:
## •
## Fall
## •
## Spring
## •
## Summer
## •
## Winter
## Type
int
SequenceNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The display position of the Learning Pathway Template Item.
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## 246
LearningPathwayTemplateItemEducation Cloud Standard Objects

DetailsField
## Description
Specifies the type of Learning Pathway Template Item.
Possible values are:
## •
## Requirement
## •
RequirementPlaceholder—Requirement Placeholder
## •
SeasonPlaceholder—Season Placeholder
## •
YearPlaceholder—Year Placeholder
## Type
picklist
## Year
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the year in which the Learning Pathway Template Item is taken.
Possible values are:
## •
## Year1
## •
## Year2
## •
## Year3
## •
## Year4
## •
## Year5
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningPathwayTemplateItemHistory on page 385
History is available for tracked fields of the object.
LearningPathwayTmplPgmPlan
Represents a junction between Learning Program Plan and Learning Pathway Template objects. This object is available in API version
61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 247
LearningPathwayTmplPgmPlanEducation Cloud Standard Objects

## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningPathwayTemplateId
## Properties
## Create, Filter, Group, Sort
## Description
The Learning Pathway Template associated with the Learning Program Plan.
This field is a relationship field.
## Relationship Name
LearningPathwayTemplate
## Relationship Type
## Master-detail
## 248
LearningPathwayTmplPgmPlanEducation Cloud Standard Objects

DetailsField
## Refers To
LearningPathwayTemplate (the master object)
## Type
reference
LearningProgramPlanId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Learning Program Plan associated with the Learning Pathway Template.
This field is a relationship field.
## Relationship Name
LearningProgramPlan
## Relationship Type
## Lookup
## Refers To
LearningProgramPlan
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Learning Pathway Template Program Plan.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningPathwayTmplPgmPlanHistory on page 385
History is available for tracked fields of the object.
LearningProgram
Represents information about one or more trainings in a program that’s required to obtain a credential.  This object is available in API
version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 249
LearningProgramEducation Cloud Standard Objects

## Fields
DetailsField
## Type
picklist
AcademicLevel
## Properties
Filter, Group, Restricted picklist, Nillable, Sort
## Description
The applicable point in the education process.
Possible values are:
## •
AdultEducation
## •
## Doctoral
## •
## Elementary
## •
## Graduate
## •
HighSchool
## •
MiddleSchool
## •
Post-BaccalaureateCertificate
## •
Pre-K/Preschool
## •
ProfessionalEducation
## •
## Undergraduate
## Type
date
ActiveFromDate
## Properties
## Filter, Group, Nillable, Sort
## Description
Date the Learning Program became active.
## Type
date
ActiveToDate
## Properties
## Filter, Group, Nillable, Sort
## Description
Date the Learning Program became inactive.
## Type
string
## Category
## Properties
## Filter, Nillable, Sort
## Description
Specifies the category of the learning program.
## 250
LearningProgramEducation Cloud Standard Objects

DetailsField
## Type
string
CipCode
## Properties
## Filter, Group, Nillable, Sort
## Description
Classification of Instructional Programming code that identifies the program or field of study.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Learning Program.
## Type
boolean
DoesCreateOpportunityRecord
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether an Opportunity record is created (true) or not (false) for expressions of
interest in the Learning Program. The default value is false.
## Type
boolean
DoesGroupOpportunities
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether an applicant’s academic interests are linked to a single opportunity (true)
or not (false). This field is available in API version 62.0 and later.
The default value is false.
## 251
LearningProgramEducation Cloud Standard Objects

DetailsField
## Type
double
## Duration
## Properties
## Filter, Nillable, Sort
## Description
The allocated length of time for completion of the Learning Program.
## Type
picklist
DurationUnit
## Properties
Filter, Group, Restricted picklist, Nillable, Sort
## Description
The unit of measurement for the length of time for completion.
Possible values are:
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
string
## Format
## Properties
## Filter, Nillable, Sort
## Description
Specifies the format in which the learning program is offered.
## Type
string
## Grade
## Properties
## Filter, Nillable, Sort
## Description
Specifies the grade of the learning program.
## Type
url
ImageUrl
## Properties
## Filter, Group, Nillable, Sort
## Description
The URL to an image for the learning program.
## 252
LearningProgramEducation Cloud Standard Objects

DetailsField
## Type
boolean
IsActive
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Specifies that the Learning Program is active.
The default value is false.
## Type
boolean
IsTopLevelProgram
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Identifies whether the learning program is a top-level program (true) or not (false). The
default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
it’s possible the user accessed this record or list view (LastReferencedDate) but didn’t
view it.
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort
## Description
Learning (unique parent field) associated with a Learning Program.
This field is a relationship field.
## 253
LearningProgramEducation Cloud Standard Objects

DetailsField
## Relationship Name
## Learning
## Relationship Type
## Lookup
## Refers To
## Learning
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Name of the Learning Program that leads to a Learning Achievement.
## Type
reference
Product2Id
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The product associated with the learning program.
This field is a relationship field. It’s available in API version 62.0 and later.
## Relationship Name
## Product2
## Refers To
## Product2
## Type
reference
ProviderId
## Properties
## Filter, Group, Nillable, Sort
## Description
Account of the institution that provides the Learning Program.
This field is a relationship field.
## 254
LearningProgramEducation Cloud Standard Objects

DetailsField
## Relationship Name
## Provider
## Relationship Type
## Lookup
## Refers To
## Account
## Type
string
ShortDescription
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The short description of the learning program.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningProgramHistory on page 385
History is available for tracked fields of the object.
LearningProgramPlan
Represents details of a plan that’s created to execute a Learning Program.  This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
date
ActiveFromDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date the Learning Program Plan became active.
## 255
LearningProgramPlanEducation Cloud Standard Objects

DetailsField
## Type
date
ActiveToDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date after which the Learning Program Plan is inactive.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
Description of the Learning Program Plan.
## Type
textarea
DraftPlanContent
## Properties
## Create, Nillable, Update
## Description
The draft content related to the Learning Program Plan saved by the user in the Program
Plan Builder. For example, a draft about Learning Program Plan Requirements, Learning
Achievements, and so on.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Specifies whether the Learning Program Plan is active or not.
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## 256
LearningProgramPlanEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningProgramId
## Properties
## Create, Filter, Group, Sort
## Description
The Learning Program associated with the Learning Program Plan.
This field is a relationship field.
## Relationship Name
LearningProgram
## Relationship Type
## Lookup
## Refers To
LearningProgram
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
double
MinimumProgramGradePointAvg
## Properties
## Create, Filter, Nillable, Sort, Update
## 257
LearningProgramPlanEducation Cloud Standard Objects

DetailsField
## Description
The minimum cumulative GPA that's required to complete the program.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Learning Program Plan.
## Type
reference
ProviderId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account of the institution that provides the Learning Program Plan.
This field is a relationship field.
## Relationship Name
## Provider
## Relationship Type
## Lookup
## Refers To
## Account
## Type
double
VersionNumber
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Specifies the version of the Learning Program Plan.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningProgramPlanHistory on page 385
History is available for tracked fields of the object.
## 258
LearningProgramPlanEducation Cloud Standard Objects

LearningProgramPlanRqmt
Represents information about the requirements of a learning outcome that’s included in the learning program plan.  This object is
available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The category associated with the Learning Outcome Item.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Learning Program Plan Requirement.
## Type
double
## Duration
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The allocated length of time for completion of the requirement.
## Type
picklist
DurationUnit
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
The unit of measurement for length of time for completion of the requirement. Example
values include Credit Hours, Clock Hours, No Credit, Continuing Education Units, Other.
Possible values are:
## 259
LearningProgramPlanRqmtEducation Cloud Standard Objects

DetailsField
## •
ClockHours
## •
ContinuingEducationUnits
## •
CreditHours
## •
## No Credit
## •
## Other
## Type
string
GroupName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of a group of courses.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningAchievementId
## 260
LearningProgramPlanRqmtEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Learning Achievement associated with the Learning Program Plan Requirement.
This field is a relationship field.
## Relationship Name
LearningAchievement
## Relationship Type
## Lookup
## Refers To
LearningAchievement
## Type
reference
LearningProgramPlanId
## Properties
## Create, Filter, Group, Sort
## Description
The Learning Program Plan associated with the Learning Program Plan Requirement.
This field is a relationship field.
## Relationship Name
LearningProgramPlan
## Relationship Type
## Lookup
## Refers To
LearningProgramPlan
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
double
MinimumNumericGrade
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The minimum numeric grade that is required to meet the learning foundation requirement.
This is applicable to Learner Program and Course Offering Participant Result.
## 261
LearningProgramPlanRqmtEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the requirement for a Learning Program Plan.
## Type
reference
ReusableLearningProgramPlanId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reusable Learning Program Plan that is associated with the Learning Program Plan
## Requirement.
This field is a relationship field.
## Relationship Name
ReusableLearningProgramPlan
## Relationship Type
## Lookup
## Refers To
LearningProgramPlan
## Type
int
SequenceNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The order that the course or other requirement should be taken within a Learning Program
## Plan.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningProgramPlanRqmtHistory on page 385
History is available for tracked fields of the object.
LearningRule
Represents a junction between the Learning and Rule (Expression Set) objects for an extensible rule on a learning. This object is available
in API version 65.0 and later.
## 262
LearningRuleEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
string
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the Learning Rule.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## 263
LearningRuleEducation Cloud Standard Objects

DetailsField
## Type
reference
LearningId
## Properties
## Create, Filter, Group, Sort
## Description
The parent Learning related to the Learning Rule.
This field is a relationship field.
## Relationship Name
## Learning
## Relationship Type
## Master-detail
## Refers To
Learning (the master object)
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Learning Rule.
## Type
reference
RuleId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Rule (expression set) related to the Learning Rule.
This field is a relationship field.
## Relationship Name
## Rule
## Refers To
ExpressionSet
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of the Learning Rule.
Possible values are:
## 264
LearningRuleEducation Cloud Standard Objects

DetailsField
## •
## Co-requisite
## •
LinkedCourse
## •
## Prerequisite
## •
## Prerequisiteor Co-requisite
## •
## Recommended
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
LearningRuleHistory on page 385
History is available for tracked fields of the object.
MentoringProfile
Represents information for a participant in a mentoring program. This object is available in API version 61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact associated with the Mentoring Profile.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## 265
MentoringProfileEducation Cloud Standard Objects

DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
boolean
IsMentee
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the contact is a mentee (true) or not (false).
The default value is false.
This field is a calculated field.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Contact associated with the Mentoring Profile.
## Type
reference
OwnerId
## 266
MentoringProfileEducation Cloud Standard Objects

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
RelatedRecordId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Program Enrollment or Provider Offering associated with the Mentoring Profile.
This field is a polymorphic relationship field.
## Relationship Name
RelatedRecord
## Relationship Type
## Lookup
## Refers To
ProgramEnrollment, ProviderOffering
## Type
string
## Summary
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A summary of information associated with the contact.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
MentoringProfileHistory on page 385
History is available for tracked fields of the object.
MentoringProfileOwnerSharingRule on page 387
Sharing rules are available for the object.
## 267
MentoringProfileEducation Cloud Standard Objects

MentoringProfileShare on page 389
Sharing is available for the object.
PersonAcademicCredential
Represents an Academic Credential that a person has earned. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicCredentialId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Credential that's associated with the Person Academic Credential.
This field is a relationship field.
## Relationship Name
AcademicCredential
## Relationship Type
## Lookup
## Refers To
AcademicCredential
## Type
date
AchievedDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The date that the Contact achieved the Academic Credential.
## Type
string
CredentialName
## Properties
## Create, Filter, Group, Sort, Update
## Description
The name of the Academic Credential.
## 268
PersonAcademicCredentialEducation Cloud Standard Objects

DetailsField
## Type
picklist
CredentialType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of Academic Credential.
Possible values are:
## •
AssociateDegree. Available in API version 62.0 and later.
## •
Bachelor’sDegree
## •
## Badge
## •
## Certificate
## •
DoctoralDegree. Available in API version 62.0 and later.
## •
Master’sDegree. Available in API version 62.0 and later.
## •
SecondaryDiploma. Available in API version 62.0 and later.
## Type
string
IssuerName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The institution that grants the Academic Credential.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view indirectly.
## Type
reference
LearnerContactId
## 269
PersonAcademicCredentialEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact person associated with the Person Academic Credential.
This field is a relationship field.
## Relationship Name
LearnerContact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Person Academic Credential.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PersonAcademicCredentialFeed on page 379
Feed tracking is available for the object.
PersonAcademicCredentialHistory on page 385
History is available for tracked fields of the object.
## 270
PersonAcademicCredentialEducation Cloud Standard Objects

PersonAcademicCredentialShare on page 389
Sharing is available for the object.
PersonAffinity
Represents the affinity of a person. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
AffinityType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of the person affinity.
Possible values are:
## •
## Dislike
## •
## Interest
## •
## Like
## Type
date
ArchivedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date on which the person affinity was archived.
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the person affinity.
## Type
reference
ContactId
## 271
PersonAffinityEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact associated with the person affinity.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency related to the person affinity.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the person affinity.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person affinity is active (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 272
PersonAffinityEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the person affinity.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
picklist
## Source
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the information source of the person affinity.
## Type
date
StartDate
## 273
PersonAffinityEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the start date of the person affinity.
## Type
picklist
SubCategory
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the sub category of the person affinity.
## Type
picklist
UsageType
## Properties
Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort
## Description
Specifies the usage type for the person affinity.
Possible values are:
## •
EducationCloud—Education Cloud
The default value is EducationCloud.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PersonAffinityHistory on page 385
History is available for tracked fields of the object.
PersonAffinityOwnerSharingRule on page 387
Sharing rules are available for the object.
PersonAffinityShare on page 389
Sharing is available for the object.
PersonDisability
Represents information about a person's disability. This object is available in API version 57.0 and later.
## 274
PersonDisabilityEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
IndividualId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The individual associated with the disability.
This field is a polymorphic relationship field.
## Relationship Name
## Individual
## Relationship Type
## Lookup
## Refers To
## Account, Contact, Individual
## Type
boolean
IsAccommodationRequired
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the individual requires accommodation.
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 275
PersonDisabilityEducation Cloud Standard Objects

DetailsField
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## 276
PersonDisabilityEducation Cloud Standard Objects

DetailsField
## Type
int
## Rank
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the level of disability.
## Type
picklist
## Status
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the disability.
Possible values are:
## •
## Permanent
## •
## Temporary
The default value is Temporary.
## Type
picklist
## Type
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of disability.
Possible values are:
## •
## Blindness
## •
## Cognitive
## •
## Hearingimpairment
## Type
date
VerificationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the disability was verified.
## Type
picklist
VerifiedBy
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## 277
PersonDisabilityEducation Cloud Standard Objects

DetailsField
## Description
Specifies the verifier of the disability in the individual.
Possible values are:
## •
HealthcareProvider
## •
## Other
## •
## Physician
## •
## Psychologist
## •
SelfReported
## •
SocialWorker
## •
## Teacher
## •
## Therapist
The default value is Physician.
## Type
string
VerifiedByOther
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the verifier of the disability if its other than what is listed in VerifiedBy.
PersonPublicProfile
Represents information about a user that’s shown on their public profile. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
textarea
AboutMe
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The description provided by the user for their public profile.
## 278
PersonPublicProfileEducation Cloud Standard Objects

DetailsField
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact associated with the Person Public Profile
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
email
## Email
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person's email address.
## Type
dateTime
FirstPublished
## Properties
## Create, Filter, Sort, Update
## Description
When this profile was first published.
## Type
string
## Location
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person's display location.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the user.
## 279
PersonPublicProfileEducation Cloud Standard Objects

DetailsField
## Type
reference
PersonPublicProfilePrefSetId
## Properties
## Create, Filter, Group, Sort
## Description
The preferences set by the user, which determine what information to show on their public
profile.
This field is a relationship field.
## Relationship Name
PersonPublicProfilePrefSet
## Relationship Type
## Lookup
## Refers To
PersonPublicProfilePrefSet
## Type
phone
## Phone
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person's phone number.
## Type
string
PrimaryCredentialName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the most recent credential.
## Type
picklist
PrimaryCredentialType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of primary credential, such as the type of associated academic credential.
Possible values are:
## •
AssociateDegree
## •
Bachelor'sDegree
## •
## Badge
## •
## Certificate
## 280
PersonPublicProfileEducation Cloud Standard Objects

DetailsField
## •
DoctoralDegree
## •
Master'sDegree
## •
SecondaryDiploma
## Type
string
PrimaryCredentialYear
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The year of the most recent credential based on the created date.
## Type
picklist
## Pronouns
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the preferred gender pronoun for the user.
Possible values are:
## •
He/Him
## •
He/They
## •
## Not Listed
## •
She/Her
## •
She/They
## •
They/Them
## Type
picklist
UsageType
## Properties
Filter, Group, Nillable, Restricted picklist, Sort
## Description
Specifies the type of site that the sharing settings are applied to. Possible values include
Alumni and Student.
Possible values are:
## •
## Alumni
## •
## Student
## Type
url
## Website
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 281
PersonPublicProfileEducation Cloud Standard Objects

DetailsField
## Description
A website that's associated with the person.
PersonPublicProfilePrefSet
Represents the user’s preferences for which data is included in their directory entry, as well as if they show up at all. This object is available
in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
boolean
CanShareEmail
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person's email address is shared (true) or not (false).
The default value is false.
## Type
boolean
CanShareLocation
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person's location is shared (true) or not (false).
The default value is false.
## Type
boolean
CanSharePersonEducation
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that person education should be shared (true) or not (false).
The default value is false.
## 282
PersonPublicProfilePrefSetEducation Cloud Standard Objects

DetailsField
## Type
boolean
CanSharePersonEmployment
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that person employment information should be shared (true) or not (false).
The default value is false.
## Type
boolean
CanSharePhone
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person's phone numbers are shared (true) or not (false).
The default value is false.
## Type
boolean
CanSharePronouns
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person's preferred pronouns are shared (true) or not (false).
The default value is false.
## Type
boolean
CanShareWebsite
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates that website should be shared (true) or not (false).
The default value is false.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Contact associated with the Person Public Profile Preference Set.
This field is a relationship field.
## 283
PersonPublicProfilePrefSetEducation Cloud Standard Objects

DetailsField
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
boolean
IsProfilePublic
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the profile is public (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string/number assigned to the Person Public Profile Preference Set.
## Type
dateTime
ProfileVisibleDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the profile was made public.
## Type
picklist
UsageType
## Properties
Create, Filter, Group, Restricted picklist, Sort
## Description
Specifies the usage type of the sharing settings, such as Alumni or Student.
Possible values are:
## •
## Alumni
## •
## Student
## 284
PersonPublicProfilePrefSetEducation Cloud Standard Objects

PersonTrait
Represents the traits of a person. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
date
ArchivedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date on which the person trait was archived.
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the person trait.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact associated with the person trait.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## 285
PersonTraitEducation Cloud Standard Objects

DetailsField
## Description
The ISO code for the currency related to the person trait.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the person trait.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person trait is active (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the person trait.
## 286
PersonTraitEducation Cloud Standard Objects

DetailsField
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
picklist
## Source
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the information source of the person trait.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the start date of the person trait.
## Type
picklist
## Type
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the type of the person trait.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PersonTraitHistory on page 385
History is available for tracked fields of the object.
PersonTraitOwnerSharingRule on page 387
Sharing rules are available for the object.
## 287
PersonTraitEducation Cloud Standard Objects

PersonTraitShare on page 389
Sharing is available for the object.
PriceBookAcademicInterval
Represents a junction between a price book and an academic interval such as an academic term. This object is available in API version
66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicIntervalId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The academic interval that's associated with the academic order.
## Relationship Name
AcademicInterval
## Refers To
AcademicSession, AcademicTerm, AcademicYear
## Type
string
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the academic price book.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 288
PriceBookAcademicIntervalEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the academic price book.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
PricebookId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The price book that's associated with the academic price book.
This field is a relationship field.
## Relationship Name
## Pricebook
## Refers To
## Pricebook2
## 289
PriceBookAcademicIntervalEducation Cloud Standard Objects

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PriceBookAcademicIntervalFeed on page 379
Feed tracking is available for the object.
PriceBookAcademicIntervalHistory on page 385
History is available for tracked fields of the object.
PriceBookAcademicIntervalShare on page 389
Sharing is available for the object.
PriorLearningEvaluation
Represents the evaluation of a learner's prior learning that can be used for a transfer. This object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The account that's associated with the prior learning evaluation.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The contact who's associated with the prior learning evaluation.
This field is a relationship field.
## 290
PriorLearningEvaluationEducation Cloud Standard Objects

DetailsField
## Relationship Name
## Contact
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the prior learning evaluation.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but not
viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the prior learning evaluation.
## 291
PriorLearningEvaluationEducation Cloud Standard Objects

DetailsField
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
ParentPriorLearningEvalId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The prior learning evaluation record that's associated with all the prior learning evaluations
generated in the same agent session.
This field is a relationship field.
## Relationship Name
ParentPriorLearningEval
## Refers To
PriorLearningEvaluation
## Type
textarea
## Request
## Properties
## Create, Nillable, Update
## Description
The JSON request that generated the prior learning evaluation.
## Type
textarea
## Result
## Properties
## Create, Nillable, Update
## Description
The JSON response containing the details of the prior learning evaluation.
## 292
PriorLearningEvaluationEducation Cloud Standard Objects

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PriorLearningEvaluationChangeEvent on page 378
Change events are available for the object.
PriorLearningEvaluationFeed on page 379
Feed tracking is available for the object.
PriorLearningEvaluationHistory on page 385
History is available for tracked fields of the object.
PriorLearningEvaluationShare on page 389
Sharing is available for the object.
ProgramTermApplnTimeline
Represents a junction between Academic Term, Application Timeline, and Learning Program objects. This object is available in API
version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AcademicTermId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The associated Academic Term for which the program is being offered.
This field is a relationship field.
## Relationship Name
AcademicTerm
## Relationship Type
## Lookup
## Refers To
AcademicTerm
## Type
reference
ActionPlanTemplateVersionId
## 293
ProgramTermApplnTimelineEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The action plan template version associated with the Program Term Application Timeline.
## Relationship Name
ActionPlanTemplateVersion
## Relationship Type
## Lookup
## Refers To
ActionPlanTemplateVersion
## Type
reference
ApplicationTimelineId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The associated Application Timeline that determines when admissions to the program for
this term are open.
This field is a relationship field.
## Relationship Name
ApplicationTimeline
## Relationship Type
## Lookup
## Refers To
ApplicationTimeline
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 294
ProgramTermApplnTimelineEducation Cloud Standard Objects

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LearningProgramId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The associated Learning Program which is accepting students for admission.
This field is a relationship field.
## Relationship Name
LearningProgram
## Relationship Type
## Lookup
## Refers To
LearningProgram
## Type
reference
LearningProgramPlanId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning Program Plan associated with the timeline.
This field is a relationship field.
## Relationship Name
LearningProgramPlan
## Refers To
LearningProgramPlan
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
## 295
ProgramTermApplnTimelineEducation Cloud Standard Objects

DetailsField
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
PulseCheck
Represents the wellbeing of a learner based on a primary metric or criteria at a specific date and time. This object is available in API
version 62.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AssociatedObjectId
## 296
PulseCheckEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The object associated with the student's responses to a Pulse Check.
This field is a relationship field.
## Relationship Name
AssociatedObject
## Refers To
## Program
## Type
reference
AssociatedRecordTypeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The record type of the object associated with the student's responses to a Pulse Check.
This field is a relationship field.
## Relationship Name
AssociatedRecordType
## Refers To
RecordType
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the Pulse Check.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Pulse Check.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## 297
PulseCheckEducation Cloud Standard Objects

DetailsField
## Type
int
DaysOfWeek
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The days of the week for which the pulse check is scheduled. This field contains a bit mask.
## •
## Monday = 64
## •
## Tuesday = 32
## •
## Wednesday = 16
## •
## Thursday = 8
## •
## Friday = 4
## •
## Saturday = 2
## •
## Sunday = 1
Multiple days are represented as the sum of their numerical values. For example, Tuesday
and Thursday = 32 + 8 = 40.
## Type
textarea
## Description
## Properties
## Create, Update
## Description
The description of the Pulse Check.
## Type
dateTime
EndDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the Pulse Check ends.
## Type
int
ExpiryInDays
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of days the Pulse Check is active.
## Type
picklist
## Frequency
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## 298
PulseCheckEducation Cloud Standard Objects

DetailsField
## Description
Specifies the frequency that the Pulse Check occurs.
Possible values are:
## •
## Biweekly
## •
Half-Yearly—Half Yearly
## •
## Monthly
## •
## Quarterly
## •
## Weekly
## •
## Yearly
## Type
boolean
IsRecurring
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Pulse Check is recurring (true) or not (fales).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for the Pulse Check.
## 299
PulseCheckEducation Cloud Standard Objects

DetailsField
## Type
int
## Occurrences
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of occurrences of the Pulse Check.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
PrimaryQuestionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The primary assessment question associated with the Pulse Check.
This field is a relationship field.
## Relationship Name
PrimaryQuestion
## Refers To
AssessmentQuestion
## Type
reference
PulseCheckTemplateId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Pulse Check Template associated with the Pulse Check.
This field is a relationship field.
## Relationship Name
PulseCheckTemplate
## 300
PulseCheckEducation Cloud Standard Objects

DetailsField
## Refers To
PulseCheckTemplate
## Type
string
## Source
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The criteria based sharing rule or flow that triggered the Pulse Check.
## Type
dateTime
StartDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the Pulse Check starts.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PulseCheckHistory on page 385
History is available for tracked fields of the object.
PulseCheckOwnerSharingRule on page 387
Sharing rules are available for the object.
PulseCheckShare on page 389
Sharing is available for the object.
PulseCheckTemplate
Represents a common template used to create Pulse Check records. This object is available in API version 62.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 301
PulseCheckTemplateEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
AssessmentQuestionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The primary assessment question associated with the Pulse Check Template.
This field is a relationship field.
## Relationship Name
AssessmentQuestion
## Refers To
AssessmentQuestion
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the Pulse Check.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Pulse Check.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the Pulse Check Template.
## 302
PulseCheckTemplateEducation Cloud Standard Objects

DetailsField
## Type
int
ExpiryInDays
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of days the Pulse Check is active.
## Type
boolean
IsRecurring
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Pulse Check is recurring (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Pulse Check Template.
## Type
int
## Occurrences
## 303
PulseCheckTemplateEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of occurrences of the Pulse Check.
## Type
reference
OmniProcessId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Omnistudio Process associated with the Pulse Check Template.
This field is a relationship field.
## Relationship Name
OmniProcess
## Refers To
OmniProcess
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
picklist
RecurrenceFrequency
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the frequency that the Pulse Check occurs.
Possible values are:
## •
## Biweekly
## •
Half-Yearly—Half Yearly
## •
## Monthly
## •
## Quarterly
## 304
PulseCheckTemplateEducation Cloud Standard Objects

DetailsField
## •
## Weekly
## •
## Yearly
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PulseCheckTemplateHistory on page 385
History is available for tracked fields of the object.
PulseCheckTemplateOwnerSharingRule on page 387
Sharing rules are available for the object.
PulseCheckTemplateShare on page 389
Sharing is available for the object.
ProviderOffering
Represents people or organizations associated with providing benefits to program participants. This object is available in API version
60.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
BenefitId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Benefit associated with the Provider Offering.
This field is a relationship field.
## Relationship Name
## Benefit
## Relationship Type
## Lookup
## 305
ProviderOfferingEducation Cloud Standard Objects

DetailsField
## Refers To
## Benefit
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact associated with the Provider Offering.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## 306
ProviderOfferingEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string or number assigned to the Provider Offering.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The owner of the Provider Offering.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the provided Benefit.
Possible values are:
## •
## Active
## •
PendingApproval—Pending Approval
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
ProviderOfferingHistory on page 385
History is available for tracked fields of the object.
ProviderOfferingShare on page 389
Sharing is available for the object.
## 307
ProviderOfferingEducation Cloud Standard Objects

RgltyCodeRegClauseVer
Represents a junction between Regulatory Code and Regulation Clause Version objects. This object is available in API version 63.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Regulatory Code Regulation Clause Version.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## 308
RgltyCodeRegClauseVerEducation Cloud Standard Objects

DetailsField
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the Regulatory Code Regulation Clause Version.
## Type
reference
RegulationClauseVersionId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Regulation Clause Version associated with the record.
This field is a relationship field.
## Relationship Name
RegulationClauseVersion
## Refers To
RegulationClauseVersion
## Type
reference
RegulatoryCodeId
## Properties
## Create, Filter, Group, Sort
## Description
The Regulatory Code associated with the record.
This field is a relationship field.
## Relationship Name
RegulatoryCode
## Relationship Type
## Master-detail
## Refers To
RegulatoryCode (the master object)
RgltyCodeViolRegClVer
Represents a junction between Regulatory Code Violation and Regulation Clause Version objects. This object is available in API version
63.0 and later.
## 309
RgltyCodeViolRegClVerEducation Cloud Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Regulatory Code Regulation Clause Version.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## 310
RgltyCodeViolRegClVerEducation Cloud Standard Objects

DetailsField
## Description
The name of the Regulatory Code Violation Regulation Clause Version.
## Type
reference
RegulationClauseVersionId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The Regulation Clause Version associated with the record.
This field is a relationship field.
## Relationship Name
RegulationClauseVersion
## Refers To
RegulationClauseVersion
## Type
reference
RegulatoryCodeViolationId
## Properties
## Create, Filter, Group, Sort
## Description
The Regulatory Code Violation associated with the record.
This field is a relationship field.
## Relationship Name
RegulatoryCodeViolation
## Relationship Type
## Master-detail
## Refers To
RegulatoryCodeViolation (the master object)
SuccessTeam
Records details about a success team in Salesforce Scheduler. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 311
SuccessTeamEducation Cloud Standard Objects

## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The account associated with the success team.
This field is a relationship field.
## Relationship Name
## Account
## Relationship Type
## Lookup
## Refers To
## Account
## Type
boolean
CanSelfSchedule
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Specifies whether the success team can be self scheduled (true) or not (false).
The default value is false.
## Type
reference
CaseRecordTypeId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The case record type associated with the success team.
This field is a relationship field.
## Relationship Name
CaseRecordType
## Relationship Type
## Lookup
## Refers To
RecordType
## Type
string
DefaultUnassignedCaseTeam
## 312
SuccessTeamEducation Cloud Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Sort, Update
## Description
The case team associated with the success team.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Specifies whether the success team is active (true) or not (false).
The default value is false.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## 313
SuccessTeamEducation Cloud Standard Objects

DetailsField
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the success team.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
ResourceAssignmentType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of resource assignment for appointment scheduling.
Possible values are:
## •
## Automatic
## •
## Both
## •
## Manual
The default value is Manual.
## 314
SuccessTeamEducation Cloud Standard Objects

WatchlistedLearner
Represents information for a learner that needs to be monitored for support. This object is available in API version 62.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
CarePlanId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Care Plan associated with the Watchlisted Learner that's used to improve the learner’s
performance
This field is a relationship field.
## Relationship Name
CarePlan
## Refers To
CarePlan
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The learner’s Case record associated with the Watchlisted Learner.
This field is a relationship field.
## Relationship Name
## Case
## Refers To
## Case
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 315
WatchlistedLearnerEducation Cloud Standard Objects

DetailsField
## Description
Specifies the category of the Watchlisted Learner.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The ISO code for the currency associated with the Pulse Check.
Possible values are:
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
dateTime
EndDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the learner was removed as a Watchlisted Learner.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Watchlisted Learner is active (true) or not (false).
The default value is false.
## Type
boolean
IsEscalated
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Watchlisted Learner is escalated (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## 316
WatchlistedLearnerEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the Watchlisted Learner.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
ProgramEnrollmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Program Enrollment record associated with the Watchlisted Learner.
This field is a relationship field.
## 317
WatchlistedLearnerEducation Cloud Standard Objects

DetailsField
## Relationship Name
ProgramEnrollment
## Refers To
ProgramEnrollment
## Type
picklist
## Reason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the reason for adding the learner as a Watchlisted Learner.
## Type
textarea
ReasonDescription
## Properties
## Create, Nillable, Update
## Description
Descriptive context for adding the learner as a Watchlisted Learner.
## Type
dateTime
StartDate
## Properties
## Create, Filter, Sort, Update
## Description
The date and time when the learner was added as a Watchlisted Learner.
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the learner’s performance after being added as a Watchlisted Learner.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
WatchlistedLearnerHistory on page 385
History is available for tracked fields of the object.
WatchlistedLearnerOwnerSharingRule on page 387
Sharing rules are available for the object.
## 318
WatchlistedLearnerEducation Cloud Standard Objects

WatchlistedLearnerShare on page 389
Sharing is available for the object.
WorkTypeGroupRole
Represents a grouping of work types by roles, used to categorize types of appointments available in Salesforce Scheduler. This object is
available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
CaseTeamRole
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The role of the case team.
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## 319
WorkTypeGroupRoleEducation Cloud Standard Objects

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for the work type group role.
## Type
reference
WorkTypeGroupId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The work type group associated with this work type group role.
This field is a relationship field.
## Relationship Name
WorkTypeGroup
## Relationship Type
## Lookup
## Refers To
WorkTypeGroup
## 320
WorkTypeGroupRoleEducation Cloud Standard Objects

CHAPTER 5Education Cloud Fields on Standard Objects
## EDITIONS
Available in: Lightning
## Experience
in Performance, Enterprise,
## Developer,
and Unlimited editions that
have Education Cloud
enabled.
This section lists Education Cloud fields available with standard
Salesforce objects. These fields are available only in orgs where
Education Cloud is enabled.
In this chapter ...
•ActionPlanTemplate
•ActionPlanTemplateAssignment
•Assessment
•AssessmentEnvelope
•AssessmentEnvelopeItem
•AssessmentQuestion
•AssessmentQuestionResponse
•Award
•Benefit
•BenefitAssignment
•BenefitDisbursement
•BenefitType
•BusinessOperationsProcess
•BusinessProfile
•ComplianceControl
•CourseOffering
•CourseOfferingRelationship
•DocumentChecklistItem
•GiftCommitmentSchedule
•GoalAssignment
•GoalDefinition
•IndividualApplication
•Location
•PersonCompetency
•PersonEducation
•PersonEmployment
•PersonExamination
•PersonLifeEvent
•PreliminaryApplicationRef
•Program
•RecurrenceSchedule
•RegulatoryCode
•ServiceTerritoryMember
•Waitlist
## 321

ActionPlanTemplate
Represents the instance of an action plan template. This object is available in API version 60.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
boolean
ShouldShowOnLearnerPortal
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the action plan template is shown on the learner portal (true) or not (false).
The default value is false.
For more information, see ActionPlanTemplate in Salesforce Objects and Fields.
ActionPlanTemplateAssignment
Represents a junction between an action plant template's version and the target object (Care Plan Template, Benefit, and Goal Definition)
associated with them. This object is available in API version 60.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
AssignmentQueueName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 322
ActionPlanTemplateEducation Cloud Fields on Standard Objects

DetailsField
## Description
The name of the queue with ownership of the action plan records generated from the action
plan template assignment.
## Type
int
AssignmentSize
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of records to create for the assignment.
## Type
picklist
AssignmentType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of workflow to use for the assignment.
## Type
reference
AssociatedObjectId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Required. Represents the relation between an object associated with the action plan template
version record.
This field is a polymorphic relationship field.
## Relationship Name
AssociatedObject
## Relationship Type
## Lookup
## Refers To
Benefit, CarePlanTemplate, GoalDefinition
## Type
reference
AssociatedRecordTypeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The record type associated with the action plan template assignment.
This field is a relationship field.
## 323
ActionPlanTemplateAssignmentEducation Cloud Fields on Standard Objects

DetailsField
## Relationship Name
AssociatedRecordType
## Relationship Type
## Lookup
## Refers To
RecordType
For more information, see ActionPlanTemplateAssignment in Public Sector Solutions.
## Assessment
Stores the header data for an assessment. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
double
## Score
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The calculated score for an assessment.
For more information, see Assessment in Public Sector Solutions.
AssessmentEnvelope
Represents information about an envelope that contains the assessments related to a learner. This object is available in API version 62.0
and later.
## 324
AssessmentEducation Cloud Fields on Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
LearnerCaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Case of the learner associated with the Assessment Envelope.
This field is a relationship field.
## Relationship Name
LearnerCase
## Refers To
## Case
## Type
reference
LearnerProgramEnrollmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Program Enrollment of the learner associated with the Assessment Envelope.
This field is a relationship field.
## Relationship Name
LearnerProgramEnrollment
## Refers To
ProgramEnrollment
## Type
picklist
UsageType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The usage type for this assessment envelope.
Possible values are:
## •
## Default
## •
PulseCheck
## 325
AssessmentEnvelopeEducation Cloud Fields on Standard Objects

For more information, see AssessmentEnvelope in Health Cloud.
AssessmentEnvelopeItem
Represents information about an item in an envelope that contains the assessments related to a learner. This object is available in API
version 62.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
date
ExpirationDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date after which the assessment envelope becomes inactive.
## Type
int
PulseCheckOccurrenceNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The occurrence of the pulse check associated with the Assessment Envelope Item.
## Type
date
StartDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date from which the assessment envelope becomes active.
For more information, see AssessmentEnvelopeItem in Health Cloud.
AssessmentQuestion
Represents the container object that stores the questions required for an assessment. This object is available in API version 63.0 and later.
## 326
AssessmentEnvelopeItemEducation Cloud Fields on Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
DataType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The data type of the assessment question.
Possible values are:
## •
## Icon
For more information, see AssessmentQuestion in Public Sector Solutions.
AssessmentQuestionResponse
Stores the responses submitted to an assessment. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AssessmentQstnVerChoice2Id
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Assessment Question Version Choice associated with the Assessment Question Response.
This field is a relationship field.
## Relationship Name
AssessmentQuestionVerChoice
## 327
AssessmentQuestionResponseEducation Cloud Fields on Standard Objects

DetailsField
## Refers To
AssessmentQuestionVerChoice
For more information, see AssessmentQuestionResponse in Public Sector Solutions.
## Award
Represents a person's or organization's professional awards. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
boolean
IsCertification
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the award is a certification (true) or not (false).
The default value is false.
## Type
boolean
IsVerified
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates if the award is verified (true) or not (false).
The default value is false.
For more information, see Award in the Life Sciences developer guide.
## Benefit
Represents information about benefits associated with a program. This object is available in API version 57.0 and later.
## 328
AwardEducation Cloud Fields on Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
boolean
CanRegisterAsProvider
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether a user can self-register as a provider of the benefit (true) or not (false) on
an Experience Cloud site.
The default value is false.
## Type
reference
OmniProcessId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Omni Process associated with the Benefit.
This field is a relationship field.
## Relationship Name
OmniProcess
## Relationship Type
## Lookup
## Refers To
OmniProcess
For more information, see Benefit in Nonprofit Cloud.
BenefitAssignment
Represents the enrollment information of an individual to a benefit. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 329
BenefitAssignmentEducation Cloud Fields on Standard Objects

## Fields
DetailsField
## Type
reference
ProviderId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact who provides the benefit that's associated with the benefit assignment.
This field is a relationship field.
## Relationship Name
## Provider
## Relationship Type
## Lookup
## Refers To
## Contact
For more information, see BenefitAssignment in Nonprofit Cloud.
BenefitDisbursement
Represents the allocation of an enrollee's benefit that can be made as monetary or non-monetary with different frequencies. This object
is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ServiceAppointmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Service Appointment associated with the Benefit Disbursement.
This field is a relationship field.
## 330
BenefitDisbursementEducation Cloud Fields on Standard Objects

DetailsField
## Relationship Name
ServiceAppointment
## Relationship Type
## Lookup
## Refers To
ServiceAppointment
For more information, see BenefitDisbursement in Nonprofit Cloud.
BenefitType
Represents information about the type of benefits that can be applied to an individual or a group. This object is available in API version
60.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Required. The category of the benefit type. Picklist values aren't provided for this field and
must be added based on the requirements of the organization.
Possible values are:
## •
## Advising
## •
## Goods
## •
## Mentoring
## •
## Monetory
## •
## Session
For more information, see BenefitType in Public Sector Solutions.
## 331
BenefitTypeEducation Cloud Fields on Standard Objects

BusinessOperationsProcess
Represents a business operations process. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
UsageType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the usage type for the Business Operations Process.
Possible values are:
## •
## Compliance
## •
## Education
BusinessProfile
Represents details about the business on the license or permit application. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the institution.
## 332
BusinessOperationsProcessEducation Cloud Fields on Standard Objects

DetailsField
## Type
multipicklist
## Format
## Properties
Create, Filter, Nillable, Restricted picklist, Update
## Description
Specifies the education format offered at the institution.
Possible values are:
## •
## Hybrid
## •
In person
## •
## Virtual
## Type
multipicklist
GradesOffered
## Properties
Create, Filter, Nillable, Restricted picklist, Update
## Description
Specifies the grades offered at the institution.
Possible values are:
## •
## 1
## •
## 10
## •
## 11
## •
## 12
## •
## 2
## •
## 3
## •
## 4
## •
## 5
## •
## 6
## •
## 7
## •
## 8
## •
## 9
## •
## EY
## •
## K
## •
## KS1
## •
## KS2
## •
## KS3
## •
## KS4
## •
## P
## •
## PK3
## 333
BusinessProfileEducation Cloud Fields on Standard Objects

DetailsField
## •
## PK4
## Type
string
GradesOfferedSummary
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The summary of the grades offered at the institution.
## Type
url
ImageUrl
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The URL to an image for the institution.
## Type
picklist
InstitutionType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the institution's type.
Possible values are:
## •
## Charter
## •
## Private
## •
## Public
## Type
boolean
IsPubliclySearchable
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the business profile is publicly searchable (true) or not (false).
The default value is false.
## Type
picklist
## Region
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the region where the institution is located.
## 334
BusinessProfileEducation Cloud Fields on Standard Objects

DetailsField
## Type
string
ShortDescription
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The short description of the institution.
ComplianceControl
Represents a compliance control. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
UsageType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the usage type for the Compliance Control.
CourseOffering
Represents an instance of a training course with location and date details of training courses. This object is available in API version 57.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 335
ComplianceControlEducation Cloud Fields on Standard Objects

## Fields
DetailsField
## Type
reference
AcademicSessionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Academic Session associated with the Course Offering.
This field is a relationship field.
## Relationship Name
AcademicSession
## Relationship Type
## Lookup
## Refers To
AcademicSession
## Type
int
EnrolleeCount
## Properties
## Filter, Group, Nillable, Sort
## Description
The current number of enrollees in the Course Offering.
## Type
int
EnrollmentCapacity
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The maximum number of students that are allowed to enroll for the Course Offering.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the Course Offering is active (true) or not (false).
The default value is false.
## Type
boolean
IsWaitlistActive
## 336
CourseOfferingEducation Cloud Fields on Standard Objects

DetailsField
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the course offering has an active waitlist (true) or not (false).
The default value is false.
This field is a calculated field.
## Type
reference
LearningCourseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Learning Course record associated with the Course Offering.
This field is a relationship field.
## Relationship Name
LearningCourse
## Relationship Type
## Lookup
## Refers To
LearningCourse
## Type
reference
PrimaryFacultyId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact associated with the Course Offering as lead instructor.
This field is a relationship field.
## Relationship Name
PrimaryFaculty
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
string
SectionNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 337
CourseOfferingEducation Cloud Fields on Standard Objects

DetailsField
## Description
Differentiates a Course Offering from other sections in an academic term.
## Type
int
WaitlistCapacity
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The maximum number of students that can be waitlisted for the Course Offering.
## Type
int
WaitlistCount
## Properties
## Filter, Group, Nillable, Sort
## Description
The current number of people on the waitlist for the Course Offering.
## Type
picklist
WaitlistStatus
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the waitlist associated with the course offering.
Possible values are:
## •
## Canceled
## •
## Inactive
## •
## Open
## •
ProcessingOnly
## •
ProcessingPaused
For more information, see CourseOffering in Public Sector Solutions.
CourseOfferingRelationship
Represents a junction between a course offering and a related course offering. This object is available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 338
CourseOfferingRelationshipEducation Cloud Fields on Standard Objects

## Fields
DetailsField
## Type
reference
CourseOfferingId
## Properties
## Create, Filter, Group, Sort
## Description
The parent course offering related to the course offering relationship.
This field is a relationship field.
## Relationship Name
CourseOffering
## Relationship Type
## Master-detail
## Refers To
CourseOffering (the master object)
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
reference
LinkedCourseOfferingId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The linked course offering related to the course offering relationship.
This field is a relationship field.
## 339
CourseOfferingRelationshipEducation Cloud Fields on Standard Objects

DetailsField
## Relationship Name
LinkedCourseOffering
## Refers To
CourseOffering
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for the work type group role.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
CourseOfferingRelationshipFeed on page 379
Feed tracking is available for the object.
CourseOfferingRelationshipHistory on page 385
History is available for tracked fields of the object.
DocumentChecklistItem
Represents a checklist item for a file documentation upload. This object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
RejectReason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reason to reject the uploaded document.
## 340
DocumentChecklistItemEducation Cloud Fields on Standard Objects

DetailsField
## Type
picklist
RejectReasonType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the reason type to reject the uploaded document.
For more information, see DocumentChecklistItem in Financial Services Cloud.
GiftCommitmentSchedule
Represents the schedule for fulfilling the commitment. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Education Cloud Full Access license or the Fundraising Access license is enabled and the Fundraising
User system permission is assigned to users.
## Fields
DetailsField
## Type
picklist
AdvancementType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of advancement for the gift commitment schedule.
## Type
picklist
GenerationalCohort
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the generational cohort for the gift commitment schedule.
## 341
GiftCommitmentScheduleEducation Cloud Fields on Standard Objects

DetailsField
## Type
picklist
GraduationAchievement
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the graduation achievement for the gift commitment schedule.
## Type
picklist
GraduationCohort
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the graduation cohort for the gift commitment schedule.
For more information, see GiftCommitmentSchedule in Fundraising.
GoalAssignment
Represents the assignment of a goal.  This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
## Category
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The category of the goal assignment.
Possible values are:
## •
CareerAndLifeGoals—Career And Life Goals
For more information, see GoalAssignment in Health Cloud.
## 342
GoalAssignmentEducation Cloud Fields on Standard Objects

GoalDefinition
The definition of a care plan goal in the reusable PGI library that’s a part of Integrated Care Management. When instantiated, GoalDefinition
records create GoalAssignment records that serve as goals in care plans. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
## Category
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The category that the defined goal belongs to.
Possible values are:
## •
## Academic
## •
ExtraCurricular
## •
Well-Being
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of the defined goal.
Possible values are:
## •
Individual—Intermediate Goal
## •
Strategic—Top Goal
The default value is Individual.
## Type
picklist
UsageType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
This field is not used in Integrated Care Management.
## 343
GoalDefinitionEducation Cloud Fields on Standard Objects

DetailsField
Possible values are:
## •
## Improvement
For more information, see GoalDefinition in Health Cloud.
IndividualApplication
Represents information about the preferences of an applicant during program enrollment. This object is available in API version 57.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
string
AcademicTerm
## Properties
## Filter, Group, Nillable, Sort
## Description
The academic term associated with the application.
## Type
email
ApplicantEmail
## Properties
## Filter, Group, Nillable, Sort
## Description
The email address of the applicant.
## Type
phone
ApplicantPhone
## Properties
## Filter, Group, Nillable, Sort
## Description
The phone number of the applicant.
## 344
IndividualApplicationEducation Cloud Fields on Standard Objects

DetailsField
## Type
picklist
ApplicationCategory
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Categorizes the ways an application can be processed.
Possible values are:
## •
EarlyDecision
## •
RegularDecision
## Type
picklist
ApplicationType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of the application.
Possible values are:
## •
## Graduate
## •
## International
## •
## Transfer
## •
## Undergraduate
## Type
dateTime
ApprovedDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date on which the application was approved.
## Type
picklist
## Category
## Properties
## Create, Filter, Group, Sort, Update
## Description
The service category of the application.
Possible values are:
## •
## Education
## Type
reference
ContactId
## 345
IndividualApplicationEducation Cloud Fields on Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact person associated with the application.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
date
DecisionReleaseDate
## Properties
## Filter, Group, Nillable, Sort
## Description
The date when the application decision is announced.
## Type
date
DueDate
## Properties
## Filter, Group, Nillable, Sort
## Description
The last date when applicants can apply for admission.
## Type
string
LearningProgram
## Properties
## Filter, Group, Nillable, Sort
## Description
The learning program associated with the application.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Opportunity associated with the Individual Application.
## Relationship Name
## Opportunity
## 346
IndividualApplicationEducation Cloud Fields on Standard Objects

DetailsField
## Relationship Type
## Lookup
## Refers To
## Opportunity
## Type
reference
ProgramTermApplnTimelineId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The application timeline of the program term associated with the application.
This field is a relationship field.
## Relationship Name
ProgramTermApplnTimeline
## Relationship Type
## Lookup
## Refers To
ProgramTermApplnTimeline
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The submission and approval status of the application.
Possible values are:
## •
ApplicationDecision
## •
## Canceled
## •
## Denied
## •
## Enrolled
## •
EnrollmentFailed
## •
## In Review
## •
## Processing
## •
ReadyFor Decision
For more information, see IndividualApplication in Public Sector Solutions.
## 347
IndividualApplicationEducation Cloud Fields on Standard Objects

## Location
Represents details about a facility, building, room, or region. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
int
MaximumOccupancy
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The maximum occupancy of the location.
## Type
picklist
OwnershipStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of ownership of the facility.
Possible values are:
## •
## Leased
## •
## Other
## •
## Owned
## •
## Rented
For more information, see Location in Salesforce Platform Objects.
PersonCompetency
Represents the skills and competencies of a person. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 348
LocationEducation Cloud Fields on Standard Objects

## Fields
DetailsField
## Type
picklist
## Stage
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the stage of the person's competency.
Possible values are:
## •
## Acquired
## •
## Interested
PersonEducation
Represents information about the academic standing of an applicant. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account associated with the Person Education.
This field is a relationship field.
## Relationship Name
## Account
## Relationship Type
## Lookup
## Refers To
## Account
## 349
PersonEducationEducation Cloud Fields on Standard Objects

DetailsField
## Type
string
ClassRank
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The measure of the applicant's academic performance compared to the other students in
their class. This rank is based on the class rank reporting format that's followed by the institute,
such as a number or percentage.
## Type
picklist
ClassRankReportingFormat
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the class rank reporting format followed by the institution to report the applicant's
performance.
Possible values are:
## •
## Decile
## •
## Exact
## •
## None
## •
## Quartile
## •
## Quintile
## Type
picklist
ClassRankWeightingType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the GPA weighting type that’s used to calculate the applicant’s class rank.
Possible values are:
## •
## Unweighted
## •
## Weighted
## Type
reference
## Comment
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Comments on the applicant’s education details.
## 350
PersonEducationEducation Cloud Fields on Standard Objects

DetailsField
## Type
double
CumulativeGpa
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The grade point average of all the grades earned by an applicant in all the semesters or terms.
## Type
picklist
EducationLevel
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
Level of education achieved.
Possible values are:
## •
## Graduate
## •
HighSchool
## •
No FormalEducation
## •
PostGraduate
The default value is Fellowship.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the individual’s education.
## Type
int
GpaScale
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The scale used when calculating the applicant's grade point average.
## Type
picklist
GpaWeightingType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of weightage given to the applicant's grades when calculating their grade
point average.
## 351
PersonEducationEducation Cloud Fields on Standard Objects

DetailsField
Possible values are:
## •
## Unweighted
## •
## Weighted
## Type
int
GraduationClassSize
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of students who graduated from the same school, in the same academic year,
as the applicant.
## Type
reference
InstitutionAccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The institution associated with the applicant’s education.
This field is a relationship field.
## Relationship Name
## Individual
## Relationship Type
## Lookup
## Refers To
## Individual
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is active.
The default value is false.
For more information, see PersonEducation in Public Sector Solutions.
PersonEmployment
Represents information about a person’s employment. This object is available in API version 57.0 and later.
## 352
PersonEmploymentEducation Cloud Fields on Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account associated with the Person Employment.
This field is a relationship field.
## Relationship Name
## Account
## Relationship Type
## Lookup
## Refers To
## Account
## Type
currency
AnnualIncome
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The annual income of the person.
## Type
address
EmployerAddress
## Properties
## Filter, Nillable
## Description
The complete address of the employer.
## Type
string
EmployerCity
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The city where the employer is located.
## 353
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Type
string
EmployerCountry
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The country where the employer is located.
## Type
picklist
EmployerGeocodeAccuracy
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The level of accuracy of a location’s geographical coordinates compared with its physical
address. A geocoding service typically provides this value based on the address’s latitude
and longitude coordinates.
Possible values are:
## •
## Address
## •
## Block
## •
## City
## •
## County
## •
ExtendedZip
## •
NearAddress
## •
## Neighborhood
## •
## State
## •
## Street
## •
## Unknown
## •
## Zip
## Type
double
EmployerLatitude
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Used with Longitude to specify the precise geolocation of the address. Acceptable values
are numbers between –90 and 90 with up to 15 decimal places.
## Type
double
EmployerLongitude
## Properties
## Create, Filter, Nillable, Sort, Update
## 354
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Description
Used with Latitude to specify the precise geolocation of the address. Acceptable values are
numbers between –180 and 180 with up to 15 decimal places.
## Type
phone
EmployerPhone
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Employer's phone number.
## Type
string
EmployerPostalCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The postal code of the employer’s address.
## Type
string
EmployerState
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The state of the employer’s address.
## Type
textarea
EmployerStreet
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The street address of the employer.
## Type
string
EmployerTaxAccountNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Tax Deduction and Collection Account Number (TAN) of the employer.
Available in API version 61.0 and later with Financial Services Cloud.
## Type
picklist
EmploymentIndustry
## 355
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the employment industry.
## Type
picklist
EmploymentSite
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the site of employment.
Possible values are:
## •
## Hybrid
## •
Onsite—On-site
## •
## Remote
## Type
picklist
EmploymentStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the employment status with the employer.
Possible values are:
## •
HomeMaker
## •
## Employed
## •
## Retired
## •
Self-Employed
## •
## Student
## •
## Unemployed
## •
UnemployedwithIncome
## •
UnemployedwithoutIncome
## Type
picklist
EmploymentType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the employment type for the party.
Possible values are:
## 356
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
API version 61.0 and later with Financial Services Cloud:
## •
## Contract
## •
Full-Time
## •
Part-Time
## •
## Salaried
## •
Self-Employed
## •
## Temporary
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last date of employment at this job.
## Type
currency
HourlyWage
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The hourly wage for the party.
Available in API version 61.0 and later with Financial Services Cloud.
## Type
boolean
IsCurrentEmployment
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the person employment added is the current employer of the customer.
Available in API version 61.0 and later with Financial Services Cloud.
The default value is false.
## Type
boolean
IsFlagged
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the employment-related information requires additional scrutiny.
Available in API version 61.0 and later with Financial Services Cloud.
The default value is false.
## 357
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name for this record.
## 358
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Type
picklist
## Occupation
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the person’s occupation.
Possible values are:
## •
## Actoror Entertainer
## •
Architector UrbanPlanner
## •
## Architectureand Engineering
## •
## Artist
## •
Arts,Design,Entertainment,Sports,and Media
## •
Business(Clerical)
## •
BusinessExecutive(Management,Administrator)
## •
BusinessOwneror Proprietor
## •
BusinessSalespersonor Buyer
## •
Buildingand GroundsCleaning/Maintenance
## •
Clergy(Minister,Priest)
## •
Clergy(OtherReligious)
## •
ClinicalPsychologist
## •
CollegeAdministratoror Staff
## •
CollegeTeacher
## •
Communityand SocialService
## •
ComputerProgrammeror Analyst
## •
## Computerand Mathematical
## •
## Conservationistor Forester
## •
## Constructionand Extraction
## •
Dentist(IncludingOrthodontist)
## •
## Dietitianor Nutritionist
## •
Education,Training,and Library
## •
## Engineer
## •
## Farmeror Rancher
## •
Farming,Fishing,and Forestry
## •
FoodPreparationand Serving
## •
ForeignServiceWorker(IncludingDiplomat)
## •
HealthcarePractitionersand Technical
## •
HealthcareSupport
## •
Homemaker(Full-Time)
## 359
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## •
InteriorDecorator(IncludingDesigner)
## •
Installation,Maintenance,and Repair
## •
## Lab Technicianor Hygienist
## •
## Laborer
## •
Law EnforcementOfficer
## •
Lawyer(Attorney)or Judge
## •
## Legal
## •
Life,Physical,and SocialScience
## •
## Management
## •
MilitaryService(Career)
## •
Musician(Performer,Composer)
## •
## Nurse
## •
OfficeAdmin
## •
## Optometrist
## •
## Other
## •
PersonalCareand Service
## •
## Pharmacist
## •
## Physician
## •
## Policymakeror Government
## •
ProtectiveService
## •
## Production
## •
## Sales
## •
SchoolCounselor
## •
SchoolPrincipalor Superintendent
## •
ScientificResearcher
## •
SkilledTrades
## •
Social,Welfare,or RecreationWorker
## •
Teacheror Administrator(Elementary)
## •
Teacheror Administrator(Secondary)
## •
Therapist(Physical,Occupational,Speech)
## •
Transportationand MaterialMoving
## •
## Veterinarian
## •
## Writeror Journalist
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## 360
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
string
## Position
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last position of the person at this job.
## Type
reference
RelatedPersonId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The person associated with the employment.
This field is a polymorphic relationship field.
## Relationship Name
RelatedPerson
## Relationship Type
## Lookup
## Refers To
## Account, Contact
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of employment at this job.
## Type
date
VerificationDate
## 361
PersonEmploymentEducation Cloud Fields on Standard Objects

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the person employment was verified.
Available in API version 61.0 and later with Financial Services Cloud.
## Type
picklist
VerificationStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the employment verification done for the party profile.
Available in API version 61.0 and later with Financial Services Cloud.
## Type
int
WeeklyHourCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of hours per week that the party works for the employer.
Available in API version 61.0 and later with Financial Services Cloud.
## Type
picklist
WorkerType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the worker type for the party that's employed.
Possible values are:
## •
## Hourly
## •
## Salaried
For more information, see PersonEmployment in Public Sector Solutions.
PersonExamination
Represents the examinations taken by a person. This object is available in API version 57.0 and later.
## 362
PersonExaminationEducation Cloud Fields on Standard Objects

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account associated with the Person Examination.
This field is a relationship field.
## Relationship Name
## Account
## Relationship Type
## Lookup
## Refers To
## Account
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
ID of the contact related to this record.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
dateTime
EffectiveFrom
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Date from which the examination is effective from.
## 363
PersonExaminationEducation Cloud Fields on Standard Objects

DetailsField
## Type
dateTime
EffectiveTo
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Date till which the examination is effective.
## Type
dateTime
ExaminationDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Date the examination was taken.
## Type
reference
ExaminationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
ID of the examination.
This field is a relationship field.
## Relationship Name
## Examination
## Relationship Type
## Lookup
## Refers To
## Examination
## Type
picklist
InstitutionName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Name of the institution offering the examination.
Possible values are:
## •
## Abitur
## •
## Apolytirion
## •
Baccalauréat(BAC)
## •
CambridgeInternationEducationPre-University(CIE
Pre-U)
## 364
PersonExaminationEducation Cloud Fields on Standard Objects

DetailsField
## •
CaribbeanAdvancedProficiencyExamII (CAPE)
## •
CenterShikenor KyotsuTests
## •
ChineseNationalEntranceExamination(GaoKao)or Joint
EntranceExamination(JEE)
## •
CollegeScholasticAbilityTest(CSAT)
## •
ConcursoNacionalde Acessoao EnsinoSuperior(CNA)
## •
EmeritesStandardizedTest(EmSAT)
## •
EthiopianSchoolLeavingCertificateExams(ESLCE)or
EthiopianHigherEducationEntrance
## •
EuropeanBaccalaureate
## •
GCE-AdvancedLevelExaminations(GCE-ALevels)
## •
## Higher/ Level6
## •
HigherSecondaryCertificate(HSC)
## •
HigherSecondaryEducationBoardExamination(HSEBE)or
SchoolLeavingCertificate(SLC)
## •
HigherSecondarySchoolCertificate(HSSC)
## •
IndianCertificateof SecondaryEducation- ClassX
## (ICSE)
## •
IndianSchoolCertificate- ClassXII (ISC)
## •
IrishLeavingCertificate
## •
KenyaCertificateof SecondaryEducation(KCSE)
## •
Matriculationand SecondaryEducationCertificate
## (MATSEC)
## •
Matura(Maturita)
## •
## Other
## •
Pruebade SelecciónUniversitaria(PSU)
## •
SijilTinggiPersekolahanMalaysia(STPM)
## •
Te'udatBagrut
## •
TertiaryEntranceRank(TER)or UniversitiesAdmission
Index(UAI)
## •
ThanaweyaAmma
## •
WesternAfricanSeniorSchoolCertificateExamination
## (WASSCE)
## Type
boolean
IsLocked
## Properties
Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the record is locked (true) or not (false).
## 365
PersonExaminationEducation Cloud Fields on Standard Objects

DetailsField
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
boolean
MayEdit
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the record can be edited (true) or not (false).
The default value is false.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name for this record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this record.
This field is a polymorphic relationship field.
## 366
PersonExaminationEducation Cloud Fields on Standard Objects

DetailsField
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ParentPersonExaminationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The parent Person Examination associated with this examination.
This field is a relationship field.
## Relationship Name
ParentPersonExamination
## Relationship Type
## Lookup
## Refers To
PersonExamination
## Type
picklist
## Result
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Result of the examination.
Possible values are:
## •
## Fail
## •
## Pass
## Type
int
## Score
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Score secured in the examination.
## Type
picklist
ScoreType
## 367
PersonExaminationEducation Cloud Fields on Standard Objects

DetailsField
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the type of examination score.
Possible values are:
## •
## Actual
## •
## Predicted
## Type
picklist
SubjectName
## Properties
Create, Filter, Group, Restricted picklist, Nillable, Sort, Update
## Description
Specifies the academic subject associated with the examination.
Possible values are:
## •
## English
## •
## Mathematics
## •
## Reading
## •
## Readingand Writing
## •
## Science
## •
## Writing
## •
## Composite
## Type
dateTime
VerificationDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Date and time the examination details were verified.
## Type
picklist
VerificationStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Status of the examination details verification.
Possible values are:
## •
## Accepted
## •
## Rejected
## 368
PersonExaminationEducation Cloud Fields on Standard Objects

DetailsField
## •
## Verified
## •
## Waived
For more information, see PersonExamination in Public Sector Solutions.
PersonLifeEvent
Represents the life events of an Individual. Eg: Marriage, Birth of a baby, Birthday, Engagement, Divorce This object is available in API
version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
picklist
EventType
## Properties
## Create, Filter, Group, Sort
## Description
Possible values are:
## •
## Baby
## •
## Birth
## •
DomesticPartnership
## •
## Enrolled
## •
## Graduation
## •
## Home
## •
## Job
## •
## Marriage
## •
## Relocation
## •
## Retirement
For more information, see PersonLifeEvent in Public Sector Solutions.
## 369
PersonLifeEventEducation Cloud Fields on Standard Objects

PreliminaryApplicationRef
Represents details about saved applications. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
ApplicantId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact record associated with the person who submitted the application.
This field is a relationship field.
## Relationship Name
## Applicant
## Relationship Type
## Lookup
## Refers To
## Contact
## Type
picklist
ApplicationCategory
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the category of the application based on the admission decision period.
Possible values are:
## •
EarlyDecision
## •
RegularDecision
## Type
picklist
ApplicationType
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## 370
PreliminaryApplicationRefEducation Cloud Fields on Standard Objects

DetailsField
## Description
Possible values are:
## •
BusinessLicenseApplication
## •
BusinessPrescreening
## •
IndividualApplication
## •
PublicComplaint
## Type
reference
ProgramTermApplnTimelineId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The program term application timeline associated with the preliminary application reference
record.
This field is a relationship field.
## Relationship Name
ProgramTermApplnTimeline
## Relationship Type
## Lookup
## Refers To
ProgramTermApplnTimeline
## Type
date
SubmissionDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the application was submitted.
## Type
reference
SubmittedByContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Contact who submits an application.
This field is a relationship field.
## Relationship Name
## Contact
## Relationship Type
## Lookup
## 371
PreliminaryApplicationRefEducation Cloud Fields on Standard Objects

DetailsField
## Refers To
## Contact
For more information, see PreliminaryApplicationRef in Nonprofit Cloud.
## Program
Represents information about the enrollment and disbursement of benefits in a program. This object is available in API version 57.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
multipicklist
## Format
## Properties
Create, Filter, Nillable, Restricted picklist, Update
## Description
Specifies the format in which the program is offered.
Possible values are:
## •
## Hybrid
## •
In person
## •
## Virtual
## Type
reference
OmniProcessId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The omniscript that runs the prerequisite questionnaire for program enrollment.
This field is a relationship field.
## Relationship Name
OmniProcess
## 372
ProgramEducation Cloud Fields on Standard Objects

DetailsField
## Relationship Type
## Lookup
## Refers To
OmniProcess
## Type
boolean
ShouldShowOnLearnerPortal
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Determines whether the program is shown on the learner portal (true) or not (false).
The default value is false.
## Type
reference
SuccessTeamId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The success team associated with the Program.
This field is a relationship field.
## Relationship Name
SuccessTeam
## Relationship Type
## Lookup
## Refers To
SuccessTeam
For more information, see Program in Nonprofit Cloud.
RecurrenceSchedule
Represents a recurrence schedule.  This object is available in API version 62.0 and later.
## Supported Calls
create(), delete(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve(),
undelete(), update(), upsert()
## 373
RecurrenceScheduleEducation Cloud Fields on Standard Objects

## Fields
DetailsField
## Type
picklist
ProcessName
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The name of the scheduling process that executes the request.
Possible values are:
## •
Industries_PulseCheck—Pulse Checks
For more information, see RecurrenceSchedule in Nonprofit Cloud.
RegulatoryCode
Represents the regulation code enforced by the regulatory body. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
boolean
CanResolveAutomatically
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the regulatory code can be automatically resolved (true) or not (false).
The default value is false.
For more information, see RegulatoryCode in the Public Sector Solutions developer guide.
## 374
RegulatoryCodeEducation Cloud Fields on Standard Objects

ServiceTerritoryMember
Represents a service resource who can be assigned in a service territory in Field Service, Salesforce Scheduler, Workforce Engagement,
or Education Cloud. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), update(), upsert()
## Fields
DetailsField
## Type
reference
LocationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The location where the service resource takes appointments.
This field is a relationship field.
## Relationship Name
## Location
## Relationship Type
## Lookup
## Refers To
## Location
For more information, see ServiceTerritoryMember in Salesforce Scheduler.
## Waitlist
Represents a queue to which drop in customers who visit the branch without an already scheduled appointment are added. This object
is available in API version 61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 375
ServiceTerritoryMemberEducation Cloud Fields on Standard Objects

## Fields
DetailsField
## Type
url
## Link
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The URL for the waitlist.
For more information, see
Example: Waitlist in Salesforce Scheduler.
## 376
WaitlistEducation Cloud Fields on Standard Objects

CHAPTER 6Education Cloud Associated Objects
## EDITIONS
Available in: Lightning
## Experience
in Performance, Enterprise,
## Developer,
and Unlimited editions that
have Education Cloud
enabled.
This section provides a list of objects associated to Consumer Goods
Cloud standard objects with their standard fields.
Some fields may not be listed for some objects. To see the system
fields for each object, see System Fields in the Object Reference for
Salesforce and Lightning Platform.
To verify the complete list of fields for an object, use a describe call
from the API or inspect with an appropriate tool. For example,
inspect the WSDL or use a schema viewer.
In this chapter ...
•StandardObjectNameChangeEvent
•StandardObjectNameFeed
•StandardObjectNameHistory
•StandardObjectNameOwnerSharingRule
•StandardObjectNameShare
## 377

StandardObjectNameChangeEvent
A ChangeEvent object is available for each object that supports Change Data Capture. You can subscribe to a stream of change events
using Change Data Capture to receive data tied to record changes in Salesforce. Changes include record creation, updates to an existing
record, deletion of a record, and undeletion of a record. A change event isn’t a Salesforce object — it doesn’t support CRUD operations
or queries. It’s included in the object reference so you can discover which Salesforce objects support change events.
## Supported Calls
describeSObjects()
## Special Access Rules
## •
Not all objects may be available in your org. Some objects require specific feature settings and permissions to be enabled.
## •
For more special access rules, if any, see the documentation for the standard object. For example, for AccountChangeEvent, see the
special access rules for Account.
## Change Event Name
Change events are available for all custom objects and a subset of standard objects. The name of a change event is based on the name
of the corresponding object for which it captures the changes.
## Standard Object Change Event Name
<Standard_Object_Name>ChangeEvent
Example: AccountChangeEvent
## Custom Object Change Event Name
<Custom_Object_Name>__ChangeEvent
Example: MyCustomObject__ChangeEvent
## Change Event Fields
The fields that a change event can include correspond to the fields on the associated parent Salesforce object, with a few exceptions.
For example, AccountChangeEvent fields correspond to the fields on Account.
The fields that a change event doesn’t include are:
## •
The IsDeleted system field.
## •
The SystemModStamp system field.
## •
Any field whose value isn’t on the record and is derived from another record or from a formula, except roll-up summary fields, which
are included. Examples are formula fields. Examples of fields with derived values include LastActivityDate and PhotoUrl.
Each change event also contains header fields. The header fields are included inside the ChangeEventHeader field. They contain
information about the event, such as whether the change was an update or delete and the name of the object, like Account.
In addition to the event payload, the event schema ID is included in the schema field. Also included is the event-specific field,
replayId, which is used for retrieving past events.
## 378
StandardObjectNameChangeEventEducation Cloud Associated Objects

## Event Message Example
The following example is an event message in JSON format for a new account record creation.
## {
"schema":"IeRuaY6cbI_HsV8Rv1Mc5g",
## "payload":{
"ChangeEventHeader":{
"entityName":"Account",
"recordIds":[
"<record_ID>"
## ],
"changeType":"CREATE",
"changeOrigin":"com/salesforce/api/soap/51.0;client=SfdcInternalAPI/",
"transactionKey":"0002343d-9d90-e395-ed20-cf416ba652ad",
"sequenceNumber":1,
"commitTimestamp":1612912679000,
"commitNumber":10716283339728,
"commitUser":"<User_ID>"
## },
"Name":"Acme",
"Description":"Everyoneis talkingaboutthe cloud.But whatdoesit mean?",
"OwnerId":"<Owner_ID>",
"CreatedDate":"2021-02-09T23:17:59Z",
"CreatedById":"<User_ID>",
"LastModifiedDate":"2021-02-09T23:17:59Z",
"LastModifiedById":"<User_ID>"
## },
## "event":{
"replayId":6
## }
## }
API Version and Schema
When you subscribe to change events, the subscription uses the latest API version and the event messages received reflect the latest
field definitions. For more information, see API Version and Event Schema in the Change Data Capture Developer Guide.
## Usage
For more information about Change Data Capture, see Change Data Capture Developer Guide.
StandardObjectNameFeed
StandardObjectNameFeed is the model for all feed objects associated with standard objects. These objects represent the posts
and feed-tracked changes of a standard object.
The object name is variable and uses StandardObjectNameFeed syntax. For example, AccountFeed represents the posts and
feed-tracked changes on an account record. We list the available associated feed objects at the end of this topic. For specific version
information, see the documentation for the standard object.
## 379
StandardObjectNameFeedEducation Cloud Associated Objects

## Supported Calls
delete(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()
## Special Access Rules
In the internal org, users can delete all feed items they created. This rule varies in Experience Cloud sites where threaded discussions
and delete-blocking are enabled. Site members can delete all feed items they created, provided the feed items don’t have content nested
under them — like a comment, answer, or reply. Where the feed item has nested content, only feed moderators and users with the
Modify All Data permission can delete threads.
To delete feed items they didn’t create, users must have one of these permissions:
## •
## Modify All Data
## •
Modify All Records on the parent object, like Account for AccountFeed
## •
## Moderate Chatter
Note:  Users with the Moderate Chatter permission can delete only the feed items and comments they can see.
Only users with this permission can delete items in unlisted groups.
For more special access rules, if any, see the documentation for the standard object. For example, for AccountFeed, see the special access
rules for Account.
## Fields
DetailsField
## Type
reference
BestCommentId
## Properties
## Filter, Group, Nillable, Sort
## Description
The ID of the comment marked as best answer on a question post.
## Type
textarea
## Body
## Properties
## Nillable, Sort
## Description
The body of the post. Required when Type is TextPost. Optional when Type is
ContentPost or LinkPost.
## Type
int
CommentCount
## Properties
## Filter, Group, Sort
## 380
StandardObjectNameFeedEducation Cloud Associated Objects

DetailsField
## Description
The number of comments associated with this feed item.
## Type
reference
ConnectionId
## Properties
## Filter, Group, Nillable, Sort
## Description
When a PartnerNetworkConnection modifies a record that is tracked, the CreatedBy field
contains the ID of the system administrator. The ConnectionId contains the ID of the
PartnerNetworkConnection. Available if Salesforce to Salesforce is enabled for your
organization.
## Type
reference
InsertedById
## Properties
## Group, Nillable, Sort
## Description
ID of the user who added this item to the feed. For example, if an application migrates posts
and comments from another application into a feed, the InsertedBy value is set to the
ID of the context user.
## Type
boolean
isRichText
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether the feed item Body contains rich text. If you post a rich text feed comment
using SOAP API, set IsRichText to true and escape HTML entities from the body.
Otherwise, the post is rendered as plain text.
Rich text supports the following HTML tags:
## •
## <p>
Tip:  Though the <br> tag isn’t supported, you can use <p>&nbsp;</p>
to create lines.
## •
## <a>
## •
## <b>
## •
## <code>
## •
## <i>
## •
## <u>
## •
## <s>
## •
## <ul>
## 381
StandardObjectNameFeedEducation Cloud Associated Objects

DetailsField
## •
## <ol>
## •
## <li>
## •
## <img>
The <img> tag is accessible only through the API and must reference files in Salesforce
similar to this example: <imgsrc="sfdc://069B0000000omjh"></img>
Note:  In API version 35.0 and later, the system replaces special characters in rich text
with escaped HTML. In API version 34.0 and prior, all rich text appears as a plain-text
representation.
## Type
int
LikeCount
## Properties
## Filter, Group, Sort
## Description
The number of likes associated with this feed item.
## Type
url
LinkUrl
## Properties
## Nillable, Sort
## Description
The URL of a LinkPost.
## Type
picklist
NetworkScope
## Properties
Group, Nillable, Restricted picklist, Sort
## Description
Specifies whether this feed item is available in the default Experience Cloud site, a specific
Experience Cloud site, or all sites. This field is available in API version 26.0 and later, if digital
experiences is enabled for your org.
NetworkScope can have the following values:
## •
NetworkId—The ID of the Experience Cloud site in which the FeedItem is available.
If left empty, the feed item is only available in the default Experience Cloud site.
## •
AllNetworks—The feed item is available in all Experience Cloud sites.
Note the following exceptions for NetworkScope:
## •
Only feed items with a Group or User parent can set a NetworkId or a null value for
NetworkScope.
## •
For feed items with a record parent, users can set NetworkScope only to
AllNetworks.
## 382
StandardObjectNameFeedEducation Cloud Associated Objects

DetailsField
## •
You can’t filter a feed item on the NetworkScope field.
## Type
reference
ParentId
## Properties
## Filter, Group, Sort
## Description
ID of the record that is tracked in the feed. The detail page for the record displays the feed.
## Type
reference
RelatedRecordId
## Properties
## Group, Nillable, Sort
## Description
ID of the ContentVersion record associated with a ContentPost. This field is null for all
posts except ContentPost.
## Type
string
## Title
## Properties
## Group, Nillable, Sort
## Description
The title of the feed item. When the Type is LinkPost, the LinkUrl is the URL and
this field is the link name.
## Type
picklist
## Type
## Properties
Filter, Group, Nillable, Restricted picklist, Sort
## Description
The type of feed item. Values are:
## •
ActivityEvent—indirectly generated event when a user or the API adds a Task
associated with a feed-enabled parent record (excluding email tasks on cases). Also
occurs when a user or the API adds or updates a Task or Event associated with a case
record (excluding email and call logging).
For a recurring Task with CaseFeed disabled, one event is generated for the series only.
For a recurring Task with CaseFeed enabled, events are generated for the series and each
occurrence.
## •
AdvancedTextPost—created when a user posts a group announcement and, in
Lightning Experience as of API version 39.0 and later, when a user shares a post.
## •
AnnouncementPost—Not used.
## •
ApprovalPost—generated when a user submits an approval.
## 383
StandardObjectNameFeedEducation Cloud Associated Objects

DetailsField
## •
BasicTemplateFeedItem—Not used.
## •
CanvasPost—a post made by a canvas app posted on a feed.
## •
CollaborationGroupCreated—generated when a user creates a public group.
## •
CollaborationGroupUnarchived—Not used.
## •
ContentPost—a post with an attached file.
## •
CreatedRecordEvent—generated when a user creates a record from the publisher.
## •
DashboardComponentAlert—generated when a dashboard metric or gauge
exceeds a user-defined threshold.
## •
DashboardComponentSnapshot—created when a user posts a dashboard
snapshot on a feed.
## •
LinkPost—a post with an attached URL.
## •
PollPost—a poll posted on a feed.
## •
ProfileSkillPost—generated when a skill is added to a user’s Chatter profile.
## •
QuestionPost—generated when a user posts a question.
## •
ReplyPost—generated when Chatter Answers posts a reply.
## •
RypplePost—generated when a user creates a Thanks badge in WDC.
## •
TextPost—a direct text entry on a feed.
## •
TrackedChange—a change or group of changes to a tracked field.
## •
UserStatus—automatically generated when a user adds a post. Deprecated.
## Type
picklist
## Visibility
## Properties
Filter, Group, Nillable, Restricted picklist, Sort
## Description
Specifies whether this feed item is available to all users or internal users only. This field is
available if digital experiences is enabled for your org.
Visibility can have the following values:
## •
AllUsers—The feed item is available to all users who have permission to see the
feed item.
## •
InternalUsers—The feed item is available to internal users only.
Note the following exceptions for Visibility:
## •
For record posts, Visibility is set to InternalUsers for all internal users by
default.
## •
External users can set Visibility only to AllUsers.
## •
On user and group posts, only internal users can set Visibility to
InternalUsers.
## 384
StandardObjectNameFeedEducation Cloud Associated Objects

## Usage
A feed for an object is automatically created when a user enables feed tracking for the object. Use feeds to track changes to records. For
example, AccountFeed tracks changes to an account record. Use feed objects to retrieve the content of feed fields, such as type of feed
or feed ID.
Note the following SOQL restrictions. No SOQL limit if logged-in user has View All Data permission. If not, specify a LIMIT clause of
1,000 records or fewer. SOQL ORDERBY on fields using relationships is not available. Use ORDERBY on fields on the root object
in the SOQL query.
## Objects That Follow This Model
These objects follow the standard pattern for associated feed objects.
## •
AssessmentTaskFeed
## •
AssessmentTaskDefinitionFeed
## •
AssessmentTaskIndDefinitionFeed
## •
AssortmentFeed
## •
PromotionFeed
## •
RetailLocationGroupFeed
## •
RetailStoreFeed
## •
RetailStoreGroupAssignmentFeed
## •
RetailStoreKpiFeed
## •
RetailVisitKpiFeed
## •
VisitFeed
## •
VisitedPartyFeed
## •
VisitorFeed
StandardObjectNameHistory
StandardObjectNameHistory is the model for all history objects associated with standard objects. These objects represent the
history of changes to the values in the fields of a standard object.
The object name is variable and uses StandardObjectNameHistory syntax. For example, AccountHistory represents the history of
changes to the values of an account record’s fields. We list the available associated history objects at the end of this topic. For specific
version information, see the documentation for the standard object.
## Supported Calls
describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()
## Special Access Rules
For specific special access rules, if any, see the documentation for the standard object. For example, for AccountHistory, see the special
access rules for Account.
## 385
StandardObjectNameHistoryEducation Cloud Associated Objects

## Fields
DetailsField Name
## Type
reference
StandardObjectNameId
## Properties
## Filter, Group, Sort
## Description
ID of the standard object.
## Type
picklist
DataType
## Properties
Filter, Group, Nillable, Restricted picklist, Sort
## Description
Data type of the field that was changed.
## Type
picklist
## Field
## Properties
Filter, Group, Restricted picklist, Sort
## Description
Name of the field that was changed.
## Type
anyType
NewValue
## Properties
## Nillable, Sort
## Description
New value of the field that was changed.
## Type
anyType
OldValue
## Properties
## Nillable, Sort
## Description
Old value of the field that was changed.
## 386
StandardObjectNameHistoryEducation Cloud Associated Objects

StandardObjectNameOwnerSharingRule
StandardObjectNameOwnerSharingRule is the model for all owner sharing rule objects associated with standard objects. These
objects represent a rule for sharing a standard object with users other than the owner.
The object name is variable and uses StandardObjectNameOwnerSharingRule syntax. For example,
ChannelProgramOwnerSharingRule is a rule for sharing a channel program with users other than the channel program owner. We list
the available associated owner sharing rule objects at the end of this topic. For specific version information, see the standard object
documentation.
Note:  To enable access to this object for your org, contact Salesforce customer support. However, we recommend that you
instead use Metadata API to programmatically update owner sharing rules because it triggers automatic sharing rule recalculation.
The SharingRules Metadata API type is enabled for all orgs.
## Supported Calls
create(), delete(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve(), update(),
upsert()
## Special Access Rules
For specific special access rules, if any, see the documentation for the standard object. For example, for ChannelProgramOwnerSharingRule,
see the special access rules for ChannelProgram.
## Fields
DetailsField Name
## Type
picklist
AccessLevel
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Determines the level of access users have to records. Values are:
## •
Read (read only)
## •
## Edit (read/write)
## Type
textarea
## Description
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Description of the sharing rule. Maximum length is 1000 characters.
## 387
StandardObjectNameOwnerSharingRuleEducation Cloud Associated Objects

DetailsField Name
## Type
string
DeveloperName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The unique name of the object in the API. This name can contain only underscores
and alphanumeric characters, and must be unique in your org. It must begin with
a letter, not include spaces, not end with an underscore, and not contain two
consecutive underscores. In managed packages, this field prevents naming
conflicts on package installations. With this field, a developer can change the
object’s name in a managed package and the changes are reflected in a
subscriber’s organization.
Note:  When creating large sets of data, always specify a unique
DeveloperName for each record. If no DeveloperName is
specified, performance slows down while Salesforce generates one for
each record.
## Type
reference
GroupId
## Properties
## Create, Filter, Group, Sort
## Description
ID of the source group. Records that are owned by users in the source group
trigger the rule to give access.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Label of the sharing rule as it appears in the UI. Maximum length is 80 characters.
## Type
reference
UserOrGroupId
## Properties
## Create, Filter, Group, Sort
## Description
ID of the user or group that you are granting access to.
## 388
StandardObjectNameOwnerSharingRuleEducation Cloud Associated Objects

StandardObjectNameShare
StandardObjectNameShare is the model for all share objects associated with standard objects. These objects represent a sharing
entry on the standard object.
The object name is variable and uses StandardObjectNameShare syntax. For example, AccountBrandShare is a sharing entry on
an account brand. We list the available associated share objects at the end of this topic. For specific version information, see the standard
object documentation.
## Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
## Special Access Rules
For specific special access rules, if any, see the documentation for the standard object. For example, for AccountBrandShare, see the
special access rules for AccountBrand.
## Fields
DetailsField Name
## Type
picklist
AccessLevel
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The level of access allowed. Values are:
## •
## All (owner)
## •
## Edit (read/write)
## •
Read (read only)
## Type
reference
ParentId
## Properties
## Create, Filter, Group, Sort
## Description
ID of the parent record.
## Type
picklist
RowCause
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort
## 389
StandardObjectNameShareEducation Cloud Associated Objects

DetailsField Name
## Description
Reason that the sharing entry exists.
## Type
reference
UserOrGroupId
## Properties
## Create, Filter, Group, Sort
## Description
ID of the user or group that has been given access to the object.
## Objects That Follow This Model
These objects follow the standard pattern for associated feed objects.
## •
AssessmentIndicatorDefinitionShare
## •
AssessmentTaskShare
## •
AssessmentTaskDefinitionShare
## •
AssortmentShare
## •
OtherComponentTask
## •
PromotionShare
## •
RetailLocationGroupShare
## •
RetailStoreShare
## •
RetailStoreKpiShare
## •
StoreProductShare
## •
VisitShare
## 390
StandardObjectNameShareEducation Cloud Associated Objects

CHAPTER 7Education Cloud Standard Value Set Names
and Standard Picklist Fields
This table lists the names of standard picklists as standard value sets and their corresponding field names.
Note:  The names of standard value sets and picklist fields are case-sensitive.
AcademicCredentialTypeAcademicCredentialType
AcademicCredential.Type
PersonPublicProfile.PrimaryCredentialType
AcademicCredentialType.Type
AcademicInterestSourceAcademicInterest
AcademicInterestStatus
CurrencyIsoCode
AcademicTermEnrollment.StudentAcademicLevelAcademicLevel
Learning.AcademicLevel
LearningAchievement.AcademicLevel
LearningCourse.AcademicLevel
LearningProgram.AcademicLevel
AcademicSession.SeasonAcademicSessionSeason
AcademicSession.TypeAcademicSessionType
AcademicTerm.SeasonAcademicTermSeason
ApplicationDecision.ApplicantDecisionADApplicantDecision
ApplicationDecision.ApplicationDecisionADApplicationDecision
ApplicationRenderMethod.MethodTypeApplicationRenderMethodMethodType
ApplicationRenderMethod.MethodType
ApplicationRenderMethod.UsageTypeApplicationRenderMethodUsageType
ApplicationReview.StatusApplicationReviewStatus
ApplicationSectionDefinition.TypeApplicationSectionDefinitionType
ApplicationStageDefinition.TypeApplicationStageDefinitionType
ApplicationTimeline.TypeApplicationTimelineType
ApplnStageSectionDefinition.TypeApplnStageSectionDefinitionType
ApplicationReview.ApplicationRecommendationARAppRecommendation
## 391

AcademicTermEnrollment.EnrollmentReasonATEEnrollmentReason
AcademicTermEnrollment.EnrollmentStatusATEEnrollmentStatus
AcademicTermEnrollment.StudyYearClassificationATESYearClassification
BenefitType.CategoryBenefitCategory
CourseEquivalency.FieldOfStudyCEFieldOfStudy
ConstituentRole.StatusConstituentRoleStatusType
ConstituentRole.RoleTypeConstituentRoleType
CourseOfferingParticipant.ParticipantAffiliationCOPParticipantAffiliation
CourseOfferingParticipant.ParticipationStatusCOPParticipationStatus
LearningCourse.CourseLevelDescriptionCourseLevelDescription
LabCourseType
## Lecture
## Exam
## Drill
## Recitation
CourseCreditTransferAppln.StatusCreditTransferAppStatus
LearningFoundationItem.DurationUnitDurationUnit
CourseOfferingPtcpResult.DurationUnit
LearnerProgramRqmtProgress.DurationUnit
Learning.DurationUnit
LearningCourse.DurationUnit
LearningOutcomeItem.DurationUnit
LearningProgram.DurationUnit
LearningProgramPlanRqmt.DurationUnit
EducationalInfoRequest.CategoryEduInfoRequestCategory
EducationalInfoRequest.SubCategoryEduInfoRequestSubCategory
ContactProfile.EthnicityEthnicity
CourseCreditTransferAppln.ExternalCourseDurationUnitExternalCourseDurationUnit
CourseEquivalency.ExternalCourseDurationUnit
LearningAchievement.FieldOfStudyFieldOfStudy
LearningCourse.FieldOfStudy
## 392
Education Cloud Standard Value Set Names and Standard
## Picklist Fields

GoalDefinition.CategoryGoalDefinitionCategory
ContactProfile.GraduationAchievementGraduationAchievement
ContactProfile.HighestEducationLevelHighestEducationLevel
IndividualApplicationTask.TypeIndividualApplicationTaskType
IndividualApplicationTask.StatusIndividualApplnTaskStatus
LearnerPathwayItem.SeasonLearnerPathwayItemSeason
LearnerPathwayItem.TypeLearnerPathwayItemType
LearnerPathwayItem.YearLearnerPathwayItemYear
LearnerPathway.StatusLearnerPathwayStatus
LearnerProgramRequirement.StatusLearnerProgramReqStatus
LearnerProgram.StatusLearnerProgramStatus
LearningAchievementConfig.LearningAchievementTypeLearningAchievementType
LearningFoundationItem.TypeLearningFoundationItemType
Learning.TypeLearningType
PersonLifeEvent.EventTypeLifeEventEventType
LocationUse.LocationTypeLocationType
LearnerPathwayItem.DurationUnitLPathwayItemDurationUnit
LearningPathwayTemplateItem.SeasonLPathwayTemplateItemSeason
LearningPathwayTemplateItem.TypeLPathwayTemplateItemType
LearningPathwayTemplateItem.YearLPathwayTemplateItemYear
LearningPathwayTemplate.StatusLPathwayTemplateStatus
ApplicationReview.ApplicationCategoryLPIApplnCategory
IndividualApplication.ApplicationTypeLPIApplnType
LearningPathwayTemplateItem.DurationUnitLPTItemDurationUnit
ContactProfile.MilitaryBranchMilitaryBranch
ContactProfile.MilitaryServiceMilitaryService
ApplicationTimeline.ApplicationCategoryPARApplicationCategory
CourseOfferingPtcpResult.ParticipantResultStatusParticipantResultStatus
PersonDisability.StatusPersonDisabilityStatus
PersonDisability.TypePersonDisabilityType
PersonDisability.VerifiedByPersonDisabilityVerifiedBy
## 393
Education Cloud Standard Value Set Names and Standard
## Picklist Fields

PersonPublicProfile.UsageTypePersonPublicPrflUsageType
PersonPublicProfilePrefSet.UsageType
ContactProfile.PrimaryCitizenshipTypePrimaryCitizenshipType
PersonPublicProfile.PronounsPronoun
ProviderOffering.StatusProviderOfferingStatus
ApplicationRecommender.RecommendationStatusRecommendationStatus
ContactProfile.RecurringDonorTypeRecurringDonorType
SuccessTeam.ResourceAssignmentTypeResourceAssignmentType
ContactProfile.SecondaryCitizenshipTypeSecondaryCitizenshipType
CourseEquivalency.TransferrableDurationUnitTransferrableDurationUnit
WatchlistedLearner.CategoryWatchlistedLearnerCategory
WatchlistedLearner.StatusWatchlistedLearnerStatus
WatchlistedLearner.ReasonToAddToWatchlistWLReasonToAddToWatchlist
## 394
Education Cloud Standard Value Set Names and Standard
## Picklist Fields

CHAPTER 8Education Cloud Tooling API Objects
## EDITIONS
Available in: Lightning
## Experience
in Performance, Enterprise,
## Developer,
and Unlimited editions that
have Education Cloud
enabled.
Tooling API exposes metadata used in developer tooling that you
can access through REST or SOAP. Tooling API’s SOQL capabilities
for many metadata types allow you to retrieve smaller pieces of
metadata.
For more information about Tooling API objects and to find a
complete reference of all the supported objects, see Introducing
Tooling API.
In this chapter ...
•CourseWaitlistConfig
•LearningAchievementConfig
•LocationUse
## 395

CourseWaitlistConfig
Represents the configuration for Course Waitlists. This object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
## Fields
DetailsField
## Type
string
DeveloperName
## Properties
## Create, Filter, Group, Sort, Update
## Description
The unique name for CourseWaitlistConfig.
## Type
string
MasterLabel
## Properties
## Create, Filter, Group, Sort, Update
## Description
Label for the CourseWaitlistConfig.
## Type
string
NamespacePrefix
## Properties
## Filter, Group, Nillable, Sort
## Description
The namespace prefix that is associated with this object. Each Developer Edition org that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can
refer to a component in a managed package by using the
namespacePrefix__componentName notation.
The namespace prefix can have one of the following values.
## •
In Developer Edition orgs, NamespacePrefix is set to the namespace prefix of the
org for all objects that support it, unless an object is in an installed managed package.
In that case, the object has the namespace prefix of the installed managed package. This
field’s value is the namespace prefix of the Developer Edition org of the package
developer.
## •
In orgs that are not Developer Edition orgs, NamespacePrefix is set only for objects
that are part of an installed managed package. All other objects have no namespace
prefix.
## 396
CourseWaitlistConfigEducation Cloud Tooling API Objects

DetailsField
## Type
picklist
SortOrder
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the order in which the values of the waitlist position criteria are sorted, if the type
is Waitlist Position.
Possible values are:
## •
## Ascending
## •
## Descending
## Type
picklist
## Type
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies how the course waitlist is configured according to type.
Possible values are:
## •
EnrollmentOfferExpiration—Enrollment Offer Expiration
## •
WaitlistPosition—Waitlist Position
## Type
string
## Value
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the value of a course waitlist configuration attribute based on the type.
## Type
int
WaitlistPositionFieldOrder
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the order in which fields on Course Offering Participant are evaluated to determine
a student's waitlist position, if the type is Waitlist Position.
LearningAchievementConfig
Represents the mapping details between a Learning Achievement type and a Learning Achievement record type. This object is available
in API version 59.0 and later.
## 397
LearningAchievementConfigEducation Cloud Tooling API Objects

## Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
## Fields
DetailsField
## Type
string
## Description
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The description of the Learning Achievement Configuration record.
## Type
string
DeveloperName
## Properties
## Create, Filter, Group, Sort, Update
## Description
The API name of the Learning Achievement Configuration record.
## Type
string
IconName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The icon for the Learning Achievement type that is shown on the Learning Program Builder.
## Type
picklist
## Language
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The supported language for the learning achievement configuration.
Possible values are:
## •
da—Danish
## •
de—German
## •
en_US—English
## •
es—Spanish
## •
es_MX—Spanish (Mexico)
## •
fi—Finnish
## •
fr—French
## 398
LearningAchievementConfigEducation Cloud Tooling API Objects

DetailsField
## •
it—Italian
## •
ja—Japanese
## •
ko—Korean
## •
nl_NL—Dutch
## •
no—Norwegian
## •
pt_BR—Portuguese (Brazil)
## •
ru—Russian
## •
sv—Swedish
## •
th—Thai
## •
zh_CN—Chinese (Simplified)
## •
zh_TW—Chinese (Traditional)
## Type
picklist
LearningAchievementType
## Properties
Create, Filter, Group, Restricted picklist, Sort
## Description
Specifies the type of Learning Achievement.
Possible values are:
## •
AchievementGroup—Achievement Group
## •
AchievementGroupAll—Achievement Group All
## •
## Custom
## •
LearningCourse—Learning Course
## •
LearningProgram—Learning Program
## •
Skill—Skill
## Type
reference
LearningAchvRecordTypeId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The record type that's associated with the Learning Achievement type.
This field is a relationship field.
## Relationship Name
LearningAchvRecordType
## Relationship Type
## Lookup
## Refers To
RecordType
## 399
LearningAchievementConfigEducation Cloud Tooling API Objects

DetailsField
## Type
string
MasterLabel
## Properties
## Create, Filter, Group, Sort, Update
## Description
The name of the Learning Achievement type.
## Type
string
NamespacePrefix
## Properties
## Create, Filter, Group, Sort, Update
## Description
The namespace prefix of the Learning Achievement Configuration record.
LocationUse
Records the general purpose of the Location. This object is available in API version 57.0 and later.
## Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
## Fields
DetailsField
## Type
string
DeveloperName
## Properties
## Create, Filter, Group, Sort, Update
## Description
Name of the developer of the location.
## Type
boolean
IsBookable
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates if the location is bookable.
The default value is false.
## 400
LocationUseEducation Cloud Tooling API Objects

DetailsField
## Type
picklist
## Language
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the language in use at the location.
Possible values are:
## •
da - Danish
## •
de - German
## •
en_US- English
## •
es - Spanish
## •
es_MX- Spanish(Mexico)
## •
fi - Finnish
## •
fr - French
## •
it - Italian
## •
ja - Japanese
## •
ko - Korean
## •
nl_NL- Dutch
## •
no - Norwegian
## •
pt_BR- Portuguese(Brazil)
## •
ru - Russian
## •
sv - Swedish
## •
th - Thai
## •
zh_CN- Chinese(Simplified)
## •
zh_CN- Chinese(Traditional)
## Type
picklist
LocationType
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the type of the location.
Possible values are:
## •
## Building
## •
## Campus
## •
## Other
## •
## Room
## 401
LocationUseEducation Cloud Tooling API Objects

DetailsField
## Type
string
MasterLabel
## Properties
## Create, Filter, Group, Sort, Update
## Description
The label that identifies this record throughout the user interface.
## Type
string
## Use
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Specifies what the location is used for.
## 402
LocationUseEducation Cloud Tooling API Objects

CHAPTER 9Education Cloud Business APIs
Add the provider’s contact ID to the benefit assignment record, and create Party-Role Relationship (PRR)
and Contact Contact Relationship (CCR) records if the records aren’t already present. Additionally, create
or update a learning graph, or get details of a learning graph.
In this chapter ...
•REST Reference
## Available Resources
DescriptionResource
Add the provider’s contact ID to the benefit
assignment record. Create Party-Role Relationship
/connect/education/mentoring/benefit-assignment/${benefitAssignmentId}/provider
## (POST)
(PRR) and Contact Contact Relationship (CCR)
records if the records aren’t already present.
Get details about a learning course or program,
achievements, and their associations.
/connect/education/academic-operations/learnings/recordId
## (GET)
Create a learning graph to include details of
learnings, achievements, and their associations.
## /connect/education/academic-operations/learnings
## (POST, PATCH)
Additionally, update the fields in the learning
graph.
## 403

REST Reference
You can access Education Cloud Business API by using REST endpoint. This REST API follow similar conventions as Connect REST APIs.
## Resources
Learn more about the available resources of Education Cloud Business API.
## Request Bodies
Learn more about the available request body of Education Cloud Business API.
## Response Bodies
Learn more about the available response bodies of Education Cloud Business API.
## SEE ALSO:
Connect REST API Developer Guide: Connect REST API Introduction
## Resources
Learn more about the available resources of Education Cloud Business API.
Benefit Assignment (POST)
Add the provider’s contact ID to the benefit assignment record. Create Party-Role Relationship (PRR) and Contact Contact Relationship
(CCR) records if the records aren’t already present.
Course Offering (POST)
Create course offerings and their associated course offering schedules in bulk. Use this API to create course schedules that specify
when courses are offered, helping students plan their registrations without conflicts.
Course Offering Schedules (POST)
Add or modify course offering schedules to the course offering. This resource is used to modify the schedules of an existing course
offering by adding new schedules or updating the existing schedules.
Hold Definition (POST)
Create a hold definition with hold reasons and a resolution plan.
Learning Equivalency (GET)
Retrieves a learning equivalency record along with its source and target learning mappings.
Learning Equivalency ID (GET)
Returns a single learning equivalency by its ID.
Learner Restriction Violation (GET, POST)
Retrieve and apply a new restriction (hold) to a learner by their contact ID.
Learnings Graph (POST, PATCH)
Create a learning graph to include details of learnings, achievements, and their associations. Additionally, update the fields in the
learning graph.
Learnings Graph (GET)
Get details about a learning course or program, achievements, and their associations.
## 404
REST ReferenceEducation Cloud Business APIs

Benefit Assignment (POST)
Add the provider’s contact ID to the benefit assignment record. Create Party-Role Relationship (PRR) and Contact Contact Relationship
(CCR) records if the records aren’t already present.
A PRR refers to a matching record between a mentor and a mentee depending on the benefit provided and sought after. A CCR is a
record that represents contact relationships between corresponding mentors and mentees, indicating the connection between a mentor
contact and a mentee contact.
## Resource
/connect/education/mentoring/benefit-assignment/benefitAssignmentId/provider
The benefitAssignmentId parameter is the ID of the benefit assignment record. In a mentorship benefit scenario, a benefit
assignment record represents the connection between a mentor, a mentee, and the benefit that’s provided.
## Resource Example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/mentoring/benefit-assignment/0nDSG0000000Rxt2AE/provider
Available version
## 60.0
HTTP methods
## POST
Request body for POST
JSON example
## {
"providerId":"0WqSG0000000Frt0AE"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredID of the provider offering record
associated with the benefit assignment.
StringproviderId
Response body for POST
## Mentoring Benefit Assignment
Course Offering (POST)
Create course offerings and their associated course offering schedules in bulk. Use this API to create course schedules that specify when
courses are offered, helping students plan their registrations without conflicts.
## Resource
## /connect/education/academic-operations/course-offering
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/course-offering?overwrite=false
## 405
ResourcesEducation Cloud Business APIs

Available version
## 64.0
HTTP methods
## POST
Request body for POST
JSON example
## [
## {
"courseOffering":{
"courseOfferingExternalId":{
"fieldName":"externalField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingCustomAttribute":[
## {
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## }
## ],
"courseOfferingId":"",
"courseOfferingName":"OperatingSystem",
"academicSessionId":"0vcxx00000000ODAAY",
"learningCourseId":"0vYxx00000000ODEAY",
"primaryFacultyId":"003xx000004Wj36AAC",
"startDate":"2024-12-09T20:00:00.000Z",
"endDate":"2025-12-15T20:00:00.000Z",
"isActive":"true",
"enrollmentCapacity":12,
"waitlistedCapacity":2,
"description":"CourseOfferingSummer2025OperatingSystem",
"sectionNumber":1,
"courseOfferingSchedule":[
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":"LT for OS class",
## 406
ResourcesEducation Cloud Business APIs

"courseOfferingScheduleId":""
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":" class",
"courseOfferingScheduleId":""
## }
## ]
## }
## }
## ]
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredList of course offering input to be
processed.
## Course Offering
## Input[]
courseOfferingInput
Request parameters for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
64.0RequiredCreate course offerings in bulk fashion.ObjectcourseOffering
InputRepresentation
64.0OptionalIndicates whether the external ID in the
request already exists (true) or not
## (false).
## Booleanoverwrite
Response body for POST
## Course Offering
## 407
ResourcesEducation Cloud Business APIs

Course Offering Schedules (POST)
Add or modify course offering schedules to the course offering. This resource is used to modify the schedules of an existing course
offering by adding new schedules or updating the existing schedules.
## Resource
/connect/education/academic-operations/course-offering/${courseOfferingId}/course-schedule
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/course-offering/${courseOfferingId}/course-schedule
Available version
## 64.0
HTTP methods
## POST
Request body for POST
JSON example
## {
"courseOfferingSchedule":[
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalueCRW616"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalueCRW616"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20251130T000000Z;",
"startTime":"19:00:00.000Z",
"endTime":"20:30:00.000Z",
"location":"131xx0000004FpxAAE",
"courseOfferingScheduleTemplate":"0wZxx0000000001EAA",
"startDate":"2024-12-09T20:00:00.000Z",
"type":"Lab",
"description":"ClasssessionA updated01"
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalueCRW614"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalueCRW614"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20251130T000000Z;",
"startTime":"21:00:00.000Z",
## 408
ResourcesEducation Cloud Business APIs

"endTime":"20:30:00.000Z",
"location":"111xx0000004FpxAAE",
"courseOfferingScheduleTemplate":"0wZxx0000000001EAA",
"startDate":"2024-12-09T20:00:00.000Z",
"type":"Lab",
"description":"ClasssessionA updated01"
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalueCRW615"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalueCRW615"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20251130T000000Z;",
"startTime":"22:00:00.000Z",
"endTime":"20:30:00.000Z",
"location":"131xx0000004FpxAAE",
"courseOfferingScheduleTemplate":"0qZxx0000000001EAA",
"startDate":"2024-12-09T20:00:00.000Z",
"type":"Lab",
"description":"ClasssessionA updated01"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredList of course offering schedules to be
added or modified to the course offering.
## Course Offering
## Schedule Details
## Input[]
courseOffering
## Schedule
Response body for POST
## Course Offering Schedule
Hold Definition (POST)
Create a hold definition with hold reasons and a resolution plan.
## Resource
## /connect/education/holds
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/holds
## 409
ResourcesEducation Cloud Business APIs

Available version
## 64.0
HTTP methods
## POST
Request body for POST
JSON example
## {
"name":"RestrictionName",
## "subject":"string",
"description":"Updateddescriptionfor academicprobationhold.",
"regulatoryAuthorityId":"string",
## "reasons":[
## "0x6frr566",
## "0x5674432",
## "0x6frzz566"
## ],
## "resolution":{
"actionPlanTemplateVersionId":"0x4467778"
## },
"type":"Academic",
"effectiveFrom":"2025-07-29",
"effectiveTo":"2025-07-29",
"canResolveAutomatically":true
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0OptionalIndicates whether the restriction can be
auto-resolved (true) or requires manual
resolution (false).
BooleancanResolve
## Automatically
64.0OptionalDescription of the hold.Stringdescription
64.0OptionalDate from which the hold is effective.StringeffectiveFrom
64.0OptionalDate till which the hold is effective.StringeffectiveTo
64.0OptionalName of the hold.Stringname
64.0OptionalReasons for the hold.String[]reasons
64.0RequiredUnique ID of the regulatory authority.Stringregulatory
AuthorityId
64.0RequiredUnique ID of the action plan template
associated with the resolution of this
hold.
## Action Plan
Template Input on
page 419
resolution
64.0OptionalSubject of the hold.Stringsubject
64.0OptionalType of the hold.Stringtype
## 410
ResourcesEducation Cloud Business APIs

Response body for POST
## Hold Setup
Learning Equivalency (GET)
Retrieves a learning equivalency record along with its source and target learning mappings.
## Resource
## /connect/education/academic-operations/learning-equivalency
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/learning-equivalency
Available version
## 66.0
HTTP methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
66.0OptionalIndicates if the equivalency is active.BooleanisActive
66.0RequiredThe ID of source external learning.StringsourceExternalLearningIds
Response body for GET
## Learning Equivalency Result
Learning Equivalency ID (GET)
Returns a single learning equivalency by its ID.
## Resource
/connect/education/academic-operations/learning-equivalency/learningEquivalencyId
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/learning-equivalency/1VXSG000000015l4AA
Available version
## 66.0
HTTP methods
## GET
## 411
ResourcesEducation Cloud Business APIs

Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
66.0RequiredThe ID of the learning equivalency.StringlearningEquivalencyId
Response body for GET
## Learning Equivalency Item
Learner Restriction Violation (GET, POST)
Retrieve and apply a new restriction (hold) to a learner by their contact ID.
## Resource
/connect/education/holds/assignees/${contactId}
Resource example for GET
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/holds/assignees/0x33445566778899AA
Resource example for POST
https://yourInstance.salesforce.com/services/data/v66.0connect/education/holds/assignees/0x33445566778899AA
Available version
## 64.0
HTTP methods
## GET POST
Response body for GET
## Hold Violation Result
Request body for POST
JSON example
## {
"caseStatus":"string",
"caseOrigin":"string",
"caseRecordTypeId":"string",
"dateCreated":"2025-07-25",
## "description":"string",
"complianceDueDate":"2025-07-25",
"dateResolved":"2025-07-25",
## "status":"string",
## "type":"string",
"regulatoryCodeId":"string",
## "reasons":[
## "string"
## ]
## }
## 412
ResourcesEducation Cloud Business APIs

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
65.0OptionalOrigin of the case for the contact user.StringcaseOrigin
65.0OptionalRecord Type ID of the case for the contact
user.
StringcaseRecord
TypeId
65.0OptionalStatus of the case for the contact user.StringcaseStatus
65.0OptionalDate by which compliance is expected
for the hold violation.
## Stringcompliance
DueDate
65.0OptionalDate from which the hold violation is
effective.
StringdateCreated
65.0OptionalDate on which the hold violation is
resolved.
StringdateResolved
65.0OptionalDescription of the hold violation.Stringdescription
65.0OptionalReasons for the hold violation.String[]reasons
65.0RequiredUnique ID for hold Definition.Stringregulatory
CodeId
65.0OptionalStatus of the hold violation.Stringstatus
65.0OptionalType of the hold violation.Stringtype
Response body for POST
## Hold Violation
Learnings Graph (POST, PATCH)
Create a learning graph to include details of learnings, achievements, and their associations. Additionally, update the fields in the learning
graph.
## Resource
## /connect/education/academic-operations/learnings
## Resource Example
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/learnings
Available version
## 62.0
HTTP methods
## PATCH, POST
## 413
ResourcesEducation Cloud Business APIs

Request body for PATCH
JSON example
## {
## "learnings":[
## {
## "learning":{
"learningId":"0tyLT0000000AQnYAM",
"learningCourseId":"0vYLT0000000AH72AM",
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddata
structuresand algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":6011,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:59.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## },
## "prerequisites":{
"createRecords":[
## {
"type":"SingleAchievement",
"minimumGrade":7,
## "duration":1,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004pBYAQ"
## },
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyLT00000009LcYAI",
"minimumGrade":6,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LdYAI",
"minimumGrade":7,
"type":"Learning"
## }
## ]
## }
## ],
"deleteRecords":[
## {
## 414
ResourcesEducation Cloud Business APIs

"foundationItemId":"0wwLT00000004gLYAQ"
## },
## {
"foundationItemId":"0wwLT00000004elYAA"
## }
## ]
## },
## "corequisites":{},
## "recommended":{},
## "outcomes":[]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0RequiredList of learning requests to be updated.Update Learning
## Input[]
learnings
Response body for PATCH
## Manage Learnings
Request body for POST
JSON example
## {
## "learnings":[
## {
## "learning":{
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddata
structuresand algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":601,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:59.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## },
## "prerequisites":[
## {
"type":"GroupAchievement",
## 415
ResourcesEducation Cloud Business APIs

"achievementContributors":[
## {
"id":"0tyLT00000009LOYAY",
"minimumGrade":7,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LPYAY",
"minimumGrade":6.5,
"type":"Learning"
## }
## ]
## }
## ],
## "corequisites":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tyLT00000009LQYAY"
## }
## ],
## "recommended":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tyLT00000009LRYAY"
## }
## ],
## "outcomes":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":4,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004oWYAQ"
## }
## ]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0RequiredList of learning requests to be created.Create Learning
## Input[]
learnings
## 416
ResourcesEducation Cloud Business APIs

Response body for POST
## Manage Learnings
Learnings Graph (GET)
Get details about a learning course or program, achievements, and their associations.
## Resource
/connect/education/academic-operations/learnings/learningId
Resource Example - Get learning by ID:
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/learnings/learningId
Resource Example - Get learning by course external ID:
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/learnings/{externalId}?course_external_id_field={course_custom_field}
Resource Example - Get learning by program external ID:
https://yourInstance.salesforce.com/services/data/v66.0/connect/education/academic-operations/learnings/{externalId}?program_external_id_field={program_custom_field}
Available version
## 62.0
HTTP methods
## GET
Response body for GET
## Get Learning
## Request Bodies
Learn more about the available request body of Education Cloud Business API.
## Achievement Contributor Input
Input representation of contributor for a group achievement mapping.
## Action Plan Template Input
Input representation of the action plan template for a hold.
## Course Offering Details Input
Input representation of the course offering request object.
## Course Offering Input
Input representation of the course offering request.
## Course Offering Schedule Details Input
Input representation of a single course offering schedule to create and modify within the list of course offering request.
## Course Offering Schedule Input
Input representation of the list of course offering schedules to be created or updated for the course offering.
## Custom Field Input
Input representation of custom fields for the course offering.
## 417
Request BodiesEducation Cloud Business APIs

## Create Learning Input
Input representation of the details to create learning objects, related outcomes, and foundations.
## Create Learnings Input
Input representation of the details of the request to create learnings.
Edu External ID Details Input
Input representation of external fields associated with learning object.
## Group Achievement Mapping Input
Input representation of a mapping to a given achievement that contains the shared attributes across the mapping types.
## Hold Setup Input
Input representation of the request to create a hold.
## Hold Violation Input
Input representation of the request to assign a hold to a student.
## Learning Foundation Item Lookup Input
Input representation of the lookup details for a learning foundation item.
## Learning Input
Input representation of the details that define an instructional object, which can be made available as a course, program, or an
on-site experience for a contact.
## Mentoring Benefit Assignment Input
Input representation of the request to add a provider offering’s contact ID to the benefit assignment record.
## Requirement Update Item Input
Input representation of the learning requirements, such as prerequisites, corequisites, and recommendations during the update.
## Single Achievement Mapping Input
Input representation of a mapping that’s associated with an existing learning achievement record.
## Skill Achievement Mapping Input
Input representation of a mapping that’s associated with an existing skill or must be created as a learning achievement.
## Update Learning Input
Input representation of the details of the learning along with related outcomes, and foundations for the update.
## Update Learnings Input
Input representation of the request details to update learning records.
## Achievement Contributor Input
Input representation of contributor for a group achievement mapping.
JSON example
## {
"achievementContributors":[
## {
"id":"String",
"minimumGrade":"Double",
"type":"AchievementContributorTypeEnum",
"courseExternalId":{
"fieldName":"external_course_id",
"fieldValue":"12345"
## 418
Request BodiesEducation Cloud Business APIs

## },
"programExternalId":{
"fieldName":"program_course_id",
"fieldValue":"12345"
## }
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalExternal ID of the course.Edu External ID
## Details Input
courseExternalId
62.0OptionalID that contributes to this group
achievement.
## Stringid
62.0OptionalMinimum grade required for given
achievement.
DoubleminimumGrade
62.0OptionalExternal ID of the program.Edu External ID
## Details Input
programExternalId
62.0OptionalType of contributor for given group
achievement.
## Stringtype
## Action Plan Template Input
Input representation of the action plan template for a hold.
JSON example
## {
"actionPlanTemplateVersionId":"0x44ddggg"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredUnique ID of the action plan template
version.
StringactionPlan
TemplateVersionId
## Course Offering Details Input
Input representation of the course offering request object.
## 419
Request BodiesEducation Cloud Business APIs

JSON example
## {
"courseOffering":{
"courseOfferingExternalId":{
"fieldName":"externalField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingCustomAttribute":[
## {
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## }
## ],
"courseOfferingId":"",
"courseOfferingName":"OperatingSystem",
"academicSessionId":"0vcxx00000000ODAAY",
"learningCourseId":"0vYxx00000000ODEAY",
"primaryFacultyId":"003xx000004Wj36AAC",
"startDate":"2024-12-09T20:00:00.000Z",
"endDate":"2025-12-15T20:00:00.000Z",
"isActive":"true",
"enrollmentCapacity":12,
"waitlistedCapacity":2,
"description":"CourseOfferingSummer2025OperatingSystem",
"sectionNumber":1,
"courseOfferingSchedule":[
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":"LT for OS class",
"courseOfferingScheduleId":""
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## 420
Request BodiesEducation Cloud Business APIs

## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":" class",
"courseOfferingScheduleId":""
## }
## ]
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredAcademic session for which course is
offered.
StringacademicSessionId
64.0OptionalCustom fields associated with the course
offering.
Custom Field Input[]courseOffering
CustomAttribute
64.0OptionalExternal Id details of the course offering.ObjectcourseOffering
ExternalId
64.0OptionalID of the course offering.StringcourseOffering
## Id
64.0RequiredName of the course offering.StringcourseOffering
## Name
64.0OptionalCourse offering schedules of a course
offering.
## Course Offering
## Schedule Input[]
courseOffering
## Schedule
64.0OptionalDescription of the course offering.Stringdescription
64.0OptionalEnd date of the course offering.StringendDate
64.0OptionalEnrollment capacity for the course offering.Integerenrollment
## Capacity
64.0OptionalIndicates whether the course offering is
active (true) or not (false).
BooleanisActive
64.0RequiredCourse ID for which the offering is being
made.
## Stringlearning
CourseId
## 421
Request BodiesEducation Cloud Business APIs

## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0OptionalFaculty contact ID who will be conducting
the course.
StringprimaryFacultyId
64.0OptionalSection number of the course offering.IntegersectionNumber
64.0RequiredStart date of the course offering.StringstartDate
64.0OptionalWaitlist capacity of the course offering.Integerwaitlisted
## Capacity
## Course Offering Input
Input representation of the course offering request.
JSON example
## [
## {
"courseOffering":{
"courseOfferingExternalId":{
"fieldName":"externalField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingCustomAttribute":[
## {
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## }
## ],
"courseOfferingId":"",
"courseOfferingName":"OperatingSystem",
"academicSessionId":"0vcxx00000000ODAAY",
"learningCourseId":"0vYxx00000000ODEAY",
"primaryFacultyId":"003xx000004Wj36AAC",
"startDate":"2024-12-09T20:00:00.000Z",
"endDate":"2025-12-15T20:00:00.000Z",
"isActive":"true",
"enrollmentCapacity":12,
"waitlistedCapacity":2,
"description":"CourseOfferingSummer2025OperatingSystem",
"sectionNumber":1,
"courseOfferingSchedule":[
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## 422
Request BodiesEducation Cloud Business APIs

## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":"LT for OS class",
"courseOfferingScheduleId":""
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":" class",
"courseOfferingScheduleId":""
## }
## ]
## }
## }
## ]
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredList of course offering input to be
processed.
## Course Offering
## Input[]
courseOfferingInput
## Course Offering Schedule Details Input
Input representation of a single course offering schedule to create and modify within the list of course offering request.
JSON example
## {
"courseOfferingScheduleExternalId":{
## 423
Request BodiesEducation Cloud Business APIs

"fieldName":"customField__c",
"fieldValue":"customfieldvalue"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20251130T000000Z;",
"startTime":"00:15:00.000",
"endTime":"01:15:00.000",
"location":"131xx0000004FoLAAU",
"courseOfferingScheduleTemplate":null,
"startDate":"2024-12-01",
"type":"Class",
"description":" class",
"courseOfferingScheduleId":""
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0OptionalList of custom attributes associated with
the course schedule.
## Custom Field Input
on page 426[]
courseOffering
ScheduleCustom
## Attribute
64.0OptionalExternal ID of the course schedule.ObjectcourseOffering
ScheduleExternalId
64.0Required when
editing an existing
schedule
Unique ID of the course schedule.StringcourseOffering
ScheduleId
64.0OptionalTemplate ID of the course offering
schedule.
StringcourseOffering
ScheduleTemplate
64.0OptionalDescription of the course offering
schedule.
## Stringdescription
64.0OptionalEnd time of the course offering schedule.StringendTime
64.0OptionalLocation of the course offering scheduleStringlocation
64.0OptionalRecurrence patternof the course schedule.
It uses an RRULE (Recurrence Rule) string,
## Stringrecurrence
## Pattern
which is based on a subset of the iCalendar
(RFC 5545) standard.
64.0RequiredStart date of the course offering schedule.StringstartDate
64.0RequiredStart time of the course offering schedule.StringstartTime
64.0OptionalType of the course offering schedule.Stringtype
## 424
Request BodiesEducation Cloud Business APIs

## Course Offering Schedule Input
Input representation of the list of course offering schedules to be created or updated for the course offering.
JSON example
## {
"courseOfferingSchedule":[
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalueCRW616"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalueCRW616"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20251130T000000Z;",
"startTime":"19:00:00.000Z",
"endTime":"20:30:00.000Z",
"location":"131xx0000004FpxAAE",
"courseOfferingScheduleTemplate":"0wZxx0000000001EAA",
"startDate":"2024-12-09T20:00:00.000Z",
"type":"Lab",
"description":"ClasssessionA updated01"
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalueCRW614"
## },
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalueCRW614"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20251130T000000Z;",
"startTime":"21:00:00.000Z",
"endTime":"20:30:00.000Z",
"location":"111xx0000004FpxAAE",
"courseOfferingScheduleTemplate":"0wZxx0000000001EAA",
"startDate":"2024-12-09T20:00:00.000Z",
"type":"Lab",
"description":"ClasssessionA updated01"
## },
## {
"courseOfferingScheduleExternalId":{
"fieldName":"customField__c",
"fieldValue":"customfieldvalueCRW615"
## },
"courseOfferingScheduleCustomAttribute":[
## {
## 425
Request BodiesEducation Cloud Business APIs

"fieldName":"customField1__c",
"fieldValue":"customfieldvalueCRW615"
## }
## ],
"recurrencePattern":"RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20251130T000000Z;",
"startTime":"22:00:00.000Z",
"endTime":"20:30:00.000Z",
"location":"131xx0000004FpxAAE",
"courseOfferingScheduleTemplate":"0qZxx0000000001EAA",
"startDate":"2024-12-09T20:00:00.000Z",
"type":"Lab",
"description":"ClasssessionA updated01"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredList of course offering schedules to be
added or modified to the course offering.
## Course Offering
## Schedule Details
## Input[]
courseOffering
## Schedule
## Custom Field Input
Input representation of custom fields for the course offering.
JSON example
## {
"courseOfferingScheduleCustomAttribute":[
## {
"fieldName":"customField1__c",
"fieldValue":"customfieldvalue"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0RequiredName of the custom field.StringfieldName
64.0RequiredValue of the custom field.StringfieldValue
## Create Learning Input
Input representation of the details to create learning objects, related outcomes, and foundations.
## 426
Request BodiesEducation Cloud Business APIs

JSON example
## {
## "learning":{
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddatastructures
and algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":601,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:59.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## },
## "prerequisites":[
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyLT00000009LOYAY",
"minimumGrade":7,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LPYAY",
"minimumGrade":6.5,
"type":"Learning"
## }
## ]
## }
## ],
## "corequisites":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tyLT00000009LQYAY"
## }
## ],
## "recommended":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":3,
"durationUnit":"CreditHours",
## 427
Request BodiesEducation Cloud Business APIs

"learningId":"0tyLT00000009LRYAY"
## }
## ],
## "outcomes":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":4,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004oWYAQ"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalList of the achievement mappings that are
a part of the corequisite set. This list
## Group Achievement
## Mapping Input[]
corequisites
contains co requisites that must be fulfilled
concurrently with this learning.
62.0RequiredLearning record that contains the
attributes of the course or program.
## Learning Inputlearning
62.0OptionalList of the achievement mappings that are
a part of the outcomes set. These are
## Single Achievement
## Mapping Input[]
outcomes
concrete achievements that learners are
expected to accomplish upon completion.
62.0OptionalList of the achievement mappings that are
a part of the prerequisite set. This list
## Group Achievement
## Mapping Input[]
prerequisites
contains the prerequisites that must be
met before enrolling in this learning.
62.0OptionalList of the achievement mappings that are
a part of the recommended set.
## Group Achievement
## Mapping Input[]
recommended
62.0OptionalList of the skill achievement mappings that
associate specific skills with this learning.
## Skill Achievement
## Mapping Input[]
skills
This list defines the skills that a learner is
expected to acquire or improve through
this learning.
## Create Learnings Input
Input representation of the details of the request to create learnings.
JSON example
## {
## "learnings":[
## 428
Request BodiesEducation Cloud Business APIs

## {
## "learning":{
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddata
structuresand algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":601,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:59.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## },
## "prerequisites":[
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyLT00000009LOYAY",
"minimumGrade":7,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LPYAY",
"minimumGrade":6.5,
"type":"Learning"
## }
## ]
## }
## ],
## "corequisites":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tyLT00000009LQYAY"
## }
## ],
## "recommended":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tyLT00000009LRYAY"
## }
## 429
Request BodiesEducation Cloud Business APIs

## ],
## "outcomes":[
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":4,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004oWYAQ"
## }
## ]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0RequiredList of learning requests to be created.Create Learning
## Input[]
learnings
Edu External ID Details Input
Input representation of external fields associated with learning object.
JSON example
## {
"fieldName":"external_course_id",
"fieldValue":"12345"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalField name of the external id.StringfieldName
62.0OptionalField value of the external id.StringfieldValue
## Group Achievement Mapping Input
Input representation of a mapping to a given achievement that contains the shared attributes across the mapping types.
JSON example
## {
"createRecords":[
## {
"type":"SingleAchievement",
"minimumGrade":2.5,
## "duration":4,
## 430
Request BodiesEducation Cloud Business APIs

"durationUnit":"CreditHours",
"learningId":"0tyxx00000003xyAAA"
## },
## {
"type":"SingleAchievement",
"minimumGrade":3,
## "duration":5,
"durationUnit":"CreditHours",
"learningId":"0tyxx00000003mqCAB"
## },
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyxx00000002mbAAA",
"minimumGrade":6,
"type":"Learning"
## },
## {
"id":"0tyxx00000002ppAAA",
"minimumGrade":5,
"type":"Learning"
## }
## ]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0RequiredThe type of achievement mapping.
Valid values are:
## Stringtype
## •
SingleAchievement
## •
GroupAchievement
## •
SkillAchievement
62.0OptionalContributor to an achievement within a
learning object.
## Achievement
## Contributor Input
achievementContributors
## Hold Setup Input
Input representation of the request to create a hold.
JSON example
## {
"name":"RestrictionName",
## "subject":"string",
"description":"Updateddescriptionfor academicprobationhold.",
## 431
Request BodiesEducation Cloud Business APIs

"regulatoryAuthorityId":"string",
## "reasons":[
## "0x6frr566",
## "0x5674432",
## "0x6frzz566"
## ],
## "resolution":{
"actionPlanTemplateVersionId":"0x4467778"
## },
"type":"Academic",
"effectiveFrom":"2025-07-29",
"effectiveTo":"2025-07-29",
"canResolveAutomatically":true
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
64.0OptionalIndicates whether the restriction can be
auto-resolved (true) or requires manual
resolution (false).
BooleancanResolve
## Automatically
64.0OptionalDescription of the hold.Stringdescription
64.0OptionalDate from which the hold is effective.StringeffectiveFrom
64.0OptionalDate till which the hold is effective.StringeffectiveTo
64.0OptionalName of the hold.Stringname
64.0OptionalReasons for the hold.String[]reasons
64.0RequiredUnique ID of the regulatory authority.Stringregulatory
AuthorityId
64.0RequiredUnique ID of the action plan template
associated with the resolution of this hold.
## Action Plan
Template Input on
page 419
resolution
64.0OptionalSubject of the hold.Stringsubject
64.0OptionalType of the hold.Stringtype
## Hold Violation Input
Input representation of the request to assign a hold to a student.
JSON example
## {
"caseStatus":"string",
"caseOrigin":"string",
"caseRecordTypeId":"string",
"dateCreated":"2025-07-25",
## 432
Request BodiesEducation Cloud Business APIs

## "description":"string",
"complianceDueDate":"2025-07-25",
"dateResolved":"2025-07-25",
## "status":"string",
## "type":"string",
"regulatoryCodeId":"string",
## "reasons":[
## "string"
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
65.0OptionalOrigin of the case for the contact user.StringcaseOrigin
65.0OptionalRecord Type ID of the case for the contact
user.
StringcaseRecord
TypeId
65.0OptionalStatus of the case for the contact user.StringcaseStatus
65.0OptionalDate by which compliance is expected for
the hold violation.
## Stringcompliance
DueDate
65.0OptionalDate from which the hold violation is
effective.
StringdateCreated
65.0OptionalDate on which the hold violation is
resolved.
StringdateResolved
65.0OptionalDescription of the hold violation.Stringdescription
65.0OptionalReasons for the hold violation.String[]reasons
65.0RequiredUnique ID for hold Definition.Stringregulatory
CodeId
65.0OptionalStatus of the hold violation.Stringstatus
65.0OptionalType of the hold violation.Stringtype
## Learning Foundation Item Lookup Input
Input representation of the lookup details for a learning foundation item.
JSON example
## {
"deleteRecords":[
## {
"foundationItemId":"0wwLT00000004gLYAQ"
## },
## {
"foundationItemId":"0wwLT00000004elYAA"
## 433
Request BodiesEducation Cloud Business APIs

## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalLearning course ID to be deleted. This ID
represents a prerequisite, corequisite, or
## Stringfoundation
ItemId
recommendation to be removed from the
learning record.
## Learning Input
Input representation of the details that define an instructional object, which can be made available as a course, program, or an on-site
experience for a contact.
JSON example
## {
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddata
structuresand algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":601,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:62.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalAcademic level of the learning.
Applicable for both learning program and
learning course.
StringacademicLevel
## 434
Request BodiesEducation Cloud Business APIs

## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalIndicates whether the learning is active
(true) or not (false).
Applicable for both learning program and
learning course.
## Booleanactive
62.0OptionalStart date of the learning's active period.
Applicable for both learning program and
learning course.
## Stringactive
FromDate
62.0OptionalEnd date of the learning's active period.
Applicable for both learning program and
learning course.
StringactiveToDate
62.0OptionalClassification of the instructional
programming code that identifies the
program or field of study.
Applicable for both learning program and
learning course.
StringcipCode
62.0OptionalGeneral type or level of instruction
provided by the learning course.
Applicable for learning course only.
StringcourseLevel
## Description
62.0OptionalNumeric ID of the course.
Applicable for learning course only.
StringcourseNumber
62.0OptionalDescription of the learning.
Applicable for both learning program and
learning course.
## Stringdescription
62.0OptionalAllocated duration to complete the
learning.
Applicable for both learning program and
learning course.
## Doubleduration
62.0OptionalUnit of the duration that’s allocated to
complete the learning.
Applicable for both learning program and
learning course.
StringdurationUnit
62.0OptionalField of study of the learning course.
Applicable for learning course only.
StringfieldOfStudy
## 435
Request BodiesEducation Cloud Business APIs

## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0RequiredID of the learning.
Applicable for both learning program and
learning course.
StringlearningId
62.0OptionalCustom fields on the learning course.
Applicable for learning course only.
Map<String,
## Object>
learningCourse
CustomFields
62.0OptionalID associated with the learning course.
Applicable for learning course only.
## Stringlearning
CourseId
62.0OptionalCustom fields on the learning program.
Applicable for learning program only.
Map<String,
## Object>
learningProgram
CustomFields
62.0OptionalID associated with the learning program.
Applicable for learning program only.
## Stringlearning
ProgramId
62.0OptionalName of the learning.
Applicable for both learning program and
learning course.
## Stringname
62.0OptionalAccount foreign key identifier of the
institution that provides the learning.
Applicable for both learning program and
learning course.
## Stringprovider
62.0OptionalAbbreviation for the subject of the learning
course.
Applicable for learning course only.
## Stringsubject
## Abbreviation
62.0OptionalIndicates whether the learning program is
a top-level program (true) or not
## (false).
Applicable for learning program only.
BooleantopLevel
## Program
62.0RequiredType of learning record.
Valid values are:
## Stringtype
## •
LearningProgram
## •
LearningCourse
Applicable for both learning program and
learning course.
## 436
Request BodiesEducation Cloud Business APIs

## Mentoring Benefit Assignment Input
Input representation of the request to add a provider offering’s contact ID to the benefit assignment record.
JSON example
## {
"providerId":"0WqSG0000000Frt0AE"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredID of the provider offering record
associated with the benefit assignment.
StringproviderId
## Requirement Update Item Input
Input representation of the learning requirements, such as prerequisites, corequisites, and recommendations during the update.
JSON example
## {
## "prerequisites":{
"createRecords":[
## {
"type":"SingleAchievement",
"minimumGrade":7,
## "duration":1,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004pBYAQ"
## },
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyLT00000009LcYAI",
"minimumGrade":6,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LdYAI",
"minimumGrade":7,
"type":"Learning"
## }
## ]
## }
## ],
"deleteRecords":[
## {
"foundationItemId":"0wwLT00000004gLYAQ"
## },
## {
## 437
Request BodiesEducation Cloud Business APIs

"foundationItemId":"0wwLT00000004elYAA"
## }
## ]
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalList of new prerequisites, corequisites, and
recommendations to be created.
## Group Achievement
## Mapping Input[]
createRecords
62.0OptionalList of prerequisites, corequisites, and
recommendations to be deleted.
## Learning
## Foundation Item
## Lookup Input[]
deleteRecords
## Single Achievement Mapping Input
Input representation of a mapping that’s associated with an existing learning achievement record.
JSON example
## {
"courseExternalId":{
"fieldName":"external_course_id",
"fieldValue":"12345"
## },
## "duration":4,
"durationUnit":"CreditHours",
"isPrimary":true,
"learningAchievementId":"0u9xx000000026fAAA",
"learningId":"0tyxx000000123dABC",
"learningOutcomeId":"0ttxx0000000456ABC",
"minimumGrade":3.5
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalExternal ID of the course that’s associated
with the learning achievement.
Edu External ID
## Details Input
course
ExternalId
62.0OptionalAllocated duration to complete the
learning achievement.
## Doubleduration
62.0OptionalUnit of the duration that’s allocated to
complete the learning achievement.
StringdurationUnit
62.0OptionalIndicates whether the outcome is primary
(true) or not (false).
BooleanisPrimary
## 438
Request BodiesEducation Cloud Business APIs

## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalID of the learning achievement record that
refers to an existing learning achievement.
## Stringlearning
AchievementId
62.0RequiredID of the learning course or program that
the learning achievement is associated
with.
StringlearningId
62.0OptionalID of the outcome record that’s associated
with the learning achievement.
## Stringlearning
OutcomeId
62.0OptionalMinimum grade point average required
for an achievement.
DoubleminimumGrade
## Skill Achievement Mapping Input
Input representation of a mapping that’s associated with an existing skill or must be created as a learning achievement.
JSON example
## {
"name":"AdvancedJavaProgramming",
"description":"TechnicalSkillin Java",
"learningAchievementId":"0u9SG0000001mCdYAI"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalDescription of the skill and the learning
achievement.
## Stringdescription
62.0OptionalID of the learning achievement that fulfills
this skill achievement.
## Stringlearning
AchievementId
62.0RequiredName of the skill and the learning
achievement.
## Stringname
## Update Learning Input
Input representation of the details of the learning along with related outcomes, and foundations for the update.
JSON example
## {
## "learning":{
"learningId":"0tyLT0000000AQnYAM",
"learningCourseId":"0vYLT0000000AH72AM",
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
## 439
Request BodiesEducation Cloud Business APIs

"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddatastructures
and algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":6011,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:59.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## },
## "prerequisites":{
"createRecords":[
## {
"type":"SingleAchievement",
"minimumGrade":7,
## "duration":1,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004pBYAQ"
## },
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyLT00000009LcYAI",
"minimumGrade":6,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LdYAI",
"minimumGrade":7,
"type":"Learning"
## }
## ]
## }
## ],
"deleteRecords":[
## {
"foundationItemId":"0wwLT00000004gLYAQ"
## },
## {
"foundationItemId":"0wwLT00000004elYAA"
## }
## ]
## },
## "corequisites":{},
## "recommended":{},
## "outcomes":[]
## }
## 440
Request BodiesEducation Cloud Business APIs

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0OptionalRequirement update item that’s a part of
the corequisite set.
## Requirement
## Update Item Input
corequisites
62.0RequiredLearning record to be updated.Learning Inputlearning
62.0OptionalList of achievement mappings that’s a part
of the outcome set.
## Single Achievement
## Mapping Input[]
outcomes
62.0OptionalRequirement update item that’s a part of
the prerequisite set.
## Requirement
## Update Item Input
prerequisites
62.0OptionalRequirement update item that’s a part of
the recommended set.
## Requirement
## Update Item Input
recommended
## Update Learnings Input
Input representation of the request details to update learning records.
JSON example
## {
## "learnings":[
## {
## "learning":{
"learningId":"0tyLT0000000AQnYAM",
"learningCourseId":"0vYLT0000000AH72AM",
"type":"LearningCourse",
"name":"AdvancedDataStructuresand Algorithms",
"provider":"001LT000009puL0YAI",
"description":"Thiscoursecoversadvancedconceptsin datastructuresand
algorithms,witha focuson efficientproblem-solvingand codingtechniques.",
"courseLevelDescription":"Graduate-levelcoursefocusingon advanceddata
structuresand algorithms.",
"subjectAbbreviation":"CS",
"fieldOfStudy":"ComputerScience",
"courseNumber":6011,
## "active":true,
"activeFromDate":"2024-09-01T00:00:00.00Z",
"activeToDate":"2025-12-31T23:59:59.00Z",
## "duration":4,
"durationUnit":"CreditHours",
"cipCode":"11.0101",
"academicLevel":"Graduate"
## },
## "prerequisites":{
"createRecords":[
## {
"type":"SingleAchievement",
"minimumGrade":7,
## 441
Request BodiesEducation Cloud Business APIs

## "duration":1,
"durationUnit":"CreditHours",
"learningAchievementId":"0u9LT00000004pBYAQ"
## },
## {
"type":"GroupAchievement",
"achievementContributors":[
## {
"id":"0tyLT00000009LcYAI",
"minimumGrade":6,
"type":"Learning"
## },
## {
"id":"0tyLT00000009LdYAI",
"minimumGrade":7,
"type":"Learning"
## }
## ]
## }
## ],
"deleteRecords":[
## {
"foundationItemId":"0wwLT00000004gLYAQ"
## },
## {
"foundationItemId":"0wwLT00000004elYAA"
## }
## ]
## },
## "corequisites":{},
## "recommended":{},
## "outcomes":[]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
62.0RequiredList of learning requests to be updated.Update Learning
## Input[]
learnings
## Response Bodies
Learn more about the available response bodies of Education Cloud Business API.
## Action Plan
Output representation of the action plan information related to individual hold result items.
API Error Details
Output representation of the error details.
## 442
Response BodiesEducation Cloud Business APIs

## Associated Rule
Output representation of the rule evaluated to determine whether a hold is to be applied.
## Course Offering
Output representation of the course offering.
## Course Offering Details
Output representation of each course offering submitted in a bulk request.
## Course Offering Error
Output representation of the error of the course offering schedule.
## Course Offering Schedule
Output representation of the course offering schedules to the course offering.
## Course Offering Schedule Details
Output representation that contains details about each course offering schedule. It includes the unique ID of the schedule, its success
status, and any errors encountered.
## Custom Field
Output representation of a custom field.
## Get Learning
Output representation of the details of a learning object, including its core details, prerequisites, corequisites, recommended items,
and learning outcomes.
## Hold Result Output Items
Output representation of the information related to individual hold result items.
## Hold Setup
Output representation of the response details to create a hold setup.
## Hold Violation
Output representation of the response details for a newly created hold violation.
## Hold Violation Result
Output representation of the response details to retrieve hold violation information.
## Hold Violation Result Details
Output representation of the information related to the list of hold result items.
## Learning
Output representation of the details of an instructional object, which can be made available as a course, program, or an on-site
experience for a contact.
## Learning Details
Output representation of the detailed information about a specific learning item.
## Learning Equivalency Item
Output representation of a single learning equivalency with its source and target mappings.
## Learning Equivalency Result
Output representation of the response for learning equivalency.
## Learning Foundation Item
Output representation of a foundation item associated with a learning object, such as a prerequisite, corequisite, or recommended
item.
## 443
Response BodiesEducation Cloud Business APIs

## Learning Fulfiller
Output representation of the types of fulfillment options for the learning foundation items.
## Learnings Mapping
The mappings between learnings within the group.
## Learning Outcome Item
Output representation of the details of the learning outcome item.
## Learning Status
Output representation of the details of the learner's status related to an academic course or a program.
## Manage Learning
Output representation of the result of creating a learning object. The result includes the success status, encountered errors, and IDs
of the objects created or associated with the new learning record.
## Manage Learnings
Output representation of the results of new learning objects, such as courses or programs.
## Mentoring Benefit Assignment
Output representation of the benefit assignment details along with the provider offering’s contact ID.
## Mentoring Benefit Assignment Details
Output representation of the benefit assignment record that’s updated with provider details.
## Task
Output representation of the task information related to individual hold result items.
## Action Plan
Output representation of the action plan information related to individual hold result items.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Indicates whether overrides are allowed for
the object (true) or not (false).
BooleanallowOverride
64.0Big, 64.0End date of the task or project.StringendDate
64.0Big, 64.0Unique ID for the object.Stringid
64.0Big, 64.0Name associated with the object.Stringname
64.0Big, 64.0Number of tasks that are overdue.IntegernumberOf
OverdueTasks
64.0Big, 64.0Total number of tasks associated with the
object.
IntegernumberOfTasks
64.0Big, 64.0Start date of the task or project.StringstartDate
64.0Big, 64.0Current status of the object.
Valid values are:
## Stringstatus
## •
## Active
## •
## Inactive
## 444
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Task(s) associated with the action plan.Task[]tasks
API Error Details
Output representation of the error details.
## Sample Output
## {
## "field":"name",
## "message":"success"
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Field name that has an error.Stringfield
62.0Small, 62.0Detailed message describing the error.Stringmessage
## Associated Rule
Output representation of the rule evaluated to determine whether a hold is to be applied.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
65.0Big, 65.0Description of the associated rule.Stringdescription
65.0Big, 65.0Unique ID of the expression set associated
with the rule.
StringruleExpression
SetId
65.0Big, 65.0Unique ID of the associated rule.StringruleId
65.0Big, 65.0Name of the associated rule.StringruleName
65.0Big, 65.0Current status of the rule.Stringstatus
## Course Offering
Output representation of the course offering.
JSON example
## {
"successCount":1,
"partialSuccessCount":1,
"failureCount":1,
"status":"PARTIAL_SUCCESS",
## "details":[
## 445
Response BodiesEducation Cloud Business APIs

## {
"status":"SUCCESS",
## "errors":[],
"courseOfferingId":"0xAxx0000000001EAA",
"courseSchedule":[
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001EBB",
## "errors":[]
## },
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001ECC",
## "errors":[]
## }
## ]
## },
## {
"success":"PARTIAL_SUCCESS",
"courseOfferingId":"0xAxx0000000001EDD",
## "errors":[],
"courseSchedule":[
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001EEE",
## "errors":[]
## },
## {
## "success":false,
"courseOfferingScheduleId":null,
## "errors":[
## {
"message":"Endtime< Starttimeat CourseOfferingSchedule",
"field":"courseSchedule.endTime"
## },
## {
"message":"Typeis invalid",
"field":"courseSchedule.type"
## }
## ]
## }
## ]
## },
## {
"success":"FAILURE",
"courseOfferingId":null,
## "errors":[
## {
"message":"AcademicSessionis invalid",
"field":"courseOffering.academicSessionId"
## }
## ],
"courseSchedule":[]
## }
## 446
Response BodiesEducation Cloud Business APIs

## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0List of details of each course offering and
course offering schedule.
## Course Offering[]details
64.0Big, 64.0Number of course offerings that failed to be
created.
IntegerfailureCount
64.0Big, 64.0Number of course offerings that were
partially successful.
IntegerpartialSuccess
## Count
64.0Big, 64.0Status of the entire payload request.Stringstatus
64.0Big, 64.0Number of course offerings that were
successfully created.
IntegersuccessCount
## Course Offering Details
Output representation of each course offering submitted in a bulk request.
JSON example
## {
## "details":[
## {
"status":"SUCCESS",
## "errors":[],
"courseOfferingId":"0xAxx0000000001EAA",
"courseSchedule":[
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001EBB",
## "errors":[]
## },
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001ECC",
## "errors":[]
## }
## ]
## },
## {
"success":"PARTIAL_SUCCESS",
"courseOfferingId":"0xAxx0000000001EDD",
## "errors":[],
"courseSchedule":[
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001EEE",
## "errors":[]
## 447
Response BodiesEducation Cloud Business APIs

## },
## {
## "success":false,
"courseOfferingScheduleId":null,
## "errors":[
## {
"message":"Endtime< Starttimeat CourseOfferingSchedule",
"field":"courseSchedule.endTime"
## },
## {
"message":"Typeis invalid",
"field":"courseSchedule.type"
## }
## ]
## }
## ]
## },
## {
"success":"FAILURE",
"courseOfferingId":null,
## "errors":[
## {
"message":"AcademicSessionis invalid",
"field":"courseOffering.academicSessionId"
## }
## ],
"courseSchedule":[]
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0ID of the created course offering.StringcourseOffering
## Id
64.0Big, 64.0List of details of each course offering
schedule.
## Course Offering
## Schedule[]
courseSchedules
64.0Big, 64.0List of errors encountered during the
creation of the course offering.
## Course Offering
## Error[]
errors
64.0Big, 64.0Status of entire payload request.Stringstatus
## Course Offering Error
Output representation of the error of the course offering schedule.
JSON example
## {
## "errors":[
## {
## 448
Response BodiesEducation Cloud Business APIs

"message":"Typeis invalid",
"field":"courseSchedule.type"
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Field where an error occurred.Stringfield
64.0Big, 64.0Error message in the creation or updation
of the course offering.
## Stringmessage
## Course Offering Schedule
Output representation of the course offering schedules to the course offering.
JSON example
## {
"successCount":1,
"failureCount":1,
"status":"PARTIAL_SUCCESS",
"courseSchedule":[
## {
## "success":true,
"courseOfferingScheduleId":"0xAxx0000000001EAA",
## "errors":[]
## },
## {
## "success":false,
"courseOfferingScheduleId":null,
## "errors":[
## {
"message":"Endtime< Starttimeat CourseOfferingSchedule",
"field":"courseSchedule.endTime"
## },
## {
"message":"Typeis invalid",
"field":"courseSchedule.type"
## }
## ]
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Course offering schedules of a course
offering.
## Course Offering
## Schedule Output
## Details[]
courseSchedules
## 449
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Number of schedules that failed.IntegerfailureCount
64.0Big, 64.0Status of the transaction.Stringstatus
64.0Big, 64.0Number of schedules that were added
successfully.
IntegersuccessCount
## Course Offering Schedule Details
Output representation that contains details about each course offering schedule. It includes the unique ID of the schedule, its success
status, and any errors encountered.
JSON example
## {
"courseSchedule":[
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001EBB",
## "errors":[]
## },
## {
## "success":true,
"courseOfferingScheduleId":"0eAxx0000000001ECC",
## "errors":[]
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0ID of the created or updated course offering
schedule.
StringcourseOffering
ScheduleId
64.0Big, 64.0List of errors encountered during the
creation or updation of the course offering
schedule.
## Course Offering
## Error[]
errors
64.0Big, 64.0Indicates whether the course offering
schedule was successfully created (true)
or not (false).
## Booleansuccess
## Custom Field
Output representation of a custom field.
## 450
Response BodiesEducation Cloud Business APIs

JSON example
## {
"customAttributes":[
## {
"fieldName":"Department",
"fieldValue":"Engineering"
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
65.0Big, 65.0Name of the field.StringfieldName
65.0Big, 65.0Value of the field.StringfieldValue
## Get Learning
Output representation of the details of a learning object, including its core details, prerequisites, corequisites, recommended items, and
learning outcomes.
## Sample Output
## {
## "learning":{
"learningId":"0tyxx00000002t3",
"learningCourseId":"0vYxx00000002GL",
"type":"LearningCourse",
"name":"BasicCloudComputing",
"provider":"001xx000003GehfAAC",
"activeFromDate":"2020-01-01T12:00:00.00Z",
"activeToDate":"2024-01-02T12:00:00.00Z",
## "duration":6,
"durationUnit":"CreditHours",
"cipCode":"01.0000",
"academicLevel":"Graduate",
## "active":true,
"subjectAbbreviation":"CLOUD",
"courseNumber":101,
"fieldOfStudy":"ComputerScience",
"courseLevelDescription":"BasicCloudComputingcourse",
"description":"BasicCloudComputingCourse",
"learningCourseCustomFields":{
## "custom_attr1":"value1",
## "custom_attr2":"value2"
## }
## },
## "prerequisites":[
## {
"learningFoundationItemId":"0wwxx000000004r",
"learningAchievementId":"0u9xx000000020DAAQ",
"learningAchievementType":"LearningCourse",
"minimumNumericGrade":2.5,
## 451
Response BodiesEducation Cloud Business APIs

## "duration":4,
"durationUnit":"CreditHours",
"fullfilledBy":[
## {
"learningOutcomeItem":{
## "duration":3,
"durationUnit":"",
"learningOutcomeId":"0uELT00000004nm2AA"
## },
## "learning":{
"type":"LearningCourse",
"courseLevelDescription":"",
"courseNumber":"",
## "duration":3,
"durationUnit":"",
"fieldOfStudy":"",
"learningCourseCustomFields":{},
"learningCourseId":"0vYLT00000009Bo2AI",
"learningId":"0tyLT00000009LeYAI",
"name":"OOPS",
"subjectAbbreviation":""
## }
## }
## ]
## },
## {
"learningFoundationItemId":"0wwxx000000004s",
"learningAchievementId":"0u9xx000000020DEAQ",
"learningAchievementType":"Badge",
"minimumNumericGrade":null,
## "duration":null,
"durationUnit":null,
"fullfilledBy":[
## {
"learningOutcomeItem":{
"learningOutcomeId":"0uESB00000000WI2AY",
## "duration":4,
"durationUnit":"CreditHours"
## },
## "learning":{
"type":"LearningCourse",
"learningCourseId":"0tyxx00000002ppAAA",
"name":"BasicCalculus1",
"subjectAbbreviation":"CALC",
"courseNumber":1011,
"minimumNumericGrade":3,
## "duration":3,
"durationUnit":""
## }
## }
## ]
## },
## {
"learningFoundationItemId":"0wwxx000000004t",
## 452
Response BodiesEducation Cloud Business APIs

"learningAchievementId":"0u9xx000000028HEAQ",
"learningAchievementType":"GroupAchievment",
"minimumNumericGrade":null,
## "duration":null,
"durationUnit":null,
"fullfilledBy":[
## {
"learningOutcomeItem":{
"learningOutcomeId":"0uESB00000000WI2AY",
## "duration":4,
"durationUnit":"CreditHours"
## },
## "learning":{
"type":"LearningCourse",
"learningCourseId":"0tyxx00000002ppAAA",
"name":"Surveyof Calculus1",
"subjectAbbreviation":"CALC",
"courseNumber":2233,
"minimumNumericGrade":3,
## "duration":3,
"durationUnit":""
## }
## },
## {
"learningOutcomeItem":{
"learningOutcomeId":"0uESB00000000WJ2AY",
## "duration":4,
"durationUnit":"CreditHours"
## },
## "learning":{
"type":"LearningCourse",
"learningCourseId":"0tyxx00000002pqAAA",
"name":"AnalyticGeometry& Calculus1",
"subjectAbbreviation":"AGC",
"courseNumber":501,
"minimumNumericGrade":2,
## "duration":3,
"durationUnit":""
## }
## }
## ]
## }
## ],
## "corequisites":[],
## "recommended":[],
## "outcomes":[
## {
## "category":"",
## "duration":4,
"durationUnit":"CreditHours",
"isPrimary":true,
"learningAchievementId":"0u9LT00000005anYAA",
"learningId":"0tyLT0000000AQnYAM",
"learningOutcomeId":"0uELT00000005ZB2AY",
## 453
Response BodiesEducation Cloud Business APIs

"name":"LOI-0000111"
## },
## {
## "category":"",
## "duration":4,
"durationUnit":"CreditHours",
"isPrimary":false,
"learningAchievementId":"0u9LT00000004oWYAQ",
"learningId":"0tyLT0000000AQnYAM",
"learningOutcomeId":"0uELT00000005ZC2AY",
"name":"LOI-0000112"
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0List of the corequisites that’s associated with
the learning program or course.
## Learning Foundation
## Item[]
corequisites
62.0Small, 62.0Validation errors for the API parameters.API Error Details[]errors
62.0Small, 62.0Details about the learning object.Learninglearning
62.0Small, 62.0List of the learning outcomes that’s
associated with the learning program or
course.
## Learning Outcome
## Item[]
outcomes
62.0Small, 62.0List of the prerequisites that’s associated
with the learning program or course.
## Learning Foundation
## Item[]
prerequisites
62.0Small, 62.0List of the recommended courses or skills
that’s associated with the learning program
or course.
## Learning Foundation
## Item[]
recommended
62.0Small, 62.0Indicates whether the API request is
successful (true) or not (false).
## Booleansuccess
## Hold Result Output Items
Output representation of the information related to individual hold result items.
JSON example
## [
## {
"name":"Enrollment",
## "id":"0x7fsss66",
"isRuleDriven":true,
"isExecuted":true
## },
## {
"name":"FeePayment",
## 454
Response BodiesEducation Cloud Business APIs

## "id":"0x7fsss67",
"isRuleDriven":false,
"isExecuted":false
## }
## ]
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0List of rules linked to the hold decision.Associated Rule[]associated
## Rules
64.0Big, 64.0Description or title of the hold item.Stringdescription
64.0Big, 64.0Indicates whether the hold result has been
executed (true) or not (false).
BooleanisExecuted
64.0Big, 64.0Indicates whether the hold result is driven
by rules (true) or not (false).
BooleanisRuleBased
64.0Big, 64.0Unique ID of the hold item.StringitemId
64.0Big, 64.0Name or title of the hold item.Stringname
## Hold Setup
Output representation of the response details to create a hold setup.
JSON example
## {
"regulatoryCodeId":"0x8y556ddd",
"regulatoryCodeRegClVerId":[
## "0x8y556dd3",
## "0x7725ss"
## ],
"aptAssignmentId":"0x5567777d"
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Unique ID of the action plan template
created for the hold.
StringaptAssignmentId
64.0Big, 64.0Unique ID of the Hold that was setup.StringregulatoryCodeId
64.0Big, 64.0Unique ID of the regulatory code regulation
clause version associated with the hold.
## String[]regulatory
CodeRegClVerId
## Hold Violation
Output representation of the response details for a newly created hold violation.
## 455
Response BodiesEducation Cloud Business APIs

JSON example
## {
"contactId":"string",
"caseId":"string",
"regulatoryCodeId":"string",
"regulatoryCodeViolationId":"string",
"regulatoryCodeViolRegClVerId":[
## "string"
## ],
"actionPlanId":"string",
"regulatoryCodeName":"string"
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
65.0Big, 65.0Unique ID of the action plan template
assignment ID created for the hold violation.
StringactionPlanId
65.0Big, 65.0ID of the case linked to hold violation.StringcaseId
65.0Big, 65.0Contact ID of the case linked to hold
violation.
StringcontactId
65.0Big, 65.0Unique ID of the regulatory clause version
that has been breached by a learner.
String[]regulatoryCode
ViolRegClVerId
65.0Big, 65.0ID of the hold violation that was created.StringregulatoryCode
ViolationId
## Hold Violation Result
Output representation of the response details to retrieve hold violation information.
JSON example
## {
"contactId":"string",
## "violations":[
## {
"caseId":"string",
## "description":"string",
"regulatoryCodeViolationId":"string",
"regulatoryCodeId":"string",
"regulatoryCodeName":"string",
"dateCreated":"2025-07-24T18:35:18.820Z",
"complianceDueDate":"2025-07-24T18:35:18.820Z",
"dateResolved":"2025-07-24T18:35:18.820Z",
"daysOpen":0,
## "reasons":[
## {
"name":"RegulationClauseName",
## "id":"0x6frr566",
## 456
Response BodiesEducation Cloud Business APIs

"isRuleDriven":false
## }
## ],
## "restrictions":[
## {
"name":"Enrollment",
## "id":"0x7fsss66",
"isRuleDriven":true,
"isExecuted":true
## },
## {
"name":"FeePayment",
## "id":"0x7fsss67",
"isRuleDriven":false,
"isExecuted":false
## }
## ],
## "resolution":{
## "id":"string",
## "name":"string",
"numberOfTasks":0,
"numberOfOverdueTasks":0,
## "status":"string",
"startDate":"2025-07-24T18:35:18.820Z",
"endDate":"2025-07-24T18:35:18.820Z",
"allowOverride":true,
## "tasks":[
## {
## "id":"string",
"taskParentName":"string",
"relatedTo":"string",
## "subject":"string",
## "status":"string",
## "priority":"string",
"dueDate":"2025-07-24T18:35:18.820Z",
"createdDate":"2025-07-24T18:35:18.820Z",
## "description":"string",
"completedDateTime":"2025-07-24T18:35:18.820Z"
## }
## ]
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Unique ID of the contact associated with
the hold violation.
StringcontactId
64.0Big, 64.0List of violations associated with the case
and contact.
## Hold Violation
## Result[]
violations
## 457
Response BodiesEducation Cloud Business APIs

## Hold Violation Result Details
Output representation of the information related to the list of hold result items.
JSON example
## {
## "violations":[
## {
"caseId":"string",
## "description":"string",
"regulatoryCodeViolationId":"string",
"regulatoryCodeId":"string",
"regulatoryCodeName":"string",
"dateCreated":"2025-07-24T18:35:18.820Z",
"complianceDueDate":"2025-07-24T18:35:18.820Z",
"dateResolved":"2025-07-24T18:35:18.820Z",
"daysOpen":0,
## "reasons":[
## {
"name":"RegulationClauseName",
## "id":"0x6frr566",
"isRuleDriven":false
## }
## ],
## "restrictions":[
## {
"name":"Enrollment",
## "id":"0x7fsss66",
"isRuleDriven":true,
"isExecuted":true
## },
## {
"name":"FeePayment",
## "id":"0x7fsss67",
"isRuleDriven":false,
"isExecuted":false
## }
## ],
## "resolution":{
## "id":"string",
## "name":"string",
"numberOfTasks":0,
"numberOfOverdueTasks":0,
## "status":"string",
"startDate":"2025-07-24T18:35:18.820Z",
"endDate":"2025-07-24T18:35:18.820Z",
"allowOverride":true,
## "tasks":[
## {
## "id":"string",
"taskParentName":"string",
"relatedTo":"string",
## "subject":"string",
## "status":"string",
## 458
Response BodiesEducation Cloud Business APIs

## "priority":"string",
"dueDate":"2025-07-24T18:35:18.820Z",
"createdDate":"2025-07-24T18:35:18.820Z",
## "description":"string",
"completedDateTime":"2025-07-24T18:35:18.820Z"
## }
## ]
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Unique ID of the case associated with the
hold violation.
StringcaseId
64.0Big, 64.0Date by which compliance is required to
address the violation.
## Stringcompliance
DueDate
64.0Big, 64.0Date and time when the violation record
was created.
StringdateCreated
64.0Big, 64.0Date and time when the violation was
resolved.
StringdateResolved
64.0Big, 64.0Number of days the violation remained
open before being resolved.
IntegerdaysOpen
64.0Big, 64.0Description of the violation record.Stringdescription
64.0Big, 64.0Reason for the hold result.Hold Result Output
## Items[]
reasons
64.0Big, 64.0Unique ID of the regulatory code associated
with the violation.
StringregulatoryCode
## Id
64.0Big, 64.0Name of the regulatory code associated
with the violation.
## Stringregulatory
CodeName
64.0Big, 64.0Unique ID of the violation record.StringregulatoryCode
ViolationId
64.0Big, 64.0Details about the action plan to resolve the
violation.
## Action Planresolution
64.0Big, 64.0Restriction associated with the hold result.Hold Result Output
## Items[]
restrictions
## Learning
Output representation of the details of an instructional object, which can be made available as a course, program, or an on-site experience
for a contact.
## 459
Response BodiesEducation Cloud Business APIs

## Sample Output
## {
"learningId":"0tyxx00000002t3",
"type":"LearningCourse",
"name":"BasicCloudComputing",
"provider":"001xx000003GehfAAC",
"description":"BasicCloudComputingCourse",
"activeFromDate":"2020-01-01T12:00:00.00Z",
"activeToDate":"2024-01-02T12:00:00.00Z",
## "duration":6,
"durationUnit":"CreditHours",
"cipCode":"01.0000",
"academicLevel":"Graduate",
## "active":true
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Academic level of the learning.
Valid values are:
StringacademicLevel
## •
Pre-K/Preschool
## •
## Elementary
## •
MiddleSchool
## •
HighSchool
## •
## Undergraduate
## •
## Graduate
## •
## Doctorate
## •
Post-Baccalaureate
## Certificate
## •
AdultEducation
## •
ProfessionalEducation
62.0Small, 62.0Indicates whether the learning is active
(true) or not (false).
## Booleanactive
62.0Small, 62.0Start date of the learning's active period.Stringactive
FromDate
62.0Small, 62.0End date of the learning's active period.StringactiveToDate
62.0Small, 62.0Classification of the instructional
programming code that identifies the
program or field of study.
StringcipCode
62.0Small, 62.0Description of the learning framework.Stringdescription
62.0Small, 62.0Allocated length of time for completion of
the learning.
## Doubleduration
## 460
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Unit of measurement for the length of time
for completion.
Valid values are:
StringdurationUnit
## •
CreditHours
## •
ClockHours
## •
## No Credit
## •
ContinuingEducation
## Units
## •
## Others
62.0Small, 62.0Unique ID of the learning program.StringlearningId
62.0Small, 62.0Name of the learning program.Stringname
62.0Small, 62.0Account of the institution that provides the
learning program plan.
## Stringprovider
62.0Small, 62.0Type of the academic learning.Stringtype
## Learning Details
Output representation of the detailed information about a specific learning item.
JSON example
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007RRhYAM",
"minimumLetterGrade":null,
"minimumNumericGrade":2,
"name":"ENG101",
"provider":"AllanHancockCommunityCollege",
"referencedLearningId":"1W3SG0000000N1R0AU"
## }
## ]
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Big, 66.0The length of the course.Integerduration
66.0Big, 66.0The unit of measurement for the course
duration
StringdurationUnit
66.0Big, 66.0The identifier of the parent learning record.StringlearningId
66.0Big, 66.0The letter grade required for the learning.StringminimumLetterGrade
## 461
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Big, 66.0The numeric grade required for the learning.IntegerminimumNumericGrade
66.0Big, 66.0The name of learning.Stringname
66.0Big, 66.0The provider or institution offering the
learning.
## Stringprovider
66.0Big, 66.0The identifier of the child learning record.StringreferencedLearningId
## Learning Equivalency Item
Output representation of a single learning equivalency with its source and target mappings.
JSON example
## {
"name":"EnglishTransferEquivalencyUpdated",
"customAttributes":[],
"isActive":false,
"learningEquivalencyId":"1VXSG000000015l4AA",
"learningEquivalencyType":"General",
"learningProgramIds":["0u2SG0000004bXFYAY"],
"startDate":"2026-01-01",
"endDate":"2029-12-25",
"status":"Draft",
"isPublished":false,
"category":"Internationalstudentscat",
## "source":{
"learningAchievementId":"0u9SG0000002aYrYAI",
"learningAchievementRecordType":"AchievementGroup",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007RRhYAM",
"minimumLetterGrade":null,
"minimumNumericGrade":2,
"name":"ENG101",
"description":"ENG101 Course",
"provider":"AllanHancockCommunityCollege",
"referencedLearningId":"1W3SG0000000N1R0AU"
## }
## ],
"relationship":"AND"
## },
## "target":[
## {
"learningAchievementId":"0u9SG0000002aaTYAQ",
"learningAchievementRecordType":"AchievementGroupAll",
## "learnings":[
## {
## "duration":3,
## 462
Response BodiesEducation Cloud Business APIs

"durationUnit":"CreditHours",
"learningId":"0tySG000000EWzJYAW",
"minimumLetterGrade":null,
"minimumNumericGrade":8,
"name":"ENG1002",
"description":"ENG1002Course",
"provider":"ConnectedCollege",
"referencedLearningId":"0vYSG0000006hrt2AA"
## }
## ],
"relationship":"AND"
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Big, 66.0List of custom attributes associated with the
learning equivalency.
Custom Field[]customAttributes
66.0Big, 66.0Indicates if the equivalency is active.BooleanisActive
66.0Big, 66.0ID of the learning equivalency.StringlearningEquivalencyId
66.0Big, 66.0Type of the learning equivalency.StringlearningEquivalencyType
66.0Big, 66.0List of learning program IDs associated with
this equivalency.
String[]learningProgramIds
66.0Big, 66.0The name of the learning equivalency.Stringname
66.0Big, 66.0Source learning mappings that can be
substituted by the target learnings.
## Learnings Mapping[]source
66.0Big, 66.0Target learning mappings that can
substitute the source learnings.
## Learnings Mapping[]target
## Learning Equivalency Result
Output representation of the response for learning equivalency.
JSON example
## {
## "equivalencies":[
## {
"name":"EnglishTransferEquivalency",
"customAttributes":[ ],
"isActive":true,
"learningEquivalencyId":"1VXSG000000015l4AA",
"learningEquivalencyType":"General",
"learningProgramIds":[ "0u2SG0000004bXFYAY"],
## "source":{
"learningAchievementId":"0u9SG0000002aYrYAI",
## 463
Response BodiesEducation Cloud Business APIs

## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007RRhYAM",
"minimumLetterGrade":null,
"minimumNumericGrade":2,
"name":"ENG101",
"provider":"AllanHancockCommunityCollege",
"referencedLearningId":"1W3SG0000000N1R0AU"
## }
## ],
"relationship":"AND"
## },
## "target":[
## {
"learningAchievementId":"0u9SG0000002aaTYAQ",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG000000EWzJYAW",
"minimumLetterGrade":null,
"minimumNumericGrade":8,
"name":"ENG1002",
"provider":"ConnectedCollege",
"referencedLearningId":"0vYSG0000006hrt2AA"
## }
## ],
"relationship":"AND"
## },
## {
"learningAchievementId":"0u9SG0000003nk9YAA",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007R8LYAU",
"minimumLetterGrade":null,
"minimumNumericGrade":1,
"name":"ENG1001",
## "provider":"",
"referencedLearningId":"0vYSG0000004oO12AI"
## }
## ],
"relationship":"AND"
## }
## ]
## },
## {
"customAttributes":[
## ],
"isActive":true,
## 464
Response BodiesEducation Cloud Business APIs

"learningEquivalencyId":"1VXSG00000001lh4AA",
"learningEquivalencyType":"General",
"learningProgramIds":[
## ],
"name":"EnglishEquivalency",
## "source":{
"learningAchievementId":"0u9SG0000002aYrYAI",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007RRhYAM",
"minimumLetterGrade":null,
"minimumNumericGrade":2,
"name":"ENG101",
"provider":"AllanHancockCommunityCollege",
"referencedLearningId":"1W3SG0000000N1R0AU"
## }
## ],
"relationship":"AND"
## },
## "target":[
## {
"learningAchievementId":"0u9SG0000003WEfYAM",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007R8LYAU",
"minimumLetterGrade":null,
"minimumNumericGrade":null,
"name":"ENG1001",
"provider":"UCLA",
"referencedLearningId":"0vYSG0000004oO12AI"
## },
## {
## "duration":2,
"durationUnit":"CreditHours",
"learningId":"0tySG0000006HuDYAU",
"minimumLetterGrade":null,
"minimumNumericGrade":null,
"name":"B.Sin ComputerScience",
"provider":"UCLA",
"referencedLearningId":"0u2SG0000004bXFYAY"
## }
## ],
"relationship":"AND"
## }
## ]
## }
## ]
## }
## 465
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Big, 66.0List of learning equivalencies matching the
search criteria.
## Learning Equivalency
## Item[]
equivalencies
## Learning Foundation Item
Output representation of a foundation item associated with a learning object, such as a prerequisite, corequisite, or recommended item.
## Sample Output
## {
## "corequisites":{
"learningFoundationItemId":"0wwxx000000004r",
"name":"BasicCloudComputing",
"learningId":"0tyxx00000002p5",
"learningAchievementId":"0u9xx000000020DAAQ",
"learningAchievementType":"LearningCourse",
"minimumNumericGrade":2.5,
## "duration":4,
"durationUnit":"CreditHours",
"type":"Prerequisite",
"category":"Core",
"isFulfilled":false,
"fulfilledDuration":0,
"remainingDuration":4,
"fulfilledBy":[
## {
"learningOutcome":{
"learningOutcomeId":"0uESB00000000WI2AY",
## "duration":4,
"durationUnit":"CreditHours"
## },
## "learning":{
"type":"LearningCourse",
"learningCourseId":"0tyxx00000002ppAAA",
"name":"BasicCalculus1",
"subjectAbbreviation":"CALC",
"courseNumber":1011,
"minimumGrade":3
## }
## }
## ]
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Category of the foundation item.Stringcategory
62.0Small, 62.0Duration allocated for the completion of the
learning.
## Doubleduration
## 466
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Unit of the duration.StringdurationUnit
62.0Small, 62.0List of the learning fulfillers that provides
more details about how the foundation item
can be fulfilled.
Learning Fulfiller[]fulfilledBy
62.0Small, 62.0Completed duration toward fulfilling the
learning foundation item.
## Doublefulfilled
## Duration
62.0Small, 62.0Indicates whether the learning foundation
item is fulfilled (true) or unfulfilled
## (false).
BooleanisFulfilled
62.0Small, 62.0Achievement ID of the learning object.Stringlearning
AchievementId
62.0Small, 62.0Type of achievement of the learning object.Stringlearning
AchievementType
62.0Small, 62.0ID of the learning foundation item.Stringlearning
## Foundation
ItemId
62.0Small, 62.0Learning ID associated with the learning
foundation item.
StringlearningId
62.0Small, 62.0Minimum numeric grade required to fulfill
the learning foundation item.
DoubleminimumNumeric
## Grade
62.0Small, 62.0Name of the learning foundation item.Stringname
62.0Small, 62.0Remaining duration required to fulfill the
learning foundation item.
## Doubleremaining
## Duration
62.0Small, 62.0Type of foundation.Stringtype
## Learning Fulfiller
Output representation of the types of fulfillment options for the learning foundation items.
## Sample Output
## {
"fulfilledBy":[
## {
"learningOutcome":{
"learningOutcomeId":"0uESB00000000WI2AY",
## "duration":4,
"durationUnit":"CreditHours"
## },
## "learning":{
"type":"LearningCourse",
## 467
Response BodiesEducation Cloud Business APIs

"learningCourseId":"0tyxx00000002ppAAA",
"name":"BasicCalculus1",
"subjectAbbreviation":"CALC",
"courseNumber":1011,
"minimumGrade":3
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Details about the learning course or
program that fulfills the requirement.
## Learninglearning
62.0Small, 62.0Details about the learning outcome that
fulfills the requirement.
## Learning Outcome
## Item
learning
OutcomeItem
62.0Small, 62.0Status of a learning foundation item.Learning Statuslearning
## Status
## Learnings Mapping
The mappings between learnings within the group.
JSON example
## "source":{
"learningAchievementId":"0u9SG0000002aYrYAI",
"learningAchievementRecordType":"LearningAchievement",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
"learningId":"0tySG0000007RRhYAM",
"minimumLetterGrade":null,
"minimumNumericGrade":2,
"name":"ENG101",
"provider":"AllanHancockCommunityCollege",
"referencedLearningId":"1W3SG0000000N1R0AU"
## }
## ],
"relationship":"AND"
## },
## "target":[
## {
"learningAchievementId":"0u9SG0000002aaTYAQ",
"learningAchievementRecordType":"LearningAchievement",
## "learnings":[
## {
## "duration":3,
"durationUnit":"CreditHours",
## 468
Response BodiesEducation Cloud Business APIs

"learningId":"0tySG000000EWzJYAW",
"minimumLetterGrade":null,
"minimumNumericGrade":8,
"name":"ENG1002",
"provider":"ConnectedCollege",
"referencedLearningId":"0vYSG0000006hrt2AA"
## }
## ],
"relationship":"AND"
## },
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Big, 66.0The ID of the learning achievement.StringlearningAchievementId
66.0Big, 66.0List of learning items within this mapping
group.
## Learning Details[]learnings
66.0Big, 66.0AND or OR relationship between learnings.Stringrelationship
## Learning Outcome Item
Output representation of the details of the learning outcome item.
## Sample Output
## [
## {
"learningOutcome":{
"learningOutcomeId":"0uESB00000000WI2AY",
## "duration":4,
"durationUnit":"CreditHours"
## },
## "learning":{
"type":"LearningCourse",
"learningCourseId":"0tyxx00000002ppAAA",
"name":"Surveyof Calculus1",
"subjectAbbreviation":"CALC",
"courseNumber":2233,
"minimumGrade":3
## }
## },
## {
"learningOutcome":{
"learningOutcomeId":"0uESB00000000WJ2AY"
## },
## "learning":{
"type":"LearningCourse",
"learningCourseId":"0tyxx00000002pqAAA",
"name":"AnalyticGeometry& Calculus1",
"subjectAbbreviation":"AGC",
## 469
Response BodiesEducation Cloud Business APIs

"courseNumber":501,
"minimumGrade":2
## }
## }
## ]
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Category associated with the learning
outcome item.
## Stringcategory
62.0Small, 62.0Allocated length of time for completion of
the learning.
## Doubleduration
62.0Small, 62.0Unit of measurement for the length of time
for completion.
Valid values are:
StringdurationUnit
## •
CreditHours
## •
ClockHours
## •
## No Credit
## •
ContinuingEducation
## Units
## •
## Others
62.0Small, 62.0Indicates whether the learning outcome
item is primary (true) or not (false).
BooleanisPrimary
62.0Small, 62.0ID associated with the learning
achievement.
## Stringlearning
AchievementId
62.0Small, 62.0Unique ID of the learning program.StringlearningId
62.0Small, 62.0Unique ID of the learning outcome.Stringlearning
OutcomeId
62.0Small, 62.0Minimum numeric grade required to
achieve the learning outcome.
## Doubleminimum
NumericGrade
62.0Small, 62.0Name of the learning outcome.Stringname
## Learning Status
Output representation of the details of the learner's status related to an academic course or a program.
## Sample Output
## {
"academicSeason":"Fall",
"academicTermEnrollmentId":"0atxx000000001aAAA",
"academicTermId":"0atxx000000001bBBB",
"academicYear":"2023-2024",
## 470
Response BodiesEducation Cloud Business APIs

"durationUnit":"CreditHours",
"learningId":"0tyxx00000002t3AAA",
"letterGrade":"A",
"numericGrade":95.5,
"resultStatus":"Pass",
"status":"Completed",
"unitsEarned":3.0
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Season in which this learning is taken or will
be taken.
StringacademicSeason
62.0Small, 62.0ID for academic term enrollment.StringacademicTerm
EnrollmentId
62.0Small, 62.0ID for the academic term.Stringacademic
TermId
62.0Small, 62.0Year in which this learning is taken or will
be taken.
StringacademicYear
62.0Small, 62.0Unit of measurement for completion of the
course.
StringdurationUnit
62.0Small, 62.0Unique ID of the learning course or program.StringlearningId
62.0Small, 62.0Letter grade awarded to the learner for
completing the course.
StringletterGrade
62.0Small, 62.0Numeric grade awarded to the learner for
completing the course.
DoublenumericGrade
62.0Small, 62.0Type or status of the learner's result.
Valid values are:
StringresultStatus
## •
## Pass
## •
## Fail
62.0Small, 62.0Status of the learning.
Valid values are:
## Stringstatus
## •
## Completed
## •
## Enrolled
## •
## Planned
## •
## Unplanned
62.0Small, 62.0Units of value awarded for completing the
course.
DoubleunitsEarned
## 471
Response BodiesEducation Cloud Business APIs

## Manage Learning
Output representation of the result of creating a learning object. The result includes the success status, encountered errors, and IDs of
the objects created or associated with the new learning record.
## Sample Output
## {
## "details":{
## "success":"boolean",
"learningId":"string",
"learningCourseId":"string",
"learningAchievementIds":[
## "string"
## ],
"learningFoundationItemIds":[
## "string"
## ],
"learningOutcomeItemIds":[
## "string"
## ],
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ]
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Details of the processing errors.API Error Details[]errors
62.0Small, 62.0Learning achievement IDs created or
updated with the learning.
## String[]learning
AchievementIds
62.0Small, 62.0Learning course IDs created or updated with
the learning.
## Stringlearning
CourseId
62.0Small, 62.0Learning foundation IDs created or updated
with the learning.
## String[]learning
FoundationItem
## Ids
62.0Small, 62.0Learning IDs created or updated with the
learning.
StringlearningId
62.0Small, 62.0Learning outcome IDs created or updated
with the learning.
## String[]learning
OutcomeItem
## Ids
62.0Small, 62.0Learning program IDs created or updated
with the learning.
## Stringlearning
ProgramId
## 472
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Indicates whether the learning creation is
successful (true) or not (false).
## Booleansuccess
## Manage Learnings
Output representation of the results of new learning objects, such as courses or programs.
## Sample Output
## {
"successeCount":"integer",
"failureCount":"integer",
## "status":"string",
## "details":[
## {
## "success":"boolean",
"learningId":"string",
"learningCourseId":"string",
"learningAchievementIds":[
## "string"
## ],
"learningFoundationItemIds":[
## "string"
## ],
"learningOutcomeItemIds":[
## "string"
## ],
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ]
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Details of the learning response.Manage Learning[]details
62.0Small, 62.0Number of transactions that failed to be
created.
IntegerfailureCount
62.0Small, 62.0Status of a bulk transaction.Stringstatus
62.0Small, 62.0Number of transactions that were created.IntegersuccessCount
## 473
Response BodiesEducation Cloud Business APIs

## Mentoring Benefit Assignment
Output representation of the benefit assignment details along with the provider offering’s contact ID.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Benefit assignment record that contains
provider details.
## Mentoring Benefit
## Assignment Details
mentoring
## Benefit
## Assignment
## Mentoring Benefit Assignment Details
Output representation of the benefit assignment record that’s updated with provider details.
JSON example
This JSON example shows the updated providerId details.
## {
"mentoringBenefitAssignment":{
"benefitId":"0jixx0000000001AAA",
"createdById":"005xx000001X7rlAAC",
"createdDate":"2023-10-31T04:34:46.000+0000",
"endDateTime":"2023-11-11T20:00:00.000+0000",
"enrolleeId":"003xx000004WhHQAA0",
"enrollmentCount":"1",
"entitlementAmount":"1.00",
"id":"0nDxx0000000001EAA",
"lastModifiedById":"005xx000001X7rlAAC",
"lastModifiedDate":"2023-11-01T00:38:55.000+0000",
"maximumBenefitAmount":"1.00",
"minimumBenefitAmount":"1.00",
"name":"BA-000000001",
"parentRecordId":"11Xxx0000004GfjEAE",
"priority":"High",
"programEnrollmentId":"11Xxx0000004GfjEAE",
"providerId":"003xx000004WhJ2AAK",
"startDateTime":"2023-10-30T19:00:00.000+0000",
"status":"Enrolled",
"taskJobStatus":"NA",
"taskJobStatusMessage":"NA",
"unitOfMeasureId":"0hExx0000000001EAA"
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0ID of the benefit associated with the benefit
assignment.
StringbenefitId
60.0Small, 60.0ID of the user who created the benefit
assignment.
StringcreatedById
## 474
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Date when the benefit assignment record
was created.
StringcreatedDate
60.0Small, 60.0Date and time until when the assignment
is valid.
StringendDateTime
60.0Small, 60.0ID of the participant who enrolls for the
benefit assignment.
StringenrolleeId
60.0Small, 60.0Number of times that the benefit is
applicable to an individual.
## Stringenrollment
## Count
60.0Small, 60.0Amount that a participant is entitled to
receive from the assignment.
## Stringentitlement
## Amount
60.0Small, 60.0ID of the benefit assignment record.Stringid
60.0Small, 60.0ID of the user who updated the benefit
assignment record.
StringlastModified
ById
60.0Small, 60.0Date when the benefit assignment record
was last modified.
StringlastModified
## Date
60.0Small, 60.0Maximum amount that’s disbursed during
an assignment period.
## Stringmaximum
BenefitAmount
60.0Small, 60.0Minimum amount that’s disbursed during
an assignment period.
## Stringminimum
BenefitAmount
60.0Small, 60.0Name of the benefit assignment.Stringname
60.0Small, 60.0ID of the parent record that’s associated with
the benefit assignment.
## Stringparent
RecordId
60.0Small, 60.0Priority of the benefit assignment record.Stringpriority
60.0Small, 60.0ID of the enrollment program record created
for the participant that this benefit is
assigned to.
## Stringprogram
EnrollmentId
60.0Small, 60.0ID of the contact who provides the benefit
that’s associated with the benefit
assignment.
StringproviderId
60.0Small, 60.0Date and time when the benefit assignment
was first available.
StringstartDateTime
60.0Small, 60.0Status of the benefit assignment.Stringstatus
60.0Small, 60.0Status of the task that’s associated with the
benefit assignment.
StringtaskJobStatus
60.0Small, 60.0Status message of the task that’s associated
with the benefit assignment.
StringtaskJob
StatusMessage
## 475
Response BodiesEducation Cloud Business APIs

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0ID of the unit of measure that’s associated
with the benefit assignment.
StringunitOf
MeasureId
## Task
Output representation of the task information related to individual hold result items.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Big, 64.0Date and time when the task was
completed
## Stringcompleted
DateTime
64.0Big, 64.0Date when the task was created.StringcreatedDate
64.0Big, 64.0Detailed description of the task.Stringdescription
64.0Big, 64.0Date and time by which the task is be
completed.
StringdueDate
64.0Big, 64.0Unique ID of the object.Stringid
64.0Big, 64.0Priority level of the task.
Valid values are:
## Stringpriority
## •
## High
## •
## Medium
## •
## Low
64.0Big, 64.0Entity or object that this task is related to.StringrelatedTo
64.0Big, 64.0Current status of the task.
Valid values are:
## Stringstatus
## •
## Pending
## •
## Completed
64.0Big, 64.0Subject or title of the task.Stringsubject
64.0Big, 64.0Name of the parent task associated with this
object.
StringtaskParent
## Name
## 476
Response BodiesEducation Cloud Business APIs

CHAPTER 10Fundraising
## EDITIONS
Available in: Lightning
## Experience
Available in: Enterprise
Unlimited and Developer
## Editions.
This guide provides information about the objects and APIs that
Fundraising uses.
In this chapter ...
•Fundraising Standard
## Objects
•Fundraising Fields on
## Other Objects
•Fundraising Business
APIs
•Fundraising
## Invocable Actions
•Fundraising
Metadata API Types
•Fundraising Tooling
API Objects
## 477

## Fundraising Standard Objects
## EDITIONS
Available in: Lightning
## Experience
Available in: Enterprise,
Unlimited, and Developer
## Editions.
Fundraising data model provides objects and fields to manage gifts and donors for your nonprofit
or education organization.
DocGenerationQueryResult
Represents information, including a report, template, and process lookup, for a document
generation job. This object is available in API version 61.0 and later.
DonorGiftConcept
The initial idea or proposal for a gift, including the donor’s intent and preliminary purpose.  This
object is available in API version 64.0 and later.
DonorGiftConceptOpportunity
The junction between a Donor Gift Concept and an Opportunity. This object is available in API version 66.0 and later.
DonorGiftSummary
Represents gift summaries for accounts and contacts. This object is available in API version 59.0 and later.
GiftActuarialEntry
Represents the foundational data for calculating the future value of a planned gift, including life expectancy and discount rates. This
object is available in API version 65.0 and later.
GiftStewardship
Represents stewardship of a gift by a contact or an organization that isn't a donor. This object is available in API version 65.0 and
later.
GiftStewardshipActivity
Represents an activity carried out as part of gift stewardship. This object is available in API version 65.0 and later.
GiftAgreement
The agreement to accept a gift. This object is available in API version 64.0 and later.
GiftBatch
Represents the details and status of the batch of gifts. This object is available in API version 59.0 and later.
GiftCommitment
Represents the commitment made by a donor. This object is available in API version 59.0 and later.
GiftCmtChangeAttrLog
Represents the history of changes to a Gift Commitment over time with attribution to the source campaign or source code attributed
to that change. This object is available in API version 60.0 and later.
GiftCommitmentSchedule
Represents the schedule for fulfilling the commitment. This object is available in API version 59.0 and later.
GiftDefaultDesignation
Represents the default designation for gifts that originate from an opportunity, campaign, or commitment. This object is available
in API version 59.0 and later.
GiftDefaultSoftCredit
Represents the default allocation for soft credits on gift commitment transactions that are created by a recurrence engine and
credited to constituents who influenced the commitment. This object is available in API version 62.0 and later.
GiftDesignation
Represents a designation that can be assigned to a gift transaction. This object is available in API version 59.0 and later.
## 478
Fundraising Standard ObjectsFundraising

GiftEntry
Represents gifts created individually or in a batch before they're processed and logged in their target records. After processing, these
records serve as an audit trail for gift transactions. This object is available in API version 59.0 and later.
GiftRefund
Represents a refund of a gift. This object is available in API version 59.0 and later.
GiftSoftCredit
Represents the soft credit attributed to a person or organization for the gift transaction. This object is available in API version 59.0
and later.
GiftTransaction
Represents a completed transaction from a gift. This object is available in API version 59.0 and later.
GiftTransactionDesignation
Represents a junction between a gift transaction and a gift designation. This object is available in API version 59.0 and later.
GiftTribute
Represents the details and status of the gift tribute. This object is available in API version 59.0 and later.
GiftValueForecast
The past, current, and projected monetary value of a gift. This object is available in API version 64.0 and later.
OutreachSourceCode
Represents information about a source code that's associated with an outreach campaign. This object is available in API version 59.0
and later.
OutreachSummary
Represents a summary of results of the outreach campaign. This object is available in API version 59.0 and later.
PartyCategory
The criteria for categorizing contacts and accounts based on specific classification information for a specified time period. This object
is available in API version 64.0 and later.
PartyPhilanthropicAssessment
Represents a formalized assessment of wealth when a rating takes place, such as a third-party wealth assessment, a property valuation,
a financial asset assessment, or an internal assessment. This object is available in API version 63.0 and later.
PartyPhilanthropicIndicator
Represents an unconfirmed or soft indication that highlights a person's wealth or growth potential. This object is available in API
version 63.0 and later.
PartyPhilanthropicMilestone
Represents philanthropic activities and financial status for a period of time. This object is available in API version 63.0 and later.
PartyPhilanthropicOccurrence
xxx This object is available in API version XX.0 and later.
PartyPhilanthropicRsrchPrfl
Captures information associated with a contact or an organization in a many-to-one relationship. Serves as a pivot point for research
on the person or organization. This object is available in API version 64.0 and later.
PaymentInstrument
Represents the details related to the Payment Instrument used to complete the transaction. This object is available in API version
60.0 and later.
PlannedGift
A complex gift such as an annuity, bequest, or trust. This object is available in API version 64.0 and later.
## 479
Fundraising Standard ObjectsFundraising

PlannedGiftAnnuityRate
The rate used to calculate payments for a charitable gift annuity. This object is available in API version 64.0 and later.
PlannedGiftPerformance
The performance of a planned gift over time, including returns, expenses, and net value. This object is available in API version 64.0
and later.
DocGenerationQueryResult
Represents information, including a report, template, and process lookup, for a document generation job. This object is available in API
version 61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the FundraisingAccess license is enabled and the DocGen User permission set and the Fundraising User
system permission are assigned to users.
## Fields
DetailsField
## Type
reference
DocumentGenerationProcessId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The process associated with the document creation.
This field is a relationship field.
## Relationship Name
DocumentGenerationProcess
## Relationship Type
## Lookup
## Refers To
DocumentGenerationProcess
## Type
reference
DocumentTemplateId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 480
DocGenerationQueryResultFundraising

DetailsField
## Description
The template associated with the document creation.
This field is a relationship field.
## Relationship Name
DocumentTemplate
## Relationship Type
## Lookup
## Refers To
DocumentTemplate
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the batch query job.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ReportFolderId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The report folder associated with the document generation query result.
This is a relationship field and is available from API version 62.0 and later.
## Relationship Name
ReportFolder
## 481
DocGenerationQueryResultFundraising

DetailsField
## Refers To
## Folder
## Type
dateTime
RunDateTime
## Properties
Create, Defaulted on create, Filter, Sort, Update
## Description
The date and time when the query and job was run.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
DocGenerationQueryResultChangeEvent
Change events are available for the object.
DocGenerationQueryResultFeed
Feed tracking is available for the object.
DocGenerationQueryResultHistory
History is available for tracked fields of the object.
DocGenerationQueryResultOwnerSharingRule
Sharing rules are available for the object.
DocGenerationQueryResultShare
Sharing is available for the object.
DonorGiftConcept
The initial idea or proposal for a gift, including the donor’s intent and preliminary purpose.  This object is available in API version 64.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## 482
DonorGiftConceptFundraising

## Fields
DetailsField
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The case associated with the gift concept record.
This field is a relationship field.
## Relationship Name
## Case
## Refers To
## Case
## Type
double
ConceptPriority
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The level of a proposed gift's importance to the donor or institution relative to other proposed
gifts.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
A contact for the gift concept.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
A description of the gift concept.
## 483
DonorGiftConceptFundraising

DetailsField
## Type
percent
DonorCommitmentLikelihood
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
An estimate of the likelihood the donor commits to the gift concept.
## Type
reference
DonorId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The donor associated with the gift concept.
This field is a relationship field.
## Relationship Name
## Donor
## Refers To
## Account
## Type
double
DonorPriorityRank
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The donor's rank of a gift concept among other potential gifts the donor is considering.
## Type
currency
EstimatedGiftValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
An estimate of a proposed gift's potential value, based on preliminary discussions with the
donor.
## Type
date
ExpectedEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
## 484
DonorGiftConceptFundraising

DetailsField
## Type
date
ExpectedStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The expected end date for formalizing the gift concept.
## Type
reference
GiftAgreementId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
A gift agreement record associated with the gift concept, used to track its progression from
concept to commitment.
This field is a relationship field.
## Relationship Name
GiftAgreement
## Refers To
GiftAgreement
## Type
double
InstitutionPriorityRank
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Your institution's rank of a gift concept's importance to its fundraising strategy.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## 485
DonorGiftConceptFundraising

DetailsField
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift concept record.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Opportunity records associated with the gift concept, used to track its progression from
concept to commitment.
This field is a relationship field.
## Relationship Name
## Opportunity
## Refers To
## Opportunity
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
double
SequenceNumber
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A gift concept's position in a sequence of proposals for the donor.
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 486
DonorGiftConceptFundraising

DetailsField
## Description
The status of the gift concept.
Possible values are:
## •
ConceptApproved
## •
## In Discussion
## •
## In Review
## •
PendingApproval
## •
## Planning
## Type
string
## Title
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The title of the gift concept.
## Type
picklist
## Type
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of the gift concept.
Possible values are:
## •
CapitalCampaignConcept
## •
## In Development
## •
MajorGiftConcept
## •
OtherGiftConcept
## •
PlannedGiftConcept
## •
Programand SupportGiftConcept
## •
SpecializedGiftConcept
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
DonorGiftConceptChangeEvent
Change events are available for the object.
DonorGiftConceptFeed
Feed tracking is available for the object.
## 487
DonorGiftConceptFundraising

DonorGiftConceptHistory
History is available for tracked fields of the object.
DonorGiftConceptOwnerSharingRule
Sharing rules are available for the object.
DonorGiftConceptShare
Sharing is available for the object.
DonorGiftConceptOpportunity
The junction between a Donor Gift Concept and an Opportunity. This object is available in API version 66.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
DonorGiftConceptId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The donor gift concept associated with this donor gift concept opportunity.
This field is a relationship field.
## Relationship Name
DonorGiftConcept
## Relationship Type
## Master-detail
## Refers To
DonorGiftConcept (the master object)
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## 488
DonorGiftConceptOpportunityFundraising

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view indirectly.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the donor gift concept opportunity.
## Type
currency
OpportunityAmount
## Properties
## Filter, Nillable, Sort
## Description
The estimated total gift amount of the associated opportunity. Read-only field that is derived
from the opportunity amount.
## Type
date
OpportunityCloseDate
## Properties
## Filter, Group, Nillable, Sort
## Description
The date when the associated opportunity is expected to close. Read-only field that is derived
from the opportunity close date.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The opportunity associated with the donor gift concept.
This field is a relationship field and unique within your organization.
## Relationship Name
## Opportunity
## Refers To
## Opportunity
## 489
DonorGiftConceptOpportunityFundraising

DetailsField
## Type
picklist
OpportunityStageName
## Properties
## Filter, Group, Nillable, Sort
## Description
The stage of the associated opportunity. Read-only field that is derived from the opportunity
stage name.
Possible values are:
## •
ClosedLost
## •
ClosedWon
## •
Id. DecisionMakers
## •
NeedsAnalysis
## •
Negotiation/Review
## •
PerceptionAnalysis
## •
Proposal/PriceQuote
## •
## Prospecting
## •
## Qualification
## •
ValueProposition
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
DonorGiftConceptOpportunityChangeEvent
Change events are available for the object.
DonorGiftConceptOpportunityFeed
Feed tracking is available for the object.
DonorGiftConceptOpportunityHistory
History is available for tracked fields of the object.
DonorGiftSummary
Represents gift summaries for accounts and contacts. This object is available in API version 59.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), undelete(), update(), upsert()
## 490
DonorGiftSummaryFundraising

## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
currency
AverageGiftAmount
## Properties
## Filter, Sort
## Description
The average value of the gifts the donor directly contributed.
This value of this field is calculated using a formula: (TotalGiftTransactionAmount
/ GiftCount).
## Type
string
BestGiftYear
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The year in which the donor gave the largest value of gifts. Data Processing Engine finds the
year in which the donor gave the largest sum of paid gift transaction amounts. You can
schedule this calculation to run on a regular basis.
## Type
currency
BookedPledges
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of a donor's pledges that are fully accounted for. Data Processing Engine
calculates this value by adding the amounts of the donor's pledges with
FormalCommitmentType= Written. You can schedule this calculation to run on
a regular basis.
Available in API version 62.0 and later.
## Type
int
CompositeRfmScore
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 491
DonorGiftSummaryFundraising

DetailsField
## Description
The score that represents the composite threshold of gift recency, gift frequency, and gift
monetary value. Data Processing Engine calculates this value according to how you configure
RFM Scoring. You can schedule this calculation to run on a regular basis.
Available in API version 61.0 and later.
## Type
date
CurrentRecurringStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the donor's first recurring gift transaction for their active recurring gift. Data
Processing Engine finds the date of the donor's first paid transaction associated with a related
recurring gift commitment that isn't closed. You can schedule this calculation to run on a
regular basis.
## Type
int
CurrentYearGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of gifts that the donor directly contributed this year. Data Processing Engine
calculates this value by counting the paid gift transactions this calendar year. You can schedule
this calculation to run on a regular basis.
## Type
int
CurrentYearSoftCreditCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The total number of gift soft credit records attributed to the donor this year.
Available in API version 63.0 and later.
## Type
currency
CurrentYearSoftCreditsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of gift soft credits earned by the donor this year.
Available in API version 63.0 and later.
## 492
DonorGiftSummaryFundraising

DetailsField
## Type
int
DaysSinceLastGift
## Properties
## Filter, Group, Nillable, Sort
## Description
The number of days since the donor gave a direct contribution.
This value of this field is calculated using a formula:
IF(ISBLANK(TEXT(LastGiftDate)),NULL,TODAY()-
LastGiftDate).
## Type
reference
DonorId
## Properties
## Create, Filter, Group, Sort
## Description
The person, household, or organization account associated with the donor gift summary.
This field is a relationship field.
## Relationship Name
## Donor
## Relationship Type
Master-Detail
## Refers To
## Account
## Type
currency
FirstGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the first gift the donor directly contributed. Data Processing Engine calculates
this value by finding the amount of the donor's first paid gift transaction. You can schedule
this calculation to run on a regular basis.
## Type
reference
FirstGiftCampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The first campaign to which the donor contributed. Data Processing Engine calculates this
value by finding the campaign of the donor's first paid gift transaction related to a campaign.
You can schedule this calculation to run on a regular basis.
## 493
DonorGiftSummaryFundraising

DetailsField
This field is a relationship field.
## Relationship Name
FirstGiftCampaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
date
FirstGiftDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the donor's first direct contribution. Data Processing Engine calculates this value
by finding the date of the donor's first paid gift transaction. You can schedule this calculation
to run on a regular basis.
## Type
date
FirstRecurringStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the donor's first recurring gift transaction. Data Processing Engine calculates this
value by finding the date of the donor's first paid gift transaction related to a recurring gift
commitment. You can schedule this calculation to run on a regular basis.
## Type
currency
FirstSoftCreditAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the first gift the donor influenced but didn't directly contribute. Data Processing
Engine calculates this value by finding the soft credit amount of the first paid gift transaction
for which the donor receives soft credit. You can schedule this calculation to run on a regular
basis.
## Type
date
FirstSoftCreditDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 494
DonorGiftSummaryFundraising

DetailsField
## Description
The date of the first gift the donor influenced but didn't directly contribute. Data Processing
Engine calculates this value by finding the date of the first paid gift transaction for which the
donor receives soft credit. You can schedule this calculation to run on a regular basis.
## Type
date
FirstVolunJobPstnAsgntDt
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the contact's first volunteer shift. Data Processing Engine finds the first job position
assignment that's related to a volunteer initiative and calculates the value. You can schedule
this calculation to run regularly.
## Type
int
FrequencyScore
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The score that represents the giving frequency of the donor. Data Processing Engine calculates
this value according to how you configure RFM Scoring. You can schedule this calculation
to run on a regular basis.
Available in API version 61.0 and later.
## Type
int
GiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The total number of gifts the donor directly contributed. Data Processing Engine calculates
this value by counting all of the donor's paid gift transactions. You can schedule this
calculation to run on a regular basis.
## Type
currency
GiftsLastYearAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of gifts that the donor directly contributed last year. Data Processing Engine
calculates this value by adding the amounts of paid gift transactions from the last calendar
year. You can schedule this calculation to run on a regular basis.
## 495
DonorGiftSummaryFundraising

DetailsField
## Type
currency
GiftsThisYearAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of gifts that the donor directly contributed this year. Data Processing Engine
calculates this value by adding the amounts of the donor's paid gift transactions from this
calendar year. You can schedule this calculation to run on a regular basis.
## Type
currency
GiftsTwoYearsAgoAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of gifts the donor directly contributed two years ago. Data Processing Engine
calculates this value by adding the amounts of the donor's paid gift transactions from two
calendar years ago. You can schedule this calculation to run on a regular basis.
## Type
picklist
GivingLevel
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The range within which the donor's total contributions fall for the current year.
Possible values are:
## •
## $25,000,000+
## •
## $10,000,000-$24,999,999
## •
## $5,000,000-$9,999,999
## •
## $1,000,000-$4,999,999
## •
## $250,000-$999,999
## •
## $100,000-$249,999
## •
## $50,000-$99,999
## •
## $25,000-$49,999
## •
## $10,000-$24,999
## •
## $5,000-$9,999
## •
## $2,500-$4,999
## •
## $1,000-$2,499
## •
## $500-$999
## •
## $100-$499
## •
## Under$100
## 496
DonorGiftSummaryFundraising

DetailsField
## Type
currency
HighestGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The largest single gift that the donor directly contributed. Data Processing Engine calculates
this value by finding the amount of the donor's largest paid gift transaction. You can schedule
this calculation to run on a regular basis.
## Type
currency
HighestGiftYearAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount the donor gave in the year they directly contributed the largest value. Data
Processing Engine calculates this value by finding the total amount of all paid gift transactions
in the year when the donor gave the largest amount. You can schedule this calculation to
run on a regular basis.
## Type
currency
HighestSoftCreditAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the largest single gift the donor influenced but didn't directly contribute. Data
Processing Engine calculates this value by finding the largest gift transaction for which the
donor receives soft credit. You can schedule this calculation to run on a regular basis.
## Type
date
HighestSoftCreditDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the largest single gift the donor influenced but didn't directly contribute. Data
Processing Engine calculates this value by finding the date of the largest gift transaction for
which the donor receives soft credit. You can schedule this calculation to run on a regular
basis.
## Type
currency
LastGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## 497
DonorGiftSummaryFundraising

DetailsField
## Description
The value of the donor's most recent directly contributed gift. Data Processing Engine
calculates this value by finding the amount of the donor's most recent paid gift transaction.
You can schedule this calculation to run on a regular basis.
## Type
date
LastGiftDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the donor's most recent directly contributed gift. Data Processing Engine calculates
this value by finding the date of the donor's most recent paid gift transaction. You can
schedule this calculation to run on a regular basis.
## Type
date
LastRecurringPaymentDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the donor last made a payment toward a recurring gift. Data Processing
Engine calculates this value by finding the date of the donor's most recent paid gift transaction
related to a recurring gift commitment. You can schedule this calculation to run on a regular
basis.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
currency
LastSoftCreditAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the most recent gift the donor influenced but didn't directly contribute. Data
Processing Engine calculates this value by finding the amount of the most recent paid gift
transaction for which the donor received soft credit. You can schedule this calculation to run
on a regular basis.
## 498
DonorGiftSummaryFundraising

DetailsField
## Type
date
LastSoftCreditDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the most recent gift the donor influenced but didn't directly contribute. Data
Processing Engine calculates this value by finding the date of the most recent paid gift
transaction for which the donor received soft credit. You can schedule this calculation to run
on a regular basis.
## Type
int
LastTwoYearGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The total number of gifts the donor directly contributed two calendar years ago. Data
Processing Engine calculates this value by counting the donor's paid gift transactions with
a transaction date from two calendar years ago. You can schedule this calculation to run on
a regular basis.
## Type
int
LastTwoYearSoftCreditCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The total number of gift soft credit records attributed to the donor two years ago.
Available in API version 63.0 and later.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view.
## Type
date
LastVolunJobPstnAsgntDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 499
DonorGiftSummaryFundraising

DetailsField
## Description
The date of the contact's last volunteer shift. Data Processing Engine calculates this value by
finding the most recent job position assignment that is related to a volunteer initiative. You
can schedule this calculation to run on a regular basis.
## Type
int
LastYearGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The total number of gifts that the donor directly contributed last calendar year. Data
Processing Engine calculates this value by counting the number of the donor's paid gift
transactions with a transaction date in the last calendar year. You can schedule this calculation
to run on a regular basis.
## Type
int
LastYearSoftCreditCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The total number of gift soft credits attributed to the donor last year.
Available in API version 63.0 and later.
## Type
currency
LastYearSoftCreditsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of soft credits earned by the donor last year.
Available in API version 63.0 and later.
## Type
currency
LowestGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The smallest single gift the donor directly contributed. Data Processing Engine calculates
this value by finding the amount of the smallest paid gift transaction of all of the donor's
paid gift transactions. You can schedule this calculation to run on a regular basis.
## Type
int
MonetaryScore
## 500
DonorGiftSummaryFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The score that represents the monetary value of the donor's gifts. Data Processing Engine
calculates this value according to how you configure RFM Scoring. You can schedule this
calculation to run on a regular basis.
Available in API version 61.0 and later.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The auto-numbered name that uniquely identifies the donor gift summary.
## Type
int
RecencyScore
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The score that represents the giving recency of a donor. Data Processing Engine calculates
this value according to how you configure RFM Scoring. You can schedule this calculation
to run on a regular basis.
Available in API version 61.0 and later.
## Type
date
SecondGiftDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the second gift the donor directly contributed. Data Processing Engine calculates
this value by finding the date of the donor's second paid gift transaction. You can schedule
this calculation to run on a regular basis.
## Type
int
SoftCreditCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of gifts the donor influenced and didn't directly contribute. Data Processing
Engine calculates this value by counting paid gift transactions for which the donor receives
soft credit. You can schedule this calculation to run on a regular basis.
## 501
DonorGiftSummaryFundraising

DetailsField
## Type
currency
TotalBookableRevenue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Data Processing Engine calculates this value by subtracting any transactions associated with
booked pledges from the value of all transactions and booked pledges. You can schedule
this calculation to run on a regular basis.
Available in API version 62.0 and later.
## Type
currency
TotalGiftsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of all gifts the donor directly contributed. Data Processing Engine calculates this
value by adding the amounts of the donor's paid gift transactions. You can schedule this
calculation to run on a regular basis.
## Type
int
TotalHardSoftCredits
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of gifts the donor directly contributed and influenced. Data Processing Engine
calculates this value by counting the donor's paid transactions and paid transactions for
which the donor receives soft credit.. You can schedule this calculation to run on a regular
basis.
## Type
currency
TotalHardSoftCreditsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of all gifts the donor directly contributed and influenced. Data Processing Engine
calculates this value by adding the amounts of the donor's paid transactions and paid
transactions for which the donor receives soft credit.. You can schedule this calculation to
run on a regular basis.
## Type
int
TotalPaidRcrInstallments
## 502
DonorGiftSummaryFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of recurring installments that the donor directly contributed. Data Processing
Engine calculates this value by counting the donor's paid gift transactions associated with
recurring gift commitments. You can schedule this calculation to run on a regular basis.
## Type
currency
TotalPaidRcrInstlAmt
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of all of the recurring installments that the donor directly contributed. Data
Processing Engine calculates this value by adding the amounts of the donor's paid gift
transactions associated with recurring gift commitments. You can schedule this calculation
to run on a regular basis.
## Type
int
TotalVolunJobPstnAsgnCnt
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of times a contact has volunteered, which is the number of job position
assignments related to volunteer initiatives. The Data Processing Engine adds the assignments
and calculates the value. You can schedule this calculation to run regularly.
## Type
double
TotalVolunteerHours
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total hours a contact volunteered. The Data Processing Engine adds the hours from job
position assignments related to volunteer initiatives and calculates the value. You can schedule
this calculation to run regularly.
## Type
currency
TotalSoftCreditsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all soft credits the donor has earned.
Available in API version 63.0 and later.
## 503
DonorGiftSummaryFundraising

GiftActuarialEntry
Represents the foundational data for calculating the future value of a planned gift, including life expectancy and discount rates. This
object is available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
## Fields
DetailsField
## Type
picklist
ActuarialMethod
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the actuarial method of the actuarial entry.
Possible values are:
## •
CommutationFactors
## •
DiscountedRates
## •
## Expectancy
## •
## Not Applicable
## •
PresentValue
## Type
double
AdjustmentFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The factor used to adjust annuities based on the payment frequency of the actuarial entry.
## Type
int
AgeInYears
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The age in years of the person related to the actuarial entry.
## 504
GiftActuarialEntryFundraising

DetailsField
## Type
double
AnnuityFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The factor used to calculate the annuities of the actuarial entry.
## Type
double
CommutationFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The commutation factor used to calculate the annuities and current values of the actuarial
entry.
## Type
double
DiscountFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The factor used to calculate the applicable discount for the actuarial entry.
## Type
int
DurationInYears
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The time in years for which the actuarial entry applies.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date after which the actuarial entry isn't in effect.
## Type
double
## Expectancy
## Properties
## Create, Filter, Nillable, Sort, Update
## 505
GiftActuarialEntryFundraising

DetailsField
## Description
The life expectancy based on the actuarial model of the actuarial entry.
## Type
double
IncomeInterest
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The interest gained on the income of the person related to the actuarial entry.
## Type
percent
InterestRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The interest rate percentage of the actuarial entry.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the actuarial entry is active (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## 506
GiftActuarialEntryFundraising

DetailsField
## Type
int
MonthsToAnnualPayout
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of months before the annual payout of the actuarial entry.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the actuarial entry.
## Type
int
OlderAgeInYears
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The older age in years among two individuals.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
string
PaymentFrequency
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The payment frequency of the actuarial entry.
## 507
GiftActuarialEntryFundraising

DetailsField
## Type
double
PayoutRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The payout rate of the actuarial entry.
## Type
double
RemainderFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The factor used to calculate the remainder of the actuarial entry.
## Type
string
## Source
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The source of the actuarial entry.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date from which the actuarial entry takes effect.
## Type
string
## Title
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The title of the actuarial entry.
## Type
string
ValuationFactor
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the valuation factor for the actuarial entry.
## 508
GiftActuarialEntryFundraising

DetailsField
## Type
string
## Version
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The version of the actuarial entry.
## Type
int
YoungerAgeInYears
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The younger age in years among two individuals.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftActuarialEntryChangeEvent
Change events are available for the object.
GiftActuarialEntryFeed
Feed tracking is available for the object.
GiftActuarialEntryHistory
History is available for tracked fields of the object.
GiftActuarialEntryOwnerSharingRule
Sharing rules are available for the object.
GiftActuarialEntryShare
Sharing is available for the object.
GiftStewardship
Represents stewardship of a gift by a contact or an organization that isn't a donor. This object is available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 509
GiftStewardshipFundraising

## Special Access Rules
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
ID of a person, household, or organization involved in the stewardship of the gift.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
ID of the contact for the stewardship of the gift.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
multipicklist
DonorPreferences
## Properties
## Create, Filter, Nillable, Update
## Description
The donor's preferences for channels for communicating about the gift.
Possible values are:
## •
AnnualGivingSummary
## •
AnonymousRecognition
## •
CustomStewardshipPlan
## •
NamedRecognition
## •
## Newsletter
## 510
GiftStewardshipFundraising

DetailsField
## •
PhysicalRecognitionItem
## •
QuarterlyImpactReport
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of stewardship activities for the gift.
## Type
reference
GiftAgreementId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
ID of the agreement associated with the stewardship of the gift.
This field is a relationship field.
## Relationship Name
GiftAgreement
## Refers To
GiftAgreement
## Type
reference
GiftId
## Properties
## Create, Filter, Group, Sort, Update
## Description
ID of the gift under stewardship.
This field is a polymorphic relationship field.
## Relationship Name
## Gift
## Refers To
GiftCommitment, GiftTransaction, PlannedGift
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## 511
GiftStewardshipFundraising

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift stewardship record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object. ID of the creator of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of stewardship activities for the gift.
## Type
string
## Title
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The title of the gift stewardship record.
## 512
GiftStewardshipFundraising

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftStewardshipChangeEvent
Change events are available for the object.
GiftStewardshipFeed
Feed tracking is available for the object.
GiftStewardshipHistory
History is available for tracked fields of the object.
GiftStewardshipOwnerSharingRule
Sharing rules are available for the object.
GiftStewardshipShare
Sharing is available for the object.
GiftStewardshipActivity
Represents an activity carried out as part of gift stewardship. This object is available in API version 65.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
date
ActivityDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the stewardship activity.
## Type
textarea
ActivityDescription
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A description of the stewardship activity.
## Type
picklist
ActivityType
## 513
GiftStewardshipActivityFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of stewardship activity.
## Type
reference
AssignedToId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
ID of the team member responsible for the stewardship activity.
This field is a relationship field.
## Relationship Name
AssignedTo
## Refers To
## User
## Type
reference
GiftStewardshipId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The ID of the gift stewardship associated with the activity.
This field is a relationship field.
## Relationship Name
GiftStewardship
## Refers To
GiftStewardship
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## 514
GiftStewardshipActivityFundraising

DetailsField
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift stewardship activity record.
## Type
textarea
## Notes
## Properties
## Create, Nillable, Update
## Description
Notes on the stewardship activity and its outcomes.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object. ID of the creator of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The status of the stewardship activity.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
## 515
GiftStewardshipActivityFundraising

GiftStewardshipActivityChangeEvent
Change events are available for the object.
GiftStewardshipActivityFeed
Feed tracking is available for the object.
GiftStewardshipActivityHistory
History is available for tracked fields of the object.
GiftStewardshipActivityOwnerSharingRule
Sharing rules are available for the object.
GiftStewardshipActivityShare
Sharing is available for the object.
GiftAgreement
The agreement to accept a gift. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
A person, household, or organization associated with the gift agreement.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 516
GiftAgreementFundraising

DetailsField
## Description
The case associated with the gift agreement.
This field is a relationship field.
## Relationship Name
## Case
## Refers To
## Case
## Type
picklist
ComplianceStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The status of compliance review for the gift.
Possible values are:
## •
## Compliant
## •
## In Review
## •
## Noncompliant
## •
## Not Yet Submitted
## •
RequiresModification
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
A contact for the gift agreement.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
reference
ContractId
## Properties
## Create, Filter, Group, Sort
## Description
The contract associated with the gift agreement.
This field is a relationship field.
## 517
GiftAgreementFundraising

DetailsField
## Relationship Name
## Contract
## Relationship Type
## Master-detail
## Refers To
Contract (the master object)
## Type
string
GiftAgreementTitle
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The title of the gift agreement.
## Type
picklist
GiftType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of gift.
Possible values are:
## •
CapitalCampaign
## •
## In Development
## •
MajorGift
## •
OtherGiftConcept
## •
PlannedGift
## •
Programand SupportGiftConcept
## •
SpecializedGift
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## 518
GiftAgreementFundraising

DetailsField
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift agreement record.
## Type
currency
TotalGiftValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total monetary value of the gift as stated in the gift agreement.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftAgreementChangeEvent
Change events are available for the object.
GiftAgreementFeed
Feed tracking is available for the object.
GiftAgreementHistory
History is available for tracked fields of the object.
GiftAgreementOwnerSharingRule
Sharing rules are available for the object.
GiftAgreementShare
Sharing is available for the object.
GiftBatch
Represents the details and status of the batch of gifts. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## 519
GiftBatchFundraising

## Fields
DetailsField
## Type
textarea
DefaultGiftFieldValues
## Properties
## Create, Nillable, Update
## Description
The default values used for new Gift Entry Grid rows in a gift batch.
This field is available from API version 65.0 and later.
## Type
textarea
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the gift batch.
## Type
boolean
DoesTotalGiftValueMatch
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the total and estimated amount of gifts or total and estimated count of
gifts in the gift batch match (true) or not (false).
The default value is false.
## Type
int
EstimatedGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The expected number of gifts in the gift batch.
## Type
double
ExpectedValueofGiftsinBatch
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
When a single currency is accepted, this field shows the expected total value in the default
currency of the gifts in the gift batch. When multiple currencies are accepted, this field is
currency agnostic and is used to validate Estimated and Actual Batch values.
## 520
GiftBatchFundraising

DetailsField
## Type
int
FailedGiftCount
## Properties
## Filter, Group, Nillable, Sort
## Description
The number of gifts that failed to process.
## Type
dateTime
LastProcessedDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The last date and time when the gift batch was processed.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The autogenerated name of the gift batch.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## 521
GiftBatchFundraising

DetailsField
## Description
ID of the owner of this object. ID of the creator of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
int
ProcessedGiftCount
## Properties
## Filter, Group, Nillable, Sort
## Description
The number of gifts that have been processed.
## Type
picklist
ScreenTemplateName
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Specifies the name of the screen template that's used for the gift batch.
Possible values are:
## •
## Default
The default value is Default.
## Type
picklist
## Status
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the gift batch.
Possible values are:
## •
## Failed
## •
## In Progress
## •
PartiallyProcessed
## •
## Processed
## •
## Unprocessed
The default value is Unprocessed.
## 522
GiftBatchFundraising

DetailsField
## Type
string
StatusReason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reason for a gift batch status.
## Type
double
TotalBatchAmount
## Properties
## Filter, Nillable, Sort
## Description
When a single currency is accepted, this field shows the total value in the default currency
of the gifts in the gift batch. When multiple currencies are accepted, this field is currency
agnostic and is used to validate Estimated and Actual Batch values.
## Type
int
TotalGiftCount
## Properties
## Filter, Group, Nillable, Sort
## Description
The total number of gifts in the gift batch.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftBatchChangeEvent
Change events are available for the object.
GiftBatchFeed
Feed tracking is available for the object.
GiftBatchHistory
History is available for tracked fields of the object.
GiftBatchOwnerSharingRule
Sharing rules are available for the object.
GiftBatchShare
Sharing is available for the object.
GiftCommitment
Represents the commitment made by a donor. This object is available in API version 59.0 and later.
## 523
GiftCommitmentFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
CampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The campaign associated with this commitment.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
reference
CurrentGiftCmtScheduleId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The current, active schedule of the commitment.
This field is a relationship field.
## Relationship Name
CurrentGiftCmtSchedule
## Relationship Type
## Lookup
## Refers To
GiftCommitmentSchedule
## Type
textarea
## Description
## 524
GiftCommitmentFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description about the gift commitment.
## Type
reference
DonorId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The person, household, or organization account associated with this commitment.
This field is a relationship field.
## Relationship Name
## Donor
## Relationship Type
## Lookup
## Refers To
## Account
## Type
reference
DonorGiftConceptId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift concept associated with the gift commitment.
This field is a relationship field.
## Relationship Name
DonorGiftConcept
## Relationship Type
## Lookup
## Refers To
DonorGiftConcept
## Type
date
EffectiveStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date from when the commitment is in effect.
## 525
GiftCommitmentFundraising

DetailsField
## Type
int
EffectiveTransactionInterval
## Properties
## Filter, Group, Nillable, Sort
## Description
The transaction interval that's applicable based on the currently active schedule.
## Type
string
EffectiveTransactionPeriod
## Properties
## Filter, Group, Nillable, Sort
## Description
The transaction period that's applicable based on the currently active schedule.
## Type
date
ExpectedAssetMaturityDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The expected maturity date of all the committed assets for a commitment.
## Type
date
ExpectedAssetTransferDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The expected date of transferring all the committed assets for a commitment.
## Type
date
ExpectedEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the total amount of the commitment is expected to be fully paid.
## Type
currency
ExpectedTotalCmtAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total donation amount that's expected for this commitment.
## 526
GiftCommitmentFundraising

DetailsField
## Type
picklist
FormalCommitmentType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the formality type of the commitment.
Possible values are:
## •
## Verbal
## •
## Written
The default value is Verbal.
## Type
picklist
FulfillmentType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies whether the commitment fulfillment depends on one or more conditions or is
unconditional.
Possible values are:
## •
## Conditional
## •
## Unconditional
The default value is Unconditional.
## Type
reference
GiftAgreementId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift agreement associated with the gift commitment.
This field is a relationship field.
## Relationship Name
GiftAgreement
## Relationship Type
## Lookup
## Refers To
GiftAgreement
## Type
picklist
GiftVehicle
## 527
GiftCommitmentFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the vehicle that's used to fulfill a gift commitment.
Possible values are:
## •
## Bequest
## •
CharitableGiftAnnuity
## •
DonorAdvisedFund
## •
LifeInsurance
## •
## Other
## •
PooledIncomeFund
## •
## Trust
## Type
picklist
GiftVehicleType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of gift vehicle that fulfills the gift commitment.
Possible values are:
## •
CharitableLeadTrust
## •
CharitableRemainderTrust
## •
DeferredGiftAnnuity
## •
FlexibleGiftAnnuity
## •
ImmediateGiftAnnuity
## •
## Other
## Type
boolean
IsAssetTransferExpected
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the donor intends to transfer non-monetary assets or not.
The default value is false.
## Type
date
LastPaidTransactionDate
## Properties
## Filter, Group, Nillable, Sort
## 528
GiftCommitmentFundraising

DetailsField
## Description
The date of the last paid transaction for the commitment.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view indirectly.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the gift commitment.
## Type
currency
NextTransactionAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The expected amount of the next gift transaction in the commitment schedule. This is
calculated automatically based on the currently active schedule.
## Type
date
NextTransactionDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the next gift transaction in the commitment schedule. This is calculated
automatically based on the currently active schedule.
## 529
GiftCommitmentFundraising

DetailsField
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The opportunity associated with this commitment.
This field is a relationship field.
## Relationship Name
## Opportunity
## Relationship Type
## Lookup
## Refers To
## Opportunity
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
PartyPhilanthropicRsrchPrflId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The research profile related to the gift commitment.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicRsrchPrfl
## Relationship Type
## Lookup
## 530
GiftCommitmentFundraising

DetailsField
## Refers To
PartyPhilanthropicRsrchPrfl
## Type
reference
PlannedGiftId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The planned gift associated with the gift commitment.
This field is a relationship field.
## Relationship Name
PlannedGift
## Relationship Type
## Lookup
## Refers To
PlannedGift
## Type
picklist
RecurrenceType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of recurrence of a commitment.
Possible values are:
## •
FixedLength
## •
OpenEnded
The default value is OpenEnded.
## Type
picklist
ScheduleType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the schedule and type of the commitment.
Possible values are:
## •
## Custom
## •
## Recurring
The default value is Recurring.
## 531
GiftCommitmentFundraising

DetailsField
## Type
picklist
## Status
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the commitment.
Possible values are:
## •
## Active
## •
## Closed
## •
## Draft
## •
## Failing
## •
## Lapsed
## •
## Paused
The default value is Draft.
## Type
currency
TotCommitmentScheduleAmt
## Properties
## Filter, Nillable, Sort
## Description
The total expected donation amount that's calculated across all schedules in this commitment.
This field is a calculated field.
## Type
currency
TotExpcAssetMaturityVal
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The expected maturity value of all the committed assets for a commitment.
## Type
currency
TotExpcAssetTransferVal
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total expected value of all the committed assets when they're transferred for a
commitment.
## Type
currency
TotalAssetPresentValue
## 532
GiftCommitmentFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total current value of all the committed assets for a commitment.
## Type
currency
TotalCurrentMonth
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all gift commitments made for the current month. This field is available
from API version 62.0 and later.
## Type
currency
TotalCurrentQuarter
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all gift commitments made for the current quarter. This field is available
from API version 62.0 and later.
## Type
currency
TotalCurrentYear
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all gift commitments made for the current year. This field is available from
API version 62.0 and later.
## Type
currency
TotalNextYear
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all gift commitments made for the next year. This field is available from
API version 62.0 and later.
## Type
currency
TotalPaidTransactionAmount
## Properties
## Filter, Nillable, Sort
## 533
GiftCommitmentFundraising

DetailsField
## Description
The total amount of paid gift transactions for the commitment.
## Type
int
TransactionPaymentCount
## Properties
## Filter, Group, Nillable, Sort
## Description
The number of paid gift transactions for the commitment.
## Type
currency
WrittenOffAmount
## Properties
## Filter, Nillable, Sort
## Description
The total amount of written-off gift transactions for this commitment.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftCommitmentChangeEvent (API Version 62.0)
Change events are available for the object.
GiftCommitmentFeed
Feed tracking is available for the object.
GiftCommitmentHistory
History is available for tracked fields of the object.
GiftCommitmentOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftCommitmentShare
Sharing is available for the object.
GiftCmtChangeAttrLog
Represents the history of changes to a Gift Commitment over time with attribution to the source campaign or source code attributed
to that change. This object is available in API version 60.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## 534
GiftCmtChangeAttrLogFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
CampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The campaign associated with this commitment.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
currency
ChangePerDayAmount
## Properties
## Create, Filter, Sort, Update
## Description
The change in amount of the commitment converted to amount per day.
## Type
picklist
ChangeStatus
## Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
## Description
The status of the change to the commitment.
Possible values are:
## •
## Downgrade
## •
## Neutral
## 535
GiftCmtChangeAttrLogFundraising

DetailsField
## •
## Pause
## •
## Resume
## •
## Upgrade
The default value is Upgrade.
## Type
picklist
ChangeType
## Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of change to the commitment. It’s value is populated based on the current
schedule and the schedule before it.
Possible values are:
## •
Amount- When the amount changes, comparing the actual amount on the schedule.
## •
Frequency- When the Transaction Interval or Transaction Period changes.
## •
Frequencyand Amount- When both the interval and the amount changes.
Applies when the first commitment is scheduled, the current schedule is paused or when
a paused schedule is resumed.
The default value is Frequency.
## Type
date
EffectiveDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The effective date for the commitment change.
## Type
reference
GiftCommitmentId
## Properties
## Create, Filter, Group, Sort
## Description
The commitment associated with this gift commitment schedule.
This field is a relationship field.
## Relationship Name
GiftCommitment
## Relationship Type
Master-Detail
## Refers To
GiftCommitment
## 536
GiftCmtChangeAttrLogFundraising

DetailsField
## Type
reference
GiftCommitmentScheduleId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift commitment schedule associated with the gift transaction.
This field is a relationship field.
## Relationship Name
GiftCommitmentSchedule
## Relationship Type
## Lookup
## Refers To
GiftCommitmentSchedule
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the gift commitment schedule.
## Type
reference
OutreachSourceCodeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 537
GiftCmtChangeAttrLogFundraising

DetailsField
## Description
The outreach source code associated with this gift commitment attribution change log.
This field is a relationship field.
## Relationship Name
OutreachSourceCode
## Relationship Type
## Lookup
## Refers To
OutreachSourceCode
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftCmtChangeAttrLogFeed
Feed tracking is available for the object.
GiftCmtChangeAttrLogHistory
History is available for tracked fields of the object.
GiftCommitmentSchedule
Represents the schedule for fulfilling the commitment. This object is available in API version 59.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
CampaignId
## 538
GiftCommitmentScheduleFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The campaign associated with this gift commitment schedule. All gift transactions associated
with this gift commitment schedule are associated with this campaign.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
string
CampaignName
## Properties
## Filter, Group, Nillable, Sort
## Description
The name of the campaign associated with the gift commitment schedule.
## Type
picklist
CommitmentUpdateReason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reason the gift commitment schedule changed.
Possible values are:
## •
PaymentMethodDeclined
## •
FinancialHardship
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the new schedule for this gift commitment.
## Type
reference
GiftCommitmentId
## Properties
## Create, Filter, Group, Sort
## 539
GiftCommitmentScheduleFundraising

DetailsField
## Description
The commitment associated with this gift commitment schedule. A value is always required
in this field to save the record.
This field is a relationship field.
## Relationship Name
GiftCommitment
## Relationship Type
Master-Detail
## Refers To
GiftCommitment
## Type
string
GiftCommitmentName
## Properties
## Filter, Group, Nillable, Sort
## Description
The name of the related gift commitment.
## Type
reference
GiftCommitmentSchdBefEditId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The schedule that's associated with the current gift commitment schedule before it was
edited
This field is a relationship field.
## Relationship Name
GiftCommitmentSchdBefEdit
## Relationship Type
## Lookup
## Refers To
GiftCommitmentSchedule
## Type
picklist
GiftCommitmentStatus
## Properties
Defaulted on create, Filter, Group, Nillable, Sort
## Description
The status of the gift commitment that's fulfilled by the schedule.
Possible values are:
## •
## Active
## 540
GiftCommitmentScheduleFundraising

DetailsField
## •
## Closed
## •
## Draft
## •
## Failing
## •
## Lapsed
## •
## Paused
The default value is Draft.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the gift commitment schedule.
## Type
lookup
OutreachSourceCodeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach source code associated with the gift transaction.
This field is a relationship field. This field is available from API version 60.0 and later.
## Relationship Name
OutreachSourceCode
## Relationship Type
## Lookup
## 541
GiftCommitmentScheduleFundraising

DetailsField
## Refers To
OutreachSourceCode
## Type
lookup
PaymentInstrumentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Payment Instrument used to complete the transaction. This field is available from API
version 60.0 and later.
This field is a relationship field.
## Relationship Name
PaymentInstrument
## Relationship Type
## Lookup
## Refers To
PaymentInstrument
## Type
picklist
PaymentMethod
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The payment method for the transactions associated with this gift commitment schedule.
All transactions associated with the commitment schedule default to this gift payment
method.
Possible values are:
## •
## ACH
## •
## Asset
## •
## Cash
## •
## Check
## •
CreditCard
## •
## Cryptocurrency
## •
In-Kind
## •
PayPal
## •
## Stock
## •
## Unknown
## •
## Venmo
## 542
GiftCommitmentScheduleFundraising

DetailsField
## Type
string
ProcessorReference
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reference of the payment processor associated with the payment instrument. This field
is available from API version 60.0 and later.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The start date of the new schedule for this gift commitment. A value is always required in
this field to save the record.
## Type
currency
TotalScheduleAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The expected total amount of all gift transactions associated with the gift commitment
schedule.
## Type
currency
TransactionAmount
## Properties
## Create, Filter, Sort, Update
## Description
The gift amount of each transaction associated with the gift commitment schedule. A value
is always required in this field to save the record.
## Type
picklist
TransactionDay
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The day of the month to create gift transaction in the future for a monthly or yearly transaction
period. If you select the day as 29 or 30, the gift transaction will be created on the last day
for months that don't have that many days.
Possible values are the numbers 1 through 30 or the value LastDay.
The default value is 1.
## 543
GiftCommitmentScheduleFundraising

DetailsField
Always required when the Transaction Period is Monthly.
## Type
int
TransactionInterval
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The interval of running the gift commitment schedule. The transaction period and interval
define how the schedule is run. For example, if the transaction period is monthly and the
transaction interval is 3, the schedule is run after every three months.
## Type
picklist
TransactionPeriod
## Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
## Description
The period for which the gift commitment schedule is run. The transaction period and
frequency define how the schedule is run. For example, if the transaction period is monthly
and the transaction frequency is 3, the schedule is run after every three months. A value is
always required in this field to save the record.
Possible values are:
## •
## Custom
## •
## Daily
## •
## Monthly
## •
## Weekly
## •
## Yearly
The default value is Monthly.
## Type
picklist
## Type
## Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of gift commitment schedule. A value is always required in this field to
save the record.
Possible values are:
## •
CreateTransactions
## •
PauseTransactions
The default value is CreateTransactions.
## 544
GiftCommitmentScheduleFundraising

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftCommitmentScheduleChangeEvent (API Version 62.0)
Change events are available for the object.
GiftCommitmentScheduleFeed
Feed tracking is available for the object.
GiftCommitmentScheduleHistory
History is available for tracked fields of the object.
GiftCommitmentScheduleOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftCommitmentScheduleShare (API Version 64.0)
Sharing is available for the object.
GiftDefaultDesignation
Represents the default designation for gifts that originate from an opportunity, campaign, or commitment. This object is available in API
version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
percent
AllocatedPercentage
## Properties
## Create, Filter, Sort, Update
## Description
The percentage of the gift that's allocated to this designation.
## Type
reference
GiftDesignationId
## Properties
## Create, Filter, Group, Sort, Update
## 545
GiftDefaultDesignationFundraising

DetailsField
## Description
The gift designation associated with this gift default designation.
A value is always required in this field to save the record.
This field is a relationship field.
## Relationship Name
GiftDesignation
## Relationship Type
## Lookup
## Refers To
GiftDesignation
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The auto-numbered name that uniquely identifies this gift default designation.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object. ID of the creator of this object.
This field is a polymorphic relationship field.
## 546
GiftDefaultDesignationFundraising

DetailsField
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ParentRecordId
## Properties
## Create, Filter, Group, True, Sort, Update
## Description
The parent record of this gift default designation.
A value is always required in this field to save the record.
This field is a polymorphic relationship field.
## Relationship Name
ParentRecord
## Relationship Type
## Lookup
## Refers To
Campaign, GiftCommitment, Opportunity
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftDefaultDesignationChangeEvent (API Version 64.0)
Change events are available for the object.
GiftDefaultDesignationFeed
Feed tracking is available for the object.
GiftDefaultDesignationHistory
History is available for tracked fields of the object.
GiftDefaultDesignationOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftDefaultDesignationShare
Sharing is available for the object.
GiftDefaultSoftCredit
Represents the default allocation for soft credits on gift commitment transactions that are created by a recurrence engine and credited
to constituents who influenced the commitment. This object is available in API version 62.0 and later.
## 547
GiftDefaultSoftCreditFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view indirectly.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The unique, auto-numbered name of the gift default soft credit.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## 548
GiftDefaultSoftCreditFundraising

DetailsField
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
ParentRecordId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The parent opportunity, or gift commitment record that's related to this default soft credit.
This field is a polymorphic relationship field.
## Relationship Name
ParentRecord
## Refers To
GiftCommitment, Opportunity
## Type
currency
PartialAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount of the gift transaction that's allocated as a soft credit to the specified recipient.
## Type
percent
PartialPercent
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of the gift transaction that's allocated as a soft credit to the specified recipient.
## Type
reference
RecipientId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person or organization account that's associated with the soft credit.
This field is a relationship field.
## Relationship Name
## Recipient
## 549
GiftDefaultSoftCreditFundraising

DetailsField
## Refers To
## Account
## Type
picklist
## Role
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The soft credit role of the account or contact.
Possible values are:
## •
## Honoree
## •
HouseholdMember
## •
## Influencer
## •
MatchedDonor
## •
## Other
## •
SoftCredit
## •
## Solicitor
## •
ThirdPartyDonor
The default value is SoftCredit.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftDefaultSoftCreditChangeEvent (API Version 64.0)
Change events are available for the object.
GiftDefaultSoftCreditFeed (API Version 64.0)
Feed tracking is available for the object.
GiftDefaultSoftCreditHistory
History is available for tracked fields of the object.
GiftDefaultSoftCreditOwnerSharingRule
Sharing rules are available for the object.
GiftDefaultSoftCreditShare
Sharing is available for the object.
GiftDesignation
Represents a designation that can be assigned to a gift transaction. This object is available in API version 59.0 and later.
## 550
GiftDesignationFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
currency
AverageTransactionAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The average value of all paid gift transactions related to the related gift designation. Data
Processing Engine calculates this value by dividing the gift designation's total transaction
amount by its total transaction count. You can schedule this calculation to run on a regular
basis.
## Type
int
CurrentYearTransactionCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The count of the current year's paid transactions related to the related gift designation. Data
Processing Engine calculates this value by counting the gift designation's paid gift transactions
with a transaction date in this calendar year. You can schedule this calculation to run on a
regular basis.
## Type
currency
CurrentYearTrxnAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the current year's paid transactions related to the related gift designation. Data
Processing Engine calculates this value by adding the amounts of the gift designation's paid
gift transactions with a transaction date this calendar year. You can schedule this calculation
to run on a regular basis.
## Type
textarea
## Description
## 551
GiftDesignationFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the gift designation.
## Type
date
FirstPaidTransactionDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the first paid gift transaction related to the related gift designation. Data Processing
Engine calculates this value by finding the date of the first paid gift transaction related to
the gift designation. You can schedule this calculation to run on a regular basis.
## Type
currency
HighestTransactionAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The highest transaction value associated with the related gift designation. Data Processing
Engine calculates this value by finding the amount of the largest paid gift transaction related
to the gift designation. You can schedule this calculation to run on a regular basis.
## Type
boolean
IsActive
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates if the gift designation is active (true) or not (false).
The default value is true.
## Type
boolean
IsDefault
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the unrestricted gift amount is to be allocated to this designation as default
(true) or not (false). There can only be a single designation with this set to true at a
time.
The default value is false.
## 552
GiftDesignationFundraising

DetailsField
## Type
date
LastPaidTransactionDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the most recent paid gift transaction related to the related gift designation. Data
Processing Engine calculates this value by finding the date of the most recent related paid
gift transaction related to the gift designation. You can schedule this calculation to run on
a regular basis.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
currency
LastTwoYearTrxnAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the gift transactions completed two calendar years ago related to the related
gift designation. Data Processing Engine calculates this value by adding the amounts of all
paid gift transactions related to the gift designation with a transaction date from two calendar
years ago. You can schedule this calculation to run on a regular basis.
## Type
int
LastTwoYearTrxnCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The count of gift transactions made two calendar years ago that are related to the related
gift designation. Data Processing Engine calculates this value by counting all paid gift
transactions related to the gift designation with a transaction date from two calendar years
ago. You can schedule this calculation to run on a regular basis.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## 553
GiftDesignationFundraising

DetailsField
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view.
## Type
int
LastYearTransactionCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The count of gift transactions related to the related gift designation and made last calendar
year. Data Processing Engine calculates this value by counting all paid gift transactions related
to the gift designation with a transaction date in the last calendar year. You can schedule
this calculation to run on a regular basis.
## Type
currency
LastYearTrxnAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of gift transactions related to the related gift designation and completed last
calendar year. Data Processing Engine calculates this value by adding the amounts of all paid
gift transactions related to the gift designation with a transaction date from the last calendar
year. You can schedule this calculation to run on a regular basis.
## Type
currency
LowestTransactionAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the smallest paid transaction related to the related gift transaction. Data
Processing Engine calculates this value by finding the smallest paid gift transaction amount
related to the related gift designation. You can schedule this calculation to run on a regular
basis.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the gift designation.
## Type
reference
OwnerId
## 554
GiftDesignationFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
currency
TotalTransactionAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all gift transactions related to the related gift designation. Data Processing
Engine calculates this value by adding the total amounts of all paid gift transactions related
to the gift designation. You can schedule this calculation to run on a regular basis.
## Type
int
TotalTransactionCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The count of all paid transactions related to the related gift designation. Data Processing
Engine calculates this value counting the paid gift transactions related to the gift designation.
You can schedule this calculation to run on a regular basis.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftDesignationChangeEvent (API Version 64.0)
Change events are available for the object.
GiftDesignationFeed
Feed tracking is available for the object.
GiftDesignationHistory
History is available for tracked fields of the object.
## 555
GiftDesignationFundraising

GiftDesignationOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftDesignationShare
Sharing is available for the object.
GiftEntry
Represents gifts created individually or in a batch before they're processed and logged in their target records. After processing, these
records serve as an audit trail for gift transactions. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
CampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The campaign that's associated with the gift entry.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
date
CheckDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date on the check that is used as the payment method for the gift.
## 556
GiftEntryFundraising

DetailsField
## Type
string
## City
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The city where the donor resides.
## Type
string
## Country
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The country where the donor resides.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Identifies the currency used for the gift transaction.
Valid value is:
## •
USD—U.S. Dollar
The default value is USD. Available in API version 61.0 and later.
## Type
currency
DonorCoverAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The fee amount that a donor pays in addition to the gift amount.
## Type
reference
DonorId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person, household, or organization account associated with the gift.
This field is a relationship field.
## Relationship Name
## Donor
## 557
GiftEntryFundraising

DetailsField
## Relationship Type
## Lookup
## Refers To
## Account
## Type
date
EffectiveStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date from when the commitment is in effect. Available in API version 61.0 and later.
## Type
email
## Email
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The email of the donor.
## Type
date
ExpectedEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the total amount of the commitment is expected to be paid. Available in API
version 61.0 and later.
## Type
string
ExpiryMonth
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The month of the credit card expiration date. This field is available from API version 60.0 and
later.
## Type
string
ExpiryYear
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The year of the credit card expiration date. This field is available from API version 60.0 and
later.
## 558
GiftEntryFundraising

DetailsField
## Type
string
FirstName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The first name of the donor.
## Type
currency
GiftAmount
## Properties
## Create, Filter, Sort, Update
## Description
The amount of the gift.
## Type
reference
GiftBatchId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The parent gift batch that's associated with the gift entry.
This field is a relationship field.
## Relationship Name
GiftBatch
## Relationship Type
## Lookup
## Refers To
GiftBatch
## Type
reference
GiftCommitmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift commitment that's associated with the gift entry.
This field is a relationship field.
## Relationship Name
GiftCommitment
## Relationship Type
## Lookup
## Refers To
GiftCommitment
## 559
GiftEntryFundraising

DetailsField
## Type
currency
GiftDesignation1Amount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount to be allocated to designation 1.
## Type
reference
GiftDesignation1Id
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the designation 1 to which the gift amount is to be allocated.
This field is a relationship field.
## Relationship Name
GiftDesignation1
## Relationship Type
## Lookup
## Refers To
GiftDesignation
## Type
percent
GiftDesignation1Percent
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of gift amount to be allocated to designation 1 if the direct amount isn’t
being allocated.
## Type
currency
GiftDesignation2Amount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount to be allocated to designation 2.
## Type
reference
GiftDesignation2Id
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 560
GiftEntryFundraising

DetailsField
## Description
The name of the designation 2 to which the gift amount is to be allocated.
This field is a relationship field.
## Relationship Name
GiftDesignation2
## Relationship Type
## Lookup
## Refers To
GiftDesignation
## Type
percent
GiftDesignation2Percent
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of gift amount to be allocated to designation 2 if the direct amount isn’t
being allocated.
## Type
currency
GiftDesignation3Amount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount to be allocated to designation 3.
## Type
reference
GiftDesignation3Id
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the designation 3 to which the gift amount is to be allocated.
This field is a relationship field.
## Relationship Name
GiftDesignation3
## Relationship Type
## Lookup
## Refers To
GiftDesignation
## Type
percent
GiftDesignation3Percent
## 561
GiftEntryFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of gift amount to be allocated to designation 3 if the direct amount isn’t
being allocated.
## Type
string
GiftProcessingResult
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The processing result of the gift entry record.
## Type
textarea
GiftDesignationInformation
## Properties
## Create, Nillable, Update
## Description
Details about the gift designation such as the designation name, amount, or percentage of
the gift that's allocated to the designation.
Available in API version 66.0 and later.
## Type
picklist
GiftProcessingStatus
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the processing status of the gift entry.
Possible values are:
## •
## Failure
## •
## New
## •
## Success
The default value is New.
## Type
date
GiftReceivedDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The date when the gift is received.
## 562
GiftEntryFundraising

DetailsField
## Type
reference
GiftTransactionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift transaction that's associated with the gift entry.
This field is a relationship field.
## Relationship Name
GiftTransaction
## Relationship Type
## Lookup
## Refers To
GiftTransaction
## Type
picklist
GiftType
## Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
## Description
Specifies the type of gift that's associated with the gift entry.
Possible values are:
## •
## Individual
## •
## Organizational
The default value is Individual.
## Type
phone
HomePhone
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The home phone number of the donor.
## Type
boolean
IsNewRecurringGift
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the gift is a new recurring gift commitment (true) or not (false).
The default value is false. Available in API version 61.0 and later.
## 563
GiftEntryFundraising

DetailsField
## Type
boolean
IsSetAsDefault
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the values in the gift entry are used as default values in other gift entries
of the gift batch or not.
The default value is false.
## Type
string
## Last4
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last 4 digits of the credit card or bank account. This field is available from API version
60.0 and later.
## Type
string
LastName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The last name of the donor.
## Type
dateTime
LastProcessedDateTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time when the gift entry was last processed.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## 564
GiftEntryFundraising

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
phone
MobilePhone
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The mobile number of the donor.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The name of the gift entry record.
## Type
string
OrganizationName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the donating organization that's associated with the gift entry.
## Type
reference
OutreachSourceCodeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach source code that's associated with the campaign for the gift entry record.
This field is a relationship field.
## Relationship Name
OutreachSourceCode
## Relationship Type
## Lookup
## Refers To
OutreachSourceCode
## 565
GiftEntryFundraising

DetailsField
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object. ID of the creator of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
string
PaymentIdentifier
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The identifier of the payment method for the gift, such as check number, transaction order
number, merchant order number.
## Type
picklist
PaymentMethod
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the payment method used for this gift.
Possible values are:
## •
## ACH
## •
## Asset
## •
## Cash
## •
## Check
## •
CreditCard
## •
## Cryptocurrency
## •
In-Kind
## •
PayPal
## •
## Stock
## •
## Unknown
## •
## Venmo
## 566
GiftEntryFundraising

DetailsField
## Type
string
PostalCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The postal code from the donor's address.
## Type
picklist
## Salutation
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the honorific abbreviation, word, or phrase to be used in front of the donor's name
in greetings, such as Dr. or Mrs.
Possible values are:
## •
## Dr.
## •
## Mr.
## •
## Mrs.
## •
## Ms.
## •
## Mx.
## •
## Prof.
## Type
textarea
SoftCreditInformation
## Properties
## Create, Nillable, Update
## Description
The information about the soft credit, such as the name of the soft creditor, role, and amount
or percentage of soft credit allocated to the soft creditor.
## Type
string
## State
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the state or province where the donor resides.
## Type
string
## Street
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 567
GiftEntryFundraising

DetailsField
## Description
The street details from the donor's address.
## Type
currency
TotalTransactionFeeAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total transaction fees charged by the payment processor for the gift. For example,
application fees, processing fees.
## Type
picklist
TransactionDay
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the day of the month to create gift transaction in the future for a monthly transaction
period. If you select the day as 29 or 30, the gift transaction will be created on the last day
for months that don't have that many days.
Valid values are: numerals 1–30 and LastDay (of the month)
The default value is 1. Available in API version 61.0 and later.
## Type
int
TransactionInterval
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The interval of running the gift commitment schedule. The transaction period and interval
define how the schedule is run. For example, if the transaction period is monthly and
transaction interval is 3, the schedule is run after every three months. Available in API version
61.0 and later.
## Type
picklist
TransactionPeriod
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The period for which the gift commitment schedule is run. The transaction period and
frequency define how the schedule is run. For example, if the transaction period is monthly
and transaction frequency is 3, the schedule is run after every three months.
Valid values are:
## •
## Custom
## 568
GiftEntryFundraising

DetailsField
## •
## Daily
## •
## Monthly
## •
## Weekly
## •
## Yearly
The default value is Monthly. Available in API version 61.0 and later.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftEntryChangeEvent
Change events are available for the object.
GiftEntryFeed
Feed tracking is available for the object.
GiftEntryHistory
History is available for tracked fields of the object.
GiftEntryOwnerSharingRule
Sharing rules are available for the object.
GiftEntryShare
Sharing is available for the object.
GiftRefund
Represents a refund of a gift. This object is available in API version 59.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## 569
GiftRefundFundraising

## Fields
DetailsField
## Type
currency
## Amount
## Properties
## Create, Filter, Sort, Update
## Description
The amount of the refund.
## Type
date
## Date
## Properties
## Create, Filter, Group, Sort, Update
## Description
The date the transaction was refunded.
## Type
currency
GatewayTransactionFee
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The transaction fee charged by the payment gateway. This field is available from API version
60.0 and later.
## Type
reference
GiftTransactionId
## Properties
## Create, Filter, Group, Sort
## Description
The gift transaction associated with this refund.
This field is a relationship field.
## Relationship Name
GiftTransaction
## Relationship Type
Master-Detail
## Refers To
GiftTransaction
## Type
string
LastGatewayErrorMessage
## 570
GiftRefundFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The most recent error message that's received by the gateway. This field is available from
API version 60.0 and later.
## Type
dateTime
LastGatewayProcessedDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time of the last processing attempt by the gateway. This field is available from
API version 60.0 and later.
## Type
string
LastGatewayResponseCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The most recent response code that's received by the gateway. This field is available from
API version 60.0 and later.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## 571
GiftRefundFundraising

DetailsField
## Description
The unique, auto-numbered name of the gift refund.
## Type
currency
ProcessorTransactionFee
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The transaction fee charged by the payment processor. This field is available from API version
60.0 and later.
## Type
picklist
## Reason
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reason for the refund.
Possible values are:
## •
DonorRequest
## •
IncorrectAmount
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the refund.
Possible values are:
## •
## Completed
## •
## Failed
## •
## Initiated
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftRefundChangeEvent (API Version 62.0)
Change events are available for the object.
GiftRefundFeed
Feed tracking is available for the object.
## 572
GiftRefundFundraising

GiftRefundHistory
History is available for tracked fields of the object.
GiftRefundOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftRefundShare(API Version 64.0)
Sharing is available for the object.
GiftSoftCredit
Represents the soft credit attributed to a person or organization for the gift transaction. This object is available in API version 59.0 and
later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
GiftTransactionId
## Properties
## Create, Filter, Group, Sort
## Description
The gift transaction associated with this soft credit.
This field is a relationship field.
## Relationship Name
GiftTransaction
## Relationship Type
Master-Detail
## Refers To
GiftTransaction
## Type
dateTime
LastReferencedDate
## 573
GiftSoftCreditFundraising

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The unique, auto-numbered name of the gift soft credit.
## Type
currency
PartialAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount of the soft credit when it isn't the full transaction amount.
## Type
percent
PartialPercent
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of the full transaction amount for this soft credit when it isn't the full
transaction amount.
Note:  Soft Credit percent values don’t need to total to 100% when there are multiple
soft credit records.
## Type
reference
PartyPhilanthropicRsrchPrflId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 574
GiftSoftCreditFundraising

DetailsField
## Description
The research profile associated with the gift.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicRsrchPrfl
## Relationship Type
## Lookup
## Refers To
PartyPhilanthropicRsrchPrfl
## Type
reference
RecipientId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person account that's associated with the soft credit.
This field is a relationship field.
## Relationship Name
## Recipient
## Relationship Type
## Lookup
## Refers To
## Account
## Type
picklist
## Role
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The soft credit role of the account or contact.
Possible values are:
## •
## Honoree
## •
HouseholdMember
## •
## Influencer
## •
MatchedDonor
## •
## Other
## •
SoftCredit
## •
## Solicitor
## •
ThirdPartyDonor
## 575
GiftSoftCreditFundraising

DetailsField
The default value is SoftCredit.
## Type
currency
SoftCreditAmount
## Properties
## Filter, Nillable, Sort
## Description
The calculated amount of the soft credit.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftSoftCreditChangeEvent (API Version 62.0)
Change events are available for the object.
GiftSoftCreditFeed
Feed tracking is available for the object.
GiftSoftCreditHistory
History is available for tracked fields of the object.
GiftSoftCreditOwnerSharingRule
Sharing rules are available for the object.
GiftSoftCreditShare (API Version 64.0)
Sharing is available for the object.
GiftTransaction
Represents a completed transaction from a gift. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## 576
GiftTransactionFundraising

## Fields
DetailsField
## Type
date
AcknowledgementDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift transaction was acknowledged.
## Type
picklist
AcknowledgementStatus
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the acknowledgement that's sent for the gift transaction.
Possible values are:
## •
Don'tSend
## •
## Sent
## •
## To Be Sent
The default value is To Be Sent.
## Type
reference
CampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The campaign associated with the gift transaction.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
date
CheckDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 577
GiftTransactionFundraising

DetailsField
## Description
The date on the check.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Identifies the currency used for the gift transaction.
Valid value is:
## •
USD—U.S. Dollar
The default value is USD. Available in API version 61.0 and later.
## Type
currency
CurrentAmount
## Properties
## Filter, Nillable, Sort
## Description
This field is a calculated field.
## Type
textarea
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the gift transaction.
## Type
currency
DonorCoverAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount the donor added to their gift to cover fees. Available in API version 61.0 and
later.
## Type
reference
DonorGiftConceptId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift concept associated with the gift.
## 578
GiftTransactionFundraising

DetailsField
This field is a relationship field.
## Relationship Name
DonorGiftConcept
## Relationship Type
## Lookup
## Refers To
DonorGiftConcept
## Type
reference
DonorId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person, household, or organization account associated with the gift transaction.
This field is a relationship field.
## Relationship Name
## Donor
## Relationship Type
## Lookup
## Refers To
## Account
## Type
string
GatewayReference
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Reference of the transaction that the gateway assigned. This field is available from API version
60.0 and later.
## Type
currency
GatewayTransactionFee
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The transaction fee charged by the payment gateway. This field is available from API version
60.0 and later.
## Type
reference
GiftAgreementId
## 579
GiftTransactionFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift agreement associated with the gift transaction.
This field is a relationship field.
## Relationship Name
GiftAgreement
## Relationship Type
## Lookup
## Refers To
GiftAgreement
## Type
reference
GiftCommitmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift commitment associated with the gift transaction.
This field is a relationship field.
## Relationship Name
GiftCommitment
## Relationship Type
## Lookup
## Refers To
GiftCommitment
## Type
reference
GiftCommitmentScheduleId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift commitment schedule associated with the gift transaction.
This field is a relationship field.
## Relationship Name
GiftCommitmentSchedule
## Relationship Type
## Lookup
## Refers To
GiftCommitmentSchedule
## 580
GiftTransactionFundraising

DetailsField
## Type
picklist
GiftType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of gift that's associated with the gift transaction.
Possible values are:
## •
## Individual
## •
## Organizational
The default value is Individual.
## Type
boolean
IsFullyRefunded
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Set to true when Status equals FullyRefunded. You can query and filter on this
field, but you cannot directly set the value.
## Type
boolean
IsPaid
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Set to true when Status equals Paid and Current Amount equals 0. You can query
and filter on this field, but you cannot directly set the value.
## Type
boolean
IsPartiallyRefunded
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Set to true when Status equals Paid and Current Amount is greater than 0. You can
query and filter on this field, but you cannot directly set the value.
## Type
boolean
IsWrittenOff
## Properties
Defaulted on create, Filter, Group, Sort
## 581
GiftTransactionFundraising

DetailsField
## Description
Set to true when Status equals Written-Off. You can query and filter on this field, but
you cannot directly set the value.
## Type
string
LastGatewayErrorMessage
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The most recent error message that's received by the gateway. This field is available from
API version 60.0 and later.
## Type
dateTime
LastGatewayProcessedDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time of the last processing attempt by the gateway. This field is available from
API version 60.0 and later.
## Type
string
LastGatewayResponseCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The most recent response code that's received by the gateway. This field is available from
API version 60.0 and later.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## 582
GiftTransactionFundraising

DetailsField
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn't null, the user accessed this record or list view.
## Type
reference
MatchingEmployerTransactionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift transaction made by the employer that matches the gift transaction.
This field is a relationship field.
## Relationship Name
MatchingEmployerTransaction
## Relationship Type
## Lookup
## Refers To
GiftTransaction
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the gift transaction.
## Type
currency
NonTaxDeductibleAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The portion of the gift transaction amount that can't be claimed as a tax deduction by the
donor. Available in API version 61.0 and later.
## Type
currency
OriginalAmount
## Properties
## Create, Filter, Sort, Update
## Description
The original amount of gift transaction that includes donor cover and excludes the transaction
fees. A value is always required in this field to save the record.
## 583
GiftTransactionFundraising

DetailsField
## Type
reference
OutreachSourceCodeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach source code associated with the gift transaction.
This field is a relationship field.
## Relationship Name
OutreachSourceCode
## Relationship Type
## Lookup
## Refers To
OutreachSourceCode
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
PartyPhilanthropicRsrchPrflId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The research profile associated with the gift.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicRsrchPrfl
## Relationship Type
## Lookup
## 584
GiftTransactionFundraising

DetailsField
## Refers To
PartyPhilanthropicRsrchPrfl
## Type
string
PaymentIdentifier
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reference number associated with the payment method for the gift, such as check
number, transaction order number, merchant order number.
## Type
lookup
PaymentInstrumentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Payment Instrument used to complete the transaction. This field is available from API
version 60.0 and later.
This field is a relationship field.
## Relationship Name
PaymentInstrument
## Relationship Type
## Lookup
## Refers To
PaymentInstrument
## Type
picklist
PaymentMethod
## Properties
## Create, Filter, Group, Sort, Update
## Description
Specifies the payment method used to complete the gift transaction. A value is always
required in this field to save the record.
Possible values are:
## •
## ACH
## •
## Asset
## •
## Cash
## •
## Check
## •
CreditCard
## •
## Cryptocurrency
## •
In-Kind
## 585
GiftTransactionFundraising

DetailsField
## •
PayPal
## •
## Stock
## •
## Unknown
## •
## Venmo
## Type
string
ProcessorReference
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reference of the payment processor associated with the payment instrument. This field
is available from API version 60.0 and later.
## Type
currency
ProcessorTransactionFee
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The transaction fee charged by the payment processor. This field is available from API version
60.0 and later.
## Type
currency
RefundedAmount
## Properties
Defaulted on create, Filter, Nillable, Sort
## Description
The amount of the original gift transaction that was refunded.
This field is a calculated field.
## Type
picklist
## Status
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Specifies the status of the gift transaction. A value is always required in this field to save the
record.
Possible values are:
## •
## Canceled
## •
## Failed
## •
FullyRefunded
## •
## Paid
## 586
GiftTransactionFundraising

DetailsField
## •
## Pending
## •
## Unpaid
## •
Written-Off
The default value is Unpaid.
## Type
picklist
TaxReceiptStatus
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the tax receipt for the gift transaction. This field is available from API
version 62.0 and later.
Possible values are:
## •
Don'tSend
## •
## Sent
## •
## To Be Sent
The default value is To Be Sent.
## Type
currency
TotalTransactionFee
## Properties
## Filter, Nillable, Sort
## Description
The total amount of fees charged by the payment gateway and processor for this transaction.
This field is available from API version 60.0 and later.
This field is a calculated field.
## Type
date
TransactionDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the donor completed the gift transaction.
This field is required if the gift transaction status is set to Paid or FullyRefunded.
## Type
date
TransactionDueDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 587
GiftTransactionFundraising

DetailsField
## Description
The expected date of the scheduled gift transaction.
This field is required if the gift transaction is related to a gift commitment.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftTransactionChangeEvent (API Version 62.0)
Change events are available for the object.
GiftTransactionFeed
Feed tracking is available for the object.
GiftTransactionHistory
History is available for tracked fields of the object.
GiftTransactionOwnerSharingRule
Sharing rules are available for the object.
GiftTransactionShare
Sharing is available for the object.
GiftTransactionDesignation
Represents a junction between a gift transaction and a gift designation. This object is available in API version 59.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
currency
## Amount
## 588
GiftTransactionDesignationFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount of the transaction allocated to the designation.
## Type
reference
GiftDesignationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift designation associated with this transaction designation. A value is always required
in this field to save the record.
This field is a relationship field.
## Relationship Name
GiftDesignation
## Relationship Type
## Lookup
## Refers To
GiftDesignation
## Type
reference
GiftTransactionId
## Properties
## Create, Filter, Group, Sort
## Description
The transaction associated with this transaction designation. A value is always required in
this field to save the record.
This field is a relationship field.
## Relationship Name
GiftTransaction
## Relationship Type
Master-Detail
## Refers To
GiftTransaction
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## 589
GiftTransactionDesignationFundraising

DetailsField
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The auto-numbered name that uniquely identifies this transaction designation.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
percent
## Percent
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of the transaction amount allocated to the designation.
## 590
GiftTransactionDesignationFundraising

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftTransactionDesignationChangeEvent (API Version 62.0)
Change events are available for the object.
GiftTransactionDesignationFeed
Feed tracking is available for the object.
GiftTransactionDesignationHistory
History is available for tracked fields of the object.
GiftTransactionDesignationOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftTransactionDesignationShare
Sharing is available for the object.
GiftTribute
Represents the details and status of the gift tribute. This object is available in API version 59.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
GiftCommitmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift commitment associated with this tribute.
This field is a relationship field.
## Relationship Name
GiftCommitment
## Relationship Type
## Lookup
## 591
GiftTributeFundraising

DetailsField
## Refers To
GiftCommitment
## Type
reference
GiftTransactionId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift transaction associated with this tribute.
This field is a relationship field.
## Relationship Name
GiftTransaction
## Relationship Type
## Lookup
## Refers To
GiftTransaction
## Type
reference
HonoreeContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact (person account) associated with the tribute gift transaction.
This field is a relationship field.
## Relationship Name
HonoreeContact
## Relationship Type
## Lookup
## Refers To
## Account
## Type
textarea
HonoreeInformation
## Properties
## Create, Nillable, Update
## Description
The additional details of the tribute recipient.
## Type
string
HonoreeName
## 592
GiftTributeFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the person being honored by the tribute gift transaction.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The unique, auto-numbered name of the gift tribute.
## Type
picklist
NotificationChannel
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies how to notify the tribute notification contact should be notified.
Possible values are:
## •
## Email
## •
## Mail
## Type
reference
NotificationContactId
## 593
GiftTributeFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact (person account) who should be notified of the tribute gift transaction.
This field is a relationship field.
## Relationship Name
NotificationContact
## Relationship Type
## Lookup
## Refers To
## Account
## Type
string
NotificationContactName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the person who should be notified of the tribute gift transaction.
## Type
date
NotificationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the recipient was notified about the tribute.
## Type
email
NotificationEmail
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The email that's used to notify a person about the tribute gift transaction.
## Type
textarea
NotificationInfo
## Properties
## Create, Nillable, Update
## Description
The information about the person who should be notified of the tribute gift transaction.
## 594
GiftTributeFundraising

DetailsField
## Type
textarea
NotificationMessage
## Properties
## Create, Nillable, Update
## Description
The notification message that's sent for the tribute gift transaction.
## Type
picklist
NotificationStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the status of the notification sent to the tribute recipient.
Possible values are:
## •
Don'tSend
## •
## Sent
## •
## To Be Sent
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
picklist
TributeType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of tribute when a gift is given on behalf of someone else.
Possible values are:
## •
## Honor
## •
## Memorial
## 595
GiftTributeFundraising

## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
GiftTributeChangeEvent (API Version 64.0)
Change events are available for the object.
GiftTributeFeed
Feed tracking is available for the object.
GiftTributeHistory
History is available for tracked fields of the object.
GiftTributeOwnerSharingRule (API Version 64.0)
Sharing rules are available for the object.
GiftTributeShare
Sharing is available for the object.
GiftValueForecast
The past, current, and projected monetary value of a gift. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
double
ActuarialFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A factor based on actuarial assumptions that’s used to calculate the gift’s future value.
## Type
currency
CurrentValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The gift's current value.
## 596
GiftValueForecastFundraising

DetailsField
## Type
reference
GiftId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The gift associated with the gift value forecast.
This field is a polymorphic relationship field.
## Relationship Name
## Gift
## Refers To
GiftCommitment, PlannedGift
## Type
currency
InitialValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The gift's initial value.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
date
LastUpdatedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift’s value was last updated.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
date
MaturityDate
## 597
GiftValueForecastFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift’s expected to mature.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift value forecast record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
currency
ProjectedValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The gift’s projected value at maturity.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The start date for tracking the gift’s value.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
## 598
GiftValueForecastFundraising

GiftValueForecastChangeEvent
Change events are available for the object.
GiftValueForecastFeed
Feed tracking is available for the object.
GiftValueForecastHistory
History is available for tracked fields of the object.
GiftValueForecastOwnerSharingRule
Sharing rules are available for the object.
GiftValueForecastShare
Sharing is available for the object.
OutreachSourceCode
Represents information about a source code that's associated with an outreach campaign. This object is available in API version 59.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users
## Fields
DetailsField
## Type
int
AudienceCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of person accounts, contacts, and businesses in this audience.
## Type
textarea
AudienceInformation
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Detailed information about the audience for the outreach source code. This field is available
from API version 62.0 and later.
## 599
OutreachSourceCodeFundraising

DetailsField
## Type
reference
CampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The parent campaign associated with this source code.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Identifies the currency used for the gift transaction.
Valid value is:
## •
USD—U.S. Dollar
The default value is USD. Available in API version 61.0 and later.
## Type
textarea
## Description
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The description of the source code.
## Type
reference
FocusSegmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Lists individuals who are segmented for this source code.
This field is available with a Data Cloud license.
This field is a relationship field.
## 600
OutreachSourceCodeFundraising

DetailsField
## Relationship Name
MarketSegment
## Relationship Type
## Lookup
## Refers To
MarketSegment
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view.
## Type
picklist
MessageChannel
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The channel used for the message from which the donation originated. This field is available
from API version 60.0 and later.
Possible values are:
## •
DigitalPaid
## •
DirectMail
## •
## Email
## •
OrganicWeb
## •
## Physical
## •
## SMS
## •
SharePartner
## •
SocialOrganic
## •
SocialPaid
## 601
OutreachSourceCodeFundraising

DetailsField
## •
## Telemarketing
## Type
string
MessageChannelPlatform
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach message channel platform from which the donation originated. This field is
available from API version 60.0 and later.
## Type
string
MessageChannelPlatformAccount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The platform account used to send the outreach message. This field is available from API
version 60.0 and later.
## Type
string
MessageContent
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach message content. This field is available from API version 60.0 and later.
## Type
string
MessageContentTitle
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach message title. This field is available from API version 60.0 and later.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The name of the source code.
## Type
reference
OwnerId
## 602
OutreachSourceCodeFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
ID of the owner of this object. ID of the creator of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
dateTime
SentDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The date and time that the outreach was sent. Available in API version 61.0 and later.
## Type
string
SourceCode
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
The unique source code. This field is unique within your organization.
## Type
url
SourceCodeBaseUrl
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The base URL for the outreach source code. This field is available from API version 60.0 and
later.
## Type
url
SourceCodeUrl
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The URL with UTM codes that's generated for the outreach source code. This field is available
from API version 60.0 and later.
## 603
OutreachSourceCodeFundraising

DetailsField
## Type
picklist
## Status
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The status of the source code.
Possible values are:
## •
## Active
## •
## Archived
## •
## Inactive
The default value is Active.
## Type
picklist
UsageType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the usage of the outreach source code.
Possible values are:
## •
## Fundraising
The default value is Fundraising.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
OutreachSourceCodeChangeEvent (API Version 62.0)
Change events are available for the object.
OutreachSourceCodeFeed
Feed tracking is available for the object.
OutreachSourceCodeHistory
History is available for tracked fields of the object.
OutreachSourceCodeOwnerSharingRule
Sharing rules are available for the object.
OutreachSourceCodeShare
Sharing is available for the object.
OutreachSummary
Represents a summary of results of the outreach campaign. This object is available in API version 59.0 and later.
## 604
OutreachSummaryFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
currency
AverageGiftAmount
## Properties
## Filter, Sort
## Description
The average amount of all gifts in response to the related outreach source code or campaign.
Data Processing Engine calculates this value by dividing the total gift transaction amount
by the gift count. You can schedule this calculation to run on a regular basis.
## Type
currency
AverageOnetimeGiftAmount
## Properties
## Filter, Sort
## Description
The average amount of all one-time, non-recurring gifts in response to the related outreach
source code or campaign. Data Processing Engine calculates this value by dividing the total
one-time gift amount by the one-time donor count. You can schedule this calculation to
run on a regular basis.
## Type
currency
AverageRecurringGiftAmount
## Properties
## Filter, Sort
## Description
The average amount of all recurring gifts in response to the related outreach source code
or campaign. Data Processing Engine calculates this value by dividing the total recurring gift
amount by the recurring donor count. You can schedule this calculation to run on a regular
basis.
## Type
reference
CampaignId
## 605
OutreachSummaryFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The campaign associated with this outreach gift summary. You can associate one campaign
with an outreach summary.
This field is a relationship field.
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
int
DonorCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of unique donors in response to the related outreach source code or campaign.
Data Processing Engine calculates this value by counting the unique donors with paid
transactions. You can schedule this calculation to run on a regular basis.
## Type
int
GiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of gifts in response to the related outreach source code or campaign. Data
Processing Engine calculates this value by counting the paid gift transactions related to the
campaign or source code. You can schedule this calculation to run on a regular basis.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## 606
OutreachSummaryFundraising

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The auto-numbered name that uniquely identifies the outreach summary.
## Type
int
OnetimeDonorCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of contacts who gave a one-time, non-recurring donation in response to the
related outreach source code or campaign. Data Processing Engine calculates this value by
counting the unique donors with related gift transactions that are paid and not associated
with a gift commitment. You can schedule this calculation to run on a regular basis.
## Type
reference
OutreachSourceCodeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach source code associated with this outreach gift summary. You can associate
one outreach source code with an outreach summary.
This field is a relationship field.
## Relationship Name
OutreachSourceCode
## Relationship Type
## Lookup
## Refers To
OutreachSourceCode
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## 607
OutreachSummaryFundraising

DetailsField
## Description
ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
int
RecurringDonorCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of contacts who gave a recurring donation in response to the related outreach
source code or campaign. Data Processing Engine calculates this value by counting the
unique donors for gift transactions that are paid and related to recurring gift commitments.
You can schedule this calculation to run on a regular basis.
## Type
percent
ResponseRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of responses received from donors to the related outreach source code or
campaign. Data Processing Engine calculates this value by dividing the donor count by the
audience count. You can schedule this calculation to run on a regular basis.
## Type
currency
TotalGiftTransactionAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all paid gifts in response to the related outreach source code or campaign.
Data Processing Engine calculates this value by adding the amounts of all paid gift
transactions. You can schedule this calculation to run on a regular basis.
## Type
currency
TotalOnetimeGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## 608
OutreachSummaryFundraising

DetailsField
## Description
The total value of all one-time gifts in response to the related outreach source code or
campaign. Data Processing Engine calculates this value by adding the total amounts of all
related paid gift transactions that aren't related to a gift commitment. You can schedule this
calculation to run on a regular basis.
## Type
currency
TotalRecurringGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total value of all recurring gifts in response to the related outreach source code or
campaign. Data Processing Engine calculates this value by adding the total amounts of all
paid gift transactions that are related to recurring gift commitments. You can schedule this
calculation to run on a regular basis.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
OutreachSummaryFeed
Feed tracking is available for the object.
OutreachSummaryHistory
History is available for tracked fields of the object.
OutreachSummaryShare
Sharing is available for the object.
PartyCategory
The criteria for categorizing contacts and accounts based on specific classification information for a specified time period. This object is
available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## 609
PartyCategoryFundraising

## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account ID related to the classification record.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
picklist
## Classification
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The classification associated with the contact or account.
Possible values are:
## •
HighNet WorthProspect
## •
InfluencerProspect
## •
## LYBUNT
## •
LapsedDonor
## •
LegacyProspect
## •
LifetimeStewardship
## •
## SYBUNT
## •
## Top 100
## •
## Top 25
## •
Undergrador GradProspect
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact ID related to the classification record.
This field is a relationship field.
## 610
PartyCategoryFundraising

DetailsField
## Relationship Name
## Contact
## Refers To
## Contact
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the classification.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the classification record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## 611
PartyCategoryFundraising

DetailsField
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the classification.
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the status of the classification record.
Possible values are:
## •
## Active
## •
## Archived
## •
## Error
## •
## Inactive
## •
## Pending
## •
## Superseded
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartyCategoryHistory
History is available for tracked fields of the object.
PartyCategoryOwnerSharingRule
Sharing rules are available for the object.
PartyCategoryShare
Sharing is available for the object.
PartyPhilanthropicAssessment
Represents a formalized assessment of wealth when a rating takes place, such as a third-party wealth assessment, a property valuation,
a financial asset assessment, or an internal assessment. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 612
PartyPhilanthropicAssessmentFundraising

## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account associated with the assessment.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
AssessmentOrganizationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The organization performing the assessment.
This field is a relationship field.
## Relationship Name
AssessmentOrganization
## Refers To
## Account
## Type
picklist
AssessmentType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of assessment, such as executive summary, donor brief, or third-party assessment.
Possible values are:
## •
DonorBrief
## •
ExecutiveSummary
## •
ThirdPartyAssessment
## Type
currency
AssetLiquidationValue
## 613
PartyPhilanthropicAssessmentFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the party's assets that can be liquidated within a specified time period.
## Type
reference
AttributedUserId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person the research is attributed to.
This field is a relationship field.
## Relationship Name
AttributedUser
## Refers To
## User
## Type
currency
BusinessOwnershipValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of private businesses owned by the party.
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The case that delivers the research.
This field is a relationship field.
## Relationship Name
## Case
## Relationship Type
## Lookup
## Refers To
## Case
## Type
reference
ContactId
## 614
PartyPhilanthropicAssessmentFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact associated with the assessment.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
date
## Date
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the assessment.
## Type
textarea
ExtendedSummary
## Properties
## Create, Nillable, Update
## Description
A detailed summary of the assessment.
## Type
picklist
GivingLevel
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The party's giving level.
Possible values are:
## •
## $1,000,000-$4,999,999
## •
## $1,000-$2,499
## •
## $10,000,000-$24,999,999
## •
## $10,000-$24,999
## •
## $100,000-$249,999
## •
## $100-$499
## •
## $2,500-$4,999
## •
## $25,000,000+
## •
## $25,000-$49,999
## 615
PartyPhilanthropicAssessmentFundraising

DetailsField
## •
## $250,000-$999,999
## •
## $5,000,000-$9,999,999
## •
## $5,000-$9,999
## •
## $50,000-$99,999
## •
## $500-$999
## •
## Under$100
## Type
picklist
GraduationCohort
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The party's graduation cohort, if the party is a person.
Possible values are:
## •
0-5 YearsSinceGraduation
## •
11-20YearsSinceGraduation
## •
21-30YearsSinceGraduation
## •
31-40YearsSinceGraduation
## •
41-50YearsSinceGraduation
## •
50+ YearsSinceGraduation
## •
6-10YearsSinceGraduation
## Type
picklist
GraduationStatus
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The party's graduation status, if the party is a person.
Possible values are:
## •
AssociateDegree
## •
## Certificateor Award
## •
MultipleDegrees
## •
Non-Graduate
## •
## Other
## •
PostgraduateDegree
## •
SecondaryDiploma
## •
UndergraduateDegree
## 616
PartyPhilanthropicAssessmentFundraising

DetailsField
## Type
currency
## Income
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The party's annual income.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string or number assigned to the assessment.
## Type
currency
OtherAssetsValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the party's assets not covered by other measures of net worth.
## Type
currency
OtherNonprofitGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## 617
PartyPhilanthropicAssessmentFundraising

DetailsField
## Description
The monetary value of the party's donations to other nonprofits.
## Type
int
OtherNonprofitGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of the party's donations to other nonprofits.
## Type
picklist
OverallRating
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The overall rating determined by the assessment.
Possible values are:
## •
## High
## •
## Low
## •
## Medium
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
PartyPhilanthropicRsrchPrflId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The research profile associated with the research.
This field is a relationship field.
## 618
PartyPhilanthropicAssessmentFundraising

DetailsField
## Relationship Name
PartyPhilanthropicRsrchPrfl
## Relationship Type
## Lookup
## Refers To
PartyPhilanthropicRsrchPrfl
## Type
currency
RealEstateValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of real estate owned by the party.
## Type
date
ResearchEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the research, used to measure the research period and assess the efficiency
of the research.
## Type
double
ResearchHours
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total hours spent on research for the assessment, used to track resource allocation and
time spent on researching each prospect.
## Type
date
ResearchSharedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date the completed research is shared with the relationship officer, used to ensure
transparency and track the flow of information in prospect engagement.
## Type
date
ResearchStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 619
PartyPhilanthropicAssessmentFundraising

DetailsField
## Description
The start date of the research, used to create a timeline for the research process and track
the duration of the research phase.
## Type
reference
ResponsiblePersonId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The relationship officer assigned to the party.
This field is a relationship field.
## Relationship Name
ResponsiblePerson
## Refers To
## User
## Type
currency
RetirementSavingsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The party's retirement savings.
## Type
textarea
ShortSummary
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A short summary of the assessment.
## Type
currency
StockValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of public stock owned by the party.
## Type
textarea
StrengthsAndOpportunities
## Properties
## Create, Nillable, Update
## 620
PartyPhilanthropicAssessmentFundraising

DetailsField
## Description
The strengths and opportunities identified in the assessment.
## Type
textarea
WeaknessesAndDrawbacks
## Properties
## Create, Nillable, Update
## Description
The weaknesses and drawbacks identified in the assessment.
## Type
currency
WealthAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The party's total wealth.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartyPhilanthropicAssessmentHistory
History is available for tracked fields of the object.
PartyPhilanthropicAssessmentOwnerSharingRule
Sharing rules are available for the object.
PartyPhilanthropicAssessmentShare
Sharing is available for the object.
PartyPhilanthropicIndicator
Represents an unconfirmed or soft indication that highlights a person's wealth or growth potential. This object is available in API version
63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 621
PartyPhilanthropicIndicatorFundraising

## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account associated with the indicator.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
AttributedUserId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person the research is attributed to.
This field is a relationship field.
## Relationship Name
AttributedUser
## Refers To
## User
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The case that delivers the research.
This field is a relationship field.
## Relationship Name
## Case
## Relationship Type
## Lookup
## Refers To
## Case
## 622
PartyPhilanthropicIndicatorFundraising

DetailsField
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact associated with the indicator.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
date
DateCollected
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date the information about the indicator was collected.
## Type
currency
EstimatedValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The estimated monetary value of the indicator.
## Type
picklist
## Indicator
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The indicator, such as donation history, net worth, volunteer hours, or inheritance.
Possible values are:
## •
DonationHistory
## •
## Inheritance
## •
## Net Worth
## •
VolunteerHours
## Type
picklist
IndicatorType
## 623
PartyPhilanthropicIndicatorFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of indicator, such as engagement, wealth, philanthropy, communication,
volunteerism, or media mention.
Possible values are:
## •
## Communication
## •
## Engagement
## •
MediaMention
## •
## Philanthropy
## •
## Volunteerism
## •
## Wealth
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string or number assigned to the party philanthropic indicator.
## Type
string
OtherSource
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 624
PartyPhilanthropicIndicatorFundraising

DetailsField
## Description
An indicator source that isn't a Salesforce object.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
ParticipantId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The person involved in collecting the research.
This field is a relationship field.
## Relationship Name
## Participant
## Refers To
## Contact
## Type
reference
PartyPhilanthropicOccurrenceId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The prospect research event associated with the indicator.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicOccurrence
## Refers To
PartyPhilanthropicOccurrence
## Type
reference
PartyPhilanthropicRsrchPrflId
## 625
PartyPhilanthropicIndicatorFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The research profile associated with the indicator.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicRsrchPrfl
## Relationship Type
## Lookup
## Refers To
PartyPhilanthropicRsrchPrfl
## Type
reference
RelatedOrganizationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The organization involved in collecting the research.
This field is a relationship field.
## Relationship Name
RelatedOrganization
## Refers To
## Account
## Type
date
ResearchEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the research, used to measure the research period and assess the efficiency
of the research.
## Type
double
ResearchHours
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total hours spent researching the indicator, used to track resource allocation and time
spent on researching each prospect.
## 626
PartyPhilanthropicIndicatorFundraising

DetailsField
## Type
date
ResearchSharedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the completed research is shared with the relationship officer, used to ensure
transparency and track the flow of information in prospect engagement.
## Type
date
ResearchStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the research, used to create a timeline for the research process and track
the duration of the research phase.
## Type
reference
SourceId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The business milestone, life event, or interaction summary associated with the indicator.
This field is a polymorphic relationship field.
## Relationship Name
## Source
## Refers To
BusinessMilestone, InteractionSummary, PersonLifeEvent
## Type
picklist
SourceType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of source, such as external interaction, internal data, third-party data, or public
records.
Possible values are:
## •
ExternalInteraction
## •
InternalData
## •
PublicRecords
## •
Third-PartyData
## 627
PartyPhilanthropicIndicatorFundraising

DetailsField
## Type
picklist
## Status
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The status of the prospect research indicator, if it hasn't been verified as a party philanthropic
occurrence.
Possible values are:
## •
## Promoted
## Type
textarea
## Summary
## Properties
## Create, Nillable, Update
## Description
A summary of the indicator.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartyPhilanthropicIndicatorHistory
History is available for tracked fields of the object.
PartyPhilanthropicIndicatorOwnerSharingRule
Sharing rules are available for the object.
PartyPhilanthropicIndicatorShare
Sharing is available for the object.
PartyPhilanthropicMilestone
Represents philanthropic activities and financial status for a period of time. This object is available in API version 63.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 628
PartyPhilanthropicMilestoneFundraising

## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account associated with the milestone.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
currency
AssetLiquidationValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the party's assets that can be liquidated within a specified time period.
## Type
currency
BusinessOwnershipValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
FIXME: Add the description here. [Writers: - The following description was added by the
developer when they created this field. - It may nor may not be correct, complete, or up to
date. - It is visible to customers in Setup > Object Manager in the UI. If you need to change
what is visible there, ask the developer to change it.] The value of private businesses owned
by the party.
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact associated with the milestone.
This field is a relationship field.
## Relationship Name
## Contact
## 629
PartyPhilanthropicMilestoneFundraising

DetailsField
## Refers To
## Contact
## Type
date
## Date
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date of the milestone.
## Type
textarea
ExtendedSummary
## Properties
## Create, Nillable, Update
## Description
A detailed summary of the milestone.
## Type
picklist
GivingLevel
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The party's giving level.
Possible values are:
## •
## $1,000,000-$4,999,999
## •
## $1,000-$2,499
## •
## $10,000,000-$24,999,999
## •
## $10,000-$24,999
## •
## $100,000-$249,999
## •
## $100-$499
## •
## $2,500-$4,999
## •
## $25,000,000+
## •
## $25,000-$49,999
## •
## $250,000-$999,999
## •
## $5,000,000-$9,999,999
## •
## $5,000-$9,999
## •
## $50,000-$99,999
## •
## $500-$999
## •
## Under$100
## 630
PartyPhilanthropicMilestoneFundraising

DetailsField
## Type
picklist
GraduationCohort
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The person's graduation cohort.
Possible values are:
## •
0-5 YearsSinceGraduation
## •
11-20YearsSinceGraduation
## •
21-30YearsSinceGraduation
## •
31-40YearsSinceGraduation
## •
41-50YearsSinceGraduation
## •
50+ YearsSinceGraduation
## •
6-10YearsSinceGraduation
## Type
picklist
GraduationStatus
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The person's graduation status.
Possible values are:
## •
AssociateDegree
## •
## Certificateor Award
## •
MultipleDegrees
## •
Non-Graduate
## •
## Other
## •
PostgraduateDegree
## •
SecondaryDiploma
## •
UndergraduateDegree
## Type
currency
## Income
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The party's annual income.
## 631
PartyPhilanthropicMilestoneFundraising

DetailsField
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string or number assigned to the milestone.
## Type
currency
OtherAssetsValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the party's assets not covered by other measures of net worth.
## Type
currency
OtherNonprofitGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The monetary value of the party's donations to other nonprofits.
## Type
int
OtherNonprofitGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 632
PartyPhilanthropicMilestoneFundraising

DetailsField
## Description
The number of the party's donations to other nonprofits.
## Type
picklist
OverallRating
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The overall rating of the milestone.
Possible values are:
## •
## High
## •
## Low
## •
## Medium
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
int
PtyPhilanthropicAsmtCnt
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of party philanthropic assessments within the milestone period.
## Type
int
PtyPhilanthropicIndCnt
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of party philanthropic indicators within the milestone period.
## 633
PartyPhilanthropicMilestoneFundraising

DetailsField
## Type
int
PtyPhilanthropicOccrCnt
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of party philanthropic occurrences within the milestone period.
## Type
currency
RealEstateValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of real estate owned by the party.
## Type
reference
ResponsiblePersonId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The relationship officer assigned to the assessed party at the time the assessment milestone
is generated.
This field is a relationship field.
## Relationship Name
ResponsiblePerson
## Refers To
## User
## Type
currency
RetirementSavingsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The party's retirement savings.
## Type
textarea
ShortSummary
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A short summary of the milestone.
## 634
PartyPhilanthropicMilestoneFundraising

DetailsField
## Type
currency
StockValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of public stock owned by the party.
## Type
textarea
StrengthsAndOpportunities
## Properties
## Create, Nillable, Update
## Description
The strengths and opportunities identified in the milestone.
## Type
textarea
WeaknessesAndDrawbacks
## Properties
## Create, Nillable, Update
## Description
The weaknesses and drawbacks identified in the milestone.
## Type
currency
WealthAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The party's total wealth for the milestone.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartyPhilanthropicMilestoneHistory
History is available for tracked fields of the object.
PartyPhilanthropicMilestoneOwnerSharingRule
Sharing rules are available for the object.
PartyPhilanthropicMilestoneShare
Sharing is available for the object.
## 635
PartyPhilanthropicMilestoneFundraising

PartyPhilanthropicOccurrence
xxx This object is available in API version XX.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account associated with the occurrence.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
AttributedUserId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The user the research is attributed to.
This field is a relationship field.
## Relationship Name
AttributedUser
## Refers To
## User
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The case that delivers the research.
## 636
PartyPhilanthropicOccurrenceFundraising

DetailsField
This field is a relationship field.
## Relationship Name
## Case
## Relationship Type
## Lookup
## Refers To
## Case
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact associated with the occurrence.
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
date
DateCollected
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date the information about the occurrence was collected.
## Type
currency
EstimatedValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The estimated monetary value of the occurrence.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
## 637
PartyPhilanthropicOccurrenceFundraising

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
An auto-generated string or number assigned to the party philanthropic occurrence.
## Type
picklist
OccurrenceType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The type of occurrence, such as donation history, net worth, volunteer hours, or inheritance.
Possible values are:
## •
DonationHistory
## •
## Inheritance
## •
## Net Worth
## •
VolunteerHours
## Type
string
OtherSource
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
An occurrence source that isn't a Salesforce record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The user who owns this record.
## 638
PartyPhilanthropicOccurrenceFundraising

DetailsField
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
ParticipantId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The participant contact involved in collecting the research.
This field is a relationship field.
## Relationship Name
## Participant
## Refers To
## Contact
## Type
reference
PartyPhilanthropicAssessmentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The party philanthropic assessment associated with the occurrence.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicAssessment
## Refers To
PartyPhilanthropicAssessment
## Type
reference
PartyPhilanthropicRsrchPrflId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The research profile associated with the occurrence.
This field is a relationship field.
## Relationship Name
PartyPhilanthropicRsrchPrfl
## Relationship Type
## Lookup
## 639
PartyPhilanthropicOccurrenceFundraising

DetailsField
## Refers To
PartyPhilanthropicRsrchPrfl
## Type
reference
RelatedOrganizationId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The account of the organization that provided the occurrence.
This field is a relationship field.
## Relationship Name
RelatedOrganization
## Refers To
## Account
## Type
date
ResearchEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the research, used to measure the duration of the research period and assess
the efficiency of the research.
## Type
double
ResearchHours
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total hours spent researching the occurrence, used to track resource allocation and time
spent on researching each prospect.
## Type
date
ResearchSharedDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the completed research is shared with the relationship officer, used to ensure
transparency and track the flow of information in prospect engagement.
## Type
date
ResearchStartDate
## 640
PartyPhilanthropicOccurrenceFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the research, used to create a timeline for the research process and track
the duration of the research phase.
## Type
picklist
ResearchType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The classification of research for the occurrence.
Possible values are:
## •
## Communication
## •
## Engagement
## •
MediaMention
## •
## Philanthropy
## •
## Volunteerism
## •
## Wealth
## Type
reference
SourceId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The business milestone, life event, or interaction summary associated wiith the occurrence.
This field is a polymorphic relationship field.
## Relationship Name
## Source
## Refers To
BusinessMilestone, InteractionSummary, PersonLifeEvent
## Type
picklist
SourceType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of source, such as external interaction, internal data, third-party data, or public
records.
Possible values are:
## 641
PartyPhilanthropicOccurrenceFundraising

DetailsField
## •
ExternalInteraction
## •
InternalData
## •
PublicRecords
## •
Third-PartyData
## Type
textarea
## Summary
## Properties
## Create, Nillable, Update
## Description
A description of the occurrence.
## Type
picklist
VerificationType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies whether the occurrence is known or inferred.
Possible values are:
## •
## Inferred
## •
## Known
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartyPhilanthropicOccurrenceHistory
History is available for tracked fields of the object.
PartyPhilanthropicOccurrenceOwnerSharingRule
Sharing rules are available for the object.
PartyPhilanthropicOccurrenceShare
Sharing is available for the object.
PartyPhilanthropicRsrchPrfl
Captures information associated with a contact or an organization in a many-to-one relationship. Serves as a pivot point for research on
the person or organization. This object is available in API version 64.0 and later.
## 642
PartyPhilanthropicRsrchPrflFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The account ID associated with the research profile.
This field is a relationship field.
## Relationship Name
## Account
## Refers To
## Account
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The case associated with the research profile.
This field is a relationship field.
## Relationship Name
## Case
## Refers To
## Case
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact ID associated with the research profile.
This field is a relationship field.
## 643
PartyPhilanthropicRsrchPrflFundraising

DetailsField
## Relationship Name
## Contact
## Refers To
## Contact
## Type
textarea
DetailedSummary
## Properties
## Create, Nillable, Update
## Description
A comprehensive summary of the research findings for the profile.
## Type
date
EndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The end date of the research stage, used to measure the duration of the research period and
assess the efficiency of the research.
## Type
double
HoursSpentOnResearch
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total hours spent on the stage, used for resource allocation and performance tracking.
## Type
boolean
IsResearchCompleted
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the research profile is complete (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## 644
PartyPhilanthropicRsrchPrflFundraising

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the research profile record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
percent
PctOfResearchCompleted
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of completion for the research profile stage.
## Type
picklist
ResearchProfilePhase
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The research stage of the research profile.
Possible values are:
## •
CultivationStrategyDevelopment
## •
## Disqualification
## 645
PartyPhilanthropicRsrchPrflFundraising

DetailsField
## •
## Identification
## •
InitialScreening
## •
OngoingMonitoring
## •
## Planning
## •
## Prioritization
## •
## Qualification
## •
## Ratingand Segmentation
## •
ResearchDeepDive
## •
RobustResearchCompleted
## Type
picklist
ResearchProfileType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of research profile.
Possible values are:
## •
CapitalCampaign
## •
PlannedGiving
## Type
reference
ResearcherAssignedId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The team member responsible for completing the research stage, ensuring accountability
and tracking workload across researchers.
This field is a relationship field.
## Relationship Name
ResearcherAssigned
## Refers To
## User
## Type
textarea
ShortSummary
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A brief summary of the research findings for the profile.
## 646
PartyPhilanthropicRsrchPrflFundraising

DetailsField
## Type
date
StartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of the research stage, used to track the duration of the stage and create a
timeline for the research process.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartyPhilanthropicRsrchPrflHistory
History is available for tracked fields of the object.
PartyPhilanthropicRsrchPrflOwnerSharingRule
Sharing rules are available for the object.
PartyPhilanthropicRsrchPrflShare
Sharing is available for the object.
PaymentInstrument
Represents the details related to the Payment Instrument used to complete the transaction. This object is available in API version 60.0
and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users
## Fields
DetailsField
## Type
string
AccountHolderName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 647
PaymentInstrumentFundraising

DetailsField
## Description
Name of the Payment Instrument Holder.
## Type
reference
AccountId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The Account or PersonAccount that is using the payment instrument.
This field is a relationship field.
## Relationship Name
## Account
## Relationship Type
## Lookup
## Refers To
## Account
## Type
string
BankAccountHolderType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Determines if the bank account holder is an individual or a company.
## Type
string
BankAccountNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The bank account number used for payment.
## Type
string
BankAccountType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Type of the Bank Account.
## Type
string
BankCode
## 648
PaymentInstrumentFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Code of bank associated with the bank account.
## Type
string
BankName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Name of bank associated with the bank account.
## Type
string
CardBrand
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The credit card brand, network, or issuer.
## Type
picklist
CurrencyIsoCode
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The currency ISO code. This field is hidden when multicurrency is off.
Possible values are:
## •
AUD—Australian Dollar
## •
GBP—British Pound
## •
USD—U.S. Dollar
The default value is USD.
## Type
string
DigitalWalletProvider
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The provider of the digital wallet.
## Type
string
ExpiryMonth
## 649
PaymentInstrumentFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Expire month if payment method is credit card.
## Type
string
ExpiryYear
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Expire year if payment method is credit card.
## Type
string
GatewayName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the payment gateway.
## Type
string
GatewayReference
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
A reference number from the gateway for this payment instrument.
## Type
string
## Last4
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Last 4 digits of payment method.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp for when the current user last viewed a record related to this record.
## Type
dateTime
LastViewedDate
## 650
PaymentInstrumentFundraising

DetailsField
## Properties
## Filter, Nillable, Sort
## Description
The timestamp for when the current user last viewed this record.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The unique, auto-numbered name of the payment instrument.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
string
PaymentProcessorName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the payment processor.
## Type
string
ProcessorReference
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The reference of the payment processor associated with the payment instrument.
## Type
picklist
## Type
## 651
PaymentInstrumentFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Specifies the type of the payment instrument.
Possible values are:
## •
## ACH
## •
BACSDebit
## •
BECSDebit
## •
## Bancontact
## •
CreditCard
## •
PayPal
## •
SEPADirectDebit
## •
## Venmo
## •
iDEAL
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PaymentInstrumentFeed
Feed tracking is available for the object.
PaymentInstrumentHistory
History is available for tracked fields of the object.
PaymentInstrumentShare
Sharing is available for the object.
PlannedGift
A complex gift such as an annuity, bequest, or trust. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## 652
PlannedGiftFundraising

## Fields
DetailsField
## Type
double
ActuarialFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A factor based on actuarial assumptions that’s used to calculate the gift’s future value.
## Type
currency
AmountReceived
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount received since the planned gift record was created.
## Type
date
BequestRealizationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The expected date when a bequest is likely to be realized.
## Type
reference
CaseId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The case associated with the planned gift.
This field is a relationship field.
## Relationship Name
## Case
## Refers To
## Case
## Type
reference
ContactId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The contact for the planned gift.
## 653
PlannedGiftFundraising

DetailsField
This field is a relationship field.
## Relationship Name
## Contact
## Refers To
## Contact
## Type
currency
CurrentValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The planned gift's current value.
## Type
date
DateCommitted
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift was committed.
## Type
date
DateReceived
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift was received.
## Type
int
DeferralPeriod
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The time period, in years, after which payments start.
## Type
currency
DeferredFutureValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The projected value of a deferred gift annuity at maturity.
## 654
PlannedGiftFundraising

DetailsField
## Type
percent
DiscountRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The discount rate applied to project the future value of the gift.
## Type
reference
DonorGiftConceptId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift concept associated with the planned gift.
This field is a relationship field.
## Relationship Name
DonorGiftConcept
## Refers To
DonorGiftConcept
## Type
reference
DonorId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The donor of the planned gift.
This field is a relationship field.
## Relationship Name
## Donor
## Refers To
## Account
## Type
double
## Expectancy
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The expected number of years to maturity, based on actuarial assumptions.
## Type
currency
ExpectedAmount
## 655
PlannedGiftFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The expected value of the planned gift.
## Type
currency
ExpectedEstateValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total estimated value of a donor's estate.
## Type
currency
ExpensesAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total management expenses associated with the gift.
## Type
currency
FaceValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The face value of the gift, if the gift is life insurance.
## Type
date
FirstPaymentDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the first payment is made, if the gift is a trust or an annuity.
## Type
currency
FutureValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The gift's projected value at maturity.
## Type
reference
GiftAgreementId
## 656
PlannedGiftFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift agreement associated with the planned gift.
This field is a relationship field.
## Relationship Name
GiftAgreement
## Refers To
GiftAgreement
## Type
picklist
GiftType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of planned gift.
Possible values are:
## •
## Bequest
## •
BequestSpecificAmount
## •
BequestSpecificPercentage
## •
CharitableGiftAnnuity
## •
CharitableLeadAnnuityTrust
## •
CharitableRemainderAnnuityTrust
## •
CharitableRemainderTrust
## •
CharitableRemainderUnitrust
## •
DeferredGiftAnnuity
## •
DonorAdvisedFund
## •
ImmediateGiftAnnuity
## •
LifeInsurance
## •
LifeInsuranceIrrevocableInterest
## •
OtherPlannedGift
## •
PersonalProperty
## •
PooledIncomeFund
## •
RealEstate
## •
## Securities
## Type
percent
InvestmentReturnRate
## 657
PlannedGiftFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The return rate on investments related to the gift.
## Type
boolean
IsRevocable
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the gift is revocable (true) or not (false).
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
date
LastValuationDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the planned gift value was last updated.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
currency
MarketValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The gift's current market value.
## Type
date
MaturityDate
## 658
PlannedGiftFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift is expected to mature or be realized.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the planned gift record.
## Type
percent
NetReturnRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The expected annual net return rate on the gift’s investments.
## Type
currency
NetValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The net value of the gift after expenses and payouts.
## Type
reference
OpportunityId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The opportunity associated with the planned gift.
This field is a relationship field.
## Relationship Name
## Opportunity
## Refers To
## Opportunity
## Type
reference
OwnerId
## 659
PlannedGiftFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
picklist
PayoutFrequency
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The payment frequency.
Possible values are:
## •
## Annual
## •
## Custom
## •
## Monthly
## •
One-Time
## •
## Quarterly
## •
Semi-Annual
## Type
percent
PayoutRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The rate at which payouts are made to beneficiaries.
## Type
string
PolicyNumber
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The policy number, if the gift is life insurance.
## Type
currency
PremiumAmount
## 660
PlannedGiftFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The premium amount, if the gift is life insurance.
## Type
currency
PresentValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A calculated value of future cash flows associated with an asset or planned gift.
## Type
currency
PrincipalAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The principal amount of the gift.
## Type
percent
PrincipalPercentage
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of the expected amount that's the principal amount of the gift.
## Type
percent
ProbabilityFactor
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The probability of receiving the gift.
## Type
percent
ResiduaryShare
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The percentage of the estate allocated to the institution for residuary bequests.
## Type
date
StartDate
## 661
PlannedGiftFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift agreement is initiated.
## Type
picklist
## Status
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The status of the planned gift.
Possible values are:
## •
## Active
## •
## Closed
## •
## In Probate
## •
## Inactive
## •
## Matured
## •
PendingApproval
## •
## Realized
## •
UnderAgreement
## Type
double
## Term
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The term of a trust for calculating future and present value.
## Type
date
TermEndDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the gift matures or the trust term ends.
## Type
picklist
TermType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 662
PlannedGiftFundraising

DetailsField
## Description
The term type for the trust, such as fixed number of years, one life, or two lives.
Possible values are:
## •
FixedNumberof Years
## •
JointLife
## •
## Lifeof Beneficiary
## •
## Lifeof Donor
## •
One LifeFixedTerm
## •
SingleLife
## •
Two LivesFixedTerm
## Type
string
TrustName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The name of the trust, if the gift is categorized as a trust.
## Type
picklist
TrustType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of trust.
Possible values are:
## •
CharitableLeadAnnuityTrust
## •
CharitableLeadUnitrust
## •
CharitableRemainderAnnuityTrust
## •
CharitableRemainderTrust
## •
CharitableRemainderUnitrust
## •
IrrevocableTrust
## •
RevocableTrust
## •
TestamentaryTrust
## Type
currency
TrusteeFees
## Properties
## Create, Filter, Nillable, Sort, Update
## 663
PlannedGiftFundraising

DetailsField
## Description
Fees paid to the trustee.
## Type
double
UnitsHeld
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The number of units that the donor holds in the pooled income fund.
## Type
currency
UnitsValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of 1 unit in the pooled income fund.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PlannedGiftChangeEvent
Change events are available for the object.
PlannedGiftFeed
Feed tracking is available for the object.
PlannedGiftHistory
History is available for tracked fields of the object.
PlannedGiftOwnerSharingRule
Sharing rules are available for the object.
PlannedGiftShare
Sharing is available for the object.
PlannedGiftAnnuityRate
The rate used to calculate payments for a charitable gift annuity. This object is available in API version 64.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 664
PlannedGiftAnnuityRateFundraising

## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
date
EffectiveDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date the annuity rate becomes effective.
## Type
picklist
GiftType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The gift type associated with the gift annuity. Determines the payout rate for the gift.
Possible values are:
## •
## Bequest
## •
CharitableGiftAnnuity
## •
CharitableLeadAnnuityTrust
## •
CharitableRemainderAnnuityTrust
## •
CharitableRemainderTrust
## •
DeferredGiftAnnuity
## •
DonorAdvisedFund
## •
LifeInsurance
## •
OtherPlannedGift
## •
PersonalProperty
## •
PooledIncomeFund
## •
RealEstate
## •
## Securities
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## 665
PlannedGiftAnnuityRateFundraising

DetailsField
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
date
MaturityDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the annuity payments end.
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift annuity rate record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
reference
PlannedGiftId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The planned gift associated with the gift annuity rate.
This field is a relationship field.
## Relationship Name
PlannedGift
## 666
PlannedGiftAnnuityRateFundraising

DetailsField
## Refers To
PlannedGift
## Type
percent
## Rate
## Properties
## Create, Filter, Sort, Update
## Description
The annuity rate used to calculate payments to the donor or beneficiary.
## Type
date
StartDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The date when the annuity payments begin.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PlannedGiftAnnuityRateChangeEvent
Change events are available for the object.
PlannedGiftAnnuityRateFeed
Feed tracking is available for the object.
PlannedGiftAnnuityRateHistory
History is available for tracked fields of the object.
PlannedGiftAnnuityRateOwnerSharingRule
Sharing rules are available for the object.
PlannedGiftAnnuityRateShare
Sharing is available for the object.
PlannedGiftPerformance
The performance of a planned gift over time, including returns, expenses, and net value. This object is available in API version 64.0 and
later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## 667
PlannedGiftPerformanceFundraising

## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
currency
## Expenses
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The total management expense associated with the planned gift.
## Type
percent
InvestmentReturnRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The investment return rate associated with the planned gift.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
## Type
string
## Name
## Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
## Description
The ID of the gift performance record.
## Type
currency
NetValue
## 668
PlannedGiftPerformanceFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the planned gift after accounting for expenses and payouts.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Refers To
## Group, User
## Type
percent
PayoutRate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The rate at which payouts are made to beneficiaries of the planned gift.
## Type
date
PayoutStartDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The start date of payouts to beneficiaries from the planned gift.
## Type
reference
PlannedGiftId
## Properties
## Create, Filter, Group, Sort, Update
## Description
The planned gift associated with the performance record.
This field is a relationship field.
## Relationship Name
PlannedGift
## Refers To
PlannedGift
## 669
PlannedGiftPerformanceFundraising

DetailsField
## Type
date
StartDate
## Properties
## Create, Filter, Group, Sort, Update
## Description
The start date of performance tracking for the planned gift.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PlannedGiftPerformanceChangeEvent
Change events are available for the object.
PlannedGiftPerformanceFeed
Feed tracking is available for the object.
PlannedGiftPerformanceHistory
History is available for tracked fields of the object.
PlannedGiftPerformanceOwnerSharingRule
Sharing rules are available for the object.
PlannedGiftPerformanceShare
Sharing is available for the object.
Fundraising Fields on Other Objects
Fundraising includes fields that are available on other Salesforce objects. These fields are available only in orgs with Nonprofit Cloud or
Education Cloud when Fundraising is enabled.
ContactPointAddress
Represents a contact’s billing or shipping address, which is associated with an individual or a person account. This object is available
in API version 61.0 and later.
ContactProfile
Represents information about an individual, such as their ethnicity, citizenship, birth place, race, and so on. The Fundraising fields
on this object are available in API version 59.0 and later.
ListEmail
Represents a list email sent from Salesforce, or sent from Account Engagement and synced to Salesforce. When the list email is sent,
the recipients are generated by combining recipients in the ListEmailIndividualRecipients and ListEmailRecipientSource objects.
Duplicate and other invalid recipients are removed. The result is the recipients are sent any given list email. ListEmail has a one-to-many
relationship with ListEmailRecipientSource and ListEmailIndividualRecipient objects. This object is available in API version 61.0 and
later.
## 670
Fundraising Fields on Other ObjectsFundraising

ContactPointAddress
Represents a contact’s billing or shipping address, which is associated with an individual or a person account. This object is available in
API version 61.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available only if the FundraisingAccess license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
date
ActiveFromDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the contact’s address became active.
## Type
date
ActiveToDate
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The date when the contact’s address is no longer active.
## Type
address
## Address
## Properties
## Filter, Nillable
## Description
The full address.
## Type
picklist
AddressType
## 671
ContactPointAddressFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The type of address.
Valid values are:
## •
## Billing
## •
## Shipping
## Type
time
BestTimeToContactEndTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The latest time to contact the individual.
## Type
time
BestTimeToContactStartTime
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The earliest time to contact the individual.
## Type
picklist
BestTimeToContactTimezone
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The timezone applied to the best time to contact the individual.
## Type
string
## City
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The address city.
## Type
reference
ContactPointPhoneId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## 672
ContactPointAddressFundraising

DetailsField
## Description
The primary phone number associated with this address.
This field is a relationship field.
## Relationship Name
ContactPointPhone
## Relationship Type
## Lookup
## Refers To
ContactPointPhone
## Type
string
## Country
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The address country.
## Type
picklist
GeocodeAccuracy
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The level of accuracy of a location’s geographical coordinates compared with its physical
address. A geocoding service typically provides this value based on the address’s latitude
and longitude coordinates.
Valid values are:
## •
## Address
## •
## Block
## •
## City
## •
## County
## •
ExtendedZip
## •
NearAddress
## •
## Neighborhood
## •
## State
## •
## Street
## •
## Unknown
## •
## Zip
## Type
boolean
IsDefault
## 673
ContactPointAddressFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether a contact’s address is the preferred method of communication (true)
or not (false).
The default value is false.
## Type
boolean
IsPrimary
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether a contact’s address is their primary address (true) or not (false).
The default value is false.
## Type
boolean
IsThirdPartyAddress
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the address is associated with a third party (true) or not (false).
The default value is false.
## Type
boolean
IsUndeliverable
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the address is undeliverable (true) or not (false).
The default value is false.
## Type
dateTime
LastAddressStdDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The most recent date and time that the address was evaluated by the address standardization
provider.
## Type
string
LastAddressStdStatus
## 674
ContactPointAddressFundraising

DetailsField
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The most recent status received from the address standardization provider.
## Type
dateTime
LastChangeOfAddressDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The most recent date and time that the address was evaluated by the change of address
provider.
## Type
string
LastChangeOfAddressStatus
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The status of the latest change of address request.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp for when the current user last referenced a record related to this record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp for when the current user last viewed this record. If this value is null, it’s
possible that this record was referenced (LastReferencedDate) and not viewed.
## Type
double
## Latitude
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Used with Longitude to specify the precise geolocation of the address. Acceptable values
are numbers between –90 and 90 with up to 15 decimal places.
## 675
ContactPointAddressFundraising

DetailsField
## Type
double
## Longitude
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Used with Latitude to specify the precise geolocation of the address. Acceptable values
are numbers between –180 and 180 with up to 15 decimal places.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Required. The name of the contact point address record.
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The ID of the account’s owner associated with this contact.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
reference
ParentId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The ID of the contact’s parent record. Only an individual or account can be a contact’s parent.
This field is a polymorphic relationship field.
## Relationship Name
## Parent
## Relationship Type
## Master-detail
## 676
ContactPointAddressFundraising

DetailsField
## Refers To
Account, Individual (the master object)
## Type
string
PostalCode
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The address postal code.
## Type
int
PreferenceRank
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The preference rank when there are multiple contact point addresses.
## Type
picklist
SeasonalEndDay
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The day when the seasonal address of the contact is replaced by the default address.
Valid values are: 1–31
## Type
picklist
SeasonalEndMonth
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The month when the seasonal address of the contact is replaced by the default address.
Valid values are: 1–12
## Type
picklist
SeasonalStartDay
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The day when the seasonal address of the contact replaces the default address.
Valid values are: 1–31
## 677
ContactPointAddressFundraising

DetailsField
## Type
picklist
SeasonalStartMonth
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The month when the seasonal address of the contact replaces the default address.
Valid values are: 1–12
## Type
string
## State
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The address state.
## Type
textarea
## Street
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The address street.
## Type
picklist
UsageType
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The usage type of this address. For instance, whether it’s a work address or a home address.
Valid values are:
## •
## Home
## •
## Inactive
## •
## Temporary
## •
## Work
ContactProfile
Represents information about an individual, such as their ethnicity, citizenship, birth place, race, and so on. The Fundraising fields on
this object are available in API version 59.0 and later.
## 678
ContactProfileFundraising

## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Fields
DetailsField
## Type
currency
AssetLiquidationValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of assets that can be liquidated within 90 days.
## Type
currency
BusinessOwnershipValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of private businesses the contact owns.
## Type
currency
## Income
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The annual income amount of the contact.
## Type
string
## Location
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The location where the contact currently resides.
## Type
currency
OtherAssetsValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of the contact's assets that aren't covered by other ways of measuring net worth.
## 679
ContactProfileFundraising

DetailsField
## Type
currency
OtherNonprofitGiftAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount of donations the contact has given to other nonprofits.
## Type
int
OtherNonprofitGiftCount
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The number of donations the contact has given to other nonprofits.
## Type
currency
RealEstateValue
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of real estate the contact owns.
## Type
picklist
RecurringDonorType
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of recurring donor.
Possible values are:
## •
## Active
## •
## Former
## •
## Lapsed
## Type
currency
RetirementSavingsAmount
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The amount of the contact's retirement savings.
## Type
currency
StockValue
## 680
ContactProfileFundraising

DetailsField
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
The value of public stock the contact owns.
## Type
url
## Website
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
A website that's associated with the contact.
For more information, see ContactProfile in Education Cloud.
ListEmail
Represents a list email sent from Salesforce, or sent from Account Engagement and synced to Salesforce. When the list email is sent, the
recipients are generated by combining recipients in the ListEmailIndividualRecipients and ListEmailRecipientSource objects. Duplicate
and other invalid recipients are removed. The result is the recipients are sent any given list email. ListEmail has a one-to-many relationship
with ListEmailRecipientSource and ListEmailIndividualRecipient objects. This object is available in API version 61.0 and later.
## Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
## Special Access Rules
This object is available to Marketing Cloud users with the FundraisingAccess permission set on Marketing Cloud Growth Edition campaigns.
## Fields
DetailsField
## Type
reference
CampaignId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The ID of the related campaign.
This field is a relationship field.
## 681
ListEmailFundraising

DetailsField
## Relationship Name
## Campaign
## Relationship Type
## Lookup
## Refers To
## Campaign
## Type
textarea
FromAddress
## Properties
## Create, Filter, Update
## Description
Read-only except when the list email is in a draft state. Validated against user’s addresses.
## Type
string
FromName
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
Read-only except when the list email is in a draft state. Validated against user’s addresses.
This field is null for emails sent from Account Engagement.
## Type
boolean
HasAttachment
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Read-only. Defaulted on create and update. Indicates if the list email has an attachment
(true) or not (false). This field is null for emails sent from Account Engagement.
The default value is false.
## Type
textarea
HtmlBody
## Properties
## Create, Nillable, Update
## Description
The body of the list email. This field is null for emails sent from Account Engagement.
List emails can contain up to 32,000 characters for the body. These limits include visible
characters and other characters in the email, including markup.
## 682
ListEmailFundraising

DetailsField
## Type
boolean
IsOutreachSourceCodeEnabled
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates whether outreach source code can be added to this record (true) or not (false).
The default value is false.
This field is a calculated field.
## Type
boolean
IsTracked
## Properties
Defaulted on create, Filter, Group, Sort
## Description
Indicates if email tracking was on when the list email was sent (true) or not (false). This
field is blank for emails sent from Account Engagement and synced to Salesforce. This field
is null for emails sent from Account Engagement.
The default value is false.
## Type
dateTime
LastReferencedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
## Type
dateTime
LastViewedDate
## Properties
## Filter, Nillable, Sort
## Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate isn’t null, the user accessed this record or list view indirectly.
## Type
string
## Name
## Properties
Create, Filter, Group, idLookup, Sort, Update
## Description
Read-only except when the list email is in a draft state.
## 683
ListEmailFundraising

DetailsField
## Type
reference
OutreachSourceCodeId
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach source code associated with the gift transaction.
This field is a relationship field.
## Relationship Name
OutreachSourceCode
## Relationship Type
## Lookup
## Refers To
OutreachSourceCode
## Type
reference
OwnerId
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
The ID of the owner of this object.
This field is a polymorphic relationship field.
## Relationship Name
## Owner
## Relationship Type
## Lookup
## Refers To
## Group, User
## Type
dateTime
ScheduledDate
## Properties
## Create, Filter, Nillable, Sort, Update
## Description
Read-only. If null and Status is set to Scheduled, then defaults to created time.
## Type
picklist
## Status
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
Read-only except when the list email is in a draft state.
## 684
ListEmailFundraising

DetailsField
Changing the status to Scheduled causes the list email to be sent.
Valid values are:
## •
## Cancelled
## •
## Draft
## •
LimitError
## •
## Running
## •
## Scheduled
## •
## Sent
## Type
textarea
## Subject
## Properties
## Create, Filter, Nillable, Update
## Description
Read-only except when the list email is in a draft state. This field is null for emails sent from
## Account Engagement.
List emails can contain up to 3,000 characters for the subject. These limits include visible
characters and other characters in the email, including markup.
## Type
textarea
TextBody
## Properties
## Create, Nillable, Update
## Description
Read-only except when the list email is in a draft state. This field is null for emails sent from
## Account Engagement.
## Type
int
TotalSent
## Properties
Defaulted on create, Filter, Group, Nillable, Sort
## Description
Read-only. The total number of list emails sent, including bounced, opted-out, and invalid
To: addresses.
## Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
ListEmailChangeEvent
Change events are available for the object.
## 685
ListEmailFundraising

ListEmailFeed
Feed tracking is available for the object.
ListEmailHistory
History is available for tracked fields of the object.
ListEmailOwnerSharingRule
Sharing rules are available for the object.
ListEmailShare
Sharing is available for the object.
Fundraising Business APIs
You can access Salesforce Fundraising APIs using REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
To use the Fundraising Business Process APIs:
## •
Enable Fundraising in your org.
## •
Enable donor matching method. See Configure Fundraising Settings. See the FundraisingConfig object to know about the donor
matching method details.
## •
Selet a default gift designation. See Gift Designation.
## •
Configure the duplicate and matching rules for the Account and Contact objets, Or set Duplicate Matching in Settings to No Matching.
## See Customize Duplicate Management.
The Fundraising Business Process APIs help teams create strong integrations using industry-standard tools. Use the Salesforce composite
Fundraising BP API to send a single complex payload instead of making multiple calls using multiple APIs to various objects.
Developer-friendly APIs don’t require a detailed and complete understanding of the NPC data model, greatly simplifying integrations.
These APIs offer scalability and flexibility through features like automatic record matching, batch processing, bulk operations, and dynamic
data mapping. Five robust endpoints are currently available to:
## •
Create bulk gift transactions with related donor and designations
## •
Create bulk gift commitments with related donor, schedule, and default designations
## •
Modify the future recurring schedule on a gift commitment
## •
Apply payment update metadata to gift transactions and future gift commitment installments
The Fundraising Business Process APIs are available as a standard Salesforce Connect API REST endpoint as well as through Apex.
To understand the architecture, authentication, rate limits, and how the requests and responses work, see Connect REST API Developer
## Guide.
To use Business APIs on the Postman API platform, see the Postman collection for Fundraising.
## Resources
Learn more about the available Fundraising API resources.
## Request Bodies
Learn more about the available Fundraising API request bodies.
## Response Bodies
Learn more about the available Fundraising API response bodies.
## 686
Fundraising Business APIsFundraising

## Resources
Learn more about the available Fundraising API resources.
Commitments (POST)
Create recurring gift commitments and schedules, along with associated new or matched donor. Customize fields for donor accounts,
gift commitments, and schedules.
Commitments (PATCH)
Modify the data for the schedule, campaign, outreach source code, donor, and payment instrument on an active gift commitment.
## Gift Transactions
Get gift transactions associated with a gift commitment record.
## Gift Transaction Designations
Get designations associated with a gift transaction, campaign, commitment, or opportunity.
## Gift Commitment Transactions
Get a list of gift transactions associated with a gift commitment for a donor account.
## Gift Commitment Default Designations
Get default designations associated with a gift commitment.
## Gift Campaign Default Designations
Get default designations associated with a gift campaign.
Gifts Transactions (POST)
Create gift transactions with related new or matched donor, optional transaction designations, and payment-instrument metadata.
This API supports custom fields for the donor account and gift transaction.
Transactions Payment Updates (POST)
Update the gateway and processor metadata for gift transactions. This API supports updating only the properties that are specified
in the reuest body. If you include any other standard or custom fields in the request body beyond the specified properties, an error
is shown.
Commitments Payment Updates (POST)
Update the metadata for your payment instruments for all active gift commitments.
Commitments (POST)
Create recurring gift commitments and schedules, along with associated new or matched donor. Customize fields for donor accounts,
gift commitments, and schedules.
## Resource
## /connect/fundraising/commitments
Resource example
https://yourInstance.salesforce.com/services/data/v/connect/fundraising/commitments
Available version
## 60.0
HTTP methods
## POST
## 687
ResourcesFundraising

Request body for POST
Note:  You can pass the campaign, donor, and designation IDs in an externalId object containing fieldName and
fieldValue.
JSON example
## {
"processingOptions":{
"donorOptions":{
"defaultUpdateLogic":"update_all"
## }
## },
## "commitments":[
## {
## "amount":150.25,
## "type":"pledge",
"currencyIsoCode":"USD",
"transactionPeriod":"monthly",
"transactionInterval":3,
"transactionDay":"5",
"startDate":"2024-07-06",
"endDate":"2024-07-06",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"id":"0015500000WO1ZxxAL",
"organizationName":"minicat town",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-432-9876",
## "email":"d.chavez.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## },
"paymentInstrument":{
## 688
ResourcesFundraising

"type":"CreditCard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Diner'sClub",
"bankName":"chase",
"digitalWalletProvider":"EwalletProvider",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
## "designations":[
## {
"designationId":"0gd0030f0303024",
## "percent":10
## }
## ],
"firstTransaction":{
## "amount":150.25,
"receivedDate":"2024-07-06",
"donorCoverAmount":0.25,
"transactionStatus":"Unpaid",
"gatewayTransactionFee":0.75,
"processorTransactionFee":0.45,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe
card’ssecuritycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z"
## },
"giftCommitmentCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"giftCommitmentScheduleCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"giftTransactionCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## 689
ResourcesFundraising

## }
## ]
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredDetails of the request to create the
commitment.
Limited to 100 commitments in a single
request.
## Create
## Commitment
## Request Input[]
commitments
60.0OptionalOptions for the donor matching process.Processing Options
## Details Input
processing
## Options
Response body for POST
## Create Commitment
## SEE ALSO:
## Nonprofit Cloud Developer Guide: Fundraising
Commitments (PATCH)
Modify the data for the schedule, campaign, outreach source code, donor, and payment instrument on an active gift commitment.
## Resource
/connect/fundraising/commitments/commitmentId
Resource example
https://yourInstance.salesforce.com/services/data/v/connect
/fundraising/commitments/6gc0000AbCdZF9q
Available version
## 60.0
HTTP methods
## PATCH
Request body for PATCH
Note:  You can pass the campaign, donor, and designation IDs in an externalId object containing fieldName and
fieldValue.
JSON example
## {
## "amount":150.25,
## "type":"pledge",
"transactionInterval":3,
"transactionDay":"5",
"startDate":"2024-07-06",
## 690
ResourcesFundraising

"endDate":"2024-07-06",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"organizationName":"ABCInc.",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-434-8920",
## "email":"d.chavez@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"paymentInstrument":{
"type":"CreditCard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Diner'sClub",
"bankName":"chase",
"digitalWalletProvider":"EProvider",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
"giftCommitmentCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
## 691
ResourcesFundraising

"giftCommitmentScheduleCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredGift amount of each transaction
associated with the gift commitment
schedule.
## Doubleamount
60.0OptionalCampaign that's associated with the gift
commitment.
## Campaign Detailscampaign
60.0OptionalCurrency ISO code of the gift
commitment.
## Stringcurrency
IsoCode
60.0OptionalPerson, household, or organization
account associated with the
commitment.
Donor Details InputdonorId
60.0OptionalEnd date of the new schedule for this gift
commitment. The format is
## YYYY-MM-DD.
StringendDate
60.0OptionalCustom fields of the gift commitment.Custom Field
## Details[]
giftCommitment
CustomFields
60.0OptionalCustom fields of the gift commitment
schedule.
## Custom Field
## Details[]
giftCommitment
## Schedule
CustomFields
60.0OptionalOutreach source code that's associated
with the campaign for the gift
commitment.
## Outreach Source
## Code Details
outreach
SourceCode
60.0RequiredPayment instrument that's used to
complete the transaction.
## Payment
## Instrument Details
payment
## Instrument
60.0RequiredStart date of the new schedule for this
gift commitment. The format is
## YYYY-MM-DD.
StringstartDate
60.0OptionalSpecifies the day of the month to create
gift transactions in the future for a
## Stringtransaction
## Day
monthly transaction period. If you select
the day as 29 or 30, the gift transaction
## 692
ResourcesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
is created on the last day for the months
that don't have that many days.
60.0OptionalTransaction interval that's applicable to
an incoming transaction in the
commitment.
## Integertransaction
## Interval
60.0RequiredTransaction period that's applicable to
the incoming transaction in the
## Stringtransaction
## Period
commitment. When type is pledge,
this property must be set to Custom. If
transactionPeriod is not
provided, the default isCustom.
62.0OptionalType of transaction. Possible values are:Stringtype
## •
## Pledge
## •
## Recurring
The default value is the Recurring.
Response body for PATCH
Update Commitment on page 748
## SEE ALSO:
## Nonprofit Cloud Developer Guide: Fundraising
## Gift Transactions
Get gift transactions associated with a gift commitment record.
## Resource
/connect/fundraising/gift-commitments/${commitmentId}/gift-transactions
Resource examples
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/gift-commitments/6gcxx000004WhULAA0/gift-transactions
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/gift-commitments/6gcxx000004WhULAA0/gift-transactions?count=2&period=Recent&status=Canceled,Failed
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/gift-commitments/6gcxx000004WhULAA0/gift-transactions?count=2&period=Past&fromDate=2023-02-11T13:05:23.000Z
Available version
## 59.0
HTTP methods
## GET
## 693
ResourcesFundraising

Query parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
59.0OptionalNumber of gift transactions to be retrieved.
You can get a maximum of 12 transactions
in one request.
## Integercount
By default, the API returns 12 transactions.
59.0OptionalDate
(yyyy-MM-dd'T'HH:mm:ss.SSSX)
StringfromDate
from when you want to get the
transactions. This field is not applicable if
period is Recent.
59.0OptionalPeriod for getting gift transactions.
possible values are:
## Stringperiod
## •
## Future
## •
## Past
## •
## Recent
The default period is Future.
59.0OptionalComma-separated list of gift-transactions
statuses. Possible values are:
## String[]status
## •
## Canceled
## •
## Failed
## •
FullyRefunded
## •
## Paid
## •
## Unpaid
## •
Written-Off
The default status is Unpaid.
Response body for GET
## Gift Transactions Output
## Gift Transaction Designations
Get designations associated with a gift transaction, campaign, commitment, or opportunity.
Note:  When there are no designations associated with a gift transaction, campaign, commitment, or opportunity, the API returns
the organization-wide default designations.
## Resource
/connect/fundraising/transaction/${transactionId}/designations
## 694
ResourcesFundraising

Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/transaction/6trRM000000007XYAQ/designations
Available version
## 59.0
HTTP methods
## GET
Response body for GET
## Gift Transaction Linked Designations Output
## Gift Commitment Transactions
Get a list of gift transactions associated with a gift commitment for a donor account.
## Resource
/connect/fundraising/donor/${donorId}/commitments
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/donor/001xx000003GYOpAAO/commitments
Available version
## 59.0
HTTP methods
## GET
Response body for GET
## Gift Commitment Transaction Matching Output
## Gift Commitment Default Designations
Get default designations associated with a gift commitment.
## Resource
/connect/fundraising/commitment/${commitmentId}/default-designations
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/commitment/6trRM000000007XYAQ/default-designations
Available version
## 59.0
HTTP methods
## GET
Response body for GET
## Gift Commitment Default Designations Output
## Gift Campaign Default Designations
Get default designations associated with a gift campaign.
## 695
ResourcesFundraising

## Resource
/connect/fundraising/campaign/${campaignId}/default-designations
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/fundraising/campaign/701RM000000FhntYAC/default-designations
Available version
## 59.0
HTTP methods
## GET
Response body for GET
## Gift Campaign Default Designations Output
Gifts Transactions (POST)
Create gift transactions with related new or matched donor, optional transaction designations, and payment-instrument metadata. This
API supports custom fields for the donor account and gift transaction.
## Resource
## /connect/fundraising/gifts
Resource example
https://yourInstance.salesforce.com/services/data/v/connect/fundraising/gifts
Available version
## 60.0
HTTP methods
## POST
Request body for POST
Note:  You can pass the campaign, donor, and designation IDs in an externalId object containing fieldName and
fieldValue.
JSON example
## {
"processingOptions":{
"donorOptions":{
"defaultUpdateLogic":"update_all"
## }
## },
## "gifts":[
## {
## "amount":150.25,
"currencyIsoCode":"USD",
"receivedDate":"2024-07-06",
"donorCoverAmount":0.25,
"transactionStatus":"Unpaid",
"commitmentId":"00x324303243fsfd",
"paymentIdentifier":"1234",
## 696
ResourcesFundraising

"gatewayTransactionFee":0.75,
"processorTransactionFee":0.45,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe
card’ssecuritycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"id":"0015500000WO1ZiAAL",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-432-1234",
## "email":"danielchavez@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## },
"paymentInstrument":{
## "type":"creditcard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Dinersclub",
"bankName":"chase",
"digitalWalletProvider":"Diner'sClub",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"centpro",
"processorPaymentReference":"string",
## 697
ResourcesFundraising

"gatewayReference":"string"
## },
## "designations":[
## {
"designationId":"0gd0030f0303024",
## "percent":10,
## "amount":150.25
## }
## ],
"giftTransactionCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredDetails of the request to create the gift.Create Gift Request
## Input[]
gifts
60.0OptionalOptions for the donor matching process.Processing Options
## Details Input
processing
## Options
Response body for POST
## Create Gift
## SEE ALSO:
## Nonprofit Cloud Developer Guide: Fundraising
Transactions Payment Updates (POST)
Update the gateway and processor metadata for gift transactions. This API supports updating only the properties that are specified in
the reuest body. If you include any other standard or custom fields in the request body beyond the specified properties, an error is shown.
## Resource
## /connect/fundraising/transactions/payment-updates
Resource example
https://yourInstance.salesforce.com/services/data/v/connect/fundraising/transactions/payment-updates
Available version
## 60.0
## 698
ResourcesFundraising

HTTP methods
## POST
Request body for POST
Note:  You can pass the transaction ID in an externalId object containing fieldName and fieldValue..
JSON example
## {
## "updates":[
## {
"giftTransactionId":"6TR5500000WO1ZIFGE",
"transactionStatus":"Unpaid",
"processorReference":"string",
"gatewayReference":"string",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe
card’ssecuritycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredContains the details of the request to
update the transaction payment.
## Transaction
## Payment Update
## Request Input[]
updates
Response body for POST
Transaction Payment Updates on page 746
## SEE ALSO:
## Nonprofit Cloud Developer Guide: Fundraising
Commitments Payment Updates (POST)
Update the metadata for your payment instruments for all active gift commitments.
## Resource
## /connect/fundraising/commitments/payment-updates
Resource example
https://yourInstance.salesforce.com/services/data/v/connect/fundraising/commitments/payment-updates
Available version
## 60.0
## 699
ResourcesFundraising

HTTP methods
## POST
Request body for POST
Note:  You can pass the commitment ID in an externalId object containing fieldName and fieldValue.
JSON example
## {
## "updates":[
## {
"giftCommitmentId":"6TR5500000WO1ZIFGE",
"paymentInstrument":{
"type":"Venmo",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"visa",
"bankName":"chase",
"digitalWalletProvider":"Diner'sClub",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## }
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredContains the request details to update
the commitment payment.
## Commitment
## Payment Updates
## Request Input[]
updates
Response body for POST
## Commitment Payment Updates
## SEE ALSO:
## Nonprofit Cloud Developer Guide: Fundraising
## 700
ResourcesFundraising

## Request Bodies
Learn more about the available Fundraising API request bodies.
## Address Details
Input representation of the donor's address details.
## Campaign Details Input
Input representation of the campaign that's associated with the gift transaction.
## Commitment Payment Updates Input
Input representation of the details of the payment update to the fundraising commitments.
## Commitment Payment Updates Request Input
Input representation of the details of the gift commitment and payment instrument.
## Create Commitment Input
Input representation of the request to create commitments.
## Create Commitment Request Input
Input representation of the request to create a recurring gift commitment. This request body accepts an array of commitment
requests. However, for the API version 60.0, up to 100 commitments is supported per request.<
## Create Gift Input
Input representation of the request to create gifts, including donor details, amount, and payment method.
## Create Gift Request Input
Input representation of the data required to create a new gift. This request body accepts both standard and custom fields for donor
account and gift transaction. If a standard field does not appear in the request body, you can include it in the customFields section
for the relevant object.
## Custom Field Details Input
Input representation of the custom fields for the request to incorporate custom attributes into records.
## Designation Details Input
Input representation of the designations that are associated with the request.
## Donor Details Input
Input representation of the donor details that’s associated with the gift transaction.
## Donor Options Details Input
Input representation of the available donor processing options that includes targeted update logic for the donor-related components
of the commitment transaction.
## Outreach Source Code Details Input
Input representation of the outreach source code that's associated with the request.
## Payment Instrument Details Input
Input representation of the payment instrument used for the request.
## Processing Options Details Input
Input representation of the donor processing options.
## Transaction Details Input
Input representation of the transaction details.
## 701
Request BodiesFundraising

## Transaction Payment Update Request Input
Input representation of the details of the gateway and processor metadata to update the transaction payment. If you include any
other standard or custom fields in the request body beyond the specified properties, an error is shown.
## Transaction Payment Updates Input
Input representation of the gateway and processor metadata to update the transaction payment. If you include any other standard
or custom fields in the request body beyond the specified properties, an error is shown.
## Update Commitment Input
Input representation of the request to update a commitment.
## Address Details
Input representation of the donor's address details.
JSON example
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredCity of the donor.Stringcity
60.0RequiredCountry of the donor.Stringcountry
60.0RequiredPostal code of the donor.StringpostalCode
60.0RequiredState of the donor.Stringstate
60.0RequiredStreet name of the donor.Stringstreet
## Campaign Details Input
Input representation of the campaign that's associated with the gift transaction.
JSON example
## {
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## }
## }
## 702
Request BodiesFundraising

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalID of the gift designation. This ID can also
be passed as an externalID in the
format given below:
## {
"externalId":{
## Stringid
"fieldName":
## "<EXTERNAL_ID_FIELD_NAME>",
"fieldValue":
## "<EXTERNAL_ID_FIELD_VALUE>"
## },
## Commitment Payment Updates Input
Input representation of the details of the payment update to the fundraising commitments.
JSON example
## {
## "updates":[
## {
"giftCommitmentId":"6TR5500000WO1ZIFGE",
"paymentInstrument":{
"type":"Venmo",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"visa",
"bankName":"chase",
"digitalWalletProvider":"Diner'sClub",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## }
## }
## ]
## }
## 703
Request BodiesFundraising

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredContains the request details to update the
commitment payment.
## Commitment
## Payment Updates
## Request Input[]
updates
## Commitment Payment Updates Request Input
Input representation of the details of the gift commitment and payment instrument.
JSON example
Note:  You can pass the campaign, donor, and designation IDs in an externalId object containing fieldName and
fieldValue.
## {
"giftCommitmentId":"6TR5500000WO1ZIFGE",
"paymentInstrument":{
"type":"Venmo",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"visa",
"bankName":"chase",
"digitalWalletProvider":"Diner'sClub",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredID of the gift commitment record for the
payment update. This ID can also be
## Stringgift
CommitmentId
passed as an externalID in the format
given below:
## {
"externalId":{
## 704
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
"fieldName":
## "<EXTERNAL_ID_FIELD_NAME>",
"fieldValue":
## "<EXTERNAL_ID_FIELD_VALUE>"
## },
60.0RequiredContains details about the payment
instrument.
## Payment Instrument
Details Input on
page 719
payment
## Instrument
## Create Commitment Input
Input representation of the request to create commitments.
JSON example
## {
"processingOptions":{
"donorOptions":{
"defaultUpdateLogic":"update_all"
## }
## },
## "commitments":[
## {
## "amount":150.25,
## "type":"pledge",
"currencyIsoCode":"USD",
"transactionPeriod":"monthly",
"transactionInterval":3,
"transactionDay":"5",
"startDate":"2024-07-06",
"endDate":"2024-07-06",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"id":"0015500000WO1ZxxAL",
"organizationName":"minicat town",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-432-9876",
## "email":"d.chavez.com",
## 705
Request BodiesFundraising

## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## },
"paymentInstrument":{
"type":"CreditCard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Diner'sClub",
"bankName":"chase",
"digitalWalletProvider":"EwalletProvider",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
## "designations":[
## {
"designationId":"0gd0030f0303024",
## "percent":10
## }
## ],
"firstTransaction":{
## "amount":150.25,
"receivedDate":"2024-07-06",
"donorCoverAmount":0.25,
"transactionStatus":"Unpaid",
"gatewayTransactionFee":0.75,
"processorTransactionFee":0.45,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe card’s
securitycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z"
## },
## 706
Request BodiesFundraising

"giftCommitmentCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"giftCommitmentScheduleCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"giftTransactionCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredDetails of the request to create the
commitment.
Limited to 100 commitments in a single
request.
## Create Commitment
## Request Input[]
commitments
60.0OptionalOptions for the donor matching process.Processing Options
## Details Input
processing
## Options
## Create Commitment Request Input
Input representation of the request to create a recurring gift commitment. This request body accepts an array of commitment requests.
However, for the API version 60.0, up to 100 commitments is supported per request.<
To include the standard fields for the donor account , use the Create Commitment Input request body to specify the standard fields.
JSON example
Note:  You can pass the campaign, donor, and designation IDs in an externalId object containing fieldName and
fieldValue.
## {
## "commitments":[
## {
## "amount":15,
## "type":"pledge",
"currencyIsoCode":"USD",
"transactionInterval":1,
"transactionDay":"1",
"startDate":"2023-11-01",
"endDate":"",
## 707
Request BodiesFundraising

"outreachSourceCode":{
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"id":"0015500000WO1ZixxL",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-432-1234",
## "email":"d.chavez@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Tardis",
"state":"NJ",
"postalCode":"08638",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## },
"paymentInstrument":{
"type":"CreditCard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Diner'sClub",
"bankName":"chase",
"digitalWalletProvider":"",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
## "designations":[
## {
"designationId":"0gd0030f0303xx4",
## "percent":0
## }
## ],
"firstTransaction":{
## "amount":15,
"receivedDate":"2023-11-02",
"donorCoverAmount":0.25,
## 708
Request BodiesFundraising

"transactionStatus":"Paid",
"gatewayTransactionFee":0.75,
"processorTransactionFee":0.045,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"",
"lastGatewayErrorMessage":"",
"lastGatewayProcessedDateTime":"2023-11-02T21:57:51Z"
## }
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalStandard and custom fields for the donor
account.
## Custom Field Details
## Input[]
accountCustomFields
60.0RequiredExpected amount of the gift transaction in
the commitment schedule.
## Doubleamount
60.0OptionalCampaign that's associated with the
commitment.
## Campaign Details
## Input
campaign
60.0OptionalCurrency ISO code for the commitment.Stringcurrency
IsoCode
60.0OptionalDefault gift designations that are
associated with the commitment.
## Designation Details
## Input[]
designations
60.0RequiredPerson, household, or organization
account that's associated with the
commitment.
## Donor Details Inputdonor
60.0RequiredDate when the total amount of the
commitment is expected to be paid. The
default format is YYYY-MM-DD.
StringendDate
60.0OptionalFirst transaction of the commitment. Note:
When type is pledge, this property
cannot be included.
## Transaction Details
## Input
first
## Transaction
60.0OptionalStandard and custom fields of the gift
commitment.
## Custom Field Details
## Input[]
giftCommitment
CustomFields
60.0OptionalStandard and custom fields of the gift
commitment schedule.
## Custom Field Details
## Input[]
giftCommitment
## Schedule
CustomFields
60.0OptionalCustom fields for the gift transaction. The
giftTransactionCustomFields property also
## Custom Field Details
## Input[]
giftTransaction
CustomFields
## 709
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
accepts the standard fields for the gift
transaction.
60.0OptionalOutreach source code that's associated
with the campaign for the gift
commitment schedule.
## Outreach Source
## Code Details Input
outreach
SourceCode
60.0RequiredPayment instrument that's used to
complete the transaction.
## Payment Instrument
## Details Input
payment
## Instrument
60.0OptionalReference number of the commitment
that was assigned by the processor.
## Stringpayment
## Processor
CommitmentId
60.0RequiredDate from when the commitment is in
effect. The default format is
## YYYY-MM-DD.
StringstartDate
60.0OptionalDay of the month to create gift transaction
in the future for a monthly transaction
## Stringtransaction
## Day
period. If you select the day as 29 or 30,
the gift transaction is created on the last
day for months that don't have that many
days.
60.0OptionalTransaction interval that's applicable to the
incoming transaction in the commitment.
## Integertransaction
## Interval
60.0RequiredTransaction period that's applicable to the
incoming transaction in the commitment.
## Stringtransaction
## Period
When type is pledge, this property
must be set to Custom. If
transactionPeriod is not
provided, the default isCustom.
62.0OptionalType of transaction. Possible values are:Stringtype
## •
## Pledge
## •
## Recurring
The default value is the Recurring.
## Create Gift Input
Input representation of the request to create gifts, including donor details, amount, and payment method.
JSON example
## {
"processingOptions":{
"donorOptions":{
## 710
Request BodiesFundraising

"defaultUpdateLogic":"update_all"
## }
## },
## "gifts":[
## {
## "amount":150.25,
"currencyIsoCode":"USD",
"receivedDate":"2024-07-06",
"donorCoverAmount":0.25,
"transactionStatus":"Unpaid",
"commitmentId":"00x324303243fsfd",
"paymentIdentifier":"1234",
"gatewayTransactionFee":0.75,
"processorTransactionFee":0.45,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe card’s
securitycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"id":"0015500000WO1ZiAAL",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-432-1234",
## "email":"danielchavez@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## },
"paymentInstrument":{
## "type":"creditcard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
## 711
Request BodiesFundraising

"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Dinersclub",
"bankName":"chase",
"digitalWalletProvider":"Diner'sClub",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
## "designations":[
## {
"designationId":"0gd0030f0303024",
## "percent":10,
## "amount":150.25
## }
## ],
"giftTransactionCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredDetails of the request to create the gift.Create Gift Request
## Input[]
gifts
60.0OptionalOptions for the donor matching process.Processing Options
## Details Input
processing
## Options
## Create Gift Request Input
Input representation of the data required to create a new gift. This request body accepts both standard and custom fields for donor
account and gift transaction. If a standard field does not appear in the request body, you can include it in the customFields section for
the relevant object.
JSON example
## {
## "gifts":[
## {
## "amount":150.25,
## 712
Request BodiesFundraising

"currencyIsoCode":"USD",
"receivedDate":"2024-07-06",
"donorCoverAmount":0.25,
"transactionStatus":"Unpaid",
"commitmentId":"00x324303243fsfd",
"paymentIdentifier":"1234",
"gatewayTransactionFee":0.75,
"processorTransactionFee":0.45,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe card’s
securitycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"id":"0015500000WO1ZixxL",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-432-1234",
## "email":"example@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## },
"paymentInstrument":{
## "type":"creditcard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"visa",
"bankName":"chase",
"digitalWalletProvider":"Diner'sClub",
"bankAccountHolderType":"primary",
## 713
Request BodiesFundraising

"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"OptiSynth",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
## "designations":[
## {
"designationId":"0gd0030f0303024",
## "percent":10,
## "amount":150.25
## }
## ],
"giftTransactionCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalCustom fields for the donor account. The
accountCustomFields property
## Custom Field Details
## Input[]
accountCustomFields
aslo accepts the standard fields for the
donor account.
60.0RequiredOriginal amount of the gift transaction.Doubleamount
60.0OptionalCampaign that's associated with the gift
transaction.
## Campaign Details
## Input
campaign
60.0OptionalGift commitment ID that's associated with
the gift transaction.
StringcommitmentId
60.0OptionalISO code of the currency.Stringcurrency
IsoCode
60.0OptionalDesignations that are associated with the
gift transaction.
## Designation Details
## Input[]
designations
60.0RequiredDonor details that are associated with the
gift transaction.
## Donor Details Inputdonor
60.0OptionalAmount that the donor added to their gift
to cover fees.
DoubledonorCover
## Amount
## 714
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalReference of the transaction to which the
gateway is assigned.
## Stringgateway
## Reference
60.0OptionalTransaction fees charged by the gateway.Doublegateway
TransactionFee
60.0OptionalCustom fields for the gift transaction. The
giftTransactionCustomFields
## Custom Field Details
## Input[]
giftTransaction
CustomFields
property also accepts the standard fields
for the gift transaction.
60.0OptionalMost recent error message received by the
gateway.
StringlastGateway
ErrorMessage
60.0OptionalLast attempt made by the gateway.StringlastGateway
ProcessedDate
## Time
60.0OptionalMost recent response code that was
received by the gateway.
StringlastGateway
ResponseCode
60.0OptionalOutreach source code that's associated
with the gift transaction.
## Outreach Source
## Code Details Input
outreach
SourceCode
60.0OptionalUnique ID for the payment transaction.Stringpayment
## Identifier
60.0RequiredPayment instrument used for the gift
transaction.
## Payment Instrument
## Details Input
payment
## Instrument
60.0OptionalReference of the transaction to which the
payment processor is assigned.
## Stringprocessor
## Reference
60.0OptionalTransaction fees charged by the processor.Doubleprocessor
## Transaction
## Fee
60.0RequiredDate when the donor completed the gift
transaction.
StringreceivedDate
60.0RequiredStatus of the gift transaction.Stringtransaction
## Status
## Custom Field Details Input
Input representation of the custom fields for the request to incorporate custom attributes into records.
You can include the standard fields such as Description, EffectiveStartDate, and more in this request body. To include the standard fields
in the request body, specify the API name of the standard field as the value of the fieldName property, and provide the value for
the standard field in the fieldValue property.
## 715
Request BodiesFundraising

JSON example
This example shows a sample request that includes a standard field.
## {
"fieldName":"effectiveStartDate",
"fieldValue":"2024-05-06"
## }
This example shows a sample request that includes a custom field.
## {
"fieldName":"TShirtSize__c",
"fieldValue":"Medium"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalAPI name of the custom or standard field.StringfieldName
60.0OptionalValue of the custom or standard field.ObjectfieldValue
## Designation Details Input
Input representation of the designations that are associated with the request.
JSON example
## {
## "designations":{
## "id":"0gd0030f0303xx4",
## "amount":150.25,
## "percent":10
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalTransaction amount that's allocated to the
designation, which is for gifts only.
## Doubleamount
60.0OptionalID of the gift designation. This ID can also
be passed as an externalID in the
format given below:
## {
"externalId":{
## Stringid
"fieldName":
## "<EXTERNAL_ID_FIELD_NAME>",
## 716
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
"fieldValue":
## "<EXTERNAL_ID_FIELD_VALUE>"
## },
60.0OptionalPercentage of the transaction or
commitment amount that's allocated to
the designation.
## Doublepercent
## Donor Details Input
Input representation of the donor details that’s associated with the gift transaction.
JSON example
## {
"donorType":"individual",
"id":"0015500000WO1ZiAAL",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-434-8920",
## "email":"d.chavez@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalAccount standard and custom fields of the
donor.
## Custom Field Details
## Input[]
account
CustomFields
## 717
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalAddress details of the donor.Address Details
## Input[]
address
60.0RequiredType of the donor.
You can’t use the
organizationName when the
StringdonorType
donorType is set to Individual.
Similarly, don’t use firstName or
lastName properties when the
donorType is Organizational.
60.0OptionalEmail address of the donor.Stringemail
60.0RequiredFirst name of the donor.StringfirstName
60.0OptionalID of the gift designation. This ID can also
be passed as an externalID in the
format given below:
## {
"externalId":{
## Stringid
"fieldName":
## "<EXTERNAL_ID_FIELD_NAME>",
"fieldValue":
## "<EXTERNAL_ID_FIELD_VALUE>"
## }
60.0RequiredLast name of the donor.StringlastName
60.0RequiredOrganization name of the donor.Stringorganization
## Name
60.0OptionalPhone number of the donor.Stringphone
## Donor Options Details Input
Input representation of the available donor processing options that includes targeted update logic for the donor-related components
of the commitment transaction.
JSON example
"donorOptions":{
"defaultUpdateLogic":"update_all"
## }
## 718
Request BodiesFundraising

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalDefault update value for the donor
updates. Valid values are:
## Stringdefault
UpdateLogic
## •
update_all- If an existing donor
is matched (whether by a record ID,
external ID, or Duplicate Rules), any
donor properties that are provided are
updated on the matched donor's
account, including any custom
account field mappings.
## •
no_update- If an existing donor is
matched (whether by a record ID,
external ID, or Duplicate Rules), none
of the donor properties that are
provided are updated on the matched
donor’s account, including any custom
account field mappings.
## Outreach Source Code Details Input
Input representation of the outreach source code that's associated with the request.
JSON example
## {
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalID of the outreach source code.Stringid
60.0OptionalUnique code associated with the outreach
source.
StringsourceCode
## Payment Instrument Details Input
Input representation of the payment instrument used for the request.
JSON example
## {
"type":"CreditCard",
## 719
Request BodiesFundraising

"accountHolderName":"DianaGómez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Diner'sClub",
"bankName":"chase",
"digitalWalletProvider":"",
"bankAccountHolderType":"",
"bankAccountType":"",
"bankAccountNumber":"",
"bankCode":"",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalName of the payment instrument holder.Stringaccount
HolderName
60.0OptionalSpecifies if the bank account holder is an
individual or a company.
StringbankAccount
HolderType
60.0OptionalBank account number associated with the
payment instrument.
StringbankAccount
## Number
60.0OptionalType of the bank account.StringbankAccount
## Type
60.0OptionalCode of the bank that's associated with
the bank account.
StringbankCode
60.0OptionalBank name that’s associated with the bank
account.
StringbankName
60.0OptionalBrand, network, or issuer of the credit card.StringcardBrand
60.0OptionalProvider of the digital wallet.Stringdigital
WalletProvider
60.0OptionalExpiration month if the payment method
is credit card.
StringexpiryMonth
60.0OptionalExpiration year if the payment method is
credit card.
StringexpiryYear
60.0OptionalName of the payment gateway.StringgatewayName
60.0OptionalReference number of the gateway for this
payment instrument.
## Stringgateway
## Reference
## 720
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalLast four digits of the account number for
the payment method.
## Stringlast4
60.0OptionalName of the payment processor.StringprocessorName
60.0OptionalReference of the payment processor that's
associated with the payment instrument.
## Stringprocessor
## Payment
## Reference
60.0RequiredType of the payment instrument used for
the request.
## Stringtype
## Processing Options Details Input
Input representation of the donor processing options.
JSON example
## {
"processingOptions":{
"donorOptions":{
"defaultUpdateLogic":"update_all"
## }
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalDonor processing options to create gift
commitments.
## Donor Options
## Details Input
donorOptions
## Transaction Details Input
Input representation of the transaction details.
JSON example
## {
## "amount":150.25,
"receivedDate":"2024-07-06",
"donorCoverAmount":0.25,
"transactionStatus":"Unpaid",
"gatewayTransactionFee":0.75,
"processorTransactionFee":0.45,
"processorReference":"cls-1247586928747",
"gatewayReference":"102656693ac3ca6e0cdafbfe89ab99",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe card’s
## 721
Request BodiesFundraising

securitycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalOriginal amount of the gift transaction.Doubleamount
60.0OptionalAmount that the donor added to their gift
to cover fees.
## Doubledonor
CoverAmount
60.0OptionalReference of the transaction to which the
gateway is assigned.
## Stringgateway
## Reference
60.0OptionalTransaction fees charged by the gateway.Doublegateway
TransactionFee
60.0OptionalMost recent error message received by the
gateway.
StringlastGateway
ErrorMessage
60.0OptionalLast attempt made by the gateway.StringlastGatewayProcessedDateTime
60.0OptionalMost recent response code that was
received by the gateway.
StringlastGateway
ResponseCode
60.0OptionalReference of the transaction to which the
payment processor is assigned.
## Stringprocessor
## Reference
60.0OptionalTransaction fees charged by the processor.Doubleprocessor
TransactionFee
60.0OptionalDate when the donor completed the gift
transaction.
StringreceivedDate
60.0OptionalTransaction status of the gift.Stringtransaction
## Status
## Transaction Payment Update Request Input
Input representation of the details of the gateway and processor metadata to update the transaction payment. If you include any other
standard or custom fields in the request body beyond the specified properties, an error is shown.
JSON example
## {
"giftTransactionId":"6TR5500000WO1ZIxxE",
"transactionStatus":"Unpaid",
"processorReference":"string",
"gatewayReference":"string",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe card’s
securitycodeor use a differentcard.",
## 722
Request BodiesFundraising

"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z"
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalReference of the transaction to which the
gateway is assigned.
## Stringgateway
## Reference
60.0RequiredID of the gift transaction record. This ID can
also be passed as an externalID in
the format given below:
## {
"externalId":{
## Stringgift
TransactionId
"fieldName":
## "<EXTERNAL_ID_FIELD_NAME>",
"fieldValue":
## "<EXTERNAL_ID_FIELD_VALUE>"
## }
60.0OptionalMost recent error message received by the
gateway.
StringlastGateway
ErrorMessage
60.0OptionalLast attempt made by the gateway.StringlastGateway
## Processed
DateTime
60.0OptionalMost recent response code that was
received by the gateway.
StringlastGateway
ResponseCode
60.0OptionalReference of the transaction to which the
payment processor is assigned.
## Stringprocessor
## Reference
60.0RequiredGift status of the transaction.Stringtransaction
## Status
## Transaction Payment Updates Input
Input representation of the gateway and processor metadata to update the transaction payment. If you include any other standard or
custom fields in the request body beyond the specified properties, an error is shown.
JSON example
## {
## "updates":[
## {
"giftTransactionId":"6TR5500000WO1ZIFGE",
## 723
Request BodiesFundraising

"transactionStatus":"Unpaid",
"processorReference":"string",
"gatewayReference":"string",
"lastGatewayResponseCode":"invalid_cvc",
"lastGatewayErrorMessage":"Thecard’ssecuritycodeis invalid.Checkthe card’s
securitycodeor use a differentcard.",
"lastGatewayProcessedDateTime":"2023-07-06T21:57:51Z"
## }
## ]
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredContains the details of the request to
update the transaction payment.
## Transaction
## Payment Update
## Request Input[]
updates
## Update Commitment Input
Input representation of the request to update a commitment.
JSON example
## {
## "amount":150.25,
## "type":"pledge",
"transactionInterval":3,
"transactionDay":"5",
"startDate":"2024-07-06",
"endDate":"2024-07-06",
## "campaign":{
## "id":"701y0030d0zk6t06f4"
## },
"outreachSourceCode":{
"id":"0gx000d0d0d0FD",
"sourceCode":"AnimalEmailCampaign2023"
## },
## "donor":{
"donorType":"individual",
"organizationName":"ABCInc.",
"firstName":"Daniel",
"lastName":"Chavez",
## "phone":"510-434-8920",
## "email":"d.chavez@salesforce.com",
## "address":[
## {
"street":"123MainStreet",
"city":"Oakland",
"state":"CA",
"postalCode":"94610",
"country":"US"
## 724
Request BodiesFundraising

## }
## ],
"accountCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"paymentInstrument":{
"type":"CreditCard",
"accountHolderName":"DanielChavez",
"expiryMonth":"10",
"expiryYear":"2026",
## "last4":"4321",
"cardBrand":"Diner'sClub",
"bankName":"chase",
"digitalWalletProvider":"EProvider",
"bankAccountHolderType":"primary",
"bankAccountType":"checking",
"bankAccountNumber":"123456",
"bankCode":"HBUK",
"gatewayName":"Gateway",
"processorName":"Centpro",
"processorPaymentReference":"string",
"gatewayReference":"string"
## },
"giftCommitmentCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ],
"giftCommitmentScheduleCustomFields":[
## {
"fieldName":"string",
"fieldValue":"string"
## }
## ]
## }
## }
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0RequiredGift amount of each transaction associated
with the gift commitment schedule.
## Doubleamount
60.0OptionalCampaign that's associated with the gift
commitment.
## Campaign Detailscampaign
60.0OptionalCurrency ISO code of the gift commitment.Stringcurrency
IsoCode
## 725
Request BodiesFundraising

## Available
## Version
Required or
## Optional
DescriptionTypeName
60.0OptionalPerson, household, or organization
account associated with the commitment.
Donor Details InputdonorId
60.0OptionalEnd date of the new schedule for this gift
commitment. The format is
## YYYY-MM-DD.
StringendDate
60.0OptionalCustom fields of the gift commitment.Custom Field
## Details[]
giftCommitment
CustomFields
60.0OptionalCustom fields of the gift commitment
schedule.
## Custom Field
## Details[]
giftCommitment
## Schedule
CustomFields
60.0OptionalOutreach source code that's associated
with the campaign for the gift
commitment.
## Outreach Source
## Code Details
outreach
SourceCode
60.0RequiredPayment instrument that's used to
complete the transaction.
## Payment Instrument
## Details
payment
## Instrument
60.0RequiredStart date of the new schedule for this gift
commitment. The format is
## YYYY-MM-DD.
StringstartDate
60.0OptionalSpecifies the day of the month to create
gift transactions in the future for a monthly
## Stringtransaction
## Day
transaction period. If you select the day as
29 or 30, the gift transaction is created on
the last day for the months that don't have
that many days.
60.0OptionalTransaction interval that's applicable to an
incoming transaction in the commitment.
## Integertransaction
## Interval
60.0RequiredTransaction period that's applicable to the
incoming transaction in the commitment.
## Stringtransaction
## Period
When type is pledge, this property
must be set to Custom. If
transactionPeriod is not
provided, the default isCustom.
62.0OptionalType of transaction. Possible values are:Stringtype
## •
## Pledge
## •
## Recurring
The default value is the Recurring.
## 726
Request BodiesFundraising

## Response Bodies
Learn more about the available Fundraising API response bodies.
## Commitment Payment Updates
Output representation of the request to update the commitment payment for a fundraising commitment.
## Commitment Payment Updates
Output representation of the updates for the commitment payment.
## Commitment Payment Updates Response Link
Output representation of the links to the response object for the commitment payment updates.
## Create Commitment
Output representation of the fundraising commitment request that contains the commitment ID and associated links.
## Create Commitment Response Details
Output representation of the create commitment result with success status code, error, if any, and associated object links.
## Create Commitment Response Link
Output representation of the links to the response object.
## Create Gift
Output representation of the details of the created gift transaction response.
## Create Gift Response Details
Output representation of the request details to create the gift.
## Create Gift Response Link
Output representation of the links to the response object.
## Error Details
Output representation of the errors encountered during an API request.
## Gift Campaign Default Designations Output
Output representation of a list of default designations associated with a gift campaign record.
## Gift Campaign Default Designation Record Output
Output representation of a default designation record associated with a gift campaign.
## Gift Commitment Default Designations Output
Output representation of a list of default designations associated with a gift commitment.
## Gift Commitment Default Designation Record Output
Output representation of a default designation record associated with a gift commitment.
## Gift Commitment Transaction Matching Output
Output representation of a list of gift transactions.
## Gift Transactions Output
Output representation of the gift transactions associated with a gift commitment record.
## Gift Transaction Linked Designations Output
Output representation of a list of gift designations.
## Gift Transaction Record Output
Output representation of a gift transaction record.
## 727
Response BodiesFundraising

## Gift Designation Record Output
Output representation of a gift designation record.
## Link Details
Output representation of the link details for the response object.
## Transaction Payment Updates
Output representation of the transaction payment updates.
## Transaction Payment Updates Response
Output representation of the updates for the transaction payment.
## Transaction Payment Updates Response Link
Output representation of the links to the response object for the transaction payment updates.
## Update Commitment
Output representation of the update commitment request that contains the status, errors if any, and the links to objects after you
update a gift commitment.
## Update Commitment Response Link
Output representation of the links to the response object for the commitment updates.
## Commitment Payment Updates
Output representation of the request to update the commitment payment for a fundraising commitment.
## Sample Response
## {
## "successes":0,
## "failures":0,
"notProcessed":0,
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
## 728
Response BodiesFundraising

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Contains the response of the commitment
payment update.
## Commitment
## Payment Updates[]
on page 729
details
60.0Small, 60.0Number of gift commitments that failed to
be updated.
## Integerfailures
60.0Small, 60.0Number of gift commitments that weren't
processed.
IntegernotProcessed
60.0Small, 60.0Number of gift commitments that were
updated.
## Integersuccesses
## Commitment Payment Updates
Output representation of the updates for the commitment payment.
## Sample Response
## {
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Error message if a process failed.Error Details[]errors
60.0Small, 60.0Links to the response object.Commitment
## Payment Updates
## Response Link
links
## 729
Response BodiesFundraising

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Indicates whether the request was
processed successfully (true) or not
## (false).
## Booleansuccess
## Commitment Payment Updates Response Link
Output representation of the links to the response object for the commitment payment updates.
## Sample Response
## {
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Link to the gift commitment response.Link Detailsgift
commitment
60.0Small, 60.0Link to the first payment instrument
response.
## Link Detailspayment
instrument
## Create Commitment
Output representation of the fundraising commitment request that contains the commitment ID and associated links.
## Sample Response
## {
## "successes":0,
## "failures":0,
"notProcessed":0,
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## 730
Response BodiesFundraising

## ],
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitmentschedule":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftdefaultdesignation":[
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## ],
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "account":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Contains the response to the create
commitment request.
## Create Commitment
## Response Details[]
details
60.0Small, 60.0Number of commitments that failed to be
created.
## Integerfailures
60.0Small, 60.0Number of commitments that weren't
processed.
IntegernotProcessed
60.0Small, 60.0Number of successful commitments that
were created.
## Integersuccesses
## Create Commitment Response Details
Output representation of the create commitment result with success status code, error, if any, and associated object links.
## 731
Response BodiesFundraising

## Sample Response
## {
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitmentschedule":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftdefaultdesignation":[
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## ],
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "account":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Details of the error if the request failed to
process.
## Error Details[]errors
60.0Small, 60.0Links to the response object.Create Commitment
## Response Link
links
## 732
Response BodiesFundraising

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Indicates whether the request was
processed successfully (true) or not
## (false).
## Booleansuccess
## Create Commitment Response Link
Output representation of the links to the response object.
## Sample Response
## {
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitmentschedule":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftdefaultdesignation":[
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## ],
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "account":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Link to the donor account.Link Detailsaccount
60.0Small, 60.0Link to the gift commitment response.Link Detailsgiftcommitment
60.0Small, 60.0Link to the gift commitment schedule
response.
## Link Detailsgiftcommitment
schedule
## 733
Response BodiesFundraising

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Link to the gift default designation response.Link Details[]giftdefault
designation
60.0Small, 60.0Link to the first gift transaction response.Link Detailsgift
transaction
60.0Small, 60.0Link to the first payment instrument
response.
## Link Detailspayment
instrument
## Create Gift
Output representation of the details of the created gift transaction response.
## Sample Response
## {
## "successes":0,
## "failures":0,
"notProcessed":0,
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "account":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "gifttransactiondesignation":[
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## ],
## 734
Response BodiesFundraising

## "campaign":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "outreachsourcecode":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Contains the details of the gift response.Create Gift Response
## Details[]
details
60.0Small, 60.0Number of transactions that failed to be
created.
## Integerfailures
60.0Small, 60.0Number of transactions that weren’t
processed.
IntegernotProcessed
60.0Small, 60.0Number of transactions that were created.Integersuccesses
## Create Gift Response Details
Output representation of the request details to create the gift.
## Sample Response
## {
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "account":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## 735
Response BodiesFundraising

## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "gifttransactiondesignation":[
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## ],
## "campaign":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "outreachsourcecode":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Details of the error if the request failed to
process.
## Error Details[]errors
60.0Small, 60.0Links to the response object.Create Gift Response
## Link
links
60.0Small, 60.0Indicates whether the request was
processed successfully (true) or not
## (false).
## Booleansuccess
## Create Gift Response Link
Output representation of the links to the response object.
## Sample Response
## {
## "links":{
## "account":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## 736
Response BodiesFundraising

## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "paymentinstrument":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "gifttransactiondesignation":[
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## ],
## "campaign":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "outreachsourcecode":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Link to the donor account.Link Detailsaccount
60.0Small, 60.0Link to the gift commitment response.Link Detailsgift
commitment
60.0Small, 60.0Link to the gift transaction response.Link Detailsgift
transaction
60.0Small, 60.0Link to the gift transaction designations.Link Detailsgifttransaction
designation
60.0Small, 60.0Link to the payment instrument response.Link Detailspayment
instrument
## Error Details
Output representation of the errors encountered during an API request.
## Sample Response
## {
## "errors":{
## "field":"string",
## "message":"string"
## }
## }
## 737
Response BodiesFundraising

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Name of the field that has errors.Stringfield
60.0Small, 60.0Error message for the failed process.Stringmessage
## Gift Campaign Default Designations Output
Output representation of a list of default designations associated with a gift campaign record.
JSON example
## {{
"campaignDefaultDesignations":[
## {
"designationId":"6gdRM000000000LYAQ",
"designationName":"DefaultDesignation",
## "percent":50
## },
## {
"designationId":"6gdxx000004WhULAA0",
"designationName":"OtherDesignation",
## "percent":50
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0List of default gift designations associated
with a gift campaign record.
## Gift Campaign
## Default Designation
## Record Output[]
campaignDefaultDesignations
## Gift Campaign Default Designation Record Output
Output representation of a default designation record associated with a gift campaign.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0ID of the default gift designation record.StringdesignationId
66.0Small, 66.0The name of the gift designationStringdesignationName
59.0Small, 59.0Percentage value of the default gift
designation record.
## Doublepercentage
## Gift Commitment Default Designations Output
Output representation of a list of default designations associated with a gift commitment.
## 738
Response BodiesFundraising

JSON example
## {
"commitmentDefaultDesignations":[
## {
"designationId":"6idRM000000000LYAQ",
## "percent":100
## },
## {
"designationId":"6gaxx000004WhULAA0",
## "percent":50
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0List of default gift designations associated
with a gift commitment.
## Gift Commitment
## Default Designation
## Record Output []
commitmentDefaultDesignations
## Gift Commitment Default Designation Record Output
Output representation of a default designation record associated with a gift commitment.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0ID of the default gift designation record.StringdesignationId
66.0Small, 66.0The name of the gift designationStringdesignationName
59.0Small, 59.0Percentage value of the default gift
designation record.
## Doublepercentage
## Gift Commitment Transaction Matching Output
Output representation of a list of gift transactions.
JSON example
## {
"giftTransactions":[
## {
## "fields":[
## {
"fieldApiName":"GiftCommitmentId",
"label":"GiftCommitmentID",
"type":"String",
"value":"6gcRM0000004CD0YAM"
## },
## {
## 739
Response BodiesFundraising

"fieldApiName":"Id",
"label":"GiftTransactionID",
"type":"String",
"value":"6trRM00000000CwYAI"
## },
## {
"fieldApiName":"Name",
"label":"Name",
"type":"String",
"value":"TomC3 - Tom C3 GT 7"
## },
## {
"fieldApiName":"GiftType",
"label":"GiftType",
"type":"String",
"value":"Individual"
## },
## {
"fieldApiName":"TransactionDueDate",
"label":"TransactionDue Date",
"type":"DateOnlyWrapper",
"value":"ThuAug 31 00:00:00GMT 2023"
## },
## {
"fieldApiName":"DonorId",
"label":"DonorID",
"type":"String",
"value":"001RM000005bZRUYA2"
## },
## {
"fieldApiName":"OwnerId",
"label":"OwnerID",
"type":"String",
"value":"005RM0000027gL8YAI"
## },
## {
"fieldApiName":"RefundedAmount",
"label":"RefundedAmount",
"type":"Double",
## "value":"0.0"
## },
## {
"fieldApiName":"Status",
"label":"Status",
"type":"String",
"value":"Unpaid"
## },
## {
"fieldApiName":"IsDeleted",
"label":"Deleted",
"type":"Boolean",
## "value":"false"
## },
## {
## 740
Response BodiesFundraising

"fieldApiName":"IsPartiallyRefunded",
"label":"PartiallyRefunded",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"CurrentAmount",
"label":"CurrentAmount",
"type":"Double",
"value":"2.2222222E7"
## },
## {
"fieldApiName":"AcknowledgementStatus",
"label":"AcknowledgementStatus",
"type":"String",
"value":"ToBe Sent"
## },
## {
"fieldApiName":"OriginalAmount",
"label":"OriginalAmount",
"type":"Double",
"value":"2.2222222E7"
## },
## {
"fieldApiName":"IsWrittenOff",
"label":"WrittenOff",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"IsFullyRefunded",
"label":"FullyRefunded",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"PaymentMethod",
"label":"PaymentMethod",
"type":"String",
"value":"Cash"
## },
## {
"fieldApiName":"IsPaid",
"label":"Paid",
"type":"Boolean",
## "value":"false"
## }
## ],
"objectApiName":"GiftTransaction"
## },
## {
## "fields":[
## {
"fieldApiName":"GiftCommitmentId",
## 741
Response BodiesFundraising

"label":"GiftCommitmentID",
"type":"String",
"value":"6gcRM0000004CD0YAM"
## },
## {
"fieldApiName":"Id",
"label":"GiftTransactionID",
"type":"String",
"value":"6trRM00000000CxYAI"
## },
## {
"fieldApiName":"Name",
"label":"Name",
"type":"String",
"value":"TomC3 - Tom C3 GT 6"
## },
## {
"fieldApiName":"GiftType",
"label":"GiftType",
"type":"String",
"value":"Individual"
## },
## {
"fieldApiName":"TransactionDueDate",
"label":"TransactionDue Date",
"type":"DateOnlyWrapper",
"value":"WedAug 30 00:00:00GMT 2023"
## },
## {
"fieldApiName":"DonorId",
"label":"DonorID",
"type":"String",
"value":"001RM000005bZRUYA2"
## },
## {
"fieldApiName":"OwnerId",
"label":"OwnerID",
"type":"String",
"value":"005RM0000027gL8YAI"
## },
## {
"fieldApiName":"RefundedAmount",
"label":"RefundedAmount",
"type":"Double",
## "value":"0.0"
## },
## {
"fieldApiName":"Status",
"label":"Status",
"type":"String",
"value":"Unpaid"
## },
## {
"fieldApiName":"IsDeleted",
## 742
Response BodiesFundraising

"label":"Deleted",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"IsPartiallyRefunded",
"label":"PartiallyRefunded",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"CurrentAmount",
"label":"CurrentAmount",
"type":"Double",
## "value":"11111.0"
## },
## {
"fieldApiName":"AcknowledgementStatus",
"label":"AcknowledgementStatus",
"type":"String",
"value":"ToBe Sent"
## },
## {
"fieldApiName":"OriginalAmount",
"label":"OriginalAmount",
"type":"Double",
## "value":"11111.0"
## },
## {
"fieldApiName":"IsWrittenOff",
"label":"WrittenOff",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"IsFullyRefunded",
"label":"FullyRefunded",
"type":"Boolean",
## "value":"false"
## },
## {
"fieldApiName":"PaymentMethod",
"label":"PaymentMethod",
"type":"String",
"value":"Cash"
## },
## {
"fieldApiName":"IsPaid",
"label":"Paid",
"type":"Boolean",
## "value":"false"
## }
## ],
"objectApiName":"GiftTransaction"
## 743
Response BodiesFundraising

## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0List of gift transactions associated with a gift
commitment.
## Standard Object
## Details[]
giftTransactions
## Gift Transactions Output
Output representation of the gift transactions associated with a gift commitment record.
JSON examples
Here’s an example of a list of future gift transactions.
## {
"giftTransactions":[
## {
## "amount":9999,
"commitmentId":"6gcxx000004WhULAA0",
"commitmentScheduleId":"6csxx000004WhULAA0",
"paymentMethod":"Cash",
"transactionDate":"2023-09-01T00:00:00.000Z"
## },
## {
## "amount":2099,
"commitmentId":"6gcxx000004WhULAA0",
"commitmentScheduleId":"6csxx000004UhUMAB0",
"paymentMethod":"Cash",
"transactionDate":"2023-10-01T00:00:00.000Z"
## }
## ]
## }
Here’s an example of a list of past gift transactions.
## {
"giftTransactions":[
## {
## "amount":9999,
"commitmentId":"6gcxx000004WhULAA0",
"commitmentScheduleId":"6csxx000004WhULAA0",
"paymentMethod":"Cash",
"status":"Canceled"
## },
## {
## "amount":2099,
"commitmentId":"6gcxx000004WhULAA0",
"commitmentScheduleId":"6csxx000004UhUMAB0",
"paymentMethod":"Cash",
"status":"Canceled"
## 744
Response BodiesFundraising

## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0List of gift transactions associated with a gift
commitment record.
## Gift Transaction
## Record Output[]
gift
## Transactions
## Gift Transaction Linked Designations Output
Output representation of a list of gift designations.
JSON example
## {
"transactionLinkedDesignations":[
## {
## "amount":100,
"designationId":"6gdRM000000000LYAQ",
## "percent":100
## },
## {
## "amount":100,
"designationId":"6gcxx000004WhULAA0",
## "percent":50
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0List of designations.Gift Designation
## Record Output[]
transactionLinkedDesignations
## Gift Transaction Record Output
Output representation of a gift transaction record.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0Transaction amount.Doubleamount
59.0Small, 59.0ID of the gift commitment record.StringcommitmentId
59.0Small, 59.0ID of the gift commitment schedule record.Stringcommitment
ScheduleId
59.0Small, 59.0Mode of payment for the transaction.StringpaymentMethod
## 745
Response BodiesFundraising

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0Status of the transaction.
This field is not applicable for future
transactions.
## Stringstatus
59.0Small, 59.0Payment due date.
This field is applicable only for future
transactions.
## Stringtransaction
## Date
## Gift Designation Record Output
Output representation of a gift designation record.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
59.0Small, 59.0Amount value of the designation record.Doubleamount
59.0Small, 59.0ID of the designation record.StringdesignationId
59.0Small, 59.0Percentage value of the designation record.Doublepercent
## Link Details
Output representation of the link details for the response object.
## Sample Response
## {
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Object link that provides the direct access
to the resource.
## Stringhref
60.0Small, 60.0Salesforce ID of the linked resource.Stringid
## Transaction Payment Updates
Output representation of the transaction payment updates.
## Sample Response
## {
## "successes":0,
## 746
Response BodiesFundraising

## "failures":0,
"notProcessed":0,
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Payment update response of the
transaction.
## Transaction Payment
## Updates Response[]
details
60.0Small, 60.0Number of gift transactions that failed to
update.
## Integerfailures
60.0Small, 60.0Number of gift transactions that weren't
processed.
IntegernotProcessed
60.0Small, 60.0Number of gift transactions that were
updated.
## Integersuccesses
## Transaction Payment Updates Response
Output representation of the updates for the transaction payment.
## Sample Response
## {
## "details":[
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## ],
## "links":{
## "gifttransaction":{
## 747
Response BodiesFundraising

"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
## ]
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Error message if a process failed.Error Details[]errors
60.0Small, 60.0Links to the response object.Transaction Payment
## Updates Response
## Link
links
60.0Small, 60.0Indicates whether a request was processed
successfully (true) or not (false).
## Booleansuccess
## Transaction Payment Updates Response Link
Output representation of the links to the response object for the transaction payment updates.
## Sample Response
## {
## "gifttransaction":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Link to the gift transaction details.Link Detailsgift
transaction
## Update Commitment
Output representation of the update commitment request that contains the status, errors if any, and the links to objects after you update
a gift commitment.
## Sample Response
## {
## "success":true,
## "errors":[
## {
## "field":"string",
## "message":"string"
## }
## 748
Response BodiesFundraising

## ],
## "links":{
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitmentschedule":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Error message if the process failed.Error Details[]errors
60.0Small, 60.0Links to the response object.Update
## Commitment
## Response Link
links
60.0Small, 60.0Indicates whether the request was
processed successfully (true) or not
## (false).
## Booleansuccess
## Update Commitment Response Link
Output representation of the links to the response object for the commitment updates.
## Sample Response
## {
## "giftcommitment":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## },
## "giftcommitmentschedule":{
"href":"/services/data/vXX.X/sobjects/sObject/...",
## "id":"string"
## }
## }
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0Link to the updated gift commitment
details.
## Link Detailsgift
commitment
60.0Small, 60.0Link to the schedule associated with the
updated gift commitment.
## Link Detailsgiftcommitment
schedule
## 749
Response BodiesFundraising

## Fundraising Invocable Actions
Use actions to add more functionality to your applications. Choose from standard actions, such as processing gift entries, update processed
gift entries, manage gift default designations, and manage gift transaction designations.
To know more about invocable actions, see Actions Developer Guide and REST API Developer Guide.
## Close Gift Commitment Action
Updates the status of a gift commitment to closed and updates the status for each of its unpaid and failed gift transactions.
## Manage Custom Gift Commitment Schedules Action
Creates or updates up to 15 custom gift commitment schedule records and their associated gift transaction records.
## Manage Gift Default Designations Action
Creates and manages Gift Default Designation records for a gift entry associated with a campaign, opportunity, or gift commitment.
## Manage Gift Transaction Designations Action
Creates and manages Gift Transaction Designation records for a gift transaction.
## Manage Recurring Gift Commitment Schedule Action
Creates or updates a recurring type of gift commitment schedule record and creates the first upcoming gift commitment transaction
record.
## Process Gift Entries Action
Processes, singly or as part of a batch, a specified gift entry ID, creating related donor, gift transaction, gift transaction designation,
and gift soft credit records. You may also test gift entry processing to check for errors before creating related records.
## Pause Gift Commitment Schedule Action
Pauses a gift commitment schedule for a specified period of time.
## Process Gift Commitment Action
Updates the status and other relevant fields for a gift commitment based on the statuses of the associated gift transactions and the
current gift commitment schedule.
## Resume Gift Commitment Schedule Action
Resumes a paused gift commitment schedule on a specified date.
## Update Processed Gift Entries Action
Updates the status of a specified gift entry record that is already processed. If the processing fails, the failure reason is updated.
## Close Gift Commitment Action
Updates the status of a gift commitment to closed and updates the status for each of its unpaid and failed gift transactions.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/closeGiftCommitment
## Formats
## JSON
## 750
Fundraising Invocable ActionsFundraising

HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
## String
giftCommitmentId
## Description
## Required.
The ID of the gift commitment record to be closed.
## Outputs
## None.
## Example
Here’s a request for the Close Gift Commitment action.
## {
## "inputs":[
## {
"giftCommitmentId":"6gcNA000000YshCYAS"
## }
## ]
## }
Here’s a response for the Close Gift Commitment action.
## [
## {
"actionName":"closeGiftCommitment",
## "errors":null,
"isSuccess":true,
"outputValues":null,
## "version":1
## }
## ]
## Manage Custom Gift Commitment Schedules Action
Creates or updates up to 15 custom gift commitment schedule records and their associated gift transaction records.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
## 751
Manage Custom Gift Commitment Schedules ActionFundraising

Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/manageCustomGiftCmtSchds
## Formats
## JSON
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
sObject
giftCommitmentSchedules
## Description
## Required.
A collection of gift commitment schedule records to be created or updated.
## Outputs
DetailsInput
## Type
## String
giftCommitmentScheduleList
## Description
A comma-delimited list of gift commitment schedule IDs records that the action created or
updated.
## Example
Here’s a request for the Manage Custom Gift Commitment Schedules action.
## {
## "inputs":[
## {
"giftCommitmentSchedules":[
## {
"StartDate":"2023-08-26",
"PaymentMethod":"Check",
"Id":"6csNA000000hbx8YAA",
"EndDate":"2023-08-28"
## },
## 752
Manage Custom Gift Commitment Schedules ActionFundraising

## {
"StartDate":"2023-08-29",
"PaymentMethod":"Check",
"Id":"6csNA000000hby4YAA",
"EndDate":"2023-08-30"
## }
## ]
## }
## ]
## }
Here’s a response for the Manage Custom Gift Commitment Schedules action.
## [
## {
"actionName":"manageCustomGiftCmtSchds",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftCommitmentScheduleIdsList":[
"6csNA000000hbx8YAA",
"6csNA000000hby4YAA"
## ]
## },
## "version":1
## }
## ]
## Manage Gift Default Designations Action
Creates and manages Gift Default Designation records for a gift entry associated with a campaign, opportunity, or gift commitment.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/manageGiftDefaultDesignations
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## 753
Manage Gift Default Designations ActionFundraising

## Inputs
DetailsInput
## Type
sObject
giftDefaultDesignationIds
## Description
## Required.
A collection of Gift Default Designation record IDs that are to be modified or deleted.
## Type
## ID
parentRecordId
## Description
## Required.
The ID of the parent record like a campaign, opportunity, or gift commitment associated with
the gift default designation IDs in giftDefaultDesignationIds.
## Outputs
## None.
## Example
Here’s a request for the Manage Gift Default Designations action.
## {
## "inputs":[
## {
"giftDefaultDesignationIds":[
## {
"GiftDesignationId":"6gdRM0000004CD0YAM",
"AllocatedPercentage":100
## }
## ]
## }
## ],
"parentRecordId":"6gcRM00000001UNYAY"
## }
Here’s a response for the Manage Gift Default Designations action.
## [
## {
"actionName":"manageGiftDefaultDesignations",
## "errors":null,
"isSuccess":true,
"outputValues":null,
## "version":1
## 754
Manage Gift Default Designations ActionFundraising

## }
## ]
## Manage Gift Transaction Designations Action
Creates and manages Gift Transaction Designation records for a gift transaction.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/manageGiftTrxnDesignations
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
sObject
giftTransactionDesignations
## Description
## Required.
A collection of Gift Transaction Designation record IDs that are to be modified or deleted.
## Type
## ID
recordId
## Description
## Required.
The record for which the Gift Transaction Designation record is created. For example, Gift
## Transaction.
## Outputs
## None.
## 755
Manage Gift Transaction Designations ActionFundraising

## Example
Here’s a request for the Manage Gift Transaction Designations action.
## {
## "inputs":[
## {
"giftTransactionDesignations":[
## {
"GiftDesignationId":"6gdRM0000004CDAYA2",
"Percent":100,
"Amount":76
## }
## ]
## }
## ],
"recordId":"6trRM00000003PJYAY"
## }
Here’s a response for the Manage Gift Transaction Designations action.
## [
## {
"actionName":"manageGiftTrxnDesignations",
## "errors":null,
"isSuccess":true,
"outputValues":null,
## "version":1
## }
## ]
## Manage Recurring Gift Commitment Schedule Action
Creates or updates a recurring type of gift commitment schedule record and creates the first upcoming gift commitment transaction
record.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/manageRcrGiftCmtSchd
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## 756
Manage Recurring Gift Commitment Schedule ActionFundraising

## Inputs
DetailsInput
## Type
## Date
effectiveFromDate
## Description
The date from when the updates to the gift commitment schedule are effective. Only applicable
in a schedule update scenario.
## Type
## Date
effectiveToDate
## Description
The date until when the updates to the gift commitment schedule are effective. Only applicable
in a schedule update scenario.
## Type
sObject
giftCommitment
## Schedule
## Description
## Required.
The gift commitment schedule record to be created or updated.
## Type
sObject
PaymentInstrument
## Description
## Required.
The payment instrument record to be created or updated.
## Outputs
DetailsInput
## Type
## Date
giftCommitment
ScheduleIdsList
## Description
A comma-delimited list of gift commitment schedule IDs for schedules that were created or
updated.
## 757
Manage Recurring Gift Commitment Schedule ActionFundraising

## Example
Here’s a request for the Manage Recurring Gift Commitment Schedule action.
## {
## "inputs":[
## {
"giftCommitmentSchedules":[
## {
"StartDate":"2023-08-26",
"PaymentMethod":"Check",
"Id":"6csNA000000hbx8YAA",
"EndDate":"2023-08-28"
## },
## {
"StartDate":"2023-08-29",
"PaymentMethod":"Check",
"Id":"6csNA000000hby4YAA",
"EndDate":"2023-08-30"
## }
## ],
"paymentInstrument":{
"Last4":"1234",
"Type":"CreditCard",
"ExpiryMonth":"May",
"ExpiryYear":"29"
## }
## }
## ]
## }
Here’s a response for the Manage Recurring Gift Commitment Schedule action.
## [
## {
"actionName":"manageRcrGiftCmtSchd",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftCommitmentScheduleIdsList":[
"6csNA000000hbx8YAA",
"6csNA000000hby4YAA"
## ]
## },
## "version":1
## }
## ]
## Process Gift Entries Action
Processes, singly or as part of a batch, a specified gift entry ID, creating related donor, gift transaction, gift transaction designation, and
gift soft credit records. You may also test gift entry processing to check for errors before creating related records.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
## 758
Process Gift Entries ActionFundraising

Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/processGiftEntries
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
## ID
giftEntryId
## Description
## Required.
The ID of the gift entry record to be processed.
## Type
## Boolean
isDryRun
## Description
Indicates whether to run the action without creating or updating records to determine if there
are any errors (true) or actual processing (false).
The default value is false.
## Outputs
DetailsOutput
## Type
## ID
donorId
## Description
The ID of the person, household, or organization account that’s associated with the gift entry.
## Type
## ID
giftEntryId
## Description
The ID of the gift entry record that is processed.
## 759
Process Gift Entries ActionFundraising

DetailsOutput
## Type
## String
giftProcessingErrorDetails
## Description
The error details when the gift processing status is Failure.
## Type
## String
giftProcessingStatus
## Description
The processing status of the gift entry.
Valid values are:
## •
## Failure
## •
## New
## •
## Success
## Type
## ID
giftTransactionId
## Description
The ID of the gift transaction that’s associated with the gift entry.
## Example
Here’s a request for the Process Gift Entries action for processing a gift entry.
## {
## "inputs":[
## {
"giftEntryId":"6geRM00000000GdYAI"
## }
## ]
## }
Here’s a response for the Process Gift Entries action for processing a gift entry.
## [
## {
"actionName":"processGiftEntries",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftProcessingStatus":"SUCCESS",
"giftEntryId":"6geRM00000000GdYAI",
"giftTransactionId":"6trRM00000003PJ",
"giftProcessingErrorDetails":null,
"donorId":"001RM000005ewDDYAY"
## },
## "version":1
## 760
Process Gift Entries ActionFundraising

## }
## ]
Here’s a request for the Process Gift Entries action for a dry run of gift entry processing.
## {
## "inputs":[
## {
"giftEntryId":"6geRM00000000GdYAI",
"isDryRun":"true",
## }
## ]
## }
Here’s a response for the Process Gift Entries action for a dry run of gift entry processing.
## [
## {
"actionName":"processGiftEntries",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftProcessingStatus":"New",
"giftEntryId":"6geRM00000000GdYAI",
"giftTransactionId":null,
"giftProcessingErrorDetails":null,
"donorId":null
## },
## "version":1
## }
## ]
## Pause Gift Commitment Schedule Action
Pauses a gift commitment schedule for a specified period of time.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/pauseGiftCommitmentSchedule
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## 761
Pause Gift Commitment Schedule ActionFundraising

## Inputs
DetailsInput
## Type
## Date
endDate
## Description
The date to resume the gift commitment schedule.
## Type
## String
giftCommitmentScheduleId
## Description
## Required.
The ID of the gift commitment schedule record to be paused.
## Type
## Date
startDate
## Description
The date to pause the gift commitment schedule.
## Type
## String
updateReason
## Description
The reason the gift commitment schedule is to be paused.
## Outputs
DetailsInput
## Type
## String
giftCommitmentScheduleIdsList
## Description
A comma-delimited list of gift commitment schedule IDs for schedules that were created or
updated.
## Example
Here’s a request for the Pause Gift Commitment Schedule action.
## {
## "inputs":[
## {
"giftCommitmentScheduleId":"6csNA000000YNbOYAW",
"startDate":"2023-08-25"
## 762
Pause Gift Commitment Schedule ActionFundraising

## }
## ]
## }
Here’s a response for the Pause Gift Commitment Schedule action.
## [
## {
"actionName":"pauseGiftCommitmentSchedule",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftCommitmentScheduleIdsList":[
"6csNA000000YNbOYAW",
"6csNA000000hbxuYAA"
## ]
## },
## "version":1
## }
## ]
## Process Gift Commitment Action
Updates the status and other relevant fields for a gift commitment based on the statuses of the associated gift transactions and the
current gift commitment schedule.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/processGiftCommitment
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
## String
giftCommitmentId
## Description
## Required.
The ID of the gift commitment record to be processed.
## 763
Process Gift Commitment ActionFundraising

## Outputs
DetailsInput
## Type
## String
giftCommitmentProcessingStatus
## Description
The status of the gift commitment record after it is processed.
## Example
Here’s a request for the Process Gift Commitment action.
## {
## "inputs":[
## {
"giftCommitmentId":"6gcNA000000PeKhYAK"
## }
## ]
## }
Here’s a response for the Process Gift Commitment action.
## [
## {
"actionName":"processGiftCommitment",
## "errors":null,
"isSuccess":true,
"outputValues":null,
## "version":1
## }
## ]
## Resume Gift Commitment Schedule Action
Resumes a paused gift commitment schedule on a specified date.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/resumeGiftCommitmentSchedule
## Formats
## JSON, XML
HTTP Methods
## POST
## 764
Resume Gift Commitment Schedule ActionFundraising

## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
## String
giftCommitmentScheduleId
## Description
## Required.
The ID of the gift commitment schedule record to be resumed.
## Type
## Date
resumeDate
## Description
The date to resume the gift commitment schedule.
## Type
## String
updateReason
## Description
The reason the gift commitment schedule is to be resumed.
## Outputs
DetailsInput
## Type
## String
giftCommitmentScheduleIdsList
## Description
A comma-delimited list of gift commitment schedule IDs for schedules that were created or
updated.
## Example
Here’s a request for the Resume Gift Commitment Schedule action.
## {
## "inputs":[
## {
"giftCommitmentScheduleId":"6csNA000000hbxpYAA",
"resumeDate":"2023-08-27"
"updateReason":"Test"
## }
## 765
Resume Gift Commitment Schedule ActionFundraising

## ]
## }
Here’s a response for the Resume Gift Commitment Schedule action.
## [
## {
"actionName":"resumeGiftCommitmentSchedule",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftCommitmentScheduleIdsList":[
"6csNA000000hbxpYAA"
## ]
## },
## "version":1
## }
## ]
## Update Processed Gift Entries Action
Updates the status of a specified gift entry record that is already processed. If the processing fails, the failure reason is updated.
This action is available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising
User system permission is assigned.
Supported REST HTTP Methods
## URI
/services/data/vXX.X/actions/standard/updateProcessedGiftEntries
## Formats
## JSON, XML
HTTP Methods
## POST
## Authentication
Authorization:Bearertoken
## Inputs
DetailsInput
## Type
## ID
donorId
## Description
The ID of the account of the donor that is updated when giftProcessingStatus is
## Success.
## Type
## ID
giftEntryId
## 766
Update Processed Gift Entries ActionFundraising

DetailsInput
## Description
## Required.
The ID of the gift entry record to be updated.
## Type
## String
giftProcessingErrorDetails
## Description
The error details when giftProcessingStatus is Failure.
## Type
## String
giftProcessingStatus
## Description
The processing status of the gift entry.
Valid values are:
## •
## Failure
## •
## New
## •
## Success
## Type
## ID
giftTransactionId
## Description
The ID of the gift transaction record associated with the gift entry that is to be updated when
giftProcessingStatus is Success.
## Outputs
DetailsField
## Type
## ID
giftEntryId
## Description
The ID of the gift entry record that is updated.
## Example
Here’s a request for the Update Processed Gift Entries action.
## {
## "inputs":[
## {
"donorId":"001RM000005ewDDYAY",
## 767
Update Processed Gift Entries ActionFundraising

"giftEntryId":"6geRM00000000GdYAI",
"giftProcessingErrorDetails":null,
"giftProcessingStatus":"SUCCESS",
"giftTransactionId":"6trRM00000003PJ"
## }
## ]
## }
Here’s a response for the Update Processed Gift Entries action.
## [
## {
"actionName":"updateProcessedGiftEntries",
## "errors":null,
"isSuccess":true,
"outputValues":{
"giftEntryId":"6geRM00000000GdYAI"
## },
## "version":1
## }
## ]
Fundraising Metadata API Types
Metadata API enables you to access some types and feature settings that you can customize in the user interface.
For more information about Metadata API and to find a complete reference of existing metadata types, see Metadata API Developer
## Guide.
AffinityScoreDefinition
Represents the affinity information used in calculations to analyze and categorize contacts for marketing purposes.
Flow for Fundraising
Represents the metadata associated with a flow. With Flow, you can create an application that navigates users through a series of
screens to query and update records in the database. You can also execute logic and provide branching capability based on user
input to build dynamic applications.
AffinityScoreDefinition
Represents the affinity information used in calculations to analyze and categorize contacts for marketing purposes.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Parent Type
This type extends the Metadata metadata type and inherits its fullName field.
## 768
Fundraising Metadata API TypesFundraising

File Suffix and Directory Location
AffinityScoreDefinition components have the suffix .affinityScoreDefinition and are stored in the
affinityScoreDefinitions folder.
## Version
AffinityScoreDefinition components are available in API version  and later.
## Special Access Rules
This metadata type is available only if the Fundraising Access license is enabled for the org and the Fundraising admin permission is
assigned to users.
## Fields
DescriptionField Name
## Field Type
string
affinityScoreDefinitionDesc
## Description
Description of the affinity score definition.
## Field Type
string
affinityScoreDefinitionName
## Description
Name of the affinity score definition.
## Field Type
AffinityScoreType (enumeration of type string)
affinityScoreType
## Description
Type of the affinity score that’s defined.
Valid values are:
## •
CAP—Capacity, Ability, Propensity (CAP)
## •
RFM—Recency, Frequency, Monetary (RFM)
The default value is RFM.
## Field Type
string
masterLabel
## Description
Label for this affinity score definition value. This display value is the internal label that
doesn't get translated.
## Field Type
int
numberOfMonths
## 769
AffinityScoreDefinitionFundraising

DescriptionField Name
## Description
Number of months to analyze the records for calculating the affinity score.
## Field Type
int
numberOfRanges
## Description
## Required.
Number of ranges to use in the calculation, ranging from 0 to 9. Provide the
corresponding range list values in the scoreRangeList field.
## Field Type
string
scoreRangeList
## Description
## Required.
Ranges that are referenced in the affinity score calculation. This field is used with
scoreRangeList. For example, to calculate RFM with numberOfRanges value
as 3, provide the values for the scoreRangeList field in this format.
## {
"R ranges":"0-30,31-100,100+",
"F ranges":"0-10,11-100,100+",
"M ranges":"0-1000,1001-5000,5000+"
## }
## Field Type
string
sourceFieldApiNameList
## Description
## Required.
API names of the source fields that are referenced in the score calculation.
## Field Type
string
sourceObjectApiNameList
## Description
API names of the source objects that are referenced in the score calculation.
## Field Type
string
targetFieldApiNameList
## Description
## Required.
API names of the target fields where the calculated scores are added.
## 770
AffinityScoreDefinitionFundraising

DescriptionField Name
## Field Type
string
targetObjectApiName
API name of the target object where the calculated scores are added.
## Declarative Metadata Sample Definition
This example shows a sample of an AffinityScoreDefinition component.
<?xmlversion="1.0"encoding="UTF-8"?>
<AffinityScoreDefinition
xmlns="http://soap.sforce.com/2006/04/metadata">
<affinityScoreDefinitionDesc>RFMAffinityScore</affinityScoreDefinitionDesc>
<affinityScoreDefinitionName>AffinityScoreDefinition_RFM</affinityScoreDefinitionName>
<affinityScoreType>RFM</affinityScoreType>
<masterLabel>MasterLabel</masterLabel>
<numberOfMonths>12</numberOfMonths>
<numberOfRanges>3</numberOfRanges>
<scoreRangeList>
## [
## {
"name":"R Ranges",
## "direction":"ascending",
## "ranges":[30,90,180]
## },
## {
"name":"F Ranges",
## "direction":"descending",
## "ranges":[10,15,100]
## },
## {
"name":"M Ranges",
## "direction":"descending",
## "ranges":[500,1000,5000]
## }
## ]
</scoreRangeList>
<sourceFieldApiNameList>
## [
## {
"name":"R Source",
## "values":
## [
## {
"fieldName":"DonorGiftSummary.DaysSinceLastGift",
"fieldWeight":1
## }
## ]
## },
## {
"name":"F Source",
## 771
AffinityScoreDefinitionFundraising

## "values":
## [
## {
"fieldName":"DonorGiftSummary.GiftCount",
"fieldWeight":1
## }
## ]
## },
## {
"name":"M Source",
## "values":
## [
## {
"fieldName":"DonorGiftSummary.TotalGiftsCount",
"fieldWeight":1
## }
## ]
## }
## ]
</sourceFieldApiNameList>
<targetFieldApiNameList>
## [
## {
"name":"R Target",
## "values":
## [
## {
"fieldName":"DonorGiftSummary.RecencyScore",
"fieldWeight":1
## }
## ]
## },
## {
"name":"F Target",
## "values":
## [
## {
"fieldName":"DonorGiftSummary.FrequencyScore",
"fieldWeight":1
## }
## ]
## },
## {
"name":"M Target",
## "values":
## [
## {
"fieldName":"DonorGiftSummary.MonetaryScore",
"fieldWeight":1
## }
## ]
## }
## ]
## 772
AffinityScoreDefinitionFundraising

</targetFieldApiNameList>
</AffinityScoreDefinition>
This example shows a sample of the package.xml file that references the previous definition.
<?xmlversion="1.0"encoding="UTF-8"?>
<Packagexmlns="http://soap.sforce.com/2006/04/metadata">
## <types>
## <members>*</members>
<name>AffinityScoreDefinition</name>
## </types>
## <version></version>
</Package>
Wildcard Support in the Manifest File
This metadata type supports the wildcard character * (asterisk) in the package.xml manifest file. For information about using the
manifest file, see Deploying and Retrieving Metadata with the Zip File.
Flow for Fundraising
Represents the metadata associated with a flow. With Flow, you can create an application that navigates users through a series of screens
to query and update records in the database. You can also execute logic and provide branching capability based on user input to build
dynamic applications.
FlowActionCall
Fundraising exposes additional actionType values for the FlowActionCall Metadata type. For more information on Flow and FlowActionCall
metadata type, see Flow.
DescriptionField TypeField Name
Required. The action type. Additional valid values only for Business Rules
Engine include:
InvocableActionType
(enumeration of
type string)
actionType
## •
closeGiftCommitment—Updates the status of a gift
commitment to closed and updates the status for each of its unpaid
and failed gift transactions. This value is available in API version 59.0
and later.
## •
manageCustomGiftCmtSchds—Creates or updates up to
15 custom gift commitment schedule records and their associated
gift transaction records. This value is available in API version 59.0 and
later.
## •
manageFundraisingDefinitions—Runs up to three
predefined Data Processing Engine (DPE) definitions in a single
action. Use this invocable action to process the Donor Gift Summary,
Outreach Summary, and Gift Designation definitions. This value is
available in API version 64.0 and later.
## •
manageGiftDefaultDesignations—Creates and manages
Gift Default Designation records for a gift entry associated with a
## 773
Flow for FundraisingFundraising

DescriptionField TypeField Name
campaign, opportunity, or gift commitment. This value is available
in API version 59.0 and later.
## •
manageGiftTrxnDesignations—Creates and manages
Gift Transaction Designation records for a gift transaction. This value
is available in API version 59.0 and later.
## •
manageRcrGiftCmtSchd—Creates or updates a recurring
type of gift commitment schedule record and creates the first
upcoming gift commitment transaction record. This value is available
in API version 59.0 and later.
## •
processGiftEntries—Processes, singly or as part of a batch,
a specified gift entry ID, creating related donor, gift transaction, gift
transaction designation, and gift soft credit records. This value is
available in API version 59.0 and later.
## •
pauseGiftCommitmentSchedule—Pauses a gift
commitment schedule for a specified period of time. This value is
available in API version 59.0 and later.
## •
processGiftCommitment—Updates the status and other
relevant fields for a gift commitment based on the statuses of the
associated gift transactions and the current gift commitment
schedule. This value is available in API version 59.0 and later.
## •
resumeGiftCommitmentSchedule—Resumes a paused
gift commitment schedule on a specified date. This value is available
in API version 59.0 and later.
## •
updateProcessedGiftEntries—Updates the status of a
specified gift entry record that is already processed. If the processing
fails, the failure reason is updated. This value is available in API version
59.0 and later.
Fundraising Tooling API Objects
Tooling API exposes metadata used in developer tooling that you can access through REST or SOAP. Tooling API’s SOQL capabilities for
many metadata types allow you to retrieve smaller pieces of metadata.
For more information about Tooling API objects and to find a complete reference of all the supported objects, see Introducing Tooling
## API.
FundraisingConfig
Represents a collection of settings to configure Fundraising. This object is available in API version 59.0 and later.
FieldMappingConfig
Represents the configuration for fields mapped between a source object and one or more destination objects and fields.  This object
is available in API version 63.0 and later.
## 774
Fundraising Tooling API ObjectsFundraising

FieldMappingConfigItem
Represents the fields mapped between a defined source object and the destination object and fields. This object is available in API
version 63.0 and later.
GiftEntryGridTemplate
Represents templates that customize the gift entry grid in Fundraising. Available in API version 66.0 and later.
FundraisingConfig
Represents a collection of settings to configure Fundraising. This object is available in API version 59.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
Supported SOAP API Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
Supported REST API Methods
DELETE,GET,HEAD,PATCH,POST,Query
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
string
DeveloperName
## Properties
## Create, Filter, Group, Sort, Update
## Description
The unqiue name for FundraisingConfig.
## Type
picklist
DonorExternalIdField
## Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The field that's used as the external ID for donor lookup during gift entry. Donor name is the
default lookup. This field is available from API version 62.0 and later.
## Type
picklist
DonorMatchingMethod
## 775
FundraisingConfigFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the donor matching method that's used as the default method for the Business
Process API.
Possible values are:
## •
Duplicate_Management_Rules—Duplicate Management Rules
## •
No_Matching—No Matching
The default value is Duplicate_Management_Rules.
## Type
int
FailedTransactionCount
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The count of consecutively failed transactions before the gift commitment status is changed
to Failing. If set to 0, the status is never auto-changed to Failing.
## Type
string
HouseholdSoftCreditRole
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The soft credit role that's assigned to members of the donor's household.
## Type
int
InstallmentExtDayCount
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The number of days before or after the scheduled gift transaction due date for the gift to
appear in Gift Entry as a match to fulfill an open gift transaction.
## Type
boolean
IsHshldSoftCrAutoCrea
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether soft credits are automatically created for household members (true) or
not (false) when the donor donates.
## 776
FundraisingConfigFundraising

DetailsField
## Type
picklist
## Language
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The language of the FundraisingConfig
Possible values are:
## •
da—Danish
## •
de—German
## •
en_US—English
## •
es—Spanish
## •
es_MX—Spanish (Mexico)
## •
fi—Finnish
## •
fr—French
## •
it—Italian
## •
ja—Japanese
## •
ko—Korean
## •
nl_NL—Dutch
## •
no—Norwegian
## •
pt_BR—Portuguese (Brazil)
## •
ru—Russian
## •
sv—Swedish
## •
th—Thai
## •
zh_CN—Chinese (Simplified)
## •
zh_TW—Chinese (Traditional)
## Type
int
LapsedUnpaidTrxnCount
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The count of consecutive unpaid transactions before the gift commitment status is changed
to Lapsed. If set to 0, the status is never auto-changed to Lapsed.
## Type
string
MasterLabel
## Properties
## Create, Filter, Group, Sort, Update
## 777
FundraisingConfigFundraising

DetailsField
## Description
Label for the FundraisingConfig. In the UI, this field is Application Record Type Configuration.
## Type
string
NamespacePrefix
## Properties
## Filter, Group, Nillable, Sort
## Description
The namespace prefix associated with this object. Each Developer Edition organization that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can
refer to a component in a managed package by using the
namespacePrefix__componentName notation.
The namespace prefix can have one of the following values:
## •
In Developer Edition organizations, the namespace prefix is set to the namespace prefix
of the organization for all objects that support it. There is an exception if an object is in
an installed managed package. In that case, the object has the namespace prefix of the
installed managed package. This field’s value is the namespace prefix of the Developer
Edition organization of the package developer.
## •
In organizations that are not Developer Edition organizations, NamespacePrefix
is only set for objects that are part of an installed managed package. There is no
namespace prefix for all other objects.
## Type
string
OutreachSourceCodeGenFmla
## Properties
## Create, Filter, Group, Nillable, Sort, Update
## Description
The outreach source code generation formula that's composed of the selected formula
components.
Available in API version 63.0 and later.
## Type
boolean
ShouldClosePaidRcrCmt
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether to automatically close a recurring gift commitment when it has no ongoing
or future schedule, and no unpaid transaction (true) or not (false).
## Type
boolean
ShouldCreateRcrSchdTrxn
## 778
FundraisingConfigFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the next transaction in a recurring schedule is automatically created
(true) or not (false).
## Type
string
UtmCampaignSrcObj
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The UTM code of the campaign for which the donation was received. This field is available
from API version 60.0 and later.
## Type
string
UtmCampaignSrcObjField
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The UTM code of the campaign for which the donation was received. This field is available
from API version 60.0 and later.
## Type
string
UtmMediumSrcObj
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The UTM code of the outreach message channel from which the donation originated. This
field is available from API version 60.0 and later.
## Type
string
UtmMediumSrcObjField
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The UTM code of the outreach message channel from which the donation originated. This
field is available from API version 60.0 and later.
## Type
string
UtmSourceSrcObj
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## 779
FundraisingConfigFundraising

DetailsField
## Description
The UTM code of the source from which the donation originated. This field is available from
API version 60.0 and later.
## Type
string
UtmSourceSrcObjField
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The UTM code of the source from which the donation originated. This field is available from
API version 60.0 and later.
FieldMappingConfig
Represents the configuration for fields mapped between a source object and one or more destination objects and fields.  This object is
available in API version 63.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
textarea
## Description
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
## Description
The description of the field mapping configuration.
## Type
string
DeveloperName
## Properties
## Create, Filter, Group, Sort, Update
## 780
FieldMappingConfigFundraising

DetailsField
## Description
The unqiue name for FieldMappingConfig.
## Type
picklist
## Language
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
The language of the FieldMappingConfig.
Possible values are:
## •
da—Danish
## •
de—German
## •
en_US—English
## •
es—Spanish
## •
es_MX—Spanish (Mexico)
## •
fi—Finnish
## •
fr—French
## •
it—Italian
## •
ja—Japanese
## •
ko—Korean
## •
nl_NL—Dutch
## •
no—Norwegian
## •
pt_BR—Portuguese (Brazil)
## •
ru—Russian
## •
sv—Swedish
## •
th—Thai
## •
zh_CN—Chinese (Simplified)
## •
zh_TW—Chinese (Traditional)
## Type
string
MasterLabel
## Properties
## Create, Filter, Group, Sort, Update
## Description
Label for the FieldMappingConfig.
## Type
string
NamespacePrefix
## Properties
## Filter, Group, Nillable, Sort
## 781
FieldMappingConfigFundraising

DetailsField
## Description
The namespace prefix associated with this object. Each Developer Edition organization that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can
refer to a component in a managed package by using the
namespacePrefix__componentName notation.
The namespace prefix can have one of the following values:
## •
In Developer Edition organizations, the namespace prefix is set to the namespace prefix
of the organization for all objects that support it. There is an exception if an object is in
an installed managed package. In that case, the object has the namespace prefix of the
installed managed package. This field’s value is the namespace prefix of the Developer
Edition organization of the package developer.
## •
In organizations that are not Developer Edition organizations, NamespacePrefix
is only set for objects that are part of an installed managed package. There is no
namespace prefix for all other objects.
## Type
picklist
ProcessType
## Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
## Description
Specifies the type of process that the field mapping configuration supports.
Possible values are:
## •
ChangeRequest
## •
GiftEntry
## •
## Incident
## •
## Problem
The default value is GiftEntry.
## Type
picklist
SourceObjectId
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The ID of the source object for all of the fields mapped in the configuration.
Possible values are:
## •
GiftEntry
## 782
FieldMappingConfigFundraising

FieldMappingConfigItem
Represents the fields mapped between a defined source object and the destination object and fields. This object is available in API
version 63.0 and later.
Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.
## Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
## Special Access Rules
This object is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users.
## Fields
DetailsField
## Type
picklist
DestinationFieldId
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The ID of the destination field for the field mapping configuration.
## Type
picklist
DestinationObjectId
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The ID of the destination object for the field mapping configuration.
## Type
reference
FieldMappingConfigId
## Properties
## Create, Filter, Group, Sort
## Description
The parent field mapping configuration associated with the field mapping configuration
item.
This field is a relationship field.
## Relationship Name
FieldMappingConfig
## 783
FieldMappingConfigItemFundraising

DetailsField
## Relationship Type
## Master-detail
## Refers To
FieldMappingConfig (the master object)
## Type
int
## Sequence
## Properties
## Create, Filter, Group, Sort, Update
## Description
The order number of the field relative to other fields, determining the sequence in which
fields are displayed within a custom user interface.
## Type
picklist
SourceFieldId
## Properties
Create, Filter, Group, Restricted picklist, Sort, Update
## Description
The ID of the source field for the field mapping configuration.
GiftEntryGridTemplate
Represents templates that customize the gift entry grid in Fundraising. Available in API version 66.0 and later.
## Special Access Rules
This object is available only if the Fundraising Access license is enabled, the Fundraising User system permission is assigned to users,
and the Gift Entry Grid is enabled.
## Fields
DetailsField
## Type
textarea
## Description
## Properties
## Create, Nillable, Update
## Description
The description of the gift entry grid template.
## Type
boolean
IsActive
## 784
GiftEntryGridTemplateFundraising

DetailsField
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether this template is active and available for use in the Gift Entry Grid. Active
templates appear as values in the Screen Template Name picklist on the gift batch object.
## Type
boolean
IsSingleGiftDefault
## Properties
Create, Defaulted on create, Filter, Group, Sort, Update
## Description
Indicates whether the template is the default template for single gift entry (true) or not (false,
the default).
## Type
string
TemplateConfiguration
## Properties
## Create, Filter, Group, Sort, Update
## Description
The template configuration file that includes the data for fields, columns, and components.
## 785
GiftEntryGridTemplateFundraising