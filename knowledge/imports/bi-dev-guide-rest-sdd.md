

Einstein Discovery REST API
## Developer Guide
## Salesforce, Spring ’26
Last updated: March 20, 2026

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
Einstein Discovery REST API Overview. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Release  Notes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Connect REST API Authorization. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
API  End-of-Life  Policy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
Examples. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Get  Predictions. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Manage  Prediction  Definitions. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
Manage  Models. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
Manage  Prediction  Jobs. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
Manage  Model  Refresh  Jobs. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
Query Prediction History. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
Einstein Discovery REST API Resources Overview. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
Smart  Data  Discovery  Resource. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
Model Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
Metrics  Resource. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
Narrative  Resource. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Prediction Definition Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Predict  Jobs  Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
Predict Resource. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
Predict  History  Resource. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
Refresh  Jobs  Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
Stories Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 44
Requests. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
Abstract Classification Threshold Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 55
Abstract Smart Data Discovery AI Model Source Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . 56
Abstract Smart Data Discovery Field Mapping Source Input. . . . . . . . . . . . . . . . . . . . . . . . . 56
Abstract Smart Data Discovery Many To One Transformation Input. . . . . . . . . . . . . . . . . . . . 56
Abstract Smart Data Discovery Model Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 57
Abstract Smart Data Discovery Model Runtime Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 57
Abstract Smart Data Discovery One To One Transformation Input. . . . . . . . . . . . . . . . . . . . . 58
Abstract Smart Data Discovery Predict Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 59
Abstract Smart Data Discovery Prediction Property Input. . . . . . . . . . . . . . . . . . . . . . . . . . . 59
Abstract Smart Data Discovery Projected Predictions Interval Setting Input. . . . . . . . . . . . . . . 60
Abstract Smart Data Discovery Transformation Filter Input. . . . . . . . . . . . . . . . . . . . . . . . . . 60
Abstract Smart Data Discovery Transformation Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61

Abstract Smart Data Discovery Transformation Override Input. . . . . . . . . . . . . . . . . . . . . . . 61
Abstract Story Data Property Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
Asset Reference Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
Base Asset Reference Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
Binary Classification Threshold Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
Predict  History  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
Predict  History  Range  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
Smart  Data  Discovery  AI  Model  Discovery  Source  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . 64
Smart Data Discovery AI Model Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64
Smart Data Discovery AI Model Transformation Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 66
Smart Data Discovery AI Model User Upload Source Input. . . . . . . . . . . . . . . . . . . . . . . . . 67
Smart Data Discovery Categorical Imputation Transformation Input. . . . . . . . . . . . . . . . . . . 67
Smart  Data  Discovery  Classification  Prediction  Property  Input. . . . . . . . . . . . . . . . . . . . . . . 67
Smart Data Discovery Cluster Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 68
Smart Data Discovery Complex Filter Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 68
Smart Data Discovery Custom Prescribable Field Definition Input. . . . . . . . . . . . . . . . . . . . . 68
Smart Data Discovery Customizable Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 69
Smart Data Discovery Discovery Model Runtime Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . 69
Smart Data Discovery Extract Day of Week Transformation Input. . . . . . . . . . . . . . . . . . . . . 69
Smart Data Discovery Extract Month of Year Transformation Input. . . . . . . . . . . . . . . . . . . . 69
Smart Data Discovery Field Mapping Analytics Dataset Field Input. . . . . . . . . . . . . . . . . . . . 69
Smart Data Discovery Field Mapping Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 70
Smart Data Discovery Field Mapping Salesforce Field Input. . . . . . . . . . . . . . . . . . . . . . . . . 70
Smart Data Discovery Filter Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 70
Smart Data Discovery Filter Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 71
Smart Data Discovery Free Text Clustering Transformation Input. . . . . . . . . . . . . . . . . . . . . . 72
Smart Data Discovery H20 Model Runtime Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 72
Smart  Data  Discovery  Model  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 72
Smart Data Discovery Model Field Date Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 73
Smart Data Discovery Model Field Numeric Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 74
Smart Data Discovery Model Field Text Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 74
Smart Data Discovery Multiclass Classification Prediction Property Input. . . . . . . . . . . . . . . . 74
Smart Data Discovery Narrative Filter Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 75
Smart  Data  Discovery  Narrative  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 75
Smart Data Discovery Narrative Insight Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 76
Smart Data Discovery Narrative Query Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 76
Smart Data Discovery Numeric Range Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 76
Smart Data Discovery Numeric Transformation Filter Input. . . . . . . . . . . . . . . . . . . . . . . . . . 77
Smart Data Discovery Numerical Imputation Transformation Input. . . . . . . . . . . . . . . . . . . . 77
Smart  Data  Discovery  Predict  Extension  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 77
Smart  Data  Discovery  Predict  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
Smart Data Discovery Predict Nested Row List Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
Smart  Data  Discovery  Predict  Job  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
Smart Data Discovery Predict Job Update Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79
## Contents

Smart  Data  Discovery  Predict  Settings  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79
Smart Data Discovery Predict Raw Data Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 80
Smart Data Discovery Predict Record Overrides Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 80
Smart Data Discovery Predict Record Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 81
Smart Data Discovery Prescribable Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 81
Smart Data Discovery Projected Prediction Settings Input. . . . . . . . . . . . . . . . . . . . . . . . . . . 81
Smart Data Discovery Projected Predictions Count From Date Interval Setting Input. . . . . . . . . 82
Smart Data Discovery Projected Predictions Count Interval Setting Input. . . . . . . . . . . . . . . . 82
Smart Data Discovery Projected Predictions Date Interval Setting Input. . . . . . . . . . . . . . . . . 83
Smart Data Discovery Projected Predictions Historical Dataset Source Input. . . . . . . . . . . . . . 83
Smart Data Discovery Projected Predictions Override Input. . . . . . . . . . . . . . . . . . . . . . . . . 83
Smart  Data  Discovery  Projected  Predictions  Transformation  Input. . . . . . . . . . . . . . . . . . . . 84
Smart Data Discovery Regression Prediction Property Input. . . . . . . . . . . . . . . . . . . . . . . . . 85
Smart Data Discovery Scikit Learn 102 Model Runtime Input. . . . . . . . . . . . . . . . . . . . . . . . . 85
Smart Data Discovery Sentiment Analysis Transformation Input. . . . . . . . . . . . . . . . . . . . . . 85
Smart Data Discovery TensorFlow 27 Model Runtime Input. . . . . . . . . . . . . . . . . . . . . . . . . 85
Smart Data Discovery TensorFlow Model Runtime Input. . . . . . . . . . . . . . . . . . . . . . . . . . . 86
Smart Data Discovery Text Transformation Filter Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 86
Story Day Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 86
Story Day of Week Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 86
Story Field Only Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
Story Month Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
Story Month of Year Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
Story Null Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Story Quarter Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Story Quarter of Year Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Story  Query  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Story Range Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 90
Story  Text  Field  Value  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 90
Story Year Field Value Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 90
Responses. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 91
Abstract  Bucketing  Strategy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 99
Abstract Classification Threshold. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
Abstract  Date  Field  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
Abstract  Field  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 101
Abstract  Numeric  Field  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 101
Abstract  Smart  Data  Discovery  Aggregate  Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . . 102
Abstract Smart Data Discovery AI Model Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
Abstract Smart Data Discovery AI Model Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
Abstract Smart Data Discovery Field Mapping Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
Abstract Smart Data Discovery Model Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
Abstract  Smart  Data  Discovery  Model  Runtime. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
Abstract Smart Data Discovery Prediction Property. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 105
## Contents

Abstract Smart Data Discovery Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 105
Abstract  Smart  Data  Discovery  Predict. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 106
Abstract  Smart  Data  Discovery  Projected  Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 106
Abstract Smart Data Discovery Projected Predictions Interval Setting. . . . . . . . . . . . . . . . . . 107
Abstract Smart Data Discovery Transformation Override. . . . . . . . . . . . . . . . . . . . . . . . . . 107
Abstract  Smart  Data  Discovery  Validation  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . 108
Abstract Story Data Property. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 108
Abstract  Story  Insights  Case. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 108
Abstract  Story  Insights. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 109
Abstract  Story  Narrative  Element. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 109
Abstract  Story  Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 110
Abstract  Text  Field  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 110
Analytics Dataset Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 111
Asset History Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 111
Asset  History. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 111
Asset  Reference. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 112
Autopilot. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 112
Base  Asset  Reference. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Binary  Classification  Threshold. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Date Field Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Diagnostic Insights Case. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
Directory Item Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
Even Width Bucketing Strategy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
Manual  Bucketing  Strategy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115
Model Field Label Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115
Numeric  Field  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115
Percentile Bucketing Strategy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115
Predict  History  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 116
Predict History. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 116
Predict History Range. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 116
Predict  History  Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 117
Report  Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 117
Smart Data Discovery Aggregate Predict Condition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 117
Smart Data Discovery Aggregate Prediction Error. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 118
Smart Data Discovery Aggregate Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 118
Smart Data Discovery AI Model Classification Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . 118
Smart  Data  Discovery  AI  Model  Coefficient  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
Smart Data Discovery AI Model Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
Smart Data Discovery AI Model Discovery Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
Smart Data Discovery AI Model Multiclass Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
Smart Data Discovery AI Model Regression Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
Smart  Data  Discovery  AI  Model  Residual  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
Smart Data Discovery AI Model Residual. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 121
Smart  Data  Discovery  AI  Model  Transformation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 121
## Contents

Smart Data Discovery AI Model User Upload Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 122
Smart Data Discovery AI Model. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 122
Smart Data Discovery Categorical Projected Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . 124
Smart Data Discovery Classification Prediction Property. . . . . . . . . . . . . . . . . . . . . . . . . . . 124
Smart Data Discovery Contact. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 125
Smart Data Discovery Custom Prescribable Field Definition. . . . . . . . . . . . . . . . . . . . . . . . 125
Smart Data Discovery Customizable Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 125
Smart Data Discovery Feature Importance Metric. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 126
Smart Data Discovery Field Mapping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 126
Smart Data Discovery Field Mapping Analytics Dataset Field. . . . . . . . . . . . . . . . . . . . . . . 127
Smart Data Discovery Field Mapping Mapped Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 127
Smart Data Discovery Field Mapping Salesforce Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . 127
Smart Data Discovery Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 128
Smart  Data  Discovery  Filter  List. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 128
Smart  Data  Discovery  Filter  Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 128
Smart Data Discovery Filter. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 128
Smart  Data  Discovery  Impute  Strategy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 129
Smart  Data  Discovery  Insight. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 130
Smart  Data  Discovery  Live  Metric  Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 130
Smart Data Discovery Live Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 130
Smart  Data  Discovery  Metrics  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 131
Smart Data Discovery Model Card. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 131
Smart  Data  Discovery  Prediction  Definition  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . 132
Smart Data Discovery Model Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 132
Smart  Data  Discovery  Model  Field  Date. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 133
Smart Data Discovery Model Field Numeric. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 133
Smart Data Discovery Model Field Text. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 133
Smart Data Discovery Model. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 134
Smart  Data  Discovery  Multiclass  Classification  Prediction  Property. . . . . . . . . . . . . . . . . . . 135
Smart Data Discovery Multiclass Predict. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Smart Data Discovery Narrative Details . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Smart Data Discovery Narrative Field Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Smart Data Discovery Narrative Field . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Smart Data Discovery Narrative Post Body Filter. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 137
Smart Data Discovery Narrative Post Body Insight. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 137
Smart Data Discovery Narrative Post Body Query. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 138
Smart  Data  Discovery  Narrative  Post  Body. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 138
Smart  Data  Discovery  Numeric  Range. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 139
Smart Data Discovery Numerical Projected Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . . 139
Smart Data Discovery Predict Column Custom Text. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 139
Smart  Data  Discovery  Predict  Column. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 140
Smart  Data  Discovery  Predict  Condition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 140
Smart  Data  Discovery  Prediction  Definition  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . 140
Smart Data Discovery Prediction Definition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 141
## Contents

Smart Data Discovery Prediction Error. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 143
Smart  Data  Discovery  Prediction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 143
Smart Data Discovery Predict Error. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 143
Smart  Data  Discovery  Import  Warnings. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 144
Smart  Data  Discovery  Predict  Job  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 144
Smart  Data  Discovery  Predict  Job. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 144
Smart Data Discovery Predict List. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 146
Smart Data Discovery Predict Settings. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 146
Smart  Data  Discovery  Predict. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 147
Smart Data Discovery Prediction Definition Outcome Field. . . . . . . . . . . . . . . . . . . . . . . . . 147
Smart Data Discovery Prescribable Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 148
Smart Data Discovery Projected Prediction Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 148
Smart Data Discovery Projected Prediction Settings. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 148
Smart Data Discovery Projected Predictions Count From Date Interval Setting. . . . . . . . . . . . 149
Smart Data Discovery Projected Predictions Count Interval Setting. . . . . . . . . . . . . . . . . . . . 149
Smart Data Discovery Projected Predictions Date Interval Setting. . . . . . . . . . . . . . . . . . . . . 150
Smart  Data  Discovery  Projected  Predictions  Override. . . . . . . . . . . . . . . . . . . . . . . . . . . . 150
Smart Data Discovery Projected Predictions. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 150
Smart Data Discovery Projected Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 151
Smart Data Discovery Pushback Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 152
Smart Data Discovery Outcome. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 152
Smart Data Discovery Recipient. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 153
Smart Data Discovery Refresh Config. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 153
Smart Data Discovery Refresh Job Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 153
Smart Data Discovery Refresh Job. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 154
Smart Data Discovery Refresh Task Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 155
Smart Data Discovery Refresh Task Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 155
Smart  Data  Discovery  Refresh  Task. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 155
Smart Data Discovery Regression Classification Prediction Property. . . . . . . . . . . . . . . . . . . 157
Smart Data Discovery Training Metrics. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 157
Smart Data Discovery User. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 157
Story  Diagnostic  Insights  Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 158
Story All Other Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 158
Story  Chart  Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 159
Story Chart Value Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 159
Story  Chart. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 161
Story  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 161
Story Count Insights Case. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 162
Story Day Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 162
Story Day of Week Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 163
Story  Descriptive  Insights  Case. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 163
Story Details. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 164
Story  Field  Correlation. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 164
Story Field Impact Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 165
## Contents

Story Field Label Value Property. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 165
Story Field Only. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 166
Story  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 166
Story First Order Insights. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 166
Story Insights Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 167
Story Month Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 168
Story Month of Year Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 168
Story Narrative Element Text. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 168
Story  Narrative. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 169
Story Null Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 169
Story  Potential  Bias. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 169
Story  Quarter  Field  Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 170
Story Quarter of Year Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 170
Story  Query  Diagnostic  Insights. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 171
Story Query Disparate Impact Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 171
Story  Query  Disparate  Impact. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 172
Story Query Input Parameter. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 172
Story  Query. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 173
Story  Range  Field  Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 174
Story  Second  Order  Insights. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 174
Story  Summary  Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 174
Story Text Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 175
Story  Version  Reference. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 175
Story  Version. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 175
Story. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 178
Story Year Field Value. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 181
Text  Field  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 182
Text Field Value Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 182
Validation  Dataset. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 182
Validation  Ratio. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 182
Einstein Discovery REST API Enums. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 184
## Contents



## EINSTEIN DISCOVERY REST API OVERVIEW
You can access Einstein Discovery features such as predictions, models, and stories programmatically using the Einstein Discovery REST
## API.
Using the Einstein Discovery REST API, you can:
## •
Create and retrieve Einstein Discovery predictions.
## •
Create and retrieve Einstein Discovery models.
## •
Create and retrieve Einstein Discovery stories.
For more information, see Einstein Prediction Service.
The Einstein Discovery REST API is based on the Connect REST API and follows its conventions. For more information about the Connect
REST API, see the Connect REST API Developer Guide.
Einstein Discovery Connect REST API Release Notes
Use the Salesforce Release Notes to learn about the most recent updates and changes to the Einstein Discovery Connect REST API.
Connect REST API Authorization
Connect REST API uses OAuth to securely identify your application before connecting to Salesforce.
API End-of-Life Policy
Salesforce is committed to supporting each API version for a minimum of three years from the date of first release. In order to mature
and improve the quality and performance of the API, versions that are more than three years old might cease to be supported.
Einstein Discovery Connect REST API Release Notes
Use the Salesforce Release Notes to learn about the most recent updates and changes to the Einstein Discovery Connect REST API.
For new and changed Einstein Discovery Connect REST resources and request and response bodies see CRM Analytics in the Salesforce
Release Notes and look for Einstein Discovery REST API.
Note:  If the API: New and Changed Items section in the Salesforce Release Notes isn’t present, there aren’t any updates for that
release.
Connect REST API Authorization
Connect REST API uses OAuth to securely identify your application before connecting to Salesforce.
OAuth and Connect REST API
For current OAuth information, see OAuth and Connect REST API in the Connect REST API developer guide.
## More Resources
Salesforce offers the following resources to help you navigate connected apps and OAuth:
## 1

## •
## Salesforce Help: Connected Apps
## •
Salesforce Help: Authorize Apps with OAuth
## •
Salesforce Help: OpenID Connect Token Introspection
## •
## Trailhead: Build Integrations Using Connected Apps
API End-of-Life Policy
Salesforce is committed to supporting each API version for a minimum of three years from the date of first release. In order to mature
and improve the quality and performance of the API, versions that are more than three years old might cease to be supported.
When an API version is to be deprecated, advance notice is given at least one year before support ends. Salesforce will directly notify
customers using API versions planned for deprecation.
Version Retirement InfoVersion Support StatusSalesforce API Versions
Supported.Versions 31.0 through 66.0
Salesforce Platform API Versions 21.0 through 30.0
## Retirement
As of Summer ’25, these versions are retired
and unavailable.
Versions 21.0 through 30.0
Salesforce Platform API Versions 7.0 through 20.0
## Retirement
As of Summer ’22, these versions are retired
and unavailable.
Versions 7.0 through 20.0
If you request any resource or use an operation from a retired API version, REST API returns 410:GONE error code.
To identify requests made from old or unsupported API versions of REST API, access the free API Total Usage event type.
## 2
API End-of-Life PolicyEinstein Discovery REST API Overview

## EINSTEIN DISCOVERY REST API EXAMPLES
Use Einstein Discovery REST API examples to perform tasks.
## Considerations
While using the Einstein Discovery REST API, keep this in mind:
## •
Request parameters may be included as part of the Einstein Discovery REST API resource URL, for example,
/smartdatadiscovery/models?q=status. A request body is a rich input which may be included as part of the request.
When accessing a resource, you can use either a request body or request parameters. You cannot use both.
## •
With a request body, use Content-Type:application/json or Content-Type:application/xml.
## •
With request parameters, use Content-Type:application/x-www-form-urlencoded.
## Get Predictions
The Einstein Prediction Service provides a REST API endpoint to request a prediction.
## Manage Prediction Definitions
The Einstein Prediction Service provides REST API endpoints to manage prediction definitions. A prediction definition specifies what
the model is trying to predict and the Salesforce entity associated with the prediction. Each prediction definition has a unique id.
Only certain attributes of a prediction definition can be modified.
## Manage Models
The Einstein Prediction Service provides REST API endpoints to manage models. Each model has a unique id. A model is used to
evaluate predictors and return predictions and improvements. These REST endpoints allow you to make updates to model metadata,
but not update the actual predictive model.
## Manage Prediction Jobs
The Einstein Prediction Service provides REST API endpoints to run bulk scoring jobs for a prediction. Bulk scoring jobs enable you
to score predictions on multiple records at a time. For example, after deploying an updated model, use bulk scoring to refresh all
prediction scores. You can also run bulk scoring on historical data to see how well your model performs. With bulk scoring, you can
score all records, a segment of the records, or records that haven’t reached the terminal state.
## Manage Model Refresh Jobs
The Einstein Prediction Service provides REST API endpoints to retrieve metadata for model refresh jobs.
## Query Prediction History
The Einstein Prediction Service provides a REST API endpoint to query prediction histories.
## Get Predictions
The Einstein Prediction Service provides a REST API endpoint to request a prediction.
## Prediction Request
POST/smartdatadiscovery/predict
## 3

POST Request Body
Use one of the following to create your request body, Smart Data Discovery Predict Input, Smart Data Discovery Predict Raw Data Input,
Smart Data Discovery Predict Record Overrides Input, or Smart Data Discovery Predict Record Input.
In the request body, you specify the prediction definition to use and the rows of data that you want to score. You can specify rows in
one of three available formats:
DescriptionFormat
Salesforce record Ids associated with the subscribedEntity of the prediction definition
(retrieved using a SOQL query).
## Records
A two-dimensional array of row values in which each row is a comma-separated list of values.RawData
Array of objects containing the Salesforce record Ids. Optionally, override or append values in
individual records with an array of row values (in which each row is a comma-separated list of
values).
RecordOverrides
When you run a prediction, Salesforce applies the model specified in the prediction definition to the set of records and returns a prediction
score for each record. If you specify 3 records, for example, you get 3 predictions in the order in which the records were specified in the
request.
Sample Request when type is Records
The following example shows a request body in which type is Records. The records attribute provides a comma-separated list
of Salesforce record Ids associated with the subscribedEntity of the prediction definition. You can retrieve a list of available
prediction definition Ids using the following API request:
GET /smartdatadiscovery/predictiondefinitions
You can specify up to 200 Salesforce record Ids. Two records are specified in the following example:
## {
"predictionDefinition":"1ORRM00000000304AA",
"type":"Records",
"records":["006RM000002bEfiYAE","006RM000002bEflYAE"]
## }
Sample Request when type is RawData
The following example shows a request body in which type is RawData. It names five columns and specifies two records with five
data values each. The columns were selected during the story setup process. For more information, see Create a Story.
## {
"predictionDefinition":"0OR1H000000Gma9WAC",
"type":"RawData",
"columnNames":["StageName","CloseDate","Account.BillingCountry","IsClosed","IsWon"],
## "rows":[
["Prospecting","2020-06-30","USA","false","false"],
["Qualification","2020-08-30","EMEA","false","false"]
## ]
## }
Sample Request when type is RecordOverrides
The following example shows a request body in which type is RecordOverrides. When specifying row data:
## 4
Get PredictionsEinstein Discovery REST API Examples

## •
Each Salesforce record Id represents a record in the subscribedEntity associated with the prediction definition.
## •
(Optional) Each row, where specified, contains the values to override or append to the data specified in the associated record.
You can specify up to 200 entries (record entries plus row entries) in a request. For example, if you have 120 record entries, you can
override up to 80 record entries with row entries. The following example specifies two columns with two record entries and two overrides.
## {
"predictionDefinition":"0OR1H000000Gma9WAC",
"type":"RecordOverrides",
"columnNames":["StageName","CloseDate"],
## "rows":[
## {
"record":"0061H00000dnhQEQAY",
"row":["Prospecting","2020-06-30"]
## },
## {
"record":"0061H00000dnhPzQAI",
"row":["Qualification","2020-08-30"]
## }
## ]
## }
Sample Request for Predictive Factors and Improvements
Starting in 50.0, this API returns a single prediction value by default. To request prediction factors and improvements, you must ask for
them explicitly in the request body. The following code snippet specifies settings to request prediction factors and improvements.
## {
"predictionDefinition":"1ORB0000000TNYIOA4",
"type":"Records",
"records":["006B0000002wvCtIAI"],
"settings":{"maxPrescriptions":3,
"maxMiddleValues":3,
"prescriptionImpactPercentage":87
## }
## }
In this example:
## •
maxPrescriptions specifies the maximum number of improvements (1-3) to return in the response
## •
maxMiddleValues specifies the number of top predictors (1-3) to return in the response
## •
prescriptionImpactPercentage specifies the threshold filter (minimum % improvement for the outcome, which in this
example is 87%) needed for the improvement to be returned in the response
To learn more about these settings and see these elements on an example Lightning page, see Add Einstein Predictions to a Lightning
## Page.
POST Response
The POST response is a Smart Data Discovery Predict List response.
## 5
Get PredictionsEinstein Discovery REST API Examples

Example POST Response
## {
"predictionDefinition": "1ORRM0000000030",
## "predictions": [ {
## "model": {
"id": "1OtRM000000002b0AA"
## },
## "prediction": {
"baseLine": 799315.4282959097,
"importWarnings": {
"mismatchedColumns": [ ],
"missingColumns": [ "OpportunityAge","Account.Owner.UniqueUserName",
"Account.Industry","Account.AccountSource","Account.Owner.Name","Account.BillingCountry",
"Name"],
"outOfBoundsColumns": [ ]
## },
"middleValues": [ {
## "columns": [ {
"columnName": "HasLineItem",
"columnValue": "true"
## } ],
## "value": 543763.66105859
## } ],
## "other": 0.0,
"smallTermCount": 0,
## "total": 1343079.0893544997
## },
## "prescriptions": [ ],
"status": "Success"
## }, {
## "model": {
"id": "1OtRM000000002b0AA"
## },
## "prediction": {
"baseLine": 799315.4282959097,
"importWarnings": {
"mismatchedColumns": [ ],
"missingColumns": [ "OpportunityAge","Account.Owner.UniqueUserName",
"Account.Industry","Account.AccountSource","Account.Owner.Name","Account.BillingCountry",
"Name"],
"outOfBoundsColumns": [ ]
## },
"middleValues": [ {
## "columns": [ {
"columnName": "HasLineItem",
"columnValue": "true"
## } ],
## "value": 543763.66105859
## } ],
## "other": 0.0,
"smallTermCount": 0,
## "total": 1343079.0893544997
## },
## "prescriptions": [ ],
## 6
Get PredictionsEinstein Discovery REST API Examples

"status": "Success"
## } ],
## "settings": {
"maxPrescriptions": 0,
"maxMiddleValues": 0,
"prescriptionImpactPercentage": 0
## }
## }
## Manage Prediction Definitions
The Einstein Prediction Service provides REST API endpoints to manage prediction definitions. A prediction definition specifies what the
model is trying to predict and the Salesforce entity associated with the prediction. Each prediction definition has a unique id. Only certain
attributes of a prediction definition can be modified.
## Get Available Prediction Definitions
GET /smartdatadiscovery/predictiondefinitions
The following code shows an example Smart Data Discovery Prediction Definition Collection response:
## HTTP/1.1200 OK
Date:Tue,15 Sep 202021:58:01GMT
Strict-Transport-Security:max-age=31536000;includeSubDomains
X-Content-Type-Options:nosniff
X-XSS-Protection:1; mode=block
X-Robots-Tag:none
X-B3-TraceId:d16d33c8d031db6e
X-B3-SpanId:d16d33c8d031db6e
X-B3-Sampled:0
Cache-Control:no-cache,must-revalidate,max-age=0,no-store,private
Set-Cookie:BrowserId=hf3WNPeeEeqhuDcd5jEV6A;domain=.salesforce.com;path=/;expires=Wed,
15-Sep-202121:58:01GMT;Max-Age=31536000
Content-Type:application/json;charset=UTF-8
Vary:Accept-Encoding
Content-Encoding:gzip
Transfer-Encoding:chunked
## {
"nextPageUrl": null,
"predictionDefinitions": [ {
"countOfActiveModels": 1,
"countOfModels": 1,
"createdBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"createdDate": "2020-04-22T01:25:19.000Z",
## 7
Manage Prediction DefinitionsEinstein Discovery REST API Examples

"id": "1ORB000000000bOOAQ",
"label": "MaximizeCLV - firstversion",
"lastModifiedBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"lastModifiedDate": "2020-04-22T01:25:19.000Z",
"modelsUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB000000000bOOAQ/models",
"name": "Maximize_CLV_first_version7c48e8db",
## "outcome": {
"goal": "Maximize",
"label": "CLV",
"name": "CLV"
## },
"predictionType": "Regression",
"status": "Enabled",
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB000000000bOOAQ"
## }, {
"countOfActiveModels": 1,
"countOfModels": 1,
"createdBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"createdDate": "2020-01-13T21:28:06.000Z",
"id": "1ORB00000004CAkOAM",
"label": "Won_Won",
"lastModifiedBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"lastModifiedDate": "2020-04-14T20:37:21.000Z",
"modelsUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CAkOAM/models",
"name": "Won_Wone329300b",
## "outcome": {
"goal": "Maximize",
"label": "Won",
"name": "Won"
## },
"predictionType": "Classification",
"status": "Enabled",
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CAkOAM"
## 8
Manage Prediction DefinitionsEinstein Discovery REST API Examples

## }, {
"countOfActiveModels": 2,
"countOfModels": 2,
"createdBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"createdDate": "2020-01-17T00:24:33.000Z",
"id": "1ORB00000004CApOAM",
"label": "CLVPrediction",
"lastModifiedBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"lastModifiedDate": "2020-01-17T00:24:33.000Z",
"modelsUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM/models",
"name": "CLV_Prediction3d72828a",
## "outcome": {
"goal": "Maximize",
"label": "CLV",
"name": "CLV"
## },
"predictionType": "Regression",
"status": "Enabled",
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM"
## }, {
"countOfActiveModels": 1,
"countOfModels": 1,
"createdBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"createdDate": "2020-02-04T08:28:14.000Z",
"id": "1ORB00000004CCCOA2",
"label": "CLV_CLV",
"lastModifiedBy": {
"id": "005B0000001nz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000008pwV/T"
## },
"lastModifiedDate": "2020-02-04T08:28:14.000Z",
"modelsUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CCCOA2/models",
## 9
Manage Prediction DefinitionsEinstein Discovery REST API Examples

"name": "CLV_CLVa7cf508c",
## "outcome": {
"goal": "Maximize",
"label": "CLV",
"name": "CLV"
## },
"predictionType": "Regression",
"status": "Enabled",
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CCCOA2"
## } ],
"totalSize": 4,
## "url": "/services/data/v52.0/smartdatadiscovery/predictiondefinitions"
## }
Get Metadata for a Prediction Definition
GET /smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>
The following code shows an example Smart Data Discovery Prediction Definition response:
## HTTP/1.1200 OK
Date:Thu,17 Sep 202016:27:43GMT
Strict-Transport-Security:max-age=31536002;includeSubDomains
Public-Key-Pins-Report-Only:pin-sha256="9n0izTnSRF+W4W4JTq51avSXkWhQB8duS2bxVLfzXsY=";
pin-sha256="5kJvNEMw0KjrCAu7eXY5HZdvyCS13BbA0VJG1RSP91w=";
pin-sha256="njN4rRG+22dNXAi+yb8e3UMypgzPUPHlv4+foULwl1g=";max-age=86400;includeSubDomains;
report-uri="https://a.forcesslreports.com/hpkp-report/00DB0000000K2Uzm";
Expect-CT:max-age=86400,
report-uri="https://a.forcesslreports.com/Expect-CT-report/00DB0000000K2Uzm"
X-Content-Type-Options:nosniff
X-XSS-Protection:1; mode=block
X-Robots-Tag:none
X-B3-TraceId:da9949518cdecb56
X-B3-SpanId:da9949518cdecb56
X-B3-Sampled:0
Cache-Control:no-cache,must-revalidate,max-age=0,no-store,private
Set-Cookie:BrowserId=tsMTvvkCEeqU9WHivUXHfA;domain=.salesforce.com;path=/;expires=Fri,
17-Sep-202116:27:43GMT;Max-Age=31536000
Content-Type:application/json;charset=UTF-8
Vary:Accept-Encoding
Content-Encoding:gzip
Transfer-Encoding:chunked
## {
"countOfActiveModels": 1,
"countOfModels": 1,
"createdBy": {
"id": "005B0000004iaa7IAA",
"name": "AdminUser",
"profilePhotoUrl": "https://MyDomainName.file.force.com/profilephoto/729B0000000EmIX/T"
## 10
Manage Prediction DefinitionsEinstein Discovery REST API Examples

## },
"createdDate": "2020-03-31T01:18:51.000Z",
"id": "1ORB000000000JuOAI",
"label": "ItalyInfo",
"lastModifiedBy": {
"id": "005B00000051RBqIAM",
"name": "YourUserName",
"profilePhotoUrl": "https://MyDomainName.file.force.com/profilephoto/729B00000003ARf/T"
## },
"lastModifiedDate": "2020-08-18T23:09:25.000Z",
"modelsUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB000000000JuOAI/models",
"name": "ItalyInfo9461190a",
## "outcome": {
"goal": "Minimize",
"label": "TotalCases",
## "name": "totale_casi"
## },
"predictionType": "Regression",
"pushbackField": {
"label": "mypredField",
"name": "Custom_Opportunity__c.mypredField__c"
## },
"refreshConfig": {
"isEnabled": true,
"recipientList": [ {
"displayName": "YourUserName",
"id": "005B00000051RBqIAM",
"type": "User"
## } ],
## "schedule": {
"dayInWeek": "wednesday",
## "frequency": "monthlyrelative",
"nextScheduledDate": "2020-10-08T02:00:00.000Z",
## "time": {
## "hour": 19,
"timeZone": {
"gmtOffset": -7.0,
"name": "PacificDaylightTime",
"zoneId": "America/Los_Angeles"
## }
## },
"weekInMonth": "first"
## },
"shouldScoreAfterRefresh": false,
"userContext": {
"id": "005B00000051RBqIAM"
## },
"warningThresholdPercentage": 0.05
## },
"status": "Enabled",
"subscribedEntity": "Custom_Opportunity__c",
## 11
Manage Prediction DefinitionsEinstein Discovery REST API Examples

"url": "/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB000000000JuOAI"
## }
The refreshConfig section describes model refresh jobs for this prediction. Model refresh jobs are configured in Model Manager
as described in Configure Automatic Model Refresh for a Prediction.
Delete a Prediction Definition
DELETE/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>
## Manage Models
The Einstein Prediction Service provides REST API endpoints to manage models. Each model has a unique id. A model is used to evaluate
predictors and return predictions and improvements. These REST endpoints allow you to make updates to model metadata, but not
update the actual predictive model.
## Get Available Models
GET /smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/models
This code shows an example response of a Smart Data Discovery Model Collection.
## HTTP/1.1200 OK
Date:Thu,30 Jan 202017:34:12GMT
Strict-Transport-Security:max-age=31536000;includeSubDomains
X-Content-Type-Options:nosniff
X-XSS-Protection:1; mode=block
X-Robots-Tag:none
Cache-Control:no-cache,must-revalidate,max-age=0,no-store,private
Set-Cookie:BrowserId=uqyLl0OGEeq2RPW2iPHbvQ;domain=.salesforce.com;path=/;expires=Fri,
29-Jan-202117:34:12GMT;Max-Age=31536000
Content-Type:application/json;charset=UTF-8
Vary:Accept-Encoding
Content-Encoding:gzip
Transfer-Encoding:chunked
## {
## "models": [ {
"actionableVariables": [ {
"label": "Type",
"name": "Type",
"type": "Text"
## }, {
"label": "Ownership",
"name": "Ownership",
"type": "Text"
## }, {
"label": "Rating",
"name": "Rating",
"type": "Text"
## 12
Manage ModelsEinstein Discovery REST API Examples

## }, {
"label": "Division",
"name": "Division",
"type": "Text"
## }, {
"label": "AccountScore",
"name": "AccountScore",
"type": "Text"
## } ],
"createdBy": {
"id": "005B0000002zz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000009ttx/T"
## },
"createdDate": "2020-01-17T00:24:35.000Z",
"fieldMappingList": [ {
"modelField": {
"label": "CloseDate",
"name": "CloseDate",
"type": "Date"
## }
## }, {
"modelField": {
"label": "Industry",
"name": "Industry",
"type": "Text"
## }
## }, {
"modelField": {
"label": "StartDate",
"name": "StartDate",
"type": "Date"
## }
## }, {
"modelField": {
"label": "Ownership",
"name": "Ownership",
"type": "Text"
## }
## }, {
"modelField": {
"label": "Type",
"name": "Type",
"type": "Text"
## }
## }, {
"modelField": {
"label": "Rating",
"name": "Rating",
"type": "Text"
## }
## }, {
"modelField": {
## 13
Manage ModelsEinstein Discovery REST API Examples

"label": "BillingState",
"name": "BillingState",
"type": "Text"
## }
## }, {
"modelField": {
"label": "Division",
"name": "Division",
"type": "Text"
## }
## }, {
"modelField": {
"label": "AccountScore",
"name": "AccountScore",
"type": "Text"
## }
## } ],
## "filters": [ ],
"id": "1OtB00000004CApKAM",
"label": "CLV",
"lastModifiedBy": {
"id": "005B0000002zz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000009ttx/T"
## },
"lastModifiedDate": "2020-01-17T00:24:35.000Z",
## "model": {
"id": "1OTB000000000ajOAA"
## },
"modelType": "Regression",
"name": "CLV",
"predictionDefinitionUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM",
"sortOrder": 0,
"status": "Enabled",
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM/models/1OtB00000004CApKAM"
## }, {
"actionableVariables": [ {
"label": "Industry",
"name": "Industry",
"type": "Text"
## }, {
"label": "Type",
"name": "Type",
"type": "Text"
## }, {
"label": "Ownership",
"name": "Ownership",
"type": "Text"
## }, {
"label": "Rating",
## 14
Manage ModelsEinstein Discovery REST API Examples

"name": "Rating",
"type": "Text"
## }, {
"label": "Division",
"name": "Division",
"type": "Text"
## } ],
"createdBy": {
"id": "005B0000002zz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000009ttx/T"
## },
"createdDate": "2020-01-17T00:26:14.000Z",
"fieldMappingList": [ {
"modelField": {
"label": "CloseDate",
"name": "CloseDate",
"type": "Date"
## }
## }, {
"modelField": {
"label": "Industry",
"name": "Industry",
"type": "Text"
## }
## }, {
"modelField": {
"label": "StartDate",
"name": "StartDate",
"type": "Date"
## }
## }, {
"modelField": {
"label": "Ownership",
"name": "Ownership",
"type": "Text"
## }
## }, {
"modelField": {
"label": "Type",
"name": "Type",
"type": "Text"
## }
## }, {
"modelField": {
"label": "Rating",
"name": "Rating",
"type": "Text"
## }
## }, {
"modelField": {
"label": "BillingState",
"name": "BillingState",
## 15
Manage ModelsEinstein Discovery REST API Examples

"type": "Text"
## }
## }, {
"modelField": {
"label": "Division",
"name": "Division",
"type": "Text"
## }
## }, {
"modelField": {
"label": "AccountScore",
"name": "AccountScore",
"type": "Text"
## }
## } ],
## "filters": [ ],
"id": "1OtB00000004CAqKAM",
"label": "CLV",
"lastModifiedBy": {
"id": "005B0000002zz1lIAA",
"name": "MyUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B00000009ttx/T"
## },
"lastModifiedDate": "2020-01-17T00:26:14.000Z",
## "model": {
"id": "1OTB000000000ajOAA"
## },
"modelType": "Regression",
"name": "CLV",
"predictionDefinitionUrl":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM",
"sortOrder": 1,
"status": "Enabled",
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM/models/1OtB00000004CAqKAM"
## } ],
"totalSize": 2,
## "url":
"/services/data/v52.0/smartdatadiscovery/predictiondefinitions/1ORB00000004CApOAM/models"
## }
Get Metadata for a Model
GET /smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/models/<modelId>
Delete a Model
DELETE/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>
/models/<modelId>
## 16
Manage ModelsEinstein Discovery REST API Examples

## Manage Prediction Jobs
The Einstein Prediction Service provides REST API endpoints to run bulk scoring jobs for a prediction. Bulk scoring jobs enable you to
score predictions on multiple records at a time. For example, after deploying an updated model, use bulk scoring to refresh all prediction
scores. You can also run bulk scoring on historical data to see how well your model performs. With bulk scoring, you can score all records,
a segment of the records, or records that haven’t reached the terminal state.
Bulk scoring jobs are configured in Model Manager. To set up Bulk Scoring jobs, see Score Records in Bulk.
Note:  If the daily predictions limit is reached in your org, active scoring jobs are paused, then resumed the next day.
Run a Bulk Scoring Job for a Prediction
POST/smartdatadiscovery/predict-jobs
POST Request Body
Use the Smart Data Discovery Job Predict Input to create your request body. In the request body, specify the prediction definition Id
associated with the bulk scoring request job, along with a user-defined label, and optional filter settings.
## {
"predictionDefinition":{"id":"{{predictionDefinitionId}}" },
## "label":"{{label}}",
"useTerminalStateFilter": false,
## "filters":{
## "filters":[
## {
"fieldName":"Opportunity.Name",
"values":["My Opportunity"],
"operator":"Equal"
## }
## ]
## }
## }
You can retrieve a list of available prediction definition Ids using the following API request:
GET /smartdatadiscovery/predictiondefinitions
## Get Scoring Jobs
GET smartdatadiscovery/predict-jobs
## Manage Model Refresh Jobs
The Einstein Prediction Service provides REST API endpoints to retrieve metadata for model refresh jobs.
Model refresh jobs are configured in Model Manager. To set up model refresh jobs, see Configure Automatic Model Refresh for a Prediction
## Definition.
## 17
Manage Prediction JobsEinstein Discovery REST API Examples

## Get Prediction Refresh Jobs
GET /smartdatadiscovery/refresh-jobs
The following code shows an example Smart Data Discovery Refresh Job Collection response.
## {
"refreshJobs": [ {
"createdBy": {
"id": "005B0000006DdetIAC",
"name": "YourUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B0000000Eqe5/T"
## },
"createdDate": "2020-09-09T16:16:39.000Z",
"endTime": "2020-09-09T16:20:02.000Z",
"id": "1OXB00000008OIPOA2",
"refreshTarget": {
"id": "1ORB0000000TNXyOAO"
## },
"refreshTasksUrl":
"/services/data/v52.0/smartdatadiscovery/refresh-jobs/1OXB00000008OIPOA2/refresh-tasks",
"startTime": "2020-09-09T16:16:41.000Z",
"status": "Success",
"type": "UserTriggered","url":
"/services/data/v52.0/smartdatadiscovery/refresh-jobs/1OXB00000008OIPOA2"
## } ],
"totalSize": 1,
## "url": "/services/data/v52.0/smartdatadiscovery/refresh-jobs"
## }
## Get Prediction Refresh Job Details
GET /smartdatadiscovery/refresh-jobs/<refreshJobId>
The following code shows an example response.
## {
"refreshJobs": [ {
"createdBy": {
"id": "005B0000006DdetIAC",
"name": "YourUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B0000000Eqe5/T"
## },
"createdDate": "2020-09-09T16:16:39.000Z",
"endTime": "2020-09-09T16:20:02.000Z",
"id": "1OXB00000008OIPOA2",
"refreshTarget": {
"id": "1ORB0000000TNXyOAO"
## },
"refreshTasksUrl":
"/services/data/v52.0/smartdatadiscovery/refresh-jobs/1OXB00000008OIPOA2/refresh-tasks",
"startTime": "2020-09-09T16:16:41.000Z",
## 18
Manage Model Refresh JobsEinstein Discovery REST API Examples

"status": "Success",
"type": "UserTriggered",
"url": "/services/data/v52.0/smartdatadiscovery/refresh-jobs/1OXB00000008OIPOA2"
## }
## Get Prediction Refresh Job Task Details
GET /smartdatadiscovery/refresh-jobs/<refreshJobId>/refresh-tasks
The following code shows an example Smart Data Discovery Refresh Job response.
## {
"refreshTasks": [ {
"createdBy": {
"id": "005B0000006DdetIAC",
"name": "YourUserName",
"profilePhotoUrl":
"https://MyDomainName.file.force.com/profilephoto/729B0000000Eqe5/T"
## },
"createdDate": "2020-09-09T16:16:39.000Z",
"endTime": "2020-09-09T16:19:54.000Z",
"id": "1OxB00000008OIKKA2",
"refreshTarget": {
"id": "1OtB0000000TNdAKAW",
"label": "IsWon",
"name": "IsWon"
## },
"refreshedAIModel": {
"id": "1OTB0000000PDeBOAW"
## },
## "source": {
## "story": {
"id": "1Y3B00000004HOCKA2"
## },
"storyVersion": {
"id": "9B4B00000008UrEKAU"
## }
## },
"startTime": "2020-09-09T16:16:45.000Z",
"status": "Success"
## } ],
"totalSize": 1,
## "url":
"/services/data/v52.0/smartdatadiscovery/refresh-jobs/1OXB00000008OIPOA2/refresh-tasks"
## }
## Query Prediction History
The Einstein Prediction Service provides a REST API endpoint to query prediction histories.
## 19
Query Prediction HistoryEinstein Discovery REST API Examples

## Predict History Request
POST/smartdatadiscovery/predict-history
POST Request Body
Use the Predict History Input to create your request body.
In the request body, you specify the ID of the goal, the prediction history range, and a list of targets.
DescriptionFormat
The ID of the prediction definition to query for historical predictions.goalId
A list of opportunity IDs as strings to use for the target entities of the query. The list is limited to
1 entry.
targets
An optional range for the query. Use the Predict History Range Input to specify the range. The
range includes:
range
## •
maxLookBack an optional value to specify the number of prediction history values. 1-3
are the valid values, with a default value of 1.
## •
interval an optional value to specify the prediction history interval. Valid values are
Weekly or None, with a default value of Weekly.
Example: Query prediction history with a maxLookBack of 2
Query the prediction history using the following API request:
POST/smartdatadiscovery/predict-history
Request body:
## {
"targets": [ "1Otxx00000000304AA"],
"goalId": "1ORxx00000000509BA",
## "range": {
"maxLookBack": 2
## }
## }
POST Response Body
The POST response is a Predict History Collection.
Example: Response body:
## {
## "history": [
## {
"target": "006xx000001a2p3AAA",
## "predictions": [
## 20
Query Prediction HistoryEinstein Discovery REST API Examples

## {
"createdDate": "2022-09-16T19:47:14.000Z",
## "value": "21.69962721629",
"model"{ "id": "1Otxx00000000304AA"}
## },
## {
"createdDate": "2022-09-16T19:47:15.000Z",
## "value": "21.83126271983",
"model"{ "id": "1Otxx00000000304AA"}
## }
## ]
## }
## ],
## "range": {
"maxLookBack": 2,
"interval": "Weekly"
## }
## }
## 21
Query Prediction HistoryEinstein Discovery REST API Examples

## EINSTEIN DISCOVERY REST RESOURCES
REST API resources are sometimes called endpoints.
## Smart Data Discovery Resource
Lists the top-level resources available for Einstein Discovery.
## Model Resources
Einstein Discovery models are sophisticated, custom mathematical constructs that are used to predict particular outcomes.
## Metrics Resource
Returns the metrics collection for Einstein Discovery.
## Narrative Resource
Returns the narrative data for an Einstein Discovery story.
## Prediction Definition Resources
A prediction definition specifies what the model is trying to predict and the Salesforce entity associated with the prediction. Each
prediction definition has a unique id. Only certain attributes of a prediction definition can be modified.
## Predict Jobs Resources
Predict jobs run bulk scoring jobs for predictions. Bulk scoring jobs enable scoring predictions on multiple records at a time. For
example, after deploying an updated model, use bulk scoring to refresh all prediction scores.
## Predict Resource
Make an Einstein Discovery prediction.
## Predict History Resource
Query the history of Einstein Discovery predictions.
## Refresh Jobs Resources
Refresh jobs run refresh Einstein Discovery models.
## Stories Resources
Einstein Discovery stories are used to analyze your data. The insights from stories show you what happened in your data, why it
happened, and what could happen.
Einstein Discovery REST API Resources Overview
The Einstein Discovery REST API provides resources so you can access your Einstein Discovery insights.
All Einstein Discovery REST API resources are accessed using:
## •
A base URL for your company (for example, https://yourInstance.salesforce.com)
## •
Version information (for example, /services/data/v53.0)
## •
A named resource (for example, /smartdatadiscovery)
Put together, an example of the full URL to the resource is:
https://yourInstance.salesforce.com/services/data/v55.0/smartdatadiscovery
Org and Object Identifiers
## 22

Id fields in Salesforce, and for Einstein Discovery, are typically 15-character, base-62, case-sensitive strings. However, many Salesforce
APIs, including the Einstein Discovery REST API, use 18-character, case-insensitive strings—for example, the Id property of the Story
resource /smartdatadiscovery/stories/<storyID>. The last 3 digits are a checksum of the preceding 15 characters.
The use of case-insensitive Id’s eases interaction with external applications and development environments that use case-insensitive
references. To convert an 18-character Id back to a 15-character ID, simply remove the last 3 characters.
## General Resources
General resources for Einstein Discovery are covered here, while specific features like prediction definitions and stories have their own
sections.
Resource URLSupported
## HTTP
## Method
DescriptionResource
/smartdatadiscovery/metricsGETReturns the metrics for Einstein Discovery.Metrics Resource
/smartdatadiscovery/narrativePOSTReturns the narrative data for an Einstein
Discovery story.
## Narrative
## Resource
/smartdatadiscovery/predictPOSTCreates an Einstein Discovery prediction.Predict Resource
/smartdatadiscovery/predict-historyPOSTQuery the history of Einstein Discovery
predictions.
## Predict History
## Resource
/smartdatadiscoveryGETLists the top-level resources available for Einstein
## Discovery.
## Smart Data
## Discovery
## Resource
Filtering REST Responses
In addition to Einstein Discovery REST API input parameters, you can use the following Connect REST API input parameters to filter the
results returned from a request: filterGroup, external, and internal. For more information, see Specifying Response Sizes
in the Connect REST API Developer Guide.
## Smart Data Discovery Resource
Lists the top-level resources available for Einstein Discovery.
Resource URL
## /smartdatadiscovery
## Formats
## JSON
## Available Version
## 46.0
HTTP Methods
## GET
Response body for GET
## Directory Item Collection
## 23
Smart Data Discovery ResourceEinstein Discovery REST Resources

## Model Resources
Einstein Discovery models are sophisticated, custom mathematical constructs that are used to predict particular outcomes.
Available resources:
Resource URLSupported
## HTTP
## Method
DescriptionResource
/smartdatadiscovery/modelsGET POSTReturns a collection of Einstein Discovery
models and creates a model.
## Models
## Resource
/smartdatadiscovery/models/<modelId>GET
## PATCH
## DELETE
Returns a model, updates a model, or deletes a
model.
## Model Resource
/smartdatadiscovery/models/<modelId>
## /coefficients
GETReturns the coefficients for a model.Model
## Coefficients
## Resource
/smartdatadiscovery/models/<modelId>
## /file
GETReturns a binary stream of the model file
contents.
## Model File
## Resource
/smartdatadiscovery/models/<modelId>
## /metrics
GETReturns the metrics for a specified model.Model Metrics
## Resource
/smartdatadiscovery/models/<modelId>
## /metrics/residuals
GETReturns the metrics residuals for a specified
model.
## Model Metrics
## Residuals
## Resource
/smartdatadiscovery/models/<modelId>
## /metrics/feature-importances
GETReturns the importance metrics for a specified
model.
## Model Metrics
## Feature
## Importances
## Resource
## Models Resource
Returns a collection of Einstein Discovery models and creates a model.
## Model Resource
Returns an Einstein Discovery model, updates a model, or deletes a model.
## Model Coefficients Resource
Returns a collection of coefficients for an Einstein Discovery model.
## Model File Resource
Returns a binary stream of the Einstein Discovery model file contents.
## Model Metrics Resource
Returns the metrics for an Einstein Discovery model.
## Model Metrics Residuals Resource
Returns the metrics residuals for an Einstein Discovery model.
## 24
Model ResourcesEinstein Discovery REST Resources

## Model Metrics Feature Importances Resources
Returns the importance metrics for an Einstein Discovery Model
## Models Resource
Returns a collection of Einstein Discovery models and creates a model.
Resource URL
## /smartdatadiscovery/models
## Formats
## JSON
## Available Version
## 48.0
HTTP Methods
## GET POST
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
48.0OptionalThe sort order for the collection. Valid
values are:
SmartDataDiscovery
SortOrderEnum
order
## •
## Ascending
## •
## Descending
48.0OptionalA generated token that indicates the view
of models to be returned.
## Stringpage
48.0OptionalThe number of items to be returned in a
single page. Minimum is 1, maximum is
200, and default is 25.
IntegerpageSize
48.0OptionalSearch terms. Individual terms are
separated by spaces. A wildcard is
## Stringq
automatically appended to the last token
in the query string. If the user’s search
query contains quotation marks or
wildcards, those symbols are automatically
removed from the query string in the URI
along with any other special characters.
48.0OptionalThe sort order type for the collection. Valid
values are:
SmartDataDiscovery
AIModelCollection
SortOrderTypeEnum
sort
## •
CreatedDate
## •
## Description
## •
## Name
## •
PredictionFieldName
## 25
Models ResourceEinstein Discovery REST Resources

## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
## •
PredictionType
## •
RuntimeType
48.0OptionalFilters the collection by source type. Valid
values are:
SmartDataDiscovery
ModelSourceType
## Enum
sourceType
## •
## Discovery
## •
UserUpload
48.0OptionalFilters the collection by status. Valid values
are:
SmartDataDiscovery
AIModelStatusEnum
status
## •
## Disabled
## •
## Enabled
## •
UploadCompleted
## •
UploadFailed
## •
## Uploading
## •
## Validating
## •
ValidationCompleted
## •
ValidationFailed
48.0OptionalFilters the collection by story history ID
## (9B4).
StringstoryHistory
## Id
48.0OptionalFilters the collection by story ID (1Y3).StringstoryId
Response body for GET
Smart Data Discovery AI Model Collection
Request body for POST
Smart Data Discovery AI Model Input
Response body for POST
Smart Data Discovery AI Model
## Model Resource
Returns an Einstein Discovery model, updates a model, or deletes a model.
Resource URL
/smartdatadiscovery/models/<modelId>
## Formats
## JSON
## Available Version
## 48.0 GET DELETE, 50.0 PATCH
## 26
Model ResourceEinstein Discovery REST Resources

HTTP Methods
## GET PATCH DELETE
Request parameters for GET and DELETE
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
48.0RequiredThe ID of the model to retrieve, update, or
delete.
StringmodelId
Response body for GET and PATCH
Smart Data Discovery AI Model
Request parameters for PATCH
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
50.0RequiredThe model information to update.SmartDataDiscovery
AIModelInput
model
50.0RequiredThe ID of the model to retrieve, update, or
delete.
StringmodelId
## Model Coefficients Resource
Returns a collection of coefficients for an Einstein Discovery model.
Resource URL
/smartdatadiscovery/models/<modelId>/coefficients
## Formats
## JSON
## Available Version
## 55.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
55.0RequiredThe ID of the model to retrieve the
coefficients for.
StringmodelId
55.0OptionalA generated token that indicates the view
of model metrics to be returned.
## Stringpage
## 27
Model Coefficients ResourceEinstein Discovery REST Resources

## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
55.0OptionalThe number of items to be returned in a
single page. Minimum is 1, maximum is
200, and default is 25.
IntegerpageSize
Response body for GET
Smart Data Discovery AI Model Coefficient Collection
## Model File Resource
Returns a binary stream of the Einstein Discovery model file contents.
Resource URL
/smartdatadiscovery/models/<modelId>/file
## Formats
## JSON
## Available Version
## 49.0 GET
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
49.0RequiredThe ID of the model to retrieve the file for.StringmodelId
Response body for GET
StreamedRepresentation. Returns a binary stream of the JSON contents of the specified file.
## Model Metrics Resource
Returns the metrics for an Einstein Discovery model.
Resource URL
/smartdatadiscovery/models/<modelId>/metrics
## Formats
## JSON
## Available Version
## 54.0
HTTP Methods
## GET
## 28
Model File ResourceEinstein Discovery REST Resources

Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
54.0RequiredThe ID of the model to retrieve the metrics
for.
StringmodelId
Response body for GET
Abstract Smart Data Discovery AI Model Metrics - Specific implementations include: Smart Data Discovery AI Model Classification
Metrics, Smart Data Discovery AI Model Multiclass Metrics, and Smart Data Discovery AI Model Regression Metrics
## Model Metrics Residuals Resource
Returns the metrics residuals for an Einstein Discovery model.
Resource URL
/smartdatadiscovery/models/<modelId>/metrics/residuals
## Formats
## JSON
## Available Version
## 55.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
55.0RequiredThe ID of the model to retrieve the metrics
residuals for.
StringmodelId
55.0OptionalA generated token that indicates the view
of metrics residuals to be returned.
## Stringpage
55.0OptionalThe number of items to be returned in a
single page. Minimum is 1, maximum is
200, and default is 25.
IntegerpageSize
Response body for GET
Smart Data Discovery AI Model Residual Collection
## Model Metrics Feature Importances Resources
Returns the importance metrics for an Einstein Discovery Model
## 29
Model Metrics Residuals ResourceEinstein Discovery REST Resources

Resource URL
/smartdatadiscovery/models/${modelId}/metrics/feature-importances
## Formats
## JSON
## Available Version
## 56.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
56.0RequiredThe ID of the model to retrieve the
importance metrics.
StringmodelId
Response body for GET
## Smart Data Discovery Feature Importance Metric
## Metrics Resource
Returns the metrics collection for Einstein Discovery.
Resource URL
## /smartdatadiscovery/metrics
## Formats
## JSON
## Available Version
## 50.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
50.0OptionalThe count for the collection.Integercount
50.0OptionalThe time span for the metrics. Valid values
are:
MetricSpanEnumspan
## •
## Day
## •
## Month
## •
SinceLastAction
## •
## Week
## 30
Metrics ResourceEinstein Discovery REST Resources

Response body for GET
## Smart Data Discovery Metrics Collection
## Narrative Resource
Returns the narrative data for an Einstein Discovery story.
Resource URL
## /smartdatadiscovery/narrative
## Formats
## JSON
## Available Version
## 51.0
HTTP Methods
## POST
Request body for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
51.0OptionalThe narrative to return data for.SmartDataDiscovery
NarrativeInput
narrative
Response body for POST
## Smart Data Discovery Narrative Field Collection
## Prediction Definition Resources
A prediction definition specifies what the model is trying to predict and the Salesforce entity associated with the prediction. Each
prediction definition has a unique id. Only certain attributes of a prediction definition can be modified.
Available resources:
Resource URLSupported
## HTTP
## Method
DescriptionResource
## /smartdatadiscovery
## /predictiondefinitions
GETReturns a collection of Einstein Discovery
prediction definitions.
## Prediction
## Definitions
## Resource
## /smartdatadiscovery
## /predictiondefinitions
/<predictionDefinitionIdOrName>
## GET
## DELETE
Returns or deletes a prediction definition.Prediction
## Definition
## Resource
## /smartdatadiscovery
## /predictiondefinitions
GETReturns a model card for an Einstein Discovery
prediction definition.
## Prediction
## Definition
## 31
Narrative ResourceEinstein Discovery REST Resources

Resource URLSupported
## HTTP
## Method
DescriptionResource
## Model Cards
## Resource
/<predictionDefinitionIdOrName>
## /modelcards
## /smartdatadiscovery
## /predictiondefinitions
DELETEDeletes a prediction definition model card.Prediction
## Definition
## Model Card
## Resource
/<predictionDefinitionIdOrName>
/modelcards/<modelCardId>
## /smartdatadiscovery
## /predictiondefinitions
GET POSTReturns a collection of Einstein Discovery
prediction definition models.
## Prediction
## Definition
## Models
## Resource
/<predictionDefinitionIdOrName>
## /models
## /smartdatadiscovery
## /predictiondefinitions
## GET
## PATCH
## DELETE
Returns or deletes a model for an Einstein
Discovery prediction definition.
## Prediction
## Definition
## Model Resource
/<predictionDefinitionIdOrName>
/models/<modelId>
## /smartdatadiscovery
## /predictiondefinitions
GETReturns a collection of metrics for a prediction
definition model.
## Prediction
## Definition
## Model Metrics
## Resource
/<predictionDefinitionIdOrName>
/models/<modelId>/metrics
## Examples
For use cases to manage prediction definitions, see Manage Prediction Definitions.
For use cases to manage models, see Manage Models.
## Prediction Definitions Resource
Returns a collection of Einstein Discovery prediction definitions.
## Prediction Definition Resource
Returns or deletes an Einstein Discovery prediction definition.
## Prediction Definition Model Cards Resource
Returns a model card for an Einstein Discovery prediction definition.
## Prediction Definition Model Card Resource
Deletes a prediction definition model card.
## Prediction Definitions Models Resource
Returns a collection of Einstein Discovery prediction definition models.
## Prediction Definitions Model Resource
Returns or deletes a model for an Einstein Discovery prediction definition.
## Prediction Definitions Model Metrics Resource
Returns a collection of metrics for a prediction definition model.
## 32
Prediction Definition ResourcesEinstein Discovery REST Resources

## Prediction Definitions Resource
Returns a collection of Einstein Discovery prediction definitions.
Resource URL
## /smartdatadiscovery/predictiondefinitions
## Formats
## JSON
## Available Version
## 41.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0OptionalThe model source type to filter the
collection by. Valid values are:
SmartDataDiscovery
ModelSourceType
## Enum
modelSource
## •
## Discovery
## •
UserUpload
41.0OptionalThe sort order for the collection. Valid
values are:
SmartDataDiscovery
SortOrderEnum
order
## •
## Ascending
## •
## Descending
41.0OptionalThe outcome field to filter the collection
by.
StringoutcomeField
41.0OptionalThe outcome goal to filter the collection
by. Valid values are:
ConnectSmartData
DiscoveryOutcome
GoalEnum
outcomeGoal
## •
## Maximize
## •
## Minimize
## •
## None
41.0OptionalA generated token that indicates the view
of models to be returned.
## Stringpage
41.0OptionalThe number of items to be returned in a
single page. Minimum is 1, maximum is
200, and default is 25.
IntegerpageSize
41.0OptionalThe prediction type to filter the collection
by. Valid values are:
ConnectSmartData
DiscoveryPrediction
TypeEnum
prediction
## Type
## •
## Classification
## •
MulticlassClassification
## 33
Prediction Definitions ResourceEinstein Discovery REST Resources

## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
## •
## Regression
## •
## Unknown
41.0OptionalSearch terms. Individual terms are
separated by spaces. A wildcard is
## Stringq
automatically appended to the last token
in the query string. If the user’s search
query contains quotation marks or
wildcards, those symbols are automatically
removed from the query string in the URI
along with any other special characters.
41.0OptionalThe sort order type for the collection. Valid
values are:
PredictionDefinition
CollectionSortOrder
TypeEnum
sort
## •
LastUpdate
## •
## Name
## •
OutcomeFieldLabel
## •
PredictionType
## •
SubscribedEntity
41.0OptionalFilters the collection by source type. Valid
values are:
SmartDataDiscovery
ModelSourceType
## Enum
sourceType
## •
## Discovery
## •
UserUpload
41.0OptionalFilters the collection by status. Valid values
are:
SmartDataDiscovery
StatusEnum
status
## •
## Disabled
## •
## Enabled
41.0OptionalFilters the collection by story ID (1Y3).IdstoryId
41.0OptionalFilters the collection by subscribed entity.Stringsubscribed
## Entity
Response body for GET
## Smart Data Discovery Prediction Definition Collection
## Prediction Definition Resource
Returns or deletes an Einstein Discovery prediction definition.
## 34
Prediction Definition ResourceEinstein Discovery REST Resources

Resource URL
/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>
## Formats
## JSON
## Available Version
## 41.0
HTTP Methods
## GET DELETE
Request parameters for GET and DELETE
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe ID or developer name of the prediction
definition to retrieve or delete.
## Stringprediction
DefinitionId
OrName
Response body for GET
## Smart Data Discovery Prediction Definition
## Prediction Definition Model Cards Resource
Returns a model card for an Einstein Discovery prediction definition.
Resource URL
/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/modelcards
## Formats
## JSON
## Available Version
## 51.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe ID or developer name of the prediction
definition to retrieve the model card for.
## Stringprediction
DefinitionId
OrName
Response body for GET
## Smart Data Discovery Model Card
## 35
Prediction Definition Model Cards ResourceEinstein Discovery REST Resources

## Prediction Definition Model Card Resource
Deletes a prediction definition model card.
Resource URL
/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/modelcards/<modelCardId>
## Formats
## JSON
## Available Version
## 51.0
HTTP Methods
## DELETE
Request parameters for DELETE
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe ID of the model card to delete.StringmodelCardId
41.0RequiredThe ID or developer name of the prediction
definition to delete the model card from.
## Stringprediction
DefinitionId
OrName
## Prediction Definitions Models Resource
Returns a collection of Einstein Discovery prediction definition models.
Resource URL
/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/models
## Formats
## JSON
## Available Version
## 41.0
HTTP Methods
## GET POST
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe ID or developer name of the prediction
definition to retrieve the models for.
## Stringprediction
DefinitionId
OrName
41.0OptionalFilters the collection by status. Valid values
are:
SmartDataDiscovery
StatusEnum
status
## •
## Disabled
## 36
Prediction Definition Model Card ResourceEinstein Discovery REST Resources

## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
## •
## Enabled
Response body for GET
## Smart Data Discovery Model Collection
Request parameters for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe model to create.Smart Data
## Discovery Model
## Input
model
41.0RequiredThe ID or developer name of the prediction
definition to create a model for.
## Stringprediction
DefinitionId
OrName
Response body for POST
## Smart Data Discovery Model
## Prediction Definitions Model Resource
Returns or deletes a model for an Einstein Discovery prediction definition.
Resource URL
/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/models/<modelId>
## Formats
## JSON
## Available Version
## 41.0
HTTP Methods
## GET PATCH DELETE
Request parameters for GET and DELETE
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe ID of the model to retrieve or delete.StringmodelId
41.0RequiredThe ID or developer name of the prediction
definition to retrieve or delete the model
for.
## Stringprediction
DefinitionId
OrName
## 37
Prediction Definitions Model ResourceEinstein Discovery REST Resources

Response body for GET and PATCH
## Smart Data Discovery Model
Request parameters for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe model to create.Smart Data
## Discovery Model
## Input
model
41.0RequiredThe ID of the model to retrieve or delete.StringmodelId
41.0RequiredThe ID or developer name of the prediction
definition to retrieve or delete the model
for.
## Stringprediction
DefinitionId
OrName
## Prediction Definitions Model Metrics Resource
Returns a collection of metrics for a prediction definition model.
Resource URL
/smartdatadiscovery/predictiondefinitions/<predictionDefinitionIdOrName>/models/<modelId>/metrics
## Formats
## JSON
## Available Version
## 50.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
50.0OptionalThe count of metrics to return.Intcount
41.0RequiredThe ID of the model to retrieve or delete.StringmodelId
41.0RequiredThe ID or developer name of the prediction
definition to retrieve or delete the model
for.
## Stringprediction
DefinitionId
OrName
50.0OptionalThe time span for the metrics. Valid values
are:
MetricSpanEnumspan
## •
## Day
## •
## Month
## •
SinceLastAction
## •
## Week
## 38
Prediction Definitions Model Metrics ResourceEinstein Discovery REST Resources

Response body for GET
## Smart Data Discovery Metrics Collection
## Predict Jobs Resources
Predict jobs run bulk scoring jobs for predictions. Bulk scoring jobs enable scoring predictions on multiple records at a time. For example,
after deploying an updated model, use bulk scoring to refresh all prediction scores.
Available resources:
Resource URLSupported
## HTTP
## Method
DescriptionResource
/smartdatadiscovery/predict-jobsGET POSTReturns a collection of Einstein Discovery predict
jobs and creates a predict job.
## Predict Jobs
## Resource
## /smartdatadiscovery/predict-jobs
/<predictJobId>
## GET
## PATCH
## DELETE
Returns an Einstein Discovery predict job.Predict Job
## Resource
## Predict Jobs Resource
Returns a collection of Einstein Discovery predict jobs and creates a predict job.
## Predict Job Resource
Returns an Einstein Discovery predict job.
## Predict Jobs Resource
Returns a collection of Einstein Discovery predict jobs and creates a predict job.
Resource URL
## /smartdatadiscovery/predict-jobs
## Formats
## JSON
## Available Version
## 48.0
HTTP Methods
## GET POST
Response body for GET
## Smart Data Discovery Predict Job Collection
## 39
Predict Jobs ResourcesEinstein Discovery REST Resources

Request body for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
48.0RequiredThe predict job information.SmartDataDiscovery
PredictJobInput
predictJob
Response body for POST
## Smart Data Discovery Predict Job
## Example
For use cases for running a bulk scoring job, see Manage Prediction Jobs.
## Predict Job Resource
Returns an Einstein Discovery predict job.
Resource URL
/smartdatadiscovery/predict-jobs/<predictJobId>
## Formats
## JSON
## Available Version
## 48.0
HTTP Methods
## GET PATCH DELETE
Request parameters for GET and DELETE
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
48.0RequiredThe ID of the predict job to retrieve or
delete.
StringpredictJobId
Response body for GET and PATCH
## Smart Data Discovery Predict Job
Request parameters for PATCH
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
49.0RequiredThe predict job to update.SmartDataDiscovery
PredictJobUpdate
## Input
predictJob
49.0RequiredThe ID of the predict job to update.StringpredictJobId
## 40
Predict Job ResourceEinstein Discovery REST Resources

## Predict Resource
Make an Einstein Discovery prediction.
Resource URL
## /smartdatadiscovery/predict
## Formats
## JSON
## Available Version
## 41.0
HTTP Methods
## POST
Request body for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
41.0RequiredThe discovery client.Stringdiscovery
## Client
41.0RequiredThe predict information. Valid values are:AbstractSmartData
DiscoveryPredict
## Input
predict
## •
SmartDataDiscoveryPredictInput
## •
SmartDataDiscoveryPredictRawData
## Input
## •
SmartDataDiscoveryPredictRecord
OverridesInput
## •
SmartDataDiscoveryPredictRecord
## Input
Response body for POST
## Smart Data Discovery Predict List
## Example
For use cases for requesting a prediction, see Get Predictions.
## Predict History Resource
Query the history of Einstein Discovery predictions.
Resource URL
## /smartdatadiscovery/predict-history
## Formats
## JSON
## 41
Predict ResourceEinstein Discovery REST Resources

## Available Version
## 56.0
HTTP Methods
## POST
Request body for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
56.0RequiredThe input for the predict history query.PredictHistoryInputpredict
## History
Response body for POST
## Predict History Collection
## Example
For use cases for querying prediction history, see Query Prediction History.
## Refresh Jobs Resources
Refresh jobs run refresh Einstein Discovery models.
Available resources:
Resource URLSupported
## HTTP
## Method
DescriptionResource
/smartdatadiscovery/refresh-jobsGETReturns a collection of Einstein Discovery refresh
jobs.
## Refresh Jobs
## Resource
## /smartdatadiscovery/refresh-jobs
/<refreshJobId>
GETReturns an Einstein Discovery refresh job.Refresh Job
## Resource
## /smartdatadiscovery/refresh-jobs
/<refreshJobId>/refresh-tasks
GETReturns a collection of refresh tasks for an
Einstein Discovery refresh job.
## Refresh Job
## Refresh Tasks
## Resource
## Examples
For use cases to manage refresh jobs, see Manage Model Refresh Jobs.
## Refresh Jobs Resource
Returns a collection of Einstein Discovery refresh jobs.
## Refresh Job Resource
Returns an Einstein Discovery refresh job.
## 42
Refresh Jobs ResourcesEinstein Discovery REST Resources

## Refresh Job Refresh Tasks Resource
Returns a collection of refresh tasks for an Einstein Discovery refresh job.
## Refresh Jobs Resource
Returns a collection of Einstein Discovery refresh jobs.
Resource URL
## /smartdatadiscovery/refresh-jobs
## Formats
## JSON
## Available Version
## 50.0
HTTP Methods
## GET POST
Response body for GET
## Smart Data Discovery Refresh Job Collection
## Refresh Job Resource
Returns an Einstein Discovery refresh job.
Resource URL
/smartdatadiscovery/refresh-jobs/<refreshJobId>
## Formats
## JSON
## Available Version
## 50.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
50.0RequiredThe ID of the refresh job to retrieve.StringrefreshJobId
Response body for GET
## Smart Data Discovery Refresh Job
## Refresh Job Refresh Tasks Resource
Returns a collection of refresh tasks for an Einstein Discovery refresh job.
## 43
Refresh Jobs ResourceEinstein Discovery REST Resources

Resource URL
/smartdatadiscovery/refresh-jobs/<refreshJobId>/refresh-tasks
## Formats
## JSON
## Available Version
## 50.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
50.0RequiredThe ID of the refresh job to retrieve the
refresh tasks for.
StringrefreshJobId
Response body for GET
## Smart Data Discovery Refresh Task Collection
## Stories Resources
Einstein Discovery stories are used to analyze your data. The insights from stories show you what happened in your data, why it happened,
and what could happen.
Available resources:
Resource URLSupported
## HTTP
## Method
DescriptionResource
/smartdatadiscovery/storiesGETReturns a collection of Einstein Discovery stories.Stories Resource
/smartdatadiscovery/stories/<storyId>GETReturns an Einstein Discovery story.Story Resource
/smartdatadiscovery/stories/<storyId>
## /query
POSTRuns a query on the current version of an
Einstein Discovery story.
## Story Query
## Resource
/smartdatadiscovery/stories/<storyId>
## /summary
GETReturns a summary for the current version of an
Einstein Discovery story.
## Story Summary
## Resource
/smartdatadiscovery/stories/<storyId>
## /histories
GETReturns a collection of Einstein Discovery story
history items.
## Story Histories
## Resource
/smartdatadiscovery/stories/<storyId>
/histories/<historyId>
GETReturns a specific Einstein Discovery story history
item.
## Story History
## Resource
/smartdatadiscovery/stories/<storyId>
/histories/<historyId>/query
POSTRuns a query on an Einstein Discovery story
history item.
## Story History
## Query Resource
## 44
Stories ResourcesEinstein Discovery REST Resources

Resource URLSupported
## HTTP
## Method
DescriptionResource
/smartdatadiscovery/stories/<storyId>
/histories/<historyId>/summary
GETReturns a summary for an Einstein Discovery
story history item.
## Story History
## Summary
## Resource
## Stories Resource
Returns a collection of Einstein Discovery stories.
## Story Resource
Returns an Einstein Discovery story.
## Story Query Resource
Queries the current version of an Einstein Discovery story.
## Story Summary Resource
Returns a summary for the current version of an Einstein Discovery story.
## Story Histories Resource
Returns a collection of Einstein Discovery story history items.
## Story History Resource
Returns a specific Einstein Discovery story history item.
## Story History Query Resource
Runs a query on an Einstein Discovery story history item.
## Story History Summary Resource
Returns a summary for an Einstein Discovery story history item.
## Stories Resource
Returns a collection of Einstein Discovery stories.
Resource URL
## /smartdatadiscovery/stories
## Formats
## JSON
## Available Version
## 48.0
## Available Components
## •
LWC — lightning/analyticSmartDataDiscoveryApigetStories()
HTTP Methods
## GET
## 45
Stories ResourceEinstein Discovery REST Resources

Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
48.0OptionalFilters the collection by a CRM Analytics
folder ID.
IdfolderId
48.0OptionalFilters the collection by a story input ID.IdinputId
48.0OptionalA generated token that indicates the view
of items to be returned.
## Stringpage
48.0OptionalThe number of items to be returned in a
single page. Minimum is 1, maximum is
200, and default is 25.
IntegerpageSize
48.0OptionalSearch terms. Individual terms are
separated by spaces. A wildcard is
## Stringq
automatically appended to the last token
in the query string. If the user’s search
query contains quotation marks or
wildcards, those symbols are automatically
removed from the query string in the URI
along with any other special characters.
48.0OptionalThe type of scope. Valid values are:AnalysisSetupScope
TypeEnum
scope
## •
CreatedByMe
## •
SharedWithMe
48.0OptionalThe type of the source. Valid values are:AnalysisSetup
SourceTypeEnum
sourceType
## •
AnalyticsDataset
## •
LiveDataset
## •
## Report
48.0OptionalA list of source types. Valid values are:AnalysisSetup
SourceTypeEnum[]
sourceTypes
## •
AnalyticsDataset
## •
LiveDataset
## •
## Report
Response body for GET
## Story Collection
## Story Resource
Returns an Einstein Discovery story.
## 46
Story ResourceEinstein Discovery REST Resources

Resource URL
/smartdatadiscovery/stories/<storyId>
## Formats
## JSON
## Available Version
## 48.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
48.0RequiredThe ID of the story to retrieve.IdstoryId
Response body for GET
## Story
## Story Query Resource
Queries the current version of an Einstein Discovery story.
Resource URL
/smartdatadiscovery/stories/<storyId>/query
## Formats
## JSON
## Available Version
## 52.0
HTTP Methods
## POST
Request parameters for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
52.0RequiredThe query information.StoryQueryInputqueryPayload
52.0RequiredThe ID of the story to query.StringstoryId
Response body for POST
## Story Query
## 47
Story Query ResourceEinstein Discovery REST Resources

## Story Summary Resource
Returns a summary for the current version of an Einstein Discovery story.
Resource URL
/smartdatadiscovery/stories/<storyId>/summary
## Formats
## JSON
## Available Version
## 51.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
51.0RequiredThe ID of the story to retrieve the summary
for.
StringstoryId
Response body for GET
## Story Summary Detail
## Story Histories Resource
Returns a collection of Einstein Discovery story history items.
Resource URL
/smartdatadiscovery/stories/<storyId>/histories
## Formats
## JSON
## Available Version
## 48.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
51.0RequiredThe ID of the story to retrieve the history
items for.
StringstoryId
Response body for GET
## Asset History Collection
## 48
Story Summary ResourceEinstein Discovery REST Resources

## Story History Resource
Returns a specific Einstein Discovery story history item.
Resource URL
/smartdatadiscovery/stories/<storyId>/histories/<historyId>
## Formats
## JSON
## Available Version
## 51.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
51.0RequiredThe ID of the story history to retrieve.StringhistoryId
51.0RequiredThe ID of the story to retrieve.StringstoryId
Response body for GET
## Story Version
## Story History Query Resource
Runs a query on an Einstein Discovery story history item.
Resource URL
/smartdatadiscovery/stories/<storyId>/histories/<historyId>/query
## Formats
## JSON
## Available Version
## 52.0
HTTP Methods
## POST
Request parameters for POST
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
52.0RequiredThe ID of the story history to query.StringhistoryId
52.0RequiredThe query information.StoryQueryInputqueryPayload
52.0RequiredThe ID of the story to retrieve the history
record for.
StringstoryId
## 49
Story History ResourceEinstein Discovery REST Resources

Response body for POST
## Story Query
## Story History Summary Resource
Returns a summary for an Einstein Discovery story history item.
Resource URL
/smartdatadiscovery/stories/<storyId>/histories/<historyId>/summary
## Formats
## JSON
## Available Version
## 51.0
HTTP Methods
## GET
Request parameters for GET
## Available
## Version
Required or
## Optional
DescriptionTypeParameter
## Name
51.0RequiredThe ID of the story history to retrieve the
summary for.
StringhistoryId
51.0RequiredThe ID of the story to retrieve the history
record for.
StringstoryId
Response body for GET
## Story Summary Detail
## 50
Story History Summary ResourceEinstein Discovery REST Resources

## EINSTEIN DISCOVERY REST API REQUEST BODIES
To perform a POST, PATCH, or PUT request, pass query parameters or create a request body formatted in either XML or JSON. This chapter
lists the request bodies. The query parameters are listed with each resource.
To create a JSON request body, specify the properties of the request body in JSON format.
This is an example of a Comment request body.
## {
"body": "Let'slookfor a new solution."
## }
If a request body is top-level, it has a root XML tag listed. To create an XML request body, nest the properties as XML tags inside the root
XML tag.
This is the same Einstein Discovery request body in XML format:
## <comment>
<body>Let'slookfor a new solution.</body>
## </comment>
## Abstract Classification Threshold Input
The base classification threshold input.
Abstract Smart Data Discovery AI Model Source Input
The base source input for an Einstein Discovery AI model.
## Abstract Smart Data Discovery Field Mapping Source Input
The base Einstein Discovery field mapping source input.
## Abstract Smart Data Discovery Many To One Transformation Input
The base input to identify the transformation as many to one.
## Abstract Smart Data Discovery Model Field Input
The base Einstein Discovery model field create or update.
## Abstract Smart Data Discovery Model Runtime Input
The base Einstein Discovery model runtime input.
## Abstract Smart Data Discovery One To One Transformation Input
The base input to identify the transformation as one to one.
## Abstract Smart Data Discovery Predict Input
The base predict input for Einstein Discovery.
## Abstract Smart Data Discovery Prediction Property Input
The base Einstein Discovery prediction property input.
## Abstract Smart Data Discovery Projected Predictions Interval Setting Input
The base Einstein Discovery projected predictions interval settings input.
## Abstract Smart Data Discovery Transformation Filter Input
The base Einstein Discovery transformation filter input.
## 51

## Abstract Smart Data Discovery Transformation Input
The base Einstein Discovery transformation input.
## Abstract Smart Data Discovery Transformation Override Input
The base Einstein Discovery transformation deploy override input.
## Abstract Story Data Property Input
The base Einstein Discovery story data property filter.
## Asset Reference Input
An Einstein Discovery asset reference. This wraps the BaseAssetReferenceInput
## Base Asset Reference Input
The base Einstein Discovery asset, inherited by AssetReferenceInput.
## Binary Classification Threshold Input
A binary classification threshold input.
## Predict History Input
The query input for prediction history.
## Predict History Range Input
The range for prediction history query.
Smart Data Discovery AI Model Discovery Source Input
The discovery source input for a Smart Data Discovery AI Model.
Smart Data Discovery AI Model Input
The Einstein Discovery AI model to create or update.
Smart Data Discovery AI Model Transformation Input
The input for an Einstein Discovery AI model transformation.
Smart Data Discovery AI Model User Upload Source Input
The user upload source input for a Smart Data Discovery AI Model.
## Smart Data Discovery Categorical Imputation Transformation Input
The input to identify the transformation as categorical imputation.
## Smart Data Discovery Classification Prediction Property Input
The input to identify the prediction type as Classification.
## Smart Data Discovery Cluster Input
The input for cluster definitions.
## Smart Data Discovery Complex Filter Input
The complex filter input for Einstein Discovery.
## Smart Data Discovery Custom Prescribable Field Definition Input
The input for a custom Einstein Discovery prescribable field definition to override default prescription text.
## Smart Data Discovery Customizable Field Input
Input for an Einstein Discovery customizable field.
## Smart Data Discovery Discovery Model Runtime Input
The input to identify the model runtime type as Discovery.
Smart Data Discovery Extract Day of Week Transformation Input
The input for an extract day of week transformation.
## 52
Einstein Discovery REST API Request Bodies

Smart Data Discovery Extract Month of Year Transformation Input
The input for an extract month of year transformation.
## Smart Data Discovery Field Mapping Analytics Dataset Field Input
Input for an Einstein Discovery field mapped from an analytics dataset source.
## Smart Data Discovery Field Mapping Input
An Einstein Discovery field mapping.
## Smart Data Discovery Field Mapping Salesforce Field Input
Input for an Einstein Discovery field mapped from a Salesforce field source.
## Smart Data Discovery Filter Input
The filter input for Einstein Discovery.
## Smart Data Discovery Filter Value Input
The filter value input for Einstein Discovery.
## Smart Data Discovery Free Text Clustering Transformation Input
The input for a free text clustering transformation.
## Smart Data Discovery H20 Model Runtime Input
The input to identify the model runtime type as H20.
## Smart Data Discovery Model Input
The Einstein Discovery model to create or update.
## Smart Data Discovery Model Field Date Input
The Einstein Discovery date model field create or update.
## Smart Data Discovery Model Field Numeric Input
The Einstein Discovery numeric model field create or update.
## Smart Data Discovery Model Field Text Input
The Einstein Discovery text model field create or update.
## Smart Data Discovery Multiclass Classification Prediction Property Input
The input to identify the prediction type as Multiclass Classification.
## Smart Data Discovery Narrative Filter Input
The narrative filter metadata.
## Smart Data Discovery Narrative Input
The Einstein Discovery story narrative to retrieve.
## Smart Data Discovery Narrative Insight Input
The narrative insight metadata.
## Smart Data Discovery Narrative Query Input
The query metadata for the Einstein Discovery story narrative to retrieve.
## Smart Data Discovery Numeric Range Input
A numeric range for a field.
## Smart Data Discovery Numeric Transformation Filter Input
The input for a numeric transformation filter.
## Smart Data Discovery Numerical Imputation Transformation Input
The input for a numerical imputation transformation.
## 53
Einstein Discovery REST API Request Bodies

## Smart Data Discovery Predict Extension Input
The predict record extension input for Einstein Discovery.
## Smart Data Discovery Predict Input
The predict input for Einstein Discovery.
## Smart Data Discovery Predict Nested Row List Input
The predict nested row list input for Einstein Discovery.
## Smart Data Discovery Predict Job Input
The predict job input for Einstein Discovery.
## Smart Data Discovery Predict Job Update Input
The input to update a predict job for Einstein Discovery.
## Smart Data Discovery Predict Settings Input
The predict settings input for Einstein Discovery.
## Smart Data Discovery Predict Raw Data Input
The predict raw data input for Einstein Discovery.
## Smart Data Discovery Predict Record Overrides Input
The predict record overrides input for Einstein Discovery.
## Smart Data Discovery Predict Record Input
The predict record input for Einstein Discovery.
## Smart Data Discovery Prescribable Field Input
Input for an Einstein Discovery prescribable field.
## Smart Data Discovery Projected Prediction Settings Input
The projected prediction settings input for Einstein Discovery.
Smart Data Discovery Projected Predictions Count From Date Interval Setting Input
The input for settings for an Einstein Discovery count from date based projection interval.
## Smart Data Discovery Projected Predictions Count Interval Setting Input
The input for settings for an Einstein Discovery count based projection interval.
## Smart Data Discovery Projected Predictions Date Interval Setting Input
The input for settings for an Einstein Discovery date interval.
## Smart Data Discovery Projected Predictions Historical Dataset Source Input
The input for projected predictions transformation.
## Smart Data Discovery Projected Predictions Override Input
The input for deploy time projected predictions transformation overrides.
## Smart Data Discovery Projected Predictions Transformation Input
The input for a projected predictions transformation.
## Smart Data Discovery Regression Prediction Property Input
The input to identify the prediction type as Regression.
## Smart Data Discovery Scikit Learn 102 Model Runtime Input
The input to identify the model runtime type as Scikit Learn v1.0.2.
## Smart Data Discovery Sentiment Analysis Transformation Input
The input for a sentiment analysis transformation.
## 54
Einstein Discovery REST API Request Bodies

Smart Data Discovery TensorFlow 27 Model Runtime Input
The input to identify the model runtime type as TensorFlow v2.7.0.
Smart Data Discovery TensorFlow Model Runtime Input
The input to identify the model runtime type as TensorFlow.
## Smart Data Discovery Text Transformation Filter Input
The input for a text transformation filter.
## Story Day Field Value Input
The story data day property.
Story Day of Week Field Value Input
The story data day of week property.
## Story Field Only Input
The story data field property.
## Story Month Field Value Input
The story data month property.
Story Month of Year Field Value Input
The story data month of year property.
## Story Null Field Value Input
The story data null property.
## Story Quarter Field Value Input
The story data quarter property.
Story Quarter of Year Field Value Input
The story data quarter of year property.
## Story Query Input
The input to query an Einstein Discovery story.
## Story Range Field Value Input
The story data range property.
## Story Text Field Value Input
The story data text property.
## Story Year Field Value Input
The story data year property.
## Abstract Classification Threshold Input
The base classification threshold input.
## Properties
Inherited by Binary Classification Threshold Input.
## 55
Abstract Classification Threshold InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
47.0RequiredThe classification type. Valid values are:ClassificationType
## Enum
type
## •
## Binary
Abstract Smart Data Discovery AI Model Source Input
The base source input for an Einstein Discovery AI model.
## Properties
Inherited by Smart Data Discovery AI Model Discovery Source Input and Smart Data Discovery AI Model User Upload Source Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe model source type. Valid values are:SmartDataDiscovery
ModelSourceType
## Enum
type
## •
## Discovery
## •
UserUpload
## Abstract Smart Data Discovery Field Mapping Source Input
The base Einstein Discovery field mapping source input.
## Properties
Inherited by Smart Data Discovery Field Mapping Analytics Dataset Field Input and Smart Data Discovery Field Mapping Salesforce
## Field Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe source type for the field mapping.
Valid values are:
SmartDataDiscovery
FieldMapSource
TypeEnum
type
## •
AnalyticsDatasetField
## •
SalesforceField
## Abstract Smart Data Discovery Many To One Transformation Input
The base input to identify the transformation as many to one.
## Properties
Inherits properties from AbstractSmartDataDiscoveryTransformationInput.
Inherited by  Smart Data Discovery Categorical Imputation Transformation Input.
## 56
Abstract Smart Data Discovery AI Model Source InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0OptionalThe filter applied after the transformation
is executed. Valid values are:
AbstractSmartData
## Discovery
TransformationFilter
## Input
post
## Transformation
## Filter
## •
SmartDataDiscoveryNumeric
TransformationFilterInput
## •
SmartDataDiscoveryText
TransformationFilterInput
55.0RequiredA list of field names for the data to
transform.
String[]sourceField
## Names
55.0RequiredThe field name to write the transformed
value to.
StringtargetField
## Name
## Abstract Smart Data Discovery Model Field Input
The base Einstein Discovery model field create or update.
## Properties
Inherited by Smart Data Discovery Model Field Date Input, Smart Data Discovery Model Numeric Field Input and Smart Data Discovery
## Model Field Text Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredIndicates whether the model field is
disparate impact (true) or not (false).
## Booleandisparate
## Impact
48.0RequiredThe label of the model field.Stringlabel
48.0RequiredThe name of the model field.Stringname
55.0OptionalIndicates whether the model field is
sensitive (true) or not (false).
## Booleansensitive
48.0Small, 48.0The type of the model field. Valid values
are:
SmartDataDiscovery
ModelFieldType
## Enum
type
## •
## Date
## •
## Number
## •
## Text
## Abstract Smart Data Discovery Model Runtime Input
The base Einstein Discovery model runtime input.
## 57
Abstract Smart Data Discovery Model Field InputEinstein Discovery REST API Request Bodies

## Properties
Inherited by Smart Data Discovery Discovery Model Runtime Input, Smart Data Discovery H2O Model Runtime Input, Smart Data
Discovery ScikitLearn 120 Model Runtime Input, Smart Data Discovery TensorFlow 27 Model Runtime Input, and Smart Data Discovery
TensorFlow Model Runtime Input
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe runtime type for the model. Valid
values are:
SmartDataDiscovery
ModelRuntimeType
## Enum
type
## •
## Discovery
## •
## H2O
## •
Py36Tensorflow244
(TensorFlow)
## •
Py37Scikitlearn102 (Scikit
Learn v1.0.2)
## •
Py37Tensorflow207
(TensorFlow v2.7.0)
## Abstract Smart Data Discovery One To One Transformation Input
The base input to identify the transformation as one to one.
## Properties
Inherits properties from AbstractSmartDataDiscoveryTransformationInput.
Inherited by  Smart Data Discovery Extract Day Of Week Transformation Input,  Smart Data Discovery Extract Month Of Year
Transformation Input,  Smart Data Discovery Free Text Clustering Transformation Input,  Smart Data Discovery Numerical Imputation
Transformation Input,  Smart Data Discovery Projected Predictions Transformation Input and  Smart Data Discovery Sentiment
## Analysis Transformation Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0OptionalThe filter applied after the transformation
is executed. Valid values are:
AbstractSmartData
## Discovery
TransformationFilter
## Input
post
## Transformation
## Filter
## •
SmartDataDiscoveryNumeric
TransformationFilterInput
## •
SmartDataDiscoveryText
TransformationFilterInput
55.0RequiredA list of field names for the data to
transform.
String[]sourceField
## Names
55.0RequiredThe field name to write the transformed
value to.
StringtargetField
## Name
## 58
## Abstract Smart Data Discovery One To One Transformation
## Input
Einstein Discovery REST API Request Bodies

## Abstract Smart Data Discovery Predict Input
The base predict input for Einstein Discovery.
## Properties
Inherited by SmartDataDiscoveryPredictInput, SmartDataDiscoveryPredictRawDataInput, SmartDataDiscoveryPredictRecordOverrides
Input, and SmartDataDiscoveryPredictRecordInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe model for the predictAsset Reference
## Input
model
44.0RequiredThe prediction definition ID for the predict.Stringprediction
## Definition
46.0OptionalThe settings to control the predict output.Smart Data Discover
## Predict Settings
## Input
settings
44.0RequiredThe predict type. Valid values are:SmartDataDiscovery
PredictTypeEnum
type
## •
RawData (Represent rows within a
two-dimensional array of row values)
## •
RecordOverrides (Represent
records using Salesforce record Ids.
Optionally override or append
individual records with an array of row
values)
## •
Records (Represent rows using
Salesforce record Ids associated with
the subscribedEntity of the
prediction definition)
## Abstract Smart Data Discovery Prediction Property Input
The base Einstein Discovery prediction property input.
## Properties
Inherited by Smart Data Discovery Classification Prediction Property Input, Smart Data Discovery Multiclass Classification Prediction
Property Input, and Smart Data Discovery Regression Prediction Property Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe prediction type for the model. Valid
values are:
SmartDataDiscovery
PredictionType
## Enum
type
## •
## Classification
## 59
Abstract Smart Data Discovery Predict InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
## •
MulticlassClassification
## •
## Regression
## •
## Unknown
## Abstract Smart Data Discovery Projected Predictions Interval Setting
## Input
The base Einstein Discovery projected predictions interval settings input.
## Properties
Inherited by Smart Data Discovery Projected Predictions Count From Date Interval Setting Input, Smart Data Discovery Projected
Predictions Count Interval Setting Input, and Smart Data Discovery Projected Predictions Date Interval Setting Input.
## Available
## Version
Required and
## Optional
DescriptionTypeProperty Name
55.0RequiredThe projected predictions interval setting
type. Valid values are:
SmartDataDiscovery
ProjectedPredictions
IntervalSettingType
## Enum
type
## •
## Count
## •
CountFromDate
## •
## Date
## Abstract Smart Data Discovery Transformation Filter Input
The base Einstein Discovery transformation filter input.
## Properties
Inherited by Smart Data Discovery Discovery Numeric Transformation Filter Input and Smart Data Discovery Discovery Text
## Transformation Filter Input
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe transformation filter type for the
model. Valid values are:
SmartDataDiscovery
TransformationFilter
TypeEnum
type
## •
## Number
## •
## Text
## 60
## Abstract Smart Data Discovery Projected Predictions Interval
## Setting Input
Einstein Discovery REST API Request Bodies

## Abstract Smart Data Discovery Transformation Input
The base Einstein Discovery transformation input.
## Properties
Inherited by Abstract Smart Data Discovery Discovery Many To One Transformation Input and Abstract Smart Data Discovery Discovery
## One To One Transformation Input
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe runtime type for the model. Valid
values are:
SmartDataDiscovery
AIModel
TransformationType
## Enum
type
## •
CategoricalImputation
(Replace categorical missing values)
## •
ExtractDayOfWeek (Extract day
of week)
## •
ExtractMonthOfYear (Extract
month of year)
## •
FreeTextClustering (Free text
clustering)
## •
NumericalImputation
(Replace numerical missing values)
## •
SentimentAnalysis (Detecting
sentiment)
## •
TimeSeriesForecast
(Projected predictions)
## •
TypographicClustering
(Fuzzy matching)
## Abstract Smart Data Discovery Transformation Override Input
The base Einstein Discovery transformation deploy override input.
## Properties
Inherited by Smart Data Discovery Projected Predictions Override Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredA transformation asset associated with the
override settings.
AssetReference
## Input
input
55.0RequiredThe transformation type. Valid values are:SmartDataDiscovery
AIModel
type
## •
CategoricalImputation
(Replace categorical missing values)
## 61
Abstract Smart Data Discovery Transformation InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
TransformationType
## Enum
## •
ExtractDayOfWeek (Extract day
of week)
## •
ExtractMonthOfYear (Extract
month of year)
## •
FreeTextClustering (Free text
clustering)
## •
NumericalImputation
(Replace numerical missing values)
## •
SentimentAnalysis (Detecting
sentiment)
## •
TimeSeriesForecast
(Projected predictions)
## •
TypographicClustering
(Fuzzy matching)
## Abstract Story Data Property Input
The base Einstein Discovery story data property filter.
## Properties
Inherited by Story Day Field Value Input, Story Day Of Week Field Value Input, Story Field Only Input, Story Month Field Value Input,
Story Month Of Year Field Value Input, Story Null Field Value Input, Story Quarter Field Value Input, Story Quarter Of Year Field Value
Input, Story Range Field Value Input, Story Text Field Value Input, and Story Year Field Value Input.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe filter field developer name.Stringfield
52.0RequiredThe filter field type.Stringtype
## Asset Reference Input
An Einstein Discovery asset reference. This wraps the BaseAssetReferenceInput
## Properties
## Base Asset Reference Input
## Base Asset Reference Input
The base Einstein Discovery asset, inherited by AssetReferenceInput.
## 62
Abstract Story Data Property InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
42.0RequiredThe ID of the asset.Stringid
42.0RequiredThe developer name of the asset.Stringname
42.0OptionalThe namespace that qualifies the asset
name.
## Stringnamespace
## Binary Classification Threshold Input
A binary classification threshold input.
## Properties
Inherits properties from AbstractClassificationThresholdInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
47.0RequiredThe data for a source analysis.Doublevalue
## Predict History Input
The query input for prediction history.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe ID of the goal.IDgoalId
56.0RequiredThe range for the prediction history query.PredictHistoryRange
## Input
range
56.0OptionalThe list of targets to query.String[]targets
## Predict History Range Input
The range for prediction history query.
## 63
Binary Classification Threshold InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
56.0OptionalThe interval for look back. Valid values are:PredictHistory
IntervalEnum
interval
## •
## None
## •
## Weekly
56.0OptionalThe maximum look back period.IntegermaxLookBack
Smart Data Discovery AI Model Discovery Source Input
The discovery source input for a Smart Data Discovery AI Model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelDiscoverySourceInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe run ID that created this AI model.Asset Reference
## Input
runId
Smart Data Discovery AI Model Input
The Einstein Discovery AI model to create or update.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0OptionalThe description for the AI model.Stringdescription
48.0RequiredThe input source for the AI model. Valid
data properties are:
AbstractSmartData
DiscoveryAIModel
SourceInput
input
## •
Smart Data Discovery AI Model
## Discovery Source Input
## •
Smart Data Discovery AI Model User
## Upload Source Input
48.0OptionalThe label for the AI model.Stringlabel
## 64
Smart Data Discovery AI Model Discovery Source InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe list of model fields for the AI model.
Valid values are:
AbstractSmartData
DiscoveryModel
FieldInput[]
modelFields
## •
SmartDataDiscoveryModelFieldDate
## Input
## •
SmartDataDiscoveryModelField
NumericInput
## •
SmartDataDiscoveryModelFieldText
## Input
48.0RequiredThe runtime for the AI model. Valid
runtimes are:
AbstractSmartData
DiscoveryModel
RuntimeInput
input
## •
## Smart Data Discovery Discovery Model
## Runtime Input
## •
Smart Data Discovery H2O Model
## Runtime Input
## •
Smart Data Discovery ScikitLearn 120
## Model Runtime Input
## •
Smart Data Discovery TensorFlow 27
## Model Runtime Input
## •
Smart Data Discovery TensorFlow
## Model Runtime Input
48.0RequiredThe developer name for the AI model.Stringname
48.0OptionalThe field name that the AI model is trying
to predict.
## Stringpredicted
## Field
48.0OptionalThe prediction property of the AI model.
Valid prediction properties are:
AbstractSmartData
DiscoveryPrediction
PropertyInput
prediction
## Property
## •
## Smart Data Discovery Classification
## Prediction Property Input
## •
## Smart Data Discovery Multiclass
## Classification Prediction Property Input
## •
## Smart Data Discovery Regression
## Prediction Property Input
49.0OptionalThe status of the AI model. Valid values are:ConnectEDInsight
TypeEnum
status
## •
## Disabled
## •
## Enabled
## •
UploadCompleted
## •
UploadFailed
## •
## Uploading
## •
## Validating
## 65
Smart Data Discovery AI Model InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
## •
ValidationCompleted
## •
ValidationFailed
48.0Small, 48.0A list of transformations associated with
this AI model.
## Smart Data
Discovery AI Model
## Transformation
## Input[]
transformations
50.0OptionalThe validation result of the AI model.Objectvalidation
## Result
Smart Data Discovery AI Model Transformation Input
The input for an Einstein Discovery AI model transformation.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
54.0RequiredA list of the model field names to use as
input parameters by the transformation.
String[]sourceFields
## Names
51.0RequiredThe model transformation state.Objectstate
54.0RequiredA list of the model field names to modify
with the transformation.
String[]targetFields
## Names
51.0RequiredThe model transformation type. Valid
values are:
SmartDataDiscovery
AIModel
TransformationType
## Enum
type
## •
CategoricalImputation
(Replace categorical missing values)
## •
ExtractDayOfWeek (Extract day
of week)
## •
ExtractMonthOfYear (Extract
month of year)
## •
FreeTextClustering (Free text
clustering)
## •
NumericalImputation
(Replace numerical missing values)
## •
SentimentAnalysis (Detecting
sentiment)
## •
TimeSeriesForecast
(Projected predictions)
## 66
Smart Data Discovery AI Model Transformation InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
## •
TypographicClustering
(Fuzzy matching)
Smart Data Discovery AI Model User Upload Source Input
The user upload source input for a Smart Data Discovery AI Model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelDiscoverySourceInput.
## Smart Data Discovery Categorical Imputation Transformation Input
The input to identify the transformation as categorical imputation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryManyToOneTransformationInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe algorithm type for the classification.
Valid values are:
SmartDataDiscovery
## Categorical
ImputationMethod
## Enum
imputeMethod
## •
## Auto
## Smart Data Discovery Classification Prediction Property Input
The input to identify the prediction type as Classification.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictionPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe algorithm type for the classification.
Valid values are:
SmartDataDiscovery
## Classification
AlgorithmType
## Enum
algorithmType
## •
Best (Model tournament)
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
## 67
Smart Data Discovery AI Model User Upload Source InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe classification threshold for the model.
Valid values are:
## Abstract
## Classification
ThresholdInput
classification
## Threshold
## •
BinaryClassificationThresholdInput
## Smart Data Discovery Cluster Input
The input for cluster definitions.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredIndicates whether the cluster is ignored
(true) or not (false).
## Booleanignored
55.0OptionalThe label for the cluster.Stringlabel
55.0RequiredThe name for the cluster.Stringname
55.0RequiredA list of values in the cluster.String[]values
## Smart Data Discovery Complex Filter Input
The complex filter input for Einstein Discovery.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
46.0RequiredThe list of filters that make up the complex
filter.
SmartDataDiscovery
FilterInput[]
filters
## Smart Data Discovery Custom Prescribable Field Definition Input
The input for a custom Einstein Discovery prescribable field definition to override default prescription text.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
50.0RequiredA list of filter rules for enabling custom text.SmartDataDiscovery
FilterInput[]
filters
## 68
Smart Data Discovery Cluster InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
50.0RequiredThe template text to use in replacements.StringtemplateText
## Smart Data Discovery Customizable Field Input
Input for an Einstein Discovery customizable field.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
57.0RequiredA list of custom field definitions.SmartDataDiscovery
CustomPrescribable
custom
## Definitions
FieldDefinition
## Input[]
57.0RequiredThe name of the customizable field.StringfieldName
## Smart Data Discovery Discovery Model Runtime Input
The input to identify the model runtime type as Discovery.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelRuntimeInput.
Smart Data Discovery Extract Day of Week Transformation Input
The input for an extract day of week transformation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryOneToOneTransformationInput.
Smart Data Discovery Extract Month of Year Transformation Input
The input for an extract month of year transformation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryOneToOneTransformationInput.
## Smart Data Discovery Field Mapping Analytics Dataset Field Input
Input for an Einstein Discovery field mapped from an analytics dataset source.
## 69
Smart Data Discovery Customizable Field InputEinstein Discovery REST API Request Bodies

## Properties
Inherits properties from AbstractSmartDataDiscoveryFieldMappingSourceInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe sObject field name used as the join
key.
StringsobjectField
JoinKey
48.0RequiredA source ID of the analytics dataset asset.AssetReference
## Input
source
48.0RequiredThe source dataset field name used as the
join key.
StringsourceField
JoinKey
## Smart Data Discovery Field Mapping Input
An Einstein Discovery field mapping.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredThe field mapping source. Valid values are:AbstractSmartData
DiscoveryField
input
## •
## Smart Data Discovery Field Mapping
## Analytics Dataset Field Input
MappingSource
## Input
## •
## Smart Data Discovery Field Mapping
## Salesforce Field Input
48.0RequiredThe mapped field name.StringmappedField
## Name
48.0RequiredThe model field.StringmodelField
## Name
## Smart Data Discovery Field Mapping Salesforce Field Input
Input for an Einstein Discovery field mapped from a Salesforce field source.
## Properties
Inherits properties from AbstractSmartDataDiscoveryFieldMappingSourceInput.
## Smart Data Discovery Filter Input
The filter input for Einstein Discovery.
## 70
Smart Data Discovery Field Mapping InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
41.0RequiredThe developer name of the field the filter
applies to.
StringfieldName
50.0RequiredAn ordered list of the values to compare
with.
SmartDataDiscovery
FilterValueInput[]
filterValues
41.0RequiredThe operator to use in the filter. Valid
values are:
ConnectSmartData
DiscoveryFilter
OperatorEnum
operator
## •
## Between
## •
## Contains
## •
EndsWith
## •
## Equal
## •
GreaterThan
## •
GreaterThanOrEqual
## •
InSet
## •
LessThan
## •
LessThanOrEqual
## •
NotBetween
## •
NotEqual
## •
NotIn
## •
StartsWith
48.0RequiredThe field type for the filter. Valid values are:SmartDataDiscovery
FilterFieldTypeEnum
type
## •
## Boolean
## •
## Date
## •
DateTime
## •
## Number
## •
## Text
## Smart Data Discovery Filter Value Input
The filter value input for Einstein Discovery.
## 71
Smart Data Discovery Filter Value InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
50.0RequiredThe type of the filter value. Valid values are:SmartDataDiscovery
FilterValueType
## Enum
type
## •
## Constant
## •
## Placeholder
50.0RequiredThe value for the filter. The value is a
constant or a placeholder
## Stringvalue
## Smart Data Discovery Free Text Clustering Transformation Input
The input for a free text clustering transformation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryOneToOneTransformationInput.
## Smart Data Discovery H20 Model Runtime Input
The input to identify the model runtime type as H20.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelRuntimeInput.
## Smart Data Discovery Model Input
The Einstein Discovery model to create or update.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
46.0OptionalThe analysis connected with the given
model.
AssetReference
## Input
analysis
48.0RequiredThe classification threshold for the model.
Valid values are:
## Abstract
## Classification
ThresholdInput
classification
## Threshold
## •
BinaryClassificationThresholdInput
57.0OptionalA list of customizable top factors for the
model.
SmartDataDiscovery
CustomizableField
## Input[]
customizable
## Factors
## 72
## Smart Data Discovery Free Text Clustering Transformation
## Input
Einstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0RequiredA list mapping the model fields to
Salesforce fields.
SmartDataDiscovery
FieldMapping
## Input[]
fieldMapping
41.0RequiredA list of filters used to determine whether
a row can be evaluated by this model.
SmartDataDiscovery
ComplexFilter
## Input[]
filterList
50.0OptionalIndicates whether this model is included
in the refresh schedule (true) or not
## (false).
BooleanisRefresh
## Enabled
41.0RequiredThe label of the model.Stringlabel
48.0RequiredA ID for the associated AI model.AssetReference
## Input
model
41.0Small, 41.0The developer name of the model.Stringname
48.0RequiredA list of the prescribable fields for the
model.
SmartDataDiscovery
PrescribableField
## Input[]
prescribable
## Fields
41.0RequiredA unique number indicating the order in
which this model's filters are evaluated
IntegersortOrder
compared to all other models in the parent
prediction definition.
46.0RequiredThe status of the model. Valid values are:SmartDataDiscovery
StatusEnum
status
## •
## Disabled
## •
## Enabled
48.0RequiredA list of the transformation overrides for
the model. Valid values are:
AbstractSmartData
## Discovery
PrescribableField[]
transformation
## Overrides
## •
## Smart Data Discovery Projected
## Predictions Override Input
## Smart Data Discovery Model Field Date Input
The Einstein Discovery date model field create or update.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelFieldInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
56.0RequiredA list of model field unique values.String[]values
## 73
Smart Data Discovery Model Field Date InputEinstein Discovery REST API Request Bodies

## Smart Data Discovery Model Field Numeric Input
The Einstein Discovery numeric model field create or update.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelFieldInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
56.0RequiredA list of model field unique values.SmartDataDiscovery
NumericRange
## Input[]
values
## Smart Data Discovery Model Field Text Input
The Einstein Discovery text model field create or update.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelFieldInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
56.0RequiredA list of model field unique values.String[]values
## Smart Data Discovery Multiclass Classification Prediction Property Input
The input to identify the prediction type as Multiclass Classification.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictionPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe algorithm type for the classification.
Valid values are:
SmartDataDiscovery
## Classification
AlgorithmType
## Enum
algorithmType
## •
Best (Model tournament)
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
## 74
Smart Data Discovery Model Field Numeric InputEinstein Discovery REST API Request Bodies

## Smart Data Discovery Narrative Filter Input
The narrative filter metadata.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe columns to use in the filter.Stringcolumns
51.0RequiredThe filter for the query service to use. Valid
data properties are:
AbstractStoryData
PropertyInput
property
## •
## Story Day Field Value Input
## •
## Story Day Field Value Input
## •
## Story Field Only Value Input
## •
## Story Month Field Value Input
## •
## Story Month Of Year Field Value Input
## •
## Story Null Field Value Input
## •
## Story Quarter Field Value Input
## •
## Story Quarter Of Year Field Value Input
## •
## Story Range Field Value Input
## •
## Story Text Field Value Input
## •
## Story Year Field Value Input
51.0RequiredThe list of values to use with the fields in
the filter.
## String[]values
## Smart Data Discovery Narrative Input
The Einstein Discovery story narrative to retrieve.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0OptionalIndicates whether the warning data should
be included (true) or not (false).
## Booleaninclude
## Warnings
51.0RequiredThe query body containing the information
for generating the narrative.
SmartDataDiscovery
NarrativeQueryInput
query
51.0RequiredThe story to use for generating the
narrative.
AssetReference
## Input
story
51.0RequiredThe ID of the story to use for generating
the narrative.
StringstoryId
## 75
Smart Data Discovery Narrative Filter InputEinstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe type of the narrative source.Stringtype
## Smart Data Discovery Narrative Insight Input
The narrative insight metadata.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe insight type to return. Valid values are:ConnectEDInsight
TypeEnum
insightType
## •
## Descriptive
## •
## Summary
51.0RequiredThe narrative type to return. Valid values
are:
ConnectEDNarrative
TypeEnum
narrativeType
## •
## Positive
## •
## Negative
51.0RequiredThe number of insights to return.IntegernumInsights
## Smart Data Discovery Narrative Query Input
The query metadata for the Einstein Discovery story narrative to retrieve.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of filters for the query.SmartDataDiscovery
NarrativeFilter
## Input[]
filters
51.0RequiredThe insights for the query.SmartDataDiscovery
NarrativeQueryInput
insight
## Smart Data Discovery Numeric Range Input
A numeric range for a field.
## 76
Smart Data Discovery Narrative Insight InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
57.0RequiredThe maximum value for the range.Doublemax
57.0RequiredThe minimum value for the range.Doublemin
## Smart Data Discovery Numeric Transformation Filter Input
The input for a numeric transformation filter.
## Properties
Inherits properties from AbstractSmartDataDiscoveryTransformationFilterInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe upper bound to be included.Doublemax
55.0RequiredThe lower bound to be included.Doublemin
## Smart Data Discovery Numerical Imputation Transformation Input
The input for a numerical imputation transformation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryOneToOneTransformationInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe numerical imputation method. Valid
values are:
SmartDataDiscovery
## Numerical
ImputationMethod
## Enum
imputeMethod
## •
## Mean
## •
## Median
## •
## Mode
## Smart Data Discovery Predict Extension Input
The predict record extension input for Einstein Discovery.
## 77
Smart Data Discovery Numeric Transformation Filter InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
44.0RequiredThe ID of the record.IDrecord
44.0RequiredA list of the rows for the extension.String[]row
## Smart Data Discovery Predict Input
The predict input for Einstein Discovery.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
43.0RequiredThe entity ID to run a prediction on.StringentityId
43.0RequiredA map of data values.Map<String,
## String>
exploratory
## Values
43.0RequiredThe model ID to use for the prediction.Stringprediction
DefinitionId
## Smart Data Discovery Predict Nested Row List Input
The predict nested row list input for Einstein Discovery.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
44.0RequiredA list of the rows.String[]row
## Smart Data Discovery Predict Job Input
The predict job input for Einstein Discovery.
## 78
Smart Data Discovery Predict InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
48.0OptionalThe filters to score a portion of the records.
If no filters are specified, then all records
SmartDataDiscovery
ComplexFilterInput
filter
are scored. If specified, use one type of
filter, either
useTerminalStateFilter or
filters, but not both.
48.0RequiredThe label for the scoring job.Stringlabel
48.0RequiredThe ID of the prediction definition for the
scoring job.
AssetReference
## Input
prediction
## Definition
49.0OptionalIndicates whether the job should score any
record NOT matching the terminal state
filter on the goal (true) or not (false).
BooleanuseTerminal
StateFilter
## Smart Data Discovery Predict Job Update Input
The input to update a predict job for Einstein Discovery.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
46.0RequiredThe status of the predict job. Valid values
are:
SmartDataDiscovery
PredictJobStatus
## Enum
status
## •
## Cancelled
## •
## Completed
## •
## Failed
## •
InProgress
## •
NotStarted
## •
## Paused
## Smart Data Discovery Predict Settings Input
The predict settings input for Einstein Discovery.
## 79
Smart Data Discovery Predict Job Update InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0OptionalA list of the aggregate functions to use.String[]aggregate
## Functions
50.0OptionalThe maximum middle value count. The
default value is 0 and the allowed range is
## [0, 3].
IntegermaxMiddle
## Values
46.0OptionalThe maximum prescription count. The
default value is -1 (unlimited) and the
allowed range is [-1, 200].
## Integermax
## Prescriptions
47.0OptionalThe impact percentage of the
prescriptions. The default value is 0.
## Integerprescription
## Impact
## Percentage
54.0OptionalThe setting overrides for projected
predictions.
SmartDataDiscovery
ProjectedPrediction
SettingsInput
projected
## Predictions
## Smart Data Discovery Predict Raw Data Input
The predict raw data input for Einstein Discovery.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
44.0RequiredA comma-separated list of column names
representing the columns that the model
analyzes.
String[]columnNames
44.0RequiredA list of row names and values.SmartDataDiscovery
PredictNestedRow
ListInput[]
rows
## Smart Data Discovery Predict Record Overrides Input
The predict record overrides input for Einstein Discovery.
## 80
Smart Data Discovery Predict Raw Data InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
44.0RequiredA comma-separated list of column names
representing the columns that the model
analyzes.
String[]columnNames
44.0RequiredA list of containing the Salesforce record
IDs.
SmartDataDiscovery
PredictExtension
## Input[]
rows
## Smart Data Discovery Predict Record Input
The predict record input for Einstein Discovery.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
44.0RequiredA list of comma-separated Salesforce
record IDs associated with the
## String[]records
subscribedEntity of the prediction
definition. Maximum of 200 records
allowed.
## Smart Data Discovery Prescribable Field Input
Input for an Einstein Discovery prescribable field.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
50.0RequiredA list of custom prescribable field
definitions to override default prescription
text.
SmartDataDiscovery
CustomPrescribable
FieldDefinition
## Input[]
custom
## Definitions
50.0RequiredThe name of the prescribable field.StringfieldName
## Smart Data Discovery Projected Prediction Settings Input
The projected prediction settings input for Einstein Discovery.
## 81
Smart Data Discovery Predict Record InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0OptionalThe confidence interval to display at each
point. Allowed values are 80 and 95.
## Integerconfidence
## Interval
54.0OptionalOverride the number of intervals to project
ahead. The allowed range is [1, 12].
IntegernumberOf
IntervalsTo
ProjectAhead
54.0OptionalIndicates whether the projected prediction
calculation is enabled for every interval
into the future (true) or not (false).
BooleanshowProjected
PredictionBy
## Interval
## Smart Data Discovery Projected Predictions Count From Date Interval
## Setting Input
The input for settings for an Einstein Discovery count from date based projection interval.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPredictionsIntervalSettingInput.
## Available
## Version
Required and
## Optional
DescriptionTypeProperty Name
55.0RequiredThe date field to use for calculating
projection intervals.
StringdateField
55.0RequiredThe number of intervals to project ahead.IntegernumIntervals
## Smart Data Discovery Projected Predictions Count Interval Setting Input
The input for settings for an Einstein Discovery count based projection interval.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPredictionsIntervalSettingInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe number of intervals to project ahead.IntegernumIntervals
## 82
## Smart Data Discovery Projected Predictions Count From Date
## Interval Setting Input
Einstein Discovery REST API Request Bodies

## Smart Data Discovery Projected Predictions Date Interval Setting Input
The input for settings for an Einstein Discovery date interval.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPredictionsIntervalSettingInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe date field to use for calculating
projection intervals.
StringdateField
## Smart Data Discovery Projected Predictions Historical Dataset Source
## Input
The input for projected predictions transformation.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe ID of the historical dataset used to
extract and build time series for each asset
## ID.
IDdatasetId
55.0RequiredThe ID of the specific dataset version used
for extraction.
IDdataset
VersionId
## Smart Data Discovery Projected Predictions Override Input
The input for deploy time projected predictions transformation overrides.
## Properties
Inherits properties from AbstractSmartDataDiscoveryTransformationOverrideInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe Salesforce object field name to use as
a look-up for a record ID in a historical
dataset.
StringassetIdField
## 83
## Smart Data Discovery Projected Predictions Date Interval
## Setting Input
Einstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe projected predictions interval settings.
Valid values are:
AbstractSmartData
DiscoveryProjected
PredictionsInterval
SettingInput
interval
## Override
## •
## Smart Data Discovery Projected
## Predictions Count From Date Interval
## Setting Input
## •
## Smart Data Discovery Projected
## Predictions Count Interval Setting
## Input
## •
## Smart Data Discovery Projected
## Predictions Date Interval Setting Input
## Smart Data Discovery Projected Predictions Transformation Input
The input for a projected predictions transformation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryOneToOneTransformationInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe group by column, used for building
time series for each asset ID.
StringassetIdField
## Name
55.0RequiredThe field used for the time series time axis.StringdateFieldName
55.0RequiredThe historical dataset input.SmartDataDiscovery
ProjectedPredictions
input
HistoricalDataset
SourceInput
55.0RequiredThe default number of intervals to project
forward.
IntegernumIntervals
55.0RequiredThe interval type for forward projections.
Valid values are:
SmartDataDiscovery
ProjectedPredictions
IntervalTypeEnum
projected
## Predictions
IntervalType
## •
## Day
## •
## Month
## •
## Quarter
## •
## Week
55.0RequiredThe time series y axis. This is the value
column projected for each asset ID.
## Stringprojection
FieldName
## 84
## Smart Data Discovery Projected Predictions Transformation
## Input
Einstein Discovery REST API Request Bodies

## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe seasonality period. Use 0 for no
seasonality, or [2-24].
## Integerseasonality
## Period
## Smart Data Discovery Regression Prediction Property Input
The input to identify the prediction type as Regression.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictionPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe algorithm type for the classification.
Valid values are:
SmartDataDiscovery
## Regression
AlgorithmType
## Enum
algorithmType
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
## Smart Data Discovery Scikit Learn 102 Model Runtime Input
The input to identify the model runtime type as Scikit Learn v1.0.2.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelRuntimeInput.
## Smart Data Discovery Sentiment Analysis Transformation Input
The input for a sentiment analysis transformation.
## Properties
Inherits properties from AbstractSmartDataDiscoveryOneToOneTransformationInput.
Smart Data Discovery TensorFlow 27 Model Runtime Input
The input to identify the model runtime type as TensorFlow v2.7.0.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelRuntimeInput.
## 85
Smart Data Discovery Regression Prediction Property InputEinstein Discovery REST API Request Bodies

Smart Data Discovery TensorFlow Model Runtime Input
The input to identify the model runtime type as TensorFlow.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelRuntimeInput.
## Smart Data Discovery Text Transformation Filter Input
The input for a text transformation filter.
## Properties
Inherits properties from AbstractSmartDataDiscoveryTransformationFilterInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
55.0RequiredA list of clusters to filter the value with.SmartDataDiscovery
ClusterInput[]
clusters
55.0RequiredIndicates weher to include values that
aren't defined in clusters (true) or not
## (false).
BooleanincludeOthers
## Story Day Field Value Input
The story data day property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe day in numeric value.Integerday
52.0RequiredIndicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0RequiredThe month in numeric value.Integermonth
52.0RequiredThe raw value of the field.StringrawValue
52.0RequiredThe year in numeric value.Integeryear
Story Day of Week Field Value Input
The story data day of week property.
## 86
Smart Data Discovery TensorFlow Model Runtime InputEinstein Discovery REST API Request Bodies

## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe day of week in numeric value.IntegerdayOfWeek
52.0RequiredThe raw value of the field.StringrawValue
## Story Field Only Input
The story data field property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Story Month Field Value Input
The story data month property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredIndicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0RequiredThe month in numeric value.Integermonth
52.0RequiredThe raw value of the field.StringrawValue
52.0RequiredThe year in numeric value.Integeryear
Story Month of Year Field Value Input
The story data month of year property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe month of year in numeric value.Integermonth
52.0RequiredThe raw value of the field.StringrawValue
## 87
Story Field Only InputEinstein Discovery REST API Request Bodies

## Story Null Field Value Input
The story data null property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Story Quarter Field Value Input
The story data quarter property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredIndicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0RequiredThe quarter in numeric value.Integerquarter
52.0RequiredThe raw value of the field.StringrawValue
52.0RequiredThe year in numeric value.Integeryear
Story Quarter of Year Field Value Input
The story data quarter of year property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredIndicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0RequiredThe quarter in numeric value.Integerquarter
52.0RequiredThe raw value of the field.StringrawValue
## Story Query Input
The input to query an Einstein Discovery story.
## 88
Story Null Field Value InputEinstein Discovery REST API Request Bodies

## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
54.0RequiredA list of filters to use in the query. Valid
values are:
AbstractStoryData
PropertyInput[]
filters
## •
## Story Day Field Value Input
## •
## Story Day Of Week Field Value Input
## •
## Story Field Only Input
## •
## Story Month Field Value Input
## •
## Story Month Of Year Field Value Input
## •
## Story Null Field Value Input
## •
## Story Quarter Field Value Input
## •
## Story Quarter Of Year Field Value Input
## •
## Story Range Field Value Input
## •
## Story Text Field Value Input
## •
## Story Year Field Value Input
54.0OptionalIndicates whether to include the story
chart in the query response (true) or not
## (false).
BooleanincludeChart
54.0OptionalIndicates whether to include the story
narrative in the query response (true) or
not (false).
## Booleaninclude
## Narrative
54.0OptionalIndicates whether to include regular fields
in the query response (true) or not
## (false).
## Booleaninclude
RegularFields
54.0OptionalIndicates whether to include sensitive
fields in the query response (true) or not
## (false).
## Booleaninclude
## Sensitive
## Fields
52.0RequiredThe analysis type for the query insights.
Valid values are:
InsightsTypeEnuminsightsType
## •
## Descriptive
## •
## Diagnostic
54.0OptionalThe total number of insight cards in the
query response.
## Integerlimit
54.0OptionalThe insight card offset value.Integeroffset
## 89
Story Query InputEinstein Discovery REST API Request Bodies

## Story Range Field Value Input
The story data range property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe end value of the range.StringendValue
52.0RequiredThe start value of the range.StringstartValue
## Story Text Field Value Input
The story data text property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe text value of the field.Stringvalue
## Story Year Field Value Input
The story data year property.
## Properties
Inherits properties from AbstractStoryDataPropertyInput.
## Available
## Version
Required or
## Optional
DescriptionTypeProperty Name
52.0RequiredIndicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0RequiredThe raw value of the field.StringrawValue
52.0RequiredThe year in numeric value.Integeryear
## 90
Story Range Field Value InputEinstein Discovery REST API Request Bodies

## EINSTEIN DISCOVERY REST API RESPONSE BODIES
The successful execution of a request to an Einstein Discovery REST API resource can return a response body in either JSON or XML
format.
A request to an Einstein Discovery REST API resource always returns an HTTP response code, whether the request was successful or not.
## Abstract Bucketing Strategy
The base bucketing strategy.
## Abstract Classification Threshold
The base classification threshold.
## Abstract Date Field Configuration
The base Einstein Discovery date field configuration.
## Abstract Field Configuration
The base Einstein Discovery field configuration.
## Abstract Numeric Field Configuration
The base Einstein Discovery numeric field configuration.
## Abstract Smart Data Discovery Aggregate Prediction
The base Einstein Discovery aggregate prediction result.
Abstract Smart Data Discovery AI Model Metrics
The base Einstein Discovery AI model metric.
Abstract Smart Data Discovery AI Model Source
The base Einstein Discovery AI model prediction property.
## Abstract Smart Data Discovery Field Mapping Source
The base Einstein Discovery field mapping source.
## Abstract Smart Data Discovery Model Field
The base Einstein Discovery model field.
## Abstract Smart Data Discovery Model Runtime
The base Einstein Discovery model run time.
## Abstract Smart Data Discovery Prediction Property
The base Einstein Discovery AI model prediction property.
## Abstract Smart Data Discovery Prediction
The base Einstein Discovery prediction result.
## Abstract Smart Data Discovery Predict
The base Einstein Discovery predict result.
## Abstract Smart Data Discovery Projected Prediction
The base Einstein Discovery projected prediction result.
## Abstract Smart Data Discovery Projected Predictions Interval Setting
The base Einstein Discovery projected predictions interval settings.
## 91

## Abstract Smart Data Discovery Transformation Override
The base Einstein Discovery transformation deploy overrides.
## Abstract Smart Data Discovery Validation Configuration
The base validation configuration output.
## Abstract Story Data Property
The base Einstein Discovery story data property filter.
## Abstract Story Insights Case
The base story insights case.
## Abstract Story Insights
The base story insights.
## Abstract Story Narrative Element
The base story narrative element.
## Abstract Story Source
The base Einstein Discovery analysis source.
## Abstract Text Field Configuration
The base Einstein Discovery text field configuration.
## Analytics Dataset Source
An analytics dataset as the analysis source.
## Asset History Collection
A collection of asset history items.
## Asset History
The asset history record.
## Asset Reference
An Einstein Discovery asset reference. This wraps the BaseAssetReference
## Autopilot
The setup for autopilot.
## Base Asset Reference
The base Einstein Discovery asset, inherited by AssetReference.
## Binary Classification Threshold
A binary classification threshold.
## Date Field Configuration
The date field configuration.
## Diagnostic Insights Case
A story query diagnostic insights.
## Directory Item Collection
A collection of directory items.
## Even Width Bucketing Strategy
The even-width bucketing strategy.
## Manual Bucketing Strategy
The manual bucketing strategy.
## 92
Einstein Discovery REST API Response Bodies

## Model Field Label Metrics
Model field information that includes label, value and metrics data.
## Numeric Field Configuration
The numeric field configuration.
## Percentile Bucketing Strategy
The percentile bucketing strategy.
## Predict History Collection
A collection of historical predictions for a goal.
## Predict History
The historical predictions for a target.
## Predict History Range
A range used for the historical prediction query.
## Predict History Value
A historical prediction value at a specific point in time.
## Report Source
An analytics report as the analysis source.
## Smart Data Discovery Aggregate Predict Condition
The aggregate predict condition for a collection of Einstein Discover predictions.
## Smart Data Discovery Aggregate Prediction Error
An Einstein Discovery aggregate prediction error.
## Smart Data Discovery Aggregate Prediction
An Einstein Discovery aggregate prediction result.
Smart Data Discovery AI Model Classification Metrics
The binomial classification metrics for an Einstein Discovery AI model.
Smart Data Discovery AI Model Coefficient Collection
A collection of Einstein Discovery AI model coefficients.
Smart Data Discovery AI Model Collection
A collection of Einstein Discovery AI models.
Smart Data Discovery AI Model Discovery Source
The discovery source for an AI model.
Smart Data Discovery AI Model Multiclass Metrics
The multiclass metrics for an Einstein Discovery AI model.
Smart Data Discovery AI Model Regression Metrics
The regression metrics for an Einstein Discovery AI model.
Smart Data Discovery AI Model Residual Collection
A collection of Einstein Discovery AI model residuals.
Smart Data Discovery AI Model Residual
AnEinstein Discovery AI model residual.
Smart Data Discovery AI Model Transformation
An Einstein Discovery AI model transformation.
## 93
Einstein Discovery REST API Response Bodies

Smart Data Discovery AI Model User Upload Source
The user upload source for an AI model.
Smart Data Discovery AI Model
An Einstein Discovery AI model to retrieve.
## Smart Data Discovery Categorical Projected Prediction
An Einstein Discovery categorical projected prediction.
## Smart Data Discovery Classification Prediction Property
The classification prediction model type.
## Smart Data Discovery Contact
An Einstein Discovery contact.
## Smart Data Discovery Custom Prescribable Field Definition
A custom Einstein Discovery prescribable field definition to override default prescription text.
## Smart Data Discovery Customizable Field
An Einstein Discovery customizable field.
## Smart Data Discovery Feature Importance Metric
An importance metric for a Einstein Discovery model.
## Smart Data Discovery Field Mapping
An Einstein Discovery field mapping.
## Smart Data Discovery Field Mapping Analytics Dataset Field
An Einstein Discovery field mapped from an analytics dataset source.
## Smart Data Discovery Field Mapping Mapped Field
A mapped field in a field mapping.
## Smart Data Discovery Field Mapping Salesforce Field
An Einstein Discovery field mapped from a Salesforce field source.
## Smart Data Discovery Field
An Einstein Discovery field.
## Smart Data Discovery Filter List
A list of record filter conditions.
## Smart Data Discovery Filter Value
The value used in an Einstein Discovery filter.
## Smart Data Discovery Filter
An Einstein Discovery filter used to select a model.
## Smart Data Discovery Impute Strategy
The impute strategy.
## Smart Data Discovery Insight
An insight for an Einstein Discovery analysis.
## Smart Data Discovery Live Metric Detail
A live AI Einstein Discovery metric.
## Smart Data Discovery Live Metrics
The categorized live AI Einstein Discovery metrics.
## 94
Einstein Discovery REST API Response Bodies

## Smart Data Discovery Metrics Collection
A collection of Einstein Discovery metrics.
## Smart Data Discovery Model Card
An Einstein Discovery model card.
## Smart Data Discovery Prediction Definition Collection
A collection of Einstein Discovery prediction definitions.
## Smart Data Discovery Model Configuration
The configuration for an Einstein Discovery model.
## Smart Data Discovery Model Field Date
An Einstein Discovery date model field.
## Smart Data Discovery Model Field Numeric
An Einstein Discovery numeric model field.
## Smart Data Discovery Model Field Text
An Einstein Discovery text model field.
## Smart Data Discovery Model
An Einstein Discovery model.
## Smart Data Discovery Multiclass Classification Prediction Property
The multiclass classification prediction model type.
## Smart Data Discovery Multiclass Predict
An Einstein Discovery multiclass predict result.
## Smart Data Discovery Narrative Details
The textual narrative data for an Einstein Discovery story.
## Smart Data Discovery Narrative Field Collection
A collection of narrative data for an Einstein Discovery story.
## Smart Data Discovery Narrative Field
A single row of narrative data for an Einstein Discovery story.
## Smart Data Discovery Narrative Post Body Filter
A query filter for narrative data of an Einstein Discovery story.
## Smart Data Discovery Narrative Post Body Insight
The narrative insight metadata.
## Smart Data Discovery Narrative Post Body Query
A query for narrative data of an Einstein Discovery story.
## Smart Data Discovery Narrative Post Body
A single row of narrative data for an Einstein Discovery story.
## Smart Data Discovery Numeric Range
A numeric range for a field.
## Smart Data Discovery Numerical Projected Prediction
An Einstein Discovery numerical projected prediction.
## Smart Data Discovery Predict Column Custom Text
The custom text for a predict column given by the Einstein Discovery prediction.
## 95
Einstein Discovery REST API Response Bodies

## Smart Data Discovery Predict Column
A column given from an Einstein Discovery prediction.
## Smart Data Discovery Predict Condition
An Einstein Discovery predict condition.
## Smart Data Discovery Prediction Definition Collection
A collection of Einstein Discovery prediction definitions.
## Smart Data Discovery Prediction Definition
An Einstein Discovery prediction definition.
## Smart Data Discovery Prediction Error
An Einstein Discovery prediction error.
## Smart Data Discovery Prediction
An Einstein Discovery prediction result.
## Smart Data Discovery Predict Error
An Einstein Discovery predict error result.
## Smart Data Discovery Import Warnings
The import warnings for an Einstein Discovery prediction.
## Smart Data Discovery Predict Job Collection
A collection of Einstein Discovery predict jobs.
## Smart Data Discovery Predict Job
An Einstein Discovery predict job.
## Smart Data Discovery Predict List
A list of Einstein Discovery predictions.
## Smart Data Discovery Predict Settings
The settings for an Einstein Discovery prediction.
## Smart Data Discovery Predict
An Einstein Discovery predict result.
## Smart Data Discovery Prediction Definition Outcome Field
An Einstein Discovery prediction definition outcome field.
## Smart Data Discovery Prescribable Field
An Einstein Discovery prescribable field.
## Smart Data Discovery Projected Prediction Field
An Einstein Discovery projected prediction field.
## Smart Data Discovery Projected Prediction Settings
The settings for projected prediction fields.
## Smart Data Discovery Projected Predictions Count From Date Interval Setting
The settings for an Einstein Discovery count from date based projection interval.
## Smart Data Discovery Projected Predictions Count Interval Setting
The settings for an Einstein Discovery count based projection interval.
## Smart Data Discovery Projected Predictions Date Interval Setting
The settings for an Einstein Discovery date interval.
## 96
Einstein Discovery REST API Response Bodies

## Smart Data Discovery Projected Predictions Override
The settings for an Einstein Discovery projected predictions override.
## Smart Data Discovery Projected Predictions
The projected predictions for an Einstein Discovery prediction result.
## Smart Data Discovery Projected Value
An Einstein Discovery projected value.
## Smart Data Discovery Pushback Field
A pushback field for an Einstein Discovery prediction.
## Smart Data Discovery Outcome
The analysis outcome for an Einstein Discovery story.
## Smart Data Discovery Recipient
An Einstein Discovery recipient.
## Smart Data Discovery Refresh Config
The refresh configuration for an Einstein Discovery prediction.
## Smart Data Discovery Refresh Job Collection
A collection of Einstein Discovery refresh jobs.
## Smart Data Discovery Refresh Job
An Einstein Discovery refresh job.
## Smart Data Discovery Refresh Task Collection
A collection of Einstein Discovery refresh task.
## Smart Data Discovery Refresh Task Source
The source for an Einstein Discovery refresh task.
## Smart Data Discovery Refresh Task
An Einstein Discovery refresh task.
## Smart Data Discovery Regression Classification Prediction Property
The regression classification prediction model type.
## Smart Data Discovery Training Metrics
A collection of Einstein Discovery metrics from training a model.
## Smart Data Discovery User
An Einstein Discovery user.
## Story Diagnostic Insights Detail
The detail for story diagnostic insights.
## Story All Other Field Value
The story data property for all other values in a field.
## Story Chart Value
A value in a story chart.
## Story Chart Value Detail
The detail for a value in a story chart.
## Story Chart
A story chart.
## 97
Einstein Discovery REST API Response Bodies

## Story Collection
A collection of Einstein Discovery stories.
## Story Count Insights Case
A count story insights case.
## Story Day Field Value
The story data day property.
Story Day of Week Field Value
The story data day of week property.
## Story Descriptive Insights Case
A descriptive story insights case.
## Story Details
The details for a story. These details are the top positive and negative factors contributing to story outcome.
## Story Field Correlation
The summary of each field in the dataset selected for story creation.
## Story Field Impact Detail
A story field impact details.
## Story Field Label Value Property
A story field.
## Story Field Only
The story data field property.
## Story Field
The field value combination that contributed to the story outcome result.
## Story First Order Insights
The first order insights for a story.
## Story Insights Detail
The insights detail for a story.
## Story Month Field Value
The story data month property.
Story Month of Year Field Value
The story data month of year property.
## Story Narrative Element Text
The text element for a story narrative.
## Story Narrative
A narrative for a story.
## Story Null Field Value
The story data null property.
## Story Potential Bias
The potential bias for a story.
## Story Quarter Field Value
The story data quarter property.
## 98
Einstein Discovery REST API Response Bodies

Story Quarter of Year Field Value
The story data quarter of year property.
## Story Query Diagnostic Insights
A story query diagnostic insights.
## Story Query Disparate Impact Detail
The detail for a story query disparate impact.
## Story Query Disparate Impact
A disparate impact for a story query.
## Story Query Input Parameter
The input parameter for a story query.
## Story Query
A query for story insights.
## Story Range Field Value
The story data range property.
## Story Second Order Insights
The second order insights for a story.
## Story Summary Detail
The summary detail for a story.
## Story Text Field Value
The story data text property.
## Story Version Reference
The basic information for an Einstein Discovery story version.
## Story Version
An Einstein Discovery story version.
## Story
An Einstein Discovery story.
## Story Year Field Value
The story data year property.
## Text Field Configuration
The text field configuration.
## Text Field Value Configuration
The text field value configuration.
## Validation Dataset
The output for a validation dataset configuration.
## Validation Ratio
The output for a validation ratio configuration.
## Abstract Bucketing Strategy
The base bucketing strategy.
## 99
Abstract Bucketing StrategyEinstein Discovery REST API Response Bodies

## Properties
Inherited by EvenWidthBucketingStrategy, ManualBucketingStrategy, and PercentileBucketingStrategy.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The bucketing strategy. Valid values are:SmartDataDiscovery
BucketingStrategy
## Enum
type
## •
EvenWidth
## •
## Manual
## •
## Percentage
## Abstract Classification Threshold
The base classification threshold.
## Properties
Inherited by Binary Classification Threshold.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
47.0Small, 47.0The classification type. Valid values are:ClassificationType
## Enum
type
## •
## Binary
## Abstract Date Field Configuration
The base Einstein Discovery date field configuration.
## Properties
Inherits properties from AbstractFieldConfiguration.
Inherited by DateFieldConfiguration.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The date interval for the field. Valid values
are:
SmartDataDiscovery
DateIntervalEnum
interval
## •
## Auto
## •
## Day
## •
## Month
## •
## None
## •
## Quarter
## •
## Year
## 100
Abstract Classification ThresholdEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The maximum date value for the field.Datemax
54.0Small, 54.0The minimum date value for the field.Datemin
54.0Small, 54.0A list of the periodic date intervals for the
field. Valid values are:
SmartDataDiscovery
PeriodicDateInterval
## Enum[]
periodic
## Intervals
## •
## Day_of_week
## •
## Month_of_year
## •
## Quarter_of_year
## Abstract Field Configuration
The base Einstein Discovery field configuration.
## Properties
Inherited by AbstractDateFieldConfiguration, AbstractNumericFieldConfiguration, andAbstractTextFieldConfiguration
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0Indicates whether the field is a high
cardinality field (true) or not (false).
## Booleanhigh
## Cardinality
54.0Small, 54.0Indicates whether the field is ignored
(true) or not (false).
## Booleanignored
54.0Small, 54.0The developer name for the field.Stringlabel
54.0Small, 54.0The display name for the field.Stringname
54.0Small, 54.0Indicates whether the field is sensitive
(true) or not (false).
## Booleansensitive
54.0Small, 54.0The field type. Valid values are:SmartDataDiscovery
FilterFieldTypeEnum
type
## •
## Boolean
## •
## Date
## •
DateTime
## •
## Number
## •
## Text
## Abstract Numeric Field Configuration
The base Einstein Discovery numeric field configuration.
## 101
Abstract Field ConfigurationEinstein Discovery REST API Response Bodies

## Properties
Inherits properties from AbstractFieldConfiguration.
Inherited by NumericFieldConfiguration.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The bucketing strategy for the field. Valid
values are:
AbstractBucketing
## Strategy
bucketing
## Strategy
## •
EvenWidthBucketingStrategy
## •
ManualBucketingStrategy
## •
PercentileBucketingStrategy
54.0Small, 54.0The impute strategy for the field.SmartDataDiscovery
ImputeStrategy
impute
## Strategy
54.0Small, 54.0The maximum value for the field.Doublemax
54.0Small, 54.0The minimum value for the field.Doublemin
## Abstract Smart Data Discovery Aggregate Prediction
The base Einstein Discovery aggregate prediction result.
## Properties
Inherited by Smart Data Discovery Aggregate Prediction and Smart Data Discovery Aggregate Prediction Error.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The predict aggregate function. Valid
values are:
SmartDataDiscovery
PredictAggregate
FunctionEnum
aggregate
## Function
## •
## Average
## •
## Median
## •
## Sum
55.0Small, 55.0The list of middle values.SmartDataDiscovery
AggregatePredict
## Condition[]
middleValues
55.0Small, 55.0The list of prescriptions.SmartDataDiscovery
AggregatePredict
## Condition[]
prescriptions
55.0Small, 55.0The predict aggregate status. Valid values
are:
SmartDataDiscovery
PredictAggregate
StatusEnum
status
## •
## Error
## 102
Abstract Smart Data Discovery Aggregate PredictionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
## Success
Abstract Smart Data Discovery AI Model Metrics
The base Einstein Discovery AI model metric.
## Properties
Inherited by Smart Data Discovery AI Model Classification Metrics, Smart Data Discovery AI Model Multiclass Metrics, and Smart Data
Discovery AI Model Regression Metrics.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The URL to the data segments metrics for
the AI model.
StringdataSegments
## Url
56.0Small, 56.0The URL to the feature importances
metrics for the AI model.
## Stringfeature
## Importances
## Url
54.0Small, 54.0The prediction type of the AI model. Valid
values are:
SmartDataDiscovery
PredictionType
## Enum
prediction
## Type
## •
## Classification
## •
MulticlassClassification
## •
## Regression
## •
## Unknown
54.0Small, 54.0The URL for the metricsStringurl
Abstract Smart Data Discovery AI Model Source
The base Einstein Discovery AI model prediction property.
## Properties
Inherited by Smart Data Discovery AI Model Discovery Source and Smart Data Discovery AI Model User Upload Source.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The source type of the AI model. Valid
values are:
SmartDataDiscovery
ModelSourceType
## Enum
type
## •
## Discovery
## •
UserUpload
## 103
Abstract Smart Data Discovery AI Model MetricsEinstein Discovery REST API Response Bodies

## Abstract Smart Data Discovery Field Mapping Source
The base Einstein Discovery field mapping source.
## Properties
Inherited by Smart Data Discovery Field Mapping Analytics Dataset Field and Smart Data Discovery Field Mapping Salesforce Field.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The source type for the field mapping.
Valid values are:
SmartDataDiscovery
FieldMapSource
TypeEnum
type
## •
AnalyticsDatasetField
## •
SalesforceField
## Abstract Smart Data Discovery Model Field
The base Einstein Discovery model field.
## Properties
Inherited by Smart Data Discovery Model Field Date, Smart Data Discovery Model Field Numeric and Smart Data Discovery Model
## Field Text.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0Indicates whether the model field is
disparate impact (true) or not (false).
## Booleandisparate
## Impact
48.0Small, 48.0The label of the model field.Stringlabel
48.0Small, 48.0The name of the model field.Stringname
55.0Small, 55.0Indicates whether the model field is
sensitive (true) or not (false).
## Booleansensitive
48.0Small, 48.0The type of the model field. Valid values
are:
SmartDataDiscovery
ModelFieldType
## Enum
type
## •
## Date
## •
## Number
## •
## Text
## Abstract Smart Data Discovery Model Runtime
The base Einstein Discovery model run time.
## 104
Abstract Smart Data Discovery Field Mapping SourceEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The run time type of the model. Valid
values are:
SmartDataDiscovery
ModelRuntimeType
## Enum
type
## •
## Discovery
## •
## H2O
## •
Py36Tensorflow244
(TensorFlow)
## •
Py37Scikitlearn102 (Scikit
Learn v1.0.2)
## •
Py37Tensorflow207
(TensorFlow v2.7.0)
## Abstract Smart Data Discovery Prediction Property
The base Einstein Discovery AI model prediction property.
## Properties
Inherited by Smart Data Discovery Classification Prediction Property, Smart Data Discovery Multiclass Classification Prediction Property,
and Smart Data Discovery Regression Classification Prediction Property.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
44.0Small, 44.0The prediction type. Valid values are:SmartDataDiscovery
PredictionType
## Enum
type
## •
## Classification
## •
MulticlassClassification
## •
## Regression
## •
## Unknown
## Abstract Smart Data Discovery Prediction
The base Einstein Discovery prediction result.
## Properties
Inherited by Smart Data Discovery Prediction and Smart Data Discovery Prediction Error.
## 105
Abstract Smart Data Discovery Prediction PropertyEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
44.0Small, 44.0The predict status. Valid values are:SmartDataDiscovery
PredictStatusEnum
status
## •
## Error
## •
## Success
## Abstract Smart Data Discovery Predict
The base Einstein Discovery predict result.
## Properties
Inherited by Smart Data Discovery Multiclass Prediction, Smart Data Discovery Predict Error and Smart Data Discovery Predict.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
41.0Small, 41.0The base line metric for the predict result.DoublebaseLine
41.0Small, 41.0The import warnings for the predict result.SmartDataDiscovery
PredictImport
## Warnings
import
## Warnings
41.0Small, 41.0Any other values for the predict result.Doubleother
41.0Small, 41.0The small term count for the predict result.IntegersmallTerm
## Count
41.0Small, 41.0The total of the predict result.Integertotal
## Abstract Smart Data Discovery Projected Prediction
The base Einstein Discovery projected prediction result.
## Properties
Inherited by Smart Data Discovery Catagorical Projected Prediction and Smart Data Discovery Numerical Projected Prediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The projected predictions type. Valid
values are:
SmartDataDiscovery
ProjectedPredictions
TypeEnum
type
## •
## Categorical
## •
## Numerical
## 106
Abstract Smart Data Discovery PredictEinstein Discovery REST API Response Bodies

## Abstract Smart Data Discovery Projected Predictions Interval Setting
The base Einstein Discovery projected predictions interval settings.
## Properties
Inherited by Smart Data Discovery Projected Predictions Count From Date Interval Setting, Smart Data Discovery Projected Predictions
Count Interval Setting, and Smart Data Discovery Projected Predictions Date Interval Setting.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The projected predictions interval setting
type. Valid values are:
SmartDataDiscovery
ProjectedPredictions
IntervalSettingType
## Enum
type
## •
## Count
## •
CountFromDate
## •
## Date
## Abstract Smart Data Discovery Transformation Override
The base Einstein Discovery transformation deploy overrides.
## Properties
Inherited by Smart Data Discovery Projected Predictions Override.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The ID of the override.Stringid
55.0Small, 55.0A transformation asset associated with the
override settings.
AssetReferenceinput
55.0Small, 55.0The transformation type. Valid values are:SmartDataDiscovery
AIModel
type
## •
CategoricalImputation
(Replace categorical missing values)
TransformationType
## Enum
## •
ExtractDayOfWeek (Extract day
of week)
## •
ExtractMonthOfYear (Extract
month of year)
## •
FreeTextClustering (Free text
clustering)
## •
NumericalImputation
(Replace numerical missing values)
## •
SentimentAnalysis (Detecting
sentiment)
## 107
## Abstract Smart Data Discovery Projected Predictions Interval
## Setting
Einstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
TimeSeriesForecast
(Projected predictions)
## •
TypographicClustering
(Fuzzy matching)
## Abstract Smart Data Discovery Validation Configuration
The base validation configuration output.
## Properties
Inherited by Validation Dataset and Validation Ratio.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0The validation strategy for the
configuration. Valid values are:
## Validation
## Configuration
StrategyEnum
strategy
## •
Validation_Dataset
## •
Validation_Set_Ratio
## Abstract Story Data Property
The base Einstein Discovery story data property filter.
## Properties
Inherited by Story All Other Field Value, Story Day Field Value, Story Day Of Week Field Value, Story Field Only, Story Month Field
Value, Story Month Of Year Field Value, Story Null Field Value, Story Quarter Field Value, Story Quarter Of Year Field Value, Story Range
Field Value, Story Text Field Value, and Story Year Field Value.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The filter field developer name.Stringfield
52.0Small, 52.0The filter field type.Stringtype
## Abstract Story Insights Case
The base story insights case.
## Properties
Inherited by StoryDescriptiveInsightsCase and StoryCountInsightsCase.
## 108
Abstract Smart Data Discovery Validation ConfigurationEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The case field for the story insight.StoryFieldLabel
ValueProperty
field
52.0Small, 52.0The analysis type. Valid values are:StoryAnalysisType
## Enum
type
## •
## Count
## •
## Descriptive
52.0Small, 52.0The field value for the story insight.Stringvalue
## Abstract Story Insights
The base story insights.
## Properties
Inherited by StoryFirstOrderInsights and StorySecondOrderInsights.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The insights chart for the story.StoryChartchart
52.0Small, 52.0A list of insight details for the story.StoryInsightsDetail[]details
52.0Small, 52.0The insights filter field details for the story.StoryFieldLabel
ValueProperty
filterField
54.0Small, 54.0The insights narrative for the story.StoryNarrativenarrative
52.0Small, 52.0The descriptive insights result type. Valid
values are:
InsightsResultsType
## Enum
type
## •
FirstOrder
## •
SecondOrder
## Abstract Story Narrative Element
The base story narrative element.
## Properties
Inherited by StoryNarrativeElementText.
## 109
Abstract Story InsightsEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The narrative element type. Valid values
are:
StoryNarrative
ElementTypeEnum
type
## •
BadSelection
## •
## Body
## •
BucketsMismatchSection
## •
GoodSection
## •
## Heading
## •
MissingValuesSection
## •
NewValuesSection
## •
NumberedList
## •
OutcomeValue
## •
## Paragraph
## •
SubHeading
## •
UnorderedList
## Abstract Story Source
The base Einstein Discovery analysis source.
## Properties
Inherited by AnalyticsDatasetSource and ReportSource.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
45.0Small, 45.0The source type of the analysis. Valid values
are:
AnalysisSetup
SourceTypeEnum
type
## •
AnalyticsDataset
## •
LiveDataset
## •
## Report
## Abstract Text Field Configuration
The base Einstein Discovery text field configuration.
## Properties
Inherits properties from AbstractFieldConfiguration.
Inherited by TextFieldConfiguration.
## 110
Abstract Story SourceEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0Indicates whether values that don't match
the specified values should be grouped
into other (true) or not (false).
BooleanincludeOther
54.0Small, 54.0The strategy for ordering text values. Valid
values are:
SmartDataDiscovery
OrderingEnum
ordering
## •
## Alphabetical
## •
## Numeric
## •
## Occurrence
54.0Small, 54.0A list of values for the field.TextFieldValue
## Configuration[]
values
## Analytics Dataset Source
An analytics dataset as the analysis source.
## Properties
Inherits properties from AbstractStorySource.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
45.0Small, 45.0The dataset for an analysis source.Asset Referencedataset
45.0Small, 45.0The dataset version for an analysis source.Asset Referencedataset
## Version
## Asset History Collection
A collection of asset history items.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
46.0Small, 46.0The list of asset histories.AssetHistory[]histories
## Asset History
The asset history record.
## 111
Analytics Dataset SourceEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
46.0Small, 46.0The user who created the asset history
record.
WaveUsercreatedBy
46.0Small, 46.0The creation date of the asset history
record.
DatecreatedDate
46.0Small, 46.0The URL to the asset history metadata
details.
StringhistoryUrl
46.0Small, 46.0The ID for the asset history record.Stringid
47.0Small, 47.0Indicates whether this history record is the
current version of the asset (true) or not
## (false).
BooleanisCurrent
46.0Small, 46.0The optional label tag for the asset history
record.
## Stringlabel
46.0Small, 46.0The developer name for the asset history
record.
## Stringname
46.0Small, 46.0The URL to preview how an asset looked
at a particular point in time. This URL
StringpreviewUrl
doesn't revert the current asset to the asset
history record.
46.0Small, 46.0The URL to revert the current asset to this
asset history record.
StringrevertUrl
49.0Small, 49.0The status value of the asset.Stringstatus
## Asset Reference
An Einstein Discovery asset reference. This wraps the BaseAssetReference
## Properties
## Base Asset Reference
## Autopilot
The setup for autopilot.
## 112
Asset ReferenceEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0Indicates whether autopilot is enabled
(true) or not (false).
## Booleanenabled
## Base Asset Reference
The base Einstein Discovery asset, inherited by AssetReference.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
42.0Small, 42.0The ID of the asset.Stringid
42.0Small, 42.0The label of the asset.Stringlabel
42.0Small, 42.0The developer name of the asset.Stringname
42.0Small, 42.0The namespace that qualifies the asset
name.
## Stringnamespace
42.0Small, 42.0The URL of the asset.Stringurl
## Binary Classification Threshold
A binary classification threshold.
## Properties
Inherits properties from AbstractClassificationThreshold.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
47.0Small, 47.0The data for a source analysis.Doublevalue
## Date Field Configuration
The date field configuration.
## Properties
Inherits properties from AbstractDateFieldConfiguration.
## 113
Base Asset ReferenceEinstein Discovery REST API Response Bodies

## Diagnostic Insights Case
A story query diagnostic insights.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
53.0Small, 53.0The change in outcome score.DoublechangeIn
## Outcome
53.0Small, 53.0A list of fields responsible for impact on
outcome due to the selected condition.
StoryFieldLabel
ValueProperty[]
fields
53.0Small, 53.0The global mean without any condition.DoubleglobalMean
53.0Small, 53.0Indicates whether the demographic
changed due to this case (true) or not
## (false).
## Booleanhas
## Demographic
## Changed
53.0Small, 53.0The mean with the primary condition
selected for diagnostic insight.
DoublemeanWith
## Condition
53.0Small, 53.0The change in outcome value. Valid values
are:
InsightsOutcome
ChangeEnum
outcomeChange
## Type
## •
## Decreased
## •
## Increased
## Directory Item Collection
A collection of directory items.
## Properties
## Available
## Version
## Filter Group
and Version
DescriptionTypeProperty Name
50.0Small, 50.0A list of items in the collection and their URLs.Stringitems
## Even Width Bucketing Strategy
The even-width bucketing strategy.
## Properties
Inherits properties from AbstractBucketingStrategy.
## 114
Diagnostic Insights CaseEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The number of buckets for a numeric field.IntegernumberOf
## Buckets
## Manual Bucketing Strategy
The manual bucketing strategy.
## Properties
Inherits properties from AbstractBucketingStrategy.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0A list of manual buckets for a numeric field.Double[]cutoffs
## Model Field Label Metrics
Model field information that includes label, value and metrics data.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The label of the model field.StringfieldLabel
56.0Small, 56.0The name of the model field.StringfieldName
56.0Small, 56.0The metrics value of the model field.Doublevalue
## Numeric Field Configuration
The numeric field configuration.
## Properties
Inherits properties from AbstractNumericFieldConfiguration.
## Percentile Bucketing Strategy
The percentile bucketing strategy.
## Properties
Inherits properties from AbstractBucketingStrategy.
## 115
Manual Bucketing StrategyEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The number of buckets for a numeric field.IntegernumberOf
## Buckets
## Predict History Collection
A collection of historical predictions for a goal.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The prediction goal.AssetReferencegoal
56.0Small, 56.0The prediction history.PredictHistoryhistory
56.0Small, 56.0The range used to query the prediction
history.
PredictHistoryRangerange
## Predict History
The historical predictions for a target.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0A list of the predictions that were made.PredictHistory
## Value[]
predictions
56.0Small, 56.0The ID of prediction target.Stringtarget
## Predict History Range
A range used for the historical prediction query.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The interval for look back. Valid values are:PredictHistory
IntervalEnum
interval
## •
## None
## •
## Weekly
## 116
Predict History CollectionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The maximum look back period.IntegermaxLookBack
## Predict History Value
A historical prediction value at a specific point in time.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The date the prediction was made.DatecreatedDate
56.0Small, 56.0The model used to make the prediction.AssetReferencemodel
56.0Small, 56.0The prediction value.Stringvalue
## Report Source
An analytics report as the analysis source.
## Properties
Inherits properties from AbstractStorySource.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
45.0Small, 45.0The report for an analysis source.Asset Referencereport
45.0Small, 45.0The report instance for an analysis source.Asset Referencereport
## Instance
## Smart Data Discovery Aggregate Predict Condition
The aggregate predict condition for a collection of Einstein Discover predictions.
## Properties
## Available
## Version
## Filter Group
and Version
DescriptionTypeProperty Name
55.0Small, 55.0The count of rows included in the aggregate conditionIntegercount
## 117
Predict History ValueEinstein Discovery REST API Response Bodies

## Smart Data Discovery Aggregate Prediction Error
An Einstein Discovery aggregate prediction error.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAggregatePrediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The error code.IntegererrorCode
55.0Small, 55.0The error message.Stringmessage
## Smart Data Discovery Aggregate Prediction
An Einstein Discovery aggregate prediction result.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAggregatePrediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The value of the aggregate result.Doublevalue
Smart Data Discovery AI Model Classification Metrics
The binomial classification metrics for an Einstein Discovery AI model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelMetrics.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The AUC for the model.Doubleauc
54.0Small, 54.0The false negative rate for the model.DoublefalseNegative
## Rate
54.0Small, 54.0The false positive rate for the model.DoublefalsePositive
## Rate
54.0Small, 54.0The GINI for the model.Doublegini
54.0Small, 54.0The MCC for the model.Doublemcc
54.0Small, 54.0The true negative rate for the model.DoubletrueNegative
## Rate
## 118
Smart Data Discovery Aggregate Prediction ErrorEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The true positive rate for the model.DoubletruePositive
## Rate
Smart Data Discovery AI Model Coefficient Collection
A collection of Einstein Discovery AI model coefficients.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The list of coefficients for the model.SmartDataDiscovery
PredictCondition[]
coefficients
55.0Small, 55.0The URL to get the next page of results.StringnextPageUrl
55.0Small, 55.0The total count of items in the collection.IntegertotalSize
55.0Small, 55.0The URL to get the collection.Stringurl
Smart Data Discovery AI Model Collection
A collection of Einstein Discovery AI models.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The list of AI models available to the
current user.
SmartDataDiscovery
AIModel[]
models
51.0Small, 51.0The URL to get the next page of results.StringnextPageUrl
48.0Small, 48.0The total count of items in the collection.IntegertotalSize
48.0Small, 48.0The URL to get the collection.Stringurl
Smart Data Discovery AI Model Discovery Source
The discovery source for an AI model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelSource.
## 119
Smart Data Discovery AI Model Coefficient CollectionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The source story asset.Asset Referencestory
48.0Small, 48.0The source story history asset.Asset ReferencestoryHistory
Smart Data Discovery AI Model Multiclass Metrics
The multiclass metrics for an Einstein Discovery AI model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelMetrics.
Smart Data Discovery AI Model Regression Metrics
The regression metrics for an Einstein Discovery AI model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelMetrics.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The MAE for the model.Doublemae
55.0Small, 55.0The residuals URL for the model.StringresidualsUrl
54.0Small, 54.0The RMSE for the model.Doublermse
54.0Small, 54.0The R Squared for the model.Doublersquared
Smart Data Discovery AI Model Residual Collection
A collection of Einstein Discovery AI model residuals.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The URL to get the next page of results.StringnextPageUrl
55.0Small, 55.0The list of residuals for the model.SmartDataDiscovery
AIModelResidual[]
residuals
55.0Small, 55.0The total count of items in the collection.IntegertotalSize
55.0Small, 55.0The URL to get the collection.Stringurl
## 120
Smart Data Discovery AI Model Multiclass MetricsEinstein Discovery REST API Response Bodies

Smart Data Discovery AI Model Residual
AnEinstein Discovery AI model residual.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The actual value.Doubleactual
55.0Small, 55.0The predicted value.Doublepredicted
Smart Data Discovery AI Model Transformation
An Einstein Discovery AI model transformation.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The ID for the AI model.Stringid
54.0Small, 54.0A list of the model field names used as
input parameters by the transformation.
Valid values are:
AbstractSmartData
DiscoveryModel
## Field[]
sourceFields
## •
SmartDataDiscoveryModelFieldDate
## •
SmartDataDiscoveryModelField
## Numeric
## •
SmartDataDiscoveryModelFieldText
51.0Small, 51.0A map of the model transformation state.Map<Object,
## Object>
state
54.0Small, 54.0A list of the model field names modified
by the transformation. Valid values are:
AbstractSmartData
DiscoveryModel
## Field[]
targetFields
## •
SmartDataDiscoveryModelFieldDate
## •
SmartDataDiscoveryModelField
## Numeric
## •
SmartDataDiscoveryModelFieldText
51.0Small, 51.0The model transformation type. Valid
values are:
SmartDataDiscovery
AIModel
TransformationType
## Enum
type
## •
CategoricalImputation
(Replace categorical missing values)
## •
ExtractDayOfWeek (Extract day
of week)
## 121
Smart Data Discovery AI Model ResidualEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
ExtractMonthOfYear (Extract
month of year)
## •
FreeTextClustering (Free text
clustering)
## •
NumericalImputation
(Replace numerical missing values)
## •
SentimentAnalysis (Detecting
sentiment)
## •
TimeSeriesForecast
(Projected predictions)
## •
TypographicClustering
(Fuzzy matching)
Smart Data Discovery AI Model User Upload Source
The user upload source for an AI model.
## Properties
Inherits properties from AbstractSmartDataDiscoveryAIModelSource.
Smart Data Discovery AI Model
An Einstein Discovery AI model to retrieve.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The coefficients URL for the AI model.Stringcoefficients
## Url
48.0Small, 48.0The user that created the AI modelSmartDataDiscovery
## User
createdBy
48.0Small, 48.0The date on which the AI model was
created.
DatecreatedDate
48.0Small, 48.0The description for the AI model.Stringdescription
48.0Small, 48.0The ID for the AI model.Stringid
## 122
Smart Data Discovery AI Model User Upload SourceEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The input source for the AI model. Valid
data properties are:
AbstractSmartData
DiscoveryAIModel
## Source
input
## •
Smart Data Discovery AI Model
## Discovery Source
## •
Smart Data Discovery AI Model User
## Upload Source
48.0Small, 48.0The label for the AI model.Stringlabel
48.0Small, 48.0The user who last modified the AI modelSmartDataDiscovery
## User
lastModified
## By
48.0Small, 48.0The date on which the AI model was last
modified.
DatelastModified
## Date
54.0Small, 54.0The metrics URL for the AI model.StringmetricsUrl
48.0Small, 48.0The list of model fields for the AI model.
Valid values are:
AbstractSmartData
DiscoveryModel
## Field[]
modelFields
## •
SmartDataDiscoveryModelFieldDate
## •
SmartDataDiscoveryModelField
## Numeric
## •
SmartDataDiscoveryModelFieldText
49.0Small, 49.0The file URL for the AI model.StringmodelFileUrl
48.0Small, 48.0The run time model for the AI model.AbstractSmartData
DiscoveryModel
## Runtime
modelRuntime
48.0Small, 48.0The developer name for the AI model.Stringname
51.0Small, 51.0The namespace for the AI model.Stringnamespace
48.0Small, 48.0The predicted field name for the AI model.Stringpredicted
## Field
48.0Small, 48.0The prediction property for the AI model.
Valid prediction properties are:
AbstractSmartData
DiscoveryPrediction
## Property
prediction
## Property
## •
## Smart Data Discovery Classification
## Prediction Property
## •
## Smart Data Discovery Multiclass
## Classification Prediction Property
## •
## Smart Data Discovery Regression
## Classification Prediction Property
48.0Small, 48.0The model status. Valid values are:SmartDataDiscovery
AIModelStatusEnum
status
## •
## Disabled
## 123
Smart Data Discovery AI ModelEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
## Enabled
## •
UploadCompleted
## •
UploadFailed
## •
## Uploading
## •
## Validating
## •
ValidationCompleted
## •
ValidationFailed
48.0Small, 48.0The list of transformations associated with
the AI model.
SmartDataDiscovery
AIModel
## Transformation[]
transformations
48.0Small, 48.0The URL for the AI model.Stringurl
50.0Small, 50.0The validation result for the AI model,
when available.
Map<Object,
## Object>
validation
## Result
## Smart Data Discovery Categorical Projected Prediction
An Einstein Discovery categorical projected prediction.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPrediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The predict probabilities for each class.Doubleclass
## Probabilities
54.0Small, 54.0The prediction outcome.Stringprediction
## Smart Data Discovery Classification Prediction Property
The classification prediction model type.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictionProperty.
## 124
Smart Data Discovery Categorical Projected PredictionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The classification algorithm type. Valid
values are:
SmartDataDiscovery
## Classification
AlgorithmType
## Enum
algorithmType
## •
Best (Model tournament)
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
48.0Small, 48.0The classification threshold (e.g. binary
classification threshold for logistic
regression models).
BinaryClassification
## Threshold
classification
## Threshold
## Smart Data Discovery Contact
An Einstein Discovery contact.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The email for the contact.Stringemail
51.0Small, 51.0The name of the contact.Stringname
## Smart Data Discovery Custom Prescribable Field Definition
A custom Einstein Discovery prescribable field definition to override default prescription text.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0A list of filter rules for enabling custom text.SmartDataDiscovery
## Filter[]
filters
50.0Small, 50.0The template text to use in replacements.StringtemplateText
## Smart Data Discovery Customizable Field
An Einstein Discovery customizable field.
## 125
Smart Data Discovery ContactEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0A list of custom field definitions.SmartDataDiscovery
CustomPrescribable
FieldDefinition[]
custom
## Definitions
57.0Small, 57.0The name of the customizable field.StringfieldName
## Smart Data Discovery Feature Importance Metric
An importance metric for a Einstein Discovery model.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The list of importance metrics.ModelFieldLabel
## Metrics[]
feature
## Importance
56.0Small, 56.0The URL to the importance metrics.Stringurl
## Smart Data Discovery Field Mapping
An Einstein Discovery field mapping.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The field mapping source. Valid values are:AbstractSmartData
DiscoveryField
MappingSource
input
## •
## Smart Data Discovery Field Mapping
## Analytics Dataset Field
## •
## Smart Data Discovery Field Mapping
## Salesforce Field
48.0Small, 48.0The mapped field.SmartDataDiscovery
FieldMapping
MappedField
mappedField
48.0Small, 48.0The model field. Valid values are:AbstractSmartData
DiscoveryModel
## Field[]
modelField
## •
SmartDataDiscoveryModelFieldDate
## •
SmartDataDiscoveryModelField
## Numeric
## 126
Smart Data Discovery Feature Importance MetricEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
SmartDataDiscoveryModelFieldText
## Smart Data Discovery Field Mapping Analytics Dataset Field
An Einstein Discovery field mapped from an analytics dataset source.
## Properties
Inherits properties from AbstractSmartDataDiscoveryFieldMappingSource.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The sObject field name used as the join
key.
StringsobjectField
JoinKey
48.0Small, 48.0A source ID of the analytics dataset asset.AssetReferencesource
48.0Small, 48.0The source dataset field name used as the
join key.
StringsourceField
JoinKey
## Smart Data Discovery Field Mapping Mapped Field
A mapped field in a field mapping.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The label of the mapped field.Stringlabel
48.0Small, 48.0The name of the mapped field.Stringname
48.0Small, 48.0The type of the mapped field.Stringtype
## Smart Data Discovery Field Mapping Salesforce Field
An Einstein Discovery field mapped from a Salesforce field source.
## Properties
Inherits properties from AbstractSmartDataDiscoveryFieldMappingSource.
## 127
Smart Data Discovery Field Mapping Analytics Dataset FieldEinstein Discovery REST API Response Bodies

## Smart Data Discovery Field
An Einstein Discovery field.
## Properties
Inherited by Smart Data Discovery Pushback Field.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
46.0Small, 46.0The label of the field.Stringlabel
46.0Small, 46.0The name of the field.Stringname
## Smart Data Discovery Filter List
A list of record filter conditions.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
46.0Small, 46.0The list of filter conditions.SmartDataDiscovery
## Filter[]
filters
## Smart Data Discovery Filter Value
The value used in an Einstein Discovery filter.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The type of the filter value. Valid values are:SmartDataDiscovery
FilterValueType
## Enum
type
## •
## Constant
## •
## Placeholder
50.0Small, 50.0The value of the filter. The value can be a
constant or a valid placeholder.
## Stringvalue
## Smart Data Discovery Filter
An Einstein Discovery filter used to select a model.
## 128
Smart Data Discovery FieldEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
41.0Small, 41.0The developer name of the field to apply
the filter to.
StringfieldName
50.0Small, 50.0An ordered list of values to be applied in
the filter.
SmartDataDiscovery
FilterValue[]
filterValues
54.0Small, 54.0The operator to apply to this filter. Valid
values are:
ConnectSmartData
DiscoveryFilter
OperatorEnum
operator
## •
## Between
## •
## Contains
## •
EndsWith
## •
## Equal
## •
GreaterThan
## •
GreaterThanOrEqual
## •
InSet
## •
LessThan
## •
LessThanOrEqual
## •
NotBetween
## •
NotEqual
## •
NotIn
## •
StartsWith
48.0Small, 48.0The filter field type. Valid values are:SmartDataDiscovery
FilterFieldTypeEnum
type
## •
## Boolean
## •
## Date
## •
DateTime
## •
## Number
## •
## Text
## Smart Data Discovery Impute Strategy
The impute strategy.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The field name value to group by.StringgroupByFieldName
## 129
Smart Data Discovery Impute StrategyEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The impute method. Valid values are:SmartDataDiscovery
ImputeMethod
## Enum
method
## •
## Mean
## •
## Median
## •
## Mode
## •
## None
## Smart Data Discovery Insight
An insight for an Einstein Discovery analysis.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
44.0Small, 44.0The id of the insight.IDid
44.0Small, 44.0A map of the properties for the insight.Map<Object,
## Object>
properties
44.0Small, 44.0The sort order of the insight.IntegersortOrder
## Smart Data Discovery Live Metric Detail
A live AI Einstein Discovery metric.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The end date of this metric.DateendDate
50.0Small, 50.0The row count of this metric.IntegerrowCount
50.0Small, 50.0The start date of this metric.DatestartDate
50.0Small, 50.0The complex value of this metric
represented as a Map.
Map<Object,
## Object>
value
## Smart Data Discovery Live Metrics
The categorized live AI Einstein Discovery metrics.
## 130
Smart Data Discovery InsightEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0A list of disparateImpact metrics
during the span.
SmartDataDiscovery
LiveMetricDetail[]
disparate
## Impacts
50.0Small, 50.0A list of missing column metrics during the
span.
SmartDataDiscovery
LiveMetricDetail[]
missing
## Columns
50.0Small, 50.0A list of out of bounds column metrics
during the span.
SmartDataDiscovery
LiveMetricDetail[]
outOfBounds
## Columns
50.0Small, 50.0A list of the total predictions during the
span.
SmartDataDiscovery
LiveMetricDetail[]
predictions
50.0Small, 50.0A list of the total warnings during the span.SmartDataDiscovery
LiveMetricDetail[]
warnings
## Smart Data Discovery Metrics Collection
A collection of Einstein Discovery metrics.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The live metrics from running predictions.SmartDataDiscovery
LiveMetrics
liveMetrics
51.0Small, 51.0The total number of active models.IntegertotalActive
## Models
51.0Small, 51.0The total number of models.IntegertotalModels
50.0Small, 50.0The model level metrics from training.SmartDataDiscovery
TrainingMetrics
training
## Metrics
50.0Small, 50.0The URL to get the metrics results.Integerurl
## Smart Data Discovery Model Card
An Einstein Discovery model card.
## 131
Smart Data Discovery Metrics CollectionEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The contact person for the model card.SmartDataDiscovery
## Contact
contact
51.0Small, 51.0The user who created the model card.SmartDataDiscovery
## User
createdBy
51.0Small, 51.0The creation date of the model card.DatecreatedDate
51.0Small, 51.0The ID of the model card.Stringid
51.0Small, 51.0The label of the model card.Stringlabel
51.0Small, 51.0The user who last modified the model card.SmartDataDiscovery
## User
lastModified
## By
51.0Small, 51.0The last modified date of the model card.DatelastModified
## Date
51.0Small, 51.0A map of the user customizable
description for the model card.
Map<Object,
## Object>
sections
51.0Small, 51.0The URL for the model card.Stringurl
## Smart Data Discovery Prediction Definition Collection
A collection of Einstein Discovery prediction definitions.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
41.0Small, 41.0The list of models.SmartDataDiscovery
## Model[]
models
41.0Small, 41.0The total count of items in the collection.IntegertotalSize
41.0Small, 41.0The URL to get the collection.Stringurl
## Smart Data Discovery Model Configuration
The configuration for an Einstein Discovery model.
## 132
Smart Data Discovery Prediction Definition CollectionEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The algorithm type for the model. Valid
values are:
SmartDataDiscovery
## Classification
AlgorithmType
## Enum
algorithmType
## •
Best (Model tournament)
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
## Smart Data Discovery Model Field Date
An Einstein Discovery date model field.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelField.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0A list of model field unique values.String[]values
## Smart Data Discovery Model Field Numeric
An Einstein Discovery numeric model field.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelField.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0A list of model field unique values.SmartDataDiscovery
NumericRange[]
values
## Smart Data Discovery Model Field Text
An Einstein Discovery text model field.
## Properties
Inherits properties from AbstractSmartDataDiscoveryModelField.
## 133
Smart Data Discovery Model Field DateEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0A list of model field unique values.String[]values
## Smart Data Discovery Model
An Einstein Discovery model.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The classification threshold for the model.
Valid values are:
## Abstract
## Classification
## Threshold
classification
## Threshold
## •
BinaryClassificationThreshold
41.0Small, 41.0The user who created the model.SmartDataDiscovery
## User
createdBy
41.0Small, 41.0The creation date of the model.DatecreatedDate
57.0Small, 57.0A list of customizable top factors for the
model.
SmartDataDiscovery
CustomizableField[]
customizable
## Factors
48.0Small, 48.0A list mapping the model fields to
Salesforce fields.
SmartDataDiscovery
FieldMapping[]
fieldMapping
## List
41.0Small, 41.0A list of filters used to determine whether
this model should be applied to a record.
SmartDataDiscovery
## Filter[]
filters
49.0Small, 49.0The URL for the model history.StringhistoryUrl
41.0Small, 41.0The ID of the model.Stringid
50.0Small, 50.0Indicates whether this model is included
in the refresh schedule (true) or not
## (false).
BooleanisRefresh
## Enabled
41.0Small, 41.0The label of the model.Stringlabel
41.0Small, 41.0The user who last modified the model.SmartDataDiscovery
## User
lastModified
## By
41.0Small, 41.0The last modified date of the model.DatelastModified
## Date
48.0Small, 48.0A ID for the AI model.AssetReferencemodel
47.0Small, 47.0The type of the model.StringmodelType
41.0Small, 41.0The developer name of the model.Stringname
## 134
Smart Data Discovery ModelEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
41.0Small, 41.0The URL to the prediction definition for the
model.
## Stringprediction
DefinitionUrl
48.0Small, 48.0A list of the prescribable fields for the
model.
SmartDataDiscovery
PrescribableField[]
prescribable
## Fields
41.0Small, 41.0A unique number indicating the order in
which this model's filters are evaluated
IntegersortOrder
compared to all other models in the parent
prediction definition.
46.0Small, 46.0The status of the model. Valid values are:SmartDataDiscovery
StatusEnum
status
## •
## Disabled
## •
## Enabled
52.0Small, 52.0A story asset reference information.AssetReferencestory
55.0Small, 55.0A list of the transformation overrides for
the model. Valid values are:
AbstractSmartData
## Discovery
## Transformation
## Override[]
transformation
## Overrides
## •
## Smart Data Discovery Projected
## Predictions Override
41.0Small, 41.0The URL for the model.Stringurl
## Smart Data Discovery Multiclass Classification Prediction Property
The multiclass classification prediction model type.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictionProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The classification algorithm type. Valid
values are:
SmartDataDiscovery
## Classification
AlgorithmType
## Enum
algorithmType
## •
Best (Model tournament)
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
## 135
## Smart Data Discovery Multiclass Classification Prediction
## Property
Einstein Discovery REST API Response Bodies

## Smart Data Discovery Multiclass Predict
An Einstein Discovery multiclass predict result.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredict.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0A map of predict probabilities for each
class.
Map<Double,
## Double>
class
## Probabilities
52.0Small, 52.0The predict value.Stringpredicted
## Class
52.0Small, 52.0The type of the predict result.Stringtype
## Smart Data Discovery Narrative Details
The textual narrative data for an Einstein Discovery story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The text for the narrative data.Stringtext
## Smart Data Discovery Narrative Field Collection
A collection of narrative data for an Einstein Discovery story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The live metrics from running predictions.SmartDataDiscovery
NarrativePostBody
postBody
51.0Small, 51.0The list of fields for the narrative.SmartDataDiscovery
NarrativeField[]
results
## Smart Data Discovery Narrative Field
A single row of narrative data for an Einstein Discovery story.
## 136
Smart Data Discovery Multiclass PredictEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The field name for the narrative data.Stringfield
51.0Small, 51.0The interpreted narrative for the condition.SmartDataDiscovery
NarrativeDetails
narrative
51.0Small, 51.0The score for the condition.Doublescore
## Smart Data Discovery Narrative Post Body Filter
A query filter for narrative data of an Einstein Discovery story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The list of columns for filtering the query.String[]columns
52.0Small, 52.0The filter for the query service to use. Valid
data properties are:
AbstractStoryData
## Property
property
## •
## Story All Other Field Value
## •
## Story Day Field Value
## •
## Story Day Field Value
## •
## Story Field Only Value
## •
## Story Month Field Value
## •
## Story Month Of Year Field Value
## •
## Story Null Field Value
## •
## Story Quarter Field Value
## •
## Story Quarter Of Year Field Value
## •
## Story Range Field Value
## •
## Story Text Field Value
## •
## Story Year Field Value
51.0Small, 51.0The list of values to used to filter the query.String[]values
## Smart Data Discovery Narrative Post Body Insight
The narrative insight metadata.
## 137
Smart Data Discovery Narrative Post Body FilterEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The requested insight type. Valid values
are:
ConnectEDInsight
TypeEnum
insightType
## •
## Descriptive
## •
## Summary
51.0Small, 51.0The requested narrative type. Valid values
are:
ConnectEDNarrative
TypeEnum
narrativeType
## •
## Positive
## •
## Negative
51.0Small, 51.0The number of insights returned.IntegernumInsights
## Smart Data Discovery Narrative Post Body Query
A query for narrative data of an Einstein Discovery story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The list of filters for the query.SmartDataDiscovery
NarrativePostBody
## Filter[]
filters
51.0Small, 51.0The insight for the query.SmartDataDiscovery
NarrativePostBody
## Insight
insight
## Smart Data Discovery Narrative Post Body
A single row of narrative data for an Einstein Discovery story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0Indicates whether warnings are detected
in this narrative (true) or not (false).
## Booleaninclude
## Warnings
## 138
Smart Data Discovery Narrative Post Body QueryEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The query parameters passed for the
narrative.
SmartDataDiscovery
NarrativePostBody
## Query
query
51.0Small, 51.0The story for the narrative.AssetReferencestory
51.0Small, 51.0The ID of the story for this narrative.StringstoryId
## Smart Data Discovery Numeric Range
A numeric range for a field.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0The maximum value for the range.Doublemax
57.0Small, 57.0The minimum value for the range.Doublemin
## Smart Data Discovery Numerical Projected Prediction
An Einstein Discovery numerical projected prediction.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPrediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The prediction outcome.Stringprediction
## Smart Data Discovery Predict Column Custom Text
The custom text for a predict column given by the Einstein Discovery prediction.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0A placeholder to the resolved value
defined in the template text. The map is
null if there are no placeholders.
Map<String,
## String>
mapping
## 139
Smart Data Discovery Numeric RangeEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The template text if a custom override is
defined for the column. When the column
StringtemplateText
value should be skipped, this is an empty
string.
## Smart Data Discovery Predict Column
A column given from an Einstein Discovery prediction.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The label of the column.StringcolumnLabel
41.0Small, 41.0The name of the column.StringcolumnName
51.0Small, 51.0The value of the column.StringcolumnValue
50.0Small, 50.0The custom text definition, if it's defined
for the column name.
SmartDataDiscovery
PredictColumn
CustomText
customText
50.0Small, 50.0The input value that created this prediction
column.
StringinputValue
## Smart Data Discovery Predict Condition
An Einstein Discovery predict condition.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
41.0Small, 41.0The list of column information for the
prediction.
SmartDataDiscovery
PredictColumn[]
columns
41.0Small, 41.0The value of the prediction.Doublevalue
## Smart Data Discovery Prediction Definition Collection
A collection of Einstein Discovery prediction definitions.
## 140
Smart Data Discovery Predict ColumnEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The URL to get the next page of results.StringnextPageUrl
41.0Small, 41.0The list of prediction definitions.SmartDataDiscovery
## Prediction
## Definition[]
prediction
## Definitions
41.0Small, 41.0The total count of items in the collection.IntegertotalSize
41.0Small, 41.0The URL to get the collection.Stringurl
## Smart Data Discovery Prediction Definition
An Einstein Discovery prediction definition.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The number of active models currently
present for the prediction model.
IntegercountOfActive
## Models
41.0Small, 41.0The number of all models currently present
for the prediction model.
IntegercountOfModels
41.0Small, 41.0The user who created the prediction
definition.
SmartDataDiscovery
## User
createdBy
41.0Small, 41.0The creation date of the prediction
definition.
DatecreatedDate
41.0Small, 41.0The ID of the prediction definition.Stringid
41.0Small, 41.0The label of the prediction definition.Stringlabel
41.0Small, 41.0The user who last modified the prediction
definition.
SmartDataDiscovery
## User
lastModified
## By
41.0Small, 41.0The last modified date of the prediction
definition.
DatelastModified
## Date
47.0Small, 47.0The mapped outcome field for Salesforce.IntegermappedOutcome
## Field
41.0Small, 41.0The URL for the prediction definition's
models.
StringmodelsUrl
41.0Small, 41.0The developer name of the prediction
definition.
## Stringname
## 141
Smart Data Discovery Prediction DefinitionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The qualified namespace of the prediction
definition.
## Stringnamespace
50.0Supplemental, 50.0The total number of warnings for the
prediction model over the last 90 days.
IntegerninetyDay
WarningCount
46.0Small, 46.0The outcome information of the prediction
definition.
SmartDataDiscovery
PredDefOutcome
## Field
outcome
48.0Small, 48.0The prediction type. Valid values are:SmartDataDiscovery
PredictionType
## Enum
prediction
## Type
## •
## Classification
## •
MulticlassClassification
## •
## Regression
## •
## Unknown
46.0Small, 46.0The pushback of the prediction definition.SmartDataDiscovery
PushbackField
pushbackField
52.0Small, 52.0The pushback type. Valid values are:SmartDataDiscovery
PushbackTypeEnum
pushbackType
## •
AiRecordInsight
## •
## Direct
50.0Small, 50.0The refresh configuration of the prediction
definition.
SmartDataDiscovery
RefreshConfig
refreshConfig
46.0Small, 46.0The status of the prediction definition.
Valid values are:
SmartDataDiscovery
StatusEnum
status
## •
## Disabled
## •
## Enabled
41.0Small, 41.0The entity the prediction definition is
subscribed to.
## Stringsubscribed
## Entity
46.0Small, 46.0The terminal state filter of the prediction
definition.
SmartDataDiscovery
FilterList
terminalState
## Filter
50.0Supplemental, 50.0The total number of predictions for the
prediction definition.
## Integertotal
## Predictions
## Count
50.0Supplemental, 50.0The total number of warnings for the
prediction definition.
IntegertotalWarnings
## Count
41.0Small, 41.0The URL for the prediction definition.Stringurl
## 142
Smart Data Discovery Prediction DefinitionEinstein Discovery REST API Response Bodies

## Smart Data Discovery Prediction Error
An Einstein Discovery prediction error.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPrediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
44.0Small, 44.0The error code.IntegererrorCode
44.0Small, 44.0The error message.Stringmessage
## Smart Data Discovery Prediction
An Einstein Discovery prediction result.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPrediction.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
47.0Small, 47.0The model information of a success
prediction.
AssetReferencemodel
41.0Small, 41.0The raw prediction, including prediction
value, predictive factors, and warnings.
Valid values are:
AbstractSmartData
DiscoveryPredict
prediction
## •
## Smart Data Discovery Multiclass
## Prediction
## •
## Smart Data Discovery Predict Error
## •
## Smart Data Discovery Predict
41.0Small, 41.0The details of how actionable values could
be used to improve the prediction.
SmartDataDiscovery
PredictCondition[]
prescriptions
54.0Small, 54.0The projected predictions for the
prediction, if available.
SmartDataDiscovery
ProjectedPredictions
projected
## Predictions
## Smart Data Discovery Predict Error
An Einstein Discovery predict error result.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredict.
## 143
Smart Data Discovery Prediction ErrorEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
44.0Small, 44.0The error code.IntegererrorCode
44.0Small, 44.0The error message.Stringmessage
## Smart Data Discovery Import Warnings
The import warnings for an Einstein Discovery prediction.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
42.0Small, 42.0A list of mismatched columns for the
predict result.
## String[]mismatched
## Columns
42.0Small, 42.0A list of missing columns for the predict
result.
## String[]missing
## Columns
42.0Small, 42.0A list of out of bounds columns for the
predict result.
SmartDataDiscovery
PredictColumn[]
outOfBounds
## Columns
## Smart Data Discovery Predict Job Collection
A collection of Einstein Discovery predict jobs.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0A list of predict jobs available to the current
user.
SmartDataDiscovery
PredictJob[]
predictJobs
48.0Small, 48.0The total size of the items in the collection.IntegertotalSize
48.0Small, 48.0The URL to get the predict job results.Integerurl
## Smart Data Discovery Predict Job
An Einstein Discovery predict job.
## 144
Smart Data Discovery Import WarningsEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The number of records processed per
batch.
IntegerbatchSize
48.0Small, 48.0The user who created the predict job.SmartDataDiscovery
## User
createdBy
48.0Small, 48.0The creation date of the predict job.DatecreatedDate
49.0Small, 49.0The total number of records that failed to
process.
IntegerfailedRecords
48.0Small, 48.0A list of filters applied to determine
whether a row was scored by the predict
job.
SmartDataDiscovery
## Filter[]
filters
48.0Small, 48.0The ID of the predict job.Stringid
48.0Small, 48.0The label of the predict job.Stringlabel
48.0Small, 48.0The user who last modified the predict job.SmartDataDiscovery
## User
lastModified
## By
48.0Small, 48.0The last modified date of the predict job.DatelastModified
## Date
48.0Small, 48.0The extended message for the status of
the predict job, if available.
## Stringmessage
48.0Small, 48.0The developer name of the predict job.Stringname
48.0Small, 48.0The prediction definition information for
the predict job.
AssetReferenceprediction
## Definition
49.0Small, 49.0The total number of records that
processed, including failures.
## Integerprocessed
## Records
48.0Small, 48.0The status of the predict job. Valid values
are:
SmartDataDiscovery
PredictJobStatus
## Enum
status
## •
## Cancelled
## •
## Completed
## •
## Failed
## •
InProgress
## •
NotStarted
## •
## Paused
48.0Small, 48.0The entity the predict job is subscribed to.Stringsubscribed
## Entity
## 145
Smart Data Discovery Predict JobEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The total number of records that
processed.
IntegertotalRecords
48.0Small, 48.0The URL for the predict job.Stringurl
49.0Small, 49.0Indicates whether the job scored any
record NOT matching the terminal state
filter on the goal (true) or not (false).
BooleanuseTerminal
StateFilter
## Smart Data Discovery Predict List
A list of Einstein Discovery predictions.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0A list of aggregate prediction results. Valid
values are:
AbstractSmartData
DiscoveryAggregate
## Prediction[]
aggregate
## Predictions
## •
SmartDataDiscoveryAggregate
## Prediction
## •
SmartDataDiscoveryAggregate
PredictionError
44.0Small, 44.0The ID of the prediction definition used to
make the prediction.
## Stringprediction
## Definition
55.0Small, 55.0The prediction type. Valid values are:SmartDataDiscovery
PredictionType
## Enum
prediction
## Type
## •
## Classification
## •
MulticlassClassification
## •
## Regression
## •
## Unknown
55.0Small, 55.0A list of predictions. Valid values are:AbstractSmartData
## Discovery
## Prediction[]
predictions
## •
SmartDataDiscoveryPrediction
## •
SmartDataDiscoveryPredictionError
46.0Small, 46.0The settings used for improvements.SmartDataDiscovery
PredictSettings
settings
## Smart Data Discovery Predict Settings
The settings for an Einstein Discovery prediction.
## 146
Smart Data Discovery Predict ListEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The list of the aggregate functions used to
make the prediction.
## String[]aggregate
## Functions
50.0Small, 50.0The maximum middle values. Range is
## [0, 3].
IntegermaxMiddle
## Values
41.0Small, 41.0The maximum prescription count. Range
is [-1,200], where -1 indicates
unlimited.
## Integermax
## Prescriptions
47.0Small, 47.0The impact percentage of prescriptions. If
the value is 0, the default value, then all
## Integerprescription
## Impact
## Percentage
prescriptions are returned. If the value is 5,
then only prescriptions that will improve
the prediction by at least 5% are returned.
54.0Small, 54.0The setting overrides for projected
predictions.
SmartDataDiscovery
ProjectedPrediction
## Settings
settings
## Smart Data Discovery Predict
An Einstein Discovery predict result.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredict.
## Smart Data Discovery Prediction Definition Outcome Field
An Einstein Discovery prediction definition outcome field.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
46.0Small, 46.0The prediction definition outcome goal.
Valid values are:
ConnectSmartData
DiscoveryOutcome
GoalEnum
goal
## •
## Maximize
## •
## Minimize
## •
## None
## 147
Smart Data Discovery PredictEinstein Discovery REST API Response Bodies

## Smart Data Discovery Prescribable Field
An Einstein Discovery prescribable field.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0A list of custom prescribable field
definitions to override default prescription
text.
SmartDataDiscovery
CustomPrescribable
FieldDefinition[]
custom
## Definitions
50.0Small, 50.0A prescribable field. Valid values are:AbstractSmartData
DiscoveryModel
## Field[]
field
## •
SmartDataDiscoveryModelFieldDate
## •
SmartDataDiscoveryModelField
## Numeric
## •
SmartDataDiscoveryModelFieldText
## Smart Data Discovery Projected Prediction Field
An Einstein Discovery projected prediction field.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The projected predictions internal type.
Valid values are:
SmartDataDiscovery
ProjectedPredictions
IntervalTypeEnum
intervalType
## •
## Day
## •
## Month
## •
## Quarter
## •
## Week
54.0Small, 54.0The name of the field.Stringname
54.0Small, 54.0The number of intervals used to produce
the results in projected prediction for all
fields.
IntegernumberOf
## Intervals
54.0Small, 54.0A list of projected values for each interval.SmartDataDiscovery
ProjectedValue[]
projected
## Values
## Smart Data Discovery Projected Prediction Settings
The settings for projected prediction fields.
## 148
Smart Data Discovery Prescribable FieldEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The confidence interval to display at each
point. Allowed values are 80 and 95.
## Integerconfidence
## Interval
41.0Small, 41.0The override value for the number of
intervals to predict ahead. Range is [1,
## 12].
IntegernumberOf
IntervalsTo
PredictAhead
54.0Small, 54.0Indicates whether to enable projected
prediction calculation for every interval
into the future (true) or not (false).
BooleanshowProjected
PredictionsBy
## Interval
## Smart Data Discovery Projected Predictions Count From Date Interval
## Setting
The settings for an Einstein Discovery count from date based projection interval.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPredictionsIntervalSetting.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The date field to use for calculating
projection intervals.
StringdateField
55.0Small, 55.0The label for the date field.StringdateField
## Label
55.0Small, 55.0The number of intervals to project ahead.IntegernumIntervals
## Smart Data Discovery Projected Predictions Count Interval Setting
The settings for an Einstein Discovery count based projection interval.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPredictionsIntervalSetting.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The number of intervals to project ahead.IntegernumIntervals
## 149
## Smart Data Discovery Projected Predictions Count From Date
## Interval Setting
Einstein Discovery REST API Response Bodies

## Smart Data Discovery Projected Predictions Date Interval Setting
The settings for an Einstein Discovery date interval.
## Properties
Inherits properties from AbstractSmartDataDiscoveryProjectedPredictionsIntervalSetting.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The date field to use for calculating
projection intervals.
StringdateField
55.0Small, 55.0The label for the date field.StringdateField
## Label
## Smart Data Discovery Projected Predictions Override
The settings for an Einstein Discovery projected predictions override.
## Properties
Inherits properties from AbstractSmartDataDiscoveryTransformationOverride.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The Salesforce object field name to use as
a look-up for a record ID in a historical
dataset.
StringassetIdField
55.0Small, 55.0The projected predictions interval settings.
Valid values are:
AbstractSmartData
DiscoveryProjected
PredictionsInterval
## Setting
interval
## Override
## •
## Smart Data Discovery Projected
## Predictions Count From Date Interval
## Setting
## •
## Smart Data Discovery Projected
## Predictions Count Interval Setting
## •
## Smart Data Discovery Projected
## Predictions Date Interval Setting
## Smart Data Discovery Projected Predictions
The projected predictions for an Einstein Discovery prediction result.
## 150
## Smart Data Discovery Projected Predictions Date Interval
## Setting
Einstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The field level information for each
projected prediction transformation.
SmartDataDiscovery
ProjectedPrediction
## Field[]
fields
55.0Small, 55.0The setting used for calculating projected
prediction interval. Valid values are:
AbstractSmartData
DiscoveryProjected
PredictionsInterval
## Setting
interval
## Setting
## •
## Smart Data Discovery Projected
## Predictions Count From Date Interval
## Setting
## •
## Smart Data Discovery Projected
## Predictions Count Interval Setting
## •
## Smart Data Discovery Projected
## Predictions Date Interval Setting
54.0Small, 54.0The projected predictions interval type.
Valid values are:
SmartDataDiscovery
ProjectedPredictions
IntervalTypeEnum
intervalType
## •
## Day
## •
## Month
## •
## Quarter
## •
## Week
54.0Small, 54.0The number of intervals used to produce
the results in projected prediction for all
fields.
IntegernumberOf
## Intervals
## Projected
## Ahead
54.0Small, 54.0A list of projected prediction results per
interval. Valid values are:
AbstractSmartData
DiscoveryProjected
## Prediction[]
predictions
## •
## Smart Data Discovery Catagorical
## Projected Prediction
## •
## Smart Data Discovery Numerical
## Projected Prediction
## Smart Data Discovery Projected Value
An Einstein Discovery projected value.
## 151
Smart Data Discovery Projected ValueEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The confidence interval lower bound at
the interval.
## Doubleconfidence
IntervalLower
## Bound
55.0Small, 55.0The confidence interval upper bound at
the interval.
## Doubleconfidence
IntervalUpper
## Bound
54.0Small, 54.0The projected value at the interval.Doublevalue
## Smart Data Discovery Pushback Field
A pushback field for an Einstein Discovery prediction.
## Properties
Inherits properties from SmartDataDiscoveryField.
## Smart Data Discovery Outcome
The analysis outcome for an Einstein Discovery story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The analysis prediction type. Valid values
are:
AnalysisPrediction
TypeEnum
prediction
## Type
## •
## Binary
## •
## Count
## •
MultiClass
## •
## None
## •
## Numeric
44.0Small, 44.0The analysis outcome type. Valid values
are:
AnalysisOutcome
TypeEnum
type
## •
## Categorical
## •
## Count
## •
## Number
## •
## Text
## 152
Smart Data Discovery Pushback FieldEinstein Discovery REST API Response Bodies

## Smart Data Discovery Recipient
An Einstein Discovery recipient.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The display name of the recipient.StringdisplayName
50.0Small, 50.0The ID of the recipient.Stringid
50.0Small, 50.0The type of the recipient. Valid values are:SmartDataDiscovery
RecipientTypeEnum
type
## •
## Group
## •
## User
## Smart Data Discovery Refresh Config
The refresh configuration for an Einstein Discovery prediction.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0Indicates whether scheduled refresh is
enabled (true) or not (false).
BooleanisEnabled
50.0Small, 50.0A list of recipients for email notification.SmartDataDiscovery
## Recipient[]
recipientList
50.0Small, 50.0The schedule for the refresh job.Scheduleschedule
50.0Small, 50.0Indicates whether to automatically rescore
records after a successful refresh (true)
or not (false).
BooleanshouldScore
AfterRefresh
50.0Small, 50.0The user context for the refresh job.SmartDataDiscovery
## User
userContext
50.0Small, 50.0The refresh warning threshold percentage
for auto model deploy.
## Doublewarning
## Threshold
## Percentage
## Smart Data Discovery Refresh Job Collection
A collection of Einstein Discovery refresh jobs.
## 153
Smart Data Discovery RecipientEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The list of refresh jobs available to the
current user.
SmartDataDiscovery
RefreshJob[]
refreshJobs
50.0Small, 50.0The total count of items in the collection.IntegertotalSize
50.0Small, 50.0The URL to get the collection.Stringurl
## Smart Data Discovery Refresh Job
An Einstein Discovery refresh job.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The user who created the refresh job.SmartDataDiscovery
## User
createdBy
50.0Small, 50.0The creation date of the refresh job.DatecreatedDate
50.0Small, 50.0The end time of the refresh job.DateendTime
50.0Small, 50.0The ID of the refresh job.Stringid
50.0Small, 50.0The extended message for the status of
the refresh job, if available.
## Stringmessage
50.0Small, 50.0The refresh target for the refresh job.AssetReferencerefreshTarget
50.0Small, 50.0The URL to the refresh tasks collection for
the refresh job.
StringrefreshTasks
## Url
50.0Small, 50.0The start time of the refresh job.DatestartTime
50.0Small, 50.0The status of the refresh job. Valid values
are:
SmartDataDiscovery
RefreshJobStatus
## Enum
status
## •
## Cancelled
## •
CompletedWithWarnings
## •
## Failure
## •
NoRunnableTask
## •
NotStarted
## •
## Running
## •
ScoringJobFailed
## •
## Success
## •
UserNotFound
## 154
Smart Data Discovery Refresh JobEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The type of the refresh job. Valid values
are:
SmartDataDiscovery
RefreshJobType
## Enum
type
## •
## Scheduled
## •
UserTriggered
48.0Small, 48.0The URL for the predict job.Stringurl
## Smart Data Discovery Refresh Task Collection
A collection of Einstein Discovery refresh task.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The list of refresh task available to the
current user.
SmartDataDiscovery
RefreshTask[]
refreshTasks
50.0Small, 50.0The total count of items in the collection.IntegertotalSize
50.0Small, 50.0The URL to get the collection.Stringurl
## Smart Data Discovery Refresh Task Source
The source for an Einstein Discovery refresh task.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The specific dataset version used for this
refresh.
AssetReferencedataset
## Version
50.0Small, 50.0The specific story used for this refresh.AssetReferencestory
50.0Small, 50.0The specific story version used for this
refresh.
AssetReferencestoryVersion
## Smart Data Discovery Refresh Task
An Einstein Discovery refresh task.
## 155
Smart Data Discovery Refresh Task CollectionEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The user who created the refresh task.SmartDataDiscovery
## User
createdBy
50.0Small, 50.0The creation date of the refresh task.DatecreatedDate
50.0Small, 50.0The end time of the refresh task.DateendTime
50.0Small, 50.0The ID of the refresh task.Stringid
50.0Small, 50.0The extended message for the status of
the refresh task, if available.
## Stringmessage
50.0Small, 50.0The refresh target for the refresh task.AssetReferencerefreshTarget
50.0Small, 50.0The refreshed AI model.AssetReferencerefreshedAI
## Model
50.0Small, 50.0The input source used for the refresh task.SmartDataDiscovery
RefreshTaskSource
source
50.0Small, 50.0The start time of the refresh job.DatestartTime
50.0Small, 50.0The status of the refresh task. Valid values
are:
SmartDataDiscovery
RefreshTaskStatus
## Enum
status
## •
AnalysisNotFound
## •
## Cancelled
## •
DatasetJoinFieldsMissing
## •
DatasetNotFound
## •
DatasetNotUpdated
## •
## Failure
## •
LimitsReached
## •
ModelSchemaChanged
## •
NotStarted
## •
OutcomeValuesChanged
## •
PoissonDistribution
## Disabled
## •
## Running
## •
StoryCreationFailure
## •
## Success
## •
UserNotFound
## •
WarningThresholdReached
48.0Small, 48.0The URL for the predict job.Stringurl
## 156
Smart Data Discovery Refresh TaskEinstein Discovery REST API Response Bodies

## Smart Data Discovery Regression Classification Prediction Property
The regression classification prediction model type.
## Properties
Inherits properties from AbstractSmartDataDiscoveryPredictionProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The regression algorithm type. Valid values
are:
SmartDataDiscovery
## Regression
AlgorithmType
## Enum
algorithmType
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
48.0Small, 48.0The classification threshold (e.g. binary
classification threshold for logistic
regression models).
BinaryClassification
## Threshold
classification
## Threshold
## Smart Data Discovery Training Metrics
A collection of Einstein Discovery metrics from training a model.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The mean absolute error (mae) training
metric.
## Doublemae
50.0Small, 50.0The number of rows this model was
trained on.
IntegerrowCount
50.0Small, 50.0The complex value of this training metric
represented as a Map.
Map<Object,
## Object>
value
## Smart Data Discovery User
An Einstein Discovery user.
## 157
## Smart Data Discovery Regression Classification Prediction
## Property
Einstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
41.0Small, 41.0The ID of the user.Stringid
41.0Small, 41.0The name of the user.Stringname
41.0Small, 41.0The Chatter profile photo of the user.StringprofilePhoto
## Url
## Story Diagnostic Insights Detail
The detail for story diagnostic insights.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
53.0Small, 53.0The insights result category. Valid values
are:
InsightsResult
CategoryEnum
category
## •
## Negative
## •
## Positive
53.0Small, 53.0The insights condition restriction. Valid
values are:
InsightsCondition
RestrictionEnum
condition
## Restriction
## •
## Included
## •
NotIncluded
53.0Small, 53.0A list of the case details for a diagnostic
insight.
DiagnosticInsights
## Case[]
details
53.0Small, 53.0The descriptive insights impact for the
story. Valid values are:
StoryDescriptive
InsightsImpact
## Enum
impact
## •
## Improved
## •
## Worsened
## Story All Other Field Value
The story data property for all other values in a field.
## Properties
Inherits properties from AbstractStoryDataProperty.
## 158
Story Diagnostic Insights DetailEinstein Discovery REST API Response Bodies

## Story Chart Value
A value in a story chart.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0A list of the story chart value class specific
details.
StoryChartValue
## Detail[]
classDetails
54.0Small, 54.0A list of the story chart value details.StoryChartValue
## Detail[]
details
54.0Small, 54.0A list of the story chart value dimensions.StoryFieldLabel
ValueProperty[]
dimensions
54.0Small, 54.0The story chart value type. Valid values are:StoryChartValue
TypeEnum
type
## •
## Average
## •
## Baseline
## •
## Impact
## •
## Prediction
## •
SmallTerms
## •
## Unexplained
## •
## Value
54.0Small, 54.0The value of the story chart.Doublevalue
## Story Chart Value Detail
The detail for a value in a story chart.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The count of all others.DoubleallOthers
## Count
54.0Small, 54.0The ratio of the all others count.DoubleallOthers
CountRatio
54.0Small, 54.0The average of the value.Doubleaverage
54.0Small, 54.0The base coefficient of the value.Doublebase
## Coefficient
## 159
Story Chart ValueEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The range of the bucket during story
version comparison.
StringbucketRange
54.0Small, 54.0The change from average for the value.DoublechangeFrom
## Average
54.0Small, 54.0The change from average for other buckets
for the value.
DoublechangeFrom
AverageFor
OtherBuckets
54.0Small, 54.0The change from expected for the value.DoublechangeFrom
## Expected
54.0Small, 54.0The change from overall for the value.DoublechangeFrom
## Overall
54.0Small, 54.0The change from usual for the value.DoublechangeFrom
## Usual
54.0Small, 54.0The coefficient for the value.Doublecoefficient
54.0Small, 54.0The impact of combined terms for the
value.
## Doublecombined
## Impact
54.0Small, 54.0The conditional frequency for the value.Doubleconditional
## Frequency
54.0Small, 54.0The frequency for the value.Doublefrequency
54.0Small, 54.0The global count for the value.DoubleglobalCount
54.0Small, 54.0The global mean for the value.DoubleglobalMean
54.0Small, 54.0The impact for the value.Doubleimpact
54.0Small, 54.0Indicates whether the value is a reference
group (true) or not (false).
BooleanisReference
## Group
54.0Small, 54.0Indicates whether the value is significantly
different (true) or not (false).
## Booleanis
## Significantly
## Different
54.0Small, 54.0The left frequency for the value.DoubleleftFrequency
54.0Small, 54.0The left impact for the value.DoubleleftImpact
54.0Small, 54.0The order for the value.Integerorder
54.0Small, 54.0The precluded count for the value.Integerprecluded
## Count
54.0Small, 54.0The precluded sum for the value.DoubleprecludedSum
55.0Small, 55.0The ratio difference for the value.Doubleratio
## Difference
## 160
Story Chart Value DetailEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The right frequency for the value.Doubleright
## Frequency
54.0Small, 54.0The right impact for the value.DoublerightImpact
54.0Small, 54.0The row count for the value.LongrowCount
54.0Small, 54.0The row count ratio for the value.DoublerowCountRatio
54.0Small, 54.0The standard deviation for the value.Doublestandard
## Deviation
54.0Small, 54.0The number of combined terms for the
value.
IntegertermsCombined
54.0Small, 54.0The total for the value.Doubletotal
## Story Chart
A story chart.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The category label for the story chart.StringcategoryLabel
54.0Small, 54.0The metric label for the story chart.StringmetricLabel
54.0Small, 54.0A list of the story chart values.StoryChartValue[]values
## Story Collection
A collection of Einstein Discovery stories.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
48.0Small, 48.0The URL to get the next page of items for
the collection.
IntegernextPageUrl
48.0Small, 48.0A list of stories available to the current user.Story[]stories
48.0Small, 48.0The total size of the items in the collection.IntegertotalSize
48.0Small, 48.0The URL to get the predict job results.Integerurl
## 161
Story ChartEinstein Discovery REST API Response Bodies

## Story Count Insights Case
A count story insights case.
## Properties
Inherits properties from AbstractStoryInsightsCase.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The count for the insights caseDoublecount
54.0Small, 54.0The count change from for the insights
case
DoublecountChange
## From
52.0Small, 52.0The summary statistics frequency value for
the insights case
## Doublefrequency
52.0Small, 52.0The impact due to changed summary
value. Valid values are:
StoryCountInsights
FrequencyChange
## Enum
frequency
## Change
## •
## Down
## •
## Up
52.0Small, 52.0The change in the summary statistics value
for the insights case
## Doublefrequency
ChangeFrom
52.0Small, 52.0The occurrence frequency rate for the
insights case. Valid values are:
StoryCountInsights
FrequencyEnum
frequencyRate
## •
LessOften
## •
MoreOften
52.0Small, 52.0The score of the field value for the insights
case
## Doublemultiplier
54.0Small, 54.0The sum value for the insights caseDoublesum
54.0Small, 54.0The sum change from value for the insights
case
DoublesumChangeFrom
## Story Day Field Value
The story data day property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The day in numeric value.Integerday
## 162
Story Count Insights CaseEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0Indicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0Small, 52.0The month in numeric value.Integermonth
52.0Small, 52.0The raw value of the field.StringrawValue
52.0Small, 52.0The year in numeric value.Integeryear
Story Day of Week Field Value
The story data day of week property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The day of week in numeric value.IntegerdayOfWeek
52.0Small, 52.0The raw value of the field.StringrawValue
## Story Descriptive Insights Case
A descriptive story insights case.
## Properties
Inherits properties from AbstractStoryInsightsCase.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The changed value for the insights caseDoublechange
52.0Small, 52.0The impact on the result. Valid values are:StoryDescriptive
InsightsImpact
## Enum
frequency
## Change
## •
## Improved
## •
## Worsened
52.0Small, 52.0A list of field values that impact the result.StoryFieldImpact
## Detail[]
impactDetails
54.0Small, 54.0The mean value for the insights caseDoublemean
52.0Small, 52.0The score rating of the average outcome.
Valid values are:
StoryDescriptive
InsightsRatingEnum
rating
## •
AboveAverage
## 163
Story Day of Week Field ValueEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
BelowAverage
## •
## Higher
## •
## Lower
## Story Details
The details for a story. These details are the top positive and negative factors contributing to story outcome.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The field value combination that
contributed to the outcome result.
StoryField[]condition
51.0Small, 51.0The count of the condition records.Longcount
51.0Small, 51.0The difference between the mean and the
global average for analysis with outcome.
DoublediffFrom
## Average
51.0Small, 51.0The difference between the mean and the
global average for count analysis.
DoublediffFrom
## Expected
51.0Small, 51.0The difference between the mean with
constraing and without constraint for
count analysis.
DoublediffFromUsual
51.0Small, 51.0The percentage value.Doublepercentage
51.0Small, 51.0The occurrence count.DoublerateOf
## Occurrence
51.0Small, 51.0The score of the condition field.Doublescore
## Story Field Correlation
The summary of each field in the dataset selected for story creation.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The field correlation to outcome value.DoublecorrelationTo
## Outcome
51.0Small, 51.0The label for the dataset field.StringfieldLabel
## 164
Story DetailsEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The name for the dataset field.StringfieldName
## Story Field Impact Detail
A story field impact details.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0A details of the field impacting the story
result.
StoryFieldLabel
ValueProperty
impactField
## Story Field Label Value Property
A story field.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The label for the story field.Stringlabel
52.0Small, 52.0The data property of the story field. Valid
values are:
AbstractStoryData
## Property
property
## •
## Story Day Field Value
## •
## Story Day Of Week Field Value
## •
## Story Field Only
## •
## Story Month Field Value
## •
## Story Month Of Year Field Value
## •
## Story Null Field Value
## •
## Story Quarter Field Value
## •
## Story Quarter Of Year Field Value
## •
## Story Range Field Value
## •
## Story Text Field Value
## •
## Story Year Field Value
52.0Small, 52.0The value for the story field.Stringvalue
## 165
Story Field Impact DetailEinstein Discovery REST API Response Bodies

## Story Field Only
The story data field property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Story Field
The field value combination that contributed to the story outcome result.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The name for the story field.StringfieldName
52.0Small, 52.0The field property. Valid values are:AbstractStoryData
## Property
property
## •
## Story All Other Field Value
## •
## Story Day Field Value
## •
## Story Day Of Week Field Value
## •
## Story Field Only
## •
## Story Month Field Value
## •
## Story Month Of Year Field Value
## •
## Story Null Field Value
## •
## Story Quarter Field Value
## •
## Story Quarter Of Year Field Value
## •
## Story Range Field Value
## •
## Story Text Field Value
## •
## Story Year Field Value
54.0Small, 54.0The field type. Valid values are:StoryFieldDetailType
## Enum
type
## •
## Field
## •
## Outcome
51.0Small, 51.0The value for the field.Stringvalue
## Story First Order Insights
The first order insights for a story.
## Properties
Inherits properties from AbstractStoryInsights.
## 166
Story Field OnlyEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The correlation value with respect to the
outcome variable.
## Doublecorrelation
54.0Small, 54.0The disparate impact results for a story
query.
StoryQueryDisparate
## Impact
storyHistory
54.0Small, 54.0A list of the potential bias results for a story
query.
StoryPotentialBias[]potentialBias
54.0Small, 54.0Indicates whether the insight is
significantly different (true) or not
## (false).
## Booleansignificantly
## Different
## Story Insights Detail
The insights detail for a story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0A list of story insights cases. Valid values
are:
AbstractStory
InsightsCase[]
cases
## •
StoryDescriptiveInsightsCase
## •
StoryCountInsightsCase
52.0Small, 52.0The insights result category. Valid values
are:
InsightsResult
CategoryEnum
category
## •
## Negative
## •
## Positive
52.0Small, 52.0The insights score comparison criteria.
Valid values are:
InsightsComparison
## Enum
comparedWith
## •
## Average
## •
## Other
## •
UniformDistribution
55.0Small, 55.0Indicates whether there are more cases
(true) or not (false).
BooleanhasMoreCases
55.0Small, 55.0The outcome class for the story insight.StringoutcomeClass
## 167
Story Insights DetailEinstein Discovery REST API Response Bodies

## Story Month Field Value
The story data month property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0Indicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0Small, 52.0The month in numeric value.Integermonth
52.0Small, 52.0The raw value of the field.StringrawValue
52.0Small, 52.0The year in numeric value.Integeryear
Story Month of Year Field Value
The story data month of year property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The month of year in numeric value.Integermonth
52.0Small, 52.0The raw value of the field.StringrawValue
## Story Narrative Element Text
The text element for a story narrative.
## Properties
Inherits properties from AbstractStoryNarrativeElement.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The narrative text with data properties.
Valid values are:
AbstractStoryData
## Property
condition
## Field
## •
## Story All Other Field Value
## •
## Story Day Field Value
## •
## Story Day Of Week Field Value
## 168
Story Month Field ValueEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
## Story Field Only
## •
## Story Month Field Value
## •
## Story Month Of Year Field Value
## •
## Story Null Field Value
## •
## Story Quarter Field Value
## •
## Story Quarter Of Year Field Value
## •
## Story Range Field Value
## •
## Story Text Field Value
## •
## Story Year Field Value
54.0Small, 54.0The value for the narrative text.Stringvalue
## Story Narrative
A narrative for a story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The body of the narrative. Valid values are:AbstractStory
NarrativeElement
body
## •
StoryNarrativeElementText
54.0Small, 54.0The body of the narrative. Valid values are:AbstractStory
NarrativeElement
header
## •
StoryNarrativeElementText
54.0Small, 54.0The body of the narrative. Valid values are:AbstractStory
NarrativeElement
title
## •
StoryNarrativeElementText
## Story Null Field Value
The story data null property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Story Potential Bias
The potential bias for a story.
## 169
Story NarrativeEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The details for the bias field.StoryFieldLabel
ValueProperty
biasField
54.0Small, 54.0The variation for the bias field.DoublebiasField
## Variation
54.0Small, 54.0The combined variation for the bias field
and the filter field.
## Doublecombined
## Variation
54.0Small, 54.0The variation for the filter field.DoublefilterField
## Variation
54.0Small, 54.0The similarity between the bias field and
the filter field.
## Doublesimilarity
## Story Quarter Field Value
The story data quarter property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0Indicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0Small, 52.0The quarter in numeric value.Integerquarter
52.0Small, 52.0The raw value of the field.StringrawValue
52.0Small, 52.0The year in numeric value.Integeryear
Story Quarter of Year Field Value
The story data quarter of year property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## 170
Story Quarter Field ValueEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0Indicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0Small, 52.0The quarter in numeric value.Integerquarter
52.0Small, 52.0The raw value of the field.StringrawValue
## Story Query Diagnostic Insights
A story query diagnostic insights.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
53.0Small, 53.0The change in outcome because of
selected condition.
DoublechangeIn
## Outcome
54.0Small, 54.0The chart for the diagnostic insight.StoryChartchart
53.0Small, 53.0The condition selected for the diagnostic
insight.
StoryFieldLabel
ValueProperty
condition
## Field
53.0Small, 53.0A list of diagnostic insight records.StoryDiagnostic
InsightsDetail[]
details
54.0Small, 54.0The disparate impact details for the
diagnostic insight.
StoryQueryDisparate
## Impact
details
54.0Small, 54.0The disparate impact details for the
diagnostic insight.
StoryNarrativenarrative
55.0Small, 55.0The outcome class for the diagnostic
insight.
StringoutcomeClass
53.0Small, 53.0The outcome field for the diagnostic
insight.
SmartDataDiscovery
## Outcome
outcomeField
54.0Small, 54.0The potential bias details for the diagnostic
insight.
StoryPotentialBiaspotentialBias
## Story Query Disparate Impact Detail
The detail for a story query disparate impact.
## 171
Story Query Diagnostic InsightsEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The adverse ratio value for a disparate
impact.
DoubleadverseRatio
54.0Small, 54.0The field value with adverse ratio.Stringvalue
## Story Query Disparate Impact
A disparate impact for a story query.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0A list of details for the disparate impact.StoryQueryDisparate
ImpactDetail[]
details
54.0Small, 54.0The reference field value used to calculate
the disparate impact.
## Stringreference
## Value
## Story Query Input Parameter
The input parameter for a story query.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0A list of filter fields used to query insights.
Valid values are:
AbstractStoryData
PropertyInput[]
filters
## •
## Story Day Field Value Input
## •
## Story Day Of Week Field Value Input
## •
## Story Field Only Input
## •
## Story Month Field Value Input
## •
## Story Month Of Year Field Value Input
## •
## Story Null Field Value Input
## •
## Story Quarter Field Value Input
## •
## Story Quarter Of Year Field Value Input
## •
## Story Range Field Value Input
## •
## Story Text Field Value Input
## 172
Story Query Disparate ImpactEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
## Story Year Field Value Input
52.0Small, 52.0The insights type. Valid values are:InsightsTypeEnuminsightsType
## •
## Descriptive
## •
## Diagnostic
## Story Query
A query for story insights.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0A list of descriptive story insights. Valid
values are:
AbstractStory
## Insights[]
descriptive
## Insights
## •
StoryFirstOrderInsights
## •
StorySecondOrderInsights
53.0Small, 53.0A list of diagnostic story insights.StoryQuery
DiagnosticInsights[]
diagnostic
## Insights
54.0Small, 54.0Indicates whether to include the story
chart in the query response (true) or not
## (false).
BooleanincludeChart
54.0Small, 54.0Indicates whether to include the story
narrative in the query response (true) or
not (false).
## Booleaninclude
## Narrative
54.0Small, 54.0Indicates whether to include regular fields
in the query response (true) or not
## (false).
## Booleaninclude
RegularFields
54.0Small, 54.0Indicates whether to include sensitive
fields in the query response (true) or not
## (false).
## Booleaninclude
## Sensitive
## Fields
54.0Small, 54.0The total number of insight cards in the
query response.
## Integerlimit
54.0Small, 54.0The insight card offset value.Integeroffset
52.0Small, 52.0The story query input parameters.StoryQueryInput
## Parameter
query
52.0Small, 52.0The total insight count for the story.IntegertotalSize
## 173
Story QueryEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The URL for the story query.Stringurl
## Story Range Field Value
The story data range property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The end value of the range.StringendValue
52.0Small, 52.0The start value of the range.StringstartValue
## Story Second Order Insights
The second order insights for a story.
## Properties
Inherits properties from AbstractStoryInsights.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The condition field used for second order
analysis.
StoryFieldLabel
ValueProperty
condition
## Field
## Story Summary Detail
The summary detail for a story.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The statistical mean for outcome variable.Doubleaverage
## Outcome
51.0Small, 51.0A summary of each field in the dataset
selected for story creation.
StoryField
## Correlation[]
correlations
## 174
Story Range Field ValueEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0A list of importance metrics for the AI
model.
ModelFieldLabel
## Metrics[]
feature
## Importances
51.0Small, 51.0A list of the top negative factors
contributing to the outcome.
StoryDetails[]negative
## Factors
51.0Small, 51.0A list of the top positive factors
contributing to the outcome.
StoryDetails[]positive
## Factors
51.0Small, 51.0The total number of rows in the dataset.LongrowCount
51.0Small, 51.0The URL for the story summary detail.Stringurl
## Story Text Field Value
The story data text property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The text value of the field.Stringvalue
## Story Version Reference
The basic information for an Einstein Discovery story version.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The creation date of the story version.DatecreatedDate
51.0Small, 51.0The ID of the story version.Stringid
51.0Small, 51.0The URL for the story version.Stringurl
## Story Version
An Einstein Discovery story version.
## 175
Story Text Field ValueEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
53.0Small, 53.0The URL for the alerts for this story version.StringalertsUrl
47.0Small, 47.0The threshold for classification. Valid values
are:
## Abstract
## Classification
## Threshold
classification
## Threshold
## •
## Binary Classification Threshold
44.0Small, 44.0The user who created this story version.SmartDataDiscovery
## User
createdBy
44.0Small, 44.0The creation date of the story version.DatecreatedDate
50.0Small, 50.0The description of the story version.Stringdescription
44.0Small, 44.0The error code for the story version, if any.IntegererrorCode
47.0Small, 47.0A list of field configurations. Valid values
are:
AbstractField
## Configuration[]
fields
## •
AbstractDateFieldConfiguration
## •
AbstractNumericFieldConfiguration
## •
AbstractTextFieldConfiguration
44.0Small, 44.0The folder that the story version belongs
to.
AssetReferencefolder
51.0Small, 51.0The ID of the story version.Stringid
45.0Small, 45.0The source for the story version. Valid
values are:
AbstractStorySourceinput
## •
AnalyticsDatasetSource
## •
ReportSource
46.0Small, 46.0The statistical summary of the input data.AssetReferenceinputProfile
44.0Small, 44.0A list of insights associated with this story
version.
SmartDataDiscovery
## Insights[]
insights
44.0Small, 44.0The label for the story version.Stringlabel
44.0Small, 44.0The user who last modified this story
version.
SmartDataDiscovery
## User
lastModified
## By
44.0Small, 44.0The last modified date of the story version.DatelastModified
## Date
44.0Small, 44.0The error message for the story version, if
any.
## Stringmessage
## 176
Story VersionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The model configuration for the story
version.
SmartDataDiscovery
ModelConfiguration
model
## Configuration
44.0Small, 44.0The field on which analysis is performed
and its attributes.
SmartDataDiscovery
## Outcome
outcome
44.0Small, 44.0The parent of the story version, when it is
created from an existing story.
AssetReferenceparent
57.0Small, 57.0The number of rows processed in building
the analysis.
IntegerprocessedRow
## Count
57.0Small, 57.0The sampling strategy associated with the
story version. Valid values are:
AnalysisSampling
StrategyEnum
sampling
## Strategy
## •
## Discovery
## •
## None
## •
## Random
44.0Big, 44.0A map of the JSON containing information
about the setup menu, names, action
Map<Object,
## Object>
setup
variables, model settings, variables, and
outcomes.
44.0Small, 44.0The current status of the analysis. Valid
values are:
AnalysisSetupStatus
## Enum
status
## •
## Autopilot
## •
DoneDescriptive
## •
DoneFeatureEngineering
## •
DoneModelMetrics
## •
DonePredictive
## •
## Draft
## •
## Failed
## •
## Fetching
## •
GenerateSetup
## •
InProgress
## •
## Postprocessing
## •
## Preprocessing
## •
## Queued
## •
QueuedForFetching
## •
QueuedForPostprocessing
## •
RequestToDelete
## •
## Resizing
## •
RetryPreprocessing
## 177
Story VersionEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
## •
RunningDescriptive
## •
RunningFeature
## Engineering
## •
RunningModelMetrics
## •
RunningPredictive
## •
## Success
## •
TimedOut
55.0Small, 55.0A list of field transformation. Valid values
in the list are:
AbstractSmartData
## Discovery
## Transformation
## Input[]
transformations
## •
## Smart Data Discovery Categorical
## Imputation Transformation Input
## •
## Smart Data Discovery Extract Day Of
## Week Transformation Input
## •
## Smart Data Discovery Extract Month
## Of Year Transformation Input
## •
## Smart Data Discovery Free Text
## Clustering Transformation Input
## •
## Smart Data Discovery Numerical
## Imputation Transformation Input
## •
## Smart Data Discovery Projected
## Predictions Transformation Input
## •
## Smart Data Discovery Sentiment
## Analysis Transformation Input
51.0Small, 51.0The URL for the story version.Stringurl
57.0Small, 57.0The validation configuration for the story.
Valid values are:
AbstractSmartData
DiscoveryValidation
## Configuration
validation
## Configuration
## •
## Validation Dataset
## •
## Validation Ratio
53.0Small, 53.0The analysis source for the validation
dataset. Valid values are:
AbstractStorySourcevalidation
## Input
## •
AnalyticsDatasetSource
## •
ReportSource
## Story
An Einstein Discovery story.
## 178
StoryEinstein Discovery REST API Response Bodies

## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The autopilot settings for the story.Autopilotautopilot
48.0Small, 48.0The threshold for classification predictions
for the story. Valid values are:
## Abstract
## Classification
## Threshold
classification
## Threshold
## •
BinaryClassificationThreshold
48.0Small, 48.0The user who created the prediction
definition.
SmartDataDiscovery
## User
createdBy
48.0Small, 48.0The creation date of the prediction
definition.
DatecreatedDate
48.0Small, 48.0The diagnostic error code for the story.IntegererrorCode
54.0Small, 54.0A list of field configurations for the story.
Valid values are:
AbstractField
## Configuration
fields
## •
DateFieldConfiguration
## •
NumericFieldConfiguration
## •
TextFieldConfiguration
48.0Small, 48.0The analytics folder the story belongs to.AssetReferencefolder
48.0Small, 48.0The URL for the story's history items.StringhistoriesUrl
48.0Small, 48.0The ID of the story.Stringid
48.0Small, 48.0The input data for the story. Valid values
are:
AbstractStorySourceinput
## •
AnalyticsDatasetSource
## •
ReportSource
48.0Small, 48.0The statistical summary of the input data.AssetReferenceinputProfile
48.0Small, 48.0The label of the story.Stringlabel
48.0Small, 48.0The user who last modified the story.SmartDataDiscovery
## User
lastModified
## By
48.0Small, 48.0The last modified date of the story.DatelastModified
## Date
51.0Small, 51.0The mapped outcome field for Salesforce.StoryVersion
## Reference
last
## Successful
## Version
48.0Small, 48.0The informational message related to the
story generation.
## Stringmessage
## 179
StoryEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The model configuration for the story.SmartDataDiscovery
ModelConfiguration
models
## Configuration
53.0Small, 53.0The developer name of the story.Stringname
53.0Small, 53.0The qualified namespace of the story.Stringnamespace
48.0Small, 48.0The selected outcome of the generated
story.
SmartDataDiscovery
## Outcome
outcome
48.0Small, 48.0The run ID for fetching the story insights.IDrunId
46.0Big, 46.0A map of the setup information for the
story, including names, action variables,
model settings, variables, and outcomes.
Map<Object,
## Object>
setup
46.0Small, 46.0The current status of the story. Valid values
are:
AnalysisSetupStatus
## Enum
status
## •
## Autopilot
## •
DoneDescriptive
## •
DoneFeatureEngineering
## •
DoneModelMetrics
## •
DonePredictive
## •
## Draft
## •
## Failed
## •
## Fetching
## •
GenerateSetup
## •
InProgress
## •
## Postprocessing
## •
## Preprocessing
## •
## Queued
## •
QueuedForFetching
## •
QueuedForPostprocessing
## •
RequestToDelete
## •
## Resizing
## •
RetryPreprocessing
## •
RunningDescriptive
## •
RunningFeature
## Engineering
## •
RunningModelMetrics
## •
RunningPredictive
## •
## Success
## •
TimedOut
## 180
StoryEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0A list of field transformation. Valid values
in the list are:
AbstractSmartData
## Discovery
## Transformation
## Input[]
transformations
## •
## Smart Data Discovery Categorical
## Imputation Transformation Input
## •
## Smart Data Discovery Extract Day Of
## Week Transformation Input
## •
## Smart Data Discovery Extract Month
## Of Year Transformation Input
## •
## Smart Data Discovery Free Text
## Clustering Transformation Input
## •
## Smart Data Discovery Numerical
## Imputation Transformation Input
## •
## Smart Data Discovery Projected
## Predictions Transformation Input
## •
## Smart Data Discovery Sentiment
## Analysis Transformation Input
48.0Small, 48.0The URL for the story.Stringurl
57.0Small, 57.0The validation configuration for the story.
Valid values are:
AbstractSmartData
DiscoveryValidation
## Configuration
validation
## Configuration
## •
## Validation Dataset
## •
## Validation Ratio
## Story Year Field Value
The story data year property.
## Properties
Inherits properties from AbstractStoryDataProperty.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0Indicates whether the value is in a fiscal
year (true) or not (false).
## Booleanfiscal
52.0Small, 52.0The raw value of the field.StringrawValue
52.0Small, 52.0The year in numeric value.Integeryear
## 181
Story Year Field ValueEinstein Discovery REST API Response Bodies

## Text Field Configuration
The text field configuration.
## Properties
Inherits properties from AbstractTextFieldConfiguration.
## Text Field Value Configuration
The text field value configuration.
## Properties
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0Indicates whether the field value is ignored
(true) or not (false).
## Booleanignored
54.0Small, 54.0The label of the field value.Stringlabel
54.0Small, 54.0The name of the field value.Stringname
## Validation Dataset
The output for a validation dataset configuration.
## Properties
Inherits properties from AbstractSmartDataDiscoveryValidationConfiguration.
## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0The source of the validation dataset
configuration. Valid values are:
AbstractStorySourceinput
## •
AnalyticsDatasetSource
## •
ReportSource
## Validation Ratio
The output for a validation ratio configuration.
## Properties
Inherits properties from AbstractSmartDataDiscoveryValidationConfiguration.
## 182
Text Field ConfigurationEinstein Discovery REST API Response Bodies

## Available
## Version
Filter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0The value of the validation ratio.Integervalidation
## Ratio
## 183
Validation RatioEinstein Discovery REST API Response Bodies

## EINSTEIN DISCOVERY REST API ENUMS
Enums specific to the /smartdatadiscovery namespace
Enums are not versioned. Enum Values are returned in all API versions. Clients should handle values they don't understand gracefully.
DescriptionEnum
The analysis outcome type. Valid values are:AnalysisOutcomeTypeEnum
## •
## Categorical
## •
## Count
## •
## Number
## •
## Text
The analysis prediction type. Valid values are:AnalysisPredictionTypeEnum
## •
## Binary
## •
## Count
## •
MultiClass
## •
## None
## •
## Numeric
The sampling strategy associated with the story version. Valid values are:AnalysisSamplingStrategyEnum
## •
## Discovery
## •
## None
## •
## Random
The type of scope. Valid values are:AnalysisSetupScopeTypeEnum
## •
CreatedByMe
## •
SharedWithMe
The type of source. Valid values are:AnalysisSetupSourceTypeEnum
## •
AnalyticsDataset
## •
LiveDataset
## •
## Report
The state of analysis performed by an Einstein Discovery service. Valid values are:AnalysisSetupStatusEnum
## •
## Autopilot
## •
DoneDescriptive
## •
DoneFeatureEngineering
## •
DoneModelMetrics
## •
DonePredictive
## 184

DescriptionEnum
## •
## Draft
## •
## Failed
## •
## Fetching
## •
GenerateSetup
## •
InProgress
## •
## Postprocessing
## •
## Preprocessing
## •
## Queued
## •
QueuedForFetching
## •
QueuedForPostprocessing
## •
RequestToDelete
## •
## Resizing
## •
RetryPreprocessing
## •
RunningDescriptive
## •
RunningFeatureEngineering
## •
RunningModelMetrics
## •
RunningPredictive
## •
## Success
## •
TimedOut
The type of classification. Valid values are:ClassificationTypeEnum
## •
## Binary
The insight type to return. Valid values are:ConnectEDInsightTypeEnum
## •
## Descriptive
## •
## Summary
The narrative type to return. Valid values are:ConnectEDNarrativeTypeEnum
## •
## Positive
## •
## Negative
The operator to apply to this filter. Valid values are:ConnectSmartDataDiscoveryFilter
OperatorEnum
## •
## Between
## •
## Contains
## •
EndsWith
## •
## Equal
## •
GreaterThan
## •
GreaterThanOrEqual
## •
InSet
## 185
Einstein Discovery REST API Enums

DescriptionEnum
## •
LessThan
## •
LessThanOrEqual
## •
NotBetween
## •
NotEqual
## •
NotIn
## •
StartsWith
The outcome goal to filter the collection by. Valid values are:ConnectSmartDataDiscovery
OutcomeGoalEnum
## •
## Maximize
## •
## Minimize
## •
## None
The insights score comparison criteria. Valid values are:InsightsComparisonEnum
## •
## Average
## •
## Other
## •
UniformDistribution
The insights condition restriction. Valid values are:InsightsConditionRestrictionEnum
## •
## Included
## •
NotIncluded
The change in outcome value. Valid values are:InsightsOutcomeChangeEnum
## •
## Decreased
## •
## Increased
The insights result category. Valid values are:InsightsResultCategoryEnum
## •
## Negative
## •
## Positive
The descriptive insights result type. Valid values are:InsightsResultsTypeEnum
## •
FirstOrder
## •
SecondOrder
The analysis type for query insights. Valid values are:InsightsTypeEnum
## •
## Descriptive
## •
## Diagnostic
The time span for the metrics. Valid values are:MetricSpanEnum
## •
## Day
## •
## Month
## •
SinceLastAction
## 186
Einstein Discovery REST API Enums

DescriptionEnum
## •
## Week
The interval for look back. Valid values are:PredictHistoryIntervalEnum
## •
## None
## •
## Weekly
The sort order type for the collection. Valid values are:PredictionDefinitionCollection
CollectionSortOrderTypeEnum
## •
LastUpdate
## •
## Name
## •
OutcomeFieldLabel
## •
PredictionType
## •
SubscribedEntity
The sort order type for the collection. Valid values are:SmartDataDiscoveryAIModel
CollectionSortOrderTypeEnum
## •
CreatedDate
## •
## Description
## •
## Name
## •
PredictionFieldName
## •
PredictionType
## •
RuntimeType
The model status. Valid values are:SmartDataDiscoveryAIModelStatus
## Enum
## •
## Disabled
## •
## Enabled
## •
UploadCompleted
## •
UploadFailed
## •
## Uploading
## •
## Validating
## •
ValidationCompleted
## •
ValidationFailed
The transformation type. Valid values are:SmartDataDiscoveryAIModel
TransformationTypeEnum
## •
CategoricalImputation (Replace categorical missing values)
## •
ExtractDayOfWeek (Extract day of week)
## •
ExtractMonthOfYear (Extract month of year)
## •
FreeTextClustering (Free text clustering)
## •
NumericalImputation (Replace numerical missing values)
## •
SentimentAnalysis (Detecting sentiment)
## •
TimeSeriesForecast (Projected predictions)
## •
TypographicClustering (Fuzzy matching)
## 187
Einstein Discovery REST API Enums

DescriptionEnum
The bucketing strategy. Valid values are:SmartDataDiscoveryBucketing
StrategyEnum
## •
EvenWidth
## •
## Manual
## •
## Percentage
The categorical imputation method. Valid values are:SmartDataDiscoveryCategorical
ImputationMethodEnum
## •
## Auto
The classification algorithm type. Valid values are:SmartDataDiscoveryClassification
AlgorithmTypeEnum
## •
Best (Model tournament)
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
The date interval for the field. Valid values are:SmartDataDiscoveryDateInterval
## Enum
## •
## Auto
## •
## Day
## •
## Month
## •
## None
## •
## Quarter
## •
## Year
The source type for the field mapping. Valid values are:SmartDataDiscoveryFieldMapSource
TypeEnum
## •
AnalyticsDatasetField
## •
SalesforceField
The filter field type. Valid values are:SmartDataDiscoveryFilterFieldType
## Enum
## •
## Boolean
## •
## Date
## •
DateTime
## •
## Number
## •
## Text
The type of the filter value. Valid values are:SmartDataDiscoveryFilterValueType
## Enum
## •
## Constant
## •
## Placeholder
The impute method. Valid values are:SmartDataDiscoveryImputeMethod
## Enum
## •
## Mean
## •
## Median
## 188
Einstein Discovery REST API Enums

DescriptionEnum
## •
## Mode
## •
## None
The type of the model field. Valid values are:SmartDataDiscoveryModelFieldType
## Enum
## •
## Date
## •
## Number
## •
## Text
The runtime type of the model. Valid values are:SmartDataDiscoveryModelRuntime
TypeEnum
## •
## Discovery
## •
## H2O
## •
Py36Tensorflow244 (TensorFlow)
## •
Py37Scikitlearn102 (Scikit Learn v1.0.2)
## •
Py37Tensorflow207 (TensorFlow v2.7.0)
The model source type. Valid values are:SmartDataDiscoveryModelSource
TypeEnum
## •
## Discovery
## •
UserUpload
The numerical imputation method. Valid values are:SmartDataDiscoveryNumerical
ImputationMethodEnum
## •
## Mean
## •
## Median
## •
## Mode
The periodic date interval. Valid values are:SmartDataDiscoveryPeriodicDate
IntervalEnum
## •
## Day_of_week
## •
## Month_of_year
## •
## Quarter_of_year
The predict aggregate function type. Valid values are:SmartDataDiscoveryPredict
AggregateFunctionEnum
## •
## Average
## •
## Median
## •
## Sum
The predict aggregate status. Valid values are:SmartDataDiscoveryPredict
AggregateStatusEnum
## •
## Error
## •
## Success
The status of the predict job. Valid values are:SmartDataDiscoveryPredictJobStatus
## Enum
## •
## Cancelled
## •
## Completed
## 189
Einstein Discovery REST API Enums

DescriptionEnum
## •
## Failed
## •
InProgress
## •
NotStarted
## •
## Paused
The predict status. Valid values are:SmartDataDiscoveryPredictStatus
## Enum
## •
## Error
## •
## Success
The predict type. Valid values are:SmartDataDiscoveryPredictType
## Enum
## •
RawData (Represent rows within a two-dimensional array of row values)
## •
RecordOverrides (Represent records using Salesforce record Ids. Optionally override
or append individual records with an array of row values)
## •
Records (Represent rows using Salesforce record Ids associated with the
subscribedEntity of the prediction definition)
The prediction type. Valid values are:SmartDataDiscoveryPredictionType
## Enum
## •
## Classification
## •
MulticlassClassification
## •
## Regression
## •
## Unknown
The projected predictions interval setting type. Valid values are:SmartDataDiscoveryProjected
PredictionsIntervalSettingTypeEnum
## •
## Count
## •
CountFromDate
## •
## Date
The projected predictions internal type. Valid values are:SmartDataDiscoveryProjected
PredictionsIntervalTypeEnum
## •
## Day
## •
## Month
## •
## Quarter
## •
## Week
The projected predictions type. Valid values are:SmartDataDiscoveryProjected
PredictionsTypeEnum
## •
## Categorical
## •
## Numerical
The pushback type. Valid values are:SmartDataDiscoveryPushbackType
## Enum
## •
AiRecordInsight
## •
## Direct
## 190
Einstein Discovery REST API Enums

DescriptionEnum
The strategy for ordering text values. Valid values are:SmartDataDiscoveryOrderingEnum
## •
## Alphabetical
## •
## Numeric
## •
## Occurrence
The type of the recipient. Valid values are:SmartDataDiscoveryRecipientType
## Enum
## •
## Group
## •
## User
The status of the refresh job. Valid values are:SmartDataDiscoveryRefreshJobStatus
## Enum
## •
## Cancelled
## •
CompletedWithWarnings
## •
## Failure
## •
NoRunnableTask
## •
NotStarted
## •
## Running
## •
ScoringJobFailed
## •
## Success
## •
UserNotFound
The type of the refresh job. Valid values are:SmartDataDiscoveryRefreshJobType
## Enum
## •
## Scheduled
## •
UserTriggered
The status of the refresh task. Valid values are:SmartDataDiscoveryRefreshTask
StatusEnum
## •
AnalysisNotFound
## •
## Cancelled
## •
DatasetJoinFieldsMissing
## •
DatasetNotFound
## •
DatasetNotUpdated
## •
## Failure
## •
LimitsReached
## •
ModelSchemaChanged
## •
NotStarted
## •
OutcomeValuesChanged
## •
PoissonDistributionDisabled
## •
## Running
## •
StoryCreationFailure
## •
## Success
## 191
Einstein Discovery REST API Enums

DescriptionEnum
## •
UserNotFound
## •
WarningThresholdReached
The regression algorithm type. Valid values are:SmartDataDiscoveryRegression
AlgorithmTypeEnum
## •
Drf (Distributed Random Forest)
## •
Gbm (GBM)
## •
Glm (GLM)
## •
Xgboost (XGBoost)
The sort order for the collection. Valid values are:SmartDataDiscoverySortOrderEnum
## •
## Ascending
## •
## Descending
The transformation filter type for the model. Valid values are:SmartDataDiscoveryTransformation
FilterTypeEnum
## •
## Number
## •
## Text
The status. Valid values are:SmartDataDiscoveryStatusEnum
## •
## Disabled
## •
## Enabled
The analysis type. Valid values are:StoryAnalysisTypeEnum
## •
## Count
## •
## Descriptive
The story chart value type. Valid values are:StoryChartValueTypeEnum
## •
## Average
## •
## Baseline
## •
## Impact
## •
## Prediction
## •
SmallTerms
## •
## Unexplained
## •
## Value
The story count insights frequency change. Valid values are:StoryCountInsightsFrequencyChange
## Enum
## •
## Down
## •
## Up
The story count imsights frequency. Valid values are:StoryCountInsightsFrequency;Enum
## •
LessOften
## •
MoreOften
## 192
Einstein Discovery REST API Enums

DescriptionEnum
The descriptive insights impact for the story. Valid values are:StoryDescriptiveInsightsImpactEnum
## •
## Improved
## •
## Worsened
The story descriptive insights rate. Valid values are:StoryDescriptiveInsightsRatingEnum
## •
AboveAverage
## •
BelowAverage
## •
## Higher
## •
## Lower
The field type. Valid values are:StoryFieldDetailTypeEnum
## •
## Field
## •
## Outcome
The narrative element type. Valid values are:StoryNarrativeElementTypeEnum
## •
BadSelection
## •
## Body
## •
BucketsMismatchSection
## •
GoodSection
## •
## Heading
## •
MissingValuesSection
## •
NewValuesSection
## •
NumberedList
## •
OutcomeValue
## •
## Paragraph
## •
SubHeading
## •
UnorderedList
The validation strategy for the configuration. Valid values are:ValidationConfigurationStrategy
## Enum
## •
Validation_Dataset
## •
Validation_Set_Ratio
## 193
Einstein Discovery REST API Enums